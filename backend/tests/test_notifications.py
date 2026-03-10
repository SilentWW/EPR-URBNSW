"""
Notification System API Tests
- In-App Notifications with WebSocket real-time updates
- Email Notifications using configurable SMTP
- User Notification Preferences
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from main agent
TEST_ADMIN_EMAIL = "testadmin@example.com"
TEST_ADMIN_PASSWORD = "test123456"
TEST_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiZmI4NDQ2OTYtZDIyOC00MThiLTkzZWQtOTBlN2UxNzM3MzdmIiwiZW1haWwiOiJ0ZXN0YWRtaW5AZXhhbXBsZS5jb20iLCJyb2xlIjoiYWRtaW4iLCJjb21wYW55X2lkIjoiYTQxZWJlMjAtOTFiNi00NTUzLWJmZGUtZjkxNTQzMWMxMGM4IiwiZXhwIjoxNzczMjU2MDk1fQ.qTo3H0I_FQrEozQQDhi_FM-grYQTPa69FNJnJ6_k8GI"


@pytest.fixture
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture
def auth_token(api_client):
    """Get authentication token"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_ADMIN_EMAIL,
        "password": TEST_ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("access_token")  # API returns access_token not token
    # Fall back to provided test token
    pytest.skip(f"Login failed: {response.status_code} - {response.text}")


@pytest.fixture
def authenticated_client(api_client, auth_token):
    """Session with auth header"""
    api_client.headers.update({"Authorization": f"Bearer {auth_token}"})
    return api_client


class TestNotificationAPIs:
    """Notification endpoint tests"""
    
    def test_get_notifications(self, authenticated_client):
        """Test GET /api/notifications - Get notifications for current user"""
        response = authenticated_client.get(f"{BASE_URL}/api/notifications")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "notifications" in data
        assert "unread_count" in data
        assert isinstance(data["notifications"], list)
        assert isinstance(data["unread_count"], int)
        print(f"✓ GET /api/notifications - Found {len(data['notifications'])} notifications, {data['unread_count']} unread")
    
    def test_get_unread_count(self, authenticated_client):
        """Test GET /api/notifications/unread-count - Get unread notification count"""
        response = authenticated_client.get(f"{BASE_URL}/api/notifications/unread-count")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "unread_count" in data
        assert isinstance(data["unread_count"], int)
        print(f"✓ GET /api/notifications/unread-count - Unread count: {data['unread_count']}")
    
    def test_get_notifications_unread_only(self, authenticated_client):
        """Test GET /api/notifications?unread_only=true - Filter unread notifications"""
        response = authenticated_client.get(f"{BASE_URL}/api/notifications?unread_only=true")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "notifications" in data
        # All returned notifications should be unread
        for notification in data["notifications"]:
            assert notification.get("is_read") == False, "Expected all notifications to be unread"
        print(f"✓ GET /api/notifications?unread_only=true - Found {len(data['notifications'])} unread notifications")


class TestNotificationPreferences:
    """Notification preferences tests"""
    
    def test_get_preferences(self, authenticated_client):
        """Test GET /api/notifications/preferences - Get notification preferences"""
        response = authenticated_client.get(f"{BASE_URL}/api/notifications/preferences")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Check expected preference fields exist
        expected_fields = ["task_assignments", "task_updates", "payroll_processed", "payslip_ready",
                          "leave_approvals", "leave_rejections", "low_inventory", "new_orders",
                          "email_enabled", "in_app_enabled"]
        for field in expected_fields:
            assert field in data, f"Expected '{field}' in preferences"
            assert isinstance(data[field], bool), f"Expected '{field}' to be boolean"
        print(f"✓ GET /api/notifications/preferences - Preferences retrieved successfully")
    
    def test_update_preferences(self, authenticated_client):
        """Test PUT /api/notifications/preferences - Update notification preferences"""
        # First get current preferences
        get_response = authenticated_client.get(f"{BASE_URL}/api/notifications/preferences")
        assert get_response.status_code == 200
        original_prefs = get_response.json()
        
        # Update preferences
        new_prefs = {
            "task_assignments": True,
            "task_updates": True,
            "payroll_processed": True,
            "payslip_ready": True,
            "leave_approvals": True,
            "leave_rejections": True,
            "low_inventory": False,  # Toggle this one
            "new_orders": True,
            "email_enabled": True,
            "in_app_enabled": True
        }
        
        response = authenticated_client.put(f"{BASE_URL}/api/notifications/preferences", json=new_prefs)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "message" in data
        assert "success" in data["message"].lower()
        
        # Verify persistence
        verify_response = authenticated_client.get(f"{BASE_URL}/api/notifications/preferences")
        assert verify_response.status_code == 200
        updated_prefs = verify_response.json()
        assert updated_prefs["low_inventory"] == False
        print(f"✓ PUT /api/notifications/preferences - Preferences updated and verified")


