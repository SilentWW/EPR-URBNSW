"""
Backend Tests for ERP System - Supplier, GRN, and Purchase Order Features
Tests: Supplier creation with email validation, GRN from PO, PO status
"""
import pytest
import requests
import os
import json
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "admin@example.com"
TEST_PASSWORD = "admin123"


class TestSupplierCreation:
    """Supplier creation tests - Bug fix verification"""
    
    def test_create_supplier_with_valid_email(self, auth_token):
        """Test creating supplier with valid email - should succeed"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        supplier_data = {
            "name": f"TEST Supplier {datetime.now().strftime('%H%M%S')}",
            "email": "valid_supplier@example.com",
            "phone": "+94771234567",
            "address": "123 Test Street",
            "contact_person": "Test Contact"
        }
        
        response = requests.post(f"{BASE_URL}/api/suppliers", 
                                headers=headers, json=supplier_data)
        
        assert response.status_code == 200, f"Create supplier failed: {response.text}"
        data = response.json()
        assert data["name"] == supplier_data["name"]
        assert data["email"] == supplier_data["email"]
        assert "id" in data
        print(f"✓ Created supplier with valid email: {data['name']}")
        return data["id"]
    
    def test_create_supplier_with_invalid_email_format(self, auth_token):
        """Test creating supplier with invalid email - should return 422 validation error"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        supplier_data = {
            "name": f"TEST Invalid Email Supplier {datetime.now().strftime('%H%M%S')}",
            "email": "invalid-email-format",  # Invalid email format
            "phone": "+94771234567"
        }
        
        response = requests.post(f"{BASE_URL}/api/suppliers", 
                                headers=headers, json=supplier_data)
        
        # Should return 422 Unprocessable Entity for validation error
        assert response.status_code == 422, f"Expected 422 for invalid email, got {response.status_code}: {response.text}"
        
        # Verify error response structure
        data = response.json()
        assert "detail" in data
        print(f"✓ Invalid email correctly rejected with 422: {response.text[:100]}")
    
    def test_create_supplier_without_email(self, auth_token):
        """Test creating supplier without email - should succeed (email is optional)"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        supplier_data = {
            "name": f"TEST No Email Supplier {datetime.now().strftime('%H%M%S')}",
            "phone": "+94771234567",
            "contact_person": "No Email Contact"
        }
        
        response = requests.post(f"{BASE_URL}/api/suppliers", 
                                headers=headers, json=supplier_data)
        
        assert response.status_code == 200, f"Create supplier without email failed: {response.text}"
        data = response.json()
        assert data["name"] == supplier_data["name"]
        assert data.get("email") is None
        print(f"✓ Created supplier without email: {data['name']}")
    
    def test_get_suppliers_list(self, auth_token):
        """Test getting suppliers list"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.get(f"{BASE_URL}/api/suppliers", headers=headers)
        
        assert response.status_code == 200
        suppliers = response.json()
        assert isinstance(suppliers, list)
        print(f"✓ Retrieved {len(suppliers)} suppliers")


