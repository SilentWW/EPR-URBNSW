"""
Product Variations Router
Handles WooCommerce variable products and variations sync, inventory at variation level
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Optional, List
from datetime import datetime, timezone
from pydantic import BaseModel
import httpx

from utils.helpers import serialize_doc, generate_id, get_current_timestamp
from utils.auth import get_current_user

router = APIRouter(prefix="/variations", tags=["Product Variations"])

# Database will be injected from main app
db = None

def set_db(database):
    global db
    db = database

# ============== MODELS ==============

class VariationAttribute(BaseModel):
    name: str  # e.g., "Color", "Size"
    option: str  # e.g., "Blue", "32"

class ProductVariation(BaseModel):
    id: Optional[str] = None
    parent_product_id: str
    woo_variation_id: Optional[str] = None
    sku: str
    attributes: List[VariationAttribute]
    cost_price: float = 0.0
    regular_price: float = 0.0
    sale_price: Optional[float] = None
    stock_quantity: int = 0
    weight: Optional[float] = None
    manage_stock: bool = True

class VariationCreate(BaseModel):
    parent_product_id: str
    sku: str
    attributes: List[VariationAttribute]
    cost_price: float = 0.0
    regular_price: float = 0.0
    sale_price: Optional[float] = None
    stock_quantity: int = 0
    weight: Optional[float] = None

class VariationUpdate(BaseModel):
    sku: Optional[str] = None
    cost_price: Optional[float] = None
    regular_price: Optional[float] = None
    sale_price: Optional[float] = None
    stock_quantity: Optional[int] = None
    weight: Optional[float] = None

# Models for creating variable products from ERP
class ProductAttribute(BaseModel):
    name: str  # e.g., "Color", "Size"
    options: List[str]  # e.g., ["Blue", "Black", "Red"] or ["S", "M", "L", "XL"]

class VariableProductCreate(BaseModel):
    name: str
    sku: str
    description: Optional[str] = None
    short_description: Optional[str] = None
    category: Optional[str] = None
    attributes: List[ProductAttribute]  # Define Color, Size options
    generate_variations: bool = True  # Auto-generate all combinations
    sync_to_woo: bool = True

class BulkVariationCreate(BaseModel):
    parent_product_id: str
    variations: List[VariationCreate]
    sync_to_woo: bool = True

# ============== WOOCOMMERCE CLIENT HELPER ==============

async def get_woo_client(company_id: str):
    """Get WooCommerce client settings for a company"""
    company = await db.companies.find_one({"id": company_id})
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    woo_settings = company.get("woo_settings")
    if not woo_settings or not woo_settings.get("enabled"):
        raise HTTPException(status_code=400, detail="WooCommerce integration not configured or disabled")
    
    return {
        "store_url": woo_settings["store_url"].rstrip('/'),
        "consumer_key": woo_settings["consumer_key"],
        "consumer_secret": woo_settings["consumer_secret"]
    }

async def woo_request(client_config: dict, method: str, endpoint: str, data: dict = None, params: dict = None):
    """Make authenticated request to WooCommerce API"""
    url = f"{client_config['store_url']}/wp-json/wc/v3/{endpoint}"
    auth = (client_config["consumer_key"], client_config["consumer_secret"])
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.request(
                method=method,
                url=url,
                auth=auth,
                json=data,
                params=params
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"WooCommerce API error: {e.response.text}"
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=503,
                detail=f"Failed to connect to WooCommerce: {str(e)}"
            )

# ============== VARIATION ENDPOINTS ==============

@router.get("/product/{product_id}")
async def get_product_variations(
    product_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get all variations for a product"""
    company_id = current_user["company_id"]
    
    # Verify product exists
    product = await db.products.find_one({
        "id": product_id,
        "company_id": company_id
    })
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Get variations
    variations = await db.product_variations.find(
        {"parent_product_id": product_id, "company_id": company_id},
        {"_id": 0}
    ).to_list(1000)
    
    return {
        "product_id": product_id,
        "product_name": product.get("name"),
        "product_type": product.get("product_type", "simple"),
        "variations": variations,
        "total_variations": len(variations)
    }

