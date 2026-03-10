"""
Employee Portal Router
Handles Employee Self-Service features:
- Task Categories (manager-created)
- Enhanced Tasks (with attachments, comments, subtasks, time tracking)
- Employee Dashboard
- My Tasks (employee-specific view)
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from typing import Optional, List
from datetime import datetime, timezone
from pydantic import BaseModel
from enum import Enum
import uuid
import os

from utils.helpers import serialize_doc, generate_id, get_current_timestamp
from utils.auth import get_current_user

router = APIRouter(prefix="/portal", tags=["Employee Portal"])

# Database will be injected from main app
db = None

def set_db(database):
    global db
    db = database


# ============== ENUMS ==============

class TaskStatus(str, Enum):
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    VERIFIED = "verified"
    CANCELLED = "cancelled"

class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


# ============== MODELS ==============

class TaskCategoryCreate(BaseModel):
    name: str
    color: str = "#6366f1"  # Default indigo
    description: Optional[str] = None

class TaskCategoryUpdate(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class SubtaskCreate(BaseModel):
    title: str
    is_completed: bool = False

class TaskCommentCreate(BaseModel):
    content: str

class TimeLogCreate(BaseModel):
    hours: float
    description: Optional[str] = None
    log_date: Optional[str] = None

class EnhancedTaskCreate(BaseModel):
    employee_id: str
    title: str
    description: Optional[str] = None
    category_id: Optional[str] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: Optional[str] = None
    amount: float = 0.0  # Payment amount for task
    subtasks: Optional[List[SubtaskCreate]] = []
    notes: Optional[str] = None

class EnhancedTaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[str] = None
    priority: Optional[TaskPriority] = None
    due_date: Optional[str] = None
    amount: Optional[float] = None
    notes: Optional[str] = None


# ============== TASK CATEGORIES ENDPOINTS ==============

@router.get("/task-categories")
async def get_task_categories(
    include_inactive: bool = False,
    current_user: dict = Depends(get_current_user)
):
    """Get all task categories for the company"""
    query = {"company_id": current_user["company_id"]}
    if not include_inactive:
        query["is_active"] = True
    
    categories = await db.task_categories.find(query, {"_id": 0}).sort("name", 1).to_list(100)
    return categories

@router.post("/task-categories")
async def create_task_category(
    data: TaskCategoryCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new task category (Manager/Admin only)"""
    if current_user["role"] not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Only admin or manager can create categories")
    
    company_id = current_user["company_id"]
    
    # Check for duplicate name
    existing = await db.task_categories.find_one({
        "company_id": company_id,
        "name": {"$regex": f"^{data.name}$", "$options": "i"}
    })
    if existing:
        raise HTTPException(status_code=400, detail="Category with this name already exists")
    
    category_id = generate_id()
    timestamp = get_current_timestamp()
    
    category = {
        "id": category_id,
        "company_id": company_id,
        "name": data.name,
        "color": data.color,
        "description": data.description,
        "is_active": True,
        "created_by": current_user["user_id"],
        "created_at": timestamp
    }
    
    await db.task_categories.insert_one(category)
    category.pop("_id", None)
    
    return category