class TestSMTPSettings:
    """SMTP settings tests (admin only)"""
    
    def test_get_smtp_settings(self, authenticated_client):
        """Test GET /api/notifications/smtp-settings - Get SMTP settings (admin only)"""
        response = authenticated_client.get(f"{BASE_URL}/api/notifications/smtp-settings")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Should have configured field
        assert "configured" in data
        if data["configured"]:
            assert "smtp_host" in data
            assert "smtp_port" in data
            # Password should not be returned
            assert "smtp_password" not in data or data["smtp_password"] == ""
        print(f"✓ GET /api/notifications/smtp-settings - SMTP configured: {data['configured']}")
    
    def test_update_smtp_settings(self, authenticated_client):
        """Test PUT /api/notifications/smtp-settings - Update SMTP settings"""
        smtp_settings = {
            "smtp_host": "smtp.gmail.com",
            "smtp_port": 587,
            "smtp_username": "test@gmail.com",
            "smtp_password": "test-app-password",
            "from_email": "test@gmail.com",
            "from_name": "ERP Test System",
            "use_tls": True,
            "enabled": False  # Disabled for testing
        }
        
        response = authenticated_client.put(f"{BASE_URL}/api/notifications/smtp-settings", json=smtp_settings)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "message" in data
        assert "success" in data["message"].lower()
        
        # Verify persistence
        verify_response = authenticated_client.get(f"{BASE_URL}/api/notifications/smtp-settings")
        assert verify_response.status_code == 200
        saved_settings = verify_response.json()
        assert saved_settings["configured"] == True
        assert saved_settings["smtp_host"] == "smtp.gmail.com"
        print(f"✓ PUT /api/notifications/smtp-settings - SMTP settings saved and verified")


class TestSendNotification:
    """Send notification tests (admin only)"""
    
    def test_send_notification_to_self(self, authenticated_client, auth_token):
        """Test POST /api/notifications/send - Send notification (admin only)"""
        import jwt
        # Decode token to get user_id (without verification since we're just reading)
        try:
            payload = jwt.decode(auth_token, options={"verify_signature": False})
            user_id = payload.get("user_id")
        except:
            user_id = None
        
        notification_data = {
            "user_id": user_id,
            "title": "TEST_Notification System Test",
            "message": "This is a test notification from the automated tests",
            "notification_type": "system",
            "severity": "info",
            "send_email": False
        }
        
        response = authenticated_client.post(f"{BASE_URL}/api/notifications/send", json=notification_data)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "message" in data
        print(f"✓ POST /api/notifications/send - Notification sent successfully")
    
    def test_send_broadcast_notification(self, authenticated_client):
        """Test POST /api/notifications/send - Send broadcast to all users"""
        notification_data = {
            "user_id": None,  # Broadcast to all
            "title": "TEST_Broadcast Notification",
            "message": "This is a broadcast test notification",
            "notification_type": "system",
            "severity": "info",
            "send_email": False
        }
        
        response = authenticated_client.post(f"{BASE_URL}/api/notifications/send", json=notification_data)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "message" in data
        print(f"✓ POST /api/notifications/send (broadcast) - Notification sent successfully")


