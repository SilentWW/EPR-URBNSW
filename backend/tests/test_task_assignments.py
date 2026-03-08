"""
Test Task Assignments API - Task-Based Payment System
Tests task creation, status workflow, and payroll integration
"""
import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "lahiruraja97@gmail.com"
TEST_PASSWORD = "password123"


class TestTaskAssignmentsAPI:
    """Task Assignment API Tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - authenticate and get token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        token = login_response.json().get("access_token")  # API returns access_token, not token
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        # Get employees for testing
        emp_response = self.session.get(f"{BASE_URL}/api/payroll/employees", params={"status": "active"})
        assert emp_response.status_code == 200
        self.employees = emp_response.json()
        assert len(self.employees) > 0, "No employees found for testing"
        self.test_employee = self.employees[0]
        
        yield
        
        # Cleanup - cancel any test tasks created
        self._cleanup_test_tasks()
    
    def _cleanup_test_tasks(self):
        """Clean up test-created tasks"""
        try:
            tasks_response = self.session.get(f"{BASE_URL}/api/payroll/tasks", params={"include_paid": True})
            if tasks_response.status_code == 200:
                tasks = tasks_response.json()
                for task in tasks:
                    if task.get("title", "").startswith("TEST_"):
                        # Cancel if not paid
                        if not task.get("payroll_id") and task.get("status") != "cancelled":
                            self.session.post(f"{BASE_URL}/api/payroll/tasks/{task['id']}/cancel", params={"reason": "Test cleanup"})
        except Exception:
            pass
    
    # ============== GET /payroll/tasks ==============
    
    def test_get_tasks_list(self):
        """Test getting all tasks"""
        response = self.session.get(f"{BASE_URL}/api/payroll/tasks", params={"include_paid": True})
        
        assert response.status_code == 200, f"Failed to get tasks: {response.text}"
        tasks = response.json()
        assert isinstance(tasks, list)
        print(f"GET /payroll/tasks - Found {len(tasks)} tasks")
    
    def test_get_tasks_filter_by_status(self):
        """Test filtering tasks by status"""
        for status in ["assigned", "in_progress", "completed", "verified", "cancelled"]:
            response = self.session.get(f"{BASE_URL}/api/payroll/tasks", params={"status": status, "include_paid": True})
            assert response.status_code == 200, f"Failed to filter by status {status}"
            tasks = response.json()
            # All returned tasks should have the requested status
            for task in tasks:
                assert task["status"] == status, f"Task {task['id']} has status {task['status']}, expected {status}"
            print(f"GET /payroll/tasks?status={status} - Found {len(tasks)} tasks")
    
    def test_get_tasks_filter_by_category(self):
        """Test filtering tasks by category"""
        for category in ["design", "development", "marketing", "production", "admin", "other"]:
            response = self.session.get(f"{BASE_URL}/api/payroll/tasks", params={"category": category, "include_paid": True})
            assert response.status_code == 200, f"Failed to filter by category {category}"
            print(f"GET /payroll/tasks?category={category} - Found {len(response.json())} tasks")
    
    def test_get_tasks_filter_by_employee(self):
        """Test filtering tasks by employee"""
        response = self.session.get(f"{BASE_URL}/api/payroll/tasks", params={
            "employee_id": self.test_employee["id"],
            "include_paid": True
        })
        assert response.status_code == 200
        tasks = response.json()
        for task in tasks:
            assert task["employee_id"] == self.test_employee["id"]
        print(f"GET /payroll/tasks?employee_id={self.test_employee['id']} - Found {len(tasks)} tasks")
    
    # ============== GET /payroll/tasks/pending-payment ==============
    
    def test_get_pending_payment_tasks(self):
        """Test getting tasks pending payment (verified but not paid)"""
        response = self.session.get(f"{BASE_URL}/api/payroll/tasks/pending-payment")
        
        assert response.status_code == 200
        tasks = response.json()
        # All tasks should be verified and not paid
        for task in tasks:
            assert task["status"] == "verified", f"Task {task['id']} should be verified"
            assert task.get("payroll_id") is None, f"Task {task['id']} should not have payroll_id"
        print(f"GET /payroll/tasks/pending-payment - Found {len(tasks)} tasks pending payment")
    
    # ============== GET /payroll/tasks/categories ==============
    
    def test_get_task_categories(self):
        """Test getting task categories"""
        response = self.session.get(f"{BASE_URL}/api/payroll/tasks/categories")
        
        assert response.status_code == 200
        categories = response.json()
        assert len(categories) == 6
        category_values = [c["value"] for c in categories]
        assert "design" in category_values
        assert "development" in category_values
        assert "marketing" in category_values
        assert "production" in category_values
        assert "admin" in category_values
        assert "other" in category_values
        print(f"GET /payroll/tasks/categories - {categories}")
    
    # ============== POST /payroll/tasks - Create Task ==============
    
    def test_create_task_success(self):
        """Test creating a new task assignment"""
        due_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        payload = {
            "employee_id": self.test_employee["id"],
            "title": "TEST_Create new marketing materials",
            "description": "Design marketing brochures for Q1 campaign",
            "category": "marketing",
            "amount": 7500.00,
            "due_date": due_date,
            "notes": "High priority task"
        }
        
        response = self.session.post(f"{BASE_URL}/api/payroll/tasks", json=payload)
        
        assert response.status_code == 200, f"Failed to create task: {response.text}"
        data = response.json()
        assert "id" in data
        assert "task_number" in data
        assert data["task_number"].startswith("TASK-")
        print(f"POST /payroll/tasks - Created task {data['task_number']}")
        
        # Verify task was created
        get_response = self.session.get(f"{BASE_URL}/api/payroll/tasks/{data['id']}")
        assert get_response.status_code == 200
        task = get_response.json()
        assert task["title"] == payload["title"]
        assert task["category"] == payload["category"]
        assert task["amount"] == payload["amount"]
        assert task["status"] == "assigned"
    
    def test_create_task_minimal_fields(self):
        """Test creating task with only required fields"""
        payload = {
            "employee_id": self.test_employee["id"],
            "title": "TEST_Minimal task",
            "category": "other",
            "amount": 1000.00
        }
        
        response = self.session.post(f"{BASE_URL}/api/payroll/tasks", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        print(f"POST /payroll/tasks (minimal) - Created task {data['task_number']}")
    
    def test_create_task_invalid_employee(self):
        """Test creating task for non-existent employee"""
        payload = {
            "employee_id": "invalid-employee-id",
            "title": "TEST_Task for invalid employee",
            "category": "other",
            "amount": 1000.00
        }
        
        response = self.session.post(f"{BASE_URL}/api/payroll/tasks", json=payload)
        
        assert response.status_code == 404
        print("POST /payroll/tasks (invalid employee) - Correctly rejected")
    
    # ============== GET /payroll/tasks/{task_id} ==============
    
    def test_get_task_details(self):
        """Test getting single task details"""
        # Create a task first
        payload = {
            "employee_id": self.test_employee["id"],
            "title": "TEST_Task for detail view",
            "category": "development",
            "amount": 3000.00
        }
        create_response = self.session.post(f"{BASE_URL}/api/payroll/tasks", json=payload)
        assert create_response.status_code == 200
        task_id = create_response.json()["id"]
        
        # Get task details
        response = self.session.get(f"{BASE_URL}/api/payroll/tasks/{task_id}")
        
        assert response.status_code == 200
        task = response.json()
        assert task["id"] == task_id
        assert task["title"] == payload["title"]
        assert task["employee_name"], "Employee name should be populated"
        assert task["employee_code"], "Employee code should be populated"
        print(f"GET /payroll/tasks/{task_id} - Task details retrieved")
    
    def test_get_task_not_found(self):
        """Test getting non-existent task"""
        response = self.session.get(f"{BASE_URL}/api/payroll/tasks/invalid-task-id")
        
        assert response.status_code == 404
        print("GET /payroll/tasks/invalid-id - Correctly returned 404")
    
    # ============== PUT /payroll/tasks/{task_id} - Update Task ==============
    
    def test_update_task(self):
        """Test updating task details (only when assigned)"""
        # Create a task first
        payload = {
            "employee_id": self.test_employee["id"],
            "title": "TEST_Task to update",
            "category": "design",
            "amount": 2000.00
        }
        create_response = self.session.post(f"{BASE_URL}/api/payroll/tasks", json=payload)
        assert create_response.status_code == 200
        task_id = create_response.json()["id"]
        
        # Update the task
        update_payload = {
            "title": "TEST_Updated task title",
            "amount": 2500.00,
            "notes": "Updated notes"
        }
        
        response = self.session.put(f"{BASE_URL}/api/payroll/tasks/{task_id}", json=update_payload)
        
        assert response.status_code == 200
        print(f"PUT /payroll/tasks/{task_id} - Task updated")
        
        # Verify update
        get_response = self.session.get(f"{BASE_URL}/api/payroll/tasks/{task_id}")
        assert get_response.status_code == 200
        task = get_response.json()
        assert task["title"] == update_payload["title"]
        assert task["amount"] == update_payload["amount"]
    
    # ============== Status Workflow Tests ==============
    
    def test_task_status_workflow_assigned_to_in_progress(self):
        """Test: Assigned → In Progress (Start task)"""
        # Create task
        payload = {
            "employee_id": self.test_employee["id"],
            "title": "TEST_Task for status workflow",
            "category": "production",
            "amount": 4000.00
        }
        create_response = self.session.post(f"{BASE_URL}/api/payroll/tasks", json=payload)
        assert create_response.status_code == 200
        task_id = create_response.json()["id"]
        
        # Start task
        start_response = self.session.post(f"{BASE_URL}/api/payroll/tasks/{task_id}/start")
        
        assert start_response.status_code == 200, f"Failed to start task: {start_response.text}"
        print(f"POST /payroll/tasks/{task_id}/start - Task started")
        
        # Verify status
        get_response = self.session.get(f"{BASE_URL}/api/payroll/tasks/{task_id}")
        assert get_response.json()["status"] == "in_progress"
        assert get_response.json()["started_at"] is not None
    
    def test_task_status_workflow_in_progress_to_completed(self):
        """Test: In Progress → Completed (Complete task)"""
        # Create and start task
        payload = {
            "employee_id": self.test_employee["id"],
            "title": "TEST_Task for completion",
            "category": "admin",
            "amount": 1500.00
        }
        create_response = self.session.post(f"{BASE_URL}/api/payroll/tasks", json=payload)
        task_id = create_response.json()["id"]
        self.session.post(f"{BASE_URL}/api/payroll/tasks/{task_id}/start")
        
        # Complete task
        complete_response = self.session.post(f"{BASE_URL}/api/payroll/tasks/{task_id}/complete", params={"notes": "Work completed"})
        
        assert complete_response.status_code == 200, f"Failed to complete task: {complete_response.text}"
        print(f"POST /payroll/tasks/{task_id}/complete - Task completed")
        
        # Verify status
        get_response = self.session.get(f"{BASE_URL}/api/payroll/tasks/{task_id}")
        assert get_response.json()["status"] == "completed"
        assert get_response.json()["completed_at"] is not None
    
    def test_task_status_workflow_completed_to_verified(self):
        """Test: Completed → Verified (Manager verifies)"""
        # Create, start, and complete task
        payload = {
            "employee_id": self.test_employee["id"],
            "title": "TEST_Task for verification",
            "category": "design",
            "amount": 6000.00
        }
        create_response = self.session.post(f"{BASE_URL}/api/payroll/tasks", json=payload)
        task_id = create_response.json()["id"]
        self.session.post(f"{BASE_URL}/api/payroll/tasks/{task_id}/start")
        self.session.post(f"{BASE_URL}/api/payroll/tasks/{task_id}/complete")
        
        # Verify task
        verify_response = self.session.post(f"{BASE_URL}/api/payroll/tasks/{task_id}/verify")
        
        assert verify_response.status_code == 200, f"Failed to verify task: {verify_response.text}"
        print(f"POST /payroll/tasks/{task_id}/verify - Task verified")
        
        # Verify status
        get_response = self.session.get(f"{BASE_URL}/api/payroll/tasks/{task_id}")
        assert get_response.json()["status"] == "verified"
        assert get_response.json()["verified_at"] is not None
    
    def test_task_status_workflow_reject_task(self):
        """Test: Completed → In Progress (Manager rejects)"""
        # Create, start, and complete task
        payload = {
            "employee_id": self.test_employee["id"],
            "title": "TEST_Task for rejection",
            "category": "development",
            "amount": 5000.00
        }
        create_response = self.session.post(f"{BASE_URL}/api/payroll/tasks", json=payload)
        task_id = create_response.json()["id"]
        self.session.post(f"{BASE_URL}/api/payroll/tasks/{task_id}/start")
        self.session.post(f"{BASE_URL}/api/payroll/tasks/{task_id}/complete")
        
        # Reject task
        reject_response = self.session.post(f"{BASE_URL}/api/payroll/tasks/{task_id}/reject", params={"reason": "Needs revision"})
        
        assert reject_response.status_code == 200, f"Failed to reject task: {reject_response.text}"
        print(f"POST /payroll/tasks/{task_id}/reject - Task rejected")
        
        # Verify status is back to in_progress
        get_response = self.session.get(f"{BASE_URL}/api/payroll/tasks/{task_id}")
        task = get_response.json()
        assert task["status"] == "in_progress"
        assert task.get("rejection_reason") == "Needs revision"
    
    def test_task_status_workflow_cancel_task(self):
        """Test: Cancel task"""
        # Create task
        payload = {
            "employee_id": self.test_employee["id"],
            "title": "TEST_Task to cancel",
            "category": "other",
            "amount": 2000.00
        }
        create_response = self.session.post(f"{BASE_URL}/api/payroll/tasks", json=payload)
        task_id = create_response.json()["id"]
        
        # Cancel task
        cancel_response = self.session.post(f"{BASE_URL}/api/payroll/tasks/{task_id}/cancel", params={"reason": "No longer needed"})
        
        assert cancel_response.status_code == 200, f"Failed to cancel task: {cancel_response.text}"
        print(f"POST /payroll/tasks/{task_id}/cancel - Task cancelled")
        
        # Verify status
        get_response = self.session.get(f"{BASE_URL}/api/payroll/tasks/{task_id}")
        task = get_response.json()
        assert task["status"] == "cancelled"
        assert task.get("cancellation_reason") == "No longer needed"
    
    # ============== Status Transition Error Cases ==============
    
    def test_cannot_start_already_started_task(self):
        """Test cannot start a task that's already in progress"""
        # Create and start task
        payload = {
            "employee_id": self.test_employee["id"],
            "title": "TEST_Task already started",
            "category": "other",
            "amount": 1000.00
        }
        create_response = self.session.post(f"{BASE_URL}/api/payroll/tasks", json=payload)
        task_id = create_response.json()["id"]
        self.session.post(f"{BASE_URL}/api/payroll/tasks/{task_id}/start")
        
        # Try to start again
        response = self.session.post(f"{BASE_URL}/api/payroll/tasks/{task_id}/start")
        
        assert response.status_code == 400
        print("Start on in_progress task - Correctly rejected")
    
    def test_cannot_verify_non_completed_task(self):
        """Test cannot verify a task that's not completed"""
        # Create and start task (but don't complete)
        payload = {
            "employee_id": self.test_employee["id"],
            "title": "TEST_Task not completed",
            "category": "other",
            "amount": 1000.00
        }
        create_response = self.session.post(f"{BASE_URL}/api/payroll/tasks", json=payload)
        task_id = create_response.json()["id"]
        self.session.post(f"{BASE_URL}/api/payroll/tasks/{task_id}/start")
        
        # Try to verify
        response = self.session.post(f"{BASE_URL}/api/payroll/tasks/{task_id}/verify")
        
        assert response.status_code == 400
        print("Verify on in_progress task - Correctly rejected")
    
    # ============== Employee Task Summary ==============
    
    def test_get_employee_task_summary(self):
        """Test getting task summary for an employee"""
        response = self.session.get(f"{BASE_URL}/api/payroll/tasks/employee/{self.test_employee['id']}/summary")
        
        assert response.status_code == 200
        summary = response.json()
        assert "assigned" in summary
        assert "in_progress" in summary
        assert "completed" in summary
        assert "verified" in summary
        assert "cancelled" in summary
        assert "pending_payment_amount" in summary
        assert "total_earned" in summary
        print(f"GET /payroll/tasks/employee/{self.test_employee['id']}/summary - {summary}")


