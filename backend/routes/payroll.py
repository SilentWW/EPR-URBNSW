"""
Payroll Module Router
Handles Departments, Employees, Salary Structure, Leave, Advances, Payroll Processing
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List
from datetime import datetime, timezone, date, timedelta
from pydantic import BaseModel
from enum import Enum
from decimal import Decimal

from utils.helpers import serialize_doc, generate_id, get_current_timestamp
from utils.auth import get_current_user

router = APIRouter(prefix="/payroll", tags=["Payroll"])

# Database will be injected from main app
db = None

def set_db(database):
    global db
    db = database

# ============== ENUMS ==============

class EmployeeType(str, Enum):
    PERMANENT = "permanent"
    CASUAL = "casual"
    FREELANCER = "freelancer"
    CONTRACT = "contract"

class EmployeeStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    TERMINATED = "terminated"

class PaymentFrequency(str, Enum):
    MONTHLY = "monthly"
    WEEKLY = "weekly"
    DAILY = "daily"
    PER_TASK = "per_task"

class LeaveType(str, Enum):
    ANNUAL = "annual"
    SICK = "sick"
    CASUAL = "casual"
    MATERNITY = "maternity"
    PATERNITY = "paternity"

class LeaveStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class PayrollStatus(str, Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    PROCESSED = "processed"
    PAID = "paid"

class AdvanceStatus(str, Enum):
    ACTIVE = "active"
    FULLY_PAID = "fully_paid"

class TaskStatus(str, Enum):
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    VERIFIED = "verified"
    CANCELLED = "cancelled"

class TaskCategory(str, Enum):
    DESIGN = "design"
    DEVELOPMENT = "development"
    MARKETING = "marketing"
    PRODUCTION = "production"
    ADMIN = "admin"
    OTHER = "other"

class AttendanceStatus(str, Enum):
    PRESENT = "present"
    ABSENT = "absent"
    HALF_DAY = "half_day"
    LATE = "late"
    ON_LEAVE = "on_leave"

# ============== MODELS ==============

# Department Models
class DepartmentCreate(BaseModel):
    name: str
    description: Optional[str] = None
    manager_id: Optional[str] = None

class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    manager_id: Optional[str] = None

# Employee Models
class EmployeeCreate(BaseModel):
    employee_id: str  # Custom employee ID like EMP001
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    nic: Optional[str] = None  # National ID
    address: Optional[str] = None
    department_id: Optional[str] = None
    employee_type: EmployeeType
    payment_frequency: PaymentFrequency = PaymentFrequency.MONTHLY
    basic_salary: float = 0
    hourly_rate: float = 0
    daily_rate: float = 0
    bank_name: Optional[str] = None
    bank_account_number: Optional[str] = None
    bank_branch: Optional[str] = None
    join_date: Optional[str] = None
    contract_end_date: Optional[str] = None
    notes: Optional[str] = None

class EmployeeUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    nic: Optional[str] = None
    address: Optional[str] = None
    department_id: Optional[str] = None
    employee_type: Optional[EmployeeType] = None
    payment_frequency: Optional[PaymentFrequency] = None
    basic_salary: Optional[float] = None
    hourly_rate: Optional[float] = None
    daily_rate: Optional[float] = None
    bank_name: Optional[str] = None
    bank_account_number: Optional[str] = None
    bank_branch: Optional[str] = None
    contract_end_date: Optional[str] = None
    status: Optional[EmployeeStatus] = None
    notes: Optional[str] = None
    user_id: Optional[str] = None  # Link employee to user account

# Allowance/Deduction Models
class AllowanceCreate(BaseModel):
    name: str
    type: str  # 'fixed' or 'percentage'
    value: float
    is_taxable: bool = True
    applies_to: List[str] = []  # Employee types it applies to, empty = all

class DeductionCreate(BaseModel):
    name: str
    type: str  # 'fixed' or 'percentage'
    value: float
    is_statutory: bool = False
    applies_to: List[str] = []

# Leave Models
class LeaveRequestCreate(BaseModel):
    employee_id: str
    leave_type: LeaveType
    start_date: str
    end_date: str
    reason: Optional[str] = None

class LeaveBalanceUpdate(BaseModel):
    annual: Optional[float] = None
    sick: Optional[float] = None
    casual: Optional[float] = None
    maternity: Optional[float] = None
    paternity: Optional[float] = None

# Advance/Loan Models
class AdvanceCreate(BaseModel):
    employee_id: str
    amount: float
    type: str  # 'advance' or 'loan'
    monthly_deduction: float
    reason: Optional[str] = None
    bank_account_id: Optional[str] = None

# Payroll Models
class PayrollCreate(BaseModel):
    period_start: str
    period_end: str
    payment_frequency: PaymentFrequency
    employee_ids: Optional[List[str]] = None  # None = all active employees

class PayrollItemAdjustment(BaseModel):
    employee_id: str
    overtime_hours: Optional[float] = None
    overtime_weekend_hours: Optional[float] = None
    bonus: Optional[float] = None
    other_allowances: Optional[float] = None
    other_deductions: Optional[float] = None
    unpaid_leave_days: Optional[float] = None
    notes: Optional[str] = None

class TaskPaymentCreate(BaseModel):
    employee_id: str
    description: str
    amount: float
    payment_date: Optional[str] = None
    bank_account_id: Optional[str] = None

# Task Assignment Models
class TaskAssignmentCreate(BaseModel):
    employee_id: str
    title: str
    description: Optional[str] = None
    category: TaskCategory
    amount: float
    due_date: Optional[str] = None
    notes: Optional[str] = None

class TaskAssignmentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[TaskCategory] = None
    amount: Optional[float] = None
    due_date: Optional[str] = None
    notes: Optional[str] = None

# Attendance Models
class AttendanceCreate(BaseModel):
    employee_id: str
    date: str  # YYYY-MM-DD
    check_in: Optional[str] = None  # HH:MM
    check_out: Optional[str] = None  # HH:MM
    status: AttendanceStatus
    notes: Optional[str] = None

class AttendanceUpdate(BaseModel):
    check_in: Optional[str] = None
    check_out: Optional[str] = None
    status: Optional[AttendanceStatus] = None
    notes: Optional[str] = None

class BulkAttendanceCreate(BaseModel):
    date: str  # YYYY-MM-DD
    records: List[dict]  # [{employee_id, status, check_in, check_out, notes}]


# ============== DEPARTMENTS ENDPOINTS ==============

@router.get("/departments")
async def get_departments(current_user: dict = Depends(get_current_user)):
    """Get all departments"""
    departments = await db.departments.find(
        {"company_id": current_user["company_id"]},
        {"_id": 0}
    ).sort("name", 1).to_list(100)
    
    # Get employee count per department
    for dept in departments:
        count = await db.employees.count_documents({
            "company_id": current_user["company_id"],
            "department_id": dept["id"],
            "status": "active"
        })
        dept["employee_count"] = count
    
    return departments

@router.post("/departments")
async def create_department(
    data: DepartmentCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new department"""
    company_id = current_user["company_id"]
    
    # Check duplicate name
    existing = await db.departments.find_one({
        "company_id": company_id,
        "name": {"$regex": f"^{data.name}$", "$options": "i"}
    })
    if existing:
        raise HTTPException(status_code=400, detail="Department with this name already exists")
    
    dept_id = generate_id()
    department = {
        "id": dept_id,
        "company_id": company_id,
        "name": data.name,
        "description": data.description,
        "manager_id": data.manager_id,
        "created_at": get_current_timestamp(),
        "updated_at": get_current_timestamp()
    }
    
    await db.departments.insert_one(department)
    return {"id": dept_id, "message": "Department created successfully"}

