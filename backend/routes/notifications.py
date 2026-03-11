"""
Notification System Routes
- In-App Notifications with WebSocket real-time updates
- Email Notifications using configurable SMTP
- User Notification Preferences
"""

from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
import jwt

router = APIRouter(prefix="/notifications", tags=["Notifications"])
security = HTTPBearer()

# These will be set by the main server
db = None
JWT_SECRET = None
JWT_ALGORITHM = "HS256"

def set_db(database):
    global db
    db = database

def set_jwt_config(secret, algorithm="HS256"):
    global JWT_SECRET, JWT_ALGORITHM
    JWT_SECRET = secret
    JWT_ALGORITHM = algorithm

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
        elif hasattr(value, '__str__') and type(value).__name__ == 'ObjectId':
            result[key] = str(value)
        elif isinstance(value, datetime):
            result[key] = value.isoformat()
        else:
            result[key] = value
    return result

# ============== MODELS ==============

class SMTPSettings(BaseModel):
    smtp_host: str
    smtp_port: int = 587
    smtp_username: str
    smtp_password: str
    from_email: str
    from_name: Optional[str] = "ERP System"
    use_tls: bool = True
    enabled: bool = True

class NotificationPreferences(BaseModel):
    task_assignments: bool = True
    task_updates: bool = True
    payroll_processed: bool = True
    payslip_ready: bool = True
    leave_approvals: bool = True
    leave_rejections: bool = True
    low_inventory: bool = True
    new_orders: bool = True
    email_enabled: bool = True
    in_app_enabled: bool = True

class NotificationCreate(BaseModel):
    user_id: Optional[str] = None
    title: str
    message: str
    notification_type: str
    severity: str = "info"
    reference_type: Optional[str] = None
    reference_id: Optional[str] = None
    send_email: bool = False

class NotificationUpdate(BaseModel):
    is_read: Optional[bool] = None

# ============== WEBSOCKET CONNECTION MANAGER ==============

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        logging.info(f"WebSocket connected for user {user_id}")
    
    def disconnect(self, websocket: WebSocket, user_id: str):
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        logging.info(f"WebSocket disconnected for user {user_id}")
    
    async def send_to_user(self, user_id: str, message: dict):
        if user_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    disconnected.append(connection)
            for conn in disconnected:
                self.disconnect(conn, user_id)
    
    async def broadcast_to_company(self, company_id: str, message: dict, exclude_user: str = None):
        """Send to all users in a company"""
        if db is None:
            return
        users = await db.users.find({"company_id": company_id}, {"id": 1}).to_list(1000)
        for user in users:
            if exclude_user and user["id"] == exclude_user:
                continue
            await self.send_to_user(user["id"], message)

manager = ConnectionManager()

# ============== EMAIL SERVICE ==============

async def get_smtp_settings(company_id: str) -> Optional[dict]:
    """Get SMTP settings for a company"""
    if db is None:
        return None
    settings = await db.smtp_settings.find_one({"company_id": company_id}, {"_id": 0})
    return settings

