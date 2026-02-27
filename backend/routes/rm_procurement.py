"""
Raw Material Procurement Module Router
Handles RM Suppliers, RM Purchase Orders, RM GRN, and RM GRN Returns
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List
from datetime import datetime, timezone
from pydantic import BaseModel
from enum import Enum

from utils.helpers import serialize_doc, generate_id, get_current_timestamp
from utils.auth import get_current_user

router = APIRouter(prefix="/rm-procurement", tags=["RM Procurement"])

# Database will be injected from main app
db = None

def set_db(database):
    global db
    db = database

# ============== ENUMS ==============

class PaymentTerms(str, Enum):
    IMMEDIATE = "immediate"
    NET_30 = "net_30"
    NET_60 = "net_60"
    NET_90 = "net_90"

class Priority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class RMPOStatus(str, Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    PARTIALLY_RECEIVED = "partially_received"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class RMGRNStatus(str, Enum):
    RECEIVED = "received"
    PARTIAL_RETURN = "partial_return"
    RETURNED = "returned"

# ============== MODELS ==============

# RM Supplier Models
class RMSupplierCreate(BaseModel):
    name: str
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    default_payment_terms: PaymentTerms = PaymentTerms.NET_30
    notes: Optional[str] = None

class RMSupplierUpdate(BaseModel):
    name: Optional[str] = None
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    default_payment_terms: Optional[PaymentTerms] = None
    notes: Optional[str] = None

# RM PO Models
class RMPOItem(BaseModel):
    raw_material_id: str
    quantity: float
    unit_price: float

class RMPOCreate(BaseModel):
    supplier_id: str
    items: List[RMPOItem]
    payment_terms: PaymentTerms = PaymentTerms.NET_30
    priority: Priority = Priority.NORMAL
    expected_delivery_date: Optional[str] = None
    expiry_date: Optional[str] = None
    notes: Optional[str] = None

class RMPOUpdate(BaseModel):
    items: Optional[List[RMPOItem]] = None
    payment_terms: Optional[PaymentTerms] = None
    priority: Optional[Priority] = None
    expected_delivery_date: Optional[str] = None
    expiry_date: Optional[str] = None
    notes: Optional[str] = None

# RM GRN Models
class RMGRNItem(BaseModel):
    raw_material_id: str
    po_item_index: int  # Index in PO items array
    received_quantity: float
    unit_price: float

class RMGRNCreate(BaseModel):
    rm_po_id: str
    items: List[RMGRNItem]
    received_date: Optional[str] = None
    reference_number: Optional[str] = None
    bank_account_id: Optional[str] = None  # For immediate payment
    notes: Optional[str] = None

# RM GRN Return Models
class RMGRNReturnItem(BaseModel):
    raw_material_id: str
    return_quantity: float
    reason: str

class RMGRNReturnCreate(BaseModel):
    rm_grn_id: str
    items: List[RMGRNReturnItem]
    settlement_type: str  # 'refund' or 'credit'
    refund_account_id: Optional[str] = None  # For refund
    notes: Optional[str] = None


# ============== RM SUPPLIERS ENDPOINTS ==============

@router.get("/suppliers")
async def get_rm_suppliers(
    search: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all raw material suppliers"""
    query = {"company_id": current_user["company_id"]}
    
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"contact_person": {"$regex": search, "$options": "i"}}
        ]
    
    suppliers = await db.rm_suppliers.find(query, {"_id": 0}).sort("name", 1).to_list(500)
    return suppliers

