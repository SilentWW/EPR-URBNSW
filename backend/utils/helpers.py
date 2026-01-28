"""
Common helper functions for the ERP system
"""
from bson import ObjectId
from datetime import datetime, timezone
import uuid

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

def generate_id() -> str:
    """Generate a unique ID"""
    return str(uuid.uuid4())

def get_current_timestamp() -> str:
    """Get current timestamp in ISO format"""
    return datetime.now(timezone.utc).isoformat()

def get_financial_year_dates(date: datetime = None, fy_start_month: int = 4) -> tuple:
    """
    Get financial year start and end dates.
    Default: April 1 - March 31
    """
    if date is None:
        date = datetime.now(timezone.utc)
    
    year = date.year
    
    # If we're before the FY start month, we're in the previous FY
    if date.month < fy_start_month:
        fy_start = datetime(year - 1, fy_start_month, 1, tzinfo=timezone.utc)
        fy_end = datetime(year, fy_start_month - 1 if fy_start_month > 1 else 12, 31, 23, 59, 59, tzinfo=timezone.utc)
    else:
        fy_start = datetime(year, fy_start_month, 1, tzinfo=timezone.utc)
        fy_end = datetime(year + 1, fy_start_month - 1 if fy_start_month > 1 else 12, 31, 23, 59, 59, tzinfo=timezone.utc)
    
    # Adjust for March (month 3) ending
    if fy_start_month == 4:
        if date.month < 4:
            fy_end = datetime(year, 3, 31, 23, 59, 59, tzinfo=timezone.utc)
        else:
            fy_end = datetime(year + 1, 3, 31, 23, 59, 59, tzinfo=timezone.utc)
    
    return fy_start, fy_end

def format_currency(amount: float, currency: str = "LKR") -> str:
    """Format amount as currency string"""
    return f"{currency} {amount:,.2f}"