@router.put("/task-categories/{category_id}")
async def update_task_category(
    category_id: str,
    data: TaskCategoryUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update a task category (Manager/Admin only)"""
    if current_user["role"] not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Only admin or manager can update categories")
    
    category = await db.task_categories.find_one({
        "id": category_id,
        "company_id": current_user["company_id"]
    })
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if update_data:
        update_data["updated_at"] = get_current_timestamp()
        await db.task_categories.update_one({"id": category_id}, {"$set": update_data})
    
    updated = await db.task_categories.find_one({"id": category_id}, {"_id": 0})
    return updated

@router.delete("/task-categories/{category_id}")
async def delete_task_category(
    category_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a task category (soft delete - set inactive)"""
    if current_user["role"] not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Only admin or manager can delete categories")
    
    result = await db.task_categories.update_one(
        {"id": category_id, "company_id": current_user["company_id"]},
        {"$set": {"is_active": False, "updated_at": get_current_timestamp()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Category not found")
    
    return {"message": "Category deleted"}


# ============== ENHANCED TASKS ENDPOINTS ==============

@router.get("/tasks")
async def get_enhanced_tasks(
    employee_id: Optional[str] = None,
    status: Optional[str] = None,
    category_id: Optional[str] = None,
    priority: Optional[str] = None,
    assigned_to_me: bool = False,
    current_user: dict = Depends(get_current_user)
):
    """Get tasks with filters. Employees see only their own tasks unless manager/admin."""
    company_id = current_user["company_id"]
    query = {"company_id": company_id}
    
    # Role-based filtering
    if current_user["role"] == "employee" or assigned_to_me:
        # Get the employee record for this user
        employee = await db.employees.find_one({"user_id": current_user["user_id"], "company_id": company_id})
        if employee:
            query["employee_id"] = employee["id"]
        else:
            return []  # No employee record, no tasks
    elif employee_id:
        query["employee_id"] = employee_id
    
    if status and status != 'all':
        query["status"] = status
    if category_id and category_id != 'all':
        query["category_id"] = category_id
    if priority and priority != 'all':
        query["priority"] = priority
    
    tasks = await db.employee_tasks.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
    
    # Enrich with employee and category names
    emp_ids = list(set(t.get("employee_id") for t in tasks if t.get("employee_id")))
    cat_ids = list(set(t.get("category_id") for t in tasks if t.get("category_id")))
    
    emp_map = {}
    if emp_ids:
        emps = await db.employees.find({"id": {"$in": emp_ids}}, {"_id": 0, "id": 1, "first_name": 1, "last_name": 1, "employee_id": 1}).to_list(500)
        emp_map = {e["id"]: e for e in emps}
    
    cat_map = {}
    if cat_ids:
        cats = await db.task_categories.find({"id": {"$in": cat_ids}}, {"_id": 0, "id": 1, "name": 1, "color": 1}).to_list(100)
        cat_map = {c["id"]: c for c in cats}
    
    for task in tasks:
        emp = emp_map.get(task.get("employee_id"), {})
        task["employee_name"] = f"{emp.get('first_name', '')} {emp.get('last_name', '')}".strip() or "Unassigned"
        task["employee_code"] = emp.get("employee_id", "")
        
        cat = cat_map.get(task.get("category_id"), {})
        task["category_name"] = cat.get("name", "Uncategorized")
        task["category_color"] = cat.get("color", "#6b7280")
        
        # Count subtasks
        subtasks = task.get("subtasks", [])
        task["subtasks_total"] = len(subtasks)
        task["subtasks_completed"] = len([s for s in subtasks if s.get("is_completed")])
        
        # Sum time logged
        task["total_hours"] = sum(t.get("hours", 0) for t in task.get("time_logs", []))
    
    return tasks

@router.get("/tasks/{task_id}")
async def get_task_detail(
    task_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get detailed task information including comments, attachments, time logs"""
    task = await db.employee_tasks.find_one({
        "id": task_id,
        "company_id": current_user["company_id"]
    }, {"_id": 0})
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Check access: employees can only view their own tasks
    if current_user["role"] == "employee":
        employee = await db.employees.find_one({"user_id": current_user["user_id"]})
        if not employee or task.get("employee_id") != employee["id"]:
            raise HTTPException(status_code=403, detail="You can only view your own tasks")
    
    # Enrich with names
    if task.get("employee_id"):
        emp = await db.employees.find_one({"id": task["employee_id"]}, {"_id": 0, "first_name": 1, "last_name": 1, "employee_id": 1, "department_id": 1})
        if emp:
            task["employee_name"] = f"{emp['first_name']} {emp['last_name']}"
            task["employee_code"] = emp.get("employee_id", "")
            if emp.get("department_id"):
                dept = await db.departments.find_one({"id": emp["department_id"]}, {"_id": 0, "name": 1})
                task["department_name"] = dept["name"] if dept else ""
    
    if task.get("category_id"):
        cat = await db.task_categories.find_one({"id": task["category_id"]}, {"_id": 0, "name": 1, "color": 1})
        if cat:
            task["category_name"] = cat["name"]
            task["category_color"] = cat["color"]
    
    # Get user names for comments
    comments = task.get("comments", [])
    user_ids = list(set(c.get("user_id") for c in comments if c.get("user_id")))
    if user_ids:
        users = await db.users.find({"id": {"$in": user_ids}}, {"_id": 0, "id": 1, "full_name": 1}).to_list(100)
        user_map = {u["id"]: u["full_name"] for u in users}
        for comment in comments:
            comment["user_name"] = user_map.get(comment.get("user_id"), "Unknown")
    
    task["total_hours"] = sum(t.get("hours", 0) for t in task.get("time_logs", []))
    
    return task

@router.post("/tasks")
async def create_enhanced_task(
    data: EnhancedTaskCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new task with enhanced features (Manager/Admin only)"""
    if current_user["role"] not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Only admin or manager can assign tasks")
    
    company_id = current_user["company_id"]
    
    # Verify employee exists
    employee = await db.employees.find_one({
        "id": data.employee_id,
        "company_id": company_id,
        "status": "active"
    })
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found or not active")
    
    # Verify category if provided
    if data.category_id:
        category = await db.task_categories.find_one({
            "id": data.category_id,
            "company_id": company_id,
            "is_active": True
        })
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
    
    # Generate task number
    count = await db.employee_tasks.count_documents({"company_id": company_id})
    task_number = f"TASK-{datetime.now(timezone.utc).strftime('%Y%m')}-{count + 1:04d}"
    
    task_id = generate_id()
    timestamp = get_current_timestamp()
    
    # Process subtasks
    subtasks = []
    for i, st in enumerate(data.subtasks or []):
        subtasks.append({
            "id": generate_id(),
            "title": st.title,
            "is_completed": st.is_completed,
            "order": i
        })
    
    task = {
        "id": task_id,
        "task_number": task_number,
        "company_id": company_id,
        "employee_id": data.employee_id,
        "title": data.title,
        "description": data.description,
        "category_id": data.category_id,
        "category": None,  # Legacy field
        "priority": data.priority.value,
        "amount": data.amount,
        "due_date": data.due_date,
        "status": TaskStatus.ASSIGNED.value,
        "notes": data.notes,
        "subtasks": subtasks,
        "comments": [],
        "attachments": [],
        "time_logs": [],
        "assigned_by": current_user["user_id"],
        "assigned_at": timestamp,
        "started_at": None,
        "completed_at": None,
        "verified_by": None,
        "verified_at": None,
        "payroll_id": None,
        "created_at": timestamp
    }
    
    await db.employee_tasks.insert_one(task)
    task.pop("_id", None)
    
    return {
        "id": task_id,
        "task_number": task_number,
        "message": "Task created successfully"
    }

@router.put("/tasks/{task_id}")
async def update_enhanced_task(
    task_id: str,
    data: EnhancedTaskUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update task details (Manager/Admin only, unless task is verified/paid)"""
    if current_user["role"] not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Only admin or manager can update tasks")
    
    task = await db.employee_tasks.find_one({
        "id": task_id,
        "company_id": current_user["company_id"]
    })
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task["status"] == TaskStatus.VERIFIED.value and task.get("payroll_id"):
        raise HTTPException(status_code=400, detail="Cannot update task that has been paid")
    
    update_data = {}
    for k, v in data.model_dump().items():
        if v is not None:
            if hasattr(v, 'value'):
                update_data[k] = v.value
            else:
                update_data[k] = v
    
    if update_data:
        update_data["updated_at"] = get_current_timestamp()
        await db.employee_tasks.update_one({"id": task_id}, {"$set": update_data})
    
    return {"message": "Task updated successfully"}


# ============== SUBTASKS ==============

@router.post("/tasks/{task_id}/subtasks")
async def add_subtask(
    task_id: str,
    data: SubtaskCreate,
    current_user: dict = Depends(get_current_user)
):
    """Add a subtask to a task"""
    task = await db.employee_tasks.find_one({
        "id": task_id,
        "company_id": current_user["company_id"]
    })
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Check access
    if current_user["role"] == "employee":
        employee = await db.employees.find_one({"user_id": current_user["user_id"]})
        if not employee or task.get("employee_id") != employee["id"]:
            raise HTTPException(status_code=403, detail="You can only modify your own tasks")
    
    subtask = {
        "id": generate_id(),
        "title": data.title,
        "is_completed": data.is_completed,
        "order": len(task.get("subtasks", []))
    }
    
    await db.employee_tasks.update_one(
        {"id": task_id},
        {"$push": {"subtasks": subtask}}
    )
    
    return subtask

@router.put("/tasks/{task_id}/subtasks/{subtask_id}")
async def update_subtask(
    task_id: str,
    subtask_id: str,
    is_completed: bool,
    current_user: dict = Depends(get_current_user)
):
    """Toggle subtask completion"""
    task = await db.employee_tasks.find_one({
        "id": task_id,
        "company_id": current_user["company_id"]
    })
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Check access
    if current_user["role"] == "employee":
        employee = await db.employees.find_one({"user_id": current_user["user_id"]})
        if not employee or task.get("employee_id") != employee["id"]:
            raise HTTPException(status_code=403, detail="You can only modify your own tasks")
    
    await db.employee_tasks.update_one(
        {"id": task_id, "subtasks.id": subtask_id},
        {"$set": {"subtasks.$.is_completed": is_completed}}
    )
    
    return {"message": "Subtask updated"}

@router.delete("/tasks/{task_id}/subtasks/{subtask_id}")
async def delete_subtask(
    task_id: str,
    subtask_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a subtask"""
    if current_user["role"] not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Only admin or manager can delete subtasks")
    
    result = await db.employee_tasks.update_one(
        {"id": task_id, "company_id": current_user["company_id"]},
        {"$pull": {"subtasks": {"id": subtask_id}}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Subtask not found")
    
    return {"message": "Subtask deleted"}


# ============== COMMENTS ==============

@router.post("/tasks/{task_id}/comments")
async def add_comment(
    task_id: str,
    data: TaskCommentCreate,
    current_user: dict = Depends(get_current_user)
):
    """Add a comment to a task"""
    task = await db.employee_tasks.find_one({
        "id": task_id,
        "company_id": current_user["company_id"]
    })
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Check access for employees
    if current_user["role"] == "employee":
        employee = await db.employees.find_one({"user_id": current_user["user_id"]})
        if not employee or task.get("employee_id") != employee["id"]:
            raise HTTPException(status_code=403, detail="You can only comment on your own tasks")
    
    # Get user name
    user = await db.users.find_one({"id": current_user["user_id"]}, {"_id": 0, "full_name": 1})
    
    comment = {
        "id": generate_id(),
        "user_id": current_user["user_id"],
        "user_name": user.get("full_name", "Unknown") if user else "Unknown",
        "content": data.content,
        "created_at": get_current_timestamp()
    }
    
    await db.employee_tasks.update_one(
        {"id": task_id},
        {"$push": {"comments": comment}}
    )
    
    return comment

@router.delete("/tasks/{task_id}/comments/{comment_id}")
async def delete_comment(
    task_id: str,
    comment_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a comment (only own comments or admin/manager)"""
    task = await db.employee_tasks.find_one({
        "id": task_id,
        "company_id": current_user["company_id"]
    })
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Find the comment
    comment = next((c for c in task.get("comments", []) if c["id"] == comment_id), None)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # Check permission
    if current_user["role"] not in ["admin", "manager"] and comment.get("user_id") != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="You can only delete your own comments")
    
    await db.employee_tasks.update_one(
        {"id": task_id},
        {"$pull": {"comments": {"id": comment_id}}}
    )
    
    return {"message": "Comment deleted"}


# ============== TIME TRACKING ==============

@router.post("/tasks/{task_id}/time-logs")
async def add_time_log(
    task_id: str,
    data: TimeLogCreate,
    current_user: dict = Depends(get_current_user)
):
    """Log time spent on a task"""
    task = await db.employee_tasks.find_one({
        "id": task_id,
        "company_id": current_user["company_id"]
    })
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Check access for employees
    if current_user["role"] == "employee":
        employee = await db.employees.find_one({"user_id": current_user["user_id"]})
        if not employee or task.get("employee_id") != employee["id"]:
            raise HTTPException(status_code=403, detail="You can only log time on your own tasks")
    
    time_log = {
        "id": generate_id(),
        "user_id": current_user["user_id"],
        "hours": data.hours,
        "description": data.description,
        "log_date": data.log_date or datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "created_at": get_current_timestamp()
    }
    
    await db.employee_tasks.update_one(
        {"id": task_id},
        {"$push": {"time_logs": time_log}}
    )
    
    return time_log

@router.delete("/tasks/{task_id}/time-logs/{log_id}")
async def delete_time_log(
    task_id: str,
    log_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a time log entry"""
    if current_user["role"] not in ["admin", "manager"]:
        # Employees can only delete their own time logs
        task = await db.employee_tasks.find_one({"id": task_id})
        if task:
            log = next((t for t in task.get("time_logs", []) if t["id"] == log_id), None)
            if log and log.get("user_id") != current_user["user_id"]:
                raise HTTPException(status_code=403, detail="You can only delete your own time logs")
    
    result = await db.employee_tasks.update_one(
        {"id": task_id, "company_id": current_user["company_id"]},
        {"$pull": {"time_logs": {"id": log_id}}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Time log not found")
    
    return {"message": "Time log deleted"}


# ============== TASK STATUS ACTIONS ==============

@router.post("/tasks/{task_id}/start")
async def start_task(
    task_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Start working on a task (change status to in_progress)"""
    task = await db.employee_tasks.find_one({
        "id": task_id,
        "company_id": current_user["company_id"]
    })
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Check access for employees
    if current_user["role"] == "employee":
        employee = await db.employees.find_one({"user_id": current_user["user_id"]})
        if not employee or task.get("employee_id") != employee["id"]:
            raise HTTPException(status_code=403, detail="You can only start your own tasks")
    
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
    """Mark task as completed (pending verification)"""
    task = await db.employee_tasks.find_one({
        "id": task_id,
        "company_id": current_user["company_id"]
    })
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Check access for employees
    if current_user["role"] == "employee":
        employee = await db.employees.find_one({"user_id": current_user["user_id"]})
        if not employee or task.get("employee_id") != employee["id"]:
            raise HTTPException(status_code=403, detail="You can only complete your own tasks")
    
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
    """Verify a completed task (Manager/Admin only)"""
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
    
    return {"message": "Task verified successfully"}

@router.post("/tasks/{task_id}/reject")
async def reject_task(
    task_id: str,
    reason: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Reject a completed task back to in-progress (Manager/Admin only)"""
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
    
    # Add rejection as a comment
    if reason:
        user = await db.users.find_one({"id": current_user["user_id"]}, {"_id": 0, "full_name": 1})
        comment = {
            "id": generate_id(),
            "user_id": current_user["user_id"],
            "user_name": user.get("full_name", "Manager") if user else "Manager",
            "content": f"Task rejected: {reason}",
            "created_at": get_current_timestamp(),
            "is_system": True
        }
        await db.employee_tasks.update_one({"id": task_id}, {"$push": {"comments": comment}})
    
    await db.employee_tasks.update_one({"id": task_id}, {"$set": update_data})
    
    return {"message": "Task rejected and sent back to employee"}


# ============== EMPLOYEE DASHBOARD ==============

@router.get("/my-dashboard")
async def get_employee_dashboard(
    current_user: dict = Depends(get_current_user)
):
    """Get dashboard data for the current employee"""
    company_id = current_user["company_id"]
    
    # Get employee record
    employee = await db.employees.find_one({
        "user_id": current_user["user_id"],
        "company_id": company_id
    }, {"_id": 0})
    
    if not employee:
        # Return empty dashboard for non-employee users
        return {
            "employee": None,
            "tasks": {"total": 0, "assigned": 0, "in_progress": 0, "completed": 0, "verified": 0},
            "attendance": {"present_today": False, "this_month": 0},
            "leave": {"balance": 0, "pending": 0},
            "recent_tasks": []
        }
    
    employee_id = employee["id"]
    
    # Task stats
    task_counts = {}
    for status in ["assigned", "in_progress", "completed", "verified"]:
        count = await db.employee_tasks.count_documents({
            "company_id": company_id,
            "employee_id": employee_id,
            "status": status
        })
        task_counts[status] = count
    task_counts["total"] = sum(task_counts.values())
    
    # Recent tasks (last 5)
    recent_tasks = await db.employee_tasks.find(
        {"company_id": company_id, "employee_id": employee_id},
        {"_id": 0, "id": 1, "task_number": 1, "title": 1, "status": 1, "priority": 1, "due_date": 1}
    ).sort("created_at", -1).limit(5).to_list(5)
    
    # Attendance - check if clocked in today
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    today_attendance = await db.attendance.find_one({
        "company_id": company_id,
        "employee_id": employee_id,
        "date": today
    })
    
    # Attendance this month
    month_start = datetime.now(timezone.utc).replace(day=1).strftime("%Y-%m-%d")
    month_attendance = await db.attendance.count_documents({
        "company_id": company_id,
        "employee_id": employee_id,
        "date": {"$gte": month_start},
        "status": "present"
    })
    
    # Leave balance
    leave_balance = employee.get("leave_balance", {})
    total_leave = sum(leave_balance.values()) if isinstance(leave_balance, dict) else 0
    
    # Pending leave requests
    pending_leaves = await db.leave_requests.count_documents({
        "company_id": company_id,
        "employee_id": employee_id,
        "status": "pending"
    })
    
    return {
        "employee": {
            "id": employee["id"],
            "name": f"{employee['first_name']} {employee['last_name']}",
            "employee_id": employee.get("employee_id", ""),
            "department": employee.get("department_name", ""),
            "designation": employee.get("designation", "")
        },
        "tasks": task_counts,
        "attendance": {
            "present_today": today_attendance is not None and today_attendance.get("status") == "present",
            "clock_in_time": today_attendance.get("clock_in") if today_attendance else None,
            "this_month": month_attendance
        },
        "leave": {
            "balance": total_leave,
            "pending": pending_leaves
        },
        "recent_tasks": recent_tasks
    }
