"""
Packaging Rules Router
Manage packaging rules for products - links products to their packaging materials
All items are regular Products (purchased via PO → GRN)
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
class PackagingRuleItem(BaseModel):
    product_id: str  # This is a Product ID (packaging material as product)
    quantity: int = 1


class PackagingRuleCreate(BaseModel):
    product_id: str  # Main product that needs packaging
    items: List[PackagingRuleItem]  # List of packaging products
    is_active: bool = True


class PackagingRuleUpdate(BaseModel):
    items: Optional[List[PackagingRuleItem]] = None
    is_active: Optional[bool] = None


# ==================== PACKAGING RULES ====================

@router.get("/rules")
async def get_packaging_rules(current_user: dict = Depends(get_current_user)):
    """Get all packaging rules with product details"""
    rules = await db.packaging_rules.find(
        {"company_id": current_user["company_id"]},
        {"_id": 0}
    ).to_list(500)
    
    # Enrich with product details
    for rule in rules:
        # Get main product info
        product = await db.products.find_one({"id": rule["product_id"]}, {"_id": 0, "name": 1, "sku": 1})
        rule["product_name"] = product["name"] if product else "Unknown"
        rule["product_sku"] = product["sku"] if product else ""
        
        # Get packaging product details
        for item in rule.get("items", []):
            pkg_product = await db.products.find_one(
                {"id": item["product_id"]}, 
                {"_id": 0, "name": 1, "sku": 1, "stock_quantity": 1}
            )
            if pkg_product:
                item["product_name"] = pkg_product["name"]
                item["product_sku"] = pkg_product["sku"]
                item["stock_quantity"] = pkg_product["stock_quantity"]
    
    return rules


@router.get("/rules/product/{product_id}")
async def get_packaging_rule_for_product(product_id: str, current_user: dict = Depends(get_current_user)):
    """Get packaging rule for a specific product"""
    rule = await db.packaging_rules.find_one(
        {"product_id": product_id, "company_id": current_user["company_id"]},
        {"_id": 0}
    )
    
    if rule:
        # Enrich with product details
        for item in rule.get("items", []):
            pkg_product = await db.products.find_one(
                {"id": item["product_id"]}, 
                {"_id": 0, "name": 1, "sku": 1, "stock_quantity": 1}
            )
            if pkg_product:
                item["product_name"] = pkg_product["name"]
                item["product_sku"] = pkg_product["sku"]
                item["stock_quantity"] = pkg_product["stock_quantity"]
    
    return rule


@router.post("/rules")
async def create_packaging_rule(data: PackagingRuleCreate, current_user: dict = Depends(get_current_user)):
    """Create a packaging rule for a product"""
    # Check if main product exists
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
    
    # Validate all packaging products exist
    for item in data.items:
        pkg_product = await db.products.find_one({
            "id": item.product_id,
            "company_id": current_user["company_id"]
        })
        if not pkg_product:
            raise HTTPException(
                status_code=400, 
                detail=f"Packaging product {item.product_id} not found"
            )
    
    rule_id = str(uuid.uuid4())
    rule = {
        "id": rule_id,
        "company_id": current_user["company_id"],
        "product_id": data.product_id,
        "items": [{"product_id": i.product_id, "quantity": i.quantity} for i in data.items],
        "is_active": data.is_active,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.packaging_rules.insert_one(rule)
    # Remove MongoDB _id before returning
    rule.pop('_id', None)
    return rule


@router.put("/rules/{rule_id}")
async def update_packaging_rule(rule_id: str, data: PackagingRuleUpdate, current_user: dict = Depends(get_current_user)):
    """Update a packaging rule"""
    update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}
    
    if data.items is not None:
        # Validate all packaging products exist
        for item in data.items:
            pkg_product = await db.products.find_one({
                "id": item.product_id,
                "company_id": current_user["company_id"]
            })
            if not pkg_product:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Packaging product {item.product_id} not found"
                )
        update_data["items"] = [{"product_id": i.product_id, "quantity": i.quantity} for i in data.items]
    
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

