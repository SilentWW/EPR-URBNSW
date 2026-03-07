"""
RM Procurement Module Tests
Tests for RM Suppliers, RM Purchase Orders, RM GRN, and RM GRN Returns
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    BASE_URL = "https://hr-system-build.preview.emergentagent.com"

TEST_CREDENTIALS = {
    "email": "lahiruraja97@gmail.com",
    "password": "password123"
}


def get_auth_token():
    """Get auth token from login"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json=TEST_CREDENTIALS
    )
    if response.status_code == 200:
        data = response.json()
        return data.get("access_token") or data.get("token")
    return None


def get_auth_headers():
    """Get authorization headers"""
    token = get_auth_token()
    if token:
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    return {"Content-Type": "application/json"}


class TestRMProcurementAuth:
    """Test authentication and setup"""
    
    def test_login_success(self):
        """Test login with valid credentials"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json=TEST_CREDENTIALS
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        # API returns access_token instead of token
        assert "access_token" in data or "token" in data, f"No token in response: {data.keys()}"
        assert "user" in data
        print(f"Login successful - User: {data['user'].get('email')}, Role: {data['user'].get('role')}")


class TestRMSuppliers:
    """Test RM Suppliers CRUD operations"""
    
    def test_get_rm_suppliers(self):
        """Test fetching RM suppliers list"""
        headers = get_auth_headers()
        response = requests.get(
            f"{BASE_URL}/api/rm-procurement/suppliers",
            headers=headers
        )
        assert response.status_code == 200, f"Failed to get suppliers: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"Found {len(data)} RM suppliers")
        for s in data[:3]:
            print(f"  - {s.get('name')}: {s.get('default_payment_terms')}")
        
    def test_create_rm_supplier(self):
        """Test creating a new RM supplier"""
        headers = get_auth_headers()
        supplier_data = {
            "name": f"TEST_RM_Supplier_{int(time.time())}",
            "contact_person": "John Doe",
            "email": "test_rm@supplier.com",
            "phone": "+94771234567",
            "address": "123 Test Street",
            "default_payment_terms": "net_30",
            "notes": "Test supplier for pytest"
        }
        response = requests.post(
            f"{BASE_URL}/api/rm-procurement/suppliers",
            headers=headers,
            json=supplier_data
        )
        assert response.status_code == 200, f"Failed to create supplier: {response.text}"
        data = response.json()
        assert "id" in data, "No ID returned for created supplier"
        assert data.get("message") == "Supplier created successfully"
        print(f"Created RM supplier with ID: {data['id']}")
        return data['id']
    
    def test_get_rm_supplier_by_id(self):
        """Test fetching a single RM supplier with stats"""
        headers = get_auth_headers()
        # First get the list and pick one
        response = requests.get(
            f"{BASE_URL}/api/rm-procurement/suppliers",
            headers=headers
        )
        assert response.status_code == 200
        suppliers = response.json()
        
        if suppliers:
            supplier_id = suppliers[0]['id']
            response = requests.get(
                f"{BASE_URL}/api/rm-procurement/suppliers/{supplier_id}",
                headers=headers
            )
            assert response.status_code == 200, f"Failed to get supplier: {response.text}"
            data = response.json()
            assert data['id'] == supplier_id
            assert 'total_orders' in data
            assert 'total_amount' in data
            assert 'outstanding_balance' in data
            print(f"Supplier {data['name']} - Total orders: {data['total_orders']}, Outstanding: {data['outstanding_balance']}")
        else:
            print("No suppliers found to test")
    
    def test_update_rm_supplier(self):
        """Test updating an RM supplier"""
        headers = get_auth_headers()
        # Get a test supplier
        response = requests.get(
            f"{BASE_URL}/api/rm-procurement/suppliers?search=TEST_RM",
            headers=headers
        )
        suppliers = response.json()
        
        if suppliers and len(suppliers) > 0:
            supplier_id = suppliers[0]['id']
            update_data = {
                "contact_person": "Jane Updated",
                "phone": "+94779876543"
            }
            response = requests.put(
                f"{BASE_URL}/api/rm-procurement/suppliers/{supplier_id}",
                headers=headers,
                json=update_data
            )
            assert response.status_code == 200, f"Failed to update supplier: {response.text}"
            print(f"Updated RM supplier {supplier_id}")
        else:
            print("No test suppliers found to update")
    
    def test_search_rm_suppliers(self):
        """Test searching RM suppliers"""
        headers = get_auth_headers()
        response = requests.get(
            f"{BASE_URL}/api/rm-procurement/suppliers?search=TEST",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        print(f"Found {len(data)} suppliers matching 'TEST'")


class TestRMPurchaseOrders:
    """Test RM Purchase Orders operations"""
    
    def test_get_rm_purchase_orders(self):
        """Test fetching RM purchase orders list"""
        headers = get_auth_headers()
        response = requests.get(
            f"{BASE_URL}/api/rm-procurement/purchase-orders",
            headers=headers
        )
        assert response.status_code == 200, f"Failed to get POs: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"Found {len(data)} RM purchase orders")
        for po in data[:3]:
            print(f"  - {po.get('po_number')}: {po.get('status')}, Total: {po.get('total')}")
        return data
    
    def test_get_rm_purchase_orders_by_status(self):
        """Test filtering POs by status"""
        headers = get_auth_headers()
        for status in ['draft', 'approved', 'partially_received', 'completed']:
            response = requests.get(
                f"{BASE_URL}/api/rm-procurement/purchase-orders?status={status}",
                headers=headers
            )
            assert response.status_code == 200, f"Failed to get {status} POs: {response.text}"
            data = response.json()
            print(f"Found {len(data)} {status} POs")
    
    def test_create_rm_purchase_order(self):
        """Test creating a new RM purchase order"""
        headers = get_auth_headers()
        # First get supplier and raw materials
        suppliers_res = requests.get(
            f"{BASE_URL}/api/rm-procurement/suppliers",
            headers=headers
        )
        suppliers = suppliers_res.json()
        
        materials_res = requests.get(
            f"{BASE_URL}/api/manufacturing/raw-materials",
            headers=headers
        )
        materials = materials_res.json()
        
        if not suppliers or len(suppliers) == 0:
            pytest.skip("No suppliers available for PO creation")
        if not materials or len(materials) == 0:
            pytest.skip("No raw materials available for PO creation")
        
        po_data = {
            "supplier_id": suppliers[0]['id'],
            "items": [
                {
                    "raw_material_id": materials[0]['id'],
                    "quantity": 100,
                    "unit_price": materials[0].get('cost_price', 50)
                }
            ],
            "payment_terms": "net_30",
            "priority": "normal",
            "notes": "Test PO from pytest"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/rm-procurement/purchase-orders",
            headers=headers,
            json=po_data
        )
        assert response.status_code == 200, f"Failed to create PO: {response.text}"
        data = response.json()
        assert "id" in data
        assert "po_number" in data
        print(f"Created PO: {data['po_number']} - Total: {data.get('total')}")
        return data['id']
    
    def test_get_rm_purchase_order_by_id(self):
        """Test fetching a single PO with details"""
        headers = get_auth_headers()
        # Get list first
        response = requests.get(
            f"{BASE_URL}/api/rm-procurement/purchase-orders",
            headers=headers
        )
        pos = response.json()
        
        if pos and len(pos) > 0:
            po_id = pos[0]['id']
            response = requests.get(
                f"{BASE_URL}/api/rm-procurement/purchase-orders/{po_id}",
                headers=headers
            )
            assert response.status_code == 200, f"Failed to get PO: {response.text}"
            data = response.json()
            assert data['id'] == po_id
            assert 'items' in data
            assert 'supplier' in data
            print(f"PO {data['po_number']} - Status: {data['status']}, Payment: {data['payment_status']}")
            print(f"  Items: {len(data['items'])}, GRN History: {len(data.get('grn_history', []))}")
        else:
            print("No POs found to test")
    
    def test_approve_rm_purchase_order(self):
        """Test approving a draft PO"""
        headers = get_auth_headers()
        # Get draft POs
        response = requests.get(
            f"{BASE_URL}/api/rm-procurement/purchase-orders?status=draft",
            headers=headers
        )
        draft_pos = response.json()
        
        if draft_pos and len(draft_pos) > 0:
            po_id = draft_pos[0]['id']
            response = requests.post(
                f"{BASE_URL}/api/rm-procurement/purchase-orders/{po_id}/approve",
                headers=headers
            )
            assert response.status_code == 200, f"Failed to approve PO: {response.text}"
            data = response.json()
            assert data.get("new_status") == "approved"
            print(f"Approved PO {po_id}")
        else:
            print("No draft POs available to approve")


class TestRMGRN:
    """Test RM GRN (Goods Received) operations"""
    
    def test_get_rm_grns(self):
        """Test fetching GRNs list"""
        headers = get_auth_headers()
        response = requests.get(
            f"{BASE_URL}/api/rm-procurement/grn",
            headers=headers
        )
        assert response.status_code == 200, f"Failed to get GRNs: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} RM GRNs")
        for grn in data[:3]:
            print(f"  - {grn.get('grn_number')}: Status: {grn.get('status')}, Total: {grn.get('total_cost')}")
        return data
    
    def test_create_rm_grn(self):
        """Test receiving goods against an approved PO"""
        headers = get_auth_headers()
        # Get approved POs
        response = requests.get(
            f"{BASE_URL}/api/rm-procurement/purchase-orders?status=approved",
            headers=headers
        )
        approved_pos = response.json()
        
        # Also check partially received
        response2 = requests.get(
            f"{BASE_URL}/api/rm-procurement/purchase-orders?status=partially_received",
            headers=headers
        )
        partial_pos = response2.json()
        all_pos = approved_pos + partial_pos
        
        if not all_pos or len(all_pos) == 0:
            pytest.skip("No approved POs available for GRN creation")
        
        # Get full PO details
        po_id = all_pos[0]['id']
        response = requests.get(
            f"{BASE_URL}/api/rm-procurement/purchase-orders/{po_id}",
            headers=headers
        )
        po = response.json()
        
        # Find items that can be received
        items_to_receive = []
        for idx, item in enumerate(po['items']):
            remaining = item['quantity'] - item.get('received_quantity', 0)
            if remaining > 0:
                items_to_receive.append({
                    "raw_material_id": item['raw_material_id'],
                    "po_item_index": idx,
                    "received_quantity": min(remaining, 10),  # Receive up to 10 units
                    "unit_price": item['unit_price']
                })
        
        if not items_to_receive:
            pytest.skip("All items in available POs fully received")
        
        grn_data = {
            "rm_po_id": po_id,
            "items": items_to_receive,
            "received_date": "2026-03-07",
            "reference_number": "TEST-REF-001",
            "notes": "Test GRN from pytest"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/rm-procurement/grn",
            headers=headers,
            json=grn_data
        )
        assert response.status_code == 200, f"Failed to create GRN: {response.text}"
        data = response.json()
        assert "id" in data
        assert "grn_number" in data
        print(f"Created GRN: {data['grn_number']} - Total: {data.get('total_cost')}, PO Status: {data.get('po_status')}")
    
    def test_get_rm_grn_by_id(self):
        """Test fetching a single GRN with returns"""
        headers = get_auth_headers()
        response = requests.get(
            f"{BASE_URL}/api/rm-procurement/grn",
            headers=headers
        )
        grns = response.json()
        
        if grns and len(grns) > 0:
            grn_id = grns[0]['id']
            response = requests.get(
                f"{BASE_URL}/api/rm-procurement/grn/{grn_id}",
                headers=headers
            )
            assert response.status_code == 200, f"Failed to get GRN: {response.text}"
            data = response.json()
            assert data['id'] == grn_id
            assert 'items' in data
            assert 'returns' in data
            print(f"GRN {data['grn_number']} - Status: {data['status']}, Returns: {len(data.get('returns', []))}")
        else:
            print("No GRNs found to test")


class TestRMGRNReturns:
    """Test RM GRN Returns operations"""
    
    def test_get_rm_grn_returns(self):
        """Test fetching GRN returns list"""
        headers = get_auth_headers()
        response = requests.get(
            f"{BASE_URL}/api/rm-procurement/grn-returns",
            headers=headers
        )
        assert response.status_code == 200, f"Failed to get returns: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} RM GRN returns")
        for ret in data[:3]:
            print(f"  - {ret.get('return_number')}: Settlement: {ret.get('settlement_type')}, Total: {ret.get('total_cost')}")
    
    def test_create_rm_grn_return_credit(self):
        """Test creating a GRN return with credit settlement"""
        headers = get_auth_headers()
        # Get GRNs that can have returns
        response = requests.get(
            f"{BASE_URL}/api/rm-procurement/grn",
            headers=headers
        )
        all_grns = response.json()
        grns = [g for g in all_grns if g.get('status') != 'returned']
        
        if not grns or len(grns) == 0:
            pytest.skip("No GRNs available for returns")
        
        # Get full GRN details
        grn_id = grns[0]['id']
        response = requests.get(
            f"{BASE_URL}/api/rm-procurement/grn/{grn_id}",
            headers=headers
        )
        grn = response.json()
        
        # Find items that can be returned
        items_to_return = []
        returned_map = {}
        for ret in grn.get('returns', []):
            for item in ret.get('items', []):
                rm_id = item.get('raw_material_id')
                returned_map[rm_id] = returned_map.get(rm_id, 0) + item.get('return_quantity', 0)
        
        for item in grn['items']:
            rm_id = item['raw_material_id']
            already_returned = returned_map.get(rm_id, 0)
            returnable = item['received_quantity'] - already_returned
            if returnable > 0:
                items_to_return.append({
                    "raw_material_id": rm_id,
                    "return_quantity": min(returnable, 2),  # Return up to 2 units
                    "reason": "Test return - quality issue"
                })
        
        if not items_to_return:
            pytest.skip("All items already returned from available GRNs")
        
        return_data = {
            "rm_grn_id": grn_id,
            "items": items_to_return,
            "settlement_type": "credit",  # Test credit settlement
            "notes": "Test return from pytest - credit"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/rm-procurement/grn-returns",
            headers=headers,
            json=return_data
        )
        assert response.status_code == 200, f"Failed to create return: {response.text}"
        data = response.json()
        assert "id" in data
        assert "return_number" in data
        print(f"Created Return: {data['return_number']} - Total: {data.get('total_cost')}, GRN Status: {data.get('grn_status')}")


class TestRMAccountsPayable:
    """Test RM Accounts Payable"""
    
    def test_get_rm_accounts_payable(self):
        """Test fetching RM accounts payable"""
        headers = get_auth_headers()
        response = requests.get(
            f"{BASE_URL}/api/rm-procurement/accounts-payable",
            headers=headers
        )
        assert response.status_code == 200, f"Failed to get AP: {response.text}"
        data = response.json()
        assert 'items' in data
        assert 'total_payable' in data
        print(f"Total payable: {data['total_payable']} - Items: {len(data['items'])}")
        for item in data['items'][:3]:
            print(f"  - PO {item.get('po_number')}: Balance: {item.get('balance')}, Terms: {item.get('payment_terms')}")


class TestRMProcurementCleanup:
    """Cleanup test data"""
    
    def test_cleanup_test_suppliers(self):
        """Cleanup test suppliers without orders"""
        headers = get_auth_headers()
        response = requests.get(
            f"{BASE_URL}/api/rm-procurement/suppliers?search=TEST_RM",
            headers=headers
        )
        test_suppliers = response.json()
        
        deleted_count = 0
        for supplier in test_suppliers:
            # Try to delete (will fail if has orders - that's OK)
            response = requests.delete(
                f"{BASE_URL}/api/rm-procurement/suppliers/{supplier['id']}",
                headers=headers
            )
            if response.status_code == 200:
                print(f"Deleted test supplier: {supplier['name']}")
                deleted_count += 1
            else:
                print(f"Could not delete supplier {supplier['name']}: has orders")
        print(f"Cleanup completed: {deleted_count} test suppliers deleted")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