@router.put("/departments/{dept_id}")
async def update_department(
    dept_id: str,
    data: DepartmentUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update a department"""
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    update_data["updated_at"] = get_current_timestamp()
    
    result = await db.departments.update_one(
        {"id": dept_id, "company_id": current_user["company_id"]},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Department not found")
    
    return {"message": "Department updated successfully"}

@router.delete("/departments/{dept_id}")
async def delete_department(
    dept_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a department"""
    # Check for employees
    has_employees = await db.employees.find_one({
        "company_id": current_user["company_id"],
        "department_id": dept_id
    })
    if has_employees:
        raise HTTPException(status_code=400, detail="Cannot delete department with employees")
    
    result = await db.departments.delete_one({
        "id": dept_id,
        "company_id": current_user["company_id"]
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Department not found")
    
    return {"message": "Department deleted successfully"}


# ============== EMPLOYEES ENDPOINTS ==============

@router.get("/employees")
async def get_employees(
    department_id: Optional[str] = None,
    employee_type: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all employees with filters"""
    query = {"company_id": current_user["company_id"]}
    
    if department_id:
        query["department_id"] = department_id
    if employee_type and employee_type != 'all':
        query["employee_type"] = employee_type
    if status and status != 'all':
        query["status"] = status
    else:
        query["status"] = {"$ne": "terminated"}
    
    if search:
        query["$or"] = [
            {"first_name": {"$regex": search, "$options": "i"}},
            {"last_name": {"$regex": search, "$options": "i"}},
            {"employee_id": {"$regex": search, "$options": "i"}}
        ]
    
    employees = await db.employees.find(query, {"_id": 0}).sort("employee_id", 1).to_list(500)
    
    # Get department names
    dept_ids = list(set(e.get("department_id") for e in employees if e.get("department_id")))
    depts = {}
    if dept_ids:
        dept_docs = await db.departments.find({"id": {"$in": dept_ids}}, {"_id": 0, "id": 1, "name": 1}).to_list(100)
        depts = {d["id"]: d["name"] for d in dept_docs}
    
    for emp in employees:
        emp["department_name"] = depts.get(emp.get("department_id"), "-")
        emp["full_name"] = f"{emp['first_name']} {emp['last_name']}"
    
    return employees

@router.get("/employees/{emp_id}")
async def get_employee(
    emp_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get single employee with details"""
    employee = await db.employees.find_one(
        {"id": emp_id, "company_id": current_user["company_id"]},
        {"_id": 0}
    )
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Get department name
    if employee.get("department_id"):
        dept = await db.departments.find_one({"id": employee["department_id"]}, {"_id": 0, "name": 1})
        employee["department_name"] = dept["name"] if dept else "-"
    
    # Get leave balances
    leave_balance = await db.leave_balances.find_one(
        {"employee_id": emp_id, "company_id": current_user["company_id"]},
        {"_id": 0}
    )
    employee["leave_balance"] = leave_balance or {
        "annual": 0, "sick": 0, "casual": 0, "maternity": 0, "paternity": 0
    }
    
    # Get active advances/loans
    advances = await db.employee_advances.find(
        {"employee_id": emp_id, "company_id": current_user["company_id"], "status": "active"},
        {"_id": 0}
    ).to_list(50)
    employee["active_advances"] = advances
    employee["total_advance_balance"] = sum(a.get("remaining_amount", 0) for a in advances)
    
    employee["full_name"] = f"{employee['first_name']} {employee['last_name']}"
    
    return employee

@router.get("/employees/next-id/generate")
async def get_next_employee_id(current_user: dict = Depends(get_current_user)):
    """Generate next employee ID"""
    company_id = current_user["company_id"]
    
    # Find highest employee ID
    last_emp = await db.employees.find_one(
        {"company_id": company_id, "employee_id": {"$regex": "^EMP"}},
        sort=[("employee_id", -1)]
    )
    
    if last_emp:
        try:
            num = int(last_emp["employee_id"].replace("EMP", ""))
            next_num = num + 1
        except (ValueError, AttributeError):
            next_num = 1
    else:
        next_num = 1
    
    return {"next_id": f"EMP{next_num:04d}"}

@router.post("/employees")
async def create_employee(
    data: EmployeeCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new employee"""
    company_id = current_user["company_id"]
    
    # Check duplicate employee ID
    existing = await db.employees.find_one({
        "company_id": company_id,
        "employee_id": data.employee_id
    })
    if existing:
        raise HTTPException(status_code=400, detail="Employee ID already exists")
    
    emp_id = generate_id()
    employee = {
        "id": emp_id,
        "company_id": company_id,
        "employee_id": data.employee_id,
        "first_name": data.first_name,
        "last_name": data.last_name,
        "email": data.email,
        "phone": data.phone,
        "nic": data.nic,
        "address": data.address,
        "department_id": data.department_id,
        "employee_type": data.employee_type.value,
        "payment_frequency": data.payment_frequency.value,
        "basic_salary": data.basic_salary,
        "hourly_rate": data.hourly_rate,
        "daily_rate": data.daily_rate,
        "bank_name": data.bank_name,
        "bank_account_number": data.bank_account_number,
        "bank_branch": data.bank_branch,
        "join_date": data.join_date,
        "contract_end_date": data.contract_end_date,
        "notes": data.notes,
        "status": EmployeeStatus.ACTIVE.value,
        "created_at": get_current_timestamp(),
        "updated_at": get_current_timestamp()
    }
    
    await db.employees.insert_one(employee)
    
    # Create default leave balance
    await db.leave_balances.insert_one({
        "id": generate_id(),
        "company_id": company_id,
        "employee_id": emp_id,
        "annual": 14,  # Default annual leave
        "sick": 7,
        "casual": 7,
        "maternity": 84 if data.employee_type == EmployeeType.PERMANENT else 0,
        "paternity": 3 if data.employee_type == EmployeeType.PERMANENT else 0,
        "year": datetime.now(timezone.utc).year,
        "created_at": get_current_timestamp()
    })
    
    return {"id": emp_id, "employee_id": data.employee_id, "message": "Employee created successfully"}

@router.put("/employees/{emp_id}")
async def update_employee(
    emp_id: str,
    data: EmployeeUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update an employee"""
    update_data = {}
    for k, v in data.model_dump().items():
        if v is not None:
            if hasattr(v, 'value'):
                update_data[k] = v.value
            else:
                update_data[k] = v
    
    update_data["updated_at"] = get_current_timestamp()
    
    result = await db.employees.update_one(
        {"id": emp_id, "company_id": current_user["company_id"]},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    return {"message": "Employee updated successfully"}

@router.delete("/employees/{emp_id}")
async def terminate_employee(
    emp_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Terminate/deactivate an employee"""
    result = await db.employees.update_one(
        {"id": emp_id, "company_id": current_user["company_id"]},
        {"$set": {
            "status": EmployeeStatus.TERMINATED.value,
            "termination_date": get_current_timestamp()[:10],
            "updated_at": get_current_timestamp()
        }}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    return {"message": "Employee terminated successfully"}


# ============== SALARY STRUCTURE ENDPOINTS ==============

@router.get("/salary-structure")
async def get_salary_structure(current_user: dict = Depends(get_current_user)):
    """Get salary structure settings"""
    company_id = current_user["company_id"]
    
    # Get or create default settings
    settings = await db.payroll_settings.find_one(
        {"company_id": company_id},
        {"_id": 0}
    )
    
    if not settings:
        settings = {
            "id": generate_id(),
            "company_id": company_id,
            "epf_employee_rate": 8.0,
            "epf_employer_rate": 12.0,
            "etf_employer_rate": 3.0,
            "overtime_weekday_rate": 1.25,
            "overtime_weekend_rate": 1.5,
            "allowances": [
                {"id": generate_id(), "name": "Transport Allowance", "type": "fixed", "value": 0, "is_taxable": True, "applies_to": []},
                {"id": generate_id(), "name": "Meal Allowance", "type": "fixed", "value": 0, "is_taxable": True, "applies_to": []},
                {"id": generate_id(), "name": "Phone Allowance", "type": "fixed", "value": 0, "is_taxable": True, "applies_to": []},
                {"id": generate_id(), "name": "Housing Allowance", "type": "fixed", "value": 0, "is_taxable": True, "applies_to": []},
                {"id": generate_id(), "name": "Medical Allowance", "type": "fixed", "value": 0, "is_taxable": False, "applies_to": []},
                {"id": generate_id(), "name": "Attendance Bonus", "type": "fixed", "value": 0, "is_taxable": True, "applies_to": []},
                {"id": generate_id(), "name": "Other Allowance", "type": "fixed", "value": 0, "is_taxable": True, "applies_to": []}
            ],
            "deductions": [],
            "tax_slabs": [
                {"min": 0, "max": 100000, "rate": 0},
                {"min": 100001, "max": 141667, "rate": 6},
                {"min": 141668, "max": 183333, "rate": 12},
                {"min": 183334, "max": 225000, "rate": 18},
                {"min": 225001, "max": 266667, "rate": 24},
                {"min": 266668, "max": 308333, "rate": 30},
                {"min": 308334, "max": None, "rate": 36}
            ],
            "created_at": get_current_timestamp()
        }
        await db.payroll_settings.insert_one(settings)
        # Remove the _id field added by MongoDB insert
        settings.pop("_id", None)
    
    return settings

@router.put("/salary-structure")
async def update_salary_structure(
    data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Update salary structure settings"""
    company_id = current_user["company_id"]
    
    data["updated_at"] = get_current_timestamp()
    
    await db.payroll_settings.update_one(
        {"company_id": company_id},
        {"$set": data},
        upsert=True
    )
    
    return {"message": "Salary structure updated successfully"}

@router.post("/salary-structure/allowances")
async def add_allowance(
    data: AllowanceCreate,
    current_user: dict = Depends(get_current_user)
):
    """Add a new allowance type"""
    company_id = current_user["company_id"]
    
    allowance = {
        "id": generate_id(),
        "name": data.name,
        "type": data.type,
        "value": data.value,
        "is_taxable": data.is_taxable,
        "applies_to": data.applies_to
    }
    
    await db.payroll_settings.update_one(
        {"company_id": company_id},
        {"$push": {"allowances": allowance}}
    )
    
    return {"id": allowance["id"], "message": "Allowance added successfully"}

@router.delete("/salary-structure/allowances/{allowance_id}")
async def delete_allowance(
    allowance_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete an allowance type"""
    await db.payroll_settings.update_one(
        {"company_id": current_user["company_id"]},
        {"$pull": {"allowances": {"id": allowance_id}}}
    )
    return {"message": "Allowance deleted successfully"}


# ============== LEAVE MANAGEMENT ENDPOINTS ==============

@router.get("/leave/balances")
async def get_leave_balances(
    employee_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get leave balances for employees"""
    query = {"company_id": current_user["company_id"]}
    if employee_id:
        query["employee_id"] = employee_id
    
    balances = await db.leave_balances.find(query, {"_id": 0}).to_list(500)
    
    # Get employee names
    emp_ids = [b["employee_id"] for b in balances]
    if emp_ids:
        emps = await db.employees.find(
            {"id": {"$in": emp_ids}},
            {"_id": 0, "id": 1, "first_name": 1, "last_name": 1, "employee_id": 1}
        ).to_list(500)
        emp_map = {e["id"]: e for e in emps}
        
        for bal in balances:
            emp = emp_map.get(bal["employee_id"], {})
            bal["employee_name"] = f"{emp.get('first_name', '')} {emp.get('last_name', '')}"
            bal["employee_code"] = emp.get("employee_id", "")
    
    return balances

@router.put("/leave/balances/{employee_id}")
async def update_leave_balance(
    employee_id: str,
    data: LeaveBalanceUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update leave balance for an employee"""
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    update_data["updated_at"] = get_current_timestamp()
    
    result = await db.leave_balances.update_one(
        {"employee_id": employee_id, "company_id": current_user["company_id"]},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        # Create if not exists
        await db.leave_balances.insert_one({
            "id": generate_id(),
            "company_id": current_user["company_id"],
            "employee_id": employee_id,
            **update_data,
            "year": datetime.now(timezone.utc).year,
            "created_at": get_current_timestamp()
        })
    
    return {"message": "Leave balance updated successfully"}

@router.get("/leave/requests")
async def get_leave_requests(
    employee_id: Optional[str] = None,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get leave requests"""
    query = {"company_id": current_user["company_id"]}
    if employee_id:
        query["employee_id"] = employee_id
    if status and status != 'all':
        query["status"] = status
    
    requests = await db.leave_requests.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
    
    # Get employee names
    emp_ids = list(set(r["employee_id"] for r in requests))
    if emp_ids:
        emps = await db.employees.find(
            {"id": {"$in": emp_ids}},
            {"_id": 0, "id": 1, "first_name": 1, "last_name": 1, "employee_id": 1}
        ).to_list(500)
        emp_map = {e["id"]: e for e in emps}
        
        for req in requests:
            emp = emp_map.get(req["employee_id"], {})
            req["employee_name"] = f"{emp.get('first_name', '')} {emp.get('last_name', '')}"
            req["employee_code"] = emp.get("employee_id", "")
    
    return requests

@router.post("/leave/requests")
async def create_leave_request(
    data: LeaveRequestCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a leave request"""
    company_id = current_user["company_id"]
    
    # Verify employee exists
    employee = await db.employees.find_one({
        "id": data.employee_id,
        "company_id": company_id
    })
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Calculate days
    start = datetime.strptime(data.start_date, "%Y-%m-%d")
    end = datetime.strptime(data.end_date, "%Y-%m-%d")
    days = (end - start).days + 1
    
    # Check balance
    balance = await db.leave_balances.find_one({
        "employee_id": data.employee_id,
        "company_id": company_id
    })
    
    leave_type_key = data.leave_type.value
    available = balance.get(leave_type_key, 0) if balance else 0
    
    if days > available:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient {data.leave_type.value} leave balance. Available: {available} days, Requested: {days} days"
        )
    
    request_id = generate_id()
    leave_request = {
        "id": request_id,
        "company_id": company_id,
        "employee_id": data.employee_id,
        "leave_type": data.leave_type.value,
        "start_date": data.start_date,
        "end_date": data.end_date,
        "days": days,
        "reason": data.reason,
        "status": LeaveStatus.PENDING.value,
        "created_by": current_user["user_id"],
        "created_at": get_current_timestamp()
    }
    
    await db.leave_requests.insert_one(leave_request)
    return {"id": request_id, "days": days, "message": "Leave request created"}

@router.post("/leave/requests/{request_id}/approve")
async def approve_leave_request(
    request_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Approve a leave request"""
    company_id = current_user["company_id"]
    
    request = await db.leave_requests.find_one({
        "id": request_id,
        "company_id": company_id
    })
    if not request:
        raise HTTPException(status_code=404, detail="Leave request not found")
    
    if request["status"] != LeaveStatus.PENDING.value:
        raise HTTPException(status_code=400, detail="Request already processed")
    
    # Deduct from balance
    await db.leave_balances.update_one(
        {"employee_id": request["employee_id"], "company_id": company_id},
        {"$inc": {request["leave_type"]: -request["days"]}}
    )
    
    # Update request status
    await db.leave_requests.update_one(
        {"id": request_id},
        {"$set": {
            "status": LeaveStatus.APPROVED.value,
            "approved_by": current_user["user_id"],
            "approved_at": get_current_timestamp()
        }}
    )
    
    return {"message": "Leave request approved"}

@router.post("/leave/requests/{request_id}/reject")
async def reject_leave_request(
    request_id: str,
    reason: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Reject a leave request"""
    result = await db.leave_requests.update_one(
        {"id": request_id, "company_id": current_user["company_id"]},
        {"$set": {
            "status": LeaveStatus.REJECTED.value,
            "rejection_reason": reason,
            "rejected_by": current_user["user_id"],
            "rejected_at": get_current_timestamp()
        }}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Leave request not found")
    
    return {"message": "Leave request rejected"}


# ============== ADVANCES & LOANS ENDPOINTS ==============

@router.get("/advances")
async def get_advances(
    employee_id: Optional[str] = None,
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get employee advances and loans"""
    query = {"company_id": current_user["company_id"]}
    if employee_id:
        query["employee_id"] = employee_id
    if status and status != 'all':
        query["status"] = status
    
    advances = await db.employee_advances.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
    
    # Get employee names
    emp_ids = list(set(a["employee_id"] for a in advances))
    if emp_ids:
        emps = await db.employees.find(
            {"id": {"$in": emp_ids}},
            {"_id": 0, "id": 1, "first_name": 1, "last_name": 1, "employee_id": 1}
        ).to_list(500)
        emp_map = {e["id"]: e for e in emps}
        
        for adv in advances:
            emp = emp_map.get(adv["employee_id"], {})
            adv["employee_name"] = f"{emp.get('first_name', '')} {emp.get('last_name', '')}"
            adv["employee_code"] = emp.get("employee_id", "")
    
    return advances

@router.post("/advances")
async def create_advance(
    data: AdvanceCreate,
    current_user: dict = Depends(get_current_user)
):
    """Issue an advance or loan to employee"""
    company_id = current_user["company_id"]
    user_id = current_user["user_id"]
    
    # Verify employee
    employee = await db.employees.find_one({
        "id": data.employee_id,
        "company_id": company_id
    })
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    advance_id = generate_id()
    timestamp = get_current_timestamp()
    
    # Generate advance number
    count = await db.employee_advances.count_documents({"company_id": company_id})
    advance_number = f"ADV-{datetime.now(timezone.utc).strftime('%Y%m')}-{count + 1:04d}"
    
    advance = {
        "id": advance_id,
        "advance_number": advance_number,
        "company_id": company_id,
        "employee_id": data.employee_id,
        "type": data.type,
        "amount": data.amount,
        "remaining_amount": data.amount,
        "monthly_deduction": data.monthly_deduction,
        "total_deducted": 0,
        "reason": data.reason,
        "status": AdvanceStatus.ACTIVE.value,
        "issued_by": user_id,
        "created_at": timestamp
    }
    
    await db.employee_advances.insert_one(advance)
    
    # Create financial entry if bank account provided
    if data.bank_account_id:
        entry_id = generate_id()
        journal_entry = {
            "id": entry_id,
            "company_id": company_id,
            "entry_number": advance_number,
            "date": timestamp,
            "description": f"Advance to {employee['first_name']} {employee['last_name']} - {data.reason or 'Salary Advance'}",
            "reference_type": "employee_advance",
            "reference_id": advance_id,
            "lines": [
                {
                    "account_id": "1350",
                    "account_name": "Employee Advances",
                    "debit": data.amount,
                    "credit": 0
                },
                {
                    "account_id": data.bank_account_id,
                    "account_name": "Bank/Cash",
                    "debit": 0,
                    "credit": data.amount
                }
            ],
            "total_debit": data.amount,
            "total_credit": data.amount,
            "is_auto_generated": True,
            "transaction_type": "employee_advance",
            "created_by": user_id,
            "created_at": timestamp
        }
        await db.journal_entries.insert_one(journal_entry)
        
        # Update bank balance
        await db.bank_accounts.update_one(
            {"id": data.bank_account_id},
            {"$inc": {"current_balance": -data.amount}}
        )
    
    return {"id": advance_id, "advance_number": advance_number, "message": "Advance issued successfully"}


# ============== PAYROLL PROCESSING ENDPOINTS ==============

@router.get("/payrolls")
async def get_payrolls(
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all payroll runs"""
    query = {"company_id": current_user["company_id"]}
    if status and status != 'all':
        query["status"] = status
    
    payrolls = await db.payrolls.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    return payrolls

@router.get("/payrolls/{payroll_id}")
async def get_payroll(
    payroll_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get payroll details with all items"""
    payroll = await db.payrolls.find_one(
        {"id": payroll_id, "company_id": current_user["company_id"]},
        {"_id": 0}
    )
    if not payroll:
        raise HTTPException(status_code=404, detail="Payroll not found")
    
    # Get payroll items
    items = await db.payroll_items.find(
        {"payroll_id": payroll_id},
        {"_id": 0}
    ).to_list(500)
    
    payroll["items"] = items
    return payroll

@router.post("/payrolls")
async def create_payroll(
    data: PayrollCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new payroll run"""
    company_id = current_user["company_id"]
    user_id = current_user["user_id"]
    
    # Get salary structure settings
    settings = await db.payroll_settings.find_one(
        {"company_id": company_id},
        {"_id": 0}
    )
    if not settings:
        raise HTTPException(status_code=400, detail="Please configure salary structure first")
    
    # Get employees
    emp_query = {
        "company_id": company_id,
        "status": "active",
        "payment_frequency": data.payment_frequency.value
    }
    if data.employee_ids:
        emp_query["id"] = {"$in": data.employee_ids}
    
    employees = await db.employees.find(emp_query, {"_id": 0}).to_list(500)
    
    if not employees:
        raise HTTPException(status_code=400, detail="No employees found for this payment frequency")
    
    # Generate payroll number
    count = await db.payrolls.count_documents({"company_id": company_id})
    payroll_number = f"PAY-{datetime.now(timezone.utc).strftime('%Y%m')}-{count + 1:04d}"
    
    payroll_id = generate_id()
    timestamp = get_current_timestamp()
    
    # Calculate payroll items
    payroll_items = []
    total_gross = 0
    total_deductions = 0
    total_net = 0
    total_employer_cost = 0
    
    for emp in employees:
        item = await calculate_payroll_item(emp, settings, data.period_start, data.period_end, company_id)
        item["id"] = generate_id()
        item["payroll_id"] = payroll_id
        item["company_id"] = company_id
        item["created_at"] = timestamp
        
        payroll_items.append(item)
        total_gross += item["gross_salary"]
        total_deductions += item["total_deductions"]
        total_net += item["net_salary"]
        total_employer_cost += item["employer_cost"]
    
    # Create payroll
    payroll = {
        "id": payroll_id,
        "payroll_number": payroll_number,
        "company_id": company_id,
        "period_start": data.period_start,
        "period_end": data.period_end,
        "payment_frequency": data.payment_frequency.value,
        "employee_count": len(employees),
        "total_gross": round(total_gross, 2),
        "total_deductions": round(total_deductions, 2),
        "total_net": round(total_net, 2),
        "total_employer_cost": round(total_employer_cost, 2),
        "status": PayrollStatus.DRAFT.value,
        "created_by": user_id,
        "created_at": timestamp
    }
    
    await db.payrolls.insert_one(payroll)
    
    # Insert payroll items
    if payroll_items:
        await db.payroll_items.insert_many(payroll_items)
    
    return {
        "id": payroll_id,
        "payroll_number": payroll_number,
        "employee_count": len(employees),
        "total_net": round(total_net, 2),
        "message": "Payroll created successfully"
    }

@router.put("/payrolls/{payroll_id}/items/{item_id}")
async def update_payroll_item(
    payroll_id: str,
    item_id: str,
    data: PayrollItemAdjustment,
    current_user: dict = Depends(get_current_user)
):
    """Update/adjust a payroll item"""
    company_id = current_user["company_id"]
    
    # Verify payroll is in draft status
    payroll = await db.payrolls.find_one({"id": payroll_id, "company_id": company_id})
    if not payroll:
        raise HTTPException(status_code=404, detail="Payroll not found")
    if payroll["status"] not in [PayrollStatus.DRAFT.value, PayrollStatus.PENDING_APPROVAL.value]:
        raise HTTPException(status_code=400, detail="Cannot modify processed payroll")
    
    # Get current item
    item = await db.payroll_items.find_one({"id": item_id, "payroll_id": payroll_id})
    if not item:
        raise HTTPException(status_code=404, detail="Payroll item not found")
    
    # Get settings for recalculation
    settings = await db.payroll_settings.find_one({"company_id": company_id}, {"_id": 0})
    
    # Update fields
    update_data = {}
    if data.overtime_hours is not None:
        update_data["overtime_hours"] = data.overtime_hours
        update_data["overtime_amount"] = data.overtime_hours * item["hourly_rate"] * settings.get("overtime_weekday_rate", 1.25)
    if data.overtime_weekend_hours is not None:
        update_data["overtime_weekend_hours"] = data.overtime_weekend_hours
        weekend_amt = data.overtime_weekend_hours * item["hourly_rate"] * settings.get("overtime_weekend_rate", 1.5)
        update_data["overtime_amount"] = update_data.get("overtime_amount", item.get("overtime_amount", 0)) + weekend_amt
    if data.bonus is not None:
        update_data["bonus"] = data.bonus
    if data.other_allowances is not None:
        update_data["other_allowances"] = data.other_allowances
    if data.other_deductions is not None:
        update_data["other_deductions"] = data.other_deductions
    if data.unpaid_leave_days is not None:
        update_data["unpaid_leave_days"] = data.unpaid_leave_days
        daily_rate = item["basic_salary"] / 30
        update_data["unpaid_leave_deduction"] = data.unpaid_leave_days * daily_rate
    if data.notes is not None:
        update_data["notes"] = data.notes
    
    # Recalculate totals
    new_gross = (
        item["basic_salary"] +
        item.get("total_allowances", 0) +
        update_data.get("overtime_amount", item.get("overtime_amount", 0)) +
        update_data.get("bonus", item.get("bonus", 0)) +
        update_data.get("other_allowances", item.get("other_allowances", 0))
    )
    
    new_deductions = (
        item.get("epf_employee", 0) +
        item.get("tax", 0) +
        item.get("advance_deduction", 0) +
        update_data.get("unpaid_leave_deduction", item.get("unpaid_leave_deduction", 0)) +
        update_data.get("other_deductions", item.get("other_deductions", 0))
    )
    
    update_data["gross_salary"] = round(new_gross, 2)
    update_data["total_deductions"] = round(new_deductions, 2)
    update_data["net_salary"] = round(new_gross - new_deductions, 2)
    update_data["updated_at"] = get_current_timestamp()
    
    await db.payroll_items.update_one({"id": item_id}, {"$set": update_data})
    
    # Recalculate payroll totals
    items = await db.payroll_items.find({"payroll_id": payroll_id}, {"_id": 0}).to_list(500)
    total_gross = sum(i["gross_salary"] for i in items)
    total_deductions = sum(i["total_deductions"] for i in items)
    total_net = sum(i["net_salary"] for i in items)
    total_employer = sum(i.get("employer_cost", 0) for i in items)
    
    await db.payrolls.update_one(
        {"id": payroll_id},
        {"$set": {
            "total_gross": round(total_gross, 2),
            "total_deductions": round(total_deductions, 2),
            "total_net": round(total_net, 2),
            "total_employer_cost": round(total_employer, 2),
            "updated_at": get_current_timestamp()
        }}
    )
    
    return {"message": "Payroll item updated successfully"}

@router.post("/payrolls/{payroll_id}/submit")
async def submit_payroll_for_approval(
    payroll_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Submit payroll for approval"""
    result = await db.payrolls.update_one(
        {"id": payroll_id, "company_id": current_user["company_id"], "status": PayrollStatus.DRAFT.value},
        {"$set": {
            "status": PayrollStatus.PENDING_APPROVAL.value,
            "submitted_by": current_user["user_id"],
            "submitted_at": get_current_timestamp(),
            "updated_at": get_current_timestamp()
        }}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=400, detail="Payroll not found or not in draft status")
    
    return {"message": "Payroll submitted for approval"}

@router.post("/payrolls/{payroll_id}/approve")
async def approve_payroll(
    payroll_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Approve payroll"""
    if current_user["role"] not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Only admin or manager can approve payroll")
    
    result = await db.payrolls.update_one(
        {"id": payroll_id, "company_id": current_user["company_id"], "status": PayrollStatus.PENDING_APPROVAL.value},
        {"$set": {
            "status": PayrollStatus.APPROVED.value,
            "approved_by": current_user["user_id"],
            "approved_at": get_current_timestamp(),
            "updated_at": get_current_timestamp()
        }}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=400, detail="Payroll not found or not pending approval")
    
    return {"message": "Payroll approved"}

@router.post("/payrolls/{payroll_id}/process")
async def process_payroll(
    payroll_id: str,
    bank_account_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Process approved payroll - create financial entries and pay"""
    company_id = current_user["company_id"]
    user_id = current_user["user_id"]
    
    payroll = await db.payrolls.find_one({
        "id": payroll_id,
        "company_id": company_id,
        "status": PayrollStatus.APPROVED.value
    })
    if not payroll:
        raise HTTPException(status_code=400, detail="Payroll not found or not approved")
    
    timestamp = get_current_timestamp()
    
    # Get payroll items
    items = await db.payroll_items.find({"payroll_id": payroll_id}, {"_id": 0}).to_list(500)
    
    # Calculate totals for journal entries
    total_salaries = sum(i["gross_salary"] for i in items)
    total_epf_employee = sum(i.get("epf_employee", 0) for i in items)
    total_epf_employer = sum(i.get("epf_employer", 0) for i in items)
    total_etf = sum(i.get("etf", 0) for i in items)
    total_tax = sum(i.get("tax", 0) for i in items)
    total_advances = sum(i.get("advance_deduction", 0) for i in items)
    total_net = sum(i["net_salary"] for i in items)
    
    # Create main salary journal entry
    entry_id = generate_id()
    lines = [
        {"account_id": "6100", "account_name": "Salaries & Wages Expense", "debit": total_salaries, "credit": 0}
    ]
    
    if total_epf_employer > 0:
        lines.append({"account_id": "6110", "account_name": "EPF Employer Contribution", "debit": total_epf_employer, "credit": 0})
    if total_etf > 0:
        lines.append({"account_id": "6120", "account_name": "ETF Contribution", "debit": total_etf, "credit": 0})
    
    # Credits
    if total_epf_employee > 0:
        lines.append({"account_id": "2310", "account_name": "EPF Payable - Employee", "debit": 0, "credit": total_epf_employee})
    if total_epf_employer > 0:
        lines.append({"account_id": "2320", "account_name": "EPF Payable - Employer", "debit": 0, "credit": total_epf_employer})
    if total_etf > 0:
        lines.append({"account_id": "2330", "account_name": "ETF Payable", "debit": 0, "credit": total_etf})
    if total_tax > 0:
        lines.append({"account_id": "2340", "account_name": "PAYE Tax Payable", "debit": 0, "credit": total_tax})
    if total_advances > 0:
        lines.append({"account_id": "1350", "account_name": "Employee Advances", "debit": 0, "credit": total_advances})
    
    lines.append({"account_id": bank_account_id, "account_name": "Bank/Cash", "debit": 0, "credit": total_net})
    
    total_debit = total_salaries + total_epf_employer + total_etf
    total_credit = total_epf_employee + total_epf_employer + total_etf + total_tax + total_advances + total_net
    
    journal_entry = {
        "id": entry_id,
        "company_id": company_id,
        "entry_number": payroll["payroll_number"],
        "date": timestamp,
        "description": f"Payroll {payroll['payroll_number']} - {payroll['period_start']} to {payroll['period_end']}",
        "reference_type": "payroll",
        "reference_id": payroll_id,
        "lines": lines,
        "total_debit": round(total_debit, 2),
        "total_credit": round(total_credit, 2),
        "is_auto_generated": True,
        "transaction_type": "payroll",
        "created_by": user_id,
        "created_at": timestamp
    }
    
    await db.journal_entries.insert_one(journal_entry)
    
    # Update bank balance
    await db.bank_accounts.update_one(
        {"id": bank_account_id},
        {"$inc": {"current_balance": -total_net}}
    )
    
    # Update advance balances
    for item in items:
        if item.get("advance_deduction", 0) > 0:
            # Get active advances for this employee and deduct
            advances = await db.employee_advances.find({
                "employee_id": item["employee_id"],
                "status": "active"
            }).sort("created_at", 1).to_list(10)
            
            remaining_deduction = item["advance_deduction"]
            for adv in advances:
                if remaining_deduction <= 0:
                    break
                
                to_deduct = min(remaining_deduction, adv["remaining_amount"])
                new_remaining = adv["remaining_amount"] - to_deduct
                new_status = "fully_paid" if new_remaining <= 0 else "active"
                
                await db.employee_advances.update_one(
                    {"id": adv["id"]},
                    {"$set": {
                        "remaining_amount": new_remaining,
                        "total_deducted": adv["total_deducted"] + to_deduct,
                        "status": new_status,
                        "updated_at": timestamp
                    }}
                )
                
                remaining_deduction -= to_deduct
    
    # Update payroll status
    await db.payrolls.update_one(
        {"id": payroll_id},
        {"$set": {
            "status": PayrollStatus.PAID.value,
            "paid_at": timestamp,
            "paid_by": user_id,
            "bank_account_id": bank_account_id,
            "journal_entry_id": entry_id,
            "updated_at": timestamp
        }}
    )
    
    # Mark task payments as paid (associate with this payroll)
    for item in items:
        if item.get("task_payments"):
            task_ids = [t["task_id"] for t in item["task_payments"]]
            if task_ids:
                await db.employee_tasks.update_many(
                    {"id": {"$in": task_ids}},
                    {"$set": {
                        "payroll_id": payroll_id,
                        "paid_at": timestamp,
                        "updated_at": timestamp
                    }}
                )
    
    return {"message": "Payroll processed and paid successfully", "journal_entry_id": entry_id}

@router.delete("/payrolls/{payroll_id}")
async def delete_payroll(
    payroll_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a draft payroll"""
    payroll = await db.payrolls.find_one({
        "id": payroll_id,
        "company_id": current_user["company_id"]
    })
    
    if not payroll:
        raise HTTPException(status_code=404, detail="Payroll not found")
    
    if payroll["status"] not in [PayrollStatus.DRAFT.value]:
        raise HTTPException(status_code=400, detail="Can only delete draft payrolls")
    
    await db.payroll_items.delete_many({"payroll_id": payroll_id})
    await db.payrolls.delete_one({"id": payroll_id})
    
    return {"message": "Payroll deleted successfully"}


# ============== TASK PAYMENTS (FREELANCERS) ==============

@router.post("/task-payments")
async def create_task_payment(
    data: TaskPaymentCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a one-time task payment for freelancer"""
    company_id = current_user["company_id"]
    user_id = current_user["user_id"]
    
    # Verify employee is freelancer
    employee = await db.employees.find_one({
        "id": data.employee_id,
        "company_id": company_id
    })
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    payment_id = generate_id()
    timestamp = get_current_timestamp()
    
    # Generate payment number
    count = await db.task_payments.count_documents({"company_id": company_id})
    payment_number = f"TASK-{datetime.now(timezone.utc).strftime('%Y%m')}-{count + 1:04d}"
    
    payment = {
        "id": payment_id,
        "payment_number": payment_number,
        "company_id": company_id,
        "employee_id": data.employee_id,
        "employee_name": f"{employee['first_name']} {employee['last_name']}",
        "description": data.description,
        "amount": data.amount,
        "date": data.date or timestamp[:10],
        "bank_account_id": data.bank_account_id,
        "status": "paid" if data.bank_account_id else "pending",
        "created_by": user_id,
        "created_at": timestamp
    }
    
    await db.task_payments.insert_one(payment)
    
    # Create journal entry if bank account provided
    if data.bank_account_id:
        entry_id = generate_id()
        journal_entry = {
            "id": entry_id,
            "company_id": company_id,
            "entry_number": payment_number,
            "date": timestamp,
            "description": f"Task Payment to {employee['first_name']} {employee['last_name']} - {data.description}",
            "reference_type": "task_payment",
            "reference_id": payment_id,
            "lines": [
                {"account_id": "6100", "account_name": "Salaries & Wages Expense", "debit": data.amount, "credit": 0},
                {"account_id": data.bank_account_id, "account_name": "Bank/Cash", "debit": 0, "credit": data.amount}
            ],
            "total_debit": data.amount,
            "total_credit": data.amount,
            "is_auto_generated": True,
            "transaction_type": "task_payment",
            "created_by": user_id,
            "created_at": timestamp
        }
        await db.journal_entries.insert_one(journal_entry)
        
        await db.bank_accounts.update_one(
            {"id": data.bank_account_id},
            {"$inc": {"current_balance": -data.amount}}
        )
    
    return {"id": payment_id, "payment_number": payment_number, "message": "Task payment created"}

@router.get("/task-payments")
async def get_task_payments(
    employee_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get task payments"""
    query = {"company_id": current_user["company_id"]}
    if employee_id:
        query["employee_id"] = employee_id
    
    payments = await db.task_payments.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
    return payments


# ============== REPORTS ==============

@router.get("/reports/payslip/{payroll_id}/{employee_id}")
async def get_payslip(
    payroll_id: str,
    employee_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get individual payslip"""
    company_id = current_user["company_id"]
    
    payroll = await db.payrolls.find_one(
        {"id": payroll_id, "company_id": company_id},
        {"_id": 0}
    )
    if not payroll:
        raise HTTPException(status_code=404, detail="Payroll not found")
    
    item = await db.payroll_items.find_one(
        {"payroll_id": payroll_id, "employee_id": employee_id},
        {"_id": 0}
    )
    if not item:
        raise HTTPException(status_code=404, detail="Payslip not found")
    
    employee = await db.employees.find_one(
        {"id": employee_id},
        {"_id": 0}
    )
    
    # Get company info
    company = await db.companies.find_one({"id": company_id}, {"_id": 0})
    
    return {
        "company": company,
        "payroll": payroll,
        "employee": employee,
        "payslip": item
    }

@router.get("/reports/summary")
async def get_payroll_summary(
    period_start: Optional[str] = None,
    period_end: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get payroll summary report"""
    company_id = current_user["company_id"]
    
    query = {"company_id": company_id, "status": PayrollStatus.PAID.value}
    if period_start:
        query["period_start"] = {"$gte": period_start}
    if period_end:
        query["period_end"] = {"$lte": period_end}
    
    payrolls = await db.payrolls.find(query, {"_id": 0}).to_list(100)
    
    summary = {
        "total_payrolls": len(payrolls),
        "total_gross": sum(p["total_gross"] for p in payrolls),
        "total_deductions": sum(p["total_deductions"] for p in payrolls),
        "total_net": sum(p["total_net"] for p in payrolls),
        "total_employer_cost": sum(p["total_employer_cost"] for p in payrolls),
        "payrolls": payrolls
    }
    
    return summary

@router.get("/reports/epf-etf")
async def get_epf_etf_report(
    period_start: str,
    period_end: str,
    current_user: dict = Depends(get_current_user)
):
    """Get EPF/ETF contribution report"""
    company_id = current_user["company_id"]
    
    # Get paid payrolls in period
    payrolls = await db.payrolls.find({
        "company_id": company_id,
        "status": PayrollStatus.PAID.value,
        "period_start": {"$gte": period_start},
        "period_end": {"$lte": period_end}
    }).to_list(100)
    
    payroll_ids = [p["id"] for p in payrolls]
    
    # Get all items
    items = await db.payroll_items.find(
        {"payroll_id": {"$in": payroll_ids}},
        {"_id": 0}
    ).to_list(1000)
    
    # Group by employee
    employee_contributions = {}
    for item in items:
        emp_id = item["employee_id"]
        if emp_id not in employee_contributions:
            employee_contributions[emp_id] = {
                "employee_id": emp_id,
                "employee_name": item["employee_name"],
                "employee_code": item["employee_code"],
                "nic": item.get("nic", ""),
                "total_gross": 0,
                "epf_employee": 0,
                "epf_employer": 0,
                "etf": 0
            }
        
        employee_contributions[emp_id]["total_gross"] += item["gross_salary"]
        employee_contributions[emp_id]["epf_employee"] += item.get("epf_employee", 0)
        employee_contributions[emp_id]["epf_employer"] += item.get("epf_employer", 0)
        employee_contributions[emp_id]["etf"] += item.get("etf", 0)
    
    contributions = list(employee_contributions.values())
    
    totals = {
        "total_gross": sum(c["total_gross"] for c in contributions),
        "total_epf_employee": sum(c["epf_employee"] for c in contributions),
        "total_epf_employer": sum(c["epf_employer"] for c in contributions),
        "total_etf": sum(c["etf"] for c in contributions)
    }
    
    return {
        "period_start": period_start,
        "period_end": period_end,
        "contributions": contributions,
        "totals": totals
    }

@router.get("/reports/department")
async def get_department_salary_report(
    period_start: str,
    period_end: str,
    current_user: dict = Depends(get_current_user)
):
    """Get department-wise salary breakdown"""
    company_id = current_user["company_id"]
    
    # Get payrolls
    payrolls = await db.payrolls.find({
        "company_id": company_id,
        "status": PayrollStatus.PAID.value,
        "period_start": {"$gte": period_start},
        "period_end": {"$lte": period_end}
    }).to_list(100)
    
    payroll_ids = [p["id"] for p in payrolls]
    
    # Get items with department
    items = await db.payroll_items.find(
        {"payroll_id": {"$in": payroll_ids}},
        {"_id": 0}
    ).to_list(1000)
    
    # Get departments
    departments = await db.departments.find(
        {"company_id": company_id},
        {"_id": 0}
    ).to_list(100)
    dept_map = {d["id"]: d["name"] for d in departments}
    
    # Group by department
    dept_totals = {}
    for item in items:
        dept_id = item.get("department_id", "unassigned")
        dept_name = dept_map.get(dept_id, "Unassigned")
        
        if dept_id not in dept_totals:
            dept_totals[dept_id] = {
                "department_id": dept_id,
                "department_name": dept_name,
                "employee_count": 0,
                "total_gross": 0,
                "total_deductions": 0,
                "total_net": 0,
                "employer_cost": 0
            }
        
        dept_totals[dept_id]["employee_count"] += 1
        dept_totals[dept_id]["total_gross"] += item["gross_salary"]
        dept_totals[dept_id]["total_deductions"] += item["total_deductions"]
        dept_totals[dept_id]["total_net"] += item["net_salary"]
        dept_totals[dept_id]["employer_cost"] += item.get("employer_cost", 0)
    
    return {
        "period_start": period_start,
        "period_end": period_end,
        "departments": list(dept_totals.values())
    }


# ============== HELPER FUNCTIONS ==============

async def calculate_payroll_item(employee, settings, period_start, period_end, company_id, include_task_payments=True):
    """Calculate payroll for a single employee"""
    
    basic = employee.get("basic_salary", 0)
    hourly_rate = employee.get("hourly_rate", 0) or (basic / 198 if basic else 0)  # 198 = 22 days * 9 hours
    
    # Get employee allowances
    total_allowances = 0
    allowance_details = []
    for allowance in settings.get("allowances", []):
        applies = allowance.get("applies_to", [])
        if not applies or employee["employee_type"] in applies:
            if allowance["type"] == "percentage":
                amount = basic * (allowance["value"] / 100)
            else:
                amount = allowance["value"]
            
            if amount > 0:
                allowance_details.append({
                    "name": allowance["name"],
                    "amount": round(amount, 2)
                })
                total_allowances += amount
    
    # Get verified task payments (not yet paid)
    task_payments_amount = 0
    task_payments_list = []
    if include_task_payments:
        verified_tasks = await db.employee_tasks.find({
            "employee_id": employee["id"],
            "company_id": company_id,
            "status": "verified",
            "$or": [{"payroll_id": None}, {"payroll_id": {"$exists": False}}]
        }, {"_id": 0}).to_list(100)
        
        for task in verified_tasks:
            task_payments_amount += task.get("amount", 0)
            task_payments_list.append({
                "task_id": task["id"],
                "task_number": task.get("task_number", ""),
                "title": task.get("title", ""),
                "amount": task.get("amount", 0)
            })
    
    # Get attendance data for the payroll period
    attendance_records = await db.attendance.find({
        "employee_id": employee["id"],
        "company_id": company_id,
        "date": {"$gte": period_start, "$lte": period_end}
    }, {"_id": 0}).to_list(31)
    
    # Calculate overtime from attendance (OT only for hours > 9)
    overtime_hours = 0.0
    overtime_weekend_hours = 0.0
    total_working_days = 0
    total_hours_worked = 0.0
    
    for att in attendance_records:
        if att.get("status") in ["present", "late"]:
            total_working_days += 1
        elif att.get("status") == "half_day":
            total_working_days += 0.5
        
        total_hours_worked += att.get("hours_worked", 0)
        overtime_hours += att.get("overtime_regular", 0)
        overtime_weekend_hours += att.get("overtime_weekend", 0)
    
    # Calculate overtime pay
    # Regular OT rate (e.g., 1.25x) and Weekend OT rate (e.g., 1.5x)
    ot_regular_rate = settings.get("overtime_rate_weekday", 1.25)
    ot_weekend_rate = settings.get("overtime_rate_weekend", 1.5)
    
    overtime_regular_pay = overtime_hours * hourly_rate * ot_regular_rate
    overtime_weekend_pay = overtime_weekend_hours * hourly_rate * ot_weekend_rate
    overtime_amount = overtime_regular_pay + overtime_weekend_pay
    
    gross = basic + total_allowances + task_payments_amount + overtime_amount
    
    # EPF/ETF calculations (on basic salary only, not on task payments or overtime)
    epf_employee = basic * (settings.get("epf_employee_rate", 8) / 100)
    epf_employer = basic * (settings.get("epf_employer_rate", 12) / 100)
    etf = basic * (settings.get("etf_employer_rate", 3) / 100)
    
    # Calculate tax (PAYE)
    tax = calculate_paye_tax(gross, settings.get("tax_slabs", []))
    
    # Get advance deduction
    advance_deduction = 0
    advances = await db.employee_advances.find({
        "employee_id": employee["id"],
        "company_id": company_id,
        "status": "active"
    }).to_list(10)
    
    for adv in advances:
        deduction = min(adv.get("monthly_deduction", 0), adv.get("remaining_amount", 0))
        advance_deduction += deduction
    
    total_deductions = epf_employee + tax + advance_deduction
    net_salary = gross - total_deductions
    employer_cost = gross + epf_employer + etf
    
    # Get department
    dept_name = "-"
    if employee.get("department_id"):
        dept = await db.departments.find_one({"id": employee["department_id"]}, {"_id": 0, "name": 1})
        dept_name = dept["name"] if dept else "-"
    
    return {
        "employee_id": employee["id"],
        "employee_code": employee["employee_id"],
        "employee_name": f"{employee['first_name']} {employee['last_name']}",
        "department_id": employee.get("department_id"),
        "department_name": dept_name,
        "nic": employee.get("nic", ""),
        "employee_type": employee["employee_type"],
        "basic_salary": round(basic, 2),
        "hourly_rate": round(hourly_rate, 2),
        "allowances": allowance_details,
        "total_allowances": round(total_allowances, 2),
        "task_payments": task_payments_list,
        "task_payments_amount": round(task_payments_amount, 2),
        "overtime_hours": round(overtime_hours, 2),
        "overtime_weekend_hours": round(overtime_weekend_hours, 2),
        "overtime_amount": round(overtime_amount, 2),
        "attendance_days": total_working_days,
        "attendance_hours": round(total_hours_worked, 2),
        "bonus": 0,
        "other_allowances": 0,
        "gross_salary": round(gross, 2),
        "epf_employee": round(epf_employee, 2),
        "epf_employer": round(epf_employer, 2),
        "etf": round(etf, 2),
        "tax": round(tax, 2),
        "advance_deduction": round(advance_deduction, 2),
        "unpaid_leave_days": 0,
        "unpaid_leave_deduction": 0,
        "other_deductions": 0,
        "total_deductions": round(total_deductions, 2),
        "net_salary": round(net_salary, 2),
        "employer_cost": round(employer_cost, 2)
    }


def calculate_paye_tax(monthly_income, tax_slabs):
    """Calculate PAYE tax based on Sri Lanka tax slabs"""
    if not tax_slabs:
        return 0
    
    tax = 0
    remaining = monthly_income
    
    for slab in sorted(tax_slabs, key=lambda x: x["min"]):
        slab_min = slab["min"]
        slab_max = slab.get("max")
        rate = slab["rate"] / 100
        
        if remaining <= 0:
            break
        
        if slab_max:
            taxable_in_slab = min(remaining, slab_max - slab_min + 1)
        else:
            taxable_in_slab = remaining
        
        if monthly_income > slab_min:
            tax += taxable_in_slab * rate
            remaining -= taxable_in_slab
    
    return max(0, tax)



# ============== TASK ASSIGNMENTS ENDPOINTS ==============

@router.get("/tasks")
async def get_tasks(
    employee_id: Optional[str] = None,
    status: Optional[str] = None,
    category: Optional[str] = None,
    include_paid: bool = False,
    current_user: dict = Depends(get_current_user)
):
    """Get all task assignments with filters"""
    query = {"company_id": current_user["company_id"]}
    
    if employee_id:
        query["employee_id"] = employee_id
    if status and status != 'all':
        query["status"] = status
    if category and category != 'all':
        query["category"] = category
    if not include_paid:
        query["$or"] = [
            {"payroll_id": None},
            {"payroll_id": {"$exists": False}}
        ]
    
    tasks = await db.employee_tasks.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
    
    # Get employee names
    emp_ids = list(set(t["employee_id"] for t in tasks))
    if emp_ids:
        emps = await db.employees.find(
            {"id": {"$in": emp_ids}},
            {"_id": 0, "id": 1, "first_name": 1, "last_name": 1, "employee_id": 1}
        ).to_list(500)
        emp_map = {e["id"]: e for e in emps}
        
        for task in tasks:
            emp = emp_map.get(task["employee_id"], {})
            task["employee_name"] = f"{emp.get('first_name', '')} {emp.get('last_name', '')}"
            task["employee_code"] = emp.get("employee_id", "")
    
    return tasks

@router.get("/tasks/pending-payment")
async def get_tasks_pending_payment(
    current_user: dict = Depends(get_current_user)
):
    """Get verified tasks that haven't been paid yet"""
    query = {
        "company_id": current_user["company_id"],
        "status": TaskStatus.VERIFIED.value,
        "$or": [
            {"payroll_id": None},
            {"payroll_id": {"$exists": False}}
        ]
    }
    
    tasks = await db.employee_tasks.find(query, {"_id": 0}).sort("verified_at", 1).to_list(500)
    
    # Get employee names
    emp_ids = list(set(t["employee_id"] for t in tasks))
    if emp_ids:
        emps = await db.employees.find(
            {"id": {"$in": emp_ids}},
            {"_id": 0, "id": 1, "first_name": 1, "last_name": 1, "employee_id": 1}
        ).to_list(500)
        emp_map = {e["id"]: e for e in emps}
        
        for task in tasks:
            emp = emp_map.get(task["employee_id"], {})
            task["employee_name"] = f"{emp.get('first_name', '')} {emp.get('last_name', '')}"
            task["employee_code"] = emp.get("employee_id", "")
    
    return tasks

@router.get("/tasks/categories")
async def get_task_categories():
    """Get available task categories"""
    return [
        {"value": "design", "label": "Design"},
        {"value": "development", "label": "Development"},
        {"value": "marketing", "label": "Marketing"},
        {"value": "production", "label": "Production"},
        {"value": "admin", "label": "Administrative"},
        {"value": "other", "label": "Other"},
    ]

@router.get("/tasks/{task_id}")
async def get_task(
    task_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get single task details"""
    task = await db.employee_tasks.find_one(
        {"id": task_id, "company_id": current_user["company_id"]},
        {"_id": 0}
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Get employee info
    employee = await db.employees.find_one(
        {"id": task["employee_id"]},
        {"_id": 0, "id": 1, "first_name": 1, "last_name": 1, "employee_id": 1, "department_id": 1}
    )
    if employee:
        task["employee_name"] = f"{employee['first_name']} {employee['last_name']}"
        task["employee_code"] = employee["employee_id"]
        
        if employee.get("department_id"):
            dept = await db.departments.find_one({"id": employee["department_id"]}, {"_id": 0, "name": 1})
            task["department_name"] = dept["name"] if dept else "-"
    
    return task

@router.post("/tasks")
async def create_task(
    data: TaskAssignmentCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new task assignment (Admin/Manager only)"""
    if current_user["role"] not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Only admin or manager can assign tasks")
    
    company_id = current_user["company_id"]
    user_id = current_user["user_id"]
    
    # Verify employee exists
    employee = await db.employees.find_one({
        "id": data.employee_id,
        "company_id": company_id,
        "status": "active"
    })
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found or not active")
    
    # Generate task number
    count = await db.employee_tasks.count_documents({"company_id": company_id})
    task_number = f"TASK-{datetime.now(timezone.utc).strftime('%Y%m')}-{count + 1:04d}"
    
    task_id = generate_id()
    timestamp = get_current_timestamp()
    
    task = {
        "id": task_id,
        "task_number": task_number,
        "company_id": company_id,
        "employee_id": data.employee_id,
        "title": data.title,
        "description": data.description,
        "category": data.category.value,
        "amount": data.amount,
        "due_date": data.due_date,
        "status": TaskStatus.ASSIGNED.value,
        "notes": data.notes,
        "assigned_by": user_id,
        "assigned_at": timestamp,
        "started_at": None,
        "completed_at": None,
        "verified_by": None,
        "verified_at": None,
        "payroll_id": None,
        "created_at": timestamp
    }
    
    await db.employee_tasks.insert_one(task)
    
    return {
        "id": task_id,
        "task_number": task_number,
        "message": "Task assigned successfully"
    }

@router.put("/tasks/{task_id}")
async def update_task(
    task_id: str,
    data: TaskAssignmentUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update task details (Admin/Manager only, only if not verified/paid)"""
    if current_user["role"] not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Only admin or manager can update tasks")
    
    task = await db.employee_tasks.find_one({
        "id": task_id,
        "company_id": current_user["company_id"]
    })
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task["status"] in [TaskStatus.VERIFIED.value] and task.get("payroll_id"):
        raise HTTPException(status_code=400, detail="Cannot update task that has been paid")
    
    update_data = {}
    for k, v in data.model_dump().items():
        if v is not None:
            if hasattr(v, 'value'):
                update_data[k] = v.value
            else:
                update_data[k] = v
    
    update_data["updated_at"] = get_current_timestamp()
    
    await db.employee_tasks.update_one({"id": task_id}, {"$set": update_data})
    
    return {"message": "Task updated successfully"}

@router.post("/tasks/{task_id}/start")
async def start_task(
    task_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Mark task as in progress (Employee or Admin/Manager)"""
    task = await db.employee_tasks.find_one({
        "id": task_id,
        "company_id": current_user["company_id"]
    })
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task["status"] != TaskStatus.ASSIGNED.value:
        raise HTTPException(status_code=400, detail="Task can only be started from 'assigned' status")
    
    await db.employee_tasks.update_one(
        {"id": task_id},
        {"$set": {
            "status": TaskStatus.IN_PROGRESS.value,
            "started_at": get_current_timestamp()
        }}
    )
    
    return {"message": "Task started"}

@router.post("/tasks/{task_id}/complete")
async def complete_task(
    task_id: str,
    notes: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Mark task as completed (Employee submits for verification)"""
    task = await db.employee_tasks.find_one({
        "id": task_id,
        "company_id": current_user["company_id"]
    })
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task["status"] not in [TaskStatus.ASSIGNED.value, TaskStatus.IN_PROGRESS.value]:
        raise HTTPException(status_code=400, detail="Task cannot be completed from current status")
    
    update_data = {
        "status": TaskStatus.COMPLETED.value,
        "completed_at": get_current_timestamp()
    }
    if notes:
        update_data["completion_notes"] = notes
    
    await db.employee_tasks.update_one({"id": task_id}, {"$set": update_data})
    
    return {"message": "Task marked as completed, pending verification"}

@router.post("/tasks/{task_id}/verify")
async def verify_task(
    task_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Verify completed task (Admin/Manager only)"""
    if current_user["role"] not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Only admin or manager can verify tasks")
    
    task = await db.employee_tasks.find_one({
        "id": task_id,
        "company_id": current_user["company_id"]
    })
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task["status"] != TaskStatus.COMPLETED.value:
        raise HTTPException(status_code=400, detail="Only completed tasks can be verified")
    
    await db.employee_tasks.update_one(
        {"id": task_id},
        {"$set": {
            "status": TaskStatus.VERIFIED.value,
            "verified_by": current_user["user_id"],
            "verified_at": get_current_timestamp()
        }}
    )
    
    return {"message": "Task verified and ready for payment"}

@router.post("/tasks/{task_id}/reject")
async def reject_task(
    task_id: str,
    reason: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Reject completed task back to in-progress (Admin/Manager only)"""
    if current_user["role"] not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Only admin or manager can reject tasks")
    
    task = await db.employee_tasks.find_one({
        "id": task_id,
        "company_id": current_user["company_id"]
    })
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task["status"] != TaskStatus.COMPLETED.value:
        raise HTTPException(status_code=400, detail="Only completed tasks can be rejected")
    
    update_data = {
        "status": TaskStatus.IN_PROGRESS.value,
        "completed_at": None,
        "rejection_reason": reason,
        "rejected_by": current_user["user_id"],
        "rejected_at": get_current_timestamp()
    }
    
    await db.employee_tasks.update_one({"id": task_id}, {"$set": update_data})
    
    return {"message": "Task rejected and sent back for revision"}

@router.post("/tasks/{task_id}/cancel")
async def cancel_task(
    task_id: str,
    reason: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Cancel a task (Admin/Manager only)"""
    if current_user["role"] not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Only admin or manager can cancel tasks")
    
    task = await db.employee_tasks.find_one({
        "id": task_id,
        "company_id": current_user["company_id"]
    })
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.get("payroll_id"):
        raise HTTPException(status_code=400, detail="Cannot cancel task that has been paid")
    
    await db.employee_tasks.update_one(
        {"id": task_id},
        {"$set": {
            "status": TaskStatus.CANCELLED.value,
            "cancellation_reason": reason,
            "cancelled_by": current_user["user_id"],
            "cancelled_at": get_current_timestamp()
        }}
    )
    
    return {"message": "Task cancelled"}

@router.get("/tasks/employee/{employee_id}/summary")
async def get_employee_task_summary(
    employee_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get task summary for an employee"""
    company_id = current_user["company_id"]
    
    # Get counts by status
    pipeline = [
        {"$match": {"company_id": company_id, "employee_id": employee_id}},
        {"$group": {
            "_id": "$status",
            "count": {"$sum": 1},
            "total_amount": {"$sum": "$amount"}
        }}
    ]
    
    results = await db.employee_tasks.aggregate(pipeline).to_list(10)
    
    summary = {
        "assigned": 0,
        "in_progress": 0,
        "completed": 0,
        "verified": 0,
        "cancelled": 0,
        "pending_payment_amount": 0,
        "total_earned": 0
    }
    
    for r in results:
        status = r["_id"]
        summary[status] = r["count"]
        if status == "verified":
            # Check which are pending payment
            pending = await db.employee_tasks.count_documents({
                "company_id": company_id,
                "employee_id": employee_id,
                "status": "verified",
                "$or": [{"payroll_id": None}, {"payroll_id": {"$exists": False}}]
            })
            paid = await db.employee_tasks.aggregate([
                {"$match": {
                    "company_id": company_id,
                    "employee_id": employee_id,
                    "status": "verified",
                    "payroll_id": {"$ne": None, "$exists": True}
                }},
                {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
            ]).to_list(1)
            
            summary["pending_payment_amount"] = r["total_amount"] if pending > 0 else 0
            summary["total_earned"] = paid[0]["total"] if paid else 0
    
    return summary


# ============== ATTENDANCE TRACKING ENDPOINTS ==============

# Constants for attendance
FULL_DAY_HOURS = 9.0  # 8 hrs work + 1 hr break - normal duty
HALF_DAY_HOURS = 5.0  # with break
STANDARD_WORK_HOURS = 9.0  # OT calculated only for hours > 9

def calculate_hours_worked(check_in: str, check_out: str) -> float:
    """Calculate hours worked from check-in and check-out times"""
    if not check_in or not check_out:
        return 0.0
    
    try:
        from datetime import datetime as dt
        cin = dt.strptime(check_in, "%H:%M")
        cout = dt.strptime(check_out, "%H:%M")
        
        # Handle overnight shifts
        if cout < cin:
            cout = cout.replace(day=2)
            cin = cin.replace(day=1)
        
        diff = (cout - cin).total_seconds() / 3600
        return round(diff, 2)
    except (ValueError, AttributeError):
        return 0.0

def calculate_overtime(hours_worked: float, is_weekend: bool = False) -> dict:
    """Calculate overtime hours - OT only for hours > 9 (normal duty)"""
    overtime_regular = 0.0
    overtime_weekend = 0.0
    
    # Only count overtime if worked more than 9 hours (normal duty)
    if hours_worked > STANDARD_WORK_HOURS:
        extra_hours = hours_worked - STANDARD_WORK_HOURS
        if is_weekend:
            overtime_weekend = extra_hours
        else:
            overtime_regular = extra_hours
    
    return {
        "overtime_regular": round(overtime_regular, 2),
        "overtime_weekend": round(overtime_weekend, 2)
    }

@router.get("/attendance")
async def get_attendance(
    month: Optional[str] = None,  # YYYY-MM
    employee_id: Optional[str] = None,
    department_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get attendance records with filters"""
    company_id = current_user["company_id"]
    
    query = {"company_id": company_id}
    
    if month:
        # Filter by month (date starts with YYYY-MM)
        query["date"] = {"$regex": f"^{month}"}
    
    if employee_id:
        query["employee_id"] = employee_id
    
    # If filtering by department, get employee IDs first
    if department_id:
        emps = await db.employees.find(
            {"company_id": company_id, "department_id": department_id},
            {"_id": 0, "id": 1}
        ).to_list(500)
        emp_ids = [e["id"] for e in emps]
        query["employee_id"] = {"$in": emp_ids}
    
    records = await db.attendance.find(query, {"_id": 0}).sort("date", -1).to_list(1000)
    
    # Enrich with employee names
    emp_ids = list(set(r["employee_id"] for r in records))
    if emp_ids:
        emps = await db.employees.find(
            {"id": {"$in": emp_ids}},
            {"_id": 0, "id": 1, "first_name": 1, "last_name": 1, "employee_id": 1, "department_id": 1}
        ).to_list(500)
        emp_map = {e["id"]: e for e in emps}
        
        for rec in records:
            emp = emp_map.get(rec["employee_id"], {})
            rec["employee_name"] = f"{emp.get('first_name', '')} {emp.get('last_name', '')}"
            rec["employee_code"] = emp.get("employee_id", "")
    
    return records

@router.get("/attendance/daily/{att_date}")
async def get_daily_attendance(
    att_date: str,
    current_user: dict = Depends(get_current_user)
):
    """Get attendance for all employees for a specific date"""
    company_id = current_user["company_id"]
    
    # Get all active employees
    employees = await db.employees.find(
        {"company_id": company_id, "status": "active"},
        {"_id": 0}
    ).sort("employee_id", 1).to_list(500)
    
    # Get attendance records for this date
    records = await db.attendance.find(
        {"company_id": company_id, "date": att_date},
        {"_id": 0}
    ).to_list(500)
    
    record_map = {r["employee_id"]: r for r in records}
    
    # Get departments
    depts = await db.departments.find(
        {"company_id": company_id},
        {"_id": 0, "id": 1, "name": 1}
    ).to_list(100)
    dept_map = {d["id"]: d["name"] for d in depts}
    
    # Check for leave requests on this date
    leave_requests = await db.leave_requests.find({
        "company_id": company_id,
        "status": "approved",
        "start_date": {"$lte": att_date},
        "end_date": {"$gte": att_date}
    }, {"_id": 0, "employee_id": 1}).to_list(500)
    on_leave_ids = set(lr["employee_id"] for lr in leave_requests)
    
    result = []
    for emp in employees:
        emp_id = emp["id"]
        record = record_map.get(emp_id)
        
        # Determine default status
        default_status = "on_leave" if emp_id in on_leave_ids else None
        
        result.append({
            "employee_id": emp_id,
            "employee_code": emp["employee_id"],
            "employee_name": f"{emp['first_name']} {emp['last_name']}",
            "department_id": emp.get("department_id"),
            "department_name": dept_map.get(emp.get("department_id"), "-"),
            "date": att_date,
            "check_in": record.get("check_in") if record else None,
            "check_out": record.get("check_out") if record else None,
            "hours_worked": record.get("hours_worked", 0) if record else 0,
            "status": record.get("status") if record else default_status,
            "overtime_regular": record.get("overtime_regular", 0) if record else 0,
            "overtime_weekend": record.get("overtime_weekend", 0) if record else 0,
            "notes": record.get("notes") if record else None,
            "has_record": record is not None,
            "is_on_approved_leave": emp_id in on_leave_ids
        })
    
    return result

@router.post("/attendance")
async def create_attendance(
    data: AttendanceCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create or update attendance record for an employee"""
    company_id = current_user["company_id"]
    user_id = current_user["user_id"]
    
    # Check if employee exists
    employee = await db.employees.find_one({
        "id": data.employee_id,
        "company_id": company_id
    })
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Calculate hours worked
    hours_worked = calculate_hours_worked(data.check_in, data.check_out)
    
    # Determine if weekend
    from datetime import datetime as dt
    date_obj = dt.strptime(data.date, "%Y-%m-%d")
    is_weekend = date_obj.weekday() >= 5  # Saturday=5, Sunday=6
    
    # Calculate overtime
    overtime = calculate_overtime(hours_worked, is_weekend)
    
    # Check if record already exists
    existing = await db.attendance.find_one({
        "company_id": company_id,
        "employee_id": data.employee_id,
        "date": data.date
    })
    
    timestamp = get_current_timestamp()
    
    if existing:
        # Update existing record
        await db.attendance.update_one(
            {"id": existing["id"]},
            {"$set": {
                "check_in": data.check_in,
                "check_out": data.check_out,
                "hours_worked": hours_worked,
                "status": data.status.value,
                "overtime_regular": overtime["overtime_regular"],
                "overtime_weekend": overtime["overtime_weekend"],
                "notes": data.notes,
                "updated_by": user_id,
                "updated_at": timestamp
            }}
        )
        return {"message": "Attendance updated", "id": existing["id"]}
    else:
        # Create new record
        record_id = generate_id()
        record = {
            "id": record_id,
            "company_id": company_id,
            "employee_id": data.employee_id,
            "date": data.date,
            "check_in": data.check_in,
            "check_out": data.check_out,
            "hours_worked": hours_worked,
            "status": data.status.value,
            "overtime_regular": overtime["overtime_regular"],
            "overtime_weekend": overtime["overtime_weekend"],
            "notes": data.notes,
            "created_by": user_id,
            "created_at": timestamp
        }
        await db.attendance.insert_one(record)
        return {"message": "Attendance recorded", "id": record_id}

@router.post("/attendance/bulk")
async def create_bulk_attendance(
    data: BulkAttendanceCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create or update attendance for multiple employees at once"""
    company_id = current_user["company_id"]
    user_id = current_user["user_id"]
    timestamp = get_current_timestamp()
    
    # Determine if weekend
    from datetime import datetime as dt
    date_obj = dt.strptime(data.date, "%Y-%m-%d")
    is_weekend = date_obj.weekday() >= 5
    
    created = 0
    updated = 0
    
    for rec in data.records:
        employee_id = rec.get("employee_id")
        if not employee_id:
            continue
        
        check_in = rec.get("check_in")
        check_out = rec.get("check_out")
        status = rec.get("status", "present")
        notes = rec.get("notes")
        
        # Calculate hours
        hours_worked = calculate_hours_worked(check_in, check_out)
        overtime = calculate_overtime(hours_worked, is_weekend)
        
        # Check existing
        existing = await db.attendance.find_one({
            "company_id": company_id,
            "employee_id": employee_id,
            "date": data.date
        })
        
        if existing:
            await db.attendance.update_one(
                {"id": existing["id"]},
                {"$set": {
                    "check_in": check_in,
                    "check_out": check_out,
                    "hours_worked": hours_worked,
                    "status": status,
                    "overtime_regular": overtime["overtime_regular"],
                    "overtime_weekend": overtime["overtime_weekend"],
                    "notes": notes,
                    "updated_by": user_id,
                    "updated_at": timestamp
                }}
            )
            updated += 1
        else:
            record_id = generate_id()
            record = {
                "id": record_id,
                "company_id": company_id,
                "employee_id": employee_id,
                "date": data.date,
                "check_in": check_in,
                "check_out": check_out,
                "hours_worked": hours_worked,
                "status": status,
                "overtime_regular": overtime["overtime_regular"],
                "overtime_weekend": overtime["overtime_weekend"],
                "notes": notes,
                "created_by": user_id,
                "created_at": timestamp
            }
            await db.attendance.insert_one(record)
            created += 1
    
    return {"message": f"Attendance saved: {created} created, {updated} updated"}

@router.put("/attendance/{record_id}")
async def update_attendance(
    record_id: str,
    data: AttendanceUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update an attendance record"""
    company_id = current_user["company_id"]
    
    record = await db.attendance.find_one({
        "id": record_id,
        "company_id": company_id
    })
    if not record:
        raise HTTPException(status_code=404, detail="Attendance record not found")
    
    update_data = {}
    
    check_in = data.check_in if data.check_in is not None else record.get("check_in")
    check_out = data.check_out if data.check_out is not None else record.get("check_out")
    
    if data.check_in is not None:
        update_data["check_in"] = data.check_in
    if data.check_out is not None:
        update_data["check_out"] = data.check_out
    if data.status is not None:
        update_data["status"] = data.status.value
    if data.notes is not None:
        update_data["notes"] = data.notes
    
    # Recalculate hours
    hours_worked = calculate_hours_worked(check_in, check_out)
    update_data["hours_worked"] = hours_worked
    
    # Recalculate overtime
    from datetime import datetime as dt
    date_obj = dt.strptime(record["date"], "%Y-%m-%d")
    is_weekend = date_obj.weekday() >= 5
    overtime = calculate_overtime(hours_worked, is_weekend)
    update_data["overtime_regular"] = overtime["overtime_regular"]
    update_data["overtime_weekend"] = overtime["overtime_weekend"]
    
    update_data["updated_by"] = current_user["user_id"]
    update_data["updated_at"] = get_current_timestamp()
    
    await db.attendance.update_one({"id": record_id}, {"$set": update_data})
    
    return {"message": "Attendance updated"}

@router.delete("/attendance/{record_id}")
async def delete_attendance(
    record_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete an attendance record"""
    company_id = current_user["company_id"]
    
    result = await db.attendance.delete_one({
        "id": record_id,
        "company_id": company_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Attendance record not found")
    
    return {"message": "Attendance deleted"}

@router.get("/attendance/summary/{employee_id}")
async def get_employee_attendance_summary(
    employee_id: str,
    month: str,  # YYYY-MM
    current_user: dict = Depends(get_current_user)
):
    """Get attendance summary for an employee for a month"""
    company_id = current_user["company_id"]
    
    records = await db.attendance.find({
        "company_id": company_id,
        "employee_id": employee_id,
        "date": {"$regex": f"^{month}"}
    }, {"_id": 0}).to_list(31)
    
    # Calculate summary
    present_days = sum(1 for r in records if r["status"] == "present")
    half_days = sum(1 for r in records if r["status"] == "half_day")
    absent_days = sum(1 for r in records if r["status"] == "absent")
    late_days = sum(1 for r in records if r["status"] == "late")
    leave_days = sum(1 for r in records if r["status"] == "on_leave")
    
    total_hours = sum(r.get("hours_worked", 0) for r in records)
    overtime_regular = sum(r.get("overtime_regular", 0) for r in records)
    overtime_weekend = sum(r.get("overtime_weekend", 0) for r in records)
    
    # Calculate working days equivalent
    working_days = present_days + late_days + (half_days * 0.5)
    
    return {
        "employee_id": employee_id,
        "month": month,
        "present_days": present_days,
        "half_days": half_days,
        "absent_days": absent_days,
        "late_days": late_days,
        "leave_days": leave_days,
        "total_records": len(records),
        "working_days_equivalent": working_days,
        "total_hours_worked": round(total_hours, 2),
        "overtime_regular_hours": round(overtime_regular, 2),
        "overtime_weekend_hours": round(overtime_weekend, 2),
        "total_overtime_hours": round(overtime_regular + overtime_weekend, 2)
    }

@router.get("/attendance/monthly-report")
async def get_monthly_attendance_report(
    month: str,  # YYYY-MM
    department_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get monthly attendance report for all employees"""
    company_id = current_user["company_id"]
    
    # Get employees
    emp_query = {"company_id": company_id, "status": "active"}
    if department_id:
        emp_query["department_id"] = department_id
    
    employees = await db.employees.find(emp_query, {"_id": 0}).to_list(500)
    
    # Get departments
    depts = await db.departments.find(
        {"company_id": company_id},
        {"_id": 0, "id": 1, "name": 1}
    ).to_list(100)
    dept_map = {d["id"]: d["name"] for d in depts}
    
    # Get all attendance for the month
    records = await db.attendance.find({
        "company_id": company_id,
        "date": {"$regex": f"^{month}"}
    }, {"_id": 0}).to_list(5000)
    
    # Group records by employee
    from collections import defaultdict
    emp_records = defaultdict(list)
    for r in records:
        emp_records[r["employee_id"]].append(r)
    
    report = []
    for emp in employees:
        emp_id = emp["id"]
        recs = emp_records.get(emp_id, [])
        
        present = sum(1 for r in recs if r["status"] == "present")
        half_days = sum(1 for r in recs if r["status"] == "half_day")
        absent = sum(1 for r in recs if r["status"] == "absent")
        late = sum(1 for r in recs if r["status"] == "late")
        leave = sum(1 for r in recs if r["status"] == "on_leave")
        
        total_hours = sum(r.get("hours_worked", 0) for r in recs)
        ot_regular = sum(r.get("overtime_regular", 0) for r in recs)
        ot_weekend = sum(r.get("overtime_weekend", 0) for r in recs)
        
        report.append({
            "employee_id": emp_id,
            "employee_code": emp["employee_id"],
            "employee_name": f"{emp['first_name']} {emp['last_name']}",
            "department_name": dept_map.get(emp.get("department_id"), "-"),
            "present_days": present,
            "half_days": half_days,
            "absent_days": absent,
            "late_days": late,
            "leave_days": leave,
            "working_days": present + late + (half_days * 0.5),
            "total_hours": round(total_hours, 2),
            "overtime_regular": round(ot_regular, 2),
            "overtime_weekend": round(ot_weekend, 2),
            "total_overtime": round(ot_regular + ot_weekend, 2)
        })
    
    return report

@router.get("/attendance/settings")
async def get_attendance_settings(
    current_user: dict = Depends(get_current_user)
):
    """Get attendance settings"""
    return {
        "full_day_hours": FULL_DAY_HOURS,
        "half_day_hours": HALF_DAY_HOURS,
        "standard_work_hours": STANDARD_WORK_HOURS,
        "statuses": [
            {"value": "present", "label": "Present", "color": "green"},
            {"value": "absent", "label": "Absent", "color": "red"},
            {"value": "half_day", "label": "Half Day", "color": "yellow"},
            {"value": "late", "label": "Late", "color": "orange"},
            {"value": "on_leave", "label": "On Leave", "color": "blue"}
        ]
    }
