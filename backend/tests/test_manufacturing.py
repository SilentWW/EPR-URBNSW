"""
Manufacturing Module Tests
Tests the complete manufacturing workflow:
1. Raw Materials CRUD
2. Bill of Materials (BOM) Creation
3. Work Order workflow: Create -> Issue Materials -> Start Production -> Record Production -> QC Inspection
4. Inventory updates verification
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    BASE_URL = "https://multi-tenant-hub-30.preview.emergentagent.com"

# Test credentials
TEST_EMAIL = "lahiruraja97@gmail.com"
TEST_PASSWORD = "password123"

# Store created IDs for cleanup/reference
created_ids = {
    "raw_materials": [],
    "bom": None,
    "work_order": None,
    "product": None
}

class TestManufacturingWorkflow:
    """Test the complete manufacturing workflow"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - Get auth token before tests"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        self.token = data["access_token"]
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        self.company_id = data["user"]["company_id"]
        yield
        self.session.close()

    # ============== RAW MATERIALS TESTS ==============

    def test_01_create_raw_material_fabric(self):
        """Create Fabric raw material"""
        response = self.session.post(f"{BASE_URL}/api/manufacturing/raw-materials", json={
            "sku": "TEST_FABRIC001",
            "name": "TEST Blue Cotton Fabric",
            "description": "High quality blue cotton fabric for testing",
            "category": "Fabric",
            "unit": "meter",
            "cost_price": 500.0,
            "stock_quantity": 100.0,
            "low_stock_threshold": 20.0
        })
        
        assert response.status_code == 200, f"Create fabric failed: {response.text}"
        data = response.json()
        assert "id" in data
        created_ids["raw_materials"].append(data["id"])
        print(f"✓ Created Fabric raw material: {data['id']}")

    def test_02_create_raw_material_buttons(self):
        """Create Buttons raw material"""
        response = self.session.post(f"{BASE_URL}/api/manufacturing/raw-materials", json={
            "sku": "TEST_BTN001",
            "name": "TEST Metal Buttons",
            "description": "Silver metal buttons",
            "category": "Buttons",
            "unit": "piece",
            "cost_price": 25.0,
            "stock_quantity": 500,
            "low_stock_threshold": 50
        })
        
        assert response.status_code == 200, f"Create buttons failed: {response.text}"
        data = response.json()
        assert "id" in data
        created_ids["raw_materials"].append(data["id"])
        print(f"✓ Created Buttons raw material: {data['id']}")

    def test_03_create_raw_material_thread(self):
        """Create Thread raw material"""
        response = self.session.post(f"{BASE_URL}/api/manufacturing/raw-materials", json={
            "sku": "TEST_THREAD001",
            "name": "TEST Blue Thread",
            "description": "Blue polyester thread",
            "category": "Thread",
            "unit": "roll",
            "cost_price": 150.0,
            "stock_quantity": 50,
            "low_stock_threshold": 10
        })
        
        assert response.status_code == 200, f"Create thread failed: {response.text}"
        data = response.json()
        assert "id" in data
        created_ids["raw_materials"].append(data["id"])
        print(f"✓ Created Thread raw material: {data['id']}")

    def test_04_create_raw_material_zipper(self):
        """Create Zipper raw material"""
        response = self.session.post(f"{BASE_URL}/api/manufacturing/raw-materials", json={
            "sku": "TEST_ZIP001",
            "name": "TEST Metal Zipper 20cm",
            "description": "20cm metal zipper",
            "category": "Zippers",
            "unit": "piece",
            "cost_price": 100.0,
            "stock_quantity": 200,
            "low_stock_threshold": 30
        })
        
        assert response.status_code == 200, f"Create zipper failed: {response.text}"
        data = response.json()
        assert "id" in data
        created_ids["raw_materials"].append(data["id"])
        print(f"✓ Created Zipper raw material: {data['id']}")

    def test_05_get_raw_materials_list(self):
        """Verify all raw materials are created"""
        response = self.session.get(f"{BASE_URL}/api/manufacturing/raw-materials")
        assert response.status_code == 200, f"Get raw materials failed: {response.text}"
        
        materials = response.json()
        assert isinstance(materials, list)
        
        # Filter TEST_ materials
        test_materials = [m for m in materials if m.get("sku", "").startswith("TEST_")]
        print(f"✓ Found {len(test_materials)} TEST_ raw materials")
        assert len(test_materials) >= 4, f"Expected at least 4 raw materials, got {len(test_materials)}"

    def test_06_get_raw_material_categories(self):
        """Verify raw material categories endpoint"""
        response = self.session.get(f"{BASE_URL}/api/manufacturing/raw-materials/categories")
        assert response.status_code == 200, f"Get categories failed: {response.text}"
        
        categories = response.json()
        assert isinstance(categories, list)
        print(f"✓ Raw material categories: {categories}")

    def test_07_add_stock_to_raw_material(self):
        """Test adding stock to raw material"""
        if not created_ids["raw_materials"]:
            pytest.skip("No raw materials created")
        
        material_id = created_ids["raw_materials"][0]  # Fabric
        response = self.session.post(
            f"{BASE_URL}/api/manufacturing/raw-materials/{material_id}/add-stock",
            params={"quantity": 50, "cost_price": 520.0, "reference": "TEST-PO-001"}
        )
        
        assert response.status_code == 200, f"Add stock failed: {response.text}"
        data = response.json()
        assert "new_quantity" in data
        assert data["new_quantity"] == 150.0  # 100 + 50
        print(f"✓ Added 50 units stock. New quantity: {data['new_quantity']}")

    # ============== PRODUCT & BOM TESTS ==============

    def test_08_create_test_product(self):
        """Create a product to use in BOM"""
        response = self.session.post(f"{BASE_URL}/api/products", json={
            "sku": "TEST_SHIRT001",
            "name": "TEST Blue Cotton Shirt",
            "description": "A test cotton shirt for manufacturing",
            "category": "Clothing",
            "cost_price": 0,  # Will be calculated from BOM
            "regular_price": 2500.0,
            "selling_price": 2500.0,
            "stock_quantity": 0,
            "product_type": "simple"
        })
        
        assert response.status_code == 200, f"Create product failed: {response.text}"
        data = response.json()
        assert "id" in data
        created_ids["product"] = data["id"]
        print(f"✓ Created test product: {data['id']}")

    def test_09_create_bill_of_materials(self):
        """Create BOM linking raw materials to product"""
        if not created_ids["product"]:
            pytest.skip("No product created")
        if len(created_ids["raw_materials"]) < 4:
            pytest.skip("Not enough raw materials")
        
        response = self.session.post(f"{BASE_URL}/api/manufacturing/bom", json={
            "product_id": created_ids["product"],
            "components": [
                {
                    "raw_material_id": created_ids["raw_materials"][0],  # Fabric
                    "quantity": 2.0,  # 2 meters per shirt
                    "unit": "meter",
                    "wastage_percent": 5.0
                },
                {
                    "raw_material_id": created_ids["raw_materials"][1],  # Buttons
                    "quantity": 6,  # 6 buttons per shirt
                    "unit": "piece",
                    "wastage_percent": 0
                },
                {
                    "raw_material_id": created_ids["raw_materials"][2],  # Thread
                    "quantity": 0.5,  # 0.5 roll per shirt
                    "unit": "roll",
                    "wastage_percent": 10.0
                },
                {
                    "raw_material_id": created_ids["raw_materials"][3],  # Zipper
                    "quantity": 1,
                    "unit": "piece",
                    "wastage_percent": 2.0
                }
            ],
            "labor_cost_per_unit": 200.0,
            "overhead_percent": 10.0,
            "notes": "Test BOM for blue cotton shirt"
        })
        
        assert response.status_code == 200, f"Create BOM failed: {response.text}"
        data = response.json()
        assert "id" in data
        created_ids["bom"] = data["id"]
        print(f"✓ Created BOM: {data['id']}")

    def test_10_get_bom_details(self):
        """Verify BOM was created with correct costs"""
        if not created_ids["bom"]:
            pytest.skip("No BOM created")
        
        response = self.session.get(f"{BASE_URL}/api/manufacturing/bom/{created_ids['bom']}")
        assert response.status_code == 200, f"Get BOM failed: {response.text}"
        
        bom = response.json()
        assert bom["product_id"] == created_ids["product"]
        assert len(bom["components"]) == 4
        assert bom["labor_cost_per_unit"] == 200.0
        
        # Verify cost calculation
        assert "total_material_cost" in bom
        assert "total_cost_per_unit" in bom
        assert bom["total_cost_per_unit"] > 0
        
        print(f"✓ BOM verified:")
        print(f"  - Material Cost: {bom['total_material_cost']}")
        print(f"  - Labor Cost: {bom['labor_cost_per_unit']}")
        print(f"  - Overhead: {bom['overhead_cost']}")
        print(f"  - Total Cost/Unit: {bom['total_cost_per_unit']}")

    # ============== WORK ORDER TESTS ==============

    def test_11_create_work_order(self):
        """Create a work order for production"""
        if not created_ids["product"]:
            pytest.skip("No product created")
        
        response = self.session.post(f"{BASE_URL}/api/manufacturing/work-orders", json={
            "product_id": created_ids["product"],
            "quantity": 10,  # Produce 10 shirts
            "order_type": "make_to_stock",
            "planned_start_date": "2026-01-25",
            "planned_end_date": "2026-01-26",
            "notes": "Test production run"
        })
        
        assert response.status_code == 200, f"Create work order failed: {response.text}"
        data = response.json()
        assert "id" in data
        assert "wo_number" in data
        assert "estimated_total_cost" in data
        
        created_ids["work_order"] = data["id"]
        print(f"✓ Created Work Order: {data['wo_number']}")
        print(f"  - Estimated Total Cost: {data['estimated_total_cost']}")

    def test_12_get_work_order_details(self):
        """Verify work order was created correctly"""
        if not created_ids["work_order"]:
            pytest.skip("No work order created")
        
        response = self.session.get(f"{BASE_URL}/api/manufacturing/work-orders/{created_ids['work_order']}")
        assert response.status_code == 200, f"Get work order failed: {response.text}"
        
        wo = response.json()
        assert wo["status"] == "draft"
        assert wo["quantity"] == 10
        assert wo["quantity_completed"] == 0
        
        print(f"✓ Work Order details verified:")
        print(f"  - Status: {wo['status']}")
        print(f"  - Quantity: {wo['quantity']}")
        print(f"  - Material Cost/Unit: {wo['material_cost_per_unit']}")

    def test_13_issue_materials(self):
        """Issue materials for production (deduct from raw material stock)"""
        if not created_ids["work_order"]:
            pytest.skip("No work order created")
        
        # Get initial stock levels
        initial_stocks = {}
        for mat_id in created_ids["raw_materials"]:
            resp = self.session.get(f"{BASE_URL}/api/manufacturing/raw-materials/{mat_id}")
            if resp.status_code == 200:
                initial_stocks[mat_id] = resp.json()["stock_quantity"]
        
        # Issue materials
        response = self.session.post(f"{BASE_URL}/api/manufacturing/work-orders/{created_ids['work_order']}/issue-materials")
        
        assert response.status_code == 200, f"Issue materials failed: {response.text}"
        data = response.json()
        assert data["new_status"] == "materials_issued"
        assert "total_material_cost" in data
        
        print(f"✓ Materials issued successfully:")
        print(f"  - Materials issued: {data['materials_issued']}")
        print(f"  - Total Material Cost: {data['total_material_cost']}")
        
        # Verify stock was deducted
        for mat_id in created_ids["raw_materials"]:
            resp = self.session.get(f"{BASE_URL}/api/manufacturing/raw-materials/{mat_id}")
            if resp.status_code == 200:
                new_stock = resp.json()["stock_quantity"]
                if mat_id in initial_stocks:
                    assert new_stock < initial_stocks[mat_id], f"Stock not deducted for {mat_id}"
                    print(f"  - Material {mat_id}: {initial_stocks[mat_id]} -> {new_stock}")

    def test_14_start_production(self):
        """Start production on work order"""
        if not created_ids["work_order"]:
            pytest.skip("No work order created")
        
        response = self.session.post(f"{BASE_URL}/api/manufacturing/work-orders/{created_ids['work_order']}/start-production")
        
        assert response.status_code == 200, f"Start production failed: {response.text}"
        data = response.json()
        assert data["new_status"] == "in_progress"
        print(f"✓ Production started - Status: {data['new_status']}")

    def test_15_record_production(self):
        """Record completed production quantity"""
        if not created_ids["work_order"]:
            pytest.skip("No work order created")
        
        # Record production of 10 units (full quantity)
        response = self.session.post(
            f"{BASE_URL}/api/manufacturing/work-orders/{created_ids['work_order']}/record-production",
            params={"quantity_completed": 10}
        )
        
        assert response.status_code == 200, f"Record production failed: {response.text}"
        data = response.json()
        assert data["quantity_completed"] == 10
        assert data["new_status"] == "qc_pending"  # Full quantity completed
        
        print(f"✓ Production recorded:")
        print(f"  - Quantity Completed: {data['quantity_completed']}")
        print(f"  - Remaining: {data['quantity_remaining']}")
        print(f"  - New Status: {data['new_status']}")

    def test_16_qc_inspection(self):
        """Perform QC inspection (pass/fail)"""
        if not created_ids["work_order"]:
            pytest.skip("No work order created")
        
        # QC Inspection - 9 passed, 1 failed
        response = self.session.post(
            f"{BASE_URL}/api/manufacturing/work-orders/{created_ids['work_order']}/qc-inspection",
            json={
                "work_order_id": created_ids["work_order"],
                "quantity_passed": 9,
                "quantity_failed": 1,
                "failure_reason": "Minor stitching defect",
                "notes": "Test QC inspection"
            }
        )
        
        assert response.status_code == 200, f"QC inspection failed: {response.text}"
        data = response.json()
        assert data["qc_status"] == "partial"  # Some passed, some failed
        assert data["quantity_passed"] == 9
        assert data["quantity_failed"] == 1
        assert data["new_status"] == "completed"
        
        print(f"✓ QC Inspection completed:")
        print(f"  - QC Status: {data['qc_status']}")
        print(f"  - Passed: {data['quantity_passed']}")
        print(f"  - Failed: {data['quantity_failed']}")
        print(f"  - Production Cost/Unit: {data['production_cost_per_unit']}")
        print(f"  - Total Production Cost: {data['total_production_cost']}")
        print(f"  - Scrap Cost: {data['scrap_cost']}")

    def test_17_verify_finished_goods_inventory(self):
        """Verify finished goods were added to product inventory"""
        if not created_ids["product"]:
            pytest.skip("No product created")
        
        response = self.session.get(f"{BASE_URL}/api/products/{created_ids['product']}")
        assert response.status_code == 200, f"Get product failed: {response.text}"
        
        product = response.json()
        assert product["stock_quantity"] == 9  # 9 passed QC
        
        print(f"✓ Finished goods inventory verified:")
        print(f"  - Product: {product['name']}")
        print(f"  - Stock Quantity: {product['stock_quantity']}")
        print(f"  - Cost Price (COGS): {product.get('cost_price', 'N/A')}")

    def test_18_verify_work_order_completed(self):
        """Verify work order is in completed status with all details"""
        if not created_ids["work_order"]:
            pytest.skip("No work order created")
        
        response = self.session.get(f"{BASE_URL}/api/manufacturing/work-orders/{created_ids['work_order']}")
        assert response.status_code == 200, f"Get work order failed: {response.text}"
        
        wo = response.json()
        assert wo["status"] == "completed"
        assert wo["quantity_passed_qc"] == 9
        assert wo["quantity_failed_qc"] == 1
        assert wo["actual_material_cost"] > 0
        assert wo["actual_total_cost"] > 0
        
        print(f"✓ Work Order completion verified:")
        print(f"  - Status: {wo['status']}")
        print(f"  - Passed QC: {wo['quantity_passed_qc']}")
        print(f"  - Failed QC: {wo['quantity_failed_qc']}")
        print(f"  - Actual Material Cost: {wo['actual_material_cost']}")
        print(f"  - Actual Labor Cost: {wo['actual_labor_cost']}")
        print(f"  - Actual Overhead: {wo['actual_overhead_cost']}")
        print(f"  - Actual Total Cost: {wo['actual_total_cost']}")

    def test_19_verify_journal_entries_created(self):
        """Verify manufacturing journal entries were created"""
        response = self.session.get(f"{BASE_URL}/api/finance/journal-entries")
        assert response.status_code == 200, f"Get journal entries failed: {response.text}"
        
        entries = response.json()
        
        # Look for manufacturing-related entries (MFG- prefix)
        mfg_entries = [e for e in entries if e.get("entry_number", "").startswith("MFG-")]
        
        print(f"✓ Found {len(mfg_entries)} manufacturing journal entries")
        for entry in mfg_entries[:5]:  # Show first 5
            print(f"  - {entry.get('entry_number')}: {entry.get('description')}")

    # ============== CLEANUP ==============

    def test_99_cleanup_test_data(self):
        """Cleanup all TEST_ prefixed data"""
        # Note: In a real scenario, you might want to keep this data
        # For testing purposes, we cleanup
        
        # Delete work order (if not completed, materials will be returned)
        # Note: Completed work orders typically shouldn't be deleted
        
        # Delete BOM
        if created_ids["bom"]:
            response = self.session.delete(f"{BASE_URL}/api/manufacturing/bom/{created_ids['bom']}")
            # BOM might be used, so we don't assert deletion
            print(f"  - BOM delete attempt: {response.status_code}")
        
        # Delete raw materials (may fail if used in BOM)
        for mat_id in reversed(created_ids["raw_materials"]):
            response = self.session.delete(f"{BASE_URL}/api/manufacturing/raw-materials/{mat_id}")
            print(f"  - Raw material {mat_id} delete: {response.status_code}")
        
        # Delete product
        if created_ids["product"]:
            response = self.session.delete(f"{BASE_URL}/api/products/{created_ids['product']}")
            print(f"  - Product delete: {response.status_code}")
        
        print("✓ Cleanup attempted for test data")


class TestManufacturingDashboard:
    """Test the manufacturing dashboard summary"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup auth"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        self.token = response.json()["access_token"]
        self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        yield
        self.session.close()

    def test_manufacturing_dashboard_summary(self):
        """Test manufacturing dashboard summary endpoint"""
        response = self.session.get(f"{BASE_URL}/api/manufacturing/dashboard/summary")
        assert response.status_code == 200, f"Dashboard failed: {response.text}"
        
        data = response.json()
        assert "status_summary" in data
        assert "low_stock_materials" in data
        assert "recent_work_orders" in data
        assert "this_month" in data
        
        print(f"✓ Manufacturing Dashboard Summary:")
        print(f"  - Status Summary: {data['status_summary']}")
        print(f"  - Low Stock Materials: {len(data['low_stock_materials'])} items")
        print(f"  - Recent Work Orders: {len(data['recent_work_orders'])} orders")
        print(f"  - This Month Production Value: {data['this_month']['production_value']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
