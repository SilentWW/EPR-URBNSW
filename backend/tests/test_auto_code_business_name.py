"""
Test Suite for Auto-Generate Account Codes and Dynamic Business Name Features

Features being tested:
1. Auto-generate account codes when adding new accounts in Chart of Accounts
2. GET /api/finance/chart-of-accounts/next-code/{account_type} returns correct next code
3. POST /api/finance/chart-of-accounts with no code field auto-generates code
4. Different account types generate correct code prefixes (Asset=1xxx, Liability=2xxx, Equity=3xxx, Income=4xxx, Expense=6xxx)
5. GET /api/auth/me returns company_name
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestSetup:
    """Setup tests - verify API is accessible"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@demo.com",
            "password": "password123"
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")
        
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Headers with auth token"""
        return {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }


class TestDynamicBusinessName:
    """Test dynamic business name feature - /api/auth/me returns company_name"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@demo.com",
            "password": "password123"
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Headers with auth token"""
        return {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
    
    def test_auth_me_returns_company_name(self, auth_headers):
        """Test that /api/auth/me returns company_name field"""
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "company_name" in data, "company_name field should be in /api/auth/me response"
        assert data["company_name"] is not None, "company_name should not be None"
        assert isinstance(data["company_name"], str), "company_name should be a string"
        assert len(data["company_name"]) > 0, "company_name should not be empty"
        print(f"✓ Company name returned: {data['company_name']}")
    
    def test_auth_me_company_name_matches_expected(self, auth_headers):
        """Test that company_name matches expected value 'My Test Company'"""
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        # The test user should have company_name "My Test Company" as per review_request
        assert data["company_name"] == "My Test Company", f"Expected 'My Test Company', got '{data['company_name']}'"
        print(f"✓ Company name matches expected: {data['company_name']}")


class TestNextCodeEndpoint:
    """Test GET /api/finance/chart-of-accounts/next-code/{account_type} endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@demo.com",
            "password": "password123"
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Headers with auth token"""
        return {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
    
    def test_next_code_asset(self, auth_headers):
        """Test next code for asset type (prefix: 1xxx)"""
        response = requests.get(f"{BASE_URL}/api/finance/chart-of-accounts/next-code/asset", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "next_code" in data, "Response should contain next_code field"
        next_code = data["next_code"]
        assert next_code.startswith("1"), f"Asset code should start with 1, got {next_code}"
        print(f"✓ Next asset code: {next_code}")
    
    def test_next_code_liability(self, auth_headers):
        """Test next code for liability type (prefix: 2xxx)"""
        response = requests.get(f"{BASE_URL}/api/finance/chart-of-accounts/next-code/liability", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "next_code" in data, "Response should contain next_code field"
        next_code = data["next_code"]
        assert next_code.startswith("2"), f"Liability code should start with 2, got {next_code}"
        print(f"✓ Next liability code: {next_code}")
    
    def test_next_code_equity(self, auth_headers):
        """Test next code for equity type (prefix: 3xxx)"""
        response = requests.get(f"{BASE_URL}/api/finance/chart-of-accounts/next-code/equity", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "next_code" in data, "Response should contain next_code field"
        next_code = data["next_code"]
        assert next_code.startswith("3"), f"Equity code should start with 3, got {next_code}"
        print(f"✓ Next equity code: {next_code}")
    
    def test_next_code_income(self, auth_headers):
        """Test next code for income type (prefix: 4xxx)"""
        response = requests.get(f"{BASE_URL}/api/finance/chart-of-accounts/next-code/income", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "next_code" in data, "Response should contain next_code field"
        next_code = data["next_code"]
        assert next_code.startswith("4"), f"Income code should start with 4, got {next_code}"
        print(f"✓ Next income code: {next_code}")
    
    def test_next_code_expense(self, auth_headers):
        """Test next code for expense type (prefix: 6xxx)"""
        response = requests.get(f"{BASE_URL}/api/finance/chart-of-accounts/next-code/expense", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "next_code" in data, "Response should contain next_code field"
        next_code = data["next_code"]
        assert next_code.startswith("6"), f"Expense code should start with 6, got {next_code}"
        print(f"✓ Next expense code: {next_code}")
    
    def test_next_code_invalid_type(self, auth_headers):
        """Test next code for invalid account type returns 400"""
        response = requests.get(f"{BASE_URL}/api/finance/chart-of-accounts/next-code/invalid", headers=auth_headers)
        assert response.status_code == 400, f"Expected 400 for invalid type, got {response.status_code}"
        print(f"✓ Invalid account type correctly returns 400")


class TestAutoGenerateAccountCode:
    """Test auto-generate account code when creating accounts"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@demo.com",
            "password": "password123"
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Headers with auth token"""
        return {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
    
    def test_create_expense_account_auto_code(self, auth_headers):
        """Test creating expense account without code auto-generates code"""
        # Get the expected next code first
        next_code_response = requests.get(
            f"{BASE_URL}/api/finance/chart-of-accounts/next-code/expense", 
            headers=auth_headers
        )
        expected_code = next_code_response.json()["next_code"]
        
        # Create account without providing code
        account_data = {
            "name": "TEST Auto Code Expense Account",
            "account_type": "expense",
            "category": "operating_expense",
            "description": "Test account for auto code generation"
            # NOTE: No 'code' field provided - should be auto-generated
        }
        
        response = requests.post(
            f"{BASE_URL}/api/finance/chart-of-accounts",
            json=account_data,
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        created_account = response.json()
        assert "code" in created_account, "Created account should have code field"
        assert created_account["code"] == expected_code, f"Expected code {expected_code}, got {created_account['code']}"
        assert created_account["code"].startswith("6"), "Expense code should start with 6"
        print(f"✓ Auto-generated expense account code: {created_account['code']}")
        
        # Cleanup - delete the test account
        if created_account.get("id"):
            requests.delete(
                f"{BASE_URL}/api/finance/chart-of-accounts/{created_account['id']}",
                headers=auth_headers
            )
    
    def test_create_asset_account_auto_code(self, auth_headers):
        """Test creating asset account without code auto-generates code"""
        # Get the expected next code first
        next_code_response = requests.get(
            f"{BASE_URL}/api/finance/chart-of-accounts/next-code/asset", 
            headers=auth_headers
        )
        expected_code = next_code_response.json()["next_code"]
        
        # Create account without providing code
        account_data = {
            "name": "TEST Auto Code Asset Account",
            "account_type": "asset",
            "category": "current_asset",
            "description": "Test account for auto code generation"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/finance/chart-of-accounts",
            json=account_data,
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        created_account = response.json()
        assert created_account["code"] == expected_code, f"Expected code {expected_code}, got {created_account['code']}"
        assert created_account["code"].startswith("1"), "Asset code should start with 1"
        print(f"✓ Auto-generated asset account code: {created_account['code']}")
        
        # Cleanup
        if created_account.get("id"):
            requests.delete(
                f"{BASE_URL}/api/finance/chart-of-accounts/{created_account['id']}",
                headers=auth_headers
            )
    
    def test_create_account_with_empty_code_generates_code(self, auth_headers):
        """Test creating account with empty string code auto-generates code"""
        account_data = {
            "code": "",  # Empty code should trigger auto-generation
            "name": "TEST Empty Code Account",
            "account_type": "income",
            "category": "revenue",
            "description": "Test with empty code"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/finance/chart-of-accounts",
            json=account_data,
            headers=auth_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        created_account = response.json()
        assert created_account["code"], "Code should be auto-generated"
        assert created_account["code"].startswith("4"), "Income code should start with 4"
        print(f"✓ Auto-generated income account code (from empty): {created_account['code']}")
        
        # Cleanup
        if created_account.get("id"):
            requests.delete(
                f"{BASE_URL}/api/finance/chart-of-accounts/{created_account['id']}",
                headers=auth_headers
            )
    
    def test_sequential_code_generation(self, auth_headers):
        """Test that sequential account creation generates sequential codes"""
        # Create first account
        account1_data = {
            "name": "TEST Sequential Account 1",
            "account_type": "expense",
            "category": "operating_expense"
        }
        response1 = requests.post(
            f"{BASE_URL}/api/finance/chart-of-accounts",
            json=account1_data,
            headers=auth_headers
        )
        assert response1.status_code == 200
        account1 = response1.json()
        code1 = int(account1["code"])
        
        # Create second account
        account2_data = {
            "name": "TEST Sequential Account 2",
            "account_type": "expense",
            "category": "operating_expense"
        }
        response2 = requests.post(
            f"{BASE_URL}/api/finance/chart-of-accounts",
            json=account2_data,
            headers=auth_headers
        )
        assert response2.status_code == 200
        account2 = response2.json()
        code2 = int(account2["code"])
        
        # Second code should be exactly one more than first
        assert code2 == code1 + 1, f"Expected sequential codes, got {code1} and {code2}"
        print(f"✓ Sequential codes verified: {code1} -> {code2}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/finance/chart-of-accounts/{account1['id']}", headers=auth_headers)
        requests.delete(f"{BASE_URL}/api/finance/chart-of-accounts/{account2['id']}", headers=auth_headers)


class TestAccountCodePrefixes:
    """Test that different account types generate correct prefixes"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@demo.com",
            "password": "password123"
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip(f"Authentication failed: {response.status_code} - {response.text}")
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Headers with auth token"""
        return {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
    
    def test_all_prefix_types(self, auth_headers):
        """Test all account type prefixes in one test"""
        # Expected prefixes: Asset=1, Liability=2, Equity=3, Income=4, Expense=6
        test_cases = [
            ("asset", "1", "current_asset"),
            ("liability", "2", "current_liability"),
            ("equity", "3", "capital"),
            ("income", "4", "revenue"),
            ("expense", "6", "operating_expense")
        ]
        
        created_accounts = []
        
        for account_type, expected_prefix, category in test_cases:
            response = requests.get(
                f"{BASE_URL}/api/finance/chart-of-accounts/next-code/{account_type}",
                headers=auth_headers
            )
            assert response.status_code == 200, f"Failed to get next code for {account_type}"
            
            next_code = response.json()["next_code"]
            assert next_code.startswith(expected_prefix), \
                f"{account_type} code should start with {expected_prefix}, got {next_code}"
            print(f"✓ {account_type.capitalize()} prefix verified: {next_code}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