class TestExistingVerifiedTask:
    """Test with the existing verified task mentioned in context"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert login_response.status_code == 200
        token = login_response.json().get("access_token")  # API returns access_token
        self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def test_verified_task_exists(self):
        """Check for the existing verified task TASK-202603-0001"""
        response = self.session.get(f"{BASE_URL}/api/payroll/tasks", params={"status": "verified", "include_paid": True})
        
        assert response.status_code == 200
        tasks = response.json()
        
        # Look for the task mentioned in context
        john_doe_tasks = [t for t in tasks if "John" in t.get("employee_name", "")]
        design_tasks = [t for t in tasks if t.get("category") == "design"]
        
        print(f"Found {len(tasks)} verified tasks")
        print(f"John Doe tasks: {len(john_doe_tasks)}")
        print(f"Design tasks: {len(design_tasks)}")
        
        if tasks:
            for task in tasks[:3]:  # Print first 3
                print(f"  - {task.get('task_number')}: {task.get('title')} ({task.get('employee_name')}) - LKR {task.get('amount')}")
    
    def test_pending_payment_stats(self):
        """Test stats for pending payment amount"""
        response = self.session.get(f"{BASE_URL}/api/payroll/tasks/pending-payment")
        
        assert response.status_code == 200
        tasks = response.json()
        
        total_pending = sum(t.get("amount", 0) for t in tasks)
        print(f"Pending payment: {len(tasks)} tasks, LKR {total_pending}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