@router.get("/suppliers/{supplier_id}")
async def get_rm_supplier(
    supplier_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get single RM supplier with stats"""
    supplier = await db.rm_suppliers.find_one(
        {"id": supplier_id, "company_id": current_user["company_id"]},
        {"_id": 0}
    )
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    # Get stats
    company_id = current_user["company_id"]
    total_orders = await db.rm_purchase_orders.count_documents({
        "company_id": company_id,
        "supplier_id": supplier_id
    })
    
    # Sum total amount
    pipeline = [
        {"$match": {"company_id": company_id, "supplier_id": supplier_id}},
        {"$group": {"_id": None, "total": {"$sum": "$total"}, "paid": {"$sum": "$paid_amount"}}}
    ]
    result = await db.rm_purchase_orders.aggregate(pipeline).to_list(1)
    stats = result[0] if result else {"total": 0, "paid": 0}
    
    supplier["total_orders"] = total_orders
    supplier["total_amount"] = stats.get("total", 0)
    supplier["outstanding_balance"] = stats.get("total", 0) - stats.get("paid", 0)
    
    return supplier

@router.post("/suppliers")
async def create_rm_supplier(
    data: RMSupplierCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new raw material supplier"""
    company_id = current_user["company_id"]
    
    # Check for duplicate name
    existing = await db.rm_suppliers.find_one({
        "company_id": company_id,
        "name": {"$regex": f"^{data.name}$", "$options": "i"}
    })
    if existing:
        raise HTTPException(status_code=400, detail="Supplier with this name already exists")
    
    supplier_id = generate_id()
    supplier = {
        "id": supplier_id,
        "company_id": company_id,
        "name": data.name,
        "contact_person": data.contact_person,
        "email": data.email,
        "phone": data.phone,
        "address": data.address,
        "default_payment_terms": data.default_payment_terms.value,
        "notes": data.notes,
        "created_at": get_current_timestamp(),
        "updated_at": get_current_timestamp()
    }
    
    await db.rm_suppliers.insert_one(supplier)
    return {"id": supplier_id, "message": "Supplier created successfully"}

@router.put("/suppliers/{supplier_id}")
async def update_rm_supplier(
    supplier_id: str,
    data: RMSupplierUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update an RM supplier"""
    company_id = current_user["company_id"]
    
    existing = await db.rm_suppliers.find_one({
        "id": supplier_id,
        "company_id": company_id
    })
    if not existing:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    update_data = {k: v.value if hasattr(v, 'value') else v for k, v in data.model_dump().items() if v is not None}
    update_data["updated_at"] = get_current_timestamp()
    
    await db.rm_suppliers.update_one({"id": supplier_id}, {"$set": update_data})
    return {"message": "Supplier updated successfully"}

@router.delete("/suppliers/{supplier_id}")
async def delete_rm_supplier(
    supplier_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete an RM supplier"""
    company_id = current_user["company_id"]
    
    # Check for existing POs
    has_orders = await db.rm_purchase_orders.find_one({
        "company_id": company_id,
        "supplier_id": supplier_id
    })
    if has_orders:
        raise HTTPException(status_code=400, detail="Cannot delete supplier with existing purchase orders")
    
    result = await db.rm_suppliers.delete_one({
        "id": supplier_id,
        "company_id": company_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    return {"message": "Supplier deleted successfully"}


# ============== RM PURCHASE ORDERS ENDPOINTS ==============

@router.get("/purchase-orders")
async def get_rm_purchase_orders(
    status: Optional[str] = None,
    supplier_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all raw material purchase orders"""
    query = {"company_id": current_user["company_id"]}
    
    if status and status != 'all':
        query["status"] = status
    if supplier_id:
        query["supplier_id"] = supplier_id
    
    orders = await db.rm_purchase_orders.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return orders

@router.get("/purchase-orders/{po_id}")
async def get_rm_purchase_order(
    po_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get single RM purchase order with details"""
    po = await db.rm_purchase_orders.find_one(
        {"id": po_id, "company_id": current_user["company_id"]},
        {"_id": 0}
    )
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    
    # Get supplier details
    supplier = await db.rm_suppliers.find_one({"id": po["supplier_id"]}, {"_id": 0, "name": 1})
    po["supplier"] = supplier
    
    # Get GRN history
    grns = await db.rm_grn.find(
        {"rm_po_id": po_id, "company_id": current_user["company_id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    po["grn_history"] = grns
    
    return po

@router.post("/purchase-orders")
async def create_rm_purchase_order(
    data: RMPOCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new raw material purchase order"""
    company_id = current_user["company_id"]
    
    # Verify supplier exists
    supplier = await db.rm_suppliers.find_one({
        "id": data.supplier_id,
        "company_id": company_id
    })
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    # Verify raw materials and build items
    items = []
    total = 0
    
    for item in data.items:
        material = await db.raw_materials.find_one({
            "id": item.raw_material_id,
            "company_id": company_id
        })
        if not material:
            raise HTTPException(status_code=404, detail=f"Raw material {item.raw_material_id} not found")
        
        line_total = item.quantity * item.unit_price
        items.append({
            "raw_material_id": item.raw_material_id,
            "raw_material_name": material["name"],
            "raw_material_sku": material["sku"],
            "unit": material["unit"],
            "quantity": item.quantity,
            "received_quantity": 0,
            "unit_price": item.unit_price,
            "line_total": round(line_total, 2)
        })
        total += line_total
    
    # Generate PO number
    count = await db.rm_purchase_orders.count_documents({"company_id": company_id})
    po_number = f"RMPO-{datetime.now(timezone.utc).strftime('%Y%m')}-{count + 1:04d}"
    
    po_id = generate_id()
    po = {
        "id": po_id,
        "po_number": po_number,
        "company_id": company_id,
        "supplier_id": data.supplier_id,
        "supplier_name": supplier["name"],
        "items": items,
        "subtotal": round(total, 2),
        "total": round(total, 2),
        "paid_amount": 0,
        "payment_terms": data.payment_terms.value,
        "payment_status": "unpaid",
        "priority": data.priority.value,
        "expected_delivery_date": data.expected_delivery_date,
        "expiry_date": data.expiry_date,
        "notes": data.notes,
        "status": RMPOStatus.DRAFT.value,
        "created_by": current_user["user_id"],
        "created_at": get_current_timestamp(),
        "updated_at": get_current_timestamp()
    }
    
    await db.rm_purchase_orders.insert_one(po)
    
    return {"id": po_id, "po_number": po_number, "total": round(total, 2), "message": "Purchase order created successfully"}

@router.put("/purchase-orders/{po_id}")
async def update_rm_purchase_order(
    po_id: str,
    data: RMPOUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update an RM purchase order (only draft status)"""
    company_id = current_user["company_id"]
    
    po = await db.rm_purchase_orders.find_one({
        "id": po_id,
        "company_id": company_id
    })
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    
    if po["status"] != RMPOStatus.DRAFT.value:
        raise HTTPException(status_code=400, detail="Can only update draft purchase orders")
    
    update_data = {}
    
    if data.items is not None:
        # Rebuild items with material details
        items = []
        total = 0
        for item in data.items:
            material = await db.raw_materials.find_one({
                "id": item.raw_material_id,
                "company_id": company_id
            })
            if not material:
                raise HTTPException(status_code=404, detail=f"Raw material {item.raw_material_id} not found")
            
            line_total = item.quantity * item.unit_price
            items.append({
                "raw_material_id": item.raw_material_id,
                "raw_material_name": material["name"],
                "raw_material_sku": material["sku"],
                "unit": material["unit"],
                "quantity": item.quantity,
                "received_quantity": 0,
                "unit_price": item.unit_price,
                "line_total": round(line_total, 2)
            })
            total += line_total
        
        update_data["items"] = items
        update_data["subtotal"] = round(total, 2)
        update_data["total"] = round(total, 2)
    
    if data.payment_terms is not None:
        update_data["payment_terms"] = data.payment_terms.value
    if data.priority is not None:
        update_data["priority"] = data.priority.value
    if data.expected_delivery_date is not None:
        update_data["expected_delivery_date"] = data.expected_delivery_date
    if data.expiry_date is not None:
        update_data["expiry_date"] = data.expiry_date
    if data.notes is not None:
        update_data["notes"] = data.notes
    
    update_data["updated_at"] = get_current_timestamp()
    
    await db.rm_purchase_orders.update_one({"id": po_id}, {"$set": update_data})
    return {"message": "Purchase order updated successfully"}

@router.post("/purchase-orders/{po_id}/approve")
async def approve_rm_purchase_order(
    po_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Approve an RM purchase order"""
    company_id = current_user["company_id"]
    
    po = await db.rm_purchase_orders.find_one({
        "id": po_id,
        "company_id": company_id
    })
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    
    if po["status"] != RMPOStatus.DRAFT.value:
        raise HTTPException(status_code=400, detail="Can only approve draft purchase orders")
    
    await db.rm_purchase_orders.update_one(
        {"id": po_id},
        {"$set": {
            "status": RMPOStatus.APPROVED.value,
            "approved_by": current_user["user_id"],
            "approved_at": get_current_timestamp(),
            "updated_at": get_current_timestamp()
        }}
    )
    
    return {"message": "Purchase order approved", "new_status": RMPOStatus.APPROVED.value}

@router.delete("/purchase-orders/{po_id}")
async def delete_rm_purchase_order(
    po_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete an RM purchase order (only draft, no payments)"""
    company_id = current_user["company_id"]
    
    po = await db.rm_purchase_orders.find_one({
        "id": po_id,
        "company_id": company_id
    })
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    
    if po["status"] != RMPOStatus.DRAFT.value:
        raise HTTPException(status_code=400, detail="Can only delete draft purchase orders")
    
    if po.get("paid_amount", 0) > 0:
        raise HTTPException(status_code=400, detail="Cannot delete purchase order with payments")
    
    await db.rm_purchase_orders.delete_one({"id": po_id})
    return {"message": "Purchase order deleted successfully"}


# ============== RM GRN (GOODS RECEIVED) ENDPOINTS ==============

@router.get("/grn")
async def get_rm_grns(
    po_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all raw material GRNs"""
    query = {"company_id": current_user["company_id"]}
    
    if po_id:
        query["rm_po_id"] = po_id
    
    grns = await db.rm_grn.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return grns

@router.get("/grn/{grn_id}")
async def get_rm_grn(
    grn_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get single RM GRN with details"""
    grn = await db.rm_grn.find_one(
        {"id": grn_id, "company_id": current_user["company_id"]},
        {"_id": 0}
    )
    if not grn:
        raise HTTPException(status_code=404, detail="GRN not found")
    
    # Get return history
    returns = await db.rm_grn_returns.find(
        {"rm_grn_id": grn_id, "company_id": current_user["company_id"]},
        {"_id": 0}
    ).to_list(100)
    grn["returns"] = returns
    
    return grn

@router.post("/grn")
async def create_rm_grn(
    data: RMGRNCreate,
    current_user: dict = Depends(get_current_user)
):
    """Receive raw materials against a purchase order"""
    company_id = current_user["company_id"]
    user_id = current_user["user_id"]
    
    # Get PO
    po = await db.rm_purchase_orders.find_one({
        "id": data.rm_po_id,
        "company_id": company_id
    })
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    
    if po["status"] not in [RMPOStatus.APPROVED.value, RMPOStatus.PARTIALLY_RECEIVED.value]:
        raise HTTPException(status_code=400, detail="Purchase order must be approved before receiving")
    
    # Validate items and calculate totals
    grn_items = []
    total_cost = 0
    
    for item in data.items:
        # Find matching PO item
        if item.po_item_index >= len(po["items"]):
            raise HTTPException(status_code=400, detail=f"Invalid PO item index: {item.po_item_index}")
        
        po_item = po["items"][item.po_item_index]
        remaining = po_item["quantity"] - po_item["received_quantity"]
        
        if item.received_quantity > remaining:
            raise HTTPException(
                status_code=400, 
                detail=f"Received quantity ({item.received_quantity}) exceeds remaining ({remaining}) for {po_item['raw_material_name']}"
            )
        
        line_total = item.received_quantity * item.unit_price
        grn_items.append({
            "raw_material_id": item.raw_material_id,
            "raw_material_name": po_item["raw_material_name"],
            "raw_material_sku": po_item["raw_material_sku"],
            "unit": po_item["unit"],
            "received_quantity": item.received_quantity,
            "unit_price": item.unit_price,
            "line_total": round(line_total, 2),
            "po_item_index": item.po_item_index
        })
        total_cost += line_total
    
    # Generate GRN number
    count = await db.rm_grn.count_documents({"company_id": company_id})
    grn_number = f"RMGRN-{datetime.now(timezone.utc).strftime('%Y%m')}-{count + 1:04d}"
    
    grn_id = generate_id()
    timestamp = get_current_timestamp()
    
    grn = {
        "id": grn_id,
        "grn_number": grn_number,
        "company_id": company_id,
        "rm_po_id": data.rm_po_id,
        "po_number": po["po_number"],
        "supplier_id": po["supplier_id"],
        "supplier_name": po["supplier_name"],
        "items": grn_items,
        "total_cost": round(total_cost, 2),
        "received_date": data.received_date or timestamp[:10],
        "reference_number": data.reference_number,
        "payment_terms": po["payment_terms"],
        "bank_account_id": data.bank_account_id,
        "status": RMGRNStatus.RECEIVED.value,
        "notes": data.notes,
        "received_by": user_id,
        "created_at": timestamp,
        "updated_at": timestamp
    }
    
    await db.rm_grn.insert_one(grn)
    
    # Update raw material stock
    for item in grn_items:
        await db.raw_materials.update_one(
            {"id": item["raw_material_id"]},
            {
                "$inc": {"stock_quantity": item["received_quantity"]},
                "$set": {
                    "cost_price": item["unit_price"],
                    "updated_at": timestamp
                }
            }
        )
        
        # Record stock movement
        await db.raw_material_movements.insert_one({
            "id": generate_id(),
            "company_id": company_id,
            "raw_material_id": item["raw_material_id"],
            "movement_type": "rm_grn_receipt",
            "quantity": item["received_quantity"],
            "cost_price": item["unit_price"],
            "total_cost": item["line_total"],
            "reference": grn_number,
            "grn_id": grn_id,
            "created_by": user_id,
            "created_at": timestamp
        })
    
    # Update PO received quantities
    updated_items = []
    all_received = True
    for idx, po_item in enumerate(po["items"]):
        new_received = po_item["received_quantity"]
        # Check if this item was in GRN
        for grn_item in grn_items:
            if grn_item["po_item_index"] == idx:
                new_received += grn_item["received_quantity"]
                break
        
        updated_item = {**po_item, "received_quantity": new_received}
        updated_items.append(updated_item)
        
        if new_received < po_item["quantity"]:
            all_received = False
    
    new_status = RMPOStatus.COMPLETED.value if all_received else RMPOStatus.PARTIALLY_RECEIVED.value
    
    await db.rm_purchase_orders.update_one(
        {"id": data.rm_po_id},
        {"$set": {
            "items": updated_items,
            "status": new_status,
            "updated_at": timestamp
        }}
    )
    
    # Create financial entries
    if po["payment_terms"] == PaymentTerms.IMMEDIATE.value and data.bank_account_id:
        # Immediate payment - deduct from bank/cash
        await create_rm_payment_entry(
            company_id=company_id,
            grn_id=grn_id,
            grn_number=grn_number,
            amount=total_cost,
            bank_account_id=data.bank_account_id,
            description=f"RM Purchase: {grn_number} from {po['supplier_name']}",
            user_id=user_id
        )
        
        # Update PO payment
        new_paid = po.get("paid_amount", 0) + total_cost
        payment_status = "paid" if new_paid >= po["total"] else "partial"
        await db.rm_purchase_orders.update_one(
            {"id": data.rm_po_id},
            {"$set": {
                "paid_amount": new_paid,
                "payment_status": payment_status,
                "updated_at": timestamp
            }}
        )
    else:
        # Credit terms - create AP entry
        await create_rm_ap_entry(
            company_id=company_id,
            po_id=data.rm_po_id,
            grn_id=grn_id,
            grn_number=grn_number,
            supplier_name=po["supplier_name"],
            amount=total_cost,
            payment_terms=po["payment_terms"],
            description=f"RM Purchase AP: {grn_number}",
            user_id=user_id
        )
    
    return {
        "id": grn_id,
        "grn_number": grn_number,
        "total_cost": round(total_cost, 2),
        "po_status": new_status,
        "message": "Goods received successfully"
    }


# ============== RM GRN RETURNS ENDPOINTS ==============

@router.get("/grn-returns")
async def get_rm_grn_returns(
    grn_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all raw material GRN returns"""
    query = {"company_id": current_user["company_id"]}
    
    if grn_id:
        query["rm_grn_id"] = grn_id
    
    returns = await db.rm_grn_returns.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return returns

@router.post("/grn-returns")
async def create_rm_grn_return(
    data: RMGRNReturnCreate,
    current_user: dict = Depends(get_current_user)
):
    """Return raw materials from a GRN"""
    company_id = current_user["company_id"]
    user_id = current_user["user_id"]
    
    # Get GRN
    grn = await db.rm_grn.find_one({
        "id": data.rm_grn_id,
        "company_id": company_id
    })
    if not grn:
        raise HTTPException(status_code=404, detail="GRN not found")
    
    if grn["status"] == RMGRNStatus.RETURNED.value:
        raise HTTPException(status_code=400, detail="GRN already fully returned")
    
    # Validate return quantities
    return_items = []
    total_return_cost = 0
    
    for return_item in data.items:
        # Find item in GRN
        grn_item = None
        for gi in grn["items"]:
            if gi["raw_material_id"] == return_item.raw_material_id:
                grn_item = gi
                break
        
        if not grn_item:
            raise HTTPException(status_code=400, detail=f"Raw material {return_item.raw_material_id} not found in GRN")
        
        # Calculate already returned quantity for this item
        existing_returns = await db.rm_grn_returns.find({
            "rm_grn_id": data.rm_grn_id,
            "items.raw_material_id": return_item.raw_material_id
        }).to_list(100)
        
        already_returned = 0
        for er in existing_returns:
            for ei in er.get("items", []):
                if ei["raw_material_id"] == return_item.raw_material_id:
                    already_returned += ei.get("return_quantity", 0)
        
        available_to_return = grn_item["received_quantity"] - already_returned
        
        if return_item.return_quantity > available_to_return:
            raise HTTPException(
                status_code=400,
                detail=f"Return quantity ({return_item.return_quantity}) exceeds available ({available_to_return}) for {grn_item['raw_material_name']}"
            )
        
        line_cost = return_item.return_quantity * grn_item["unit_price"]
        return_items.append({
            "raw_material_id": return_item.raw_material_id,
            "raw_material_name": grn_item["raw_material_name"],
            "return_quantity": return_item.return_quantity,
            "unit_price": grn_item["unit_price"],
            "line_cost": round(line_cost, 2),
            "reason": return_item.reason
        })
        total_return_cost += line_cost
    
    # Generate return number
    count = await db.rm_grn_returns.count_documents({"company_id": company_id})
    return_number = f"RMRET-{datetime.now(timezone.utc).strftime('%Y%m')}-{count + 1:04d}"
    
    return_id = generate_id()
    timestamp = get_current_timestamp()
    
    return_record = {
        "id": return_id,
        "return_number": return_number,
        "company_id": company_id,
        "rm_grn_id": data.rm_grn_id,
        "grn_number": grn["grn_number"],
        "rm_po_id": grn["rm_po_id"],
        "supplier_id": grn["supplier_id"],
        "supplier_name": grn["supplier_name"],
        "items": return_items,
        "total_cost": round(total_return_cost, 2),
        "settlement_type": data.settlement_type,
        "refund_account_id": data.refund_account_id,
        "notes": data.notes,
        "created_by": user_id,
        "created_at": timestamp
    }
    
    await db.rm_grn_returns.insert_one(return_record)
    
    # Deduct stock
    for item in return_items:
        await db.raw_materials.update_one(
            {"id": item["raw_material_id"]},
            {
                "$inc": {"stock_quantity": -item["return_quantity"]},
                "$set": {"updated_at": timestamp}
            }
        )
        
        # Record stock movement
        await db.raw_material_movements.insert_one({
            "id": generate_id(),
            "company_id": company_id,
            "raw_material_id": item["raw_material_id"],
            "movement_type": "rm_grn_return",
            "quantity": -item["return_quantity"],
            "cost_price": item["unit_price"],
            "total_cost": -item["line_cost"],
            "reference": return_number,
            "grn_return_id": return_id,
            "created_by": user_id,
            "created_at": timestamp
        })
    
    # Update GRN status
    # Check if fully returned
    total_received = sum(i["received_quantity"] for i in grn["items"])
    all_returns = await db.rm_grn_returns.find({"rm_grn_id": data.rm_grn_id}).to_list(100)
    total_returned = 0
    for r in all_returns:
        total_returned += sum(i.get("return_quantity", 0) for i in r.get("items", []))
    
    new_grn_status = RMGRNStatus.RETURNED.value if total_returned >= total_received else RMGRNStatus.PARTIAL_RETURN.value
    
    await db.rm_grn.update_one(
        {"id": data.rm_grn_id},
        {"$set": {"status": new_grn_status, "updated_at": timestamp}}
    )
    
    # Handle financial reversal
    if data.settlement_type == "refund" and data.refund_account_id:
        # Credit the refund to bank/cash
        await create_rm_refund_entry(
            company_id=company_id,
            return_id=return_id,
            return_number=return_number,
            amount=total_return_cost,
            bank_account_id=data.refund_account_id,
            description=f"RM Return Refund: {return_number}",
            user_id=user_id
        )
        
        # Update PO paid amount
        po = await db.rm_purchase_orders.find_one({"id": grn["rm_po_id"]})
        if po:
            new_paid = max(0, po.get("paid_amount", 0) - total_return_cost)
            payment_status = "paid" if new_paid >= po["total"] else ("partial" if new_paid > 0 else "unpaid")
            await db.rm_purchase_orders.update_one(
                {"id": grn["rm_po_id"]},
                {"$set": {
                    "paid_amount": new_paid,
                    "payment_status": payment_status,
                    "updated_at": timestamp
                }}
            )
    elif data.settlement_type == "credit":
        # Create supplier credit note
        await create_rm_credit_note(
            company_id=company_id,
            return_id=return_id,
            return_number=return_number,
            supplier_id=grn["supplier_id"],
            supplier_name=grn["supplier_name"],
            amount=total_return_cost,
            user_id=user_id
        )
    
    return {
        "id": return_id,
        "return_number": return_number,
        "total_cost": round(total_return_cost, 2),
        "grn_status": new_grn_status,
        "message": "Return processed successfully"
    }


# ============== PAYMENT ENDPOINTS ==============

@router.post("/purchase-orders/{po_id}/record-payment")
async def record_rm_po_payment(
    po_id: str,
    amount: float,
    bank_account_id: str,
    notes: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Record payment for an RM purchase order (for credit terms)"""
    company_id = current_user["company_id"]
    user_id = current_user["user_id"]
    
    po = await db.rm_purchase_orders.find_one({
        "id": po_id,
        "company_id": company_id
    })
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    
    balance = po["total"] - po.get("paid_amount", 0)
    if amount > balance:
        raise HTTPException(status_code=400, detail=f"Payment amount ({amount}) exceeds balance ({balance})")
    
    timestamp = get_current_timestamp()
    
    # Create payment entry
    await create_rm_payment_entry(
        company_id=company_id,
        grn_id=None,
        grn_number=None,
        po_id=po_id,
        po_number=po["po_number"],
        amount=amount,
        bank_account_id=bank_account_id,
        description=f"RM PO Payment: {po['po_number']} - {notes or ''}",
        user_id=user_id
    )
    
    # Update PO
    new_paid = po.get("paid_amount", 0) + amount
    payment_status = "paid" if new_paid >= po["total"] else "partial"
    
    await db.rm_purchase_orders.update_one(
        {"id": po_id},
        {"$set": {
            "paid_amount": new_paid,
            "payment_status": payment_status,
            "updated_at": timestamp
        }}
    )
    
    # Reduce AP if exists
    await db.rm_accounts_payable.update_one(
        {"rm_po_id": po_id, "company_id": company_id},
        {"$inc": {"paid_amount": amount}, "$set": {"updated_at": timestamp}}
    )
    
    return {
        "message": "Payment recorded successfully",
        "new_paid_amount": new_paid,
        "payment_status": payment_status
    }


# ============== ACCOUNTS PAYABLE ==============

@router.get("/accounts-payable")
async def get_rm_accounts_payable(
    supplier_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get raw material accounts payable"""
    query = {"company_id": current_user["company_id"]}
    
    if supplier_id:
        query["supplier_id"] = supplier_id
    
    # Get unpaid/partial POs
    po_query = {
        "company_id": current_user["company_id"],
        "payment_status": {"$ne": "paid"},
        "status": {"$in": [RMPOStatus.PARTIALLY_RECEIVED.value, RMPOStatus.COMPLETED.value]}
    }
    if supplier_id:
        po_query["supplier_id"] = supplier_id
    
    pos = await db.rm_purchase_orders.find(po_query, {"_id": 0}).to_list(1000)
    
    payables = []
    for po in pos:
        balance = po["total"] - po.get("paid_amount", 0)
        if balance > 0:
            payables.append({
                "po_id": po["id"],
                "po_number": po["po_number"],
                "supplier_id": po["supplier_id"],
                "supplier_name": po["supplier_name"],
                "total": po["total"],
                "paid": po.get("paid_amount", 0),
                "balance": balance,
                "payment_terms": po["payment_terms"],
                "created_at": po["created_at"]
            })
    
    total_payable = sum(p["balance"] for p in payables)
    
    return {
        "items": payables,
        "total_payable": round(total_payable, 2)
    }


# ============== HELPER FUNCTIONS ==============

async def create_rm_payment_entry(
    company_id: str,
    amount: float,
    bank_account_id: str,
    description: str,
    user_id: str,
    grn_id: str = None,
    grn_number: str = None,
    po_id: str = None,
    po_number: str = None
):
    """Create journal entry for RM payment (debit inventory, credit bank)"""
    timestamp = get_current_timestamp()
    
    # Get bank account
    bank_account = await db.bank_accounts.find_one({
        "id": bank_account_id,
        "company_id": company_id
    })
    
    if not bank_account:
        # Try chart of accounts
        bank_account = await db.accounts.find_one({
            "id": bank_account_id,
            "company_id": company_id
        })
    
    if not bank_account:
        return
    
    entry_id = generate_id()
    ref_number = grn_number or po_number or f"RMPAY-{entry_id[:6]}"
    
    journal_entry = {
        "id": entry_id,
        "company_id": company_id,
        "entry_number": ref_number,
        "date": timestamp,
        "description": description,
        "reference_type": "rm_purchase",
        "reference_id": grn_id or po_id,
        "lines": [
            {
                "account_id": "1200",
                "account_name": "Raw Materials Inventory",
                "debit": amount,
                "credit": 0
            },
            {
                "account_id": bank_account.get("chart_account_id", bank_account_id),
                "account_name": bank_account.get("account_name", bank_account.get("name", "Bank")),
                "debit": 0,
                "credit": amount
            }
        ],
        "total_debit": amount,
        "total_credit": amount,
        "is_auto_generated": True,
        "transaction_type": "rm_purchase",
        "created_by": user_id,
        "created_at": timestamp
    }
    
    await db.journal_entries.insert_one(journal_entry)
    
    # Update bank balance
    await db.bank_accounts.update_one(
        {"id": bank_account_id},
        {
            "$inc": {"current_balance": -amount},
            "$set": {"updated_at": timestamp}
        }
    )

async def create_rm_ap_entry(
    company_id: str,
    po_id: str,
    grn_id: str,
    grn_number: str,
    supplier_name: str,
    amount: float,
    payment_terms: str,
    description: str,
    user_id: str
):
    """Create accounts payable entry for credit purchase"""
    timestamp = get_current_timestamp()
    
    # Check if AP entry exists for this PO
    existing = await db.rm_accounts_payable.find_one({
        "company_id": company_id,
        "rm_po_id": po_id
    })
    
    if existing:
        # Update existing AP
        await db.rm_accounts_payable.update_one(
            {"id": existing["id"]},
            {
                "$inc": {"amount": amount},
                "$push": {"grn_ids": grn_id},
                "$set": {"updated_at": timestamp}
            }
        )
    else:
        # Create new AP entry
        ap_id = generate_id()
        await db.rm_accounts_payable.insert_one({
            "id": ap_id,
            "company_id": company_id,
            "rm_po_id": po_id,
            "grn_ids": [grn_id],
            "supplier_name": supplier_name,
            "amount": amount,
            "paid_amount": 0,
            "payment_terms": payment_terms,
            "created_at": timestamp,
            "updated_at": timestamp
        })
    
    # Create journal entry: Dr. Raw Materials, Cr. Accounts Payable
    entry_id = generate_id()
    journal_entry = {
        "id": entry_id,
        "company_id": company_id,
        "entry_number": grn_number,
        "date": timestamp,
        "description": description,
        "reference_type": "rm_purchase_ap",
        "reference_id": grn_id,
        "lines": [
            {
                "account_id": "1200",
                "account_name": "Raw Materials Inventory",
                "debit": amount,
                "credit": 0
            },
            {
                "account_id": "2100",
                "account_name": "Accounts Payable",
                "debit": 0,
                "credit": amount
            }
        ],
        "total_debit": amount,
        "total_credit": amount,
        "is_auto_generated": True,
        "transaction_type": "rm_purchase_ap",
        "created_by": user_id,
        "created_at": timestamp
    }
    
    await db.journal_entries.insert_one(journal_entry)

async def create_rm_refund_entry(
    company_id: str,
    return_id: str,
    return_number: str,
    amount: float,
    bank_account_id: str,
    description: str,
    user_id: str
):
    """Create journal entry for RM return refund"""
    timestamp = get_current_timestamp()
    
    bank_account = await db.bank_accounts.find_one({
        "id": bank_account_id,
        "company_id": company_id
    })
    
    if not bank_account:
        return
    
    entry_id = generate_id()
    journal_entry = {
        "id": entry_id,
        "company_id": company_id,
        "entry_number": return_number,
        "date": timestamp,
        "description": description,
        "reference_type": "rm_return_refund",
        "reference_id": return_id,
        "lines": [
            {
                "account_id": bank_account.get("chart_account_id", bank_account_id),
                "account_name": bank_account.get("account_name", "Bank"),
                "debit": amount,
                "credit": 0
            },
            {
                "account_id": "1200",
                "account_name": "Raw Materials Inventory",
                "debit": 0,
                "credit": amount
            }
        ],
        "total_debit": amount,
        "total_credit": amount,
        "is_auto_generated": True,
        "transaction_type": "rm_return_refund",
        "created_by": user_id,
        "created_at": timestamp
    }
    
    await db.journal_entries.insert_one(journal_entry)
    
    # Update bank balance
    await db.bank_accounts.update_one(
        {"id": bank_account_id},
        {
            "$inc": {"current_balance": amount},
            "$set": {"updated_at": timestamp}
        }
    )

async def create_rm_credit_note(
    company_id: str,
    return_id: str,
    return_number: str,
    supplier_id: str,
    supplier_name: str,
    amount: float,
    user_id: str
):
    """Create supplier credit note for return"""
    timestamp = get_current_timestamp()
    
    credit_note_id = generate_id()
    credit_note_number = f"RMCN-{return_number[6:]}"
    
    await db.rm_supplier_credits.insert_one({
        "id": credit_note_id,
        "credit_note_number": credit_note_number,
        "company_id": company_id,
        "supplier_id": supplier_id,
        "supplier_name": supplier_name,
        "rm_grn_return_id": return_id,
        "amount": amount,
        "used_amount": 0,
        "status": "active",
        "created_by": user_id,
        "created_at": timestamp
    })
    
    # Create journal entry: Dr. Accounts Payable, Cr. Raw Materials
    entry_id = generate_id()
    journal_entry = {
        "id": entry_id,
        "company_id": company_id,
        "entry_number": credit_note_number,
        "date": timestamp,
        "description": f"Supplier Credit Note: {credit_note_number} - {supplier_name}",
        "reference_type": "rm_credit_note",
        "reference_id": credit_note_id,
        "lines": [
            {
                "account_id": "2100",
                "account_name": "Accounts Payable",
                "debit": amount,
                "credit": 0
            },
            {
                "account_id": "1200",
                "account_name": "Raw Materials Inventory",
                "debit": 0,
                "credit": amount
            }
        ],
        "total_debit": amount,
        "total_credit": amount,
        "is_auto_generated": True,
        "transaction_type": "rm_credit_note",
        "created_by": user_id,
        "created_at": timestamp
    }
    
    await db.journal_entries.insert_one(journal_entry)
