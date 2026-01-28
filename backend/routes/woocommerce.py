"""
WooCommerce Integration Router
Two-way sync for products, orders, customers, and stock
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Optional, List
from datetime import datetime, timezone
import httpx
import base64
import asyncio

from utils.helpers import serialize_doc, generate_id, get_current_timestamp
from utils.auth import get_current_user

router = APIRouter(prefix="/woocommerce", tags=["WooCommerce"])

# Database will be injected from main app
db = None

def set_db(database):
    global db
    db = database

def set_auth_dependency(auth_func):
    # Not needed with shared auth module
    pass

# ============== WOOCOMMERCE CLIENT ==============

class WooCommerceClient:
    """WooCommerce REST API Client"""
    
    def __init__(self, store_url: str, consumer_key: str, consumer_secret: str):
        self.store_url = store_url.rstrip('/')
        self.auth = (consumer_key, consumer_secret)
        self.api_url = f"{self.store_url}/wp-json/wc/v3"
    
    async def _request(self, method: str, endpoint: str, data: dict = None, params: dict = None):
        """Make authenticated request to WooCommerce API"""
        url = f"{self.api_url}/{endpoint}"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    auth=self.auth,
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
    
    async def get(self, endpoint: str, params: dict = None):
        return await self._request("GET", endpoint, params=params)
    
    async def post(self, endpoint: str, data: dict):
        return await self._request("POST", endpoint, data=data)
    
    async def put(self, endpoint: str, data: dict):
        return await self._request("PUT", endpoint, data=data)
    
    async def delete(self, endpoint: str):
        return await self._request("DELETE", endpoint)

async def get_woo_client(company_id: str) -> WooCommerceClient:
    """Get WooCommerce client for a company"""
    company = await db.companies.find_one({"id": company_id})
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    woo_settings = company.get("woo_settings")
    if not woo_settings or not woo_settings.get("enabled"):
        raise HTTPException(status_code=400, detail="WooCommerce integration not configured or disabled")
    
    return WooCommerceClient(
        store_url=woo_settings["store_url"],
        consumer_key=woo_settings["consumer_key"],
        consumer_secret=woo_settings["consumer_secret"]
    )

# ============== CONNECTION TEST ==============

@router.get("/test-connection")
async def test_connection(current_user: dict = Depends(lambda: get_current_user)):
    """Test WooCommerce connection"""
    try:
        client = await get_woo_client(current_user["company_id"])
        
        # Try to get store info
        result = await client.get("system_status")
        
        return {
            "success": True,
            "message": "Connection successful",
            "store_info": {
                "wc_version": result.get("environment", {}).get("version"),
                "wp_version": result.get("environment", {}).get("wp_version"),
                "multisite": result.get("environment", {}).get("wp_multisite")
            }
        }
    except HTTPException as e:
        return {
            "success": False,
            "message": e.detail
        }
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }

# ============== PRODUCT SYNC ==============

@router.get("/products")
async def get_woo_products(
    page: int = 1,
    per_page: int = 20,
    current_user: dict = Depends(lambda: get_current_user)
):
    """Get products from WooCommerce"""
    client = await get_woo_client(current_user["company_id"])
    
    products = await client.get("products", params={
        "page": page,
        "per_page": per_page
    })
    
    return {
        "products": products,
        "page": page,
        "per_page": per_page
    }

@router.post("/products/sync")
async def sync_products(
    background_tasks: BackgroundTasks,
    direction: str = "both",  # woo_to_erp, erp_to_woo, both
    current_user: dict = Depends(lambda: get_current_user)
):
    """Sync products between WooCommerce and ERP"""
    company_id = current_user["company_id"]
    
    # Create sync record
    sync_id = generate_id()
    sync_record = {
        "id": sync_id,
        "company_id": company_id,
        "sync_type": "products",
        "direction": direction,
        "status": "in_progress",
        "started_at": get_current_timestamp(),
        "completed_at": None,
        "items_processed": 0,
        "items_created": 0,
        "items_updated": 0,
        "errors": []
    }
    await db.woo_sync_logs.insert_one(sync_record)
    
    # Run sync in background
    background_tasks.add_task(
        _sync_products_task,
        company_id,
        sync_id,
        direction,
        current_user["user_id"]
    )
    
    return {
        "message": "Product sync started",
        "sync_id": sync_id
    }

async def _sync_products_task(company_id: str, sync_id: str, direction: str, user_id: str):
    """Background task to sync products"""
    try:
        client = await get_woo_client(company_id)
        items_processed = 0
        items_created = 0
        items_updated = 0
        errors = []
        
        if direction in ["woo_to_erp", "both"]:
            # Fetch all products from WooCommerce
            page = 1
            while True:
                woo_products = await client.get("products", params={
                    "page": page,
                    "per_page": 100
                })
                
                if not woo_products:
                    break
                
                for woo_product in woo_products:
                    items_processed += 1
                    try:
                        # Check if product exists by WooCommerce ID
                        existing = await db.products.find_one({
                            "company_id": company_id,
                            "woo_product_id": str(woo_product["id"])
                        })
                        
                        product_data = {
                            "woo_product_id": str(woo_product["id"]),
                            "sku": woo_product.get("sku") or f"WOO-{woo_product['id']}",
                            "name": woo_product["name"],
                            "description": woo_product.get("description", ""),
                            "category": woo_product["categories"][0]["name"] if woo_product.get("categories") else None,
                            "cost_price": float(woo_product.get("regular_price") or 0) * 0.7,  # Estimate cost
                            "selling_price": float(woo_product.get("regular_price") or woo_product.get("price") or 0),
                            "stock_quantity": woo_product.get("stock_quantity") or 0,
                            "updated_at": get_current_timestamp()
                        }
                        
                        if existing:
                            await db.products.update_one(
                                {"id": existing["id"]},
                                {"$set": product_data}
                            )
                            items_updated += 1
                        else:
                            product_data["id"] = generate_id()
                            product_data["company_id"] = company_id
                            product_data["low_stock_threshold"] = 10
                            product_data["created_at"] = get_current_timestamp()
                            await db.products.insert_one(product_data)
                            items_created += 1
                            
                    except Exception as e:
                        errors.append({
                            "woo_id": woo_product["id"],
                            "name": woo_product["name"],
                            "error": str(e)
                        })
                
                page += 1
        
        if direction in ["erp_to_woo", "both"]:
            # Push ERP products to WooCommerce
            erp_products = await db.products.find(
                {"company_id": company_id, "woo_product_id": None}
            ).to_list(1000)
            
            for erp_product in erp_products:
                items_processed += 1
                try:
                    woo_data = {
                        "name": erp_product["name"],
                        "sku": erp_product["sku"],
                        "regular_price": str(erp_product["selling_price"]),
                        "description": erp_product.get("description", ""),
                        "manage_stock": True,
                        "stock_quantity": erp_product["stock_quantity"]
                    }
                    
                    result = await client.post("products", woo_data)
                    
                    # Update ERP product with WooCommerce ID
                    await db.products.update_one(
                        {"id": erp_product["id"]},
                        {"$set": {
                            "woo_product_id": str(result["id"]),
                            "updated_at": get_current_timestamp()
                        }}
                    )
                    items_created += 1
                    
                except Exception as e:
                    errors.append({
                        "erp_id": erp_product["id"],
                        "name": erp_product["name"],
                        "error": str(e)
                    })
        
        # Update sync record
        await db.woo_sync_logs.update_one(
            {"id": sync_id},
            {"$set": {
                "status": "completed",
                "completed_at": get_current_timestamp(),
                "items_processed": items_processed,
                "items_created": items_created,
                "items_updated": items_updated,
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

@router.put("/products/{product_id}/sync-stock")
async def sync_product_stock(
    product_id: str,
    current_user: dict = Depends(lambda: get_current_user)
):
    """Sync single product stock to WooCommerce"""
    company_id = current_user["company_id"]
    
    product = await db.products.find_one({
        "id": product_id,
        "company_id": company_id
    })
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    if not product.get("woo_product_id"):
        raise HTTPException(status_code=400, detail="Product not linked to WooCommerce")
    
    client = await get_woo_client(company_id)
    
    result = await client.put(f"products/{product['woo_product_id']}", {
        "stock_quantity": product["stock_quantity"],
        "manage_stock": True
    })
    
    return {
        "message": "Stock synced successfully",
        "woo_stock": result.get("stock_quantity")
    }

# ============== ORDER SYNC ==============

@router.get("/orders")
async def get_woo_orders(
    page: int = 1,
    per_page: int = 20,
    status: Optional[str] = None,
    current_user: dict = Depends(lambda: get_current_user)
):
    """Get orders from WooCommerce"""
    client = await get_woo_client(current_user["company_id"])
    
    params = {"page": page, "per_page": per_page}
    if status:
        params["status"] = status
    
    orders = await client.get("orders", params=params)
    
    return {
        "orders": orders,
        "page": page,
        "per_page": per_page
    }

@router.post("/orders/sync")
async def sync_orders(
    background_tasks: BackgroundTasks,
    since_date: Optional[str] = None,
    current_user: dict = Depends(lambda: get_current_user)
):
    """Sync orders from WooCommerce to ERP"""
    company_id = current_user["company_id"]
    
    sync_id = generate_id()
    sync_record = {
        "id": sync_id,
        "company_id": company_id,
        "sync_type": "orders",
        "direction": "woo_to_erp",
        "status": "in_progress",
        "started_at": get_current_timestamp(),
        "completed_at": None,
        "items_processed": 0,
        "items_created": 0,
        "items_updated": 0,
        "errors": []
    }
    await db.woo_sync_logs.insert_one(sync_record)
    
    background_tasks.add_task(
        _sync_orders_task,
        company_id,
        sync_id,
        since_date,
        current_user["user_id"]
    )
    
    return {
        "message": "Order sync started",
        "sync_id": sync_id
    }

async def _sync_orders_task(company_id: str, sync_id: str, since_date: str, user_id: str):
    """Background task to sync orders"""
    try:
        client = await get_woo_client(company_id)
        items_processed = 0
        items_created = 0
        items_updated = 0
        errors = []
        
        page = 1
        while True:
            params = {"page": page, "per_page": 100, "order": "asc"}
            if since_date:
                params["after"] = since_date
            
            woo_orders = await client.get("orders", params=params)
            
            if not woo_orders:
                break
            
            for woo_order in woo_orders:
                items_processed += 1
                try:
                    # Check if order exists
                    existing = await db.sales_orders.find_one({
                        "company_id": company_id,
                        "woo_order_id": str(woo_order["id"])
                    })
                    
                    if existing:
                        # Update status if changed
                        woo_status_map = {
                            "pending": "pending",
                            "processing": "processing",
                            "on-hold": "pending",
                            "completed": "completed",
                            "cancelled": "cancelled",
                            "refunded": "returned"
                        }
                        
                        new_status = woo_status_map.get(woo_order["status"], "pending")
                        if existing["status"] != new_status:
                            await db.sales_orders.update_one(
                                {"id": existing["id"]},
                                {"$set": {
                                    "status": new_status,
                                    "updated_at": get_current_timestamp()
                                }}
                            )
                            items_updated += 1
                    else:
                        # Create or find customer
                        customer_id = await _get_or_create_woo_customer(
                            company_id,
                            woo_order["billing"],
                            woo_order.get("customer_id")
                        )
                        
                        # Create order items
                        order_items = []
                        for line_item in woo_order.get("line_items", []):
                            # Try to find matching product
                            product = await db.products.find_one({
                                "company_id": company_id,
                                "$or": [
                                    {"woo_product_id": str(line_item.get("product_id"))},
                                    {"sku": line_item.get("sku")}
                                ]
                            })
                            
                            order_items.append({
                                "product_id": product["id"] if product else None,
                                "product_name": line_item["name"],
                                "sku": line_item.get("sku", ""),
                                "quantity": line_item["quantity"],
                                "unit_price": float(line_item["price"]),
                                "total": float(line_item["total"])
                            })
                        
                        # Map WooCommerce payment status
                        payment_status = "unpaid"
                        if woo_order.get("date_paid"):
                            payment_status = "paid"
                        elif woo_order.get("status") == "on-hold":
                            payment_status = "pending"
                        
                        # Create sales order
                        order_id = generate_id()
                        sales_order = {
                            "id": order_id,
                            "order_number": f"WOO-{woo_order['id']}",
                            "company_id": company_id,
                            "customer_id": customer_id,
                            "customer_name": f"{woo_order['billing']['first_name']} {woo_order['billing']['last_name']}",
                            "items": order_items,
                            "subtotal": float(woo_order.get("subtotal", 0)),
                            "discount": float(woo_order.get("discount_total", 0)),
                            "tax": float(woo_order.get("total_tax", 0)),
                            "total": float(woo_order["total"]),
                            "status": woo_status_map.get(woo_order["status"], "pending"),
                            "payment_status": payment_status,
                            "paid_amount": float(woo_order["total"]) if payment_status == "paid" else 0,
                            "notes": woo_order.get("customer_note"),
                            "woo_order_id": str(woo_order["id"]),
                            "created_by": user_id,
                            "created_at": woo_order.get("date_created", get_current_timestamp()),
                            "updated_at": get_current_timestamp()
                        }
                        await db.sales_orders.insert_one(sales_order)
                        items_created += 1
                        
                        # Create accounting entry
                        await db.accounting_entries.insert_one({
                            "id": generate_id(),
                            "company_id": company_id,
                            "entry_type": "income",
                            "category": "Sales",
                            "amount": float(woo_order["total"]),
                            "description": f"WooCommerce Order {woo_order['id']}",
                            "reference_type": "sales_order",
                            "reference_id": order_id,
                            "created_by": user_id,
                            "created_at": get_current_timestamp()
                        })
                        
                except Exception as e:
                    errors.append({
                        "woo_id": woo_order["id"],
                        "error": str(e)
                    })
            
            page += 1
        
        await db.woo_sync_logs.update_one(
            {"id": sync_id},
            {"$set": {
                "status": "completed",
                "completed_at": get_current_timestamp(),
                "items_processed": items_processed,
                "items_created": items_created,
                "items_updated": items_updated,
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

async def _get_or_create_woo_customer(company_id: str, billing: dict, woo_customer_id: int) -> str:
    """Get or create customer from WooCommerce order data"""
    # Try to find existing customer
    existing = await db.customers.find_one({
        "company_id": company_id,
        "$or": [
            {"woo_customer_id": str(woo_customer_id)} if woo_customer_id else {},
            {"email": billing.get("email")} if billing.get("email") else {}
        ]
    })
    
    if existing:
        return existing["id"]
    
    # Create new customer
    customer_id = generate_id()
    customer = {
        "id": customer_id,
        "company_id": company_id,
        "name": f"{billing.get('first_name', '')} {billing.get('last_name', '')}".strip() or "WooCommerce Customer",
        "email": billing.get("email"),
        "phone": billing.get("phone"),
        "address": f"{billing.get('address_1', '')} {billing.get('address_2', '')}, {billing.get('city', '')}, {billing.get('state', '')} {billing.get('postcode', '')}, {billing.get('country', '')}",
        "woo_customer_id": str(woo_customer_id) if woo_customer_id else None,
        "created_at": get_current_timestamp(),
        "updated_at": get_current_timestamp()
    }
    await db.customers.insert_one(customer)
    
    return customer_id

# ============== CUSTOMER SYNC ==============

@router.post("/customers/sync")
async def sync_customers(
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(lambda: get_current_user)
):
    """Sync customers from WooCommerce"""
    company_id = current_user["company_id"]
    
    sync_id = generate_id()
    sync_record = {
        "id": sync_id,
        "company_id": company_id,
        "sync_type": "customers",
        "direction": "woo_to_erp",
        "status": "in_progress",
        "started_at": get_current_timestamp(),
        "completed_at": None,
        "items_processed": 0,
        "items_created": 0,
        "items_updated": 0,
        "errors": []
    }
    await db.woo_sync_logs.insert_one(sync_record)
    
    background_tasks.add_task(
        _sync_customers_task,
        company_id,
        sync_id
    )
    
    return {
        "message": "Customer sync started",
        "sync_id": sync_id
    }

async def _sync_customers_task(company_id: str, sync_id: str):
    """Background task to sync customers"""
    try:
        client = await get_woo_client(company_id)
        items_processed = 0
        items_created = 0
        items_updated = 0
        errors = []
        
        page = 1
        while True:
            woo_customers = await client.get("customers", params={
                "page": page,
                "per_page": 100
            })
            
            if not woo_customers:
                break
            
            for woo_customer in woo_customers:
                items_processed += 1
                try:
                    existing = await db.customers.find_one({
                        "company_id": company_id,
                        "woo_customer_id": str(woo_customer["id"])
                    })
                    
                    customer_data = {
                        "name": f"{woo_customer.get('first_name', '')} {woo_customer.get('last_name', '')}".strip() or woo_customer.get("username", "Customer"),
                        "email": woo_customer.get("email"),
                        "phone": woo_customer.get("billing", {}).get("phone"),
                        "address": f"{woo_customer.get('billing', {}).get('address_1', '')} {woo_customer.get('billing', {}).get('city', '')}",
                        "woo_customer_id": str(woo_customer["id"]),
                        "updated_at": get_current_timestamp()
                    }
                    
                    if existing:
                        await db.customers.update_one(
                            {"id": existing["id"]},
                            {"$set": customer_data}
                        )
                        items_updated += 1
                    else:
                        customer_data["id"] = generate_id()
                        customer_data["company_id"] = company_id
                        customer_data["created_at"] = get_current_timestamp()
                        await db.customers.insert_one(customer_data)
                        items_created += 1
                        
                except Exception as e:
                    errors.append({
                        "woo_id": woo_customer["id"],
                        "error": str(e)
                    })
            
            page += 1
        
        await db.woo_sync_logs.update_one(
            {"id": sync_id},
            {"$set": {
                "status": "completed",
                "completed_at": get_current_timestamp(),
                "items_processed": items_processed,
                "items_created": items_created,
                "items_updated": items_updated,
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

# ============== SYNC LOGS ==============

@router.get("/sync-logs")
async def get_sync_logs(
    sync_type: Optional[str] = None,
    limit: int = 50,
    current_user: dict = Depends(lambda: get_current_user)
):
    """Get sync operation logs"""
    query = {"company_id": current_user["company_id"]}
    if sync_type:
        query["sync_type"] = sync_type
    
    logs = await db.woo_sync_logs.find(
        query,
        {"_id": 0}
    ).sort("started_at", -1).to_list(limit)
    
    return logs

@router.get("/sync-logs/{sync_id}")
async def get_sync_log(sync_id: str, current_user: dict = Depends(lambda: get_current_user)):
    """Get specific sync operation details"""
    log = await db.woo_sync_logs.find_one(
        {"id": sync_id, "company_id": current_user["company_id"]},
        {"_id": 0}
    )
    if not log:
        raise HTTPException(status_code=404, detail="Sync log not found")
    
    return log

# ============== FULL SYNC ==============

@router.post("/full-sync")
async def full_sync(
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(lambda: get_current_user)
):
    """Perform full sync of all data"""
    company_id = current_user["company_id"]
    
    sync_id = generate_id()
    sync_record = {
        "id": sync_id,
        "company_id": company_id,
        "sync_type": "full",
        "direction": "both",
        "status": "in_progress",
        "started_at": get_current_timestamp(),
        "completed_at": None,
        "sub_syncs": [],
        "errors": []
    }
    await db.woo_sync_logs.insert_one(sync_record)
    
    background_tasks.add_task(
        _full_sync_task,
        company_id,
        sync_id,
        current_user["user_id"]
    )
    
    return {
        "message": "Full sync started",
        "sync_id": sync_id
    }

async def _full_sync_task(company_id: str, sync_id: str, user_id: str):
    """Background task for full sync"""
    sub_syncs = []
    errors = []
    
    try:
        # Sync products
        try:
            await _sync_products_task(company_id, f"{sync_id}-products", "both", user_id)
            sub_syncs.append({"type": "products", "status": "completed"})
        except Exception as e:
            errors.append({"type": "products", "error": str(e)})
            sub_syncs.append({"type": "products", "status": "failed"})
        
        # Sync customers
        try:
            await _sync_customers_task(company_id, f"{sync_id}-customers")
            sub_syncs.append({"type": "customers", "status": "completed"})
        except Exception as e:
            errors.append({"type": "customers", "error": str(e)})
            sub_syncs.append({"type": "customers", "status": "failed"})
        
        # Sync orders
        try:
            await _sync_orders_task(company_id, f"{sync_id}-orders", None, user_id)
            sub_syncs.append({"type": "orders", "status": "completed"})
        except Exception as e:
            errors.append({"type": "orders", "error": str(e)})
            sub_syncs.append({"type": "orders", "status": "failed"})
        
        status = "completed" if not errors else "completed_with_errors"
        
        await db.woo_sync_logs.update_one(
            {"id": sync_id},
            {"$set": {
                "status": status,
                "completed_at": get_current_timestamp(),
                "sub_syncs": sub_syncs,
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
