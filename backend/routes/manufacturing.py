"""
Manufacturing Module Router
Handles Raw Materials, Bill of Materials (BOM), Work Orders, and Production
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Optional, List
from datetime import datetime, timezone
from pydantic import BaseModel
from enum import Enum

from utils.helpers import serialize_doc, generate_id, get_current_timestamp
from utils.auth import get_current_user

router = APIRouter(prefix="/manufacturing", tags=["Manufacturing"])

# Database will be injected from main app
db = None

def set_db(database):
    global db
    db = database

# ============== ENUMS ==============

class WorkOrderStatus(str, Enum):
    DRAFT = "draft"
    MATERIALS_ISSUED = "materials_issued"
    IN_PROGRESS = "in_progress"
    QC_PENDING = "qc_pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class WorkOrderType(str, Enum):
    MAKE_TO_STOCK = "make_to_stock"
    MAKE_TO_ORDER = "make_to_order"

class QCStatus(str, Enum):
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"
    PARTIAL = "partial"

# ============== MODELS ==============

# Raw Materials Models
class RawMaterialCreate(BaseModel):
    sku: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    unit: str = "piece"  # piece, meter, kg, liter, roll, etc.
    cost_price: float = 0.0
    stock_quantity: float = 0.0
    low_stock_threshold: float = 10.0
    supplier_id: Optional[str] = None

class RawMaterialUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    unit: Optional[str] = None
    cost_price: Optional[float] = None
    stock_quantity: Optional[float] = None
    low_stock_threshold: Optional[float] = None
    supplier_id: Optional[str] = None

# BOM Models
class BOMComponent(BaseModel):
    raw_material_id: str
    quantity: float
    unit: str
    wastage_percent: float = 0.0  # Expected wastage %
    notes: Optional[str] = None

class BOMCreate(BaseModel):
    product_id: str  # Finished product
    variation_id: Optional[str] = None  # For variable products
    components: List[BOMComponent]
    labor_cost_per_unit: float = 0.0
    overhead_percent: float = 0.0  # % of material + labor
    notes: Optional[str] = None

class BOMUpdate(BaseModel):
    components: Optional[List[BOMComponent]] = None
    labor_cost_per_unit: Optional[float] = None
    overhead_percent: Optional[float] = None
    notes: Optional[str] = None

# Work Order Models
class WorkOrderCreate(BaseModel):
    product_id: str
    variation_id: Optional[str] = None
    quantity: int
    order_type: WorkOrderType = WorkOrderType.MAKE_TO_STOCK
    sales_order_id: Optional[str] = None  # For make-to-order
    planned_start_date: Optional[str] = None
    planned_end_date: Optional[str] = None
    notes: Optional[str] = None

class WorkOrderUpdate(BaseModel):
    quantity: Optional[int] = None
    planned_start_date: Optional[str] = None
    planned_end_date: Optional[str] = None
    notes: Optional[str] = None

class QCInspectionCreate(BaseModel):
    work_order_id: str
    quantity_passed: int
    quantity_failed: int = 0
    failure_reason: Optional[str] = None
    notes: Optional[str] = None

# ============== RAW MATERIALS ENDPOINTS ==============

@router.get("/raw-materials")
async def get_raw_materials(
    search: Optional[str] = None,
    category: Optional[str] = None,
    low_stock: Optional[bool] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all raw materials"""
    query = {"company_id": current_user["company_id"]}
    
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"sku": {"$regex": search, "$options": "i"}}
        ]
    
    if category:
        query["category"] = category
    
    materials = await db.raw_materials.find(query, {"_id": 0}).sort("name", 1).to_list(1000)
    
    if low_stock:
        materials = [m for m in materials if m["stock_quantity"] <= m["low_stock_threshold"]]
    
    return materials

@router.get("/raw-materials/categories")
async def get_raw_material_categories(current_user: dict = Depends(get_current_user)):
    """Get unique raw material categories"""
    pipeline = [
        {"$match": {"company_id": current_user["company_id"]}},
        {"$group": {"_id": "$category"}},
        {"$match": {"_id": {"$ne": None}}},
        {"$sort": {"_id": 1}}
    ]
    result = await db.raw_materials.aggregate(pipeline).to_list(100)
    return [r["_id"] for r in result if r["_id"]]

@router.get("/raw-materials/next-sku")
async def get_next_raw_material_sku(current_user: dict = Depends(get_current_user)):
    """Generate next SKU for raw material"""
    company_id = current_user["company_id"]
    prefix = "RM"
    
    # Find the highest SKU number
    last_material = await db.raw_materials.find_one(
        {"company_id": company_id, "sku": {"$regex": f"^{prefix}"}},
        sort=[("sku", -1)]
    )
    
    if last_material:
        try:
            last_num = int(last_material["sku"].replace(prefix, ""))
            next_num = last_num + 1
        except ValueError:
            next_num = 1
    else:
        next_num = 1
    
    return {"next_sku": f"{prefix}{next_num:04d}"}

