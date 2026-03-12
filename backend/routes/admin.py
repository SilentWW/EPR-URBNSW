"""
Admin Router - System Administration
Data Reset, Backup, Restore, System Maintenance
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.responses import FileResponse
from typing import Optional, List
from datetime import datetime, timezone
import uuid
import os
import json
import shutil
import gzip
import logging

logger = logging.getLogger(__name__)

from models.admin import (
    DataResetRequest, DataResetResponse, ResetType,
    BackupCreate, BackupResponse, BackupType, BackupStatus,
    RestoreRequest, RestoreResponse,
    ScheduledBackupCreate
)
from utils.helpers import serialize_doc, generate_id, get_current_timestamp
from utils.auth import get_current_user

router = APIRouter(prefix="/admin", tags=["Admin"])

# Database will be injected from main app
db = None
import tempfile

BACKUP_DIR = os.environ.get("BACKUP_DIR", tempfile.gettempdir() + "/erp_backups")

def set_db(database):
    global db
    db = database

def set_auth_dependency(auth_func):
    # Not needed with shared auth module
    pass

# Collections categorized
MASTER_COLLECTIONS = [
    "users", "accounts", "tax_rates", "products", "customers", "suppliers",
    "departments", "designations", "employees", "product_categories", "product_variations",
    "raw_materials", "rm_suppliers", "packaging_rules"
]
TRANSACTIONAL_COLLECTIONS = [
    "sales_orders", "purchase_orders", "payments", "inventory_movements",
    "journal_entries", "accounting_entries", "bank_transactions", "bank_accounts",
    "audit_logs", "notifications", "grns", "grn_items", "invoices",
    "payroll", "payrolls", "payroll_items", "attendance", "employee_tasks", "leaves",
    "advances", "employee_advances", "leave_requests", "leave_balances",
    "work_orders", "work_order_materials", "bom", "bill_of_materials",
    "raw_material_movements", "rm_grn", "rm_grn_returns", "rm_purchase_orders",
    "rm_accounts_payable", "rm_supplier_credits", "supplier_credits",
    "quality_inspections", "packaging_movements", "task_payments"
]
ALL_COLLECTIONS = MASTER_COLLECTIONS + TRANSACTIONAL_COLLECTIONS

# ============== DATA RESET ==============

@router.post("/data-reset", response_model=DataResetResponse)
async def reset_data(request: DataResetRequest, current_user: dict = Depends(get_current_user)):
    """
    Reset system data with safety checks.
    Requires admin role and confirmation code "RESET"
    """
    # Security checks
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    if request.confirmation_code != "RESET":
        raise HTTPException(status_code=400, detail="Invalid confirmation code. Type 'RESET' to confirm.")
    
    company_id = current_user["company_id"]
    collections_cleared = []
    
    try:
        # Create backup before reset (skip if backup fails on restricted environments)
        backup_name = f"pre-reset-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
        try:
            await _create_backup_internal(company_id, backup_name, current_user["user_id"], "Pre-reset automatic backup")
        except (PermissionError, OSError) as e:
            # Skip backup on environments with no write access (e.g., Render)
            logger.warning(f"Could not create pre-reset backup (permission denied), proceeding without backup: {e}")
        
        if request.reset_type == ResetType.TRANSACTIONAL:
            # Reset only transactional data
            for collection in TRANSACTIONAL_COLLECTIONS:
                result = await db[collection].delete_many({"company_id": company_id})
                if result.deleted_count > 0:
                    collections_cleared.append(collection)
            
            # Reset account balances to zero (keep accounts)
            await db.accounts.update_many(
                {"company_id": company_id},
                {"$set": {"current_balance": 0, "updated_at": get_current_timestamp()}}
            )
            
            # Reset product stock to zero
            await db.products.update_many(
                {"company_id": company_id},
                {"$set": {"stock_quantity": 0, "updated_at": get_current_timestamp()}}
            )
            
        elif request.reset_type == ResetType.FULL:
            # Reset everything except users and company settings (if specified)
            collections_to_clear = TRANSACTIONAL_COLLECTIONS.copy()
            
            if not request.keep_users:
                # Keep only the current admin user
                await db.users.delete_many({
                    "company_id": company_id,
                    "id": {"$ne": current_user["user_id"]}
                })
                collections_cleared.append("users (except current admin)")
            
            if not request.keep_company_settings:
                # Reset company settings but keep basic info
                await db.companies.update_one(
                    {"id": company_id},
                    {"$set": {
                        "woo_settings": None,
                        "tax_rate": 0,
                        "updated_at": get_current_timestamp()
                    }}
                )
                collections_cleared.append("company settings")
            
            # Clear master data (except users/companies if keeping)
            master_to_clear = ["accounts", "tax_rates", "products", "customers", "suppliers"]
            for collection in master_to_clear:
                result = await db[collection].delete_many({"company_id": company_id})
                if result.deleted_count > 0:
                    collections_cleared.append(collection)
            
            # Clear transactional data (includes GRN, grn_items)
            for collection in collections_to_clear:
                result = await db[collection].delete_many({"company_id": company_id})
                if result.deleted_count > 0:
                    collections_cleared.append(collection)
            
            # Also reset any remaining account balances to zero (Bank, Cash, etc.)
            # This handles any accounts that weren't deleted above
            remaining_accounts = await db.accounts.update_many(
                {"company_id": company_id},
                {"$set": {"current_balance": 0, "updated_at": get_current_timestamp()}}
            )
            if remaining_accounts.modified_count > 0:
                collections_cleared.append("account balances reset to zero")
        
        # Log the reset action
        await db.audit_logs.insert_one({
            "id": generate_id(),
            "company_id": company_id,
            "user_id": current_user["user_id"],
            "action": "data_reset",
            "details": {
                "reset_type": request.reset_type.value,
                "collections_cleared": collections_cleared,
                "reason": request.reason
            },
            "timestamp": get_current_timestamp()
        })
        
        return DataResetResponse(
            success=True,
            message=f"Data reset ({request.reset_type.value}) completed successfully",
            collections_cleared=collections_cleared,
            timestamp=get_current_timestamp()
        )
        
    except Exception as e:
        # Log failed reset attempt
        await db.audit_logs.insert_one({
            "id": generate_id(),
            "company_id": company_id,
            "user_id": current_user["user_id"],
            "action": "data_reset_failed",
            "details": {"error": str(e), "reset_type": request.reset_type.value},
            "timestamp": get_current_timestamp()
        })
        raise HTTPException(status_code=500, detail=f"Reset failed: {str(e)}")

@router.get("/data-reset/preview")
async def preview_reset(
    reset_type: str,
    current_user: dict = Depends(get_current_user)
):
    """Preview what will be affected by a data reset"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    company_id = current_user["company_id"]
    preview = {"collections": {}, "warnings": []}
    
    if reset_type == "transactional":
        collections = TRANSACTIONAL_COLLECTIONS
        preview["warnings"].append("Account balances will be reset to zero")
        preview["warnings"].append("Product stock quantities will be reset to zero")
    else:
        collections = ALL_COLLECTIONS
        preview["warnings"].append("All master data including products, customers, suppliers will be deleted")
        preview["warnings"].append("All GRN (Goods Received Notes) records will be deleted")
        preview["warnings"].append("Bank and Cash account balances will be reset to zero")
        preview["warnings"].append("Chart of accounts will need to be re-initialized")
    
    for collection in collections:
        count = await db[collection].count_documents({"company_id": company_id})
        if count > 0:
            preview["collections"][collection] = count
    
    return preview