@router.get("/{variation_id}")
async def get_variation(
    variation_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get single variation details"""
    variation = await db.product_variations.find_one(
        {"id": variation_id, "company_id": current_user["company_id"]},
        {"_id": 0}
    )
    if not variation:
        raise HTTPException(status_code=404, detail="Variation not found")
    return variation

@router.post("")
async def create_variation(
    data: VariationCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new product variation"""
    company_id = current_user["company_id"]
    
    # Verify parent product exists
    product = await db.products.find_one({
        "id": data.parent_product_id,
        "company_id": company_id
    })
    if not product:
        raise HTTPException(status_code=404, detail="Parent product not found")
    
    # Check SKU uniqueness
    existing = await db.product_variations.find_one({
        "sku": data.sku,
        "company_id": company_id
    })
    if existing:
        raise HTTPException(status_code=400, detail="SKU already exists")
    
    variation_id = generate_id()
    
    # Build attribute display name
    attr_display = " - ".join([f"{a.option}" for a in data.attributes])
    variation_name = f"{product['name']} - {attr_display}"
    
    variation = {
        "id": variation_id,
        "company_id": company_id,
        "parent_product_id": data.parent_product_id,
        "parent_product_name": product["name"],
        "variation_name": variation_name,
        "woo_variation_id": None,
        "sku": data.sku,
        "attributes": [a.model_dump() for a in data.attributes],
        "cost_price": data.cost_price,
        "regular_price": data.regular_price,
        "sale_price": data.sale_price,
        "selling_price": data.sale_price if data.sale_price else data.regular_price,
        "stock_quantity": data.stock_quantity,
        "weight": data.weight,
        "manage_stock": True,
        "created_at": get_current_timestamp(),
        "updated_at": get_current_timestamp()
    }
    
    await db.product_variations.insert_one(variation)
    
    # Update parent product type to variable
    await db.products.update_one(
        {"id": data.parent_product_id},
        {"$set": {"product_type": "variable", "updated_at": get_current_timestamp()}}
    )
    
    return {"id": variation_id, "variation_name": variation_name, "message": "Variation created successfully"}

@router.put("/{variation_id}")
async def update_variation(
    variation_id: str,
    data: VariationUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update a product variation"""
    company_id = current_user["company_id"]
    
    existing = await db.product_variations.find_one({
        "id": variation_id,
        "company_id": company_id
    })
    if not existing:
        raise HTTPException(status_code=404, detail="Variation not found")
    
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    
    # Recalculate selling price if prices changed
    if "sale_price" in update_data or "regular_price" in update_data:
        sale = update_data.get("sale_price", existing.get("sale_price"))
        regular = update_data.get("regular_price", existing.get("regular_price"))
        update_data["selling_price"] = sale if sale else regular
    
    update_data["updated_at"] = get_current_timestamp()
    
    await db.product_variations.update_one(
        {"id": variation_id},
        {"$set": update_data}
    )
    
    return {"message": "Variation updated successfully"}

@router.delete("/{variation_id}")
async def delete_variation(
    variation_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a product variation"""
    company_id = current_user["company_id"]
    
    variation = await db.product_variations.find_one({
        "id": variation_id,
        "company_id": company_id
    })
    if not variation:
        raise HTTPException(status_code=404, detail="Variation not found")
    
    await db.product_variations.delete_one({"id": variation_id})
    
    # Check if parent still has variations
    remaining = await db.product_variations.count_documents({
        "parent_product_id": variation["parent_product_id"],
        "company_id": company_id
    })
    
    # If no variations left, change product type back to simple
    if remaining == 0:
        await db.products.update_one(
            {"id": variation["parent_product_id"]},
            {"$set": {"product_type": "simple", "updated_at": get_current_timestamp()}}
        )
    
    return {"message": "Variation deleted successfully"}

# ============== WOOCOMMERCE SYNC ENDPOINTS ==============

@router.post("/sync/product/{product_id}")
async def sync_product_variations_from_woo(
    product_id: str,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """Sync variations for a specific product from WooCommerce"""
    company_id = current_user["company_id"]
    
    # Get product
    product = await db.products.find_one({
        "id": product_id,
        "company_id": company_id
    })
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    if not product.get("woo_product_id"):
        raise HTTPException(status_code=400, detail="Product not linked to WooCommerce")
    
    # Sync in background
    background_tasks.add_task(
        _sync_variations_task,
        company_id,
        product_id,
        product["woo_product_id"],
        current_user["user_id"]
    )
    
    return {"message": "Variation sync started", "product_id": product_id}

@router.post("/sync/all")
async def sync_all_variations_from_woo(
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """Sync all variable product variations from WooCommerce"""
    company_id = current_user["company_id"]
    
    # Create sync log
    sync_id = generate_id()
    sync_log = {
        "id": sync_id,
        "company_id": company_id,
        "sync_type": "variations",
        "status": "in_progress",
        "started_at": get_current_timestamp(),
        "completed_at": None,
        "products_processed": 0,
        "variations_synced": 0,
        "errors": []
    }
    await db.woo_sync_logs.insert_one(sync_log)
    
    # Run sync in background
    background_tasks.add_task(
        _sync_all_variations_task,
        company_id,
        sync_id,
        current_user["user_id"]
    )
    
    return {"message": "Full variation sync started", "sync_id": sync_id}

async def _sync_variations_task(company_id: str, product_id: str, woo_product_id: str, user_id: str):
    """Background task to sync variations for a single product"""
    try:
        client = await get_woo_client(company_id)
        
        # Fetch variations from WooCommerce
        variations = await woo_request(
            client, "GET", 
            f"products/{woo_product_id}/variations",
            params={"per_page": 100}
        )
        
        if not variations:
            # Product might be simple, not variable
            return
        
        # Update product type to variable
        await db.products.update_one(
            {"id": product_id},
            {"$set": {"product_type": "variable", "updated_at": get_current_timestamp()}}
        )
        
        # Get parent product
        product = await db.products.find_one({"id": product_id})
        
        for woo_var in variations:
            woo_var_id = str(woo_var["id"])
            
            # Build attributes list
            attributes = []
            for attr in woo_var.get("attributes", []):
                attributes.append({
                    "name": attr.get("name", ""),
                    "option": attr.get("option", "")
                })
            
            # Build variation name
            attr_display = " - ".join([a["option"] for a in attributes if a["option"]])
            variation_name = f"{product['name']} - {attr_display}" if attr_display else product["name"]
            
            # Get prices
            regular_price = float(woo_var.get("regular_price") or woo_var.get("price") or 0)
            sale_price = float(woo_var.get("sale_price") or 0) if woo_var.get("sale_price") else None
            selling_price = sale_price if sale_price else regular_price
            
            variation_data = {
                "company_id": company_id,
                "parent_product_id": product_id,
                "parent_product_name": product["name"],
                "variation_name": variation_name,
                "woo_variation_id": woo_var_id,
                "sku": woo_var.get("sku") or f"{product.get('sku', 'VAR')}-{woo_var_id}",
                "attributes": attributes,
                "cost_price": regular_price * 0.7,  # Estimate cost at 70%
                "regular_price": regular_price,
                "sale_price": sale_price,
                "selling_price": selling_price,
                "stock_quantity": woo_var.get("stock_quantity") or 0,
                "weight": float(woo_var.get("weight") or 0) if woo_var.get("weight") else None,
                "manage_stock": woo_var.get("manage_stock", True),
                "updated_at": get_current_timestamp()
            }
            
            # Check if variation exists
            existing = await db.product_variations.find_one({
                "company_id": company_id,
                "woo_variation_id": woo_var_id
            })
            
            if existing:
                await db.product_variations.update_one(
                    {"id": existing["id"]},
                    {"$set": variation_data}
                )
            else:
                variation_data["id"] = generate_id()
                variation_data["created_at"] = get_current_timestamp()
                await db.product_variations.insert_one(variation_data)
    
    except Exception as e:
        print(f"Error syncing variations for product {product_id}: {e}")

async def _sync_all_variations_task(company_id: str, sync_id: str, user_id: str):
    """Background task to sync all variable product variations"""
    products_processed = 0
    variations_synced = 0
    errors = []
    
    try:
        client = await get_woo_client(company_id)
        
        # Fetch variable products from WooCommerce
        page = 1
        while True:
            woo_products = await woo_request(
                client, "GET", "products",
                params={"page": page, "per_page": 100, "type": "variable"}
            )
            
            if not woo_products:
                break
            
            for woo_product in woo_products:
                products_processed += 1
                woo_product_id = str(woo_product["id"])
                
                try:
                    # Find or create product in ERP
                    product = await db.products.find_one({
                        "company_id": company_id,
                        "woo_product_id": woo_product_id
                    })
                    
                    if not product:
                        # Create product
                        product_id = generate_id()
                        product = {
                            "id": product_id,
                            "company_id": company_id,
                            "woo_product_id": woo_product_id,
                            "sku": woo_product.get("sku") or f"WOO-{woo_product_id}",
                            "name": woo_product["name"],
                            "description": woo_product.get("description", ""),
                            "short_description": woo_product.get("short_description", ""),
                            "product_type": "variable",
                            "category": woo_product["categories"][0]["name"] if woo_product.get("categories") else None,
                            "cost_price": 0,
                            "regular_price": float(woo_product.get("price") or 0),
                            "selling_price": float(woo_product.get("price") or 0),
                            "stock_quantity": 0,  # Will be sum of variations
                            "low_stock_threshold": 10,
                            "visibility": "public" if woo_product.get("status") == "publish" else "private",
                            "manage_stock": False,  # Stock managed at variation level
                            "created_at": get_current_timestamp(),
                            "updated_at": get_current_timestamp()
                        }
                        await db.products.insert_one(product)
                    else:
                        product_id = product["id"]
                        # Update product type
                        await db.products.update_one(
                            {"id": product_id},
                            {"$set": {"product_type": "variable", "updated_at": get_current_timestamp()}}
                        )
                    
                    # Fetch variations for this product
                    woo_variations = await woo_request(
                        client, "GET",
                        f"products/{woo_product_id}/variations",
                        params={"per_page": 100}
                    )
                    
                    for woo_var in woo_variations:
                        woo_var_id = str(woo_var["id"])
                        
                        # Build attributes
                        attributes = []
                        for attr in woo_var.get("attributes", []):
                            attributes.append({
                                "name": attr.get("name", ""),
                                "option": attr.get("option", "")
                            })
                        
                        # Build variation name
                        attr_display = " - ".join([a["option"] for a in attributes if a["option"]])
                        variation_name = f"{product['name']} - {attr_display}" if attr_display else product["name"]
                        
                        # Get prices
                        regular_price = float(woo_var.get("regular_price") or woo_var.get("price") or 0)
                        sale_price = float(woo_var.get("sale_price") or 0) if woo_var.get("sale_price") else None
                        
                        variation_data = {
                            "company_id": company_id,
                            "parent_product_id": product_id,
                            "parent_product_name": product["name"],
                            "variation_name": variation_name,
                            "woo_variation_id": woo_var_id,
                            "sku": woo_var.get("sku") or f"{product.get('sku', 'VAR')}-{woo_var_id}",
                            "attributes": attributes,
                            "cost_price": regular_price * 0.7,
                            "regular_price": regular_price,
                            "sale_price": sale_price,
                            "selling_price": sale_price if sale_price else regular_price,
                            "stock_quantity": woo_var.get("stock_quantity") or 0,
                            "weight": float(woo_var.get("weight") or 0) if woo_var.get("weight") else None,
                            "manage_stock": woo_var.get("manage_stock", True),
                            "updated_at": get_current_timestamp()
                        }
                        
                        # Upsert variation
                        existing = await db.product_variations.find_one({
                            "company_id": company_id,
                            "woo_variation_id": woo_var_id
                        })
                        
                        if existing:
                            await db.product_variations.update_one(
                                {"id": existing["id"]},
                                {"$set": variation_data}
                            )
                        else:
                            variation_data["id"] = generate_id()
                            variation_data["created_at"] = get_current_timestamp()
                            await db.product_variations.insert_one(variation_data)
                        
                        variations_synced += 1
                    
                    # Update parent product total stock
                    total_stock = sum(v.get("stock_quantity", 0) for v in woo_variations)
                    await db.products.update_one(
                        {"id": product_id},
                        {"$set": {"stock_quantity": total_stock}}
                    )
                    
                except Exception as e:
                    errors.append({
                        "woo_product_id": woo_product_id,
                        "name": woo_product.get("name"),
                        "error": str(e)
                    })
            
            page += 1
        
        # Update sync log
        await db.woo_sync_logs.update_one(
            {"id": sync_id},
            {"$set": {
                "status": "completed",
                "completed_at": get_current_timestamp(),
                "products_processed": products_processed,
                "variations_synced": variations_synced,
                "errors": errors
            }}
        )
        
    except Exception as e:
        await db.woo_sync_logs.update_one(
            {"id": sync_id},
            {"$set": {
                "status": "failed",
                "completed_at": get_current_timestamp(),
                "errors": [{"error": str(e)}]
            }}
        )

# ============== STOCK SYNC ==============

@router.put("/{variation_id}/sync-stock")
async def sync_variation_stock_to_woo(
    variation_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Sync single variation stock to WooCommerce"""
    company_id = current_user["company_id"]
    
    variation = await db.product_variations.find_one({
        "id": variation_id,
        "company_id": company_id
    })
    if not variation:
        raise HTTPException(status_code=404, detail="Variation not found")
    
    if not variation.get("woo_variation_id"):
        raise HTTPException(status_code=400, detail="Variation not linked to WooCommerce")
    
    # Get parent product to get woo_product_id
    product = await db.products.find_one({"id": variation["parent_product_id"]})
    if not product or not product.get("woo_product_id"):
        raise HTTPException(status_code=400, detail="Parent product not linked to WooCommerce")
    
    client = await get_woo_client(company_id)
    
    result = await woo_request(
        client, "PUT",
        f"products/{product['woo_product_id']}/variations/{variation['woo_variation_id']}",
        data={
            "stock_quantity": variation["stock_quantity"],
            "manage_stock": True
        }
    )
    
    return {
        "message": "Stock synced to WooCommerce",
        "variation_id": variation_id,
        "woo_stock": result.get("stock_quantity")
    }

async def sync_variation_stock_to_woo_internal(company_id: str, variation_id: str):
    """Internal function to sync variation stock (for background tasks)"""
    try:
        variation = await db.product_variations.find_one({
            "id": variation_id,
            "company_id": company_id
        })
        if not variation or not variation.get("woo_variation_id"):
            return
        
        product = await db.products.find_one({"id": variation["parent_product_id"]})
        if not product or not product.get("woo_product_id"):
            return
        
        client = await get_woo_client(company_id)
        
        await woo_request(
            client, "PUT",
            f"products/{product['woo_product_id']}/variations/{variation['woo_variation_id']}",
            data={
                "stock_quantity": variation["stock_quantity"],
                "manage_stock": True
            }
        )
    except Exception as e:
        print(f"Error syncing variation stock: {e}")

# ============== SEARCH/LOOKUP ==============

@router.get("/search")
async def search_variations(
    query: Optional[str] = None,
    parent_product_id: Optional[str] = None,
    attribute_name: Optional[str] = None,
    attribute_value: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Search variations by various criteria"""
    company_id = current_user["company_id"]
    
    search_query = {"company_id": company_id}
    
    if parent_product_id:
        search_query["parent_product_id"] = parent_product_id
    
    if query:
        search_query["$or"] = [
            {"variation_name": {"$regex": query, "$options": "i"}},
            {"sku": {"$regex": query, "$options": "i"}},
            {"parent_product_name": {"$regex": query, "$options": "i"}}
        ]
    
    if attribute_name and attribute_value:
        search_query["attributes"] = {
            "$elemMatch": {
                "name": {"$regex": attribute_name, "$options": "i"},
                "option": {"$regex": attribute_value, "$options": "i"}
            }
        }
    
    variations = await db.product_variations.find(
        search_query,
        {"_id": 0}
    ).sort("variation_name", 1).to_list(500)
    
    return variations

@router.get("/by-sku/{sku}")
async def get_variation_by_sku(
    sku: str,
    current_user: dict = Depends(get_current_user)
):
    """Get variation by SKU"""
    variation = await db.product_variations.find_one(
        {"sku": sku, "company_id": current_user["company_id"]},
        {"_id": 0}
    )
    if not variation:
        raise HTTPException(status_code=404, detail="Variation not found")
    return variation

# ============== ATTRIBUTES HELPER ==============

@router.get("/attributes/list")
async def get_variation_attributes(
    current_user: dict = Depends(get_current_user)
):
    """Get list of all unique attribute names and values used in variations"""
    company_id = current_user["company_id"]
    
    variations = await db.product_variations.find(
        {"company_id": company_id},
        {"attributes": 1}
    ).to_list(10000)
    
    attributes_map = {}
    
    for var in variations:
        for attr in var.get("attributes", []):
            name = attr.get("name", "")
            option = attr.get("option", "")
            if name:
                if name not in attributes_map:
                    attributes_map[name] = set()
                if option:
                    attributes_map[name].add(option)
    
    # Convert to list format
    result = []
    for name, options in attributes_map.items():
        result.append({
            "name": name,
            "options": sorted(list(options))
        })
    
    return result
