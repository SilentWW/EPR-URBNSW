"""
GRN (Goods Received Note) Router
Handles goods receipt, inventory updates, and automatic finance entries
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Optional, List
from datetime import datetime, timezone
from pydantic import BaseModel

from utils.helpers import serialize_doc, generate_id, get_current_timestamp
from utils.auth import get_current_user

router = APIRouter(prefix="/grn", tags=["GRN"])

# Database will be injected from main app
db = None

def set_db(database):
    global db
    db = database

# ============== MODELS ==============

class GRNItem(BaseModel):
    product_id: Optional[str] = None
    variation_id: Optional[str] = None  # For variable products
    product_name: str
    sku: Optional[str] = None
    description: Optional[str] = None
    short_description: Optional[str] = None
    category: Optional[str] = None
    quantity: int
    cost_price: float
    regular_price: float
    sale_price: Optional[float] = None
    weight: Optional[float] = None
    visibility: str = "public"
    tags: Optional[str] = None
    attributes: Optional[List[dict]] = None

class GRNCreate(BaseModel):
    supplier_id: str
    reference_number: Optional[str] = None
    received_date: str
    items: List[GRNItem]
    notes: Optional[str] = None
    sync_to_woo: bool = True
    po_id: Optional[str] = None  # Link to Purchase Order

class GRNReturnItem(BaseModel):
    product_id: Optional[str] = None
    variation_id: Optional[str] = None  # For variable products
    product_name: str
    sku: Optional[str] = None
    quantity: int
    cost_price: float

class GRNReturn(BaseModel):
    return_type: str  # 'full' or 'partial'
    return_reason: str  # 'supplier' or 'damaged'
    settlement_type: Optional[str] = None  # 'refund' or 'credit' (only for supplier returns)
    refund_account_id: Optional[str] = None  # Bank/cash account to receive refund
    notes: Optional[str] = None
    items: List[GRNReturnItem]

# ============== SKU GENERATION ==============

async def generate_sku(company_id: str, prefix: str = "URBN") -> str:
    """Generate unique SKU like URBN0001, URBN0002, etc."""
    # Find the highest SKU number
    products = await db.products.find(
        {"company_id": company_id, "sku": {"$regex": f"^{prefix}"}},
        {"sku": 1}
    ).to_list(10000)
    
    max_num = 0
    for p in products:
        sku = p.get("sku", "")
        if sku.startswith(prefix):
            try:
                num = int(sku[len(prefix):])
                if num > max_num:
                    max_num = num
            except ValueError:
                continue
    
    new_num = max_num + 1
    return f"{prefix}{new_num:04d}"

# ============== GRN ENDPOINTS ==============

@router.get("/next-sku")
async def get_next_sku(
    prefix: str = "URBN",
    current_user: dict = Depends(get_current_user)
):
    """Get the next available SKU"""
    sku = await generate_sku(current_user["company_id"], prefix)
    return {"next_sku": sku}

@router.get("/report/summary")
async def get_grn_summary(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get GRN summary report"""
    company_id = current_user["company_id"]
    
    query = {"company_id": company_id}
    if start_date:
        query["received_date"] = {"$gte": start_date}
    if end_date:
        if "received_date" in query:
            query["received_date"]["$lte"] = end_date
        else:
            query["received_date"] = {"$lte": end_date}
    
    grns = await db.grns.find(query, {"_id": 0}).to_list(10000)
    
    total_grns = len(grns)
    total_cost = sum(g["total_cost"] for g in grns)
    total_items = sum(len(g["items"]) for g in grns)
    
    # Group by supplier
    by_supplier = {}
    for g in grns:
        supplier = g["supplier_name"]
        if supplier not in by_supplier:
            by_supplier[supplier] = {"count": 0, "total": 0}
        by_supplier[supplier]["count"] += 1
        by_supplier[supplier]["total"] += g["total_cost"]
    
    return {
        "total_grns": total_grns,
        "total_cost": round(total_cost, 2),
        "total_items": total_items,
        "by_supplier": by_supplier
    }

