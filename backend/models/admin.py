"""
Admin module models - Backup, Restore, Data Reset
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum

class ResetType(str, Enum):
    TRANSACTIONAL = "transactional"  # Reset only transactional data, keep master data
    FULL = "full"  # Reset everything except user accounts

class BackupType(str, Enum):
    FULL = "full"
    INCREMENTAL = "incremental"

class BackupStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

# Data Reset Models
class DataResetRequest(BaseModel):
    reset_type: ResetType
    confirmation_code: str  # User must type "RESET" to confirm
    keep_users: bool = True
    keep_company_settings: bool = True
    reason: Optional[str] = None

class DataResetResponse(BaseModel):
    success: bool
    message: str
    collections_cleared: List[str]
    timestamp: str

# Backup Models
class BackupCreate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    backup_type: BackupType = BackupType.FULL
    include_files: bool = True

class BackupResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    backup_type: str
    status: str
    file_path: Optional[str]
    file_size: Optional[int]
    collections_backed_up: List[str]
    created_by: str
    created_at: str
    completed_at: Optional[str]

class RestoreRequest(BaseModel):
    backup_id: str
    confirmation_code: str  # User must type "RESTORE" to confirm
    restore_collections: Optional[List[str]] = None  # None means restore all

class RestoreResponse(BaseModel):
    success: bool
    message: str
    collections_restored: List[str]
    timestamp: str

# Scheduled Backup Models
class ScheduledBackupCreate(BaseModel):
    name: str
    schedule_type: str  # daily, weekly, monthly
    time: str  # HH:MM format
    day_of_week: Optional[int] = None  # 0-6 for weekly
    day_of_month: Optional[int] = None  # 1-31 for monthly
    retention_days: int = 30
    is_active: bool = True
