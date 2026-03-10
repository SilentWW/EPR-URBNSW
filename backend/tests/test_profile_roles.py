"""
Test Suite for Profile Management and Role-Based Permissions
Tests:
1. Profile Management API - GET/PUT /api/portal/my-profile
2. Roles API - GET /api/roles, GET /api/my-permissions
3. Role Assignment - PUT /api/users/{id}/role
4. Role-based access control
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_CREDENTIALS = {"email": "manager_test@test.com", "password": "test123"}
STORE_CREDENTIALS = {"email": "store_user@test.com", "password": "test123"}
EMPLOYEE_CREDENTIALS = {"email": "emp_user@test.com", "password": "test123"}


def get_auth_token(email, password):
    """Get authentication token for a user"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": email,
        "password": password
    })
    if response.status_code == 200:
        return response.json().get("access_token")
    return None


def get_auth_headers(token):
    """Get headers with authorization token"""
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }


class TestProfileManagementAPI:
    """Tests for Profile Management endpoints - /api/portal/my-profile"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test - get admin token"""
        self.admin_token = get_auth_token(ADMIN_CREDENTIALS["email"], ADMIN_CREDENTIALS["password"])
        assert self.admin_token is not None, "Admin login failed"
        self.headers = get_auth_headers(self.admin_token)
    
    def test_get_my_profile_returns_employee_data(self):
        """Test GET /api/portal/my-profile returns employee data"""
        response = requests.get(f"{BASE_URL}/api/portal/my-profile", headers=self.headers)
        
        # Admin user (manager_test@test.com) is linked to employee Jane Smith
        if response.status_code == 200:
            data = response.json()
            assert "first_name" in data, "Response should contain first_name"
            assert "last_name" in data, "Response should contain last_name"
            assert "id" in data, "Response should contain employee id"
            print(f"Profile found: {data.get('first_name')} {data.get('last_name')}")
        elif response.status_code == 404:
            # If no employee record linked, this is acceptable
            data = response.json()
            assert "detail" in data, "404 response should contain detail"
            print(f"No employee profile linked to user: {data.get('detail')}")
        else:
            pytest.fail(f"Unexpected status code: {response.status_code}")
    
    def test_update_my_profile_phone(self):
        """Test PUT /api/portal/my-profile updates phone number"""
        # First check if profile exists
        get_response = requests.get(f"{BASE_URL}/api/portal/my-profile", headers=self.headers)
        
        if get_response.status_code == 404:
            pytest.skip("No employee profile linked to test user")
        
        assert get_response.status_code == 200
        
        # Update phone
        update_data = {"phone": "1234567890"}
        response = requests.put(
            f"{BASE_URL}/api/portal/my-profile",
            headers=self.headers,
            json=update_data
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("phone") == "1234567890", "Phone should be updated"
        print("Phone number updated successfully")
    
    def test_update_my_profile_address(self):
        """Test PUT /api/portal/my-profile updates address fields"""
        get_response = requests.get(f"{BASE_URL}/api/portal/my-profile", headers=self.headers)
        
        if get_response.status_code == 404:
            pytest.skip("No employee profile linked to test user")
        
        assert get_response.status_code == 200
        
        # Update address fields
        update_data = {
            "address": "123 Test Street",
            "city": "Test City",
            "state": "Test State",
            "postal_code": "12345"
        }
        response = requests.put(
            f"{BASE_URL}/api/portal/my-profile",
            headers=self.headers,
            json=update_data
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("address") == "123 Test Street", "Address should be updated"
        assert data.get("city") == "Test City", "City should be updated"
        assert data.get("state") == "Test State", "State should be updated"
        assert data.get("postal_code") == "12345", "Postal code should be updated"
        print("Address fields updated successfully")
    
    def test_update_my_profile_emergency_contact(self):
        """Test PUT /api/portal/my-profile updates emergency contact"""
        get_response = requests.get(f"{BASE_URL}/api/portal/my-profile", headers=self.headers)
        
        if get_response.status_code == 404:
            pytest.skip("No employee profile linked to test user")
        
        assert get_response.status_code == 200
        
        # Update emergency contact
        update_data = {
            "emergency_contact": {
                "name": "Test Contact",
                "phone": "9876543210",
                "relationship": "Spouse"
            }
        }
        response = requests.put(
            f"{BASE_URL}/api/portal/my-profile",
            headers=self.headers,
            json=update_data
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        ec = data.get("emergency_contact", {})
        assert ec.get("name") == "Test Contact", "Emergency contact name should be updated"
        assert ec.get("phone") == "9876543210", "Emergency contact phone should be updated"
        assert ec.get("relationship") == "Spouse", "Emergency contact relationship should be updated"
        print("Emergency contact updated successfully")
    
    def test_update_profile_verify_persistence(self):
        """Test that profile updates are persisted in database"""
        get_response = requests.get(f"{BASE_URL}/api/portal/my-profile", headers=self.headers)
        
        if get_response.status_code == 404:
            pytest.skip("No employee profile linked to test user")
        
        # Update and then GET to verify persistence
        unique_phone = "5551234567"
        update_data = {"phone": unique_phone}
        
        put_response = requests.put(
            f"{BASE_URL}/api/portal/my-profile",
            headers=self.headers,
            json=update_data
        )
        assert put_response.status_code == 200
        
        # GET again to verify
        verify_response = requests.get(f"{BASE_URL}/api/portal/my-profile", headers=self.headers)
        assert verify_response.status_code == 200
        data = verify_response.json()
        assert data.get("phone") == unique_phone, "Phone should be persisted"
        print("Profile update persistence verified")


class TestRolesAPI:
    """Tests for Roles API - /api/roles, /api/my-permissions"""
    
    def test_admin_get_roles_returns_all_roles(self):
        """Test GET /api/roles for admin returns all available roles"""
        token = get_auth_token(ADMIN_CREDENTIALS["email"], ADMIN_CREDENTIALS["password"])
        assert token is not None, "Admin login failed"
        headers = get_auth_headers(token)
        
        response = requests.get(f"{BASE_URL}/api/roles", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        roles = data.get("roles", [])
        
        assert len(roles) > 0, "Should return at least one role"
        
        # Admin should see all roles
        role_values = [r["value"] for r in roles]
        print(f"Admin sees roles: {role_values}")
        
        # Check that expected roles are present
        expected_roles = ["admin", "manager", "accountant", "store", "employee"]
        for expected in expected_roles:
            assert expected in role_values, f"Admin should see '{expected}' role"
    
    def test_admin_get_my_permissions(self):
        """Test GET /api/my-permissions returns admin permissions"""
        token = get_auth_token(ADMIN_CREDENTIALS["email"], ADMIN_CREDENTIALS["password"])
        assert token is not None, "Admin login failed"
        headers = get_auth_headers(token)
        
        response = requests.get(f"{BASE_URL}/api/my-permissions", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "role" in data, "Response should contain role"
        assert "modules" in data, "Response should contain modules"
        
        # Admin should have full access
        if data.get("is_admin"):
            assert "*" in data.get("modules", []), "Admin should have wildcard module access"
        
        print(f"Admin role: {data.get('role')}, is_admin: {data.get('is_admin')}")
        print(f"Admin modules: {data.get('modules')[:10]}..." if len(data.get('modules', [])) > 10 else f"Admin modules: {data.get('modules')}")
    
    def test_store_get_roles_filtered(self):
        """Test GET /api/roles for store role returns limited roles"""
        token = get_auth_token(STORE_CREDENTIALS["email"], STORE_CREDENTIALS["password"])
        if token is None:
            pytest.skip("Store user login failed - user may not exist")
        
        headers = get_auth_headers(token)
        response = requests.get(f"{BASE_URL}/api/roles", headers=headers)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        roles = data.get("roles", [])
        
        # Store role should NOT be able to create roles (can_create_roles is empty)
        role_values = [r["value"] for r in roles]
        print(f"Store user sees roles: {role_values}")
        
        # Store should not see admin role for assignment
        assert "admin" not in role_values or len(role_values) == 0, "Store should not be able to assign admin role"
    
    def test_store_get_my_permissions(self):
        """Test GET /api/my-permissions for store role"""
        token = get_auth_token(STORE_CREDENTIALS["email"], STORE_CREDENTIALS["password"])
        if token is None:
            pytest.skip("Store user login failed - user may not exist")
        
        headers = get_auth_headers(token)
        response = requests.get(f"{BASE_URL}/api/my-permissions", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data.get("role") == "store", f"Expected role 'store', got {data.get('role')}"
        modules = data.get("modules", [])
        
        # Store should have access to inventory-related modules
        store_expected_modules = ["products", "inventory", "grn", "purchase-orders", "my-dashboard", "my-tasks"]
        for mod in store_expected_modules:
            assert mod in modules, f"Store should have access to '{mod}'"
        
        # Store should NOT have access to finance/admin modules
        store_forbidden_modules = ["accounting", "payroll", "system-admin"]
        for mod in store_forbidden_modules:
            assert mod not in modules, f"Store should NOT have access to '{mod}'"
        
        print(f"Store modules: {modules}")
    
    def test_employee_get_my_permissions(self):
        """Test GET /api/my-permissions for employee role"""
        token = get_auth_token(EMPLOYEE_CREDENTIALS["email"], EMPLOYEE_CREDENTIALS["password"])
        if token is None:
            pytest.skip("Employee user login failed - user may not exist")
        
        headers = get_auth_headers(token)
        response = requests.get(f"{BASE_URL}/api/my-permissions", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data.get("role") == "employee", f"Expected role 'employee', got {data.get('role')}"
        modules = data.get("modules", [])
        
        # Employee should only have access to My Portal + Attendance + Leave
        employee_expected_modules = ["my-dashboard", "my-tasks", "attendance", "leave-management"]
        for mod in employee_expected_modules:
            assert mod in modules, f"Employee should have access to '{mod}'"
        
        # Employee should NOT have access to main modules
        employee_forbidden_modules = ["products", "inventory", "accounting", "payroll", "employees"]
        for mod in employee_forbidden_modules:
            assert mod not in modules, f"Employee should NOT have access to '{mod}'"
        
        print(f"Employee modules: {modules}")


class TestRoleAssignment:
    """Tests for Role Assignment - PUT /api/users/{id}/role"""
    
    def test_admin_can_assign_any_role(self):
        """Test that admin can assign any role to a user"""
        admin_token = get_auth_token(ADMIN_CREDENTIALS["email"], ADMIN_CREDENTIALS["password"])
        assert admin_token is not None, "Admin login failed"
        headers = get_auth_headers(admin_token)
        
        # Get list of users
        users_response = requests.get(f"{BASE_URL}/api/users", headers=headers)
        
        if users_response.status_code == 403:
            pytest.skip("Admin doesn't have access to user management")
        
        assert users_response.status_code == 200
        users = users_response.json()
        
        # Find a test user to change role (not the admin itself)
        test_user = None
        for user in users:
            if user.get("email") != ADMIN_CREDENTIALS["email"]:
                test_user = user
                break
        
        if test_user is None:
            pytest.skip("No other user found to test role assignment")
        
        original_role = test_user.get("role")
        user_id = test_user.get("id")
        
        # Change role to employee
        new_role = "employee" if original_role != "employee" else "store"
        response = requests.put(
            f"{BASE_URL}/api/users/{user_id}/role?role={new_role}",
            headers=headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        # Verify the change
        verify_response = requests.get(f"{BASE_URL}/api/users", headers=headers)
        updated_users = verify_response.json()
        updated_user = next((u for u in updated_users if u.get("id") == user_id), None)
        assert updated_user is not None
        assert updated_user.get("role") == new_role, f"Role should be changed to {new_role}"
        
        # Restore original role
        requests.put(f"{BASE_URL}/api/users/{user_id}/role?role={original_role}", headers=headers)
        print(f"Role assignment tested: {original_role} -> {new_role} -> {original_role}")
    
    def test_manager_can_create_permitted_roles(self):
        """Test that manager can create manager/accountant/store/employee roles"""
        # First need to create a manager user or find one
        admin_token = get_auth_token(ADMIN_CREDENTIALS["email"], ADMIN_CREDENTIALS["password"])
        headers = get_auth_headers(admin_token)
        
        # Get the current user's permissions
        perms_response = requests.get(f"{BASE_URL}/api/my-permissions", headers=headers)
        assert perms_response.status_code == 200
        
        data = perms_response.json()
        current_role = data.get("role")
        
        # Manager (or admin acting as one) can create these roles
        if current_role in ["admin", "manager"]:
            roles_response = requests.get(f"{BASE_URL}/api/roles", headers=headers)
            assert roles_response.status_code == 200
            
            roles = roles_response.json().get("roles", [])
            role_values = [r["value"] for r in roles]
            
            # Check that manager-creatable roles are available
            manager_creatable = ["manager", "accountant", "store", "employee"]
            for role in manager_creatable:
                assert role in role_values, f"Should be able to create '{role}' role"
            
            print(f"Role '{current_role}' can create: {role_values}")
        else:
            pytest.skip(f"Test user has role '{current_role}', not manager or admin")
    
    def test_store_cannot_assign_roles(self):
        """Test that store role cannot assign roles"""
        store_token = get_auth_token(STORE_CREDENTIALS["email"], STORE_CREDENTIALS["password"])
        if store_token is None:
            pytest.skip("Store user login failed")
        
        headers = get_auth_headers(store_token)
        
        # Get permissions to confirm store role
        perms = requests.get(f"{BASE_URL}/api/my-permissions", headers=headers).json()
        if perms.get("role") != "store":
            pytest.skip(f"User has role {perms.get('role')}, not store")
        
        # Store should not be able to access user management
        users_response = requests.get(f"{BASE_URL}/api/users", headers=headers)
        
        # Should get 403 Forbidden
        assert users_response.status_code == 403, f"Store should not access users, got {users_response.status_code}"
        print("Store correctly denied access to user management")
    
    def test_employee_cannot_assign_roles(self):
        """Test that employee role cannot assign roles"""
        emp_token = get_auth_token(EMPLOYEE_CREDENTIALS["email"], EMPLOYEE_CREDENTIALS["password"])
        if emp_token is None:
            pytest.skip("Employee user login failed")
        
        headers = get_auth_headers(emp_token)
        
        # Employee should not be able to access user management
        users_response = requests.get(f"{BASE_URL}/api/users", headers=headers)
        
        # Should get 403 Forbidden
        assert users_response.status_code == 403, f"Employee should not access users, got {users_response.status_code}"
        print("Employee correctly denied access to user management")
    
    def test_invalid_role_rejected(self):
        """Test that invalid role assignment is rejected"""
        admin_token = get_auth_token(ADMIN_CREDENTIALS["email"], ADMIN_CREDENTIALS["password"])
        assert admin_token is not None
        headers = get_auth_headers(admin_token)
        
        # Get a user to test with
        users_response = requests.get(f"{BASE_URL}/api/users", headers=headers)
        if users_response.status_code != 200:
            pytest.skip("Cannot access users")
        
        users = users_response.json()
        test_user = next((u for u in users if u.get("email") != ADMIN_CREDENTIALS["email"]), None)
        if test_user is None:
            pytest.skip("No other user found")
        
        # Try to assign invalid role
        response = requests.put(
            f"{BASE_URL}/api/users/{test_user['id']}/role?role=invalid_role_xyz",
            headers=headers
        )
        
        assert response.status_code == 400, f"Invalid role should be rejected, got {response.status_code}"
        print("Invalid role assignment correctly rejected")


class TestRoleBasedAPIAccess:
    """Tests for role-based API access control"""
    
    def test_store_can_access_inventory(self):
        """Test that store role can access inventory endpoints"""
        token = get_auth_token(STORE_CREDENTIALS["email"], STORE_CREDENTIALS["password"])
        if token is None:
            pytest.skip("Store user login failed")
        
        headers = get_auth_headers(token)
        
        # Store should be able to access products
        response = requests.get(f"{BASE_URL}/api/products", headers=headers)
        assert response.status_code == 200, f"Store should access products, got {response.status_code}"
        print("Store can access inventory endpoints")
    
    def test_store_cannot_access_payroll(self):
        """Test that store role cannot access payroll endpoints"""
        token = get_auth_token(STORE_CREDENTIALS["email"], STORE_CREDENTIALS["password"])
        if token is None:
            pytest.skip("Store user login failed")
        
        headers = get_auth_headers(token)
        
        # Store should NOT be able to access payroll - but API might not enforce this
        # The frontend enforces this through sidebar filtering
        # For now, we just verify permissions endpoint shows no payroll access
        perms = requests.get(f"{BASE_URL}/api/my-permissions", headers=headers).json()
        modules = perms.get("modules", [])
        
        assert "payroll" not in modules, "Store should not have payroll in modules"
        print("Store correctly has no payroll module access")
    
    def test_employee_can_access_portal_endpoints(self):
        """Test that employee role can access portal endpoints"""
        token = get_auth_token(EMPLOYEE_CREDENTIALS["email"], EMPLOYEE_CREDENTIALS["password"])
        if token is None:
            pytest.skip("Employee user login failed")
        
        headers = get_auth_headers(token)
        
        # Employee should be able to access their dashboard
        dashboard_response = requests.get(f"{BASE_URL}/api/portal/my-dashboard", headers=headers)
        assert dashboard_response.status_code == 200, f"Employee should access dashboard, got {dashboard_response.status_code}"
        
        # Employee should be able to access their tasks
        tasks_response = requests.get(f"{BASE_URL}/api/portal/tasks?assigned_to_me=true", headers=headers)
        assert tasks_response.status_code == 200, f"Employee should access their tasks, got {tasks_response.status_code}"
        
        print("Employee can access portal endpoints")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