@router.get("")
async def get_grns(
    status: Optional[str] = None,
    supplier_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all GRNs with optional filters"""
    query = {"company_id": current_user["company_id"]}
    
    if status:
        query["status"] = status
    if supplier_id:
        query["supplier_id"] = supplier_id
    if start_date:
        query["received_date"] = {"$gte": start_date}
    if end_date:
        if "received_date" in query:
            query["received_date"]["$lte"] = end_date
        else:
            query["received_date"] = {"$lte": end_date}
    
    grns = await db.grns.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
    return grns

@router.get("/{grn_id}")
async def get_grn(grn_id: str, current_user: dict = Depends(get_current_user)):
    """Get single GRN details"""
    grn = await db.grns.find_one(
        {"id": grn_id, "company_id": current_user["company_id"]},
        {"_id": 0}
    )
    if not grn:
        raise HTTPException(status_code=404, detail="GRN not found")
    return grn

@router.post("")
async def create_grn(
    data: GRNCreate,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a GRN (Goods Received Note)
    - Creates/updates products with pricing
    - Updates inventory
    - Creates automatic finance entries (COGS expense)
    - Optionally syncs to WooCommerce
    """
    company_id = current_user["company_id"]
    user_id = current_user["user_id"]
    
    # Validate supplier
    supplier = await db.suppliers.find_one({"id": data.supplier_id, "company_id": company_id})
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    # Generate GRN number
    count = await db.grns.count_documents({"company_id": company_id})
    grn_number = f"GRN-{datetime.now(timezone.utc).strftime('%Y%m')}-{count + 1:04d}"
    
    grn_id = generate_id()
    total_cost = 0
    processed_items = []
    products_to_sync = []
    variations_to_sync = []
    
    for item in data.items:
        # Generate SKU if not provided
        sku = item.sku
        if not sku:
            sku = await generate_sku(company_id)
        
        # Calculate selling price (sale_price if set, otherwise regular_price)
        selling_price = item.sale_price if item.sale_price else item.regular_price
        
        # Check if this is a variation item
        if item.variation_id:
            # Handle variation-level inventory
            variation = await db.product_variations.find_one({
                "id": item.variation_id,
                "company_id": company_id
            })
            if not variation:
                raise HTTPException(status_code=404, detail=f"Variation {item.variation_id} not found")
            
            # Update variation stock and prices
            await db.product_variations.update_one(
                {"id": item.variation_id},
                {"$set": {
                    "cost_price": item.cost_price,
                    "regular_price": item.regular_price,
                    "sale_price": item.sale_price,
                    "selling_price": selling_price,
                    "updated_at": get_current_timestamp()
                },
                "$inc": {"stock_quantity": item.quantity}}
            )
            
            # Also update parent product total stock
            if variation.get("parent_product_id"):
                await db.products.update_one(
                    {"id": variation["parent_product_id"]},
                    {"$inc": {"stock_quantity": item.quantity},
                     "$set": {"updated_at": get_current_timestamp()}}
                )
            
            product_id = variation.get("parent_product_id")
            variation_id = item.variation_id
            
            # Get updated variation for sync
            updated_variation = await db.product_variations.find_one({"id": variation_id}, {"_id": 0})
            variations_to_sync.append(updated_variation)
            
        elif item.product_id:
            # Check if product exists
            product = await db.products.find_one({"id": item.product_id, "company_id": company_id})
            if not product:
                raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")
            
            # Update existing product
            await db.products.update_one(
                {"id": item.product_id},
                {"$set": {
                    "cost_price": item.cost_price,
                    "regular_price": item.regular_price,
                    "sale_price": item.sale_price,
                    "selling_price": selling_price,
                    "description": item.description or product.get("description"),
                    "short_description": item.short_description or product.get("short_description"),
                    "weight": item.weight or product.get("weight"),
                    "visibility": item.visibility,
                    "tags": item.tags or product.get("tags"),
                    "attributes": item.attributes or product.get("attributes"),
                    "updated_at": get_current_timestamp()
                },
                "$inc": {"stock_quantity": item.quantity}}
            )
            product_id = item.product_id
            variation_id = None
            
            # Get updated product for sync
            updated_product = await db.products.find_one({"id": product_id}, {"_id": 0})
            products_to_sync.append(updated_product)
        else:
            # Create new product
            product_id = generate_id()
            new_product = {
                "id": product_id,
                "company_id": company_id,
                "sku": sku,
                "name": item.product_name,
                "description": item.description,
                "short_description": item.short_description,
                "category": item.category,
                "cost_price": item.cost_price,
                "regular_price": item.regular_price,
                "sale_price": item.sale_price,
                "selling_price": selling_price,
                "stock_quantity": item.quantity,
                "low_stock_threshold": 10,
                "weight": item.weight,
                "visibility": item.visibility,
                "tags": item.tags,
                "manage_stock": True,
                "attributes": item.attributes,
                "product_type": "simple",
                "woo_product_id": None,
                "created_at": get_current_timestamp(),
                "updated_at": get_current_timestamp()
            }
            await db.products.insert_one(new_product)
            products_to_sync.append(new_product)
            variation_id = None
        
        # Calculate line total
        line_total = item.quantity * item.cost_price
        total_cost += line_total
        
        processed_items.append({
            "product_id": product_id,
            "variation_id": variation_id if item.variation_id else None,
            "product_name": item.product_name,
            "sku": sku,
            "quantity": item.quantity,
            "cost_price": item.cost_price,
            "regular_price": item.regular_price,
            "sale_price": item.sale_price,
            "line_total": line_total
        })
        
        # Create inventory movement record
        await db.inventory_movements.insert_one({
            "id": generate_id(),
            "company_id": company_id,
            "product_id": product_id,
            "variation_id": variation_id if item.variation_id else None,
            "movement_type": "grn_receipt",
            "quantity": item.quantity,
            "reference_type": "grn",
            "reference_id": grn_id,
            "notes": f"Received via GRN {grn_number}",
            "created_by": user_id,
            "created_at": get_current_timestamp()
        })
    
    # Create GRN record
    grn = {
        "id": grn_id,
        "grn_number": grn_number,
        "company_id": company_id,
        "supplier_id": data.supplier_id,
        "supplier_name": supplier["name"],
        "reference_number": data.reference_number,
        "received_date": data.received_date,
        "items": processed_items,
        "total_cost": total_cost,
        "status": "received",
        "notes": data.notes,
        "sync_to_woo": data.sync_to_woo,
        "woo_sync_status": "pending" if data.sync_to_woo else None,
        "po_id": data.po_id,
        "created_by": user_id,
        "created_at": get_current_timestamp()
    }
    await db.grns.insert_one(grn)
    
    # Update linked Purchase Order status if present
    if data.po_id:
        await db.purchase_orders.update_one(
            {"id": data.po_id, "company_id": company_id},
            {"$set": {"status": "received", "updated_at": get_current_timestamp()}}
        )
    
    # Create automatic finance entries
    await create_grn_finance_entries(company_id, grn_id, grn_number, supplier["name"], total_cost, user_id)
    
    # Sync to WooCommerce in background
    if data.sync_to_woo:
        background_tasks.add_task(
            sync_grn_products_to_woo,
            company_id,
            grn_id,
            products_to_sync,
            variations_to_sync
        )
    
    return {
        "id": grn_id,
        "grn_number": grn_number,
        "total_cost": total_cost,
        "items_count": len(processed_items),
        "message": "GRN created successfully",
        "woo_sync": "Sync initiated" if data.sync_to_woo else "Not synced"
    }

async def create_grn_finance_entries(
    company_id: str,
    grn_id: str,
    grn_number: str,
    supplier_name: str,
    total_cost: float,
    user_id: str
):
    """Create automatic journal entries for GRN"""
    
    # Get account IDs
    inventory_account = await db.accounts.find_one(
        {"company_id": company_id, "code": "1400"},  # Inventory
        {"id": 1}
    )
    ap_account = await db.accounts.find_one(
        {"company_id": company_id, "code": "2100"},  # Accounts Payable
        {"id": 1}
    )
    
    if not inventory_account or not ap_account:
        print(f"Warning: Finance accounts not found for company {company_id}")
        return
    
    # Create journal entry: Debit Inventory, Credit Accounts Payable
    entry_id = generate_id()
    entry_number = f"GRN-JE-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{entry_id[:4].upper()}"
    
    lines = [
        {
            "account_id": inventory_account["id"],
            "account_code": "1400",
            "account_name": "Inventory",
            "debit": total_cost,
            "credit": 0,
            "description": f"Inventory received - {grn_number}"
        },
        {
            "account_id": ap_account["id"],
            "account_code": "2100",
            "account_name": "Accounts Payable",
            "debit": 0,
            "credit": total_cost,
            "description": f"Payable to {supplier_name} - {grn_number}"
        }
    ]
    
    journal_entry = {
        "id": entry_id,
        "entry_number": entry_number,
        "company_id": company_id,
        "entry_date": get_current_timestamp()[:10],
        "reference_number": grn_number,
        "description": f"GRN Receipt - {supplier_name}",
        "lines": lines,
        "total_debit": total_cost,
        "total_credit": total_cost,
        "is_balanced": True,
        "is_auto_generated": True,
        "is_reversed": False,
        "reference_type": "grn",
        "reference_id": grn_id,
        "created_by": user_id,
        "created_at": get_current_timestamp()
    }
    await db.journal_entries.insert_one(journal_entry)
    
    # Update account balances
    await db.accounts.update_one(
        {"id": inventory_account["id"]},
        {"$inc": {"current_balance": total_cost}}
    )
    await db.accounts.update_one(
        {"id": ap_account["id"]},
        {"$inc": {"current_balance": total_cost}}
    )
    
    # Also create accounting entry for reporting
    await db.accounting_entries.insert_one({
        "id": generate_id(),
        "company_id": company_id,
        "entry_type": "expense",
        "category": "Inventory Purchase",
        "amount": total_cost,
        "description": f"GRN {grn_number} - {supplier_name}",
        "reference_type": "grn",
        "reference_id": grn_id,
        "created_by": user_id,
        "created_at": get_current_timestamp()
    })

async def sync_grn_products_to_woo(company_id: str, grn_id: str, products: list, variations: list = None):
    """Sync GRN products and variations to WooCommerce with full stock management"""
    try:
        # Import WooCommerce client
        from routes.woocommerce import get_woo_client
        
        client = await get_woo_client(company_id)
        synced_count = 0
        errors = []
        
        # Sync simple products
        for product in products:
            try:
                woo_data = {
                    "name": product["name"],
                    "sku": product["sku"],
                    "description": product.get("description", ""),
                    "short_description": product.get("short_description", ""),
                    "regular_price": str(product.get("regular_price", 0)),
                    # IMPORTANT: Enable stock management in WooCommerce
                    "manage_stock": True,
                    "stock_quantity": product.get("stock_quantity", 0),
                    "stock_status": "instock" if product.get("stock_quantity", 0) > 0 else "outofstock",
                    "status": "publish" if product.get("visibility") == "public" else "private",
                }
                
                # Add category if set
                if product.get("category"):
                    # Try to find or create category in WooCommerce
                    try:
                        categories = await client.get("products/categories", params={
                            "search": product["category"]
                        })
                        if categories:
                            woo_data["categories"] = [{"id": categories[0]["id"]}]
                        else:
                            # Create the category
                            new_cat = await client.post("products/categories", {
                                "name": product["category"]
                            })
                            woo_data["categories"] = [{"id": new_cat["id"]}]
                    except:
                        pass  # Skip category if can't sync
                
                # Add sale price if set
                if product.get("sale_price"):
                    woo_data["sale_price"] = str(product["sale_price"])
                
                # Add weight if set
                if product.get("weight"):
                    woo_data["weight"] = str(product["weight"])
                
                # Add tags if set - generate SEO tags if not provided
                tags_str = product.get("tags", "")
                if not tags_str and product.get("name"):
                    # Auto-generate SEO tags
                    words = product["name"].lower().split()
                    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'with'}
                    auto_tags = [w for w in words if w not in stop_words and len(w) > 2][:5]
                    if product.get("category"):
                        auto_tags.append(product["category"].lower())
                    tags_str = ", ".join(auto_tags)
                
                if tags_str:
                    tags = [{"name": tag.strip()} for tag in tags_str.split(",") if tag.strip()]
                    woo_data["tags"] = tags
                
                # Add attributes if set
                if product.get("attributes"):
                    woo_data["attributes"] = product["attributes"]
                
                if product.get("woo_product_id"):
                    # Update existing product
                    await client.put(f"products/{product['woo_product_id']}", woo_data)
                else:
                    # Create new product
                    result = await client.post("products", woo_data)
                    # Update local product with WooCommerce ID
                    await db.products.update_one(
                        {"id": product["id"]},
                        {"$set": {"woo_product_id": str(result["id"])}}
                    )
                
                synced_count += 1
                
            except Exception as e:
                errors.append({"product_id": product["id"], "error": str(e)})
        
        # Sync variations
        if variations:
            for variation in variations:
                try:
                    # Get parent product woo_product_id
                    parent_product = await db.products.find_one({"id": variation["parent_product_id"]})
                    if not parent_product or not parent_product.get("woo_product_id"):
                        continue
                    
                    if variation.get("woo_variation_id"):
                        # Update variation stock in WooCommerce
                        await client.put(
                            f"products/{parent_product['woo_product_id']}/variations/{variation['woo_variation_id']}",
                            {
                                "stock_quantity": variation.get("stock_quantity", 0),
                                "manage_stock": True,
                                "regular_price": str(variation.get("regular_price", 0)),
                                "sale_price": str(variation.get("sale_price", "")) if variation.get("sale_price") else ""
                            }
                        )
                        synced_count += 1
                except Exception as e:
                    errors.append({"variation_id": variation.get("id"), "error": str(e)})
        
        # Update GRN sync status
        sync_status = "synced" if not errors else "partial"
        await db.grns.update_one(
            {"id": grn_id},
            {"$set": {
                "woo_sync_status": sync_status,
                "woo_sync_errors": errors,
                "woo_synced_at": get_current_timestamp()
            }}
        )
        
    except Exception as e:
        await db.grns.update_one(
            {"id": grn_id},
            {"$set": {
                "woo_sync_status": "failed",
                "woo_sync_errors": [{"error": str(e)}]
            }}
        )