# ============== BACKUP ==============

@router.get("/backups")
async def list_backups(current_user: dict = Depends(get_current_user)):
    """List all backups for the company"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    backups = await db.backups.find(
        {"company_id": current_user["company_id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    return backups

@router.post("/backups", response_model=BackupResponse)
async def create_backup(
    data: BackupCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new backup"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    company_id = current_user["company_id"]
    backup_name = data.name or f"backup-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
    
    backup = await _create_backup_internal(
        company_id, 
        backup_name, 
        current_user["user_id"],
        data.description,
        data.backup_type.value
    )
    
    return BackupResponse(**backup)

async def _create_backup_internal(
    company_id: str, 
    name: str, 
    user_id: str, 
    description: Optional[str] = None,
    backup_type: str = "full"
) -> dict:
    """Internal backup creation function"""
    backup_id = generate_id()
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    
    # Ensure backup directory exists
    company_backup_dir = os.path.join(BACKUP_DIR, company_id)
    os.makedirs(company_backup_dir, exist_ok=True)
    
    # Create backup record
    backup = {
        "id": backup_id,
        "company_id": company_id,
        "name": name,
        "description": description,
        "backup_type": backup_type,
        "status": BackupStatus.IN_PROGRESS.value,
        "file_path": None,
        "file_size": None,
        "collections_backed_up": [],
        "created_by": user_id,
        "created_at": get_current_timestamp(),
        "completed_at": None
    }
    await db.backups.insert_one(backup)
    
    try:
        # Collect data from all collections
        backup_data = {
            "metadata": {
                "backup_id": backup_id,
                "company_id": company_id,
                "created_at": get_current_timestamp(),
                "backup_type": backup_type
            },
            "collections": {}
        }
        
        collections_to_backup = ALL_COLLECTIONS if backup_type == "full" else TRANSACTIONAL_COLLECTIONS
        collections_backed_up = []
        
        for collection in collections_to_backup:
            docs = await db[collection].find(
                {"company_id": company_id},
                {"_id": 0}
            ).to_list(100000)
            
            if docs:
                backup_data["collections"][collection] = docs
                collections_backed_up.append(collection)
        
        # Save to compressed JSON file
        file_name = f"{backup_id}_{timestamp}.json.gz"
        file_path = os.path.join(company_backup_dir, file_name)
        
        with gzip.open(file_path, 'wt', encoding='utf-8') as f:
            json.dump(backup_data, f, default=str)
        
        file_size = os.path.getsize(file_path)
        
        # Update backup record
        await db.backups.update_one(
            {"id": backup_id},
            {"$set": {
                "status": BackupStatus.COMPLETED.value,
                "file_path": file_path,
                "file_size": file_size,
                "collections_backed_up": collections_backed_up,
                "completed_at": get_current_timestamp()
            }}
        )
        
        backup.update({
            "status": BackupStatus.COMPLETED.value,
            "file_path": file_path,
            "file_size": file_size,
            "collections_backed_up": collections_backed_up,
            "completed_at": get_current_timestamp()
        })
        
        # Log backup action
        await db.audit_logs.insert_one({
            "id": generate_id(),
            "company_id": company_id,
            "user_id": user_id,
            "action": "backup_created",
            "details": {
                "backup_id": backup_id,
                "name": name,
                "collections": collections_backed_up
            },
            "timestamp": get_current_timestamp()
        })
        
        return backup
        
    except Exception as e:
        await db.backups.update_one(
            {"id": backup_id},
            {"$set": {
                "status": BackupStatus.FAILED.value,
                "error": str(e),
                "completed_at": get_current_timestamp()
            }}
        )
        raise HTTPException(status_code=500, detail=f"Backup failed: {str(e)}")

@router.get("/backups/{backup_id}")
async def get_backup(backup_id: str, current_user: dict = Depends(get_current_user)):
    """Get backup details"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    backup = await db.backups.find_one(
        {"id": backup_id, "company_id": current_user["company_id"]},
        {"_id": 0}
    )
    if not backup:
        raise HTTPException(status_code=404, detail="Backup not found")
    
    return backup

