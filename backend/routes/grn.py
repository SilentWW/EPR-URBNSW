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
    
    for item in data.items:
        # Generate SKU if not provided
        sku = item.sku
        if not sku:
            sku = await generate_sku(company_id)
        
        # Calculate selling price (sale_price if set, otherwise regular_price)
        selling_price = item.sale_price if item.sale_price else item.regular_price
        
        # Check if product exists
        if item.product_id:
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
                "woo_product_id": None,
                "created_at": get_current_timestamp(),
                "updated_at": get_current_timestamp()
            }
            await db.products.insert_one(new_product)
            products_to_sync.append(new_product)
        
        # Calculate line total
        line_total = item.quantity * item.cost_price
        total_cost += line_total
        
        processed_items.append({
            "product_id": product_id,
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
        "created_by": user_id,
        "created_at": get_current_timestamp()
    }
    await db.grns.insert_one(grn)
    
    # Create automatic finance entries
    await create_grn_finance_entries(company_id, grn_id, grn_number, supplier["name"], total_cost, user_id)
    
    # Sync to WooCommerce in background
    if data.sync_to_woo:
        background_tasks.add_task(
            sync_grn_products_to_woo,
            company_id,
            grn_id,
            products_to_sync
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

async def sync_grn_products_to_woo(company_id: str, grn_id: str, products: list):
    """Sync GRN products to WooCommerce"""
    try:
        # Import WooCommerce client
        from routes.woocommerce import get_woo_client
        
        client = await get_woo_client(company_id)
        synced_count = 0
        errors = []
        
        for product in products:
            try:
                woo_data = {
                    "name": product["name"],
                    "sku": product["sku"],
                    "description": product.get("description", ""),
                    "short_description": product.get("short_description", ""),
                    "regular_price": str(product.get("regular_price", 0)),
                    "manage_stock": product.get("manage_stock", True),
                    "stock_quantity": product.get("stock_quantity", 0),
                    "status": "publish" if product.get("visibility") == "public" else "private",
                }
                
                # Add sale price if set
                if product.get("sale_price"):
                    woo_data["sale_price"] = str(product["sale_price"])
                
                # Add weight if set
                if product.get("weight"):
                    woo_data["weight"] = str(product["weight"])
                
                # Add tags if set
                if product.get("tags"):
                    tags = [{"name": tag.strip()} for tag in product["tags"].split(",")]
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

