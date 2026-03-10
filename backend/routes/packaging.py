"""
Packaging Rules Router
Manage packaging materials and rules for products
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone
import uuid
import jwt
import os

# Database will be set by server.py
db = None

router = APIRouter(prefix="/packaging", tags=["Packaging"])
security = HTTPBearer()

JWT_SECRET = os.environ.get('JWT_SECRET', 'erp-secret-key-change-in-production')

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token and return current user"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user = await db.users.find_one({"id": payload["user_id"]}, {"_id": 0, "password": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return {
            "user_id": user["id"],
            "email": user["email"],
            "role": user["role"],
            "company_id": user["company_id"]
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


# Pydantic Models
class PackagingItemCreate(BaseModel):
    name: str
    sku: Optional[str] = None
    description: Optional[str] = None
    stock_quantity: int = 0
    low_stock_threshold: int = 10
    unit: str = "pcs"  # pcs, meters, rolls, etc.


class PackagingItemUpdate(BaseModel):
    name: Optional[str] = None
    sku: Optional[str] = None
    description: Optional[str] = None
    stock_quantity: Optional[int] = None
    low_stock_threshold: Optional[int] = None
    unit: Optional[str] = None


class PackagingRuleItem(BaseModel):
    packaging_item_id: str
    quantity: int = 1


class PackagingRuleCreate(BaseModel):
    product_id: str
    items: List[PackagingRuleItem]
    is_active: bool = True


class PackagingRuleUpdate(BaseModel):
    items: Optional[List[PackagingRuleItem]] = None
    is_active: Optional[bool] = None


# ==================== PACKAGING ITEMS ====================

@router.get("/items")
async def get_packaging_items(current_user: dict = Depends(get_current_user)):
    """Get all packaging items for the company"""
    items = await db.packaging_items.find(
        {"company_id": current_user["company_id"]},
        {"_id": 0}
    ).sort("name", 1).to_list(500)
    return items


@router.get("/items/{item_id}")
async def get_packaging_item(item_id: str, current_user: dict = Depends(get_current_user)):
    """Get a specific packaging item"""
    item = await db.packaging_items.find_one(
        {"id": item_id, "company_id": current_user["company_id"]},
        {"_id": 0}
    )
    if not item:
        raise HTTPException(status_code=404, detail="Packaging item not found")
    return item


@router.post("/items")
async def create_packaging_item(data: PackagingItemCreate, current_user: dict = Depends(get_current_user)):
    """Create a new packaging item"""
    item_id = str(uuid.uuid4())
    
    item = {
        "id": item_id,
        "company_id": current_user["company_id"],
        "name": data.name,
        "sku": data.sku or f"PKG-{item_id[:8].upper()}",
        "description": data.description,
        "stock_quantity": data.stock_quantity,
        "low_stock_threshold": data.low_stock_threshold,
        "unit": data.unit,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.packaging_items.insert_one(item)
    
    # Record initial stock movement if quantity > 0
    if data.stock_quantity > 0:
        await db.packaging_movements.insert_one({
            "id": str(uuid.uuid4()),
            "company_id": current_user["company_id"],
            "packaging_item_id": item_id,
            "type": "in",
            "quantity": data.stock_quantity,
            "reason": "Initial stock",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": current_user["user_id"]
        })
    
    return item


@router.put("/items/{item_id}")
async def update_packaging_item(item_id: str, data: PackagingItemUpdate, current_user: dict = Depends(get_current_user)):
    """Update a packaging item"""
    update_data = {k: v for k, v in data.dict().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.packaging_items.update_one(
        {"id": item_id, "company_id": current_user["company_id"]},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Packaging item not found")
    
    return await db.packaging_items.find_one({"id": item_id}, {"_id": 0})


@router.delete("/items/{item_id}")
async def delete_packaging_item(item_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a packaging item"""
    # Check if item is used in any rules
    rule_count = await db.packaging_rules.count_documents({
        "company_id": current_user["company_id"],
        "items.packaging_item_id": item_id
    })
    
    if rule_count > 0:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot delete. This item is used in {rule_count} packaging rule(s)."
        )
    
    result = await db.packaging_items.delete_one(
        {"id": item_id, "company_id": current_user["company_id"]}
    )
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Packaging item not found")
    
    return {"message": "Packaging item deleted successfully"}