@router.get("/backups/{backup_id}/download")
async def download_backup(backup_id: str, current_user: dict = Depends(get_current_user)):
    """Download backup file"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    backup = await db.backups.find_one(
        {"id": backup_id, "company_id": current_user["company_id"]}
    )
    if not backup:
        raise HTTPException(status_code=404, detail="Backup not found")
    
    if backup["status"] != BackupStatus.COMPLETED.value:
        raise HTTPException(status_code=400, detail="Backup not completed")
    
    if not backup.get("file_path") or not os.path.exists(backup["file_path"]):
        raise HTTPException(status_code=404, detail="Backup file not found")
    
    return FileResponse(
        backup["file_path"],
        media_type="application/gzip",
        filename=f"{backup['name']}.json.gz"
    )

@router.post("/backups/upload")
async def upload_backup(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload a backup file for later restore"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    company_id = current_user["company_id"]
    
    # Validate file type
    if not file.filename.endswith(('.json', '.json.gz', '.gz')):
        raise HTTPException(status_code=400, detail="Invalid file type. Must be .json or .json.gz")
    
    # Create backup directory if needed
    company_backup_dir = os.path.join(BACKUP_DIR, company_id)
    os.makedirs(company_backup_dir, exist_ok=True)
    
    backup_id = generate_id()
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')
    
    # Determine if file is gzipped
    is_gzipped = file.filename.endswith('.gz')
    
    try:
        # Read file content
        content = await file.read()
        
        # Validate JSON structure
        if is_gzipped:
            import io
            with gzip.open(io.BytesIO(content), 'rt', encoding='utf-8') as f:
                backup_data = json.load(f)
        else:
            backup_data = json.loads(content.decode('utf-8'))
        
        # Validate backup structure
        if "collections" not in backup_data:
            raise HTTPException(status_code=400, detail="Invalid backup format: missing 'collections' key")
        
        if "metadata" not in backup_data:
            raise HTTPException(status_code=400, detail="Invalid backup format: missing 'metadata' key")
        
        # Save file
        file_name = f"uploaded-{timestamp}.json.gz"
        file_path = os.path.join(company_backup_dir, file_name)
        
        # Save as gzipped
        with gzip.open(file_path, 'wt', encoding='utf-8') as f:
            json.dump(backup_data, f)
        
        file_size = os.path.getsize(file_path)
        
        # Calculate statistics from backup data
        collections_backed_up = list(backup_data["collections"].keys())
        total_records = sum(len(docs) for docs in backup_data["collections"].values())
        
        # Create backup record
        backup_record = {
            "id": backup_id,
            "company_id": company_id,
            "name": f"Uploaded-{timestamp}",
            "description": f"Uploaded from file: {file.filename}",
            "backup_type": "full",
            "status": BackupStatus.COMPLETED.value,
            "file_path": file_path,
            "file_size": file_size,
            "collections_backed_up": collections_backed_up,
            "total_records": total_records,
            "created_by": current_user["user_id"],
            "created_at": get_current_timestamp(),
            "original_backup_date": backup_data["metadata"].get("created_at", "Unknown"),
            "is_uploaded": True
        }
        
        await db.backups.insert_one(backup_record)
        
        return {
            "message": "Backup uploaded successfully",
            "backup_id": backup_id,
            "collections": collections_backed_up,
            "total_records": total_records,
            "file_size": file_size
        }
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format in backup file")
    except HTTPException:
        raise  # Re-raise HTTP exceptions (400, 403, etc.) as-is
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process backup file: {str(e)}")

@router.delete("/backups/{backup_id}")
async def delete_backup(backup_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a backup"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    backup = await db.backups.find_one(
        {"id": backup_id, "company_id": current_user["company_id"]}
    )
    if not backup:
        raise HTTPException(status_code=404, detail="Backup not found")
    
    # Delete file if exists
    if backup.get("file_path") and os.path.exists(backup["file_path"]):
        os.remove(backup["file_path"])
    
    # Delete record
    await db.backups.delete_one({"id": backup_id})
    
    return {"message": "Backup deleted successfully"}

# ============== RESTORE ==============

@router.post("/restore", response_model=RestoreResponse)
async def restore_backup(
    request: RestoreRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Restore data from a backup.
    Requires admin role and confirmation code "RESTORE"
    """
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    if request.confirmation_code != "RESTORE":
        raise HTTPException(status_code=400, detail="Invalid confirmation code. Type 'RESTORE' to confirm.")
    
    company_id = current_user["company_id"]
    
    # Get backup
    backup = await db.backups.find_one(
        {"id": request.backup_id, "company_id": company_id}
    )
    if not backup:
        raise HTTPException(status_code=404, detail="Backup not found")
    
    if backup["status"] != BackupStatus.COMPLETED.value:
        raise HTTPException(status_code=400, detail="Cannot restore incomplete backup")
    
    if not backup.get("file_path") or not os.path.exists(backup["file_path"]):
        raise HTTPException(status_code=404, detail="Backup file not found")
    
    try:
        # Create pre-restore backup (skip if backup fails on restricted environments)
        pre_restore_name = f"pre-restore-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
        try:
            await _create_backup_internal(company_id, pre_restore_name, current_user["user_id"], "Pre-restore automatic backup")
        except (PermissionError, OSError) as e:
            logger.warning(f"Could not create pre-restore backup (permission denied), proceeding: {e}")
        
        # Read backup file
        with gzip.open(backup["file_path"], 'rt', encoding='utf-8') as f:
            backup_data = json.load(f)
        
        collections_restored = []
        collections_to_restore = request.restore_collections or list(backup_data["collections"].keys())
        
        for collection in collections_to_restore:
            if collection not in backup_data["collections"]:
                continue
            
            docs = backup_data["collections"][collection]
            if not docs:
                continue
            
            # Clear existing data for this collection
            await db[collection].delete_many({"company_id": company_id})
            
            # Insert backed up data
            await db[collection].insert_many(docs)
            collections_restored.append(collection)
        
        # Log restore action
        await db.audit_logs.insert_one({
            "id": generate_id(),
            "company_id": company_id,
            "user_id": current_user["user_id"],
            "action": "data_restored",
            "details": {
                "backup_id": request.backup_id,
                "backup_name": backup["name"],
                "collections_restored": collections_restored
            },
            "timestamp": get_current_timestamp()
        })
        
        return RestoreResponse(
            success=True,
            message="Data restored successfully",
            collections_restored=collections_restored,
            timestamp=get_current_timestamp()
        )
        
    except Exception as e:
        await db.audit_logs.insert_one({
            "id": generate_id(),
            "company_id": company_id,
            "user_id": current_user["user_id"],
            "action": "restore_failed",
            "details": {"error": str(e), "backup_id": request.backup_id},
            "timestamp": get_current_timestamp()
        })
        raise HTTPException(status_code=500, detail=f"Restore failed: {str(e)}")