class TestPurchaseOrders:
    """Purchase Order tests"""
    
    def test_get_purchase_orders(self, auth_token):
        """Test getting purchase orders list"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.get(f"{BASE_URL}/api/purchase-orders", headers=headers)
        
        assert response.status_code == 200
        orders = response.json()
        assert isinstance(orders, list)
        print(f"✓ Retrieved {len(orders)} purchase orders")
        return orders
    
    def test_get_pending_purchase_orders(self, auth_token):
        """Test getting pending purchase orders - for 'Receive as GRN' feature"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.get(f"{BASE_URL}/api/purchase-orders?status=pending", headers=headers)
        
        assert response.status_code == 200
        orders = response.json()
        assert isinstance(orders, list)
        
        # All returned orders should be pending
        for order in orders:
            assert order["status"] == "pending", f"Order {order['order_number']} is not pending"
        
        print(f"✓ Retrieved {len(orders)} pending purchase orders")
        return orders
    
    def test_get_purchase_order_details(self, auth_token):
        """Test getting single purchase order details"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # First get list of orders
        response = requests.get(f"{BASE_URL}/api/purchase-orders", headers=headers)
        orders = response.json()
        
        if not orders:
            print("⚠ No purchase orders to test details")
            return
        
        order_id = orders[0]["id"]
        response = requests.get(f"{BASE_URL}/api/purchase-orders/{order_id}", headers=headers)
        
        assert response.status_code == 200
        order = response.json()
        assert order["id"] == order_id
        assert "items" in order
        assert "supplier_name" in order
        print(f"✓ Retrieved PO details: {order['order_number']}")


class TestGRN:
    """GRN (Goods Received Note) tests"""
    
    def test_get_grns(self, auth_token):
        """Test getting GRN list"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.get(f"{BASE_URL}/api/grn", headers=headers)
        
        assert response.status_code == 200
        grns = response.json()
        assert isinstance(grns, list)
        print(f"✓ Retrieved {len(grns)} GRNs")
    
    def test_get_next_sku(self, auth_token):
        """Test getting next SKU for GRN"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.get(f"{BASE_URL}/api/grn/next-sku", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "next_sku" in data
        assert data["next_sku"].startswith("URBN")
        print(f"✓ Next SKU: {data['next_sku']}")
    
    def test_create_grn_from_po(self, auth_token):
        """Test creating GRN from Purchase Order - new feature"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Get pending POs
        response = requests.get(f"{BASE_URL}/api/purchase-orders?status=pending", headers=headers)
        pending_pos = response.json()
        
        if not pending_pos:
            print("⚠ No pending POs to create GRN from")
            return
        
        po = pending_pos[0]
        
        # Get suppliers for the GRN
        response = requests.get(f"{BASE_URL}/api/suppliers", headers=headers)
        suppliers = response.json()
        
        if not suppliers:
            print("⚠ No suppliers available")
            return
        
        # Create GRN from PO
        grn_data = {
            "supplier_id": po["supplier_id"],
            "reference_number": po["order_number"],
            "received_date": datetime.now().strftime("%Y-%m-%d"),
            "notes": f"Created from Purchase Order {po['order_number']}",
            "sync_to_woo": False,  # Don't sync for testing
            "po_id": po["id"],  # Link to PO
            "items": [
                {
                    "product_id": item.get("product_id"),
                    "product_name": item["product_name"],
                    "sku": item.get("sku", ""),
                    "quantity": item["quantity"],
                    "cost_price": item["unit_price"],
                    "regular_price": item["unit_price"] * 1.3,  # 30% markup
                    "visibility": "public"
                }
                for item in po["items"]
            ]
        }
        
        response = requests.post(f"{BASE_URL}/api/grn", headers=headers, json=grn_data)
        
        assert response.status_code == 200, f"Create GRN from PO failed: {response.text}"
        data = response.json()
        assert "grn_number" in data
        assert data["items_count"] == len(po["items"])
        print(f"✓ Created GRN from PO: {data['grn_number']}")
        
        # Verify PO status was updated to 'received'
        response = requests.get(f"{BASE_URL}/api/purchase-orders/{po['id']}", headers=headers)
        updated_po = response.json()
        assert updated_po["status"] == "received", f"PO status not updated: {updated_po['status']}"
        print(f"✓ PO status updated to 'received'")
        
        return data


class TestProducts:
    """Product tests for GRN SKU field behavior"""
    
    def test_get_products(self, auth_token):
        """Test getting products list"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.get(f"{BASE_URL}/api/products", headers=headers)
        
        assert response.status_code == 200
        products = response.json()
        assert isinstance(products, list)
        print(f"✓ Retrieved {len(products)} products")
        return products
    
    def test_product_has_sku(self, auth_token):
        """Test that products have SKU field"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.get(f"{BASE_URL}/api/products", headers=headers)
        products = response.json()
        
        if not products:
            print("⚠ No products to test SKU")
            return
        
        # Check that products have SKU
        for product in products[:5]:  # Check first 5
            assert "sku" in product, f"Product {product['name']} missing SKU"
            if product["sku"]:
                print(f"  - {product['name']}: SKU={product['sku']}")
        
        print(f"✓ Products have SKU field")


class TestDashboardAndLogin:
    """Dashboard and login tests"""
    
    def test_login_success(self):
        """Test login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        print(f"✓ Login successful for {TEST_EMAIL}")
    
    def test_dashboard_summary(self, auth_token):
        """Test dashboard summary endpoint"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.get(f"{BASE_URL}/api/dashboard/summary", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "products_count" in data
        assert "customers_count" in data
        assert "suppliers_count" in data
        print(f"✓ Dashboard summary: {data['products_count']} products, {data['suppliers_count']} suppliers")


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
