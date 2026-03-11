"""
Raw Material Add Stock with Bank Account Integration Tests
Tests the bug fix: Adding raw materials should reduce bank/cash account balance
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    BASE_URL = "https://multi-tenant-hub-30.preview.emergentagent.com"

TEST_EMAIL = "lahiruraja97@gmail.com"
TEST_PASSWORD = "password123"


class TestRawMaterialAddStockWithBank:
    """Test Add Stock with bank account integration"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - Get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        self.token = data["access_token"]
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        yield
        self.session.close()

    def test_01_get_raw_materials_list(self):
        """Test that raw materials endpoint returns list"""
        response = self.session.get(f"{BASE_URL}/api/manufacturing/raw-materials")
        assert response.status_code == 200
        materials = response.json()
        assert isinstance(materials, list)
        assert len(materials) >= 4  # Should have Buttons, Cotton, treads, zipper
        print(f"✓ Found {len(materials)} raw materials")

    def test_02_get_bank_accounts_list(self):
        """Test that bank accounts endpoint returns list with balance"""
        response = self.session.get(f"{BASE_URL}/api/bank-accounts")
        assert response.status_code == 200
        accounts = response.json()
        assert isinstance(accounts, list)
        assert len(accounts) >= 1
        
        # Verify account has required fields
        account = accounts[0]
        assert "id" in account
        assert "account_name" in account
        assert "current_balance" in account
        print(f"✓ Found {len(accounts)} bank accounts, first: {account['account_name']} with balance {account['current_balance']}")

    def test_03_add_stock_without_bank_account(self):
        """Test adding stock without bank account - should NOT create journal entry"""
        # Get a raw material
        materials_response = self.session.get(f"{BASE_URL}/api/manufacturing/raw-materials")
        materials = materials_response.json()
        material = next((m for m in materials if m["sku"] == "RM0004"), materials[0])  # treads or first material
        material_id = material["id"]
        initial_stock = material["stock_quantity"]
        
        # Add stock WITHOUT bank account
        response = self.session.post(
            f"{BASE_URL}/api/manufacturing/raw-materials/{material_id}/add-stock",
            params={
                "quantity": 5,
                "total_cost": 50,
                "cost_price": 10
            }
        )
        
        assert response.status_code == 200, f"Add stock failed: {response.text}"
        data = response.json()
        
        # Verify response
        assert data["message"] == "Stock added successfully"
        assert data["new_quantity"] == initial_stock + 5
        assert data["journal_entry_created"] == False  # No bank account = no journal entry
        print(f"✓ Added stock without bank account, journal_entry_created: {data['journal_entry_created']}")

    def test_04_add_stock_with_bank_account_creates_journal_entry(self):
        """Test adding stock WITH bank account - should create journal entry with RM- prefix"""
        # Get bank account
        accounts_response = self.session.get(f"{BASE_URL}/api/bank-accounts")
        accounts = accounts_response.json()
        bank_account = accounts[0]
        bank_account_id = bank_account["id"]
        initial_balance = bank_account["current_balance"]
        
        # Get a raw material
        materials_response = self.session.get(f"{BASE_URL}/api/manufacturing/raw-materials")
        materials = materials_response.json()
        material = next((m for m in materials if m["sku"] == "RM0002"), materials[0])  # zipper or first
        material_id = material["id"]
        initial_stock = material["stock_quantity"]
        
        # Add stock WITH bank account
        quantity = 3
        unit_cost = 10
        total_cost = 30
        
        response = self.session.post(
            f"{BASE_URL}/api/manufacturing/raw-materials/{material_id}/add-stock",
            params={
                "quantity": quantity,
                "total_cost": total_cost,
                "cost_price": unit_cost,
                "bank_account_id": bank_account_id
            }
        )
        
        assert response.status_code == 200, f"Add stock with bank failed: {response.text}"
        data = response.json()
        
        # Verify response
        assert data["message"] == "Stock added successfully"
        assert data["new_quantity"] == initial_stock + quantity
        assert data["journal_entry_created"] == True  # Should create journal entry
        print(f"✓ Added stock with bank account, journal_entry_created: {data['journal_entry_created']}")
        
        # Verify bank balance decreased
        accounts_response = self.session.get(f"{BASE_URL}/api/bank-accounts")
        accounts = accounts_response.json()
        updated_account = next(a for a in accounts if a["id"] == bank_account_id)
        expected_balance = initial_balance - total_cost
        
        assert abs(updated_account["current_balance"] - expected_balance) < 0.01, \
            f"Bank balance mismatch: expected {expected_balance}, got {updated_account['current_balance']}"
        print(f"✓ Bank balance reduced from {initial_balance} to {updated_account['current_balance']}")

    def test_05_journal_entry_has_rm_prefix(self):
        """Test that raw material purchase creates journal entry with RM- prefix"""
        # Get manufacturing transactions
        response = self.session.get(
            f"{BASE_URL}/api/simple-finance/all-transactions",
            params={"transaction_type": "manufacturing"}
        )
        
        assert response.status_code == 200, f"Get transactions failed: {response.text}"
        data = response.json()
        transactions = data["transactions"]
        
        # Find raw material purchase transactions
        rm_transactions = [t for t in transactions if t["reference"].startswith("RM-")]
        
        assert len(rm_transactions) >= 1, "No raw material purchase transactions found"
        
        # Verify transaction properties
        rm_txn = rm_transactions[0]
        assert rm_txn["transaction_type"] == "raw_material_purchase"
        assert "Raw material purchase" in rm_txn["description"]
        print(f"✓ Found {len(rm_transactions)} RM purchase transactions, first: {rm_txn['reference']}")

    def test_06_manufacturing_filter_includes_raw_material_purchases(self):
        """Test that manufacturing filter includes raw_material_purchase type"""
        response = self.session.get(
            f"{BASE_URL}/api/simple-finance/all-transactions",
            params={"transaction_type": "manufacturing"}
        )
        
        assert response.status_code == 200
        data = response.json()
        transactions = data["transactions"]
        
        # Get unique transaction types
        tx_types = set(t["transaction_type"] for t in transactions)
        
        # Should include various manufacturing types
        assert "raw_material_purchase" in tx_types, "raw_material_purchase not in manufacturing filter"
        
        # Should also include other manufacturing types if they exist
        expected_types = {"mfg_material_issue", "mfg_labor", "mfg_production", "mfg_scrap", "raw_material_purchase"}
        found_types = tx_types.intersection(expected_types)
        
        assert len(found_types) >= 2, f"Expected multiple manufacturing types, found: {found_types}"
        print(f"✓ Manufacturing filter includes transaction types: {tx_types}")

    def test_07_add_stock_auto_calculates_total_cost(self):
        """Test that total_cost is calculated from quantity * cost_price if not provided"""
        # Get a raw material
        materials_response = self.session.get(f"{BASE_URL}/api/manufacturing/raw-materials")
        materials = materials_response.json()
        material = materials[0]
        material_id = material["id"]
        
        # Add stock with only quantity and cost_price (total_cost=0)
        quantity = 2
        unit_cost = 15
        
        response = self.session.post(
            f"{BASE_URL}/api/manufacturing/raw-materials/{material_id}/add-stock",
            params={
                "quantity": quantity,
                "total_cost": 0,  # Should be auto-calculated
                "cost_price": unit_cost
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Total cost should be calculated as quantity * unit_cost
        expected_total = quantity * unit_cost
        assert data["total_cost"] == expected_total, \
            f"Total cost mismatch: expected {expected_total}, got {data['total_cost']}"
        print(f"✓ Total cost auto-calculated: {data['total_cost']} (expected {expected_total})")


class TestAddStockDialogFields:
    """Tests for Add Stock dialog UI fields via API validation"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - Get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        self.token = data["access_token"]
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        yield
        self.session.close()

    def test_add_stock_accepts_all_fields(self):
        """Test that add-stock endpoint accepts all new fields"""
        # Get first material
        materials_response = self.session.get(f"{BASE_URL}/api/manufacturing/raw-materials")
        materials = materials_response.json()
        material_id = materials[0]["id"]
        
        # Get first bank account
        accounts_response = self.session.get(f"{BASE_URL}/api/bank-accounts")
        accounts = accounts_response.json()
        bank_account_id = accounts[0]["id"] if accounts else None
        
        # Test all fields
        params = {
            "quantity": 1,
            "total_cost": 100,
            "cost_price": 100,
            "reference": "TEST-REF-001"
        }
        if bank_account_id:
            params["bank_account_id"] = bank_account_id
        
        response = self.session.post(
            f"{BASE_URL}/api/manufacturing/raw-materials/{material_id}/add-stock",
            params=params
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "new_quantity" in data
        assert "total_cost" in data
        assert "journal_entry_created" in data
        print(f"✓ Add stock accepts all fields: quantity, total_cost, cost_price, reference, bank_account_id")
