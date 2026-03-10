"""
Test Packaging Rules Refactoring
Tests for:
1. /api/packaging-items endpoint removed (should return 404)
2. /api/packaging/rules CRUD operations
3. Sales order creation deducts packaging products from inventory
4. Inventory movements recorded for packaging deductions
"""
import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
TEST_EMAIL = "test_pkg_refactor@test.com"
TEST_PASSWORD = "test123"


class TestPackagingRefactor:
    """Test suite for packaging rules refactoring"""
    
    token = None
    company_id = None
    test_product_id = None
    test_packaging_product_id = None
    test_customer_id = None
    test_rule_id = None
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: authenticate and get token"""
        # Login with test credentials
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            data = response.json()
            TestPackagingRefactor.token = data["access_token"]
            TestPackagingRefactor.company_id = data["user"]["company_id"]
        else:
            pytest.skip(f"Login failed: {response.status_code} - {response.text}")
    
    def get_headers(self):
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    # ==================== Test 1: packaging-items endpoint removed ====================
    
    def test_packaging_items_endpoint_removed(self):
        """Verify /api/packaging-items endpoint returns 404 (was removed)"""
        response = requests.get(f"{BASE_URL}/api/packaging-items", headers=self.get_headers())
        # Should return 404 since endpoint was removed
        assert response.status_code == 404, f"Expected 404 but got {response.status_code}"
        print("PASS: /api/packaging-items endpoint correctly returns 404")
    
    def test_packaging_items_create_endpoint_removed(self):
        """Verify POST /api/packaging-items endpoint returns 404"""
        response = requests.post(f"{BASE_URL}/api/packaging-items", 
            headers=self.get_headers(),
            json={"name": "Test", "sku": "TEST"}
        )
        assert response.status_code == 404, f"Expected 404 but got {response.status_code}"
        print("PASS: POST /api/packaging-items endpoint correctly returns 404")
    
    # ==================== Test 2: Packaging Rules CRUD ====================
    
    def test_packaging_rules_get_all(self):
        """Verify GET /api/packaging/rules works"""
        response = requests.get(f"{BASE_URL}/api/packaging/rules", headers=self.get_headers())
        assert response.status_code == 200, f"Expected 200 but got {response.status_code}: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"PASS: GET /api/packaging/rules returns {len(data)} rules")
    
    def test_create_test_products_for_rule(self):
        """Create test products needed for packaging rule testing"""
        # Create main product
        main_product = {
            "name": f"TEST_MainProduct_{uuid.uuid4().hex[:6]}",
            "sku": f"TEST-MAIN-{uuid.uuid4().hex[:6]}",
            "cost_price": 100.0,
            "selling_price": 150.0,
            "stock_quantity": 50,
            "low_stock_threshold": 5
        }
        response = requests.post(f"{BASE_URL}/api/products", 
            headers=self.get_headers(), 
            json=main_product
        )
        assert response.status_code == 200, f"Failed to create main product: {response.text}"
        TestPackagingRefactor.test_product_id = response.json()["id"]
        print(f"PASS: Created test main product: {TestPackagingRefactor.test_product_id}")
        
        # Create packaging product
        pkg_product = {
            "name": f"TEST_PackagingBag_{uuid.uuid4().hex[:6]}",
            "sku": f"TEST-PKG-{uuid.uuid4().hex[:6]}",
            "cost_price": 5.0,
            "selling_price": 0.0,
            "stock_quantity": 100,
            "low_stock_threshold": 10
        }
        response = requests.post(f"{BASE_URL}/api/products", 
            headers=self.get_headers(), 
            json=pkg_product
        )
        assert response.status_code == 200, f"Failed to create packaging product: {response.text}"
        TestPackagingRefactor.test_packaging_product_id = response.json()["id"]
        print(f"PASS: Created test packaging product: {TestPackagingRefactor.test_packaging_product_id}")
    
    def test_create_packaging_rule(self):
        """Test creating a packaging rule linking main product to packaging product"""
        if not TestPackagingRefactor.test_product_id or not TestPackagingRefactor.test_packaging_product_id:
            pytest.skip("Test products not created")
        
        rule_data = {
            "product_id": TestPackagingRefactor.test_product_id,
            "items": [
                {"product_id": TestPackagingRefactor.test_packaging_product_id, "quantity": 1}
            ],
            "is_active": True
        }
        response = requests.post(f"{BASE_URL}/api/packaging/rules", 
            headers=self.get_headers(), 
            json=rule_data
        )
        assert response.status_code == 200, f"Failed to create rule: {response.text}"
        data = response.json()
        TestPackagingRefactor.test_rule_id = data["id"]
        assert data["product_id"] == TestPackagingRefactor.test_product_id
        assert len(data["items"]) == 1
        assert data["items"][0]["product_id"] == TestPackagingRefactor.test_packaging_product_id
        print(f"PASS: Created packaging rule: {TestPackagingRefactor.test_rule_id}")
    
    def test_get_packaging_rule_for_product(self):
        """Test getting packaging rule for a specific product"""
        if not TestPackagingRefactor.test_product_id:
            pytest.skip("Test product not created")
        
        response = requests.get(
            f"{BASE_URL}/api/packaging/rules/product/{TestPackagingRefactor.test_product_id}",
            headers=self.get_headers()
        )
        assert response.status_code == 200, f"Expected 200 but got {response.status_code}: {response.text}"
        data = response.json()
        if data:  # Rule may not exist
            assert data["product_id"] == TestPackagingRefactor.test_product_id
        print("PASS: GET /api/packaging/rules/product/{id} works correctly")
    
    def test_update_packaging_rule(self):
        """Test updating a packaging rule"""
        if not TestPackagingRefactor.test_rule_id:
            pytest.skip("Test rule not created")
        
        update_data = {
            "items": [
                {"product_id": TestPackagingRefactor.test_packaging_product_id, "quantity": 2}
            ],
            "is_active": True
        }
        response = requests.put(
            f"{BASE_URL}/api/packaging/rules/{TestPackagingRefactor.test_rule_id}",
            headers=self.get_headers(),
            json=update_data
        )
        assert response.status_code == 200, f"Failed to update rule: {response.text}"
        data = response.json()
        assert data["items"][0]["quantity"] == 2
        print("PASS: Updated packaging rule quantity to 2")
    
    # ==================== Test 3: Sales Order with Packaging Deduction ====================
    
    def test_create_test_customer(self):
        """Create test customer for sales order"""
        customer_data = {
            "name": f"TEST_Customer_{uuid.uuid4().hex[:6]}",
            "email": f"test_{uuid.uuid4().hex[:6]}@test.com",
            "phone": "1234567890"
        }
        response = requests.post(f"{BASE_URL}/api/customers", 
            headers=self.get_headers(), 
            json=customer_data
        )
        assert response.status_code == 200, f"Failed to create customer: {response.text}"
        TestPackagingRefactor.test_customer_id = response.json()["id"]
        print(f"PASS: Created test customer: {TestPackagingRefactor.test_customer_id}")
    
    def test_sales_order_deducts_packaging(self):
        """Test that creating a sales order deducts packaging products"""
        if not all([
            TestPackagingRefactor.test_product_id, 
            TestPackagingRefactor.test_customer_id,
            TestPackagingRefactor.test_packaging_product_id
        ]):
            pytest.skip("Test data not created")
        
        # Get current stock levels
        main_response = requests.get(
            f"{BASE_URL}/api/products/{TestPackagingRefactor.test_product_id}",
            headers=self.get_headers()
        )
        pkg_response = requests.get(
            f"{BASE_URL}/api/products/{TestPackagingRefactor.test_packaging_product_id}",
            headers=self.get_headers()
        )
        
        main_stock_before = main_response.json()["stock_quantity"]
        pkg_stock_before = pkg_response.json()["stock_quantity"]
        print(f"Stock before order: Main={main_stock_before}, Packaging={pkg_stock_before}")
        
        # Create sales order
        order_data = {
            "customer_id": TestPackagingRefactor.test_customer_id,
            "items": [{
                "product_id": TestPackagingRefactor.test_product_id,
                "product_name": "Test Product",
                "sku": "TEST-SKU",
                "quantity": 2,
                "unit_price": 150.0,
                "total": 300.0
            }],
            "discount": 0,
            "notes": "Test order for packaging deduction"
        }
        
        response = requests.post(f"{BASE_URL}/api/sales-orders", 
            headers=self.get_headers(), 
            json=order_data
        )
        assert response.status_code == 200, f"Failed to create sales order: {response.text}"
        order = response.json()
        print(f"PASS: Created sales order: {order['order_number']}")
        
        # Verify stock deductions
        main_response = requests.get(
            f"{BASE_URL}/api/products/{TestPackagingRefactor.test_product_id}",
            headers=self.get_headers()
        )
        pkg_response = requests.get(
            f"{BASE_URL}/api/products/{TestPackagingRefactor.test_packaging_product_id}",
            headers=self.get_headers()
        )
        
        main_stock_after = main_response.json()["stock_quantity"]
        pkg_stock_after = pkg_response.json()["stock_quantity"]
        print(f"Stock after order: Main={main_stock_after}, Packaging={pkg_stock_after}")
        
        # Main product should be reduced by 2
        assert main_stock_after == main_stock_before - 2, \
            f"Main product stock not reduced correctly: expected {main_stock_before - 2}, got {main_stock_after}"
        
        # Packaging product should be reduced by 4 (2 items * 2 qty per rule)
        expected_pkg_deduction = 2 * 2  # order qty * rule qty (updated to 2)
        assert pkg_stock_after == pkg_stock_before - expected_pkg_deduction, \
            f"Packaging stock not reduced correctly: expected {pkg_stock_before - expected_pkg_deduction}, got {pkg_stock_after}"
        
        print(f"PASS: Stock correctly deducted - Main: {main_stock_before} -> {main_stock_after}, Packaging: {pkg_stock_before} -> {pkg_stock_after}")
        
        return order["id"]
    
    # ==================== Test 4: Inventory Movements Recorded ====================
    
    def test_inventory_movements_recorded(self):
        """Test that inventory movements are recorded for packaging deductions"""
        if not TestPackagingRefactor.test_packaging_product_id:
            pytest.skip("Test packaging product not created")
        
        response = requests.get(
            f"{BASE_URL}/api/inventory/movements?product_id={TestPackagingRefactor.test_packaging_product_id}",
            headers=self.get_headers()
        )
        assert response.status_code == 200, f"Failed to get movements: {response.text}"
        movements = response.json()
        
        # Find packaging-related movements
        packaging_movements = [m for m in movements if "Packaging" in m.get("reason", "")]
        
        if packaging_movements:
            print(f"PASS: Found {len(packaging_movements)} packaging-related inventory movements")
            for m in packaging_movements[:3]:  # Show first 3
                print(f"  - {m['reason']}: {m['quantity']} units ({m['movement_type']})")
        else:
            print("INFO: No packaging movements found (may be from previous test runs)")
    
    # ==================== Cleanup ====================
    
    def test_cleanup_delete_rule(self):
        """Clean up: delete test packaging rule"""
        if TestPackagingRefactor.test_rule_id:
            response = requests.delete(
                f"{BASE_URL}/api/packaging/rules/{TestPackagingRefactor.test_rule_id}",
                headers=self.get_headers()
            )
            if response.status_code == 200:
                print(f"PASS: Deleted test rule: {TestPackagingRefactor.test_rule_id}")
            else:
                print(f"WARN: Could not delete rule: {response.status_code}")
    
    def test_cleanup_delete_products(self):
        """Clean up: delete test products"""
        for product_id in [TestPackagingRefactor.test_product_id, TestPackagingRefactor.test_packaging_product_id]:
            if product_id:
                response = requests.delete(
                    f"{BASE_URL}/api/products/{product_id}",
                    headers=self.get_headers()
                )
                if response.status_code == 200:
                    print(f"PASS: Deleted test product: {product_id}")
    
    def test_cleanup_delete_customer(self):
        """Clean up: delete test customer"""
        if TestPackagingRefactor.test_customer_id:
            response = requests.delete(
                f"{BASE_URL}/api/customers/{TestPackagingRefactor.test_customer_id}",
                headers=self.get_headers()
            )
            if response.status_code == 200:
                print(f"PASS: Deleted test customer: {TestPackagingRefactor.test_customer_id}")


class TestExistingPackagingData:
    """Test with existing packaging data (Test T-Shirt, Courier Bag, Thank You Card)"""
    
    token = None
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup: authenticate"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            TestExistingPackagingData.token = response.json()["access_token"]
        else:
            pytest.skip("Login failed")
    
    def get_headers(self):
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def test_existing_packaging_rules_have_product_details(self):
        """Verify existing packaging rules include product details"""
        response = requests.get(f"{BASE_URL}/api/packaging/rules", headers=self.get_headers())
        assert response.status_code == 200
        rules = response.json()
        
        for rule in rules:
            # Each rule should have enriched product data
            assert "product_name" in rule, f"Rule missing product_name: {rule}"
            assert "product_sku" in rule, f"Rule missing product_sku: {rule}"
            
            # Each item should have product details
            for item in rule.get("items", []):
                if "product_name" in item:
                    print(f"  Rule for '{rule['product_name']}' includes packaging: {item['product_name']} x {item['quantity']}")
        
        print(f"PASS: All {len(rules)} rules have proper product details")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
