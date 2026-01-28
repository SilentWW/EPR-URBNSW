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

# Product Models
class ProductCreate(BaseModel):
    sku: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    cost_price: float = 0.0
    selling_price: float = 0.0
    stock_quantity: int = 0
    low_stock_threshold: int = 10
    woo_product_id: Optional[str] = None

class ProductUpdate(BaseModel):
    sku: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    cost_price: Optional[float] = None
    selling_price: Optional[float] = None
    stock_quantity: Optional[int] = None
    low_stock_threshold: Optional[int] = None

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

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    user = await db.users.find_one({"id": current_user["user_id"]}, {"_id": 0, "password": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(**user)

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
    # Check SKU uniqueness
    existing = await db.products.find_one({
        "sku": data.sku,
        "company_id": current_user["company_id"]
    })
    if existing:
        raise HTTPException(status_code=400, detail="SKU already exists")
    
    product_id = str(uuid.uuid4())
    product = {
        "id": product_id,
        "company_id": current_user["company_id"],
        **data.model_dump(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    await db.products.insert_one(product)
    
    # Log initial inventory
    if data.stock_quantity > 0:
        await db.inventory_movements.insert_one({
            "id": str(uuid.uuid4()),
            "company_id": current_user["company_id"],
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
    # Get reference order
    if data.reference_type == "sales_order":
        order = await db.sales_orders.find_one({
            "id": data.reference_id,
            "company_id": current_user["company_id"]
        })
        if not order:
            raise HTTPException(status_code=404, detail="Sales order not found")
        
        collection = db.sales_orders
        entry_type = "income"
        category = "Sales Payment"
    elif data.reference_type == "purchase_order":
        order = await db.purchase_orders.find_one({
            "id": data.reference_id,
            "company_id": current_user["company_id"]
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
        "company_id": current_user["company_id"],
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
        "company_id": current_user["company_id"],
        "type": "credit" if entry_type == "income" else "debit",
        "amount": data.amount,
        "payment_method": data.payment_method,
        "description": f"Payment for {order.get('order_number')}",
        "reference_type": data.reference_type,
        "reference_id": data.reference_id,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
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
        return {"message": "Demo data already exists"}
    
    # Categories
    categories = ["Electronics", "Clothing", "Home & Garden", "Sports", "Books"]
    
    # Create demo products
    demo_products = [
        {"sku": "ELEC-001", "name": "Wireless Earbuds", "category": "Electronics", "cost_price": 1500, "selling_price": 2500, "stock_quantity": 50},
        {"sku": "ELEC-002", "name": "Bluetooth Speaker", "category": "Electronics", "cost_price": 3000, "selling_price": 4500, "stock_quantity": 30},
        {"sku": "ELEC-003", "name": "Smart Watch", "category": "Electronics", "cost_price": 8000, "selling_price": 12000, "stock_quantity": 25},
        {"sku": "CLTH-001", "name": "Cotton T-Shirt", "category": "Clothing", "cost_price": 500, "selling_price": 1200, "stock_quantity": 100},
        {"sku": "CLTH-002", "name": "Denim Jeans", "category": "Clothing", "cost_price": 1500, "selling_price": 3500, "stock_quantity": 60},
        {"sku": "HOME-001", "name": "LED Desk Lamp", "category": "Home & Garden", "cost_price": 800, "selling_price": 1500, "stock_quantity": 40},
        {"sku": "HOME-002", "name": "Plant Pot Set", "category": "Home & Garden", "cost_price": 600, "selling_price": 1200, "stock_quantity": 80},
        {"sku": "SPRT-001", "name": "Yoga Mat", "category": "Sports", "cost_price": 700, "selling_price": 1500, "stock_quantity": 45},
        {"sku": "SPRT-002", "name": "Dumbbells Set", "category": "Sports", "cost_price": 2000, "selling_price": 3500, "stock_quantity": 20},
        {"sku": "BOOK-001", "name": "Business Guide Book", "category": "Books", "cost_price": 400, "selling_price": 800, "stock_quantity": 70},
    ]
    
    product_ids = {}
    for p in demo_products:
        pid = str(uuid.uuid4())
        product_ids[p["sku"]] = {"id": pid, "name": p["name"], "price": p["selling_price"]}
        await db.products.insert_one({
            "id": pid,
            "company_id": company_id,
            **p,
            "low_stock_threshold": 10,
            "woo_product_id": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        })
    
    # Create demo customers
    demo_customers = [
        {"name": "Kasun Perera", "email": "kasun@example.com", "phone": "+94771234567", "address": "123 Galle Road, Colombo"},
        {"name": "Nimali Silva", "email": "nimali@example.com", "phone": "+94772345678", "address": "456 Kandy Road, Kandy"},
        {"name": "Ruwan Fernando", "email": "ruwan@example.com", "phone": "+94773456789", "address": "789 Beach Road, Galle"},
        {"name": "Chamari Jayawardena", "email": "chamari@example.com", "phone": "+94774567890", "address": "321 Hill Street, Nuwara Eliya"},
        {"name": "Dinesh Kumara", "email": "dinesh@example.com", "phone": "+94775678901", "address": "654 Lake Road, Negombo"},
    ]
    
    customer_ids = []
    for c in demo_customers:
        cid = str(uuid.uuid4())
        customer_ids.append({"id": cid, "name": c["name"]})
        await db.customers.insert_one({
            "id": cid,
            "company_id": company_id,
            **c,
            "woo_customer_id": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        })
    
    # Create demo suppliers
    demo_suppliers = [
        {"name": "Tech Imports Ltd", "email": "tech@imports.lk", "phone": "+94112345678", "contact_person": "Mr. Silva"},
        {"name": "Fashion Wholesale", "email": "fashion@wholesale.lk", "phone": "+94112345679", "contact_person": "Mrs. Fernando"},
        {"name": "Home Essentials", "email": "home@essentials.lk", "phone": "+94112345680", "contact_person": "Mr. Perera"},
    ]
    
    supplier_ids = []
    for s in demo_suppliers:
        sid = str(uuid.uuid4())
        supplier_ids.append({"id": sid, "name": s["name"]})
        await db.suppliers.insert_one({
            "id": sid,
            "company_id": company_id,
            **s,
            "address": "Colombo, Sri Lanka",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        })
    
    # Create demo sales orders
    for i, cust in enumerate(customer_ids[:3]):
        items = []
        product_list = list(product_ids.values())[:3]
        for j, prod in enumerate(product_list):
            qty = (j + 1) * 2
            items.append({
                "product_id": prod["id"],
                "product_name": prod["name"],
                "sku": list(product_ids.keys())[j],
                "quantity": qty,
                "unit_price": prod["price"],
                "total": prod["price"] * qty
            })
        
        subtotal = sum(item["total"] for item in items)
        order_id = str(uuid.uuid4())
        order_number = f"SO-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{str(uuid.uuid4())[:4].upper()}"
        
        status = ["completed", "pending", "completed"][i]
        payment_status = ["paid", "unpaid", "partial"][i]
        paid = [subtotal, 0, subtotal * 0.5][i]
        
        await db.sales_orders.insert_one({
            "id": order_id,
            "order_number": order_number,
            "company_id": company_id,
            "customer_id": cust["id"],
            "customer_name": cust["name"],
            "items": items,
            "subtotal": subtotal,
            "discount": 0,
            "tax": 0,
            "total": subtotal,
            "status": status,
            "payment_status": payment_status,
            "paid_amount": paid,
            "notes": None,
            "woo_order_id": None,
            "created_by": user_id,
            "created_at": (datetime.now(timezone.utc) - timedelta(days=i*2)).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        })
        
        # Accounting entry
        await db.accounting_entries.insert_one({
            "id": str(uuid.uuid4()),
            "company_id": company_id,
            "entry_type": "income",
            "category": "Sales",
            "amount": subtotal,
            "description": f"Sales Order {order_number}",
            "reference_type": "sales_order",
            "reference_id": order_id,
            "created_by": user_id,
            "created_at": (datetime.now(timezone.utc) - timedelta(days=i*2)).isoformat()
        })
    
    # Create demo purchase orders
    for i, supp in enumerate(supplier_ids[:2]):
        items = []
        product_list = list(product_ids.values())[i*2:(i+1)*2+1]
        for j, prod in enumerate(product_list):
            cost = prod["price"] * 0.6  # 60% of selling price
            qty = 20
            items.append({
                "product_id": prod["id"],
                "product_name": prod["name"],
                "sku": list(product_ids.keys())[i*2+j],
                "quantity": qty,
                "unit_price": cost,
                "total": cost * qty
            })
        
        subtotal = sum(item["total"] for item in items)
        order_id = str(uuid.uuid4())
        order_number = f"PO-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{str(uuid.uuid4())[:4].upper()}"
        
        await db.purchase_orders.insert_one({
            "id": order_id,
            "order_number": order_number,
            "company_id": company_id,
            "supplier_id": supp["id"],
            "supplier_name": supp["name"],
            "items": items,
            "subtotal": subtotal,
            "total": subtotal,
            "status": "received" if i == 0 else "pending",
            "payment_status": "paid" if i == 0 else "unpaid",
            "paid_amount": subtotal if i == 0 else 0,
            "notes": None,
            "created_by": user_id,
            "created_at": (datetime.now(timezone.utc) - timedelta(days=i*3)).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        })
        
        # Accounting entry
        await db.accounting_entries.insert_one({
            "id": str(uuid.uuid4()),
            "company_id": company_id,
            "entry_type": "expense",
            "category": "Purchases",
            "amount": subtotal,
            "description": f"Purchase Order {order_number}",
            "reference_type": "purchase_order",
            "reference_id": order_id,
            "created_by": user_id,
            "created_at": (datetime.now(timezone.utc) - timedelta(days=i*3)).isoformat()
        })
    
    return {"message": "Demo data seeded successfully"}

# ============== ROOT ROUTE ==============

@api_router.get("/")
async def root():
    return {"message": "E1 ERP System API", "version": "1.0.0"}

# Include the router in the main app
app.include_router(api_router)

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

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