@router.post("/{grn_id}/resync")
async def resync_grn_to_woo(
    grn_id: str,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """Re-sync GRN products to WooCommerce"""
    grn = await db.grns.find_one(
        {"id": grn_id, "company_id": current_user["company_id"]}
    )
    if not grn:
        raise HTTPException(status_code=404, detail="GRN not found")
    
    # Get products from GRN items
    product_ids = [item["product_id"] for item in grn["items"]]
    products = await db.products.find(
        {"id": {"$in": product_ids}},
        {"_id": 0}
    ).to_list(100)
    
    # Update sync status
    await db.grns.update_one(
        {"id": grn_id},
        {"$set": {"woo_sync_status": "pending"}}
    )
    
    background_tasks.add_task(
        sync_grn_products_to_woo,
        current_user["company_id"],
        grn_id,
        products
    )
    
    return {"message": "Re-sync initiated"}

@router.delete("/{grn_id}")
async def delete_grn(grn_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a GRN (only if not processed)"""
    grn = await db.grns.find_one(
        {"id": grn_id, "company_id": current_user["company_id"]}
    )
    if not grn:
        raise HTTPException(status_code=404, detail="GRN not found")
    
    # Don't allow deletion of synced GRNs
    if grn.get("woo_sync_status") == "synced":
        raise HTTPException(status_code=400, detail="Cannot delete synced GRN. Reverse instead.")
    
    await db.grns.delete_one({"id": grn_id})
    return {"message": "GRN deleted"}


@router.post("/{grn_id}/return")
async def return_grn(
    grn_id: str, 
    data: GRNReturn, 
    current_user: dict = Depends(get_current_user)
):
    """
    Process a GRN return - reverses inventory and creates financial entries.
    Only Admin and Manager roles can perform this action.
    """
    import uuid
    
    # Role check - only admin and manager can return
    if current_user["role"] not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Only admin and manager can process GRN returns")
    
    # Get the GRN
    grn = await db.grns.find_one({
        "id": grn_id,
        "company_id": current_user["company_id"]
    })
    if not grn:
        raise HTTPException(status_code=404, detail="GRN not found")
    
    if grn.get("status") == "returned":
        raise HTTPException(status_code=400, detail="This GRN has already been fully returned")
    
    company_id = current_user["company_id"]
    return_date = datetime.now(timezone.utc).isoformat()
    total_return_value = 0
    products_to_sync = []  # Track products for WooCommerce sync
    
    # Process each return item
    for item in data.items:
        # Reduce inventory
        product = await db.products.find_one({
            "company_id": company_id,
            "$or": [
                {"id": item.product_id},
                {"sku": item.sku}
            ]
        }) if item.product_id or item.sku else None
        
        if product:
            new_stock = max(0, product["stock_quantity"] - item.quantity)
            await db.products.update_one(
                {"id": product["id"]},
                {"$set": {
                    "stock_quantity": new_stock,
                    "updated_at": return_date
                }}
            )
            
            # Create inventory movement record
            await db.inventory_movements.insert_one({
                "id": str(uuid.uuid4()),
                "company_id": company_id,
                "product_id": product["id"],
                "product_name": item.product_name,
                "movement_type": "out",
                "quantity": item.quantity,
                "previous_stock": product["stock_quantity"],
                "new_stock": new_stock,
                "reason": f"GRN Return - {grn['grn_number']} ({data.return_reason})",
                "reference_type": "grn_return",
                "reference_id": grn_id,
                "created_by": current_user["user_id"],
                "created_at": return_date
            })
            
            # Track products for WooCommerce sync
            products_to_sync.append({
                "product_id": product["id"],
                "new_stock": new_stock,
                "woo_product_id": product.get("woo_product_id")
            })
        
        total_return_value += item.quantity * item.cost_price
    
    # Create journal entries based on return reason and settlement type
    entry_id = str(uuid.uuid4())
    entry_number = f"GRNRET-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{entry_id[:4].upper()}"
    refund_entry_number = None
    supplier_credit_id = None
    
    if data.return_reason == "supplier":
        inventory_account = await db.accounts.find_one({"company_id": company_id, "code": "1400"})
        
        if data.settlement_type == "refund" and data.refund_account_id:
            # Supplier Returns Money (Refund)
            # 1. First entry: Debit Bank/Cash, Credit Inventory (goods returned, money received)
            bank_account = await db.bank_accounts.find_one({
                "company_id": company_id,
                "id": data.refund_account_id
            })
            
            # Get chart account linked to bank account
            bank_chart_account = None
            if bank_account and bank_account.get("chart_account_id"):
                bank_chart_account = await db.accounts.find_one({"id": bank_account["chart_account_id"]})
            
            # If no bank_account found, try chart of accounts directly
            if not bank_account:
                bank_chart_account = await db.accounts.find_one({
                    "company_id": company_id,
                    "id": data.refund_account_id
                })
            
            if inventory_account and (bank_account or bank_chart_account):
                bank_code = bank_chart_account["code"] if bank_chart_account else "1100"
                bank_name = bank_account["account_name"] if bank_account else bank_chart_account["name"]
                
                journal_entry = {
                    "id": entry_id,
                    "company_id": company_id,
                    "entry_number": entry_number,
                    "date": return_date,
                    "description": f"GRN Return - Supplier Refund - {grn['grn_number']}",
                    "reference_type": "grn_return",
                    "reference_id": grn_id,
                    "lines": [
                        {
                            "account_code": bank_code,
                            "account_name": bank_name,
                            "debit": total_return_value,
                            "credit": 0,
                            "description": "Refund received from supplier"
                        },
                        {
                            "account_code": "1400",
                            "account_name": inventory_account["name"],
                            "debit": 0,
                            "credit": total_return_value,
                            "description": "Reduce inventory - goods returned"
                        }
                    ],
                    "total_debit": total_return_value,
                    "total_credit": total_return_value,
                    "status": "posted",
                    "created_by": current_user["user_id"],
                    "created_at": return_date
                }
                await db.journal_entries.insert_one(journal_entry)
                
                # Update bank account balance
                if bank_account:
                    await db.bank_accounts.update_one(
                        {"id": data.refund_account_id},
                        {"$inc": {"current_balance": total_return_value}}
                    )
                
                # Update chart account balances
                if bank_chart_account:
                    await db.accounts.update_one(
                        {"id": bank_chart_account["id"]},
                        {"$inc": {"balance": total_return_value}}
                    )
                await db.accounts.update_one(
                    {"company_id": company_id, "code": "1400"},
                    {"$inc": {"balance": -total_return_value}}
                )
                
                refund_entry_number = entry_number
        
        elif data.settlement_type == "credit":
            # Supplier Sends More Qty (Credit)
            # Create supplier credit record and journal entry
            ap_account = await db.accounts.find_one({"company_id": company_id, "code": "2100"})
            
            if inventory_account and ap_account:
                # Journal entry: Debit AP (reduce payable), Credit Inventory
                journal_entry = {
                    "id": entry_id,
                    "company_id": company_id,
                    "entry_number": entry_number,
                    "date": return_date,
                    "description": f"GRN Return - Supplier Credit - {grn['grn_number']}",
                    "reference_type": "grn_return",
                    "reference_id": grn_id,
                    "lines": [
                        {
                            "account_code": "2100",
                            "account_name": ap_account["name"],
                            "debit": total_return_value,
                            "credit": 0,
                            "description": "Reduce payable - supplier credit"
                        },
                        {
                            "account_code": "1400",
                            "account_name": inventory_account["name"],
                            "debit": 0,
                            "credit": total_return_value,
                            "description": "Reduce inventory - goods returned"
                        }
                    ],
                    "total_debit": total_return_value,
                    "total_credit": total_return_value,
                    "status": "posted",
                    "created_by": current_user["user_id"],
                    "created_at": return_date
                }
                await db.journal_entries.insert_one(journal_entry)
                
                # Update account balances
                await db.accounts.update_one(
                    {"company_id": company_id, "code": "2100"},
                    {"$inc": {"balance": -total_return_value}}
                )
                await db.accounts.update_one(
                    {"company_id": company_id, "code": "1400"},
                    {"$inc": {"balance": -total_return_value}}
                )
            
            # Create supplier credit record
            supplier_credit_id = str(uuid.uuid4())
            supplier = await db.suppliers.find_one({"id": grn.get("supplier_id")})
            
            await db.supplier_credits.insert_one({
                "id": supplier_credit_id,
                "company_id": company_id,
                "supplier_id": grn.get("supplier_id"),
                "supplier_name": supplier["name"] if supplier else grn.get("supplier_name", "Unknown"),
                "grn_id": grn_id,
                "grn_number": grn["grn_number"],
                "amount": total_return_value,
                "remaining_amount": total_return_value,
                "status": "active",
                "reason": f"GRN Return - {grn['grn_number']}",
                "notes": data.notes,
                "created_by": current_user["user_id"],
                "created_at": return_date
            })
            
            # Update supplier credit balance
            if supplier:
                await db.suppliers.update_one(
                    {"id": grn.get("supplier_id")},
                    {"$inc": {"credit_balance": total_return_value}}
                )
    
    else:
        # Damaged/Written Off: Debit Loss/Write-off Expense, Credit Inventory
        # Use Operating Expenses for write-off
        expense_account = await db.accounts.find_one({"company_id": company_id, "code": "6000"})
        inventory_account = await db.accounts.find_one({"company_id": company_id, "code": "1400"})
        
        if expense_account and inventory_account:
            journal_entry = {
                "id": entry_id,
                "company_id": company_id,
                "entry_number": entry_number,
                "date": return_date,
                "description": f"GRN Write-off (Damaged) - {grn['grn_number']}",
                "reference_type": "grn_return",
                "reference_id": grn_id,
                "lines": [
                    {
                        "account_code": "6000",
                        "account_name": expense_account["name"],
                        "debit": total_return_value,
                        "credit": 0,
                        "description": "Write-off expense - damaged goods"
                    },
                    {
                        "account_code": "1400",
                        "account_name": inventory_account["name"],
                        "debit": 0,
                        "credit": total_return_value,
                        "description": "Reduce inventory - damaged goods"
                    }
                ],
                "total_debit": total_return_value,
                "total_credit": total_return_value,
                "status": "posted",
                "created_by": current_user["user_id"],
                "created_at": return_date
            }
            await db.journal_entries.insert_one(journal_entry)
            
            # Update account balances
            await db.accounts.update_one(
                {"company_id": company_id, "code": "6000"},
                {"$inc": {"balance": total_return_value}}  # Increase expense
            )
            await db.accounts.update_one(
                {"company_id": company_id, "code": "1400"},
                {"$inc": {"balance": -total_return_value}}  # Reduce asset
            )
    
    # Create return record
    return_record = {
        "return_date": return_date,
        "return_type": data.return_type,
        "return_reason": data.return_reason,
        "settlement_type": data.settlement_type,
        "refund_account_id": data.refund_account_id,
        "supplier_credit_id": supplier_credit_id,
        "notes": data.notes,
        "items": [item.model_dump() for item in data.items],
        "total_value": total_return_value,
        "journal_entry_number": entry_number,
        "refund_entry_number": refund_entry_number,
        "created_by": current_user["user_id"]
    }
    
    # Determine new status
    original_total = sum(item["quantity"] for item in grn["items"])
    returned_total = sum(item.quantity for item in data.items)
    new_status = "returned" if returned_total >= original_total else "partial_return"
    
    # Update GRN with return info
    await db.grns.update_one(
        {"id": grn_id},
        {
            "$set": {
                "status": new_status,
                "updated_at": return_date
            },
            "$push": {
                "returns": return_record
            }
        }
    )
    
    # If linked to a PO, update PO as well
    if grn.get("po_id"):
        await db.purchase_orders.update_one(
            {"id": grn["po_id"]},
            {"$set": {
                "has_returns": True,
                "updated_at": return_date
            }}
        )
    
    # Sync stock to WooCommerce
    woo_sync_results = []
    company = await db.companies.find_one({"id": company_id})
    woo_settings = company.get("woo_settings") if company else None
    
    if woo_settings and woo_settings.get("enabled"):
        import httpx
        store_url = woo_settings["store_url"].rstrip('/')
        consumer_key = woo_settings["consumer_key"]
        consumer_secret = woo_settings["consumer_secret"]
        api_url = f"{store_url}/wp-json/wc/v3"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for product_info in products_to_sync:
                if product_info.get("woo_product_id"):
                    try:
                        response = await client.put(
                            f"{api_url}/products/{product_info['woo_product_id']}",
                            auth=(consumer_key, consumer_secret),
                            json={"stock_quantity": product_info["new_stock"]}
                        )
                        woo_sync_results.append({
                            "product_id": product_info["product_id"],
                            "woo_product_id": product_info["woo_product_id"],
                            "status": "synced" if response.status_code < 400 else "failed"
                        })
                    except Exception as e:
                        woo_sync_results.append({
                            "product_id": product_info["product_id"],
                            "status": "failed",
                            "error": str(e)
                        })
    
    return {
        "message": "GRN return processed successfully",
        "return_value": total_return_value,
        "journal_entry": entry_number,
        "new_status": new_status,
        "settlement_type": data.settlement_type,
        "supplier_credit_id": supplier_credit_id,
        "woo_sync_results": woo_sync_results
    }
