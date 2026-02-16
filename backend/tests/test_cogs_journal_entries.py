"""
Test Suite for COGS (Cost of Goods Sold) Recognition and Journal Entries
Tests the following features:
1. Sales Order creation creates proper journal entries
2. Sales Revenue journal entry (Debit AR 1300, Credit Revenue 4100)
3. COGS journal entry (Debit COGS 5000/5100, Credit Inventory 1400)
4. Sales Return reverses both Revenue and COGS entries
5. Auto-generate Account Codes in Chart of Accounts
6. Dynamic Business Name in sidebar (verified by API)
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test data prefix for cleanup
TEST_PREFIX = "TEST_COGS_"

class TestAuthentication:
    """Authentication tests"""
    
    @pytest.fixture(scope="class")
    def session(self):
        return requests.Session()
    
    def test_login_success(self, session):
        """Test login with test credentials"""
        response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@demo.com",
            "password": "password123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == "test@demo.com"
        
        # Store token for subsequent tests
        session.headers.update({"Authorization": f"Bearer {data['access_token']}"})
        return data
    
    def test_get_current_user_with_company_name(self, session):
        """Test that /auth/me returns company_name for dynamic sidebar"""
        # First ensure we're logged in
        login_response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@demo.com",
            "password": "password123"
        })
        token = login_response.json()["access_token"]
        session.headers.update({"Authorization": f"Bearer {token}"})
        
        response = session.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 200
        
        data = response.json()
        assert "company_name" in data, "company_name field should be present for dynamic sidebar"
        print(f"Company name for sidebar: {data.get('company_name')}")


class TestChartOfAccountsAutoCode:
    """Test auto-generation of account codes in Chart of Accounts"""
    
    @pytest.fixture(scope="class")
    def auth_session(self):
        session = requests.Session()
        login_response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@demo.com",
            "password": "password123"
        })
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        session.headers.update({"Authorization": f"Bearer {token}"})
        return session
    
    def test_get_chart_of_accounts(self, auth_session):
        """Test fetching chart of accounts"""
        response = auth_session.get(f"{BASE_URL}/api/finance/chart-of-accounts")
        assert response.status_code == 200
        
        accounts = response.json()
        print(f"Found {len(accounts)} accounts in Chart of Accounts")
        
        # Check for essential accounts needed for COGS
        account_codes = [acc.get("code") for acc in accounts]
        print(f"Account codes: {account_codes[:15]}...")  # Show first 15
        
        # Verify essential accounts exist
        essential_codes = ["1300", "4100"]  # AR and Revenue
        for code in essential_codes:
            assert code in account_codes, f"Essential account {code} not found"
    
    def test_auto_generate_code_for_asset(self, auth_session):
        """Test auto-generating account code for asset type"""
        response = auth_session.get(f"{BASE_URL}/api/finance/chart-of-accounts/next-code/asset")
        assert response.status_code == 200
        
        data = response.json()
        assert "next_code" in data
        next_code = data["next_code"]
        print(f"Next asset account code: {next_code}")
        
        # Asset codes should start with 1
        assert next_code.startswith("1"), f"Asset code should start with 1, got {next_code}"
    
    def test_auto_generate_code_for_expense(self, auth_session):
        """Test auto-generating account code for expense type (for COGS)"""
        response = auth_session.get(f"{BASE_URL}/api/finance/chart-of-accounts/next-code/expense")
        assert response.status_code == 200
        
        data = response.json()
        assert "next_code" in data
        next_code = data["next_code"]
        print(f"Next expense account code: {next_code}")
        
        # Expense codes should start with 5 or 6 (5xxx for COGS, 6xxx for operating expenses)
        assert next_code.startswith("5") or next_code.startswith("6"), f"Expense code should start with 5 or 6, got {next_code}"
    
    def test_auto_generate_code_for_income(self, auth_session):
        """Test auto-generating account code for income type (for revenue)"""
        response = auth_session.get(f"{BASE_URL}/api/finance/chart-of-accounts/next-code/income")
        assert response.status_code == 200
        
        data = response.json()
        assert "next_code" in data
        next_code = data["next_code"]
        print(f"Next income account code: {next_code}")
        
        # Income codes should start with 4
        assert next_code.startswith("4"), f"Income code should start with 4, got {next_code}"
    
    def test_create_account_with_auto_code(self, auth_session):
        """Test creating an account with auto-generated code"""
        # Get next code first
        next_code_resp = auth_session.get(f"{BASE_URL}/api/finance/chart-of-accounts/next-code/expense")
        next_code = next_code_resp.json()["next_code"]
        
        # Create account with the auto-generated code
        response = auth_session.post(f"{BASE_URL}/api/finance/chart-of-accounts", json={
            "code": next_code,
            "name": f"{TEST_PREFIX}Test Expense Account",
            "account_type": "expense",
            "category": "operating_expense",
            "description": "Test account for auto-code generation",
            "opening_balance": 0
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == next_code
        print(f"Created account with auto-generated code: {next_code}")


class TestCOGSJournalEntries:
    """Test COGS recognition when sales orders are created"""
    
    @pytest.fixture(scope="class")
    def auth_session(self):
        session = requests.Session()
        login_response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@demo.com",
            "password": "password123"
        })
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        session.headers.update({"Authorization": f"Bearer {token}"})
        return session
    
    @pytest.fixture(scope="class")
    def test_customer(self, auth_session):
        """Create or get a test customer"""
        # Try to create a test customer
        response = auth_session.post(f"{BASE_URL}/api/customers", json={
            "name": f"{TEST_PREFIX}Customer",
            "email": f"test_cogs_{uuid.uuid4().hex[:6]}@test.com",
            "phone": "+94771234567",
            "address": "Test Address"
        })
        
        if response.status_code == 200:
            return response.json()
        
        # If creation failed, get existing customers
        customers_resp = auth_session.get(f"{BASE_URL}/api/customers")
        customers = customers_resp.json()
        if customers:
            return customers[0]
        
        pytest.skip("No customer available for testing")
    
    @pytest.fixture(scope="class")
    def test_product_with_cost(self, auth_session):
        """Create or get a product with cost_price set for COGS testing"""
        # Create a test product with cost_price
        response = auth_session.post(f"{BASE_URL}/api/products", json={
            "name": f"{TEST_PREFIX}Product With Cost",
            "sku": f"COGS-{uuid.uuid4().hex[:6]}",
            "cost_price": 5000.00,  # Cost price for COGS
            "regular_price": 8000.00,
            "selling_price": 8000.00,
            "stock_quantity": 100,
            "category": "Electronics"
        })
        
        if response.status_code == 200:
            product = response.json()
            print(f"Created test product: {product.get('name')} with cost_price: {product.get('cost_price')}")
            return product
        
        # If creation failed, try to get existing products with cost_price
        products_resp = auth_session.get(f"{BASE_URL}/api/products")
        products = products_resp.json()
        products_with_cost = [p for p in products if p.get("cost_price", 0) > 0]
        
        if products_with_cost:
            return products_with_cost[0]
        
        pytest.skip("No product with cost_price available for COGS testing")
    
    def test_create_sales_order_creates_revenue_journal_entry(self, auth_session, test_customer, test_product_with_cost):
        """Test that creating a sales order creates a revenue journal entry (Debit AR, Credit Revenue)"""
        # Get initial journal entry count
        initial_entries_resp = auth_session.get(f"{BASE_URL}/api/finance/journal-entries?limit=100")
        initial_count = len(initial_entries_resp.json()) if initial_entries_resp.status_code == 200 else 0
        
        # Create sales order
        unit_price = test_product_with_cost.get("selling_price", 8000)
        quantity = 2
        total = unit_price * quantity
        
        sales_order_data = {
            "customer_id": test_customer["id"],
            "items": [{
                "product_id": test_product_with_cost["id"],
                "product_name": test_product_with_cost["name"],
                "sku": test_product_with_cost.get("sku", "TEST-SKU"),
                "quantity": quantity,
                "unit_price": unit_price,
                "total": total
            }],
            "discount": 0,
            "notes": f"{TEST_PREFIX}Sales Order for COGS testing"
        }
        
        response = auth_session.post(f"{BASE_URL}/api/sales-orders", json=sales_order_data)
        assert response.status_code == 200, f"Failed to create sales order: {response.text}"
        
        sales_order = response.json()
        order_id = sales_order["id"]
        order_number = sales_order.get("order_number", "")
        print(f"Created sales order: {order_number} (ID: {order_id})")
        
        # Verify journal entries were created
        entries_resp = auth_session.get(f"{BASE_URL}/api/finance/journal-entries?limit=100")
        assert entries_resp.status_code == 200
        
        entries = entries_resp.json()
        
        # Find revenue journal entry for this order
        revenue_entries = [e for e in entries if e.get("reference_id") == order_id and "Sales Revenue" in e.get("description", "")]
        
        assert len(revenue_entries) >= 1, f"Revenue journal entry not found for order {order_id}"
        
        revenue_entry = revenue_entries[0]
        print(f"Revenue entry: {revenue_entry.get('description')}")
        
        # Verify the entry has correct structure (Debit AR, Credit Revenue)
        lines = revenue_entry.get("lines", [])
        assert len(lines) >= 2, "Revenue entry should have at least 2 lines"
        
        # Check for AR debit (1300) and Revenue credit (4100)
        ar_debit = None
        revenue_credit = None
        
        for line in lines:
            account_code = line.get("account_code", "")
            if account_code == "1300" and line.get("debit", 0) > 0:
                ar_debit = line
            if account_code == "4100" and line.get("credit", 0) > 0:
                revenue_credit = line
        
        assert ar_debit is not None, "Accounts Receivable (1300) debit not found"
        assert revenue_credit is not None, "Sales Revenue (4100) credit not found"
        
        print(f"AR Debit (1300): {ar_debit.get('debit')}")
        print(f"Revenue Credit (4100): {revenue_credit.get('credit')}")
        
        # Verify amounts match
        assert ar_debit.get("debit") == total, f"AR debit should be {total}"
        assert revenue_credit.get("credit") == total, f"Revenue credit should be {total}"
        
        # Verify entry is balanced
        assert revenue_entry.get("is_balanced") == True, "Revenue entry should be balanced"
        
        return sales_order
    
    def test_create_sales_order_creates_cogs_journal_entry(self, auth_session, test_customer, test_product_with_cost):
        """Test that creating a sales order creates a COGS journal entry (Debit COGS, Credit Inventory)"""
        # Create sales order
        cost_price = test_product_with_cost.get("cost_price", 5000)
        selling_price = test_product_with_cost.get("selling_price", 8000)
        quantity = 3
        total_cogs = cost_price * quantity
        
        sales_order_data = {
            "customer_id": test_customer["id"],
            "items": [{
                "product_id": test_product_with_cost["id"],
                "product_name": test_product_with_cost["name"],
                "sku": test_product_with_cost.get("sku", "TEST-SKU"),
                "quantity": quantity,
                "unit_price": selling_price,
                "total": selling_price * quantity
            }],
            "discount": 0,
            "notes": f"{TEST_PREFIX}Sales Order for COGS entry testing"
        }
        
        response = auth_session.post(f"{BASE_URL}/api/sales-orders", json=sales_order_data)
        assert response.status_code == 200, f"Failed to create sales order: {response.text}"
        
        sales_order = response.json()
        order_id = sales_order["id"]
        order_number = sales_order.get("order_number", "")
        print(f"Created sales order: {order_number} for COGS testing")
        
        # Wait a moment for journal entries to be created
        import time
        time.sleep(0.5)
        
        # Verify COGS journal entry was created
        entries_resp = auth_session.get(f"{BASE_URL}/api/finance/journal-entries?limit=100")
        assert entries_resp.status_code == 200
        
        entries = entries_resp.json()
        
        # Find COGS journal entry for this order (description uses "Cost of Goods Sold")
        cogs_entries = [e for e in entries if e.get("reference_id") == order_id and "Cost of Goods Sold" in e.get("description", "")]
        
        assert len(cogs_entries) >= 1, f"COGS journal entry not found for order {order_id}. Entries with this order_id: {[e.get('description') for e in entries if e.get('reference_id') == order_id]}"
        
        cogs_entry = cogs_entries[0]
        print(f"COGS entry: {cogs_entry.get('description')}")
        
        # Verify the entry has correct structure (Debit COGS 5000/5100, Credit Inventory 1400)
        lines = cogs_entry.get("lines", [])
        assert len(lines) >= 2, "COGS entry should have at least 2 lines"
        
        # Check for COGS debit (5000 or 5100) and Inventory credit (1400)
        cogs_debit = None
        inventory_credit = None
        
        for line in lines:
            account_code = line.get("account_code", "")
            if account_code in ["5000", "5100"] and line.get("debit", 0) > 0:
                cogs_debit = line
            if account_code == "1400" and line.get("credit", 0) > 0:
                inventory_credit = line
        
        assert cogs_debit is not None, f"COGS account (5000/5100) debit not found. Lines: {lines}"
        assert inventory_credit is not None, f"Inventory (1400) credit not found. Lines: {lines}"
        
        print(f"COGS Debit ({cogs_debit.get('account_code')}): {cogs_debit.get('debit')}")
        print(f"Inventory Credit (1400): {inventory_credit.get('credit')}")
        
        # Verify amounts match expected COGS
        assert cogs_debit.get("debit") == total_cogs, f"COGS debit should be {total_cogs}, got {cogs_debit.get('debit')}"
        assert inventory_credit.get("credit") == total_cogs, f"Inventory credit should be {total_cogs}, got {inventory_credit.get('credit')}"
        
        # Verify entry is balanced
        assert cogs_entry.get("is_balanced") == True, "COGS entry should be balanced"
        
        return sales_order
    
    def test_sales_return_reverses_revenue_entry(self, auth_session, test_customer, test_product_with_cost):
        """Test that returning a sales order reverses the revenue journal entry"""
        # Create a sales order first
        selling_price = test_product_with_cost.get("selling_price", 8000)
        quantity = 2
        total = selling_price * quantity
        
        sales_order_data = {
            "customer_id": test_customer["id"],
            "items": [{
                "product_id": test_product_with_cost["id"],
                "product_name": test_product_with_cost["name"],
                "sku": test_product_with_cost.get("sku", "TEST-SKU"),
                "quantity": quantity,
                "unit_price": selling_price,
                "total": total
            }],
            "discount": 0,
            "notes": f"{TEST_PREFIX}Sales Order for Return testing"
        }
        
        create_resp = auth_session.post(f"{BASE_URL}/api/sales-orders", json=sales_order_data)
        assert create_resp.status_code == 200
        sales_order = create_resp.json()
        order_id = sales_order["id"]
        order_number = sales_order.get("order_number", "")
        print(f"Created sales order {order_number} for return testing")
        
        # Process the return
        return_resp = auth_session.post(f"{BASE_URL}/api/sales-orders/{order_id}/return")
        assert return_resp.status_code == 200, f"Failed to process return: {return_resp.text}"
        print(f"Processed return for order {order_number}")
        
        # Verify reversal journal entry was created
        entries_resp = auth_session.get(f"{BASE_URL}/api/finance/journal-entries?limit=100")
        assert entries_resp.status_code == 200
        
        entries = entries_resp.json()
        
        # Find reversal entry for this order
        reversal_entries = [e for e in entries if e.get("reference_id") == order_id and "Return" in e.get("description", "")]
        
        assert len(reversal_entries) >= 1, f"Reversal journal entry not found for order {order_id}"
        
        # Check revenue reversal (Debit Revenue, Credit AR)
        revenue_reversal = [e for e in reversal_entries if "Sales Return" in e.get("description", "")]
        assert len(revenue_reversal) >= 1, "Sales Return reversal entry not found"
        
        reversal = revenue_reversal[0]
        lines = reversal.get("lines", [])
        
        # Check for Revenue debit (reversal) and AR credit (reversal)
        revenue_debit = None
        ar_credit = None
        
        for line in lines:
            account_code = line.get("account_code", "")
            if account_code == "4100" and line.get("debit", 0) > 0:
                revenue_debit = line
            if account_code == "1300" and line.get("credit", 0) > 0:
                ar_credit = line
        
        assert revenue_debit is not None, "Revenue reversal debit not found"
        assert ar_credit is not None, "AR reversal credit not found"
        
        print(f"Revenue Debit (Reversal): {revenue_debit.get('debit')}")
        print(f"AR Credit (Reversal): {ar_credit.get('credit')}")
    
    def test_sales_return_reverses_cogs_entry(self, auth_session, test_customer, test_product_with_cost):
        """Test that returning a sales order reverses the COGS journal entry"""
        # Create a sales order first
        cost_price = test_product_with_cost.get("cost_price", 5000)
        selling_price = test_product_with_cost.get("selling_price", 8000)
        quantity = 2
        total_cogs = cost_price * quantity
        
        sales_order_data = {
            "customer_id": test_customer["id"],
            "items": [{
                "product_id": test_product_with_cost["id"],
                "product_name": test_product_with_cost["name"],
                "sku": test_product_with_cost.get("sku", "TEST-SKU"),
                "quantity": quantity,
                "unit_price": selling_price,
                "total": selling_price * quantity
            }],
            "discount": 0,
            "notes": f"{TEST_PREFIX}Sales Order for COGS Reversal testing"
        }
        
        create_resp = auth_session.post(f"{BASE_URL}/api/sales-orders", json=sales_order_data)
        assert create_resp.status_code == 200
        sales_order = create_resp.json()
        order_id = sales_order["id"]
        order_number = sales_order.get("order_number", "")
        print(f"Created sales order {order_number} for COGS reversal testing")
        
        # Process the return
        return_resp = auth_session.post(f"{BASE_URL}/api/sales-orders/{order_id}/return")
        assert return_resp.status_code == 200, f"Failed to process return: {return_resp.text}"
        
        # Verify COGS reversal journal entry was created
        entries_resp = auth_session.get(f"{BASE_URL}/api/finance/journal-entries?limit=100")
        assert entries_resp.status_code == 200
        
        entries = entries_resp.json()
        
        # Find COGS reversal entry for this order
        cogs_reversal_entries = [e for e in entries if e.get("reference_id") == order_id and "COGS Reversal" in e.get("description", "")]
        
        assert len(cogs_reversal_entries) >= 1, f"COGS Reversal journal entry not found for order {order_id}. Found entries: {[e.get('description') for e in entries if e.get('reference_id') == order_id]}"
        
        cogs_reversal = cogs_reversal_entries[0]
        lines = cogs_reversal.get("lines", [])
        
        # Check for Inventory debit (restored) and COGS credit (reversed)
        inventory_debit = None
        cogs_credit = None
        
        for line in lines:
            account_code = line.get("account_code", "")
            if account_code == "1400" and line.get("debit", 0) > 0:
                inventory_debit = line
            if account_code in ["5000", "5100"] and line.get("credit", 0) > 0:
                cogs_credit = line
        
        assert inventory_debit is not None, f"Inventory debit (restoration) not found. Lines: {lines}"
        assert cogs_credit is not None, f"COGS credit (reversal) not found. Lines: {lines}"
        
        print(f"Inventory Debit (Restored): {inventory_debit.get('debit')}")
        print(f"COGS Credit (Reversed): {cogs_credit.get('credit')}")
        
        # Verify amounts
        assert inventory_debit.get("debit") == total_cogs, f"Inventory debit should be {total_cogs}"
        assert cogs_credit.get("credit") == total_cogs, f"COGS credit should be {total_cogs}"


class TestJournalEntryBalance:
    """Test that all journal entries are properly balanced"""
    
    @pytest.fixture(scope="class")
    def auth_session(self):
        session = requests.Session()
        login_response = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "test@demo.com",
            "password": "password123"
        })
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        session.headers.update({"Authorization": f"Bearer {token}"})
        return session
    
    def test_all_entries_are_balanced(self, auth_session):
        """Test that all journal entries have equal debits and credits"""
        response = auth_session.get(f"{BASE_URL}/api/finance/journal-entries?limit=200")
        assert response.status_code == 200
        
        entries = response.json()
        unbalanced = []
        
        for entry in entries:
            total_debit = sum(line.get("debit", 0) for line in entry.get("lines", []))
            total_credit = sum(line.get("credit", 0) for line in entry.get("lines", []))
            
            if abs(total_debit - total_credit) > 0.01:  # Allow small floating point differences
                unbalanced.append({
                    "entry_number": entry.get("entry_number"),
                    "description": entry.get("description"),
                    "debit": total_debit,
                    "credit": total_credit,
                    "difference": total_debit - total_credit
                })
        
        if unbalanced:
            print(f"Unbalanced entries: {unbalanced}")
        
        assert len(unbalanced) == 0, f"Found {len(unbalanced)} unbalanced journal entries"
        print(f"All {len(entries)} journal entries are balanced")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