async def send_email_notification_fire_and_forget(
    company_id: str,
    to_email: str,
    to_name: str,
    subject: str,
    body_html: str,
    body_text: str = None
):
    """Send email in background without waiting - fire and forget"""
    import subprocess
    import json
    import os
    
    settings = await get_smtp_settings(company_id)
    if not settings or not settings.get("enabled"):
        logging.info(f"Email not sent - SMTP not configured or disabled for company {company_id}")
        return False
    
    try:
        config = {
            "smtp_host": settings["smtp_host"],
            "smtp_port": settings["smtp_port"],
            "smtp_user": settings["smtp_username"],
            "smtp_pass": settings["smtp_password"],
            "from_email": settings["from_email"],
            "from_name": settings.get("from_name", "ERP System"),
            "to_email": to_email,
            "subject": subject,
            "body_html": body_html,
            "body_text": body_text,
            "use_tls": settings.get("use_tls", True)
        }
        
        script_path = os.path.join(os.path.dirname(__file__), "..", "scripts", "send_email.py")
        
        # Fire and forget - don't wait for result
        subprocess.Popen(
            ["python3", script_path, json.dumps(config)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        logging.info(f"Email queued for sending to {to_email}")
        return True
            
    except Exception as e:
        logging.error(f"Failed to queue email: {str(e)}")
        return False

async def send_email_notification(
    company_id: str,
    to_email: str,
    to_name: str,
    subject: str,
    body_html: str,
    body_text: str = None
):
    """Send email using company's SMTP settings via subprocess"""
    import asyncio
    import subprocess
    import json
    import os
    
    settings = await get_smtp_settings(company_id)
    if not settings or not settings.get("enabled"):
        logging.info(f"Email not sent - SMTP not configured or disabled for company {company_id}")
        return False
    
    try:
        config = {
            "smtp_host": settings["smtp_host"],
            "smtp_port": settings["smtp_port"],
            "smtp_user": settings["smtp_username"],
            "smtp_pass": settings["smtp_password"],
            "from_email": settings["from_email"],
            "from_name": settings.get("from_name", "ERP System"),
            "to_email": to_email,
            "subject": subject,
            "body_html": body_html,
            "body_text": body_text,
            "use_tls": settings.get("use_tls", True)
        }
        
        script_path = os.path.join(os.path.dirname(__file__), "..", "scripts", "send_email.py")
        
        # Run as subprocess
        process = await asyncio.create_subprocess_exec(
            "python3", script_path, json.dumps(config),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=90.0)
        
        result = json.loads(stdout.decode())
        if result.get("success"):
            logging.info(f"Email sent successfully to {to_email}")
            return True
        else:
            logging.error(f"Failed to send email: {result.get('error')}")
            return False
            
    except asyncio.TimeoutError:
        logging.error("Email sending timed out")
        return False
    except Exception as e:
        logging.error(f"Failed to send email: {str(e)}")
        return False

def generate_notification_email(notification: dict, user_name: str) -> tuple:
    """Generate HTML and plain text email content"""
    severity_colors = {
        "info": "#3B82F6",
        "warning": "#F59E0B",
        "error": "#EF4444",
        "success": "#10B981"
    }
    color = severity_colors.get(notification.get("severity", "info"), "#3B82F6")
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: {color}; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
            .content {{ background-color: #f9fafb; padding: 20px; border-radius: 0 0 8px 8px; }}
            .footer {{ text-align: center; padding: 20px; color: #6b7280; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>{notification['title']}</h2>
            </div>
            <div class="content">
                <p>Hi {user_name},</p>
                <p>{notification['message']}</p>
                <p style="color: #6b7280; font-size: 14px;">
                    This notification was sent at {notification.get('created_at', 'N/A')}
                </p>
            </div>
            <div class="footer">
                <p>This is an automated message from your ERP System.</p>
                <p>You can manage your notification preferences in the Settings page.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    text = f"""
    {notification['title']}
    
    Hi {user_name},
    
    {notification['message']}
    
    This notification was sent at {notification.get('created_at', 'N/A')}
    
    ---
    This is an automated message from your ERP System.
    """
    
    return html, text

# ============== NOTIFICATION HELPER FUNCTIONS ==============

async def create_notification(
    company_id: str,
    user_id: str,
    title: str,
    message: str,
    notification_type: str,
    severity: str = "info",
    reference_type: str = None,
    reference_id: str = None,
    send_email: bool = True,
    created_by: str = None
):
    """Create a notification and optionally send email"""
    if db is None:
        return None
    
    prefs = await db.notification_preferences.find_one({"user_id": user_id}, {"_id": 0})
    
    if not prefs:
        prefs = NotificationPreferences().model_dump()
    
    type_to_pref = {
        "task_assignment": "task_assignments",
        "task_update": "task_updates",
        "payroll": "payroll_processed",
        "payslip": "payslip_ready",
        "payslip_ready": "payslip_ready",
        "leave_approval": "leave_approvals",
        "leave_rejection": "leave_rejections",
        "low_inventory": "low_inventory",
        "inventory": "low_inventory",
        "new_order": "new_orders",
        "order": "new_orders",
        "system": None
    }
    
    pref_key = type_to_pref.get(notification_type)
    
    if pref_key and not prefs.get(pref_key, True):
        return None
    
    notification_id = None
    if prefs.get("in_app_enabled", True):
        notification_id = str(uuid.uuid4())
        notification = {
            "id": notification_id,
            "company_id": company_id,
            "user_id": user_id,
            "title": title,
            "message": message,
            "type": notification_type,
            "severity": severity,
            "reference_type": reference_type,
            "reference_id": reference_id,
            "is_read": False,
            "created_by": created_by,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.notifications.insert_one(notification)
        
        await manager.send_to_user(user_id, {
            "type": "new_notification",
            "notification": serialize_doc(notification)
        })
    
    if send_email and prefs.get("email_enabled", True):
        user = await db.users.find_one({"id": user_id}, {"_id": 0, "email": 1, "full_name": 1})
        if user and user.get("email"):
            notification_data = {
                "title": title,
                "message": message,
                "severity": severity,
                "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            }
            html, text = generate_notification_email(notification_data, user.get("full_name", "User"))
            # Use fire-and-forget for task notifications (non-blocking)
            await send_email_notification_fire_and_forget(
                company_id,
                user["email"],
                user.get("full_name", "User"),
                f"[ERP] {title}",
                html,
                text
            )
    
    return notification_id

async def notify_users_by_role(
    company_id: str,
    roles: List[str],
    title: str,
    message: str,
    notification_type: str,
    severity: str = "info",
    reference_type: str = None,
    reference_id: str = None,
    send_email: bool = True,
    created_by: str = None
):
    """Send notification to all users with specified roles"""
    if db is None:
        return
    users = await db.users.find(
        {"company_id": company_id, "role": {"$in": roles}, "status": "approved"},
        {"_id": 0, "id": 1}
    ).to_list(1000)
    
    for user in users:
        await create_notification(
            company_id, user["id"], title, message, notification_type,
            severity, reference_type, reference_id, send_email, created_by
        )

# ============== ROUTES ==============

@router.get("")
async def get_notifications(
    unread_only: bool = False,
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    """Get notifications for the current user"""
    query = {
        "company_id": current_user["company_id"],
        "user_id": current_user["user_id"]
    }
    
    if unread_only:
        query["is_read"] = False
    
    notifications = await db.notifications.find(query, {"_id": 0}).sort("created_at", -1).to_list(limit)
    
    unread_count = await db.notifications.count_documents({
        "company_id": current_user["company_id"],
        "user_id": current_user["user_id"],
        "is_read": False
    })
    
    return {
        "notifications": notifications,
        "unread_count": unread_count
    }

@router.get("/unread-count")
async def get_unread_count(current_user: dict = Depends(get_current_user)):
    """Get unread notification count"""
    count = await db.notifications.count_documents({
        "company_id": current_user["company_id"],
        "user_id": current_user["user_id"],
        "is_read": False
    })
    return {"unread_count": count}

@router.put("/{notification_id}/read")
async def mark_notification_read(notification_id: str, current_user: dict = Depends(get_current_user)):
    """Mark a notification as read"""
    result = await db.notifications.update_one(
        {
            "id": notification_id,
            "user_id": current_user["user_id"]
        },
        {"$set": {"is_read": True, "read_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    return {"message": "Notification marked as read"}

@router.put("/mark-all-read")
async def mark_all_read(current_user: dict = Depends(get_current_user)):
    """Mark all notifications as read"""
    result = await db.notifications.update_many(
        {
            "user_id": current_user["user_id"],
            "is_read": False
        },
        {"$set": {"is_read": True, "read_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"message": f"Marked {result.modified_count} notifications as read"}

@router.delete("/{notification_id}")
async def delete_notification(notification_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a notification"""
    result = await db.notifications.delete_one({
        "id": notification_id,
        "user_id": current_user["user_id"]
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    return {"message": "Notification deleted"}

@router.delete("")
async def clear_all_notifications(current_user: dict = Depends(get_current_user)):
    """Clear all notifications for current user"""
    result = await db.notifications.delete_many({
        "user_id": current_user["user_id"]
    })
    
    return {"message": f"Deleted {result.deleted_count} notifications"}

# ============== NOTIFICATION PREFERENCES ==============

@router.get("/preferences")
async def get_notification_preferences(current_user: dict = Depends(get_current_user)):
    """Get notification preferences for current user"""
    prefs = await db.notification_preferences.find_one(
        {"user_id": current_user["user_id"]},
        {"_id": 0}
    )
    
    if not prefs:
        prefs = {
            "user_id": current_user["user_id"],
            **NotificationPreferences().model_dump()
        }
    
    return prefs

@router.put("/preferences")
async def update_notification_preferences(
    preferences: NotificationPreferences,
    current_user: dict = Depends(get_current_user)
):
    """Update notification preferences"""
    prefs_data = {
        "user_id": current_user["user_id"],
        "company_id": current_user["company_id"],
        **preferences.model_dump(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.notification_preferences.update_one(
        {"user_id": current_user["user_id"]},
        {"$set": prefs_data},
        upsert=True
    )
    
    return {"message": "Preferences updated successfully"}

# ============== SMTP SETTINGS (Admin Only) ==============

@router.get("/smtp-settings")
async def get_smtp_settings_route(current_user: dict = Depends(get_current_user)):
    """Get SMTP settings for the company (admin only)"""
    if current_user["role"] not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    settings = await db.smtp_settings.find_one(
        {"company_id": current_user["company_id"]},
        {"_id": 0, "smtp_password": 0}
    )
    
    if not settings:
        return {"configured": False}
    
    return {**settings, "configured": True}

@router.put("/smtp-settings")
async def update_smtp_settings(
    settings: SMTPSettings,
    current_user: dict = Depends(get_current_user)
):
    """Update SMTP settings (admin only)"""
    if current_user["role"] not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    settings_data = {
        "company_id": current_user["company_id"],
        **settings.model_dump(),
        "updated_by": current_user["user_id"],
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.smtp_settings.update_one(
        {"company_id": current_user["company_id"]},
        {"$set": settings_data},
        upsert=True
    )
    
    await db.audit_logs.insert_one({
        "id": str(uuid.uuid4()),
        "company_id": current_user["company_id"],
        "user_id": current_user["user_id"],
        "action": "smtp_settings_updated",
        "details": {"smtp_host": settings.smtp_host, "from_email": settings.from_email},
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    return {"message": "SMTP settings updated successfully"}

@router.post("/smtp-settings/test")
async def test_smtp_settings(
    test_email: str,
    current_user: dict = Depends(get_current_user)
):
    """Test SMTP settings by sending a test email"""
    if current_user["role"] not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    settings = await get_smtp_settings(current_user["company_id"])
    if not settings:
        raise HTTPException(status_code=400, detail="SMTP settings not configured")
    
    user = await db.users.find_one({"id": current_user["user_id"]}, {"_id": 0})
    
    test_notification = {
        "title": "SMTP Test Email",
        "message": "This is a test email to verify your SMTP configuration is working correctly.",
        "severity": "info",
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    }
    
    html, text = generate_notification_email(test_notification, user.get("full_name", "Admin"))
    
    # For test email, we wait for it to complete
    # Using a longer timeout since SMTP can be slow
    import asyncio
    try:
        success = await asyncio.wait_for(
            send_email_notification(
                current_user["company_id"],
                test_email,
                user.get("full_name", "Admin"),
                "[ERP] SMTP Test Email",
                html,
                text
            ),
            timeout=120.0  # 2 minute timeout for test
        )
    except asyncio.TimeoutError:
        raise HTTPException(status_code=500, detail="Email sending timed out. Please check your SMTP settings.")
    
    if success:
        return {"message": "Test email sent successfully! Please check your inbox."}
    else:
        raise HTTPException(status_code=500, detail="Failed to send test email. Please check your SMTP settings.")

# ============== ADMIN: SEND NOTIFICATION ==============

@router.post("/send")
async def send_notification(
    notification: NotificationCreate,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """Send a notification (admin/manager only)"""
    if current_user["role"] not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    company_id = current_user["company_id"]
    
    if notification.user_id:
        await create_notification(
            company_id,
            notification.user_id,
            notification.title,
            notification.message,
            notification.notification_type,
            notification.severity,
            notification.reference_type,
            notification.reference_id,
            notification.send_email,
            current_user["user_id"]
        )
    else:
        users = await db.users.find(
            {"company_id": company_id, "status": "approved"},
            {"_id": 0, "id": 1}
        ).to_list(1000)
        
        for user in users:
            await create_notification(
                company_id,
                user["id"],
                notification.title,
                notification.message,
                notification.notification_type,
                notification.severity,
                notification.reference_type,
                notification.reference_id,
                notification.send_email,
                current_user["user_id"]
            )
    
    return {"message": "Notification sent successfully"}

# WebSocket endpoint - will be registered separately on the main app
async def websocket_notifications(websocket: WebSocket, token: str):
    """WebSocket connection for real-time notifications"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("user_id")
        
        if not user_id:
            await websocket.close(code=4001)
            return
        
        await manager.connect(websocket, user_id)
        
        try:
            while True:
                data = await websocket.receive_text()
                if data == "ping":
                    await websocket.send_text("pong")
        except WebSocketDisconnect:
            manager.disconnect(websocket, user_id)
    except jwt.ExpiredSignatureError:
        await websocket.close(code=4002)
    except jwt.InvalidTokenError:
        await websocket.close(code=4003)
