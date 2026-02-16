#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime
import uuid

class ERPSystemTester:
    def __init__(self, base_url="https://accounting-module-v2.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.user_id = None
        self.company_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failed_tests = []
        self.test_results = []

    def log_test(self, name, success, details="", error=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
        else:
            print(f"❌ {name} - {error}")
            self.failed_tests.append({"test": name, "error": error})
        
        self.test_results.append({
            "test": name,
            "success": success,
            "details": details,
            "error": error
        })

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        
        if headers:
            test_headers.update(headers)

        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=30)

            success = response.status_code == expected_status
            
            if success:
                try:
                    response_data = response.json() if response.content else {}
                    self.log_test(name, True, f"Status: {response.status_code}")
                    return True, response_data
                except:
                    self.log_test(name, True, f"Status: {response.status_code}, No JSON response")
                    return True, {}
            else:
                error_msg = f"Expected {expected_status}, got {response.status_code}"
                try:
                    error_detail = response.json().get('detail', '')
                    if error_detail:
                        error_msg += f" - {error_detail}"
                except:
                    pass
                self.log_test(name, False, error=error_msg)
                return False, {}

        except requests.exceptions.RequestException as e:
            self.log_test(name, False, error=f"Request failed: {str(e)}")
            return False, {}
        except Exception as e:
            self.log_test(name, False, error=f"Unexpected error: {str(e)}")
            return False, {}

    def test_user_registration(self):
        """Test user registration"""
        timestamp = datetime.now().strftime('%H%M%S')
        test_data = {
            "full_name": f"Test User {timestamp}",
            "email": f"test{timestamp}@example.com",
            "password": "TestPass123!",
            "company_name": f"Test Company {timestamp}"
        }
        
        success, response = self.run_test(
            "User Registration",
            "POST",
            "auth/register",
            200,
            test_data
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_id = response['user']['id']
            self.company_id = response['user']['company_id']
            return True
        return False

    def test_user_login(self):
        """Test user login with existing credentials"""
        # Try to login with demo credentials first
        login_data = {
            "email": "demo@example.com",
            "password": "demo123"
        }
        
        success, response = self.run_test(
            "User Login (Demo)",
            "POST", 
            "auth/login",
            200,
            login_data
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_id = response['user']['id']
            self.company_id = response['user']['company_id']
            return True
        return False

    def test_get_current_user(self):
        """Test get current user info"""
        success, response = self.run_test(
            "Get Current User",
            "GET",
            "auth/me",
            200
        )
        return success

    def test_dashboard_summary(self):
        """Test dashboard summary endpoint"""
        success, response = self.run_test(
            "Dashboard Summary",
            "GET",
            "dashboard/summary",
            200
        )
        return success

    def test_products_crud(self):
        """Test products CRUD operations"""
        # Get products list
        success, products = self.run_test(
            "Get Products List",
            "GET",
            "products",
            200
        )
        
        if not success:
            return False

        # Create a new product
        product_data = {
            "sku": f"TEST-{uuid.uuid4().hex[:8].upper()}",
            "name": "Test Product",
            "description": "Test product description",
            "category": "Test Category",
            "cost_price": 100.0,
            "selling_price": 150.0,
            "stock_quantity": 50,
            "low_stock_threshold": 10
        }
        
        success, product_response = self.run_test(
            "Create Product",
            "POST",
            "products",
            200,
            product_data
        )
        
        if not success:
            return False
            
        product_id = product_response.get('id')
        if not product_id:
            self.log_test("Create Product - Get ID", False, error="No product ID returned")
            return False

        # Get single product
        success, _ = self.run_test(
            "Get Single Product",
            "GET",
            f"products/{product_id}",
            200
        )
        
        if not success:
            return False

        # Update product
        update_data = {
            "name": "Updated Test Product",
            "selling_price": 175.0
        }
        
        success, _ = self.run_test(
            "Update Product",
            "PUT",
            f"products/{product_id}",
            200,
            update_data
        )
        
        if not success:
            return False

        # Delete product
        success, _ = self.run_test(
            "Delete Product",
            "DELETE",
            f"products/{product_id}",
            200
        )
        
        return success

    def test_customers_crud(self):
        """Test customers CRUD operations"""
        # Get customers list
        success, customers = self.run_test(
            "Get Customers List",
            "GET",
            "customers",
            200
        )
        
        if not success:
            return False

        # Create a new customer
        customer_data = {
            "name": "Test Customer",
            "email": f"customer{uuid.uuid4().hex[:8]}@example.com",
            "phone": "+94771234567",
            "address": "123 Test Street, Colombo"
        }
        
        success, customer_response = self.run_test(
            "Create Customer",
            "POST",
            "customers",
            200,
            customer_data
        )
        
        if not success:
            return False
            
        customer_id = customer_response.get('id')
        if not customer_id:
            self.log_test("Create Customer - Get ID", False, error="No customer ID returned")
            return False

        # Get single customer
        success, _ = self.run_test(
            "Get Single Customer",
            "GET",
            f"customers/{customer_id}",
            200
        )
        
        if not success:
            return False

        # Update customer
        update_data = {
            "name": "Updated Test Customer",
            "phone": "+94779876543"
        }
        
        success, _ = self.run_test(
            "Update Customer",
            "PUT",
            f"customers/{customer_id}",
            200,
            update_data
        )
        
        if not success:
            return False

        # Delete customer
        success, _ = self.run_test(
            "Delete Customer",
            "DELETE",
            f"customers/{customer_id}",
            200
        )
        
        return success

    def test_sales_orders(self):
        """Test sales orders functionality"""
        # First create a customer and product for the order
        customer_data = {
            "name": "Order Test Customer",
            "email": f"ordercust{uuid.uuid4().hex[:8]}@example.com"
        }
        
        success, customer_response = self.run_test(
            "Create Customer for Order",
            "POST",
            "customers",
            200,
            customer_data
        )
        
        if not success:
            return False
            
        customer_id = customer_response.get('id')
        
        product_data = {
            "sku": f"ORDER-{uuid.uuid4().hex[:8].upper()}",
            "name": "Order Test Product",
            "selling_price": 100.0,
            "stock_quantity": 10
        }
        
        success, product_response = self.run_test(
            "Create Product for Order",
            "POST",
            "products",
            200,
            product_data
        )
        
        if not success:
            return False
            
        product_id = product_response.get('id')

        # Create sales order
        order_data = {
            "customer_id": customer_id,
            "items": [{
                "product_id": product_id,
                "product_name": "Order Test Product",
                "sku": product_data["sku"],
                "quantity": 2,
                "unit_price": 100.0,
                "total": 200.0
            }],
            "discount": 0.0,
            "notes": "Test order"
        }
        
        success, order_response = self.run_test(
            "Create Sales Order",
            "POST",
            "sales-orders",
            200,
            order_data
        )
        
        if not success:
            return False
            
        order_id = order_response.get('id')

        # Get sales orders list
        success, _ = self.run_test(
            "Get Sales Orders List",
            "GET",
            "sales-orders",
            200
        )
        
        if not success:
            return False

        # Get single sales order
        success, _ = self.run_test(
            "Get Single Sales Order",
            "GET",
            f"sales-orders/{order_id}",
            200
        )
        
        return success

    def test_company_settings(self):
        """Test company settings"""
        # Get company info
        success, company = self.run_test(
            "Get Company Info",
            "GET",
            "company",
            200
        )
        
        if not success:
            return False

        # Update company info
        update_data = {
            "name": "Updated Test Company",
            "currency": "LKR",
            "timezone": "Asia/Colombo"
        }
        
        success, _ = self.run_test(
            "Update Company Info",
            "PUT",
            "company",
            200,
            update_data
        )
        
        return success

    def test_woocommerce_settings(self):
        """Test WooCommerce settings"""
        # Get WooCommerce settings
        success, _ = self.run_test(
            "Get WooCommerce Settings",
            "GET",
            "company/woocommerce",
            200
        )
        
        if not success:
            return False

        # Update WooCommerce settings
        woo_data = {
            "store_url": "https://test-store.com",
            "consumer_key": "ck_test_key",
            "consumer_secret": "cs_test_secret",
            "enabled": False
        }
        
        success, _ = self.run_test(
            "Update WooCommerce Settings",
            "PUT",
            "company/woocommerce",
            200,
            woo_data
        )
        
        return success

    def test_inventory_endpoints(self):
        """Test inventory related endpoints"""
        # Get low stock products
        success, _ = self.run_test(
            "Get Low Stock Products",
            "GET",
            "inventory/low-stock",
            200
        )
        
        if not success:
            return False

        # Get inventory valuation
        success, _ = self.run_test(
            "Get Inventory Valuation",
            "GET",
            "inventory/valuation",
            200
        )
        
        return success

    def test_dashboard_charts(self):
        """Test dashboard chart endpoints"""
        # Get sales chart
        success, _ = self.run_test(
            "Get Sales Chart",
            "GET",
            "dashboard/sales-chart?period=7days",
            200
        )
        
        if not success:
            return False

        # Get top products
        success, _ = self.run_test(
            "Get Top Products",
            "GET",
            "dashboard/top-products?limit=5",
            200
        )
        
        return success

    def run_all_tests(self):
        """Run all backend API tests"""
        print("🚀 Starting ERP System Backend API Tests")
        print("=" * 50)
        
        # Test authentication first
        if not self.test_user_registration():
            print("⚠️  Registration failed, trying login...")
            if not self.test_user_login():
                print("❌ Authentication failed completely. Cannot proceed with other tests.")
                return False
        
        # Test authenticated endpoints
        self.test_get_current_user()
        self.test_dashboard_summary()
        self.test_products_crud()
        self.test_customers_crud()
        self.test_sales_orders()
        self.test_company_settings()
        self.test_woocommerce_settings()
        self.test_inventory_endpoints()
        self.test_dashboard_charts()
        
        # Print summary
        print("\n" + "=" * 50)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.failed_tests:
            print("\n❌ Failed Tests:")
            for test in self.failed_tests:
                print(f"  - {test['test']}: {test['error']}")
        
        return len(self.failed_tests) == 0

def main():
    tester = ERPSystemTester()
    success = tester.run_all_tests()
    
    # Save detailed results
    results = {
        "timestamp": datetime.now().isoformat(),
        "total_tests": tester.tests_run,
        "passed_tests": tester.tests_passed,
        "failed_tests": len(tester.failed_tests),
        "success_rate": (tester.tests_passed / tester.tests_run * 100) if tester.tests_run > 0 else 0,
        "failed_test_details": tester.failed_tests,
        "all_test_results": tester.test_results
    }
    
    with open('/app/backend_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())