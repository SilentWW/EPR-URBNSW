from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import jwt
import bcrypt
from bson import ObjectId
import asyncio

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'erp-secret-key-change-in-production')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Create the main app
app = FastAPI(title="E1 ERP System", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer()

# ============== MODELS ==============

# User & Auth Models
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    company_name: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    company_id: str
    created_at: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# Company Models
class CompanyCreate(BaseModel):
    name: str
    currency: str = "LKR"
    timezone: str = "Asia/Colombo"
    tax_rate: float = 0.0
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None

class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    currency: Optional[str] = None
    timezone: Optional[str] = None
    tax_rate: Optional[float] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None

class WooCommerceSettings(BaseModel):
    store_url: str
    consumer_key: str
    consumer_secret: str
    enabled: bool = True
    auto_sync_enabled: bool = False
    auto_sync_interval: int = 60  # Minutes (default: 1 hour)

# Product Models
class ProductCreate(BaseModel):
    sku: Optional[str] = None  # Auto-generated if not provided
    name: str
    description: Optional[str] = None
    short_description: Optional[str] = None
    category: Optional[str] = None
    cost_price: float = 0.0  # COGS
    regular_price: float = 0.0  # WooCommerce Regular Price
    sale_price: Optional[float] = None  # WooCommerce Sale Price
    selling_price: float = 0.0  # Actual selling price (sale_price if set, else regular_price)
    stock_quantity: int = 0
    low_stock_threshold: int = 10
    weight: Optional[float] = None  # Weight in kg
    visibility: str = "public"  # public or private
    tags: Optional[str] = None  # Comma separated tags
    manage_stock: bool = True  # WooCommerce stock management
    attributes: Optional[List[dict]] = None  # WooCommerce attributes
    woo_product_id: Optional[str] = None

class ProductUpdate(BaseModel):
    sku: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    short_description: Optional[str] = None
    category: Optional[str] = None
    cost_price: Optional[float] = None
    regular_price: Optional[float] = None
    sale_price: Optional[float] = None
    selling_price: Optional[float] = None
    stock_quantity: Optional[int] = None
    low_stock_threshold: Optional[int] = None
    weight: Optional[float] = None
    visibility: Optional[str] = None
    tags: Optional[str] = None
    manage_stock: Optional[bool] = None
    attributes: Optional[List[dict]] = None

# GRN (Goods Received Note) Models
class GRNItem(BaseModel):
    product_id: Optional[str] = None  # Existing product or None for new
    product_name: str
    sku: Optional[str] = None
    description: Optional[str] = None
    short_description: Optional[str] = None
    category: Optional[str] = None
    quantity: int
    cost_price: float  # COGS per unit
    regular_price: float  # WooCommerce regular price
    sale_price: Optional[float] = None  # WooCommerce sale price
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

# Customer Models
class CustomerCreate(BaseModel):
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    woo_customer_id: Optional[str] = None

class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None

# Supplier Models
class SupplierCreate(BaseModel):
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    contact_person: Optional[str] = None

class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    contact_person: Optional[str] = None

# Order Item Model
class OrderItem(BaseModel):
    product_id: str
    product_name: str
    sku: str
    quantity: int
    unit_price: float
    total: float

# Sales Order Models
class SalesOrderCreate(BaseModel):
    customer_id: str
    items: List[OrderItem]
    discount: float = 0.0
    notes: Optional[str] = None
    woo_order_id: Optional[str] = None

class SalesOrderUpdate(BaseModel):
    status: Optional[str] = None
    payment_status: Optional[str] = None
    notes: Optional[str] = None

# Purchase Order Models
class PurchaseOrderCreate(BaseModel):
    supplier_id: str
    items: List[OrderItem]
    notes: Optional[str] = None

class PurchaseOrderUpdate(BaseModel):
    status: Optional[str] = None
    payment_status: Optional[str] = None
    notes: Optional[str] = None

# Payment Models
class PaymentCreate(BaseModel):
    reference_type: str  # sales_order, purchase_order
    reference_id: str
    amount: float
    payment_method: str  # cash, bank, card, online
    notes: Optional[str] = None

# Accounting Entry Models
class AccountingEntryCreate(BaseModel):
    entry_type: str  # income, expense
    category: str
    amount: float
    description: str
    reference_type: Optional[str] = None
    reference_id: Optional[str] = None

# Inventory Movement Models
class InventoryMovementCreate(BaseModel):
    product_id: str
    movement_type: str  # in, out, adjustment
    quantity: int
    reason: str
    reference_type: Optional[str] = None
    reference_id: Optional[str] = None

# ============== HELPER FUNCTIONS ==============

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_token(user_id: str, email: str, role: str, company_id: str) -> str:
    payload = {
        "user_id": user_id,
        "email": email,
        "role": role,
        "company_id": company_id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def serialize_doc(doc: dict) -> dict:
    """Convert MongoDB document to JSON-serializable dict"""
    if doc is None:
        return None
    result = {}
    for key, value in doc.items():
        if key == '_id':
            continue
        elif isinstance(value, ObjectId):
            result[key] = str(value)
        elif isinstance(value, datetime):
            result[key] = value.isoformat()
        else:
            result[key] = value
    return result

# ============== AUTH ROUTES ==============

@api_router.post("/auth/register", response_model=TokenResponse)
async def register(user_data: UserCreate):
    # Check if user exists
    existing = await db.users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create company
    company_id = str(uuid.uuid4())
    company = {
        "id": company_id,
        "name": user_data.company_name or f"{user_data.full_name}'s Company",
        "currency": "LKR",
        "timezone": "Asia/Colombo",
        "tax_rate": 0.0,
        "woo_settings": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    await db.companies.insert_one(company)
    
    # Create user
    user_id = str(uuid.uuid4())
    user = {
        "id": user_id,
        "email": user_data.email,
        "password": hash_password(user_data.password),
        "full_name": user_data.full_name,
        "role": "admin",
        "company_id": company_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(user)
    
    # Log activity
    await db.audit_logs.insert_one({
        "id": str(uuid.uuid4()),
        "company_id": company_id,
        "user_id": user_id,
        "action": "user_registered",
        "details": {"email": user_data.email},
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    token = create_token(user_id, user_data.email, "admin", company_id)
    
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user_id,
            email=user_data.email,
            full_name=user_data.full_name,
            role="admin",
            company_id=company_id,
            created_at=user["created_at"]
        )
    )

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user or not verify_password(credentials.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token(user["id"], user["email"], user["role"], user["company_id"])
    
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user["id"],
            email=user["email"],
            full_name=user["full_name"],
            role=user["role"],
            company_id=user["company_id"],
            created_at=user["created_at"]
        )
    )

@api_router.get("/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    user = await db.users.find_one({"id": current_user["user_id"]}, {"_id": 0, "password": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get company name for display
    company = await db.companies.find_one({"id": current_user["company_id"]}, {"_id": 0, "name": 1})
    company_name = company.get("name", "My Business") if company else "My Business"
    
    return {
        **user,
        "company_name": company_name
    }

# ============== COMPANY ROUTES ==============

@api_router.get("/company")
async def get_company(current_user: dict = Depends(get_current_user)):
    company = await db.companies.find_one({"id": current_user["company_id"]}, {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company

@api_router.put("/company")
async def update_company(data: CompanyUpdate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.companies.update_one(
        {"id": current_user["company_id"]},
        {"$set": update_data}
    )
    
    return await db.companies.find_one({"id": current_user["company_id"]}, {"_id": 0})

@api_router.put("/company/woocommerce")
async def update_woo_settings(settings: WooCommerceSettings, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    await db.companies.update_one(
        {"id": current_user["company_id"]},
        {"$set": {
            "woo_settings": settings.model_dump(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {"message": "WooCommerce settings updated successfully"}

@api_router.get("/company/woocommerce")
async def get_woo_settings(current_user: dict = Depends(get_current_user)):
    company = await db.companies.find_one({"id": current_user["company_id"]}, {"_id": 0})
    return company.get("woo_settings") or {"enabled": False}

# ============== USER MANAGEMENT ROUTES ==============

@api_router.get("/users")
async def get_users(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    users = await db.users.find(
        {"company_id": current_user["company_id"]},
        {"_id": 0, "password": 0}
    ).to_list(100)
    return users

@api_router.post("/users")
async def create_user(user_data: UserCreate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    existing = await db.users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already exists")
    
    user_id = str(uuid.uuid4())
    user = {
        "id": user_id,
        "email": user_data.email,
        "password": hash_password(user_data.password),
        "full_name": user_data.full_name,
        "role": "staff",
        "company_id": current_user["company_id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(user)
    
    del user["password"]
    return serialize_doc(user)

@api_router.put("/users/{user_id}/role")
async def update_user_role(user_id: str, role: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    if role not in ["admin", "manager", "accounts", "store", "staff"]:
        raise HTTPException(status_code=400, detail="Invalid role")
    
    result = await db.users.update_one(
        {"id": user_id, "company_id": current_user["company_id"]},
        {"$set": {"role": role, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "Role updated successfully"}

@api_router.delete("/users/{user_id}")
async def delete_user(user_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    if user_id == current_user["user_id"]:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    
    result = await db.users.delete_one({"id": user_id, "company_id": current_user["company_id"]})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "User deleted successfully"}

# ============== PRODUCT ROUTES ==============

@api_router.get("/products")
async def get_products(
    search: Optional[str] = None,
    category: Optional[str] = None,
    low_stock: Optional[bool] = None,
    current_user: dict = Depends(get_current_user)
):
    query = {"company_id": current_user["company_id"]}
    
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"sku": {"$regex": search, "$options": "i"}}
        ]
    if category:
        query["category"] = category
    
    products = await db.products.find(query, {"_id": 0}).to_list(1000)
    
    if low_stock:
        products = [p for p in products if p["stock_quantity"] <= p["low_stock_threshold"]]
    
    return products

@api_router.get("/products/{product_id}")
async def get_product(product_id: str, current_user: dict = Depends(get_current_user)):
    product = await db.products.find_one(
        {"id": product_id, "company_id": current_user["company_id"]},
        {"_id": 0}
    )
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@api_router.post("/products")
async def create_product(data: ProductCreate, current_user: dict = Depends(get_current_user)):
    company_id = current_user["company_id"]
    
    # Auto-generate SKU if not provided
    sku = data.sku
    if not sku:
        # Find highest existing SKU number
        products_list = await db.products.find(
            {"company_id": company_id, "sku": {"$regex": "^URBN"}},
            {"sku": 1}
        ).to_list(10000)
        
        max_num = 0
        for p in products_list:
            existing_sku = p.get("sku", "")
            if existing_sku.startswith("URBN"):
                try:
                    num = int(existing_sku[4:])
                    if num > max_num:
                        max_num = num
                except ValueError:
                    continue
        sku = f"URBN{max_num + 1:04d}"
    
    # Check SKU uniqueness
    existing = await db.products.find_one({
        "sku": sku,
        "company_id": company_id
    })
    if existing:
        raise HTTPException(status_code=400, detail="SKU already exists")
    
    product_id = str(uuid.uuid4())
    product_data = data.model_dump()
    product_data["sku"] = sku  # Use generated or provided SKU
    
    product = {
        "id": product_id,
        "company_id": company_id,
        **product_data,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    await db.products.insert_one(product)
    
    # Log initial inventory
    if data.stock_quantity > 0:
        await db.inventory_movements.insert_one({
            "id": str(uuid.uuid4()),
            "company_id": company_id,
            "product_id": product_id,
            "movement_type": "in",
            "quantity": data.stock_quantity,
            "reason": "Initial stock",
            "created_by": current_user["user_id"],
            "created_at": datetime.now(timezone.utc).isoformat()
        })
    
    return serialize_doc(product)

@api_router.put("/products/{product_id}")
async def update_product(product_id: str, data: ProductUpdate, current_user: dict = Depends(get_current_user)):
    existing = await db.products.find_one({
        "id": product_id,
        "company_id": current_user["company_id"]
    })
    if not existing:
        raise HTTPException(status_code=404, detail="Product not found")
    
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.products.update_one({"id": product_id}, {"$set": update_data})
    
    return await db.products.find_one({"id": product_id}, {"_id": 0})

@api_router.delete("/products/{product_id}")
async def delete_product(product_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.products.delete_one({
        "id": product_id,
        "company_id": current_user["company_id"]
    })
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product deleted successfully"}

@api_router.get("/products/categories/list")
async def get_categories(current_user: dict = Depends(get_current_user)):
    categories = await db.products.distinct("category", {"company_id": current_user["company_id"]})
    return [c for c in categories if c]

# ============== INVENTORY ROUTES ==============

@api_router.get("/inventory/movements")
async def get_inventory_movements(
    product_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    query = {"company_id": current_user["company_id"]}
    if product_id:
        query["product_id"] = product_id
    
    movements = await db.inventory_movements.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
    return movements

@api_router.post("/inventory/movements")
async def create_inventory_movement(data: InventoryMovementCreate, current_user: dict = Depends(get_current_user)):
    product = await db.products.find_one({
        "id": data.product_id,
        "company_id": current_user["company_id"]
    })
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Calculate new stock
    if data.movement_type == "in":
        new_stock = product["stock_quantity"] + data.quantity
    elif data.movement_type == "out":
        new_stock = product["stock_quantity"] - data.quantity
        if new_stock < 0:
            raise HTTPException(status_code=400, detail="Insufficient stock")
    else:  # adjustment
        new_stock = data.quantity
    
    # Update product stock
    await db.products.update_one(
        {"id": data.product_id},
        {"$set": {"stock_quantity": new_stock, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    # Record movement
    movement = {
        "id": str(uuid.uuid4()),
        "company_id": current_user["company_id"],
        "product_id": data.product_id,
        "product_name": product["name"],
        "movement_type": data.movement_type,
        "quantity": data.quantity,
        "previous_stock": product["stock_quantity"],
        "new_stock": new_stock,
        "reason": data.reason,
        "reference_type": data.reference_type,
        "reference_id": data.reference_id,
        "created_by": current_user["user_id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.inventory_movements.insert_one(movement)
    
    return serialize_doc(movement)

@api_router.get("/inventory/low-stock")
async def get_low_stock_products(current_user: dict = Depends(get_current_user)):
    products = await db.products.find(
        {"company_id": current_user["company_id"]},
        {"_id": 0}
    ).to_list(1000)
    
    low_stock = [p for p in products if p["stock_quantity"] <= p["low_stock_threshold"]]
    return low_stock

@api_router.get("/inventory/valuation")
async def get_inventory_valuation(current_user: dict = Depends(get_current_user)):
    products = await db.products.find(
        {"company_id": current_user["company_id"]},
        {"_id": 0}
    ).to_list(1000)
    
    total_cost = sum(p["cost_price"] * p["stock_quantity"] for p in products)
    total_retail = sum(p["selling_price"] * p["stock_quantity"] for p in products)
    total_items = sum(p["stock_quantity"] for p in products)
    
    return {
        "total_cost_value": total_cost,
        "total_retail_value": total_retail,
        "total_items": total_items,
        "total_products": len(products),
        "potential_profit": total_retail - total_cost
    }

# ============== CUSTOMER ROUTES ==============

@api_router.get("/customers")
async def get_customers(
    search: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    query = {"company_id": current_user["company_id"]}
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}}
        ]
    
    customers = await db.customers.find(query, {"_id": 0}).to_list(1000)
    return customers

@api_router.get("/customers/{customer_id}")
async def get_customer(customer_id: str, current_user: dict = Depends(get_current_user)):
    customer = await db.customers.find_one(
        {"id": customer_id, "company_id": current_user["company_id"]},
        {"_id": 0}
    )
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Get order history
    orders = await db.sales_orders.find(
        {"customer_id": customer_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    # Calculate totals
    total_orders = len(orders)
    total_spent = sum(o.get("total", 0) for o in orders)
    outstanding = sum(o.get("total", 0) - o.get("paid_amount", 0) for o in orders if o.get("payment_status") != "paid")
    
    return {
        **customer,
        "total_orders": total_orders,
        "total_spent": total_spent,
        "outstanding_balance": outstanding,
        "recent_orders": orders[:5]
    }

@api_router.post("/customers")
async def create_customer(data: CustomerCreate, current_user: dict = Depends(get_current_user)):
    customer_id = str(uuid.uuid4())
    customer = {
        "id": customer_id,
        "company_id": current_user["company_id"],
        **data.model_dump(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    await db.customers.insert_one(customer)
    return serialize_doc(customer)

@api_router.put("/customers/{customer_id}")
async def update_customer(customer_id: str, data: CustomerUpdate, current_user: dict = Depends(get_current_user)):
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.customers.update_one(
        {"id": customer_id, "company_id": current_user["company_id"]},
        {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    return await db.customers.find_one({"id": customer_id}, {"_id": 0})

@api_router.delete("/customers/{customer_id}")
async def delete_customer(customer_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.customers.delete_one({
        "id": customer_id,
        "company_id": current_user["company_id"]
    })
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Customer not found")
    return {"message": "Customer deleted successfully"}

# ============== SUPPLIER ROUTES ==============

@api_router.get("/suppliers")
async def get_suppliers(
    search: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    query = {"company_id": current_user["company_id"]}
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}}
        ]
    
    suppliers = await db.suppliers.find(query, {"_id": 0}).to_list(1000)
    return suppliers

@api_router.get("/suppliers/{supplier_id}")
async def get_supplier(supplier_id: str, current_user: dict = Depends(get_current_user)):
    supplier = await db.suppliers.find_one(
        {"id": supplier_id, "company_id": current_user["company_id"]},
        {"_id": 0}
    )
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    # Get purchase orders
    orders = await db.purchase_orders.find(
        {"supplier_id": supplier_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    total_orders = len(orders)
    total_amount = sum(o.get("total", 0) for o in orders)
    outstanding = sum(o.get("total", 0) - o.get("paid_amount", 0) for o in orders if o.get("payment_status") != "paid")
    
    return {
        **supplier,
        "total_orders": total_orders,
        "total_amount": total_amount,
        "outstanding_balance": outstanding,
        "recent_orders": orders[:5]
    }

@api_router.post("/suppliers")
async def create_supplier(data: SupplierCreate, current_user: dict = Depends(get_current_user)):
    supplier_id = str(uuid.uuid4())
    supplier = {
        "id": supplier_id,
        "company_id": current_user["company_id"],
        **data.model_dump(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    await db.suppliers.insert_one(supplier)
    return serialize_doc(supplier)

@api_router.put("/suppliers/{supplier_id}")
async def update_supplier(supplier_id: str, data: SupplierUpdate, current_user: dict = Depends(get_current_user)):
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.suppliers.update_one(
        {"id": supplier_id, "company_id": current_user["company_id"]},
        {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    return await db.suppliers.find_one({"id": supplier_id}, {"_id": 0})

@api_router.delete("/suppliers/{supplier_id}")
async def delete_supplier(supplier_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.suppliers.delete_one({
        "id": supplier_id,
        "company_id": current_user["company_id"]
    })
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return {"message": "Supplier deleted successfully"}

# ============== SALES ORDER ROUTES ==============

@api_router.get("/sales-orders")
async def get_sales_orders(
    status: Optional[str] = None,
    payment_status: Optional[str] = None,
    customer_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    query = {"company_id": current_user["company_id"]}
    if status:
        query["status"] = status
    if payment_status:
        query["payment_status"] = payment_status
    if customer_id:
        query["customer_id"] = customer_id
    
    orders = await db.sales_orders.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return orders

@api_router.get("/sales-orders/{order_id}")
async def get_sales_order(order_id: str, current_user: dict = Depends(get_current_user)):
    order = await db.sales_orders.find_one(
        {"id": order_id, "company_id": current_user["company_id"]},
        {"_id": 0}
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Get customer details
    customer = await db.customers.find_one({"id": order["customer_id"]}, {"_id": 0})
    
    # Get payments
    payments = await db.payments.find(
        {"reference_type": "sales_order", "reference_id": order_id},
        {"_id": 0}
    ).to_list(100)
    
    return {**order, "customer": customer, "payments": payments}

@api_router.post("/sales-orders")
async def create_sales_order(data: SalesOrderCreate, current_user: dict = Depends(get_current_user)):
    # Verify customer
    customer = await db.customers.find_one({
        "id": data.customer_id,
        "company_id": current_user["company_id"]
    })
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Calculate totals
    subtotal = sum(item.total for item in data.items)
    tax = subtotal * 0.0  # Will be calculated based on company settings
    total = subtotal - data.discount + tax
    
    order_id = str(uuid.uuid4())
    order_number = f"SO-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{str(uuid.uuid4())[:4].upper()}"
    
    order = {
        "id": order_id,
        "order_number": order_number,
        "company_id": current_user["company_id"],
        "customer_id": data.customer_id,
        "customer_name": customer["name"],
        "items": [item.model_dump() for item in data.items],
        "subtotal": subtotal,
        "discount": data.discount,
        "tax": tax,
        "total": total,
        "status": "pending",
        "payment_status": "unpaid",
        "paid_amount": 0.0,
        "notes": data.notes,
        "woo_order_id": data.woo_order_id,
        "created_by": current_user["user_id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    await db.sales_orders.insert_one(order)
    
    # Reduce inventory for each item
    for item in data.items:
        product = await db.products.find_one({"id": item.product_id})
        if product:
            new_stock = max(0, product["stock_quantity"] - item.quantity)
            await db.products.update_one(
                {"id": item.product_id},
                {"$set": {"stock_quantity": new_stock, "updated_at": datetime.now(timezone.utc).isoformat()}}
            )
            await db.inventory_movements.insert_one({
                "id": str(uuid.uuid4()),
                "company_id": current_user["company_id"],
                "product_id": item.product_id,
                "product_name": item.product_name,
                "movement_type": "out",
                "quantity": item.quantity,
                "previous_stock": product["stock_quantity"],
                "new_stock": new_stock,
                "reason": f"Sales Order {order_number}",
                "reference_type": "sales_order",
                "reference_id": order_id,
                "created_by": current_user["user_id"],
                "created_at": datetime.now(timezone.utc).isoformat()
            })
    
    # Create income entry
    await db.accounting_entries.insert_one({
        "id": str(uuid.uuid4()),
        "company_id": current_user["company_id"],
        "entry_type": "income",
        "category": "Sales",
        "amount": total,
        "description": f"Sales Order {order_number}",
        "reference_type": "sales_order",
        "reference_id": order_id,
        "created_by": current_user["user_id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return serialize_doc(order)

@api_router.put("/sales-orders/{order_id}")
async def update_sales_order(order_id: str, data: SalesOrderUpdate, current_user: dict = Depends(get_current_user)):
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.sales_orders.update_one(
        {"id": order_id, "company_id": current_user["company_id"]},
        {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return await db.sales_orders.find_one({"id": order_id}, {"_id": 0})

@api_router.post("/sales-orders/{order_id}/return")
async def return_sales_order(order_id: str, current_user: dict = Depends(get_current_user)):
    order = await db.sales_orders.find_one({
        "id": order_id,
        "company_id": current_user["company_id"]
    })
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order["status"] == "returned":
        raise HTTPException(status_code=400, detail="Order already returned")
    
    # Restore inventory
    for item in order["items"]:
        product = await db.products.find_one({"id": item["product_id"]})
        if product:
            new_stock = product["stock_quantity"] + item["quantity"]
            await db.products.update_one(
                {"id": item["product_id"]},
                {"$set": {"stock_quantity": new_stock}}
            )
            await db.inventory_movements.insert_one({
                "id": str(uuid.uuid4()),
                "company_id": current_user["company_id"],
                "product_id": item["product_id"],
                "product_name": item["product_name"],
                "movement_type": "in",
                "quantity": item["quantity"],
                "previous_stock": product["stock_quantity"],
                "new_stock": new_stock,
                "reason": f"Return: {order['order_number']}",
                "reference_type": "sales_return",
                "reference_id": order_id,
                "created_by": current_user["user_id"],
                "created_at": datetime.now(timezone.utc).isoformat()
            })
    
    # Reverse accounting entry
    await db.accounting_entries.insert_one({
        "id": str(uuid.uuid4()),
        "company_id": current_user["company_id"],
        "entry_type": "expense",
        "category": "Sales Return",
        "amount": order["total"],
        "description": f"Return: {order['order_number']}",
        "reference_type": "sales_return",
        "reference_id": order_id,
        "created_by": current_user["user_id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    # Update order status
    await db.sales_orders.update_one(
        {"id": order_id},
        {"$set": {"status": "returned", "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"message": "Order returned successfully"}

# ============== INVOICE ROUTES ==============

@api_router.get("/invoices")
async def get_invoices(
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    query = {"company_id": current_user["company_id"]}
    if status:
        query["payment_status"] = status
    
    orders = await db.sales_orders.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    
    # Transform to invoice format
    invoices = [{
        "id": o["id"],
        "invoice_number": o["order_number"].replace("SO-", "INV-"),
        "customer_name": o["customer_name"],
        "total": o["total"],
        "paid_amount": o["paid_amount"],
        "balance": o["total"] - o["paid_amount"],
        "status": o["payment_status"],
        "date": o["created_at"]
    } for o in orders]
    
    return invoices

@api_router.get("/invoices/{order_id}")
async def get_invoice(order_id: str, current_user: dict = Depends(get_current_user)):
    order = await db.sales_orders.find_one(
        {"id": order_id, "company_id": current_user["company_id"]},
        {"_id": 0}
    )
    if not order:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    customer = await db.customers.find_one({"id": order["customer_id"]}, {"_id": 0})
    company = await db.companies.find_one({"id": current_user["company_id"]}, {"_id": 0})
    
    return {
        "invoice_number": order["order_number"].replace("SO-", "INV-"),
        "order": order,
        "customer": customer,
        "company": company
    }

# ============== PURCHASE ORDER ROUTES ==============

@api_router.get("/purchase-orders")
async def get_purchase_orders(
    status: Optional[str] = None,
    payment_status: Optional[str] = None,
    supplier_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    query = {"company_id": current_user["company_id"]}
    if status:
        query["status"] = status
    if payment_status:
        query["payment_status"] = payment_status
    if supplier_id:
        query["supplier_id"] = supplier_id
    
    orders = await db.purchase_orders.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return orders

@api_router.get("/purchase-orders/{order_id}")
async def get_purchase_order(order_id: str, current_user: dict = Depends(get_current_user)):
    order = await db.purchase_orders.find_one(
        {"id": order_id, "company_id": current_user["company_id"]},
        {"_id": 0}
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    supplier = await db.suppliers.find_one({"id": order["supplier_id"]}, {"_id": 0})
    payments = await db.payments.find(
        {"reference_type": "purchase_order", "reference_id": order_id},
        {"_id": 0}
    ).to_list(100)
    
    return {**order, "supplier": supplier, "payments": payments}

@api_router.post("/purchase-orders")
async def create_purchase_order(data: PurchaseOrderCreate, current_user: dict = Depends(get_current_user)):
    # Verify supplier
    supplier = await db.suppliers.find_one({
        "id": data.supplier_id,
        "company_id": current_user["company_id"]
    })
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    subtotal = sum(item.total for item in data.items)
    total = subtotal
    
    order_id = str(uuid.uuid4())
    order_number = f"PO-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{str(uuid.uuid4())[:4].upper()}"
    
    order = {
        "id": order_id,
        "order_number": order_number,
        "company_id": current_user["company_id"],
        "supplier_id": data.supplier_id,
        "supplier_name": supplier["name"],
        "items": [item.model_dump() for item in data.items],
        "subtotal": subtotal,
        "total": total,
        "status": "pending",
        "payment_status": "unpaid",
        "paid_amount": 0.0,
        "notes": data.notes,
        "created_by": current_user["user_id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    await db.purchase_orders.insert_one(order)
    
    return serialize_doc(order)

@api_router.put("/purchase-orders/{order_id}")
async def update_purchase_order(order_id: str, data: PurchaseOrderUpdate, current_user: dict = Depends(get_current_user)):
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.purchase_orders.update_one(
        {"id": order_id, "company_id": current_user["company_id"]},
        {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return await db.purchase_orders.find_one({"id": order_id}, {"_id": 0})

@api_router.post("/purchase-orders/{order_id}/receive")
async def receive_purchase_order(order_id: str, current_user: dict = Depends(get_current_user)):
    order = await db.purchase_orders.find_one({
        "id": order_id,
        "company_id": current_user["company_id"]
    })
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order["status"] == "received":
        raise HTTPException(status_code=400, detail="Order already received")
    
    # Add inventory
    for item in order["items"]:
        product = await db.products.find_one({"id": item["product_id"]})
        if product:
            new_stock = product["stock_quantity"] + item["quantity"]
            # Update cost price
            await db.products.update_one(
                {"id": item["product_id"]},
                {"$set": {
                    "stock_quantity": new_stock,
                    "cost_price": item["unit_price"],
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            await db.inventory_movements.insert_one({
                "id": str(uuid.uuid4()),
                "company_id": current_user["company_id"],
                "product_id": item["product_id"],
                "product_name": item["product_name"],
                "movement_type": "in",
                "quantity": item["quantity"],
                "previous_stock": product["stock_quantity"],
                "new_stock": new_stock,
                "reason": f"Purchase Order {order['order_number']}",
                "reference_type": "purchase_order",
                "reference_id": order_id,
                "created_by": current_user["user_id"],
                "created_at": datetime.now(timezone.utc).isoformat()
            })
    
    # Create expense entry
    await db.accounting_entries.insert_one({
        "id": str(uuid.uuid4()),
        "company_id": current_user["company_id"],
        "entry_type": "expense",
        "category": "Purchases",
        "amount": order["total"],
        "description": f"Purchase Order {order['order_number']}",
        "reference_type": "purchase_order",
        "reference_id": order_id,
        "created_by": current_user["user_id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    # Update order status
    await db.purchase_orders.update_one(
        {"id": order_id},
        {"$set": {"status": "received", "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"message": "Goods received successfully"}

# ============== PAYMENT ROUTES ==============

@api_router.get("/payments")
async def get_payments(
    reference_type: Optional[str] = None,
    payment_method: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    query = {"company_id": current_user["company_id"]}
    if reference_type:
        query["reference_type"] = reference_type
    if payment_method:
        query["payment_method"] = payment_method
    
    payments = await db.payments.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return payments

@api_router.post("/payments")
async def create_payment(data: PaymentCreate, current_user: dict = Depends(get_current_user)):
    company_id = current_user["company_id"]
    
    # Get reference order
    if data.reference_type == "sales_order":
        order = await db.sales_orders.find_one({
            "id": data.reference_id,
            "company_id": company_id
        })
        if not order:
            raise HTTPException(status_code=404, detail="Sales order not found")
        
        collection = db.sales_orders
        entry_type = "income"
        category = "Sales Payment"
    elif data.reference_type == "purchase_order":
        order = await db.purchase_orders.find_one({
            "id": data.reference_id,
            "company_id": company_id
        })
        if not order:
            raise HTTPException(status_code=404, detail="Purchase order not found")
        
        collection = db.purchase_orders
        entry_type = "expense"
        category = "Purchase Payment"
    else:
        raise HTTPException(status_code=400, detail="Invalid reference type")
    
    # Create payment
    payment_id = str(uuid.uuid4())
    payment = {
        "id": payment_id,
        "company_id": company_id,
        "reference_type": data.reference_type,
        "reference_id": data.reference_id,
        "reference_number": order.get("order_number"),
        "amount": data.amount,
        "payment_method": data.payment_method,
        "notes": data.notes,
        "created_by": current_user["user_id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.payments.insert_one(payment)
    
    # Update order payment status
    new_paid = order["paid_amount"] + data.amount
    payment_status = "paid" if new_paid >= order["total"] else "partial"
    
    await collection.update_one(
        {"id": data.reference_id},
        {"$set": {
            "paid_amount": new_paid,
            "payment_status": payment_status,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Record in bank/cash ledger
    await db.bank_transactions.insert_one({
        "id": str(uuid.uuid4()),
        "company_id": company_id,
        "type": "credit" if entry_type == "income" else "debit",
        "amount": data.amount,
        "payment_method": data.payment_method,
        "description": f"Payment for {order.get('order_number')}",
        "reference_type": data.reference_type,
        "reference_id": data.reference_id,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    # Create double-entry journal entry for proper accounting
    cash_account = await db.accounts.find_one({"company_id": company_id, "code": "1100"})
    if not cash_account:
        cash_account = await db.accounts.find_one({"company_id": company_id, "category": "cash"})
    
    if data.reference_type == "purchase_order":
        # Payment to supplier: Record as Inventory purchase
        # Debit: Inventory (asset increases - we now own the goods)
        # Credit: Cash (asset decreases - money goes out)
        inventory_account = await db.accounts.find_one({"company_id": company_id, "code": "1400"})  # Inventory
        if not inventory_account:
            inventory_account = await db.accounts.find_one({"company_id": company_id, "category": "inventory"})
        
        if cash_account and inventory_account:
            entry_id = str(uuid.uuid4())
            entry_number = f"PAY-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{entry_id[:4].upper()}"
            
            journal_entry = {
                "id": entry_id,
                "entry_number": entry_number,
                "company_id": company_id,
                "entry_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "reference_number": order.get("order_number"),
                "description": f"Inventory purchase - {order.get('order_number')}",
                "lines": [
                    {"account_id": inventory_account["id"], "account_code": inventory_account["code"], "account_name": inventory_account["name"], "debit": data.amount, "credit": 0, "description": "Inventory received"},
                    {"account_id": cash_account["id"], "account_code": cash_account["code"], "account_name": cash_account["name"], "debit": 0, "credit": data.amount, "description": "Cash payment to supplier"}
                ],
                "total_debit": data.amount,
                "total_credit": data.amount,
                "is_balanced": True,
                "is_auto_generated": True,
                "is_reversed": False,
                "reference_type": "payment",
                "reference_id": payment_id,
                "created_by": current_user["user_id"],
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.journal_entries.insert_one(journal_entry)
            # Inventory (asset): debit increases balance
            await db.accounts.update_one({"id": inventory_account["id"]}, {"$inc": {"current_balance": data.amount}})
            # Cash (asset): credit decreases balance
            await db.accounts.update_one({"id": cash_account["id"]}, {"$inc": {"current_balance": -data.amount}})
    
    elif data.reference_type == "sales_order":
        # Payment from customer: Debit Cash, Credit AR
        ar_account = await db.accounts.find_one({"company_id": company_id, "code": "1300"})
        if not ar_account:
            ar_account = await db.accounts.find_one({"company_id": company_id, "category": "accounts_receivable"})
        
        if cash_account and ar_account:
            entry_id = str(uuid.uuid4())
            entry_number = f"REC-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{entry_id[:4].upper()}"
            
            journal_entry = {
                "id": entry_id,
                "entry_number": entry_number,
                "company_id": company_id,
                "entry_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "reference_number": order.get("order_number"),
                "description": f"Payment received for {order.get('order_number')}",
                "lines": [
                    {"account_id": cash_account["id"], "account_code": cash_account["code"], "account_name": cash_account["name"], "debit": data.amount, "credit": 0, "description": "Cash received from customer"},
                    {"account_id": ar_account["id"], "account_code": ar_account["code"], "account_name": ar_account["name"], "debit": 0, "credit": data.amount, "description": "Reduce accounts receivable"}
                ],
                "total_debit": data.amount,
                "total_credit": data.amount,
                "is_balanced": True,
                "is_auto_generated": True,
                "is_reversed": False,
                "reference_type": "payment",
                "reference_id": payment_id,
                "created_by": current_user["user_id"],
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.journal_entries.insert_one(journal_entry)
            await db.accounts.update_one({"id": cash_account["id"]}, {"$inc": {"current_balance": data.amount}})
            await db.accounts.update_one({"id": ar_account["id"]}, {"$inc": {"current_balance": -data.amount}})
    
    return serialize_doc(payment)

@api_router.get("/payments/summary")
async def get_payment_summary(current_user: dict = Depends(get_current_user)):
    # Get all bank transactions
    transactions = await db.bank_transactions.find(
        {"company_id": current_user["company_id"]},
        {"_id": 0}
    ).to_list(10000)
    
    cash_balance = sum(t["amount"] if t["type"] == "credit" else -t["amount"] 
                       for t in transactions if t["payment_method"] == "cash")
    bank_balance = sum(t["amount"] if t["type"] == "credit" else -t["amount"] 
                       for t in transactions if t["payment_method"] in ["bank", "card", "online"])
    
    return {
        "cash_balance": cash_balance,
        "bank_balance": bank_balance,
        "total_balance": cash_balance + bank_balance
    }

# ============== ACCOUNTING ROUTES ==============

@api_router.get("/accounting/entries")
async def get_accounting_entries(
    entry_type: Optional[str] = None,
    category: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    query = {"company_id": current_user["company_id"]}
    if entry_type:
        query["entry_type"] = entry_type
    if category:
        query["category"] = category
    if start_date:
        query["created_at"] = {"$gte": start_date}
    if end_date:
        if "created_at" in query:
            query["created_at"]["$lte"] = end_date
        else:
            query["created_at"] = {"$lte": end_date}
    
    entries = await db.accounting_entries.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return entries

@api_router.post("/accounting/entries")
async def create_accounting_entry(data: AccountingEntryCreate, current_user: dict = Depends(get_current_user)):
    entry_id = str(uuid.uuid4())
    entry = {
        "id": entry_id,
        "company_id": current_user["company_id"],
        **data.model_dump(),
        "created_by": current_user["user_id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.accounting_entries.insert_one(entry)
    return serialize_doc(entry)

@api_router.get("/accounting/profit-loss")
async def get_profit_loss(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    query = {"company_id": current_user["company_id"]}
    if start_date or end_date:
        query["created_at"] = {}
        if start_date:
            query["created_at"]["$gte"] = start_date
        if end_date:
            query["created_at"]["$lte"] = end_date
    
    entries = await db.accounting_entries.find(query, {"_id": 0}).to_list(10000)
    
    income = sum(e["amount"] for e in entries if e["entry_type"] == "income")
    expenses = sum(e["amount"] for e in entries if e["entry_type"] == "expense")
    
    # Group by category
    income_by_category = {}
    expense_by_category = {}
    for e in entries:
        if e["entry_type"] == "income":
            income_by_category[e["category"]] = income_by_category.get(e["category"], 0) + e["amount"]
        else:
            expense_by_category[e["category"]] = expense_by_category.get(e["category"], 0) + e["amount"]
    
    return {
        "total_income": income,
        "total_expenses": expenses,
        "net_profit": income - expenses,
        "income_by_category": income_by_category,
        "expense_by_category": expense_by_category
    }

@api_router.get("/accounting/receivables")
async def get_receivables(current_user: dict = Depends(get_current_user)):
    orders = await db.sales_orders.find(
        {
            "company_id": current_user["company_id"],
            "payment_status": {"$ne": "paid"}
        },
        {"_id": 0}
    ).to_list(1000)
    
    receivables = [{
        "order_id": o["id"],
        "order_number": o["order_number"],
        "customer_name": o["customer_name"],
        "total": o["total"],
        "paid": o["paid_amount"],
        "balance": o["total"] - o["paid_amount"],
        "date": o["created_at"]
    } for o in orders]
    
    total = sum(r["balance"] for r in receivables)
    
    return {
        "total_receivables": total,
        "items": receivables
    }

@api_router.get("/accounting/payables")
async def get_payables(current_user: dict = Depends(get_current_user)):
    orders = await db.purchase_orders.find(
        {
            "company_id": current_user["company_id"],
            "payment_status": {"$ne": "paid"}
        },
        {"_id": 0}
    ).to_list(1000)
    
    payables = [{
        "order_id": o["id"],
        "order_number": o["order_number"],
        "supplier_name": o["supplier_name"],
        "total": o["total"],
        "paid": o["paid_amount"],
        "balance": o["total"] - o["paid_amount"],
        "date": o["created_at"]
    } for o in orders]
    
    total = sum(p["balance"] for p in payables)
    
    return {
        "total_payables": total,
        "items": payables
    }

# ============== DASHBOARD & REPORTS ==============

@api_router.get("/dashboard/summary")
async def get_dashboard_summary(current_user: dict = Depends(get_current_user)):
    company_id = current_user["company_id"]
    
    # Get counts
    products_count = await db.products.count_documents({"company_id": company_id})
    customers_count = await db.customers.count_documents({"company_id": company_id})
    suppliers_count = await db.suppliers.count_documents({"company_id": company_id})
    
    # Get sales orders
    sales_orders = await db.sales_orders.find({"company_id": company_id}, {"_id": 0}).to_list(10000)
    total_sales = sum(o["total"] for o in sales_orders)
    pending_orders = len([o for o in sales_orders if o["status"] == "pending"])
    
    # Get low stock
    products = await db.products.find({"company_id": company_id}, {"_id": 0}).to_list(1000)
    low_stock_count = len([p for p in products if p["stock_quantity"] <= p["low_stock_threshold"]])
    
    # Get P&L
    entries = await db.accounting_entries.find({"company_id": company_id}, {"_id": 0}).to_list(10000)
    total_income = sum(e["amount"] for e in entries if e["entry_type"] == "income")
    total_expenses = sum(e["amount"] for e in entries if e["entry_type"] == "expense")
    
    # Receivables & Payables
    receivables = sum(o["total"] - o["paid_amount"] for o in sales_orders if o["payment_status"] != "paid")
    
    purchase_orders = await db.purchase_orders.find({"company_id": company_id}, {"_id": 0}).to_list(10000)
    payables = sum(o["total"] - o["paid_amount"] for o in purchase_orders if o["payment_status"] != "paid")
    
    return {
        "products_count": products_count,
        "customers_count": customers_count,
        "suppliers_count": suppliers_count,
        "total_sales": total_sales,
        "pending_orders": pending_orders,
        "low_stock_count": low_stock_count,
        "total_income": total_income,
        "total_expenses": total_expenses,
        "net_profit": total_income - total_expenses,
        "receivables": receivables,
        "payables": payables
    }

@api_router.get("/dashboard/sales-chart")
async def get_sales_chart(
    period: str = "7days",
    current_user: dict = Depends(get_current_user)
):
    company_id = current_user["company_id"]
    
    if period == "7days":
        days = 7
    elif period == "30days":
        days = 30
    else:
        days = 7
    
    start_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    
    orders = await db.sales_orders.find(
        {"company_id": company_id, "created_at": {"$gte": start_date}},
        {"_id": 0}
    ).to_list(10000)
    
    # Group by date
    daily_sales = {}
    for o in orders:
        date = o["created_at"][:10]
        daily_sales[date] = daily_sales.get(date, 0) + o["total"]
    
    # Fill missing dates
    chart_data = []
    for i in range(days):
        date = (datetime.now(timezone.utc) - timedelta(days=days-1-i)).strftime("%Y-%m-%d")
        chart_data.append({
            "date": date,
            "sales": daily_sales.get(date, 0)
        })
    
    return chart_data

@api_router.get("/dashboard/top-products")
async def get_top_products(
    limit: int = 10,
    current_user: dict = Depends(get_current_user)
):
    orders = await db.sales_orders.find(
        {"company_id": current_user["company_id"]},
        {"_id": 0}
    ).to_list(10000)
    
    product_sales = {}
    for o in orders:
        for item in o["items"]:
            pid = item["product_id"]
            if pid not in product_sales:
                product_sales[pid] = {
                    "product_id": pid,
                    "product_name": item["product_name"],
                    "quantity_sold": 0,
                    "total_revenue": 0
                }
            product_sales[pid]["quantity_sold"] += item["quantity"]
            product_sales[pid]["total_revenue"] += item["total"]
    
    top = sorted(product_sales.values(), key=lambda x: x["total_revenue"], reverse=True)[:limit]
    return top

@api_router.get("/reports/sales")
async def get_sales_report(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    query = {"company_id": current_user["company_id"]}
    if start_date or end_date:
        query["created_at"] = {}
        if start_date:
            query["created_at"]["$gte"] = start_date
        if end_date:
            query["created_at"]["$lte"] = end_date
    
    orders = await db.sales_orders.find(query, {"_id": 0}).to_list(10000)
    
    return {
        "total_orders": len(orders),
        "total_revenue": sum(o["total"] for o in orders),
        "total_discount": sum(o["discount"] for o in orders),
        "orders_by_status": {
            "pending": len([o for o in orders if o["status"] == "pending"]),
            "completed": len([o for o in orders if o["status"] == "completed"]),
            "returned": len([o for o in orders if o["status"] == "returned"])
        },
        "orders": orders
    }

@api_router.get("/notifications")
async def get_notifications(current_user: dict = Depends(get_current_user)):
    company_id = current_user["company_id"]
    notifications = []
    
    # Low stock alerts
    products = await db.products.find({"company_id": company_id}, {"_id": 0}).to_list(1000)
    for p in products:
        if p["stock_quantity"] <= p["low_stock_threshold"]:
            notifications.append({
                "id": f"low-stock-{p['id']}",
                "type": "low_stock",
                "title": "Low Stock Alert",
                "message": f"{p['name']} has only {p['stock_quantity']} items left",
                "severity": "warning",
                "created_at": datetime.now(timezone.utc).isoformat()
            })
    
    # Pending payments
    orders = await db.sales_orders.find(
        {"company_id": company_id, "payment_status": {"$ne": "paid"}},
        {"_id": 0}
    ).to_list(100)
    for o in orders:
        notifications.append({
            "id": f"pending-payment-{o['id']}",
            "type": "pending_payment",
            "title": "Payment Pending",
            "message": f"Order {o['order_number']} has pending payment of LKR {o['total'] - o['paid_amount']:.2f}",
            "severity": "info",
            "created_at": o["created_at"]
        })
    
    return notifications[:20]

@api_router.get("/audit-logs")
async def get_audit_logs(
    limit: int = 100,
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    logs = await db.audit_logs.find(
        {"company_id": current_user["company_id"]},
        {"_id": 0}
    ).sort("timestamp", -1).to_list(limit)
    
    return logs

# ============== DEMO DATA ==============

@api_router.post("/seed-demo-data")
async def seed_demo_data(current_user: dict = Depends(get_current_user)):
    company_id = current_user["company_id"]
    user_id = current_user["user_id"]
    
    # Check if demo data exists
    products_count = await db.products.count_documents({"company_id": company_id})
    if products_count > 0:
        return {"message": "Demo data already exists", "hint": "Delete existing data first or use a new account"}
    
    timestamp = datetime.now(timezone.utc).isoformat()
    
    # ============== SUPPLIERS (10 suppliers with full details) ==============
    demo_suppliers = [
        {
            "name": "Tech Imports Ltd",
            "email": "sales@techimports.lk",
            "phone": "+94112345678",
            "mobile": "+94771234567",
            "contact_person": "Mr. Amal Silva",
            "designation": "Sales Manager",
            "address": "No. 45, Union Place, Colombo 02",
            "city": "Colombo",
            "country": "Sri Lanka",
            "postal_code": "00200",
            "tax_id": "TIN123456789",
            "payment_terms": "Net 30",
            "bank_name": "Commercial Bank",
            "bank_account": "8012345678",
            "notes": "Primary supplier for electronics. Offers 5% discount on bulk orders.",
            "category": "Electronics"
        },
        {
            "name": "Fashion Wholesale Co",
            "email": "orders@fashionwholesale.lk",
            "phone": "+94112345679",
            "mobile": "+94772345678",
            "contact_person": "Mrs. Kumari Fernando",
            "designation": "Procurement Head",
            "address": "No. 78, Galle Road, Dehiwala",
            "city": "Dehiwala",
            "country": "Sri Lanka",
            "postal_code": "10350",
            "tax_id": "TIN234567890",
            "payment_terms": "Net 45",
            "bank_name": "Sampath Bank",
            "bank_account": "1023456789",
            "notes": "Reliable clothing supplier. Handles returns within 14 days.",
            "category": "Clothing"
        },
        {
            "name": "Home Essentials PVT",
            "email": "info@homeessentials.lk",
            "phone": "+94112345680",
            "mobile": "+94773456789",
            "contact_person": "Mr. Ruwan Perera",
            "designation": "Director",
            "address": "No. 23, Duplication Road, Colombo 03",
            "city": "Colombo",
            "country": "Sri Lanka",
            "postal_code": "00300",
            "tax_id": "TIN345678901",
            "payment_terms": "Net 15",
            "bank_name": "HNB",
            "bank_account": "2034567890",
            "notes": "Home goods supplier with fast delivery.",
            "category": "Home & Garden"
        },
        {
            "name": "Sports Zone International",
            "email": "procurement@sportszone.lk",
            "phone": "+94112345681",
            "mobile": "+94774567890",
            "contact_person": "Mr. Dinesh Jayawardena",
            "designation": "Supply Chain Manager",
            "address": "No. 156, High Level Road, Nugegoda",
            "city": "Nugegoda",
            "country": "Sri Lanka",
            "postal_code": "10250",
            "tax_id": "TIN456789012",
            "payment_terms": "Net 30",
            "bank_name": "BOC",
            "bank_account": "3045678901",
            "notes": "Exclusive distributor for fitness equipment.",
            "category": "Sports"
        },
        {
            "name": "Global Gadgets Inc",
            "email": "supply@globalgadgets.com",
            "phone": "+94112345682",
            "mobile": "+94775678901",
            "contact_person": "Ms. Priya Sharma",
            "designation": "Regional Manager",
            "address": "No. 89, Park Street, Colombo 02",
            "city": "Colombo",
            "country": "Sri Lanka",
            "postal_code": "00200",
            "tax_id": "TIN567890123",
            "payment_terms": "Net 60",
            "bank_name": "HSBC",
            "bank_account": "4056789012",
            "notes": "International supplier with warranty support.",
            "category": "Electronics"
        },
    ]
    
    supplier_ids = {}
    for s in demo_suppliers:
        sid = str(uuid.uuid4())
        supplier_ids[s["name"]] = {"id": sid, "name": s["name"], "category": s.get("category")}
        await db.suppliers.insert_one({
            "id": sid,
            "company_id": company_id,
            **s,
            "total_purchases": 0,
            "total_paid": 0,
            "outstanding_balance": 0,
            "is_active": True,
            "created_at": timestamp,
            "updated_at": timestamp
        })
    
    # ============== PRODUCTS (15 products with full WooCommerce fields) ==============
    demo_products = [
        {
            "sku": "ELEC-001",
            "name": "Premium Wireless Earbuds Pro",
            "description": "<p>Experience crystal-clear audio with our Premium Wireless Earbuds Pro. Features active noise cancellation, 30-hour battery life, and IPX5 water resistance. Perfect for workouts, commuting, and daily use.</p><ul><li>Bluetooth 5.3 connectivity</li><li>Touch controls</li><li>Voice assistant support</li></ul>",
            "short_description": "Premium wireless earbuds with ANC and 30-hour battery life.",
            "category": "Electronics",
            "cost_price": 4500,
            "regular_price": 7999,
            "sale_price": 6999,
            "selling_price": 6999,
            "stock_quantity": 150,
            "weight": 0.05,
            "visibility": "public",
            "tags": "wireless, earbuds, bluetooth, audio, music, tech",
            "manage_stock": True,
            "low_stock_threshold": 20
        },
        {
            "sku": "ELEC-002",
            "name": "Portable Bluetooth Speaker 20W",
            "description": "<p>Powerful 20W portable speaker with deep bass and 360° surround sound. Waterproof IPX7 rating makes it perfect for outdoor adventures. Connect up to 2 speakers for stereo mode.</p>",
            "short_description": "20W waterproof Bluetooth speaker with 360° sound.",
            "category": "Electronics",
            "cost_price": 3500,
            "regular_price": 5999,
            "sale_price": None,
            "selling_price": 5999,
            "stock_quantity": 85,
            "weight": 0.8,
            "visibility": "public",
            "tags": "speaker, bluetooth, portable, waterproof, outdoor, music",
            "manage_stock": True,
            "low_stock_threshold": 15
        },
        {
            "sku": "ELEC-003",
            "name": "Smart Fitness Watch Series 5",
            "description": "<p>Track your health and fitness with our advanced Smart Watch Series 5. Features heart rate monitoring, SpO2 sensor, GPS, sleep tracking, and 100+ workout modes. 7-day battery life with always-on display.</p>",
            "short_description": "Advanced fitness smartwatch with health monitoring.",
            "category": "Electronics",
            "cost_price": 12000,
            "regular_price": 19999,
            "sale_price": 17999,
            "selling_price": 17999,
            "stock_quantity": 65,
            "weight": 0.045,
            "visibility": "public",
            "tags": "smartwatch, fitness, health, gps, sports, wearable",
            "manage_stock": True,
            "low_stock_threshold": 10
        },
        {
            "sku": "CLTH-001",
            "name": "Organic Cotton T-Shirt - Navy Blue",
            "description": "<p>Sustainable fashion meets comfort. Our organic cotton t-shirt is made from 100% GOTS certified cotton. Pre-shrunk, breathable, and incredibly soft. Available in sizes S-XXL.</p>",
            "short_description": "100% organic cotton t-shirt, soft and sustainable.",
            "category": "Clothing",
            "cost_price": 800,
            "regular_price": 1999,
            "sale_price": 1499,
            "selling_price": 1499,
            "stock_quantity": 250,
            "weight": 0.2,
            "visibility": "public",
            "tags": "tshirt, cotton, organic, sustainable, fashion, clothing",
            "manage_stock": True,
            "low_stock_threshold": 50
        },
        {
            "sku": "CLTH-002",
            "name": "Classic Fit Denim Jeans",
            "description": "<p>Timeless style with modern comfort. Our classic fit jeans feature stretch denim for all-day comfort. 5-pocket styling, zip fly, and a versatile medium wash that goes with everything.</p>",
            "short_description": "Classic fit stretch denim jeans in medium wash.",
            "category": "Clothing",
            "cost_price": 2200,
            "regular_price": 4999,
            "sale_price": None,
            "selling_price": 4999,
            "stock_quantity": 180,
            "weight": 0.6,
            "visibility": "public",
            "tags": "jeans, denim, classic, fashion, pants, clothing",
            "manage_stock": True,
            "low_stock_threshold": 30
        },
        {
            "sku": "CLTH-003",
            "name": "Lightweight Rain Jacket",
            "description": "<p>Stay dry in style with our packable rain jacket. Waterproof fabric with sealed seams, adjustable hood, and zippered pockets. Folds into its own pocket for easy storage.</p>",
            "short_description": "Packable waterproof rain jacket with hood.",
            "category": "Clothing",
            "cost_price": 1800,
            "regular_price": 3999,
            "sale_price": 3499,
            "selling_price": 3499,
            "stock_quantity": 95,
            "weight": 0.3,
            "visibility": "public",
            "tags": "jacket, rain, waterproof, outdoor, packable, clothing",
            "manage_stock": True,
            "low_stock_threshold": 20
        },
        {
            "sku": "HOME-001",
            "name": "LED Smart Desk Lamp",
            "description": "<p>Illuminate your workspace with our smart LED desk lamp. Features 5 brightness levels, 3 color temperatures, USB charging port, and touch controls. Eye-caring technology reduces strain.</p>",
            "short_description": "Smart LED desk lamp with USB port and touch controls.",
            "category": "Home & Garden",
            "cost_price": 1500,
            "regular_price": 2999,
            "sale_price": 2499,
            "selling_price": 2499,
            "stock_quantity": 120,
            "weight": 1.2,
            "visibility": "public",
            "tags": "lamp, led, desk, office, smart, lighting, home",
            "manage_stock": True,
            "low_stock_threshold": 25
        },
        {
            "sku": "HOME-002",
            "name": "Ceramic Plant Pot Set (3 pcs)",
            "description": "<p>Bring nature indoors with our elegant ceramic pot set. Includes 3 different sizes with bamboo drainage trays. Modern minimalist design suits any decor. Perfect for succulents and small plants.</p>",
            "short_description": "Set of 3 ceramic plant pots with drainage trays.",
            "category": "Home & Garden",
            "cost_price": 1200,
            "regular_price": 2499,
            "sale_price": None,
            "selling_price": 2499,
            "stock_quantity": 75,
            "weight": 2.5,
            "visibility": "public",
            "tags": "pot, plant, ceramic, garden, decor, home, indoor",
            "manage_stock": True,
            "low_stock_threshold": 15
        },
        {
            "sku": "HOME-003",
            "name": "Bamboo Kitchen Organizer",
            "description": "<p>Declutter your kitchen with our eco-friendly bamboo organizer. Multiple compartments for utensils, spices, and accessories. Water-resistant finish and anti-slip base.</p>",
            "short_description": "Eco-friendly bamboo kitchen storage organizer.",
            "category": "Home & Garden",
            "cost_price": 900,
            "regular_price": 1799,
            "sale_price": 1499,
            "selling_price": 1499,
            "stock_quantity": 110,
            "weight": 0.8,
            "visibility": "public",
            "tags": "organizer, kitchen, bamboo, storage, eco, home",
            "manage_stock": True,
            "low_stock_threshold": 20
        },
        {
            "sku": "SPRT-001",
            "name": "Professional Yoga Mat 6mm",
            "description": "<p>Elevate your practice with our professional-grade yoga mat. 6mm thickness provides excellent cushioning. Non-slip surface, alignment guides, and eco-friendly TPE material. Includes carrying strap.</p>",
            "short_description": "6mm professional yoga mat with alignment guides.",
            "category": "Sports",
            "cost_price": 1100,
            "regular_price": 2499,
            "sale_price": None,
            "selling_price": 2499,
            "stock_quantity": 90,
            "weight": 1.5,
            "visibility": "public",
            "tags": "yoga, mat, fitness, exercise, gym, sports, wellness",
            "manage_stock": True,
            "low_stock_threshold": 15
        },
        {
            "sku": "SPRT-002",
            "name": "Adjustable Dumbbell Set 20kg",
            "description": "<p>Complete home gym solution with our adjustable dumbbells. Easily switch between 2kg to 20kg per hand. Space-saving design replaces 10 individual weights. Chrome-plated for durability.</p>",
            "short_description": "Adjustable dumbbells 2-20kg per hand with storage.",
            "category": "Sports",
            "cost_price": 8500,
            "regular_price": 14999,
            "sale_price": 12999,
            "selling_price": 12999,
            "stock_quantity": 40,
            "weight": 42.0,
            "visibility": "public",
            "tags": "dumbbell, weights, fitness, gym, home, workout, strength",
            "manage_stock": True,
            "low_stock_threshold": 10
        },
        {
            "sku": "SPRT-003",
            "name": "Resistance Bands Set (5 pcs)",
            "description": "<p>Versatile workout anywhere with our 5-piece resistance band set. Different resistance levels from light to extra heavy. Includes door anchor, handles, and ankle straps. Portable carrying bag included.</p>",
            "short_description": "5-piece resistance band set with accessories.",
            "category": "Sports",
            "cost_price": 800,
            "regular_price": 1799,
            "sale_price": 1499,
            "selling_price": 1499,
            "stock_quantity": 130,
            "weight": 0.5,
            "visibility": "public",
            "tags": "resistance, bands, fitness, workout, portable, gym, exercise",
            "manage_stock": True,
            "low_stock_threshold": 25
        },
        {
            "sku": "ELEC-004",
            "name": "Wireless Charging Pad 15W",
            "description": "<p>Fast wireless charging for all Qi-enabled devices. 15W max output for quick charging. LED indicator, foreign object detection, and overheat protection. Slim design fits any desk.</p>",
            "short_description": "15W fast wireless charging pad with safety features.",
            "category": "Electronics",
            "cost_price": 1200,
            "regular_price": 2499,
            "sale_price": 1999,
            "selling_price": 1999,
            "stock_quantity": 200,
            "weight": 0.15,
            "visibility": "public",
            "tags": "charger, wireless, fast, qi, phone, tech, accessories",
            "manage_stock": True,
            "low_stock_threshold": 40
        },
        {
            "sku": "CLTH-004",
            "name": "Sports Performance Polo",
            "description": "<p>Stay cool under pressure with our moisture-wicking polo. Breathable fabric, UV protection, and anti-odor technology. Perfect for golf, tennis, or casual wear.</p>",
            "short_description": "Moisture-wicking sports polo with UV protection.",
            "category": "Clothing",
            "cost_price": 1100,
            "regular_price": 2499,
            "sale_price": None,
            "selling_price": 2499,
            "stock_quantity": 160,
            "weight": 0.25,
            "visibility": "public",
            "tags": "polo, sports, performance, golf, tennis, clothing, activewear",
            "manage_stock": True,
            "low_stock_threshold": 30
        },
        {
            "sku": "HOME-004",
            "name": "Aromatherapy Essential Oil Diffuser",
            "description": "<p>Create a calming atmosphere with our ultrasonic diffuser. 300ml capacity, 7 LED mood lights, and whisper-quiet operation. Auto shut-off when water runs out. Timer settings up to 6 hours.</p>",
            "short_description": "Ultrasonic aromatherapy diffuser with mood lighting.",
            "category": "Home & Garden",
            "cost_price": 1400,
            "regular_price": 2999,
            "sale_price": 2499,
            "selling_price": 2499,
            "stock_quantity": 85,
            "weight": 0.45,
            "visibility": "public",
            "tags": "diffuser, aromatherapy, essential, oil, home, wellness, relaxation",
            "manage_stock": True,
            "low_stock_threshold": 15
        },
    ]
    
    product_ids = {}
    for p in demo_products:
        pid = str(uuid.uuid4())
        product_ids[p["sku"]] = {
            "id": pid, 
            "name": p["name"], 
            "sku": p["sku"],
            "cost_price": p["cost_price"],
            "selling_price": p["selling_price"],
            "category": p["category"]
        }
        await db.products.insert_one({
            "id": pid,
            "company_id": company_id,
            **p,
            "woo_product_id": None,
            "attributes": [],
            "created_at": timestamp,
            "updated_at": timestamp
        })
    
    # ============== CUSTOMERS (10 customers with full details) ==============
    demo_customers = [
        {
            "name": "Kasun Rajitha Perera",
            "email": "kasun.perera@gmail.com",
            "phone": "+94771234567",
            "mobile": "+94711234567",
            "address": "No. 123, Galle Road, Colombo 03",
            "city": "Colombo",
            "country": "Sri Lanka",
            "postal_code": "00300",
            "company_name": "Perera Holdings",
            "tax_id": "TIN987654321",
            "customer_type": "Regular",
            "credit_limit": 100000,
            "notes": "VIP customer, prefers cash on delivery"
        },
        {
            "name": "Nimali Jayasinghe Silva",
            "email": "nimali.silva@yahoo.com",
            "phone": "+94772345678",
            "mobile": "+94712345678",
            "address": "No. 456, Kandy Road, Peradeniya",
            "city": "Kandy",
            "country": "Sri Lanka",
            "postal_code": "20400",
            "company_name": None,
            "tax_id": None,
            "customer_type": "Regular",
            "credit_limit": 50000,
            "notes": "Frequent buyer of home products"
        },
        {
            "name": "Ruwan Bandara Fernando",
            "email": "ruwan.fernando@hotmail.com",
            "phone": "+94773456789",
            "mobile": "+94713456789",
            "address": "No. 789, Beach Road, Unawatuna",
            "city": "Galle",
            "country": "Sri Lanka",
            "postal_code": "80600",
            "company_name": "Fernando Enterprises",
            "tax_id": "TIN876543210",
            "customer_type": "Wholesale",
            "credit_limit": 250000,
            "notes": "Wholesale customer, orders monthly"
        },
        {
            "name": "Chamari Dilhani Jayawardena",
            "email": "chamari.j@gmail.com",
            "phone": "+94774567890",
            "mobile": "+94714567890",
            "address": "No. 321, Hill Street, Nuwara Eliya",
            "city": "Nuwara Eliya",
            "country": "Sri Lanka",
            "postal_code": "22200",
            "company_name": None,
            "tax_id": None,
            "customer_type": "Regular",
            "credit_limit": 75000,
            "notes": "Prefers eco-friendly products"
        },
        {
            "name": "Dinesh Lakshman Kumara",
            "email": "dinesh.kumara@outlook.com",
            "phone": "+94775678901",
            "mobile": "+94715678901",
            "address": "No. 654, Lake Road, Negombo",
            "city": "Negombo",
            "country": "Sri Lanka",
            "postal_code": "11500",
            "company_name": "Kumara Sports",
            "tax_id": "TIN765432109",
            "customer_type": "Retail",
            "credit_limit": 150000,
            "notes": "Sports equipment buyer, gym owner"
        },
        {
            "name": "Sachini Kaveesha Wickramasinghe",
            "email": "sachini.w@gmail.com",
            "phone": "+94776789012",
            "mobile": "+94716789012",
            "address": "No. 987, Temple Road, Anuradhapura",
            "city": "Anuradhapura",
            "country": "Sri Lanka",
            "postal_code": "50000",
            "company_name": None,
            "tax_id": None,
            "customer_type": "Regular",
            "credit_limit": 50000,
            "notes": "New customer, first purchase in electronics"
        },
        {
            "name": "Prasanna Viraj De Silva",
            "email": "prasanna.desilva@company.lk",
            "phone": "+94777890123",
            "mobile": "+94717890123",
            "address": "No. 147, Main Street, Jaffna",
            "city": "Jaffna",
            "country": "Sri Lanka",
            "postal_code": "40000",
            "company_name": "De Silva Trading",
            "tax_id": "TIN654321098",
            "customer_type": "Wholesale",
            "credit_limit": 300000,
            "notes": "Large volume orders, net 45 payment terms"
        },
        {
            "name": "Thilini Madhushani Rathnayake",
            "email": "thilini.r@gmail.com",
            "phone": "+94778901234",
            "mobile": "+94718901234",
            "address": "No. 258, Station Road, Matara",
            "city": "Matara",
            "country": "Sri Lanka",
            "postal_code": "81000",
            "company_name": None,
            "tax_id": None,
            "customer_type": "Regular",
            "credit_limit": 60000,
            "notes": "Fashion conscious, buys clothing regularly"
        },
    ]
    
    customer_ids = {}
    for c in demo_customers:
        cid = str(uuid.uuid4())
        customer_ids[c["name"]] = {"id": cid, "name": c["name"], "type": c.get("customer_type")}
        await db.customers.insert_one({
            "id": cid,
            "company_id": company_id,
            **c,
            "total_purchases": 0,
            "total_paid": 0,
            "outstanding_balance": 0,
            "is_active": True,
            "woo_customer_id": None,
            "created_at": timestamp,
            "updated_at": timestamp
        })
    
    # ============== PURCHASE ORDERS (5 POs with full details) ==============
    po_list = [
        {
            "supplier": "Tech Imports Ltd",
            "items": [
                {"sku": "ELEC-001", "qty": 50, "discount_percent": 5},
                {"sku": "ELEC-002", "qty": 30, "discount_percent": 3},
                {"sku": "ELEC-003", "qty": 25, "discount_percent": 0},
            ],
            "status": "received",
            "payment_status": "paid",
            "days_ago": 15,
            "delivery_address": "Warehouse A, No. 45, Industrial Zone, Colombo 15",
            "shipping_method": "Standard Delivery",
            "expected_delivery": 7,
            "notes": "Urgent order for holiday season stock replenishment"
        },
        {
            "supplier": "Fashion Wholesale Co",
            "items": [
                {"sku": "CLTH-001", "qty": 100, "discount_percent": 10},
                {"sku": "CLTH-002", "qty": 75, "discount_percent": 8},
                {"sku": "CLTH-003", "qty": 50, "discount_percent": 5},
            ],
            "status": "pending",
            "payment_status": "partial",
            "paid_percent": 50,
            "days_ago": 5,
            "delivery_address": "Warehouse B, No. 78, Free Trade Zone, Katunayake",
            "shipping_method": "Express Delivery",
            "expected_delivery": 3,
            "notes": "New season collection, handle with care"
        },
        {
            "supplier": "Home Essentials PVT",
            "items": [
                {"sku": "HOME-001", "qty": 40, "discount_percent": 0},
                {"sku": "HOME-002", "qty": 30, "discount_percent": 5},
                {"sku": "HOME-003", "qty": 35, "discount_percent": 0},
            ],
            "status": "pending",
            "payment_status": "unpaid",
            "days_ago": 2,
            "delivery_address": "Main Store, No. 123, Galle Road, Colombo 03",
            "shipping_method": "Standard Delivery",
            "expected_delivery": 5,
            "notes": "Q1 inventory restock"
        },
        {
            "supplier": "Sports Zone International",
            "items": [
                {"sku": "SPRT-001", "qty": 45, "discount_percent": 5},
                {"sku": "SPRT-002", "qty": 20, "discount_percent": 10},
                {"sku": "SPRT-003", "qty": 60, "discount_percent": 8},
            ],
            "status": "received",
            "payment_status": "paid",
            "days_ago": 20,
            "delivery_address": "Warehouse A, No. 45, Industrial Zone, Colombo 15",
            "shipping_method": "Standard Delivery",
            "expected_delivery": 7,
            "notes": "Fitness equipment for new gym clients"
        },
        {
            "supplier": "Global Gadgets Inc",
            "items": [
                {"sku": "ELEC-004", "qty": 100, "discount_percent": 15},
                {"sku": "CLTH-004", "qty": 80, "discount_percent": 0},
            ],
            "status": "pending",
            "payment_status": "unpaid",
            "days_ago": 1,
            "delivery_address": "Warehouse B, No. 78, Free Trade Zone, Katunayake",
            "shipping_method": "Air Freight",
            "expected_delivery": 10,
            "notes": "International order, customs clearance required"
        },
    ]
    
    po_ids = []
    for po_data in po_list:
        supplier = supplier_ids.get(po_data["supplier"])
        if not supplier:
            continue
            
        items = []
        subtotal = 0
        for item_data in po_data["items"]:
            product = product_ids.get(item_data["sku"])
            if not product:
                continue
            
            unit_price = product["cost_price"]
            discount = item_data.get("discount_percent", 0)
            discounted_price = unit_price * (1 - discount/100)
            line_total = discounted_price * item_data["qty"]
            subtotal += line_total
            
            items.append({
                "product_id": product["id"],
                "product_name": product["name"],
                "sku": item_data["sku"],
                "quantity": item_data["qty"],
                "unit_price": unit_price,
                "discount_percent": discount,
                "discounted_price": discounted_price,
                "total": line_total
            })
        
        if not items:
            continue
            
        po_id = str(uuid.uuid4())
        order_number = f"PO-{(datetime.now(timezone.utc) - timedelta(days=po_data['days_ago'])).strftime('%Y%m%d')}-{str(uuid.uuid4())[:4].upper()}"
        
        paid_amount = 0
        if po_data["payment_status"] == "paid":
            paid_amount = subtotal
        elif po_data["payment_status"] == "partial":
            paid_amount = subtotal * po_data.get("paid_percent", 50) / 100
        
        po_record = {
            "id": po_id,
            "order_number": order_number,
            "company_id": company_id,
            "supplier_id": supplier["id"],
            "supplier_name": supplier["name"],
            "items": items,
            "subtotal": subtotal,
            "tax_amount": subtotal * 0.08,  # 8% tax
            "shipping_cost": 1500,
            "total": subtotal + (subtotal * 0.08) + 1500,
            "status": po_data["status"],
            "payment_status": po_data["payment_status"],
            "paid_amount": paid_amount,
            "delivery_address": po_data["delivery_address"],
            "shipping_method": po_data["shipping_method"],
            "expected_delivery_date": (datetime.now(timezone.utc) + timedelta(days=po_data["expected_delivery"])).isoformat(),
            "notes": po_data["notes"],
            "created_by": user_id,
            "created_at": (datetime.now(timezone.utc) - timedelta(days=po_data["days_ago"])).isoformat(),
            "updated_at": timestamp
        }
        await db.purchase_orders.insert_one(po_record)
        po_ids.append({"id": po_id, "number": order_number, "status": po_data["status"], "supplier": supplier["name"]})
        
        # Create accounting entry for purchases
        await db.accounting_entries.insert_one({
            "id": str(uuid.uuid4()),
            "company_id": company_id,
            "entry_type": "expense",
            "category": "Inventory Purchases",
            "amount": po_record["total"],
            "description": f"Purchase Order {order_number} from {supplier['name']}",
            "reference_type": "purchase_order",
            "reference_id": po_id,
            "created_by": user_id,
            "created_at": (datetime.now(timezone.utc) - timedelta(days=po_data["days_ago"])).isoformat()
        })
    
    # ============== GOODS RECEIVED NOTES (3 GRNs) ==============
    grn_list = [
        {
            "supplier": "Tech Imports Ltd",
            "items": [
                {"sku": "ELEC-001", "qty": 50, "cost": 4500, "regular": 7999, "sale": 6999},
                {"sku": "ELEC-002", "qty": 30, "cost": 3500, "regular": 5999, "sale": None},
            ],
            "days_ago": 10,
            "notes": "Electronics shipment received in good condition"
        },
        {
            "supplier": "Sports Zone International",
            "items": [
                {"sku": "SPRT-001", "qty": 45, "cost": 1100, "regular": 2499, "sale": None},
                {"sku": "SPRT-002", "qty": 20, "cost": 8500, "regular": 14999, "sale": 12999},
            ],
            "days_ago": 15,
            "notes": "Sports equipment delivery complete"
        },
        {
            "supplier": "Home Essentials PVT",
            "items": [
                {"sku": "HOME-001", "qty": 40, "cost": 1500, "regular": 2999, "sale": 2499},
                {"sku": "HOME-002", "qty": 30, "cost": 1200, "regular": 2499, "sale": None},
            ],
            "days_ago": 8,
            "notes": "Home products received, quality verified"
        },
    ]
    
    for grn_data in grn_list:
        supplier = supplier_ids.get(grn_data["supplier"])
        if not supplier:
            continue
            
        grn_items = []
        total_cost = 0
        
        for item_data in grn_data["items"]:
            product = product_ids.get(item_data["sku"])
            if not product:
                continue
                
            line_cost = item_data["cost"] * item_data["qty"]
            total_cost += line_cost
            
            grn_items.append({
                "product_id": product["id"],
                "product_name": product["name"],
                "sku": item_data["sku"],
                "quantity": item_data["qty"],
                "cost_price": item_data["cost"],
                "regular_price": item_data["regular"],
                "sale_price": item_data["sale"],
                "total_cost": line_cost
            })
        
        if not grn_items:
            continue
            
        grn_id = str(uuid.uuid4())
        grn_number = f"GRN-{(datetime.now(timezone.utc) - timedelta(days=grn_data['days_ago'])).strftime('%Y%m%d')}-{str(uuid.uuid4())[:4].upper()}"
        
        await db.grns.insert_one({
            "id": grn_id,
            "grn_number": grn_number,
            "company_id": company_id,
            "supplier_id": supplier["id"],
            "supplier_name": supplier["name"],
            "received_date": (datetime.now(timezone.utc) - timedelta(days=grn_data["days_ago"])).isoformat(),
            "items": grn_items,
            "total_cost": total_cost,
            "status": "received",
            "notes": grn_data["notes"],
            "sync_to_woo": True,
            "woo_sync_status": "pending",
            "created_by": user_id,
            "created_at": (datetime.now(timezone.utc) - timedelta(days=grn_data["days_ago"])).isoformat()
        })
        
        # Create double-entry journal entry for GRN
        await db.journal_entries.insert_one({
            "id": str(uuid.uuid4()),
            "company_id": company_id,
            "date": (datetime.now(timezone.utc) - timedelta(days=grn_data["days_ago"])).isoformat(),
            "description": f"Inventory Purchase - {grn_number} from {supplier['name']}",
            "reference_type": "grn",
            "reference_id": grn_id,
            "entries": [
                {"account_code": "1300", "account_name": "Inventory", "debit": total_cost, "credit": 0},
                {"account_code": "2100", "account_name": "Accounts Payable", "debit": 0, "credit": total_cost}
            ],
            "total_debit": total_cost,
            "total_credit": total_cost,
            "status": "posted",
            "is_auto_generated": True,
            "created_by": user_id,
            "created_at": (datetime.now(timezone.utc) - timedelta(days=grn_data["days_ago"])).isoformat()
        })
    
    # ============== SALES ORDERS (8 orders with full details) ==============
    sales_list = [
        {
            "customer": "Kasun Rajitha Perera",
            "items": [
                {"sku": "ELEC-001", "qty": 2},
                {"sku": "ELEC-003", "qty": 1},
                {"sku": "HOME-001", "qty": 1},
            ],
            "status": "completed",
            "payment_status": "paid",
            "payment_method": "Bank Transfer",
            "days_ago": 12,
            "shipping_address": "No. 123, Galle Road, Colombo 03",
            "notes": "VIP customer order - express shipping"
        },
        {
            "customer": "Nimali Jayasinghe Silva",
            "items": [
                {"sku": "HOME-001", "qty": 2},
                {"sku": "HOME-002", "qty": 1},
                {"sku": "HOME-004", "qty": 1},
            ],
            "status": "completed",
            "payment_status": "paid",
            "payment_method": "Cash",
            "days_ago": 10,
            "shipping_address": "No. 456, Kandy Road, Peradeniya",
            "notes": "Gift wrapping requested"
        },
        {
            "customer": "Ruwan Bandara Fernando",
            "items": [
                {"sku": "CLTH-001", "qty": 25},
                {"sku": "CLTH-002", "qty": 15},
                {"sku": "CLTH-003", "qty": 10},
                {"sku": "CLTH-004", "qty": 20},
            ],
            "status": "processing",
            "payment_status": "partial",
            "paid_percent": 60,
            "payment_method": "Bank Transfer",
            "days_ago": 5,
            "shipping_address": "No. 789, Beach Road, Unawatuna",
            "notes": "Wholesale order - bulk discount applied"
        },
        {
            "customer": "Dinesh Lakshman Kumara",
            "items": [
                {"sku": "SPRT-001", "qty": 5},
                {"sku": "SPRT-002", "qty": 2},
                {"sku": "SPRT-003", "qty": 3},
            ],
            "status": "completed",
            "payment_status": "paid",
            "payment_method": "Credit Card",
            "days_ago": 8,
            "shipping_address": "No. 654, Lake Road, Negombo",
            "notes": "Gym equipment order"
        },
        {
            "customer": "Sachini Kaveesha Wickramasinghe",
            "items": [
                {"sku": "ELEC-002", "qty": 1},
                {"sku": "ELEC-004", "qty": 2},
            ],
            "status": "pending",
            "payment_status": "unpaid",
            "payment_method": None,
            "days_ago": 2,
            "shipping_address": "No. 987, Temple Road, Anuradhapura",
            "notes": "Awaiting payment confirmation"
        },
        {
            "customer": "Prasanna Viraj De Silva",
            "items": [
                {"sku": "ELEC-001", "qty": 30},
                {"sku": "ELEC-002", "qty": 20},
                {"sku": "ELEC-003", "qty": 15},
                {"sku": "ELEC-004", "qty": 50},
            ],
            "status": "processing",
            "payment_status": "partial",
            "paid_percent": 40,
            "payment_method": "Bank Transfer",
            "days_ago": 3,
            "shipping_address": "No. 147, Main Street, Jaffna",
            "notes": "Large wholesale order - net 45 terms"
        },
        {
            "customer": "Thilini Madhushani Rathnayake",
            "items": [
                {"sku": "CLTH-001", "qty": 3},
                {"sku": "CLTH-002", "qty": 2},
                {"sku": "CLTH-004", "qty": 2},
            ],
            "status": "completed",
            "payment_status": "paid",
            "payment_method": "Cash",
            "days_ago": 6,
            "shipping_address": "No. 258, Station Road, Matara",
            "notes": "Regular customer - fashion items"
        },
        {
            "customer": "Chamari Dilhani Jayawardena",
            "items": [
                {"sku": "HOME-003", "qty": 2},
                {"sku": "HOME-004", "qty": 1},
                {"sku": "SPRT-001", "qty": 1},
            ],
            "status": "cancelled",
            "payment_status": "refunded",
            "payment_method": "Bank Transfer",
            "days_ago": 4,
            "shipping_address": "No. 321, Hill Street, Nuwara Eliya",
            "notes": "Order cancelled by customer - full refund processed"
        },
    ]
    
    for order_data in sales_list:
        customer = customer_ids.get(order_data["customer"])
        if not customer:
            continue
            
        items = []
        subtotal = 0
        total_cost = 0
        
        for item_data in order_data["items"]:
            product = product_ids.get(item_data["sku"])
            if not product:
                continue
            
            line_total = product["selling_price"] * item_data["qty"]
            line_cost = product["cost_price"] * item_data["qty"]
            subtotal += line_total
            total_cost += line_cost
            
            items.append({
                "product_id": product["id"],
                "product_name": product["name"],
                "sku": item_data["sku"],
                "quantity": item_data["qty"],
                "unit_price": product["selling_price"],
                "cost_price": product["cost_price"],
                "total": line_total
            })
        
        if not items:
            continue
            
        order_id = str(uuid.uuid4())
        order_number = f"SO-{(datetime.now(timezone.utc) - timedelta(days=order_data['days_ago'])).strftime('%Y%m%d')}-{str(uuid.uuid4())[:4].upper()}"
        
        discount = subtotal * 0.05 if len(items) > 3 else 0  # 5% discount for 4+ items
        tax = (subtotal - discount) * 0.08  # 8% tax
        total = subtotal - discount + tax
        
        paid_amount = 0
        if order_data["payment_status"] == "paid":
            paid_amount = total
        elif order_data["payment_status"] == "partial":
            paid_amount = total * order_data.get("paid_percent", 50) / 100
        elif order_data["payment_status"] == "refunded":
            paid_amount = 0
        
        order_record = {
            "id": order_id,
            "order_number": order_number,
            "company_id": company_id,
            "customer_id": customer["id"],
            "customer_name": customer["name"],
            "items": items,
            "subtotal": subtotal,
            "discount": discount,
            "tax": tax,
            "total": total,
            "total_cost": total_cost,
            "gross_profit": total - discount - total_cost,
            "status": order_data["status"],
            "payment_status": order_data["payment_status"],
            "payment_method": order_data.get("payment_method"),
            "paid_amount": paid_amount,
            "shipping_address": order_data["shipping_address"],
            "notes": order_data["notes"],
            "woo_order_id": None,
            "created_by": user_id,
            "created_at": (datetime.now(timezone.utc) - timedelta(days=order_data["days_ago"])).isoformat(),
            "updated_at": timestamp
        }
        await db.sales_orders.insert_one(order_record)
        
        # Create journal entries for completed/processing orders
        if order_data["status"] not in ["cancelled", "returned"]:
            # Revenue entry
            await db.journal_entries.insert_one({
                "id": str(uuid.uuid4()),
                "company_id": company_id,
                "date": (datetime.now(timezone.utc) - timedelta(days=order_data["days_ago"])).isoformat(),
                "description": f"Sales Revenue - {order_number}",
                "reference_type": "sales_order",
                "reference_id": order_id,
                "entries": [
                    {
                        "account_code": "1200" if order_data["payment_status"] != "paid" else "1100",
                        "account_name": "Accounts Receivable" if order_data["payment_status"] != "paid" else "Cash/Bank",
                        "debit": total,
                        "credit": 0
                    },
                    {"account_code": "4100", "account_name": "Sales Revenue", "debit": 0, "credit": total}
                ],
                "total_debit": total,
                "total_credit": total,
                "status": "posted",
                "is_auto_generated": True,
                "created_by": user_id,
                "created_at": (datetime.now(timezone.utc) - timedelta(days=order_data["days_ago"])).isoformat()
            })
            
            # COGS entry
            if total_cost > 0:
                await db.journal_entries.insert_one({
                    "id": str(uuid.uuid4()),
                    "company_id": company_id,
                    "date": (datetime.now(timezone.utc) - timedelta(days=order_data["days_ago"])).isoformat(),
                    "description": f"Cost of Goods Sold - {order_number}",
                    "reference_type": "sales_order",
                    "reference_id": order_id,
                    "entries": [
                        {"account_code": "5100", "account_name": "Cost of Goods Sold", "debit": total_cost, "credit": 0},
                        {"account_code": "1300", "account_name": "Inventory", "debit": 0, "credit": total_cost}
                    ],
                    "total_debit": total_cost,
                    "total_credit": total_cost,
                    "status": "posted",
                    "is_auto_generated": True,
                    "created_by": user_id,
                    "created_at": (datetime.now(timezone.utc) - timedelta(days=order_data["days_ago"])).isoformat()
                })
        
        # Create accounting entry
        if order_data["status"] not in ["cancelled"]:
            await db.accounting_entries.insert_one({
                "id": str(uuid.uuid4()),
                "company_id": company_id,
                "entry_type": "income" if order_data["status"] != "cancelled" else "expense",
                "category": "Sales Revenue",
                "amount": total if order_data["status"] != "cancelled" else -total,
                "description": f"Sales Order {order_number} - {customer['name']}",
                "reference_type": "sales_order",
                "reference_id": order_id,
                "created_by": user_id,
                "created_at": (datetime.now(timezone.utc) - timedelta(days=order_data["days_ago"])).isoformat()
            })
    
    # ============== INITIALIZE CHART OF ACCOUNTS ==============
    default_accounts = [
        # Assets (1xxx)
        {"code": "1100", "name": "Cash/Bank", "category": "Assets", "type": "debit", "balance": 500000},
        {"code": "1200", "name": "Accounts Receivable", "category": "Assets", "type": "debit", "balance": 125000},
        {"code": "1300", "name": "Inventory", "category": "Assets", "type": "debit", "balance": 850000},
        {"code": "1400", "name": "Prepaid Expenses", "category": "Assets", "type": "debit", "balance": 25000},
        {"code": "1500", "name": "Fixed Assets", "category": "Assets", "type": "debit", "balance": 1500000},
        
        # Liabilities (2xxx)
        {"code": "2100", "name": "Accounts Payable", "category": "Liabilities", "type": "credit", "balance": 175000},
        {"code": "2200", "name": "Accrued Expenses", "category": "Liabilities", "type": "credit", "balance": 35000},
        {"code": "2300", "name": "VAT Payable", "category": "Liabilities", "type": "credit", "balance": 45000},
        {"code": "2400", "name": "Short-term Loans", "category": "Liabilities", "type": "credit", "balance": 200000},
        
        # Equity (3xxx)
        {"code": "3100", "name": "Owner's Capital", "category": "Equity", "type": "credit", "balance": 2000000},
        {"code": "3200", "name": "Retained Earnings", "category": "Equity", "type": "credit", "balance": 350000},
        {"code": "3300", "name": "Current Year Earnings", "category": "Equity", "type": "credit", "balance": 95000},
        
        # Revenue (4xxx)
        {"code": "4100", "name": "Sales Revenue", "category": "Revenue", "type": "credit", "balance": 1250000},
        {"code": "4200", "name": "Sales Returns & Allowances", "category": "Revenue", "type": "debit", "balance": 15000},
        {"code": "4300", "name": "Service Revenue", "category": "Revenue", "type": "credit", "balance": 75000},
        {"code": "4400", "name": "Other Income", "category": "Revenue", "type": "credit", "balance": 25000},
        
        # Expenses (5xxx)
        {"code": "5100", "name": "Cost of Goods Sold", "category": "Expenses", "type": "debit", "balance": 750000},
        {"code": "5200", "name": "Salaries & Wages", "category": "Expenses", "type": "debit", "balance": 180000},
        {"code": "5300", "name": "Rent Expense", "category": "Expenses", "type": "debit", "balance": 60000},
        {"code": "5400", "name": "Utilities Expense", "category": "Expenses", "type": "debit", "balance": 25000},
        {"code": "5500", "name": "Marketing Expense", "category": "Expenses", "type": "debit", "balance": 35000},
        {"code": "5600", "name": "Office Supplies", "category": "Expenses", "type": "debit", "balance": 12000},
        {"code": "5700", "name": "Depreciation Expense", "category": "Expenses", "type": "debit", "balance": 45000},
        {"code": "5800", "name": "Insurance Expense", "category": "Expenses", "type": "debit", "balance": 18000},
    ]
    
    for acc in default_accounts:
        await db.accounts.insert_one({
            "id": str(uuid.uuid4()),
            "company_id": company_id,
            **acc,
            "current_balance": acc["balance"],
            "is_system": True,
            "created_at": timestamp
        })
    
    # ============== NOTIFICATIONS ==============
    notifications = [
        {"type": "low_stock", "title": "Low Stock Alert", "message": "Adjustable Dumbbell Set is running low (40 units remaining)", "priority": "high"},
        {"type": "payment", "title": "Payment Received", "message": "Payment of LKR 45,000 received from Kasun Rajitha Perera", "priority": "normal"},
        {"type": "order", "title": "New Order", "message": "New wholesale order received from Prasanna Viraj De Silva", "priority": "high"},
        {"type": "system", "title": "System Update", "message": "WooCommerce sync completed successfully", "priority": "low"},
    ]
    
    for notif in notifications:
        await db.notifications.insert_one({
            "id": str(uuid.uuid4()),
            "company_id": company_id,
            "user_id": user_id,
            **notif,
            "is_read": False,
            "created_at": timestamp
        })
    
    return {
        "message": "Comprehensive demo data seeded successfully",
        "data_created": {
            "suppliers": len(demo_suppliers),
            "products": len(demo_products),
            "customers": len(demo_customers),
            "purchase_orders": len(po_list),
            "grns": len(grn_list),
            "sales_orders": len(sales_list),
            "accounts": len(default_accounts),
            "notifications": len(notifications)
        }
    }

# ============== ROOT ROUTE ==============

@api_router.get("/")
async def root():
    return {"message": "E1 ERP System API", "version": "2.0.0"}

# Include the router in the main app
app.include_router(api_router)

# Import and configure new modular routers
from routes import finance, admin, woocommerce, grn, simple_finance

# Set database and auth for finance router
finance.set_db(db)
finance.set_auth_dependency(get_current_user)
app.include_router(finance.router, prefix="/api")

# Set database and auth for admin router
admin.set_db(db)
admin.set_auth_dependency(get_current_user)
app.include_router(admin.router, prefix="/api")

# Set database and auth for woocommerce router
woocommerce.set_db(db)
woocommerce.set_auth_dependency(get_current_user)
app.include_router(woocommerce.router, prefix="/api")

# Set database and auth for GRN router
grn.set_db(db)
app.include_router(grn.router, prefix="/api")

# Set database for simple finance router
simple_finance.set_db(db)
app.include_router(simple_finance.router, prefix="/api")

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    """Start background tasks on application startup"""
    # Start WooCommerce auto-sync scheduler
    woocommerce.start_auto_sync_scheduler()
    logger.info("Application started with auto-sync scheduler")

@app.on_event("shutdown")
async def shutdown_db_client():
    # Stop auto-sync scheduler
    woocommerce.stop_auto_sync_scheduler()
    client.close()
    logger.info("Application shutdown complete")
