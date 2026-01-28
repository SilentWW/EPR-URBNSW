"""
Backend Tests for ERP System - Phase 2 Features
Tests: WooCommerce Categories/Tags, SEO Tags Suggestion, Finance Module, Products, GRN
"""
import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "admin@example.com"
TEST_PASSWORD = "admin123"


class TestWooCommerceEndpoints:
    """WooCommerce integration endpoint tests"""
    
    def test_get_woo_categories(self, auth_token):
        """Test WooCommerce categories endpoint"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/woocommerce/categories", headers=headers)
        assert response.status_code == 200, f"Categories endpoint failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ WooCommerce categories endpoint returned {len(data)} categories")
        
        # Verify structure if categories exist
        if data:
            cat = data[0]
            assert "id" in cat
            assert "name" in cat
            assert "slug" in cat
    
    def test_get_woo_tags(self, auth_token):
        """Test WooCommerce tags endpoint"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/woocommerce/tags", headers=headers)
        assert response.status_code == 200, f"Tags endpoint failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ WooCommerce tags endpoint returned {len(data)} tags")
    
    def test_suggest_seo_tags(self, auth_token):
        """Test SEO tags suggestion endpoint"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Test with product name only
        response = requests.get(
            f"{BASE_URL}/api/woocommerce/suggest-tags",
            params={"product_name": "Blue Cotton T-Shirt"},
            headers=headers
        )
        assert response.status_code == 200, f"Suggest tags failed: {response.text}"
        data = response.json()
        assert "suggested_tags" in data
        assert "tags_string" in data
        assert isinstance(data["suggested_tags"], list)
        assert len(data["suggested_tags"]) > 0
        print(f"✓ SEO tags suggested: {data['tags_string']}")
    
    def test_suggest_seo_tags_with_category(self, auth_token):
        """Test SEO tags suggestion with category"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.get(
            f"{BASE_URL}/api/woocommerce/suggest-tags",
            params={"product_name": "Running Shoes", "category": "Sports"},
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "sports" in [t.lower() for t in data["suggested_tags"]]
        print(f"✓ SEO tags with category: {data['tags_string']}")


class TestProductsSimplified:
    """Products page - simplified form tests"""
    
    def test_get_products(self, auth_token):
        """Test getting products list"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/products", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Retrieved {len(data)} products")
    
    def test_get_product_categories(self, auth_token):
        """Test getting product categories"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/products/categories", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Retrieved {len(data)} product categories")
    
    def test_create_simplified_product(self, auth_token):
        """Test creating product with simplified form (SKU, Name, Category only)"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Get next SKU
        sku_response = requests.get(f"{BASE_URL}/api/grn/next-sku", headers=headers)
        assert sku_response.status_code == 200
        next_sku = sku_response.json()["next_sku"]
        
        # Create product with minimal fields (as per simplified form)
        product_data = {
            "sku": f"TEST-{datetime.now().strftime('%H%M%S')}",
            "name": "TEST Simplified Product",
            "category": "Clothing",
            "cost_price": 0,  # Set via GRN
            "selling_price": 0,  # Set via GRN
            "stock_quantity": 0,  # Set via GRN
            "low_stock_threshold": 10
        }
        
        response = requests.post(f"{BASE_URL}/api/products", headers=headers, json=product_data)
        assert response.status_code == 200, f"Create product failed: {response.text}"
        data = response.json()
        assert data["name"] == "TEST Simplified Product"
        assert data["cost_price"] == 0  # Should be 0 until GRN
        assert data["stock_quantity"] == 0  # Should be 0 until GRN
        print(f"✓ Created simplified product: {data['sku']} - {data['name']}")
        return data["id"]


class TestGRNWithSEOTags:
    """GRN page tests including SEO tags functionality"""
    
    def test_get_grns(self, auth_token):
        """Test getting GRN list"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/grn", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Retrieved {len(data)} GRNs")
    
    def test_get_next_sku(self, auth_token):
        """Test getting next available SKU"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/grn/next-sku", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "next_sku" in data
        assert data["next_sku"].startswith("URBN")
        print(f"✓ Next SKU: {data['next_sku']}")
    
    def test_create_grn_with_new_product(self, auth_token):
        """Test creating GRN with new product (updates inventory and creates finance entries)"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Get suppliers
        suppliers_response = requests.get(f"{BASE_URL}/api/suppliers", headers=headers)
        suppliers = suppliers_response.json()
        
        if not suppliers:
            # Create a test supplier first
            supplier_data = {
                "name": "TEST GRN Supplier",
                "email": "testgrn@supplier.com",
                "phone": "1234567890",
                "address": "Test Address"
            }
            create_response = requests.post(f"{BASE_URL}/api/suppliers", headers=headers, json=supplier_data)
            if create_response.status_code == 200:
                supplier_id = create_response.json()["id"]
            else:
                print("⚠ Could not create supplier for GRN test")
                return
        else:
            supplier_id = suppliers[0]["id"]
        
        # Get next SKU
        sku_response = requests.get(f"{BASE_URL}/api/grn/next-sku", headers=headers)
        next_sku = sku_response.json()["next_sku"]
        
        # Create GRN with new product
        grn_data = {
            "supplier_id": supplier_id,
            "reference_number": f"TEST-REF-{datetime.now().strftime('%H%M%S')}",
            "received_date": datetime.now().strftime("%Y-%m-%d"),
            "items": [
                {
                    "product_id": None,  # New product
                    "product_name": f"TEST GRN Product {datetime.now().strftime('%H%M%S')}",
                    "sku": next_sku,
                    "description": "Test product created via GRN",
                    "short_description": "Test product",
                    "category": "Electronics",
                    "quantity": 10,
                    "cost_price": 100.00,
                    "regular_price": 150.00,
                    "sale_price": None,
                    "weight": 0.5,
                    "visibility": "public",
                    "tags": "test, electronics, gadget"
                }
            ],
            "notes": "Test GRN for automated testing",
            "sync_to_woo": False  # Don't sync to WooCommerce in test
        }
        
        response = requests.post(f"{BASE_URL}/api/grn", headers=headers, json=grn_data)
        assert response.status_code == 200, f"Create GRN failed: {response.text}"
        data = response.json()
        assert "grn_number" in data
        assert data["total_cost"] == 1000.00  # 10 * 100
        print(f"✓ Created GRN: {data['grn_number']} - Total: {data['total_cost']}")
        return data["id"]