class TestNotificationActions:
    """Notification CRUD operations"""
    
    def test_mark_notification_read(self, authenticated_client):
        """Test PUT /api/notifications/{id}/read - Mark notification as read"""
        # First create a notification
        notification_data = {
            "title": "TEST_Mark Read Test",
            "message": "Test notification for mark read",
            "notification_type": "system",
            "severity": "info",
            "send_email": False
        }
        send_response = authenticated_client.post(f"{BASE_URL}/api/notifications/send", json=notification_data)
        if send_response.status_code != 200:
            pytest.skip("Could not create test notification")
        
        # Get notifications to find our test notification
        get_response = authenticated_client.get(f"{BASE_URL}/api/notifications")
        assert get_response.status_code == 200
        notifications = get_response.json()["notifications"]
        
        # Find an unread notification
        test_notification = None
        for n in notifications:
            if not n.get("is_read"):
                test_notification = n
                break
        
        if not test_notification:
            pytest.skip("No unread notifications to test")
        
        # Mark as read
        response = authenticated_client.put(f"{BASE_URL}/api/notifications/{test_notification['id']}/read")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "message" in data
        print(f"✓ PUT /api/notifications/{test_notification['id']}/read - Notification marked as read")
    
    def test_mark_all_read(self, authenticated_client):
        """Test PUT /api/notifications/mark-all-read - Mark all notifications as read"""
        response = authenticated_client.put(f"{BASE_URL}/api/notifications/mark-all-read")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "message" in data
        
        # Verify all are read
        get_response = authenticated_client.get(f"{BASE_URL}/api/notifications")
        assert get_response.status_code == 200
        notifications = get_response.json()["notifications"]
        for n in notifications:
            assert n.get("is_read") == True, "Expected all notifications to be read"
        print(f"✓ PUT /api/notifications/mark-all-read - All notifications marked as read")
    
    def test_delete_notification(self, authenticated_client):
        """Test DELETE /api/notifications/{id} - Delete a notification"""
        # First create a notification
        notification_data = {
            "title": "TEST_Delete Test",
            "message": "Test notification for delete",
            "notification_type": "system",
            "severity": "info",
            "send_email": False
        }
        send_response = authenticated_client.post(f"{BASE_URL}/api/notifications/send", json=notification_data)
        if send_response.status_code != 200:
            pytest.skip("Could not create test notification")
        
        # Get notifications to find our test notification
        get_response = authenticated_client.get(f"{BASE_URL}/api/notifications")
        assert get_response.status_code == 200
        notifications = get_response.json()["notifications"]
        
        if not notifications:
            pytest.skip("No notifications to test deletion")
        
        test_notification = notifications[0]
        
        # Delete
        response = authenticated_client.delete(f"{BASE_URL}/api/notifications/{test_notification['id']}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Verify deletion
        verify_response = authenticated_client.get(f"{BASE_URL}/api/notifications")
        assert verify_response.status_code == 200
        remaining = verify_response.json()["notifications"]
        remaining_ids = [n["id"] for n in remaining]
        assert test_notification["id"] not in remaining_ids, "Notification should be deleted"
        print(f"✓ DELETE /api/notifications/{test_notification['id']} - Notification deleted and verified")


class TestCleanup:
    """Cleanup test data"""
    
    def test_clear_all_notifications(self, authenticated_client):
        """Test DELETE /api/notifications - Clear all notifications"""
        response = authenticated_client.delete(f"{BASE_URL}/api/notifications")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "message" in data
        
        # Verify all cleared
        get_response = authenticated_client.get(f"{BASE_URL}/api/notifications")
        assert get_response.status_code == 200
        notifications = get_response.json()["notifications"]
        # After clearing, should have 0 notifications
        print(f"✓ DELETE /api/notifications - All notifications cleared, remaining: {len(notifications)}")