@router.post("/items/{item_id}/adjust-stock")
async def adjust_packaging_stock(
    item_id: str, 
    quantity: int, 
    type: str,  # "in" or "out"
    reason: str = "",
    current_user: dict = Depends(get_current_user)
):
    """Adjust stock for a packaging item"""
    item = await db.packaging_items.find_one(
        {"id": item_id, "company_id": current_user["company_id"]}
    )
    
    if not item:
        raise HTTPException(status_code=404, detail="Packaging item not found")
    
    if type == "in":
        new_stock = item["stock_quantity"] + quantity
    elif type == "out":
        new_stock = item["stock_quantity"] - quantity
        if new_stock < 0:
            raise HTTPException(status_code=400, detail="Insufficient stock")
    else:
        raise HTTPException(status_code=400, detail="Type must be 'in' or 'out'")
    
    # Update stock
    await db.packaging_items.update_one(
        {"id": item_id},
        {"$set": {"stock_quantity": new_stock, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    # Record movement
    await db.packaging_movements.insert_one({
        "id": str(uuid.uuid4()),
        "company_id": current_user["company_id"],
        "packaging_item_id": item_id,
        "type": type,
        "quantity": quantity,
        "reason": reason,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": current_user["user_id"]
    })
    
    return {"message": f"Stock adjusted. New quantity: {new_stock}"}


# ==================== PACKAGING RULES ====================

@router.get("/rules")
async def get_packaging_rules(current_user: dict = Depends(get_current_user)):
    """Get all packaging rules with product and item details"""
    rules = await db.packaging_rules.find(
        {"company_id": current_user["company_id"]},
        {"_id": 0}
    ).to_list(500)
    
    # Enrich with product and item details
    for rule in rules:
        # Get product info
        product = await db.products.find_one({"id": rule["product_id"]}, {"_id": 0, "name": 1, "sku": 1})
        rule["product_name"] = product["name"] if product else "Unknown"
        rule["product_sku"] = product["sku"] if product else ""
        
        # Get item details
        for item in rule.get("items", []):
            pkg_item = await db.packaging_items.find_one(
                {"id": item["packaging_item_id"]}, 
                {"_id": 0, "name": 1, "sku": 1, "stock_quantity": 1, "unit": 1}
            )
            if pkg_item:
                item["item_name"] = pkg_item["name"]
                item["item_sku"] = pkg_item["sku"]
                item["stock_quantity"] = pkg_item["stock_quantity"]
                item["unit"] = pkg_item["unit"]
    
    return rules


@router.get("/rules/product/{product_id}")
async def get_packaging_rule_for_product(product_id: str, current_user: dict = Depends(get_current_user)):
    """Get packaging rule for a specific product"""
    rule = await db.packaging_rules.find_one(
        {"product_id": product_id, "company_id": current_user["company_id"]},
        {"_id": 0}
    )
    
    if rule:
        # Enrich with item details
        for item in rule.get("items", []):
            pkg_item = await db.packaging_items.find_one(
                {"id": item["packaging_item_id"]}, 
                {"_id": 0, "name": 1, "sku": 1, "stock_quantity": 1, "unit": 1}
            )
            if pkg_item:
                item["item_name"] = pkg_item["name"]
                item["item_sku"] = pkg_item["sku"]
                item["stock_quantity"] = pkg_item["stock_quantity"]
                item["unit"] = pkg_item["unit"]
    
    return rule


@router.post("/rules")
async def create_packaging_rule(data: PackagingRuleCreate, current_user: dict = Depends(get_current_user)):
    """Create a packaging rule for a product"""
    # Check if product exists
    product = await db.products.find_one(
        {"id": data.product_id, "company_id": current_user["company_id"]}
    )
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Check if rule already exists for this product
    existing = await db.packaging_rules.find_one({
        "product_id": data.product_id,
        "company_id": current_user["company_id"]
    })
    if existing:
        raise HTTPException(
            status_code=400, 
            detail="Packaging rule already exists for this product. Please update it instead."
        )
    
    # Validate all packaging items exist
    for item in data.items:
        pkg_item = await db.packaging_items.find_one({
            "id": item.packaging_item_id,
            "company_id": current_user["company_id"]
        })
        if not pkg_item:
            raise HTTPException(
                status_code=400, 
                detail=f"Packaging item {item.packaging_item_id} not found"
            )
    
    rule_id = str(uuid.uuid4())
    rule = {
        "id": rule_id,
        "company_id": current_user["company_id"],
        "product_id": data.product_id,
        "items": [{"packaging_item_id": i.packaging_item_id, "quantity": i.quantity} for i in data.items],
        "is_active": data.is_active,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.packaging_rules.insert_one(rule)
    return rule


@router.put("/rules/{rule_id}")
async def update_packaging_rule(rule_id: str, data: PackagingRuleUpdate, current_user: dict = Depends(get_current_user)):
    """Update a packaging rule"""
    update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}
    
    if data.items is not None:
        # Validate all packaging items exist
        for item in data.items:
            pkg_item = await db.packaging_items.find_one({
                "id": item.packaging_item_id,
                "company_id": current_user["company_id"]
            })
            if not pkg_item:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Packaging item {item.packaging_item_id} not found"
                )
        update_data["items"] = [{"packaging_item_id": i.packaging_item_id, "quantity": i.quantity} for i in data.items]
    
    if data.is_active is not None:
        update_data["is_active"] = data.is_active
    
    result = await db.packaging_rules.update_one(
        {"id": rule_id, "company_id": current_user["company_id"]},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Packaging rule not found")
    
    return await db.packaging_rules.find_one({"id": rule_id}, {"_id": 0})


@router.delete("/rules/{rule_id}")
async def delete_packaging_rule(rule_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a packaging rule"""
    result = await db.packaging_rules.delete_one(
        {"id": rule_id, "company_id": current_user["company_id"]}
    )
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Packaging rule not found")
    
    return {"message": "Packaging rule deleted successfully"}


# ==================== PACKAGING DEDUCTION ====================

async def deduct_packaging_for_order(company_id: str, order_items: list, user_id: str):
    """
    Deduct packaging materials based on order items.
    Called when a sales order is processed.
    Returns list of deductions made.
    """
    deductions = []
    
    for order_item in order_items:
        product_id = order_item.get("product_id")
        order_quantity = order_item.get("quantity", 1)
        
        # Find packaging rule for this product
        rule = await db.packaging_rules.find_one({
            "product_id": product_id,
            "company_id": company_id,
            "is_active": True
        })
        
        if not rule:
            continue
        
        # Deduct each packaging item
        for pkg_item in rule.get("items", []):
            packaging_item_id = pkg_item["packaging_item_id"]
            qty_per_product = pkg_item["quantity"]
            total_qty = qty_per_product * order_quantity
            
            # Get current stock
            item = await db.packaging_items.find_one({"id": packaging_item_id})
            if not item:
                continue
            
            new_stock = item["stock_quantity"] - total_qty
            
            # Update stock (allow negative for tracking)
            await db.packaging_items.update_one(
                {"id": packaging_item_id},
                {"$set": {"stock_quantity": new_stock, "updated_at": datetime.now(timezone.utc).isoformat()}}
            )
            
            # Record movement
            await db.packaging_movements.insert_one({
                "id": str(uuid.uuid4()),
                "company_id": company_id,
                "packaging_item_id": packaging_item_id,
                "type": "out",
                "quantity": total_qty,
                "reason": f"Sales order - {order_item.get('product_name', 'Product')} x {order_quantity}",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "created_by": user_id
            })
            
            deductions.append({
                "item_name": item["name"],
                "quantity": total_qty,
                "new_stock": new_stock
            })
    
    return deductions


@router.get("/movements")
async def get_packaging_movements(
    item_id: Optional[str] = None,
    limit: int = 100,
    current_user: dict = Depends(get_current_user)
):
    """Get packaging stock movements"""
    query = {"company_id": current_user["company_id"]}
    if item_id:
        query["packaging_item_id"] = item_id
    
    movements = await db.packaging_movements.find(query, {"_id": 0}).sort("created_at", -1).to_list(limit)
    
    # Enrich with item names
    for mov in movements:
        item = await db.packaging_items.find_one({"id": mov["packaging_item_id"]}, {"_id": 0, "name": 1})
        mov["item_name"] = item["name"] if item else "Unknown"
    
    return movements


@router.get("/low-stock")
async def get_low_stock_packaging(current_user: dict = Depends(get_current_user)):
    """Get packaging items with low stock"""
    items = await db.packaging_items.find(
        {"company_id": current_user["company_id"]},
        {"_id": 0}
    ).to_list(500)
    
    low_stock = [item for item in items if item["stock_quantity"] <= item["low_stock_threshold"]]
    return low_stock