@router.get("/raw-materials/{material_id}")
async def get_raw_material(
    material_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get single raw material"""
    material = await db.raw_materials.find_one(
        {"id": material_id, "company_id": current_user["company_id"]},
        {"_id": 0}
    )
    if not material:
        raise HTTPException(status_code=404, detail="Raw material not found")
    return material

@router.post("/raw-materials")
async def create_raw_material(
    data: RawMaterialCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new raw material"""
    company_id = current_user["company_id"]
    
    # Check SKU uniqueness
    existing = await db.raw_materials.find_one({
        "sku": data.sku,
        "company_id": company_id
    })
    if existing:
        raise HTTPException(status_code=400, detail="SKU already exists")
    
    material_id = generate_id()
    material = {
        "id": material_id,
        "company_id": company_id,
        "sku": data.sku,
        "name": data.name,
        "description": data.description,
        "category": data.category,
        "unit": data.unit,
        "cost_price": data.cost_price,
        "stock_quantity": data.stock_quantity,
        "low_stock_threshold": data.low_stock_threshold,
        "supplier_id": data.supplier_id,
        "created_at": get_current_timestamp(),
        "updated_at": get_current_timestamp()
    }
    
    await db.raw_materials.insert_one(material)
    
    return {"id": material_id, "message": "Raw material created successfully"}

@router.put("/raw-materials/{material_id}")
async def update_raw_material(
    material_id: str,
    data: RawMaterialUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update a raw material"""
    company_id = current_user["company_id"]
    
    existing = await db.raw_materials.find_one({
        "id": material_id,
        "company_id": company_id
    })
    if not existing:
        raise HTTPException(status_code=404, detail="Raw material not found")
    
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    update_data["updated_at"] = get_current_timestamp()
    
    await db.raw_materials.update_one(
        {"id": material_id},
        {"$set": update_data}
    )
    
    return {"message": "Raw material updated successfully"}

@router.delete("/raw-materials/{material_id}")
async def delete_raw_material(
    material_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a raw material"""
    company_id = current_user["company_id"]
    
    # Check if used in any BOM
    bom_usage = await db.bill_of_materials.find_one({
        "company_id": company_id,
        "components.raw_material_id": material_id
    })
    if bom_usage:
        raise HTTPException(
            status_code=400, 
            detail="Cannot delete: Raw material is used in Bill of Materials"
        )
    
    result = await db.raw_materials.delete_one({
        "id": material_id,
        "company_id": company_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Raw material not found")
    
    return {"message": "Raw material deleted successfully"}

# ============== RAW MATERIAL STOCK ==============

@router.post("/raw-materials/{material_id}/add-stock")
async def add_raw_material_stock(
    material_id: str,
    quantity: float,
    total_cost: float,
    bank_account_id: Optional[str] = None,
    cost_price: Optional[float] = None,
    reference: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Add stock to raw material (e.g., from purchase) with financial entries"""
    company_id = current_user["company_id"]
    user_id = current_user["user_id"]
    
    material = await db.raw_materials.find_one({
        "id": material_id,
        "company_id": company_id
    })
    if not material:
        raise HTTPException(status_code=404, detail="Raw material not found")
    
    # Calculate total cost if not provided
    unit_cost = cost_price if cost_price is not None else material["cost_price"]
    calculated_total = total_cost if total_cost > 0 else (unit_cost * quantity)
    
    # Update stock and cost price
    update_data = {
        "stock_quantity": material["stock_quantity"] + quantity,
        "updated_at": get_current_timestamp()
    }
    
    if cost_price is not None:
        update_data["cost_price"] = cost_price
    
    await db.raw_materials.update_one(
        {"id": material_id},
        {"$set": update_data}
    )
    
    # Record stock movement
    movement_id = generate_id()
    await db.raw_material_movements.insert_one({
        "id": movement_id,
        "company_id": company_id,
        "raw_material_id": material_id,
        "movement_type": "receipt",
        "quantity": quantity,
        "cost_price": unit_cost,
        "total_cost": calculated_total,
        "bank_account_id": bank_account_id,
        "reference": reference,
        "created_by": user_id,
        "created_at": get_current_timestamp()
    })
    
    # Create journal entry if bank account provided (immediate payment)
    if bank_account_id and calculated_total > 0:
        # Get bank account details
        bank_account = await db.bank_accounts.find_one({
            "id": bank_account_id,
            "company_id": company_id
        })
        
        if bank_account:
            # Debit: Raw Materials Inventory (1200)
            # Credit: Bank/Cash Account
            entry_id = generate_id()
            timestamp = get_current_timestamp()
            
            journal_entry = {
                "id": entry_id,
                "company_id": company_id,
                "entry_number": f"RM-{material['sku']}-{movement_id[:6]}",
                "date": timestamp,
                "description": f"Raw material purchase: {material['name']} - {quantity} {material['unit']}",
                "reference_type": "raw_material_receipt",
                "reference_id": movement_id,
                "lines": [
                    {
                        "account_id": "1200",  # Raw Materials Inventory
                        "account_name": "Raw Materials Inventory",
                        "debit": calculated_total,
                        "credit": 0
                    },
                    {
                        "account_id": bank_account.get("chart_account_id", "1100"),
                        "account_name": bank_account["account_name"],
                        "debit": 0,
                        "credit": calculated_total
                    }
                ],
                "total_debit": calculated_total,
                "total_credit": calculated_total,
                "is_auto_generated": True,
                "transaction_type": "raw_material_purchase",
                "created_by": user_id,
                "created_at": timestamp
            }
            
            await db.journal_entries.insert_one(journal_entry)
            
            # Update bank account balance
            await db.bank_accounts.update_one(
                {"id": bank_account_id},
                {
                    "$inc": {"current_balance": -calculated_total},
                    "$set": {"updated_at": timestamp}
                }
            )
            
            # Update Chart of Accounts balances
            # Increase Raw Materials Inventory (Asset - debit increases)
            await db.chart_of_accounts.update_one(
                {"company_id": company_id, "account_code": "1200"},
                {"$inc": {"balance": calculated_total}}
            )
            
            # Decrease Bank/Cash (Asset - credit decreases)
            bank_chart_code = bank_account.get("chart_account_id", "1100")
            await db.chart_of_accounts.update_one(
                {"company_id": company_id, "account_code": bank_chart_code},
                {"$inc": {"balance": -calculated_total}}
            )
    
    return {
        "message": "Stock added successfully",
        "new_quantity": material["stock_quantity"] + quantity,
        "total_cost": calculated_total,
        "journal_entry_created": bank_account_id is not None and calculated_total > 0
    }

# ============== BILL OF MATERIALS (BOM) ENDPOINTS ==============

@router.get("/bom")
async def get_all_boms(
    product_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all Bill of Materials"""
    query = {"company_id": current_user["company_id"]}
    
    if product_id:
        query["product_id"] = product_id
    
    boms = await db.bill_of_materials.find(query, {"_id": 0}).to_list(1000)
    
    # Enrich with product and material details
    for bom in boms:
        # Get product details
        product = await db.products.find_one({"id": bom["product_id"]}, {"_id": 0, "name": 1, "sku": 1})
        bom["product_name"] = product["name"] if product else "Unknown"
        bom["product_sku"] = product["sku"] if product else ""
        
        # Get variation details if applicable
        if bom.get("variation_id"):
            variation = await db.product_variations.find_one({"id": bom["variation_id"]}, {"_id": 0, "variation_name": 1, "sku": 1})
            bom["variation_name"] = variation["variation_name"] if variation else ""
            bom["variation_sku"] = variation["sku"] if variation else ""
        
        # Calculate total material cost
        total_material_cost = 0
        for comp in bom.get("components", []):
            material = await db.raw_materials.find_one({"id": comp["raw_material_id"]}, {"_id": 0, "name": 1, "cost_price": 1})
            if material:
                comp["material_name"] = material["name"]
                comp["material_cost"] = material["cost_price"]
                # Include wastage in calculation
                effective_qty = comp["quantity"] * (1 + comp.get("wastage_percent", 0) / 100)
                comp["line_cost"] = effective_qty * material["cost_price"]
                total_material_cost += comp["line_cost"]
        
        bom["total_material_cost"] = round(total_material_cost, 2)
        bom["total_labor_cost"] = bom.get("labor_cost_per_unit", 0)
        bom["overhead_cost"] = round((total_material_cost + bom["total_labor_cost"]) * bom.get("overhead_percent", 0) / 100, 2)
        bom["total_cost_per_unit"] = round(total_material_cost + bom["total_labor_cost"] + bom["overhead_cost"], 2)
    
    return boms

@router.get("/bom/{bom_id}")
async def get_bom(
    bom_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get single BOM with full details"""
    bom = await db.bill_of_materials.find_one(
        {"id": bom_id, "company_id": current_user["company_id"]},
        {"_id": 0}
    )
    if not bom:
        raise HTTPException(status_code=404, detail="BOM not found")
    
    # Enrich with details (same as above)
    product = await db.products.find_one({"id": bom["product_id"]}, {"_id": 0, "name": 1, "sku": 1})
    bom["product_name"] = product["name"] if product else "Unknown"
    bom["product_sku"] = product["sku"] if product else ""
    
    if bom.get("variation_id"):
        variation = await db.product_variations.find_one({"id": bom["variation_id"]}, {"_id": 0, "variation_name": 1, "sku": 1})
        bom["variation_name"] = variation["variation_name"] if variation else ""
    
    total_material_cost = 0
    for comp in bom.get("components", []):
        material = await db.raw_materials.find_one({"id": comp["raw_material_id"]}, {"_id": 0, "name": 1, "cost_price": 1, "unit": 1})
        if material:
            comp["material_name"] = material["name"]
            comp["material_cost"] = material["cost_price"]
            comp["material_unit"] = material["unit"]
            effective_qty = comp["quantity"] * (1 + comp.get("wastage_percent", 0) / 100)
            comp["line_cost"] = round(effective_qty * material["cost_price"], 2)
            total_material_cost += comp["line_cost"]
    
    bom["total_material_cost"] = round(total_material_cost, 2)
    bom["total_labor_cost"] = bom.get("labor_cost_per_unit", 0)
    bom["overhead_cost"] = round((total_material_cost + bom["total_labor_cost"]) * bom.get("overhead_percent", 0) / 100, 2)
    bom["total_cost_per_unit"] = round(total_material_cost + bom["total_labor_cost"] + bom["overhead_cost"], 2)
    
    return bom

@router.get("/bom/product/{product_id}")
async def get_bom_for_product(
    product_id: str,
    variation_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get BOM for a specific product/variation"""
    query = {
        "company_id": current_user["company_id"],
        "product_id": product_id
    }
    
    if variation_id:
        query["variation_id"] = variation_id
    else:
        query["variation_id"] = None
    
    bom = await db.bill_of_materials.find_one(query, {"_id": 0})
    
    if not bom:
        return None
    
    # Enrich with costs
    total_material_cost = 0
    for comp in bom.get("components", []):
        material = await db.raw_materials.find_one({"id": comp["raw_material_id"]}, {"_id": 0, "name": 1, "cost_price": 1})
        if material:
            comp["material_name"] = material["name"]
            comp["material_cost"] = material["cost_price"]
            effective_qty = comp["quantity"] * (1 + comp.get("wastage_percent", 0) / 100)
            comp["line_cost"] = round(effective_qty * material["cost_price"], 2)
            total_material_cost += comp["line_cost"]
    
    bom["total_material_cost"] = round(total_material_cost, 2)
    bom["total_cost_per_unit"] = round(
        total_material_cost + 
        bom.get("labor_cost_per_unit", 0) + 
        (total_material_cost + bom.get("labor_cost_per_unit", 0)) * bom.get("overhead_percent", 0) / 100,
        2
    )
    
    return bom

@router.post("/bom")
async def create_bom(
    data: BOMCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new Bill of Materials"""
    company_id = current_user["company_id"]
    
    # Verify product exists
    product = await db.products.find_one({"id": data.product_id, "company_id": company_id})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Verify variation if provided
    if data.variation_id:
        variation = await db.product_variations.find_one({
            "id": data.variation_id,
            "company_id": company_id
        })
        if not variation:
            raise HTTPException(status_code=404, detail="Variation not found")
    
    # Check for existing BOM
    existing_query = {
        "company_id": company_id,
        "product_id": data.product_id,
        "variation_id": data.variation_id
    }
    existing = await db.bill_of_materials.find_one(existing_query)
    if existing:
        raise HTTPException(
            status_code=400, 
            detail="BOM already exists for this product/variation. Use update instead."
        )
    
    # Verify all raw materials exist
    for comp in data.components:
        material = await db.raw_materials.find_one({
            "id": comp.raw_material_id,
            "company_id": company_id
        })
        if not material:
            raise HTTPException(
                status_code=404, 
                detail=f"Raw material {comp.raw_material_id} not found"
            )
    
    bom_id = generate_id()
    bom = {
        "id": bom_id,
        "company_id": company_id,
        "product_id": data.product_id,
        "variation_id": data.variation_id,
        "components": [c.model_dump() for c in data.components],
        "labor_cost_per_unit": data.labor_cost_per_unit,
        "overhead_percent": data.overhead_percent,
        "notes": data.notes,
        "created_by": current_user["user_id"],
        "created_at": get_current_timestamp(),
        "updated_at": get_current_timestamp()
    }
    
    await db.bill_of_materials.insert_one(bom)
    
    return {"id": bom_id, "message": "Bill of Materials created successfully"}

@router.put("/bom/{bom_id}")
async def update_bom(
    bom_id: str,
    data: BOMUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update a Bill of Materials"""
    company_id = current_user["company_id"]
    
    existing = await db.bill_of_materials.find_one({
        "id": bom_id,
        "company_id": company_id
    })
    if not existing:
        raise HTTPException(status_code=404, detail="BOM not found")
    
    update_data = {}
    
    if data.components is not None:
        # Verify all raw materials exist
        for comp in data.components:
            material = await db.raw_materials.find_one({
                "id": comp.raw_material_id,
                "company_id": company_id
            })
            if not material:
                raise HTTPException(
                    status_code=404,
                    detail=f"Raw material {comp.raw_material_id} not found"
                )
        update_data["components"] = [c.model_dump() for c in data.components]
    
    if data.labor_cost_per_unit is not None:
        update_data["labor_cost_per_unit"] = data.labor_cost_per_unit
    
    if data.overhead_percent is not None:
        update_data["overhead_percent"] = data.overhead_percent
    
    if data.notes is not None:
        update_data["notes"] = data.notes
    
    update_data["updated_at"] = get_current_timestamp()
    
    await db.bill_of_materials.update_one(
        {"id": bom_id},
        {"$set": update_data}
    )
    
    return {"message": "Bill of Materials updated successfully"}

@router.delete("/bom/{bom_id}")
async def delete_bom(
    bom_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a Bill of Materials"""
    company_id = current_user["company_id"]
    
    # Check if used in any active work orders
    active_wo = await db.work_orders.find_one({
        "company_id": company_id,
        "bom_id": bom_id,
        "status": {"$nin": ["completed", "cancelled"]}
    })
    if active_wo:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete: BOM is used in active work orders"
        )
    
    result = await db.bill_of_materials.delete_one({
        "id": bom_id,
        "company_id": company_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="BOM not found")
    
    return {"message": "Bill of Materials deleted successfully"}

# ============== WORK ORDER ENDPOINTS ==============

@router.get("/work-orders")
async def get_work_orders(
    status: Optional[str] = None,
    order_type: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all work orders"""
    query = {"company_id": current_user["company_id"]}
    
    if status:
        query["status"] = status
    
    if order_type:
        query["order_type"] = order_type
    
    work_orders = await db.work_orders.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    
    return work_orders

@router.get("/work-orders/{wo_id}")
async def get_work_order(
    wo_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get single work order with full details"""
    wo = await db.work_orders.find_one(
        {"id": wo_id, "company_id": current_user["company_id"]},
        {"_id": 0}
    )
    if not wo:
        raise HTTPException(status_code=404, detail="Work order not found")
    
    # Get material issuance records
    wo["material_issuances"] = await db.work_order_materials.find(
        {"work_order_id": wo_id},
        {"_id": 0}
    ).to_list(100)
    
    # Get QC inspections
    wo["qc_inspections"] = await db.quality_inspections.find(
        {"work_order_id": wo_id},
        {"_id": 0}
    ).to_list(100)
    
    return wo

@router.post("/work-orders")
async def create_work_order(
    data: WorkOrderCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new work order"""
    company_id = current_user["company_id"]
    
    # Get product details
    product = await db.products.find_one({"id": data.product_id, "company_id": company_id})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Get variation details if applicable
    variation_name = None
    if data.variation_id:
        variation = await db.product_variations.find_one({
            "id": data.variation_id,
            "company_id": company_id
        })
        if not variation:
            raise HTTPException(status_code=404, detail="Variation not found")
        variation_name = variation["variation_name"]
    
    # Get BOM for cost calculation
    bom_query = {
        "company_id": company_id,
        "product_id": data.product_id,
        "variation_id": data.variation_id
    }
    bom = await db.bill_of_materials.find_one(bom_query)
    if not bom:
        raise HTTPException(
            status_code=400,
            detail="No Bill of Materials found for this product. Create BOM first."
        )
    
    # Calculate costs
    total_material_cost = 0
    for comp in bom.get("components", []):
        material = await db.raw_materials.find_one({"id": comp["raw_material_id"]})
        if material:
            effective_qty = comp["quantity"] * (1 + comp.get("wastage_percent", 0) / 100)
            total_material_cost += effective_qty * material["cost_price"]
    
    labor_cost = bom.get("labor_cost_per_unit", 0)
    overhead_cost = (total_material_cost + labor_cost) * bom.get("overhead_percent", 0) / 100
    cost_per_unit = total_material_cost + labor_cost + overhead_cost
    
    # Generate work order number
    count = await db.work_orders.count_documents({"company_id": company_id})
    wo_number = f"WO-{datetime.now(timezone.utc).strftime('%Y%m')}-{count + 1:04d}"
    
    wo_id = generate_id()
    work_order = {
        "id": wo_id,
        "wo_number": wo_number,
        "company_id": company_id,
        "product_id": data.product_id,
        "product_name": product["name"],
        "product_sku": product["sku"],
        "variation_id": data.variation_id,
        "variation_name": variation_name,
        "bom_id": bom["id"],
        "quantity": data.quantity,
        "quantity_completed": 0,
        "quantity_passed_qc": 0,
        "quantity_failed_qc": 0,
        "order_type": data.order_type,
        "sales_order_id": data.sales_order_id,
        "status": WorkOrderStatus.DRAFT,
        "planned_start_date": data.planned_start_date,
        "planned_end_date": data.planned_end_date,
        "actual_start_date": None,
        "actual_end_date": None,
        # Costs
        "material_cost_per_unit": round(total_material_cost, 2),
        "labor_cost_per_unit": round(labor_cost, 2),
        "overhead_cost_per_unit": round(overhead_cost, 2),
        "total_cost_per_unit": round(cost_per_unit, 2),
        "estimated_total_cost": round(cost_per_unit * data.quantity, 2),
        "actual_material_cost": 0,
        "actual_labor_cost": 0,
        "actual_overhead_cost": 0,
        "actual_total_cost": 0,
        # Metadata
        "notes": data.notes,
        "created_by": current_user["user_id"],
        "created_at": get_current_timestamp(),
        "updated_at": get_current_timestamp()
    }
    
    await db.work_orders.insert_one(work_order)
    
    return {
        "id": wo_id,
        "wo_number": wo_number,
        "estimated_total_cost": work_order["estimated_total_cost"],
        "message": "Work order created successfully"
    }

@router.put("/work-orders/{wo_id}")
async def update_work_order(
    wo_id: str,
    data: WorkOrderUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update a work order (only draft status)"""
    company_id = current_user["company_id"]
    
    wo = await db.work_orders.find_one({
        "id": wo_id,
        "company_id": company_id
    })
    if not wo:
        raise HTTPException(status_code=404, detail="Work order not found")
    
    if wo["status"] != WorkOrderStatus.DRAFT:
        raise HTTPException(
            status_code=400,
            detail="Can only update work orders in Draft status"
        )
    
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    
    # Recalculate costs if quantity changed
    if "quantity" in update_data:
        update_data["estimated_total_cost"] = round(
            wo["total_cost_per_unit"] * update_data["quantity"], 2
        )
    
    update_data["updated_at"] = get_current_timestamp()
    
    await db.work_orders.update_one(
        {"id": wo_id},
        {"$set": update_data}
    )
    
    return {"message": "Work order updated successfully"}

@router.post("/work-orders/{wo_id}/issue-materials")
async def issue_materials(
    wo_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Issue materials for production (deduct from raw material stock)"""
    company_id = current_user["company_id"]
    user_id = current_user["user_id"]
    
    wo = await db.work_orders.find_one({
        "id": wo_id,
        "company_id": company_id
    })
    if not wo:
        raise HTTPException(status_code=404, detail="Work order not found")
    
    if wo["status"] != WorkOrderStatus.DRAFT:
        raise HTTPException(
            status_code=400,
            detail="Materials can only be issued for Draft work orders"
        )
    
    # Get BOM
    bom = await db.bill_of_materials.find_one({"id": wo["bom_id"]})
    if not bom:
        raise HTTPException(status_code=404, detail="BOM not found")
    
    # Check stock availability and calculate costs
    material_issues = []
    total_material_cost = 0
    insufficient_materials = []
    
    for comp in bom["components"]:
        material = await db.raw_materials.find_one({"id": comp["raw_material_id"]})
        if not material:
            continue
        
        # Calculate required quantity with wastage
        required_qty = comp["quantity"] * wo["quantity"] * (1 + comp.get("wastage_percent", 0) / 100)
        
        if material["stock_quantity"] < required_qty:
            insufficient_materials.append({
                "material": material["name"],
                "required": required_qty,
                "available": material["stock_quantity"],
                "short": required_qty - material["stock_quantity"]
            })
        else:
            material_issues.append({
                "raw_material_id": comp["raw_material_id"],
                "material_name": material["name"],
                "quantity": required_qty,
                "unit": material["unit"],
                "cost_price": material["cost_price"],
                "line_cost": round(required_qty * material["cost_price"], 2)
            })
            total_material_cost += required_qty * material["cost_price"]
    
    if insufficient_materials:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Insufficient raw materials",
                "materials": insufficient_materials
            }
        )
    
    # Deduct stock and create issuance records
    for issue in material_issues:
        # Deduct from stock
        await db.raw_materials.update_one(
            {"id": issue["raw_material_id"]},
            {"$inc": {"stock_quantity": -issue["quantity"]}}
        )
        
        # Record issuance
        await db.work_order_materials.insert_one({
            "id": generate_id(),
            "company_id": company_id,
            "work_order_id": wo_id,
            "raw_material_id": issue["raw_material_id"],
            "material_name": issue["material_name"],
            "quantity": issue["quantity"],
            "unit": issue["unit"],
            "cost_price": issue["cost_price"],
            "line_cost": issue["line_cost"],
            "issued_by": user_id,
            "issued_at": get_current_timestamp()
        })
        
        # Record stock movement
        await db.raw_material_movements.insert_one({
            "id": generate_id(),
            "company_id": company_id,
            "raw_material_id": issue["raw_material_id"],
            "movement_type": "production_issue",
            "quantity": -issue["quantity"],
            "reference": wo["wo_number"],
            "work_order_id": wo_id,
            "created_by": user_id,
            "created_at": get_current_timestamp()
        })
    
    # Update work order status and costs
    await db.work_orders.update_one(
        {"id": wo_id},
        {"$set": {
            "status": WorkOrderStatus.MATERIALS_ISSUED,
            "actual_material_cost": round(total_material_cost, 2),
            "actual_start_date": get_current_timestamp(),
            "updated_at": get_current_timestamp()
        }}
    )
    
    # Create journal entry: Dr. WIP, Cr. Raw Materials Inventory
    await create_manufacturing_journal_entry(
        company_id=company_id,
        work_order_id=wo_id,
        wo_number=wo["wo_number"],
        entry_type="material_issue",
        amount=total_material_cost,
        description=f"Materials issued for {wo['wo_number']} - {wo['product_name']}",
        user_id=user_id
    )
    
    return {
        "message": "Materials issued successfully",
        "materials_issued": len(material_issues),
        "total_material_cost": round(total_material_cost, 2),
        "new_status": WorkOrderStatus.MATERIALS_ISSUED
    }

@router.post("/work-orders/{wo_id}/start-production")
async def start_production(
    wo_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Start production on a work order"""
    company_id = current_user["company_id"]
    
    wo = await db.work_orders.find_one({
        "id": wo_id,
        "company_id": company_id
    })
    if not wo:
        raise HTTPException(status_code=404, detail="Work order not found")
    
    if wo["status"] != WorkOrderStatus.MATERIALS_ISSUED:
        raise HTTPException(
            status_code=400,
            detail="Can only start production after materials are issued"
        )
    
    await db.work_orders.update_one(
        {"id": wo_id},
        {"$set": {
            "status": WorkOrderStatus.IN_PROGRESS,
            "updated_at": get_current_timestamp()
        }}
    )
    
    return {"message": "Production started", "new_status": WorkOrderStatus.IN_PROGRESS}

@router.post("/work-orders/{wo_id}/record-production")
async def record_production(
    wo_id: str,
    quantity_completed: int,
    current_user: dict = Depends(get_current_user)
):
    """Record completed production quantity"""
    company_id = current_user["company_id"]
    
    wo = await db.work_orders.find_one({
        "id": wo_id,
        "company_id": company_id
    })
    if not wo:
        raise HTTPException(status_code=404, detail="Work order not found")
    
    if wo["status"] not in [WorkOrderStatus.MATERIALS_ISSUED, WorkOrderStatus.IN_PROGRESS]:
        raise HTTPException(
            status_code=400,
            detail="Cannot record production for this work order status"
        )
    
    new_completed = wo["quantity_completed"] + quantity_completed
    if new_completed > wo["quantity"]:
        raise HTTPException(
            status_code=400,
            detail=f"Total completed ({new_completed}) cannot exceed planned quantity ({wo['quantity']})"
        )
    
    # Record labor cost
    labor_cost = quantity_completed * wo["labor_cost_per_unit"]
    new_labor_cost = wo.get("actual_labor_cost", 0) + labor_cost
    
    await db.work_orders.update_one(
        {"id": wo_id},
        {"$set": {
            "quantity_completed": new_completed,
            "actual_labor_cost": round(new_labor_cost, 2),
            "status": WorkOrderStatus.IN_PROGRESS if new_completed < wo["quantity"] else WorkOrderStatus.QC_PENDING,
            "updated_at": get_current_timestamp()
        }}
    )
    
    # Create journal entry for labor: Dr. WIP, Cr. Manufacturing Labor
    if labor_cost > 0:
        await create_manufacturing_journal_entry(
            company_id=company_id,
            work_order_id=wo_id,
            wo_number=wo["wo_number"],
            entry_type="labor_cost",
            amount=labor_cost,
            description=f"Labor cost for {wo['wo_number']} - {quantity_completed} units",
            user_id=current_user["user_id"]
        )
    
    new_status = WorkOrderStatus.IN_PROGRESS if new_completed < wo["quantity"] else WorkOrderStatus.QC_PENDING
    
    return {
        "message": "Production recorded",
        "quantity_completed": new_completed,
        "quantity_remaining": wo["quantity"] - new_completed,
        "new_status": new_status
    }

@router.post("/work-orders/{wo_id}/submit-qc")
async def submit_to_qc(
    wo_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Submit work order for QC inspection"""
    company_id = current_user["company_id"]
    
    wo = await db.work_orders.find_one({
        "id": wo_id,
        "company_id": company_id
    })
    if not wo:
        raise HTTPException(status_code=404, detail="Work order not found")
    
    if wo["status"] != WorkOrderStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=400,
            detail="Can only submit in-progress work orders for QC"
        )
    
    if wo["quantity_completed"] == 0:
        raise HTTPException(
            status_code=400,
            detail="No production recorded. Record production first."
        )
    
    await db.work_orders.update_one(
        {"id": wo_id},
        {"$set": {
            "status": WorkOrderStatus.QC_PENDING,
            "updated_at": get_current_timestamp()
        }}
    )
    
    return {"message": "Submitted for QC", "new_status": WorkOrderStatus.QC_PENDING}

@router.post("/work-orders/{wo_id}/qc-inspection")
async def perform_qc_inspection(
    wo_id: str,
    data: QCInspectionCreate,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """Perform QC inspection and complete production"""
    company_id = current_user["company_id"]
    user_id = current_user["user_id"]
    
    wo = await db.work_orders.find_one({
        "id": wo_id,
        "company_id": company_id
    })
    if not wo:
        raise HTTPException(status_code=404, detail="Work order not found")
    
    if wo["status"] != WorkOrderStatus.QC_PENDING:
        raise HTTPException(
            status_code=400,
            detail="Work order must be in QC Pending status"
        )
    
    total_inspected = data.quantity_passed + data.quantity_failed
    if total_inspected > wo["quantity_completed"]:
        raise HTTPException(
            status_code=400,
            detail=f"Total inspected ({total_inspected}) cannot exceed completed ({wo['quantity_completed']})"
        )
    
    # Determine QC status
    if data.quantity_failed == 0:
        qc_status = QCStatus.PASSED
    elif data.quantity_passed == 0:
        qc_status = QCStatus.FAILED
    else:
        qc_status = QCStatus.PARTIAL
    
    # Record QC inspection
    inspection_id = generate_id()
    await db.quality_inspections.insert_one({
        "id": inspection_id,
        "company_id": company_id,
        "work_order_id": wo_id,
        "quantity_inspected": total_inspected,
        "quantity_passed": data.quantity_passed,
        "quantity_failed": data.quantity_failed,
        "status": qc_status,
        "failure_reason": data.failure_reason,
        "notes": data.notes,
        "inspected_by": user_id,
        "inspected_at": get_current_timestamp()
    })
    
    # Calculate costs
    overhead_cost = (wo["actual_material_cost"] + wo["actual_labor_cost"]) * wo["overhead_cost_per_unit"] / wo["total_cost_per_unit"] if wo["total_cost_per_unit"] > 0 else 0
    total_cost = wo["actual_material_cost"] + wo["actual_labor_cost"] + overhead_cost
    
    # Calculate cost per unit produced
    cost_per_unit = total_cost / data.quantity_passed if data.quantity_passed > 0 else 0
    scrap_cost = cost_per_unit * data.quantity_failed
    
    # Update work order
    await db.work_orders.update_one(
        {"id": wo_id},
        {"$set": {
            "quantity_passed_qc": wo.get("quantity_passed_qc", 0) + data.quantity_passed,
            "quantity_failed_qc": wo.get("quantity_failed_qc", 0) + data.quantity_failed,
            "actual_overhead_cost": round(overhead_cost, 2),
            "actual_total_cost": round(total_cost, 2),
            "status": WorkOrderStatus.COMPLETED,
            "actual_end_date": get_current_timestamp(),
            "updated_at": get_current_timestamp()
        }}
    )
    
    # Add finished goods to inventory
    if data.quantity_passed > 0:
        if wo["variation_id"]:
            # Update variation stock
            await db.product_variations.update_one(
                {"id": wo["variation_id"]},
                {
                    "$inc": {"stock_quantity": data.quantity_passed},
                    "$set": {"updated_at": get_current_timestamp()}
                }
            )
            # Also update parent product total stock
            await db.products.update_one(
                {"id": wo["product_id"]},
                {
                    "$inc": {"stock_quantity": data.quantity_passed},
                    "$set": {"updated_at": get_current_timestamp()}
                }
            )
        else:
            # Update simple product stock
            await db.products.update_one(
                {"id": wo["product_id"]},
                {
                    "$inc": {"stock_quantity": data.quantity_passed},
                    "$set": {
                        "cost_price": cost_per_unit,  # Update COGS
                        "updated_at": get_current_timestamp()
                    }
                }
            )
        
        # Record inventory movement
        await db.inventory_movements.insert_one({
            "id": generate_id(),
            "company_id": company_id,
            "product_id": wo["product_id"],
            "variation_id": wo["variation_id"],
            "movement_type": "production_receipt",
            "quantity": data.quantity_passed,
            "reference_type": "work_order",
            "reference_id": wo_id,
            "notes": f"Production completed: {wo['wo_number']}",
            "created_by": user_id,
            "created_at": get_current_timestamp()
        })
        
        # Create journal entry: Dr. Finished Goods, Cr. WIP
        await create_manufacturing_journal_entry(
            company_id=company_id,
            work_order_id=wo_id,
            wo_number=wo["wo_number"],
            entry_type="production_complete",
            amount=total_cost - scrap_cost,
            description=f"Production completed: {wo['wo_number']} - {data.quantity_passed} units",
            user_id=user_id
        )
        
        # Sync to WooCommerce in background
        background_tasks.add_task(
            sync_production_to_woo,
            company_id,
            wo["product_id"],
            wo["variation_id"]
        )
    
    # Record scrap/wastage loss
    if data.quantity_failed > 0:
        await create_manufacturing_journal_entry(
            company_id=company_id,
            work_order_id=wo_id,
            wo_number=wo["wo_number"],
            entry_type="scrap_loss",
            amount=scrap_cost,
            description=f"QC rejection/scrap: {wo['wo_number']} - {data.quantity_failed} units",
            user_id=user_id
        )
    
    return {
        "message": "QC inspection completed",
        "qc_status": qc_status,
        "quantity_passed": data.quantity_passed,
        "quantity_failed": data.quantity_failed,
        "production_cost_per_unit": round(cost_per_unit, 2),
        "total_production_cost": round(total_cost, 2),
        "scrap_cost": round(scrap_cost, 2),
        "new_status": WorkOrderStatus.COMPLETED
    }

@router.post("/work-orders/{wo_id}/cancel")
async def cancel_work_order(
    wo_id: str,
    reason: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Cancel a work order"""
    company_id = current_user["company_id"]
    
    wo = await db.work_orders.find_one({
        "id": wo_id,
        "company_id": company_id
    })
    if not wo:
        raise HTTPException(status_code=404, detail="Work order not found")
    
    if wo["status"] == WorkOrderStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail="Cannot cancel completed work orders"
        )
    
    # If materials were issued, return them to stock
    if wo["status"] in [WorkOrderStatus.MATERIALS_ISSUED, WorkOrderStatus.IN_PROGRESS, WorkOrderStatus.QC_PENDING]:
        issuances = await db.work_order_materials.find(
            {"work_order_id": wo_id}
        ).to_list(100)
        
        for issue in issuances:
            # Return stock
            await db.raw_materials.update_one(
                {"id": issue["raw_material_id"]},
                {"$inc": {"stock_quantity": issue["quantity"]}}
            )
            
            # Record return movement
            await db.raw_material_movements.insert_one({
                "id": generate_id(),
                "company_id": company_id,
                "raw_material_id": issue["raw_material_id"],
                "movement_type": "production_return",
                "quantity": issue["quantity"],
                "reference": wo["wo_number"],
                "work_order_id": wo_id,
                "created_by": current_user["user_id"],
                "created_at": get_current_timestamp()
            })
        
        # Reverse WIP journal entry
        if wo["actual_material_cost"] > 0:
            await create_manufacturing_journal_entry(
                company_id=company_id,
                work_order_id=wo_id,
                wo_number=wo["wo_number"],
                entry_type="cancel_reversal",
                amount=wo["actual_material_cost"],
                description=f"Work order cancelled: {wo['wo_number']} - Materials returned",
                user_id=current_user["user_id"]
            )
    
    await db.work_orders.update_one(
        {"id": wo_id},
        {"$set": {
            "status": WorkOrderStatus.CANCELLED,
            "cancellation_reason": reason,
            "cancelled_at": get_current_timestamp(),
            "updated_at": get_current_timestamp()
        }}
    )
    
    return {"message": "Work order cancelled", "new_status": WorkOrderStatus.CANCELLED}

# ============== HELPER FUNCTIONS ==============

async def create_manufacturing_journal_entry(
    company_id: str,
    work_order_id: str,
    wo_number: str,
    entry_type: str,
    amount: float,
    description: str,
    user_id: str
):
    """Create journal entries for manufacturing transactions"""
    
    # Define account codes for manufacturing
    ACCOUNTS = {
        "wip": "1400",  # Work in Progress (Asset)
        "raw_materials": "1200",  # Raw Materials Inventory (Asset)
        "finished_goods": "1100",  # Finished Goods Inventory (Asset)
        "manufacturing_labor": "5100",  # Manufacturing Labor (Expense)
        "manufacturing_overhead": "5200",  # Manufacturing Overhead (Expense)
        "manufacturing_loss": "5300",  # Manufacturing Loss/Scrap (Expense)
    }
    
    entry_id = generate_id()
    timestamp = get_current_timestamp()
    
    if entry_type == "material_issue":
        # Dr. WIP, Cr. Raw Materials
        entries = [
            {"account_code": ACCOUNTS["wip"], "debit": amount, "credit": 0},
            {"account_code": ACCOUNTS["raw_materials"], "debit": 0, "credit": amount}
        ]
    elif entry_type == "labor_cost":
        # Dr. WIP, Cr. Manufacturing Labor
        entries = [
            {"account_code": ACCOUNTS["wip"], "debit": amount, "credit": 0},
            {"account_code": ACCOUNTS["manufacturing_labor"], "debit": 0, "credit": amount}
        ]
    elif entry_type == "overhead_cost":
        # Dr. WIP, Cr. Manufacturing Overhead
        entries = [
            {"account_code": ACCOUNTS["wip"], "debit": amount, "credit": 0},
            {"account_code": ACCOUNTS["manufacturing_overhead"], "debit": 0, "credit": amount}
        ]
    elif entry_type == "production_complete":
        # Dr. Finished Goods, Cr. WIP
        entries = [
            {"account_code": ACCOUNTS["finished_goods"], "debit": amount, "credit": 0},
            {"account_code": ACCOUNTS["wip"], "debit": 0, "credit": amount}
        ]
    elif entry_type == "scrap_loss":
        # Dr. Manufacturing Loss, Cr. WIP
        entries = [
            {"account_code": ACCOUNTS["manufacturing_loss"], "debit": amount, "credit": 0},
            {"account_code": ACCOUNTS["wip"], "debit": 0, "credit": amount}
        ]
    elif entry_type == "cancel_reversal":
        # Reverse: Dr. Raw Materials, Cr. WIP
        entries = [
            {"account_code": ACCOUNTS["raw_materials"], "debit": amount, "credit": 0},
            {"account_code": ACCOUNTS["wip"], "debit": 0, "credit": amount}
        ]
    else:
        return
    
    journal_entry = {
        "id": entry_id,
        "company_id": company_id,
        "entry_number": f"MFG-{wo_number}",
        "date": timestamp,
        "description": description,
        "reference_type": "work_order",
        "reference_id": work_order_id,
        "entries": entries,
        "total_debit": amount,
        "total_credit": amount,
        "created_by": user_id,
        "created_at": timestamp
    }
    
    await db.journal_entries.insert_one(journal_entry)
    
    # Update account balances
    for entry in entries:
        if entry["debit"] > 0:
            await update_account_balance(company_id, entry["account_code"], entry["debit"], "debit")
        if entry["credit"] > 0:
            await update_account_balance(company_id, entry["account_code"], entry["credit"], "credit")

async def update_account_balance(company_id: str, account_code: str, amount: float, side: str):
    """Update account balance in Chart of Accounts"""
    account = await db.chart_of_accounts.find_one({
        "company_id": company_id,
        "account_code": account_code
    })
    
    if not account:
        # Create the account if it doesn't exist
        account_names = {
            "1100": "Finished Goods Inventory",
            "1200": "Raw Materials Inventory",
            "1400": "Work in Progress",
            "5100": "Manufacturing Labor",
            "5200": "Manufacturing Overhead",
            "5300": "Manufacturing Loss/Scrap"
        }
        account_types = {
            "1100": "asset",
            "1200": "asset",
            "1400": "asset",
            "5100": "expense",
            "5200": "expense",
            "5300": "expense"
        }
        
        await db.chart_of_accounts.insert_one({
            "id": generate_id(),
            "company_id": company_id,
            "account_code": account_code,
            "account_name": account_names.get(account_code, f"Account {account_code}"),
            "account_type": account_types.get(account_code, "expense"),
            "balance": 0,
            "created_at": get_current_timestamp()
        })
    
    # Update balance based on account type and side
    account = await db.chart_of_accounts.find_one({
        "company_id": company_id,
        "account_code": account_code
    })
    
    if account:
        account_type = account.get("account_type", "expense")
        
        # Assets and Expenses increase with debits
        if account_type in ["asset", "expense"]:
            if side == "debit":
                change = amount
            else:
                change = -amount
        # Liabilities, Equity, Revenue increase with credits
        else:
            if side == "credit":
                change = amount
            else:
                change = -amount
        
        await db.chart_of_accounts.update_one(
            {"company_id": company_id, "account_code": account_code},
            {"$inc": {"balance": change}}
        )

async def sync_production_to_woo(company_id: str, product_id: str, variation_id: str = None):
    """Sync production stock to WooCommerce"""
    try:
        from routes.woocommerce import get_woo_client
        
        client = await get_woo_client(company_id)
        
        if variation_id:
            # Sync variation stock
            variation = await db.product_variations.find_one({"id": variation_id})
            product = await db.products.find_one({"id": product_id})
            
            if variation and product and variation.get("woo_variation_id") and product.get("woo_product_id"):
                await client.put(
                    f"products/{product['woo_product_id']}/variations/{variation['woo_variation_id']}",
                    {
                        "stock_quantity": variation["stock_quantity"],
                        "manage_stock": True
                    }
                )
        else:
            # Sync product stock
            product = await db.products.find_one({"id": product_id})
            
            if product and product.get("woo_product_id"):
                await client.put(
                    f"products/{product['woo_product_id']}",
                    {
                        "stock_quantity": product["stock_quantity"],
                        "manage_stock": True
                    }
                )
        
        print(f"Synced production stock to WooCommerce for product {product_id}")
    except Exception as e:
        print(f"Error syncing production to WooCommerce: {e}")

# ============== DASHBOARD ENDPOINTS ==============

@router.get("/dashboard/summary")
async def get_manufacturing_dashboard(current_user: dict = Depends(get_current_user)):
    """Get manufacturing dashboard summary"""
    company_id = current_user["company_id"]
    
    # Work order counts by status
    pipeline = [
        {"$match": {"company_id": company_id}},
        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
    ]
    status_counts = await db.work_orders.aggregate(pipeline).to_list(10)
    
    # Low stock raw materials
    low_stock_materials = await db.raw_materials.find({
        "company_id": company_id,
        "$expr": {"$lte": ["$stock_quantity", "$low_stock_threshold"]}
    }, {"_id": 0, "name": 1, "stock_quantity": 1, "low_stock_threshold": 1, "unit": 1}).to_list(10)
    
    # Recent work orders
    recent_orders = await db.work_orders.find(
        {"company_id": company_id},
        {"_id": 0}
    ).sort("created_at", -1).limit(5).to_list(5)
    
    # Total production value this month
    start_of_month = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    completed_this_month = await db.work_orders.find({
        "company_id": company_id,
        "status": "completed",
        "actual_end_date": {"$gte": start_of_month.isoformat()}
    }).to_list(100)
    
    total_production_value = sum(wo.get("actual_total_cost", 0) for wo in completed_this_month)
    total_units_produced = sum(wo.get("quantity_passed_qc", 0) for wo in completed_this_month)
    
    return {
        "status_summary": {s["_id"]: s["count"] for s in status_counts},
        "low_stock_materials": low_stock_materials,
        "recent_work_orders": recent_orders,
        "this_month": {
            "production_value": round(total_production_value, 2),
            "units_produced": total_units_produced,
            "orders_completed": len(completed_this_month)
        }
    }