@router.get("/restore/preview/{backup_id}")
async def preview_restore(backup_id: str, current_user: dict = Depends(get_current_user)):
    """Preview what will be restored from a backup"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    backup = await db.backups.find_one(
        {"id": backup_id, "company_id": current_user["company_id"]}
    )
    if not backup:
        raise HTTPException(status_code=404, detail="Backup not found")
    
    if not backup.get("file_path") or not os.path.exists(backup["file_path"]):
        raise HTTPException(status_code=404, detail="Backup file not found")
    
    try:
        with gzip.open(backup["file_path"], 'rt', encoding='utf-8') as f:
            backup_data = json.load(f)
        
        preview = {
            "backup_name": backup["name"],
            "backup_date": backup["created_at"],
            "collections": {}
        }
        
        for collection, docs in backup_data["collections"].items():
            preview["collections"][collection] = len(docs)
        
        return preview
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read backup: {str(e)}")

# ============== SCHEDULED BACKUPS ==============

@router.get("/backup-schedules")
async def get_backup_schedules(current_user: dict = Depends(get_current_user)):
    """Get all scheduled backups"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    schedules = await db.backup_schedules.find(
        {"company_id": current_user["company_id"]},
        {"_id": 0}
    ).to_list(50)
    
    return schedules

@router.post("/backup-schedules")
async def create_backup_schedule(
    data: ScheduledBackupCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a scheduled backup"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    schedule_id = generate_id()
    schedule = {
        "id": schedule_id,
        "company_id": current_user["company_id"],
        **data.model_dump(),
        "last_run": None,
        "next_run": None,  # Would be calculated based on schedule
        "created_by": current_user["user_id"],
        "created_at": get_current_timestamp()
    }
    await db.backup_schedules.insert_one(schedule)
    
    return serialize_doc(schedule)

@router.delete("/backup-schedules/{schedule_id}")
async def delete_backup_schedule(schedule_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a scheduled backup"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    result = await db.backup_schedules.delete_one({
        "id": schedule_id,
        "company_id": current_user["company_id"]
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    return {"message": "Schedule deleted successfully"}

# ============== SYSTEM INFO ==============

@router.get("/system-info")
async def get_system_info(current_user: dict = Depends(get_current_user)):
    """Get system information and statistics"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    company_id = current_user["company_id"]
    
    # Get collection counts
    collection_stats = {}
    for collection in ALL_COLLECTIONS:
        count = await db[collection].count_documents({"company_id": company_id})
        collection_stats[collection] = count
    
    # Get backup stats
    backup_count = await db.backups.count_documents({"company_id": company_id})
    latest_backup = await db.backups.find_one(
        {"company_id": company_id, "status": BackupStatus.COMPLETED.value},
        {"_id": 0},
        sort=[("created_at", -1)]
    )
    
    # Get disk usage for backups
    company_backup_dir = os.path.join(BACKUP_DIR, company_id)
    backup_size = 0
    if os.path.exists(company_backup_dir):
        for file in os.listdir(company_backup_dir):
            file_path = os.path.join(company_backup_dir, file)
            if os.path.isfile(file_path):
                backup_size += os.path.getsize(file_path)
    
    return {
        "collection_stats": collection_stats,
        "total_records": sum(collection_stats.values()),
        "backup_count": backup_count,
        "latest_backup": latest_backup,
        "backup_storage_used_bytes": backup_size,
        "backup_storage_used_mb": round(backup_size / (1024 * 1024), 2)
    }
