"""
Employee Portal API Tests - Phase 1
Tests for Task Categories, Enhanced Tasks, Task Workflow, Comments, Time Logs, Subtasks, and Dashboard
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "manager_test@test.com"
TEST_PASSWORD = "test123"

@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json()["access_token"]

@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Get headers with auth token"""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }

# ============== TASK CATEGORIES TESTS ==============

class TestTaskCategories:
    """Task Categories CRUD API tests - Manager/Admin only"""
    
    def test_get_task_categories(self, auth_headers):
        """GET /api/portal/task-categories - should return list of categories"""
        response = requests.get(
            f"{BASE_URL}/api/portal/task-categories",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Existing Production category should be present
        if len(data) > 0:
            assert "id" in data[0]
            assert "name" in data[0]
            assert "color" in data[0]
            print(f"Found {len(data)} existing task categories")
    
    def test_create_task_category(self, auth_headers):
        """POST /api/portal/task-categories - create new category"""
        category_data = {
            "name": f"TEST_Category_{uuid.uuid4().hex[:6]}",
            "color": "#ef4444",
            "description": "Test category for automated testing"
        }
        response = requests.post(
            f"{BASE_URL}/api/portal/task-categories",
            headers=auth_headers,
            json=category_data
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["name"] == category_data["name"]
        assert data["color"] == category_data["color"]
        assert data["is_active"] == True
        print(f"Created category: {data['name']} with id: {data['id']}")
        return data["id"]
    
    def test_update_task_category(self, auth_headers):
        """PUT /api/portal/task-categories/{id} - update category"""
        # First create a category to update
        create_resp = requests.post(
            f"{BASE_URL}/api/portal/task-categories",
            headers=auth_headers,
            json={
                "name": f"TEST_Update_{uuid.uuid4().hex[:6]}",
                "color": "#3b82f6"
            }
        )
        assert create_resp.status_code == 200
        category_id = create_resp.json()["id"]
        
        # Update the category
        update_data = {
            "name": f"TEST_Updated_{uuid.uuid4().hex[:6]}",
            "description": "Updated description"
        }
        response = requests.put(
            f"{BASE_URL}/api/portal/task-categories/{category_id}",
            headers=auth_headers,
            json=update_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        print(f"Updated category: {data['name']}")
    
    def test_delete_task_category(self, auth_headers):
        """DELETE /api/portal/task-categories/{id} - soft delete category"""
        # First create a category to delete
        create_resp = requests.post(
            f"{BASE_URL}/api/portal/task-categories",
            headers=auth_headers,
            json={
                "name": f"TEST_Delete_{uuid.uuid4().hex[:6]}",
                "color": "#f97316"
            }
        )
        assert create_resp.status_code == 200
        category_id = create_resp.json()["id"]
        
        # Delete the category
        response = requests.delete(
            f"{BASE_URL}/api/portal/task-categories/{category_id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Category deleted"
        print(f"Deleted category: {category_id}")
    
    def test_category_duplicate_name_rejected(self, auth_headers):
        """POST /api/portal/task-categories - duplicate name should be rejected"""
        unique_name = f"TEST_Dupe_{uuid.uuid4().hex[:6]}"
        # Create first category
        requests.post(
            f"{BASE_URL}/api/portal/task-categories",
            headers=auth_headers,
            json={"name": unique_name, "color": "#22c55e"}
        )
        # Try to create duplicate
        response = requests.post(
            f"{BASE_URL}/api/portal/task-categories",
            headers=auth_headers,
            json={"name": unique_name, "color": "#8b5cf6"}
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()
        print("Duplicate name correctly rejected")

# ============== ENHANCED TASKS TESTS ==============

class TestEnhancedTasks:
    """Enhanced Tasks API tests - CRUD and enriched data"""
    
    def test_get_tasks(self, auth_headers):
        """GET /api/portal/tasks - should return list of tasks"""
        response = requests.get(
            f"{BASE_URL}/api/portal/tasks",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Check enriched data on existing task
        if len(data) > 0:
            task = data[0]
            assert "id" in task
            assert "task_number" in task
            assert "employee_name" in task
            assert "category_name" in task
            assert "subtasks_total" in task
            assert "total_hours" in task
            print(f"Found {len(data)} tasks")
    
    def test_get_tasks_with_filters(self, auth_headers):
        """GET /api/portal/tasks - test filtering options"""
        # Filter by status
        response = requests.get(
            f"{BASE_URL}/api/portal/tasks?status=in_progress",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        for task in data:
            assert task["status"] == "in_progress"
        print(f"Filter by status works: {len(data)} in_progress tasks")
        
        # Filter by priority
        response = requests.get(
            f"{BASE_URL}/api/portal/tasks?priority=high",
            headers=auth_headers
        )
        assert response.status_code == 200
        print("Filter by priority works")
    
    def test_get_task_detail(self, auth_headers):
        """GET /api/portal/tasks/{id} - get detailed task info"""
        # Get all tasks first
        tasks_resp = requests.get(f"{BASE_URL}/api/portal/tasks", headers=auth_headers)
        tasks = tasks_resp.json()
        
        if len(tasks) == 0:
            pytest.skip("No tasks available to test detail view")
        
        task_id = tasks[0]["id"]
        response = requests.get(
            f"{BASE_URL}/api/portal/tasks/{task_id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == task_id
        assert "comments" in data
        assert "time_logs" in data
        assert "subtasks" in data
        print(f"Task detail retrieved: {data['task_number']}")
    
    def test_create_task(self, auth_headers):
        """POST /api/portal/tasks - create new task with subtasks"""
        # First get an employee to assign task to (payroll employees)
        employees_resp = requests.get(f"{BASE_URL}/api/payroll/employees", headers=auth_headers)
        if employees_resp.status_code != 200 or len(employees_resp.json()) == 0:
            pytest.skip("No employees available to assign task")
        
        employee_id = employees_resp.json()[0]["id"]
        
        # Get a category
        categories_resp = requests.get(f"{BASE_URL}/api/portal/task-categories", headers=auth_headers)
        category_id = categories_resp.json()[0]["id"] if len(categories_resp.json()) > 0 else None
        
        task_data = {
            "employee_id": employee_id,
            "title": f"TEST_Task_{uuid.uuid4().hex[:6]}",
            "description": "Automated test task",
            "category_id": category_id,
            "priority": "medium",
            "due_date": "2026-03-20",
            "amount": 500.0,
            "subtasks": [
                {"title": "Subtask 1"},
                {"title": "Subtask 2"}
            ]
        }
        response = requests.post(
            f"{BASE_URL}/api/portal/tasks",
            headers=auth_headers,
            json=task_data
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "task_number" in data
        assert data["message"] == "Task created successfully"
        print(f"Created task: {data['task_number']}")
        return data["id"]
    
    def test_update_task(self, auth_headers):
        """PUT /api/portal/tasks/{id} - update task details"""
        # Get existing task
        tasks_resp = requests.get(f"{BASE_URL}/api/portal/tasks", headers=auth_headers)
        tasks = tasks_resp.json()
        test_tasks = [t for t in tasks if "TEST_" in t.get("title", "")]
        
        if len(test_tasks) == 0:
            # Create a task for testing
            employees_resp = requests.get(f"{BASE_URL}/api/payroll/employees", headers=auth_headers)
            if employees_resp.status_code == 200 and len(employees_resp.json()) > 0:
                employee_id = employees_resp.json()[0]["id"]
                create_resp = requests.post(
                    f"{BASE_URL}/api/portal/tasks",
                    headers=auth_headers,
                    json={
                        "employee_id": employee_id,
                        "title": f"TEST_Update_{uuid.uuid4().hex[:6]}",
                        "priority": "low"
                    }
                )
                task_id = create_resp.json()["id"]
            else:
                pytest.skip("No employees available to create test task")
        else:
            task_id = test_tasks[0]["id"]
        update_data = {
            "title": f"TEST_Updated_{uuid.uuid4().hex[:6]}",
            "priority": "high"
        }
        response = requests.put(
            f"{BASE_URL}/api/portal/tasks/{task_id}",
            headers=auth_headers,
            json=update_data
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Task updated successfully"
        print("Task updated successfully")

# ============== TASK WORKFLOW TESTS ==============

class TestTaskWorkflow:
    """Task status workflow tests: Assigned → In Progress → Completed → Verified"""
    
    def test_start_task(self, auth_headers):
        """POST /api/portal/tasks/{id}/start - start working on task"""
        # Get all tasks first
        tasks_resp = requests.get(f"{BASE_URL}/api/portal/tasks", headers=auth_headers)
        tasks = tasks_resp.json()
        assigned_tasks = [t for t in tasks if t["status"] == "assigned"]
        
        if len(assigned_tasks) == 0:
            # Create a new task to test workflow
            employees_resp = requests.get(f"{BASE_URL}/api/payroll/employees", headers=auth_headers)
            if employees_resp.status_code != 200 or len(employees_resp.json()) == 0:
                pytest.skip("No employees available")
            
            employee_id = employees_resp.json()[0]["id"]
            create_resp = requests.post(
                f"{BASE_URL}/api/portal/tasks",
                headers=auth_headers,
                json={
                    "employee_id": employee_id,
                    "title": f"TEST_Workflow_{uuid.uuid4().hex[:6]}",
                    "priority": "low"
                }
            )
            task_id = create_resp.json()["id"]
        else:
            task_id = assigned_tasks[0]["id"]
        
        # Start the task
        response = requests.post(
            f"{BASE_URL}/api/portal/tasks/{task_id}/start",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Task started"
        print(f"Task {task_id} started successfully")
    
    def test_complete_task(self, auth_headers):
        """POST /api/portal/tasks/{id}/complete - mark task as completed"""
        # Create and start a task first
        employees_resp = requests.get(f"{BASE_URL}/api/payroll/employees", headers=auth_headers)
        if employees_resp.status_code != 200 or len(employees_resp.json()) == 0:
            pytest.skip("No employees available")
        
        employee_id = employees_resp.json()[0]["id"]
        
        # Create task
        create_resp = requests.post(
            f"{BASE_URL}/api/portal/tasks",
            headers=auth_headers,
            json={
                "employee_id": employee_id,
                "title": f"TEST_Complete_{uuid.uuid4().hex[:6]}",
                "priority": "low"
            }
        )
        task_id = create_resp.json()["id"]
        
        # Start task
        requests.post(f"{BASE_URL}/api/portal/tasks/{task_id}/start", headers=auth_headers)
        
        # Complete task
        response = requests.post(
            f"{BASE_URL}/api/portal/tasks/{task_id}/complete",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert "completed" in response.json()["message"].lower()
        print(f"Task {task_id} completed successfully")
    
    def test_verify_task(self, auth_headers):
        """POST /api/portal/tasks/{id}/verify - manager verifies completed task"""
        # Create, start, and complete a task first
        employees_resp = requests.get(f"{BASE_URL}/api/payroll/employees", headers=auth_headers)
        if employees_resp.status_code != 200 or len(employees_resp.json()) == 0:
            pytest.skip("No employees available")
        
        employee_id = employees_resp.json()[0]["id"]
        
        # Create task
        create_resp = requests.post(
            f"{BASE_URL}/api/portal/tasks",
            headers=auth_headers,
            json={
                "employee_id": employee_id,
                "title": f"TEST_Verify_{uuid.uuid4().hex[:6]}",
                "priority": "low"
            }
        )
        task_id = create_resp.json()["id"]
        
        # Start task
        requests.post(f"{BASE_URL}/api/portal/tasks/{task_id}/start", headers=auth_headers)
        
        # Complete task
        requests.post(f"{BASE_URL}/api/portal/tasks/{task_id}/complete", headers=auth_headers)
        
        # Verify task
        response = requests.post(
            f"{BASE_URL}/api/portal/tasks/{task_id}/verify",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Task verified successfully"
        print(f"Task {task_id} verified successfully")
    
    def test_reject_task(self, auth_headers):
        """POST /api/portal/tasks/{id}/reject - manager rejects completed task"""
        # Create, start, and complete a task first
        employees_resp = requests.get(f"{BASE_URL}/api/payroll/employees", headers=auth_headers)
        if employees_resp.status_code != 200 or len(employees_resp.json()) == 0:
            pytest.skip("No employees available")
        
        employee_id = employees_resp.json()[0]["id"]
        
        # Create task
        create_resp = requests.post(
            f"{BASE_URL}/api/portal/tasks",
            headers=auth_headers,
            json={
                "employee_id": employee_id,
                "title": f"TEST_Reject_{uuid.uuid4().hex[:6]}",
                "priority": "low"
            }
        )
        task_id = create_resp.json()["id"]
        
        # Start task
        requests.post(f"{BASE_URL}/api/portal/tasks/{task_id}/start", headers=auth_headers)
        
        # Complete task
        requests.post(f"{BASE_URL}/api/portal/tasks/{task_id}/complete", headers=auth_headers)
        
        # Reject task
        response = requests.post(
            f"{BASE_URL}/api/portal/tasks/{task_id}/reject?reason=Needs%20more%20work",
            headers=auth_headers
        )
        assert response.status_code == 200
        assert "rejected" in response.json()["message"].lower()
        print(f"Task {task_id} rejected successfully")

# ============== SUBTASKS TESTS ==============

class TestSubtasks:
    """Subtask CRUD tests"""
    
    def test_add_subtask(self, auth_headers):
        """POST /api/portal/tasks/{id}/subtasks - add subtask to task"""
        # Get an existing task
        tasks_resp = requests.get(f"{BASE_URL}/api/portal/tasks", headers=auth_headers)
        tasks = tasks_resp.json()
        
        if len(tasks) == 0:
            pytest.skip("No tasks available")
        
        task_id = tasks[0]["id"]
        subtask_data = {"title": f"TEST_Subtask_{uuid.uuid4().hex[:6]}"}
        
        response = requests.post(
            f"{BASE_URL}/api/portal/tasks/{task_id}/subtasks",
            headers=auth_headers,
            json=subtask_data
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["title"] == subtask_data["title"]
        print(f"Added subtask: {data['title']}")
    
    def test_toggle_subtask_completion(self, auth_headers):
        """PUT /api/portal/tasks/{id}/subtasks/{subtask_id} - toggle subtask completion"""
        # Get a task with subtasks
        tasks_resp = requests.get(f"{BASE_URL}/api/portal/tasks", headers=auth_headers)
        tasks = tasks_resp.json()
        
        task_with_subtasks = None
        for task in tasks:
            if task.get("subtasks_total", 0) > 0:
                # Get full details to get subtask IDs
                detail = requests.get(f"{BASE_URL}/api/portal/tasks/{task['id']}", headers=auth_headers)
                if detail.status_code == 200 and len(detail.json().get("subtasks", [])) > 0:
                    task_with_subtasks = detail.json()
                    break
        
        if not task_with_subtasks:
            pytest.skip("No tasks with subtasks available")
        
        subtask = task_with_subtasks["subtasks"][0]
        new_status = not subtask["is_completed"]
        
        response = requests.put(
            f"{BASE_URL}/api/portal/tasks/{task_with_subtasks['id']}/subtasks/{subtask['id']}?is_completed={str(new_status).lower()}",
            headers=auth_headers
        )
        assert response.status_code == 200
        print(f"Toggled subtask completion to: {new_status}")

# ============== COMMENTS TESTS ==============

class TestComments:
    """Task comments tests"""
    
    def test_add_comment(self, auth_headers):
        """POST /api/portal/tasks/{id}/comments - add comment to task"""
        # Get an existing task
        tasks_resp = requests.get(f"{BASE_URL}/api/portal/tasks", headers=auth_headers)
        tasks = tasks_resp.json()
        
        if len(tasks) == 0:
            pytest.skip("No tasks available")
        
        task_id = tasks[0]["id"]
        comment_data = {"content": f"TEST comment at {uuid.uuid4().hex[:6]}"}
        
        response = requests.post(
            f"{BASE_URL}/api/portal/tasks/{task_id}/comments",
            headers=auth_headers,
            json=comment_data
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["content"] == comment_data["content"]
        assert "user_name" in data
        print(f"Added comment by: {data['user_name']}")

# ============== TIME LOGS TESTS ==============

class TestTimeLogs:
    """Time tracking tests"""
    
    def test_add_time_log(self, auth_headers):
        """POST /api/portal/tasks/{id}/time-logs - log time on task"""
        # Get an existing task
        tasks_resp = requests.get(f"{BASE_URL}/api/portal/tasks", headers=auth_headers)
        tasks = tasks_resp.json()
        
        if len(tasks) == 0:
            pytest.skip("No tasks available")
        
        task_id = tasks[0]["id"]
        time_log_data = {
            "hours": 1.5,
            "description": f"TEST time log {uuid.uuid4().hex[:6]}"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/portal/tasks/{task_id}/time-logs",
            headers=auth_headers,
            json=time_log_data
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["hours"] == time_log_data["hours"]
        print(f"Logged {data['hours']} hours")

# ============== DASHBOARD TESTS ==============

class TestMyDashboard:
    """My Dashboard API tests"""
    
    def test_get_dashboard(self, auth_headers):
        """GET /api/portal/my-dashboard - get employee dashboard data"""
        response = requests.get(
            f"{BASE_URL}/api/portal/my-dashboard",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        # Structure validation
        assert "employee" in data
        assert "tasks" in data
        assert "attendance" in data
        assert "leave" in data
        assert "recent_tasks" in data
        
        # Tasks structure
        assert "total" in data["tasks"]
        assert "assigned" in data["tasks"]
        assert "in_progress" in data["tasks"]
        assert "completed" in data["tasks"]
        assert "verified" in data["tasks"]
        
        if data["employee"]:
            print(f"Dashboard for employee: {data['employee']['name']}")
        else:
            print("Dashboard returned (no linked employee profile - expected for admin user)")

# ============== CLEANUP ==============

class TestCleanup:
    """Cleanup test data"""
    
    def test_cleanup_test_categories(self, auth_headers):
        """Delete TEST_ prefixed categories"""
        response = requests.get(
            f"{BASE_URL}/api/portal/task-categories?include_inactive=true",
            headers=auth_headers
        )
        categories = response.json()
        
        deleted = 0
        for cat in categories:
            if "TEST_" in cat.get("name", ""):
                del_resp = requests.delete(
                    f"{BASE_URL}/api/portal/task-categories/{cat['id']}",
                    headers=auth_headers
                )
                if del_resp.status_code == 200:
                    deleted += 1
        
        print(f"Cleaned up {deleted} test categories")