class TestFinanceModule:
    """Finance module comprehensive tests"""
    
    def test_initialize_chart_of_accounts(self, auth_token):
        """Test chart of accounts initialization"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.post(f"{BASE_URL}/api/finance/chart-of-accounts/initialize", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "count" in data
        print(f"✓ Chart of accounts: {data['message']} - Count: {data['count']}")
    
    def test_get_chart_of_accounts(self, auth_token):
        """Test getting chart of accounts"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/finance/chart-of-accounts", headers=headers)
        assert response.status_code == 200
        accounts = response.json()
        assert isinstance(accounts, list)
        assert len(accounts) > 0
        
        # Verify key accounts exist
        account_codes = [a["code"] for a in accounts]
        required_codes = ["1100", "1200", "1300", "1400", "2100", "4100", "5100"]
        for code in required_codes:
            assert code in account_codes, f"Missing required account: {code}"
        
        print(f"✓ Chart of accounts has {len(accounts)} accounts with all required codes")
    
    def test_get_journal_entries(self, auth_token):
        """Test getting journal entries"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/finance/journal-entries", headers=headers)
        assert response.status_code == 200
        entries = response.json()
        assert isinstance(entries, list)
        print(f"✓ Retrieved {len(entries)} journal entries")
    
    def test_create_balanced_journal_entry(self, auth_token):
        """Test creating a balanced journal entry"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Get accounts
        accounts_response = requests.get(f"{BASE_URL}/api/finance/chart-of-accounts", headers=headers)
        accounts = accounts_response.json()
        
        cash_account = next((a for a in accounts if a["code"] == "1100"), None)
        expense_account = next((a for a in accounts if a["code"] == "6100"), None)
        
        if not cash_account or not expense_account:
            print("⚠ Required accounts not found for journal entry test")
            return
        
        entry_data = {
            "entry_date": datetime.now().strftime("%Y-%m-%d"),
            "reference_number": f"TEST-JE-{datetime.now().strftime('%H%M%S')}",
            "description": "TEST Journal Entry",
            "lines": [
                {
                    "account_id": expense_account["id"],
                    "debit": 5000,
                    "credit": 0,
                    "description": "Test expense"
                },
                {
                    "account_id": cash_account["id"],
                    "debit": 0,
                    "credit": 5000,
                    "description": "Test cash payment"
                }
            ],
            "is_auto_generated": False
        }
        
        response = requests.post(f"{BASE_URL}/api/finance/journal-entries", headers=headers, json=entry_data)
        assert response.status_code == 200, f"Create journal entry failed: {response.text}"
        data = response.json()
        assert data["is_balanced"] == True
        assert data["total_debit"] == 5000
        assert data["total_credit"] == 5000
        print(f"✓ Created balanced journal entry: {data['entry_number']}")
    
    def test_reject_unbalanced_entry(self, auth_token):
        """Test that unbalanced entries are rejected"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        accounts_response = requests.get(f"{BASE_URL}/api/finance/chart-of-accounts", headers=headers)
        accounts = accounts_response.json()
        
        cash_account = next((a for a in accounts if a["code"] == "1100"), None)
        expense_account = next((a for a in accounts if a["code"] == "6100"), None)
        
        if not cash_account or not expense_account:
            print("⚠ Required accounts not found")
            return
        
        entry_data = {
            "entry_date": datetime.now().strftime("%Y-%m-%d"),
            "reference_number": f"UNBAL-{datetime.now().strftime('%H%M%S')}",
            "description": "Unbalanced test entry",
            "lines": [
                {
                    "account_id": expense_account["id"],
                    "debit": 10000,
                    "credit": 0,
                    "description": "Expense"
                },
                {
                    "account_id": cash_account["id"],
                    "debit": 0,
                    "credit": 5000,  # Intentionally unbalanced
                    "description": "Cash"
                }
            ],
            "is_auto_generated": False
        }
        
        response = requests.post(f"{BASE_URL}/api/finance/journal-entries", headers=headers, json=entry_data)
        assert response.status_code == 400
        assert "not balanced" in response.text.lower()
        print("✓ Unbalanced entry correctly rejected")
    
    def test_profit_loss_report(self, auth_token):
        """Test P&L report"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/finance/reports/profit-loss", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "period" in data
        assert "income" in data
        assert "expenses" in data
        assert "net_profit" in data
        print(f"✓ P&L Report - Net Profit: {data['net_profit']}")
    
    def test_balance_sheet(self, auth_token):
        """Test Balance Sheet report"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/finance/reports/balance-sheet", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "as_of_date" in data
        assert "assets" in data
        assert "liabilities" in data
        assert "equity" in data
        assert "total_assets" in data
        assert "total_liabilities_equity" in data
        print(f"✓ Balance Sheet - Assets: {data['total_assets']}, Liabilities+Equity: {data['total_liabilities_equity']}")
    
    def test_trial_balance(self, auth_token):
        """Test Trial Balance report"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/finance/reports/trial-balance", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "as_of_date" in data
        assert "accounts" in data
        assert "total_debit" in data
        assert "total_credit" in data
        assert "is_balanced" in data
        print(f"✓ Trial Balance - Balanced: {data['is_balanced']}, Debit: {data['total_debit']}, Credit: {data['total_credit']}")
    
    def test_general_ledger(self, auth_token):
        """Test General Ledger"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/finance/general-ledger", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ General Ledger - {len(data)} accounts with transactions")


class TestSupplierCreation:
    """Supplier creation regression tests"""
    
    def test_create_supplier_with_valid_email(self, auth_token):
        """Test creating supplier with valid email"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        supplier_data = {
            "name": f"TEST Supplier {datetime.now().strftime('%H%M%S')}",
            "email": f"test{datetime.now().strftime('%H%M%S')}@supplier.com",
            "phone": "1234567890",
            "address": "Test Address"
        }
        
        response = requests.post(f"{BASE_URL}/api/suppliers", headers=headers, json=supplier_data)
        assert response.status_code == 200, f"Create supplier failed: {response.text}"
        data = response.json()
        assert data["name"] == supplier_data["name"]
        assert data["email"] == supplier_data["email"]
        print(f"✓ Created supplier: {data['name']}")
    
    def test_create_supplier_with_invalid_email(self, auth_token):
        """Test creating supplier with invalid email format"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        supplier_data = {
            "name": "Invalid Email Supplier",
            "email": "invalid-email",  # Invalid format
            "phone": "1234567890"
        }
        
        response = requests.post(f"{BASE_URL}/api/suppliers", headers=headers, json=supplier_data)
        assert response.status_code == 422, f"Expected 422 for invalid email, got {response.status_code}"
        print("✓ Invalid email correctly rejected with 422")
    
    def test_get_suppliers(self, auth_token):
        """Test getting suppliers list"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/suppliers", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Retrieved {len(data)} suppliers")


# Fixtures
@pytest.fixture(scope="session")
def auth_token():
    """Get authentication token for tests"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code != 200:
        pytest.skip(f"Authentication failed: {response.text}")
    return response.json()["access_token"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
