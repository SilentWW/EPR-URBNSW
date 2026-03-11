"""
Comprehensive ERP System Backend Tests
Tests: Auth, Products, Inventory, Suppliers, Customers, Purchase Orders, GRN, 
Sales Orders, Invoices, Payments, Finance, Payroll, HR, Notifications
"""
import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
TEST_CREDENTIALS = {
    "email": "lahiruraja97@gmail.com",
    "password": "password123"
}

class TestContext:
    """Shared test context for data created during tests"""
    token = None
    company_id = None
    user_id = None
    product_id = None
    supplier_id = None
    customer_id = None
    purchase_order_id = None
    sales_order_id = None
    employee_id = None
    department_id = None

ctx = TestContext()

@pytest.fixture(scope="session", autouse=True)
def authenticate():
    """Login and get token for all tests"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json=TEST_CREDENTIALS)
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    ctx.token = data["access_token"]
    ctx.company_id = data["user"]["company_id"]
    ctx.user_id = data["user"]["id"]
    print(f"Authenticated as: {data['user']['email']}")
    yield
    print("Tests completed")

@pytest.fixture
def auth_headers():
    """Get auth headers for requests"""
    return {"Authorization": f"Bearer {ctx.token}"}


# ============== AUTH TESTS ==============
class TestAuth:
    """Authentication Tests"""
    
    def test_login_success(self):
        """Test successful login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=TEST_CREDENTIALS)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == TEST_CREDENTIALS["email"]
        print(f"Login successful - Role: {data['user']['role']}")
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "wrong@email.com",
            "password": "wrongpass"
        })
        assert response.status_code == 401
    
    def test_get_me(self, auth_headers):
        """Test get current user profile"""
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == TEST_CREDENTIALS["email"]
        assert "company_name" in data
        print(f"Company: {data.get('company_name')}")


# ============== DASHBOARD TESTS ==============
class TestDashboard:
    """Dashboard API Tests"""
    
    def test_dashboard_stats(self, auth_headers):
        """Test dashboard stats endpoint"""
        response = requests.get(f"{BASE_URL}/api/dashboard/stats", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        # Check for key dashboard metrics
        print(f"Dashboard stats: {list(data.keys())}")


# ============== PRODUCTS TESTS ==============
class TestProducts:
    """Products CRUD Tests"""
    
    def test_list_products(self, auth_headers):
        """Test listing products"""
        response = requests.get(f"{BASE_URL}/api/products", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} products")
        if data:
            ctx.product_id = data[0]["id"]
    
    def test_create_product(self, auth_headers):
        """Test creating a product"""
        product_data = {
            "name": f"TEST Product {datetime.now().timestamp()}",
            "description": "Test product description",
            "cost_price": 100.0,
            "selling_price": 150.0,
            "regular_price": 150.0,
            "stock_quantity": 50,
            "low_stock_threshold": 10,
            "category": "Test Category"
        }
        response = requests.post(f"{BASE_URL}/api/products", json=product_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == product_data["name"]
        assert "sku" in data
        ctx.product_id = data["id"]
        print(f"Created product: {data['sku']}")
    
    def test_get_product(self, auth_headers):
        """Test getting a specific product"""
        if not ctx.product_id:
            pytest.skip("No product ID available")
        response = requests.get(f"{BASE_URL}/api/products/{ctx.product_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == ctx.product_id
    
    def test_update_product(self, auth_headers):
        """Test updating a product"""
        if not ctx.product_id:
            pytest.skip("No product ID available")
        update_data = {"selling_price": 175.0}
        response = requests.put(f"{BASE_URL}/api/products/{ctx.product_id}", 
                               json=update_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["selling_price"] == 175.0


# ============== INVENTORY TESTS ==============
class TestInventory:
    """Inventory Management Tests"""
    
    def test_inventory_valuation(self, auth_headers):
        """Test inventory valuation endpoint"""
        response = requests.get(f"{BASE_URL}/api/inventory/valuation", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_cost_value" in data
        assert "total_retail_value" in data
        print(f"Inventory Value: Cost={data['total_cost_value']}, Retail={data['total_retail_value']}")
    
    def test_low_stock_products(self, auth_headers):
        """Test low stock products endpoint"""
        response = requests.get(f"{BASE_URL}/api/inventory/low-stock", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Low stock items: {len(data)}")


# ============== SUPPLIERS TESTS ==============
class TestSuppliers:
    """Suppliers CRUD Tests"""
    
    def test_list_suppliers(self, auth_headers):
        """Test listing suppliers"""
        response = requests.get(f"{BASE_URL}/api/suppliers", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} suppliers")
        if data:
            ctx.supplier_id = data[0]["id"]
    
    def test_create_supplier(self, auth_headers):
        """Test creating a supplier"""
        supplier_data = {
            "name": f"TEST Supplier {datetime.now().timestamp()}",
            "email": "testsupplier@test.com",
            "phone": "+94771234567",
            "address": "Test Address",
            "contact_person": "Test Contact"
        }
        response = requests.post(f"{BASE_URL}/api/suppliers", json=supplier_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == supplier_data["name"]
        ctx.supplier_id = data["id"]
        print(f"Created supplier: {data['name']}")
    
    def test_get_supplier(self, auth_headers):
        """Test getting supplier details"""
        if not ctx.supplier_id:
            pytest.skip("No supplier ID available")
        response = requests.get(f"{BASE_URL}/api/suppliers/{ctx.supplier_id}", headers=auth_headers)
        assert response.status_code == 200


# ============== CUSTOMERS TESTS ==============
class TestCustomers:
    """Customers CRUD Tests"""
    
    def test_list_customers(self, auth_headers):
        """Test listing customers"""
        response = requests.get(f"{BASE_URL}/api/customers", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} customers")
        if data:
            ctx.customer_id = data[0]["id"]
    
    def test_create_customer(self, auth_headers):
        """Test creating a customer"""
        customer_data = {
            "name": f"TEST Customer {datetime.now().timestamp()}",
            "email": "testcustomer@test.com",
            "phone": "+94779876543",
            "address": "Test Customer Address"
        }
        response = requests.post(f"{BASE_URL}/api/customers", json=customer_data, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == customer_data["name"]
        ctx.customer_id = data["id"]
        print(f"Created customer: {data['name']}")


# ============== PURCHASE ORDERS TESTS ==============
class TestPurchaseOrders:
    """Purchase Orders Tests"""
    
    def test_list_purchase_orders(self, auth_headers):
        """Test listing purchase orders"""
        response = requests.get(f"{BASE_URL}/api/purchase-orders", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} purchase orders")
        if data:
            ctx.purchase_order_id = data[0]["id"]
    
    def test_get_purchase_order(self, auth_headers):
        """Test getting a specific PO"""
        if not ctx.purchase_order_id:
            pytest.skip("No PO ID available")
        response = requests.get(f"{BASE_URL}/api/purchase-orders/{ctx.purchase_order_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "order_number" in data


# ============== GRN TESTS ==============
class TestGRN:
    """Goods Received Note Tests"""
    
    def test_list_grns(self, auth_headers):
        """Test listing GRNs"""
        response = requests.get(f"{BASE_URL}/api/grn", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} GRNs")


# ============== SALES ORDERS TESTS ==============
class TestSalesOrders:
    """Sales Orders Tests"""
    
    def test_list_sales_orders(self, auth_headers):
        """Test listing sales orders"""
        response = requests.get(f"{BASE_URL}/api/sales-orders", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} sales orders")
        if data:
            ctx.sales_order_id = data[0]["id"]
    
    def test_get_sales_order(self, auth_headers):
        """Test getting a specific sales order"""
        if not ctx.sales_order_id:
            pytest.skip("No sales order ID available")
        response = requests.get(f"{BASE_URL}/api/sales-orders/{ctx.sales_order_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "order_number" in data


# ============== INVOICES TESTS ==============
class TestInvoices:
    """Invoice Tests"""
    
    def test_list_invoices(self, auth_headers):
        """Test listing invoices"""
        response = requests.get(f"{BASE_URL}/api/invoices", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} invoices")


# ============== PAYMENTS TESTS ==============
class TestPayments:
    """Payments Tests"""
    
    def test_list_payments(self, auth_headers):
        """Test listing payments"""
        response = requests.get(f"{BASE_URL}/api/payments", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} payments")


# ============== BANK ACCOUNTS TESTS ==============
class TestBankAccounts:
    """Bank Accounts Tests"""
    
    def test_list_bank_accounts(self, auth_headers):
        """Test listing bank accounts"""
        response = requests.get(f"{BASE_URL}/api/bank-accounts", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} bank accounts")


# ============== CHART OF ACCOUNTS TESTS ==============
class TestChartOfAccounts:
    """Chart of Accounts Tests"""
    
    def test_get_chart_of_accounts(self, auth_headers):
        """Test getting chart of accounts"""
        response = requests.get(f"{BASE_URL}/api/finance/chart-of-accounts", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} accounts in CoA")


# ============== FINANCIAL REPORTS TESTS ==============
class TestFinancialReports:
    """Financial Reports Tests"""
    
    def test_trial_balance(self, auth_headers):
        """Test trial balance report"""
        response = requests.get(f"{BASE_URL}/api/finance/reports/trial-balance", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "accounts" in data
        assert "total_debit" in data
        assert "total_credit" in data
        print(f"Trial Balance: Debit={data['total_debit']}, Credit={data['total_credit']}")
    
    def test_profit_loss(self, auth_headers):
        """Test P&L report"""
        response = requests.get(f"{BASE_URL}/api/finance/reports/profit-loss", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "income" in data
        assert "expenses" in data
        assert "net_profit" in data
        print(f"P&L: Income={data['income']['total']}, Expenses={data['expenses']['total']}, Net={data['net_profit']}")
    
    def test_balance_sheet(self, auth_headers):
        """Test balance sheet report"""
        response = requests.get(f"{BASE_URL}/api/finance/reports/balance-sheet", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "assets" in data
        assert "liabilities" in data
        assert "equity" in data
        print(f"Balance Sheet: Assets={data['total_assets']}, Liab+Equity={data['total_liabilities_equity']}")


# ============== DEPARTMENTS TESTS ==============
class TestDepartments:
    """Department Tests"""
    
    def test_list_departments(self, auth_headers):
        """Test listing departments"""
        response = requests.get(f"{BASE_URL}/api/payroll/departments", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} departments")
        if data:
            ctx.department_id = data[0]["id"]


# ============== DESIGNATIONS TESTS ==============
class TestDesignations:
    """Designation Tests"""
    
    def test_list_designations(self, auth_headers):
        """Test listing designations"""
        response = requests.get(f"{BASE_URL}/api/payroll/designations", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} designations")


# ============== EMPLOYEES TESTS ==============
class TestEmployees:
    """Employee Tests"""
    
    def test_list_employees(self, auth_headers):
        """Test listing employees"""
        response = requests.get(f"{BASE_URL}/api/payroll/employees", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} employees")
        if data:
            ctx.employee_id = data[0]["id"]
    
    def test_get_employee(self, auth_headers):
        """Test getting employee details"""
        if not ctx.employee_id:
            pytest.skip("No employee ID available")
        response = requests.get(f"{BASE_URL}/api/payroll/employees/{ctx.employee_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "full_name" in data


# ============== ATTENDANCE TESTS ==============
class TestAttendance:
    """Attendance Tests"""
    
    def test_list_attendance(self, auth_headers):
        """Test listing attendance"""
        today = datetime.now().strftime("%Y-%m")
        response = requests.get(f"{BASE_URL}/api/payroll/attendance?month={today}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} attendance records")


# ============== LEAVE MANAGEMENT TESTS ==============
class TestLeaveManagement:
    """Leave Management Tests"""
    
    def test_list_leave_requests(self, auth_headers):
        """Test listing leave requests"""
        response = requests.get(f"{BASE_URL}/api/payroll/leave/requests", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} leave requests")
    
    def test_list_leave_balances(self, auth_headers):
        """Test listing leave balances"""
        response = requests.get(f"{BASE_URL}/api/payroll/leave/balances", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} leave balance records")


# ============== ADVANCES/LOANS TESTS ==============
class TestAdvancesLoans:
    """Advances and Loans Tests"""
    
    def test_list_advances(self, auth_headers):
        """Test listing advances"""
        response = requests.get(f"{BASE_URL}/api/payroll/advances", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} advances/loans")


# ============== TASK ASSIGNMENTS TESTS ==============
class TestTaskAssignments:
    """Task Assignment Tests"""
    
    def test_list_tasks(self, auth_headers):
        """Test listing task assignments"""
        response = requests.get(f"{BASE_URL}/api/payroll/tasks", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} task assignments")


# ============== PAYROLL TESTS ==============
class TestPayroll:
    """Payroll Tests"""
    
    def test_list_payrolls(self, auth_headers):
        """Test listing payroll runs"""
        response = requests.get(f"{BASE_URL}/api/payroll/payrolls", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} payroll runs")


# ============== NOTIFICATIONS TESTS ==============
class TestNotifications:
    """Notification Tests"""
    
    def test_list_notifications(self, auth_headers):
        """Test listing notifications"""
        response = requests.get(f"{BASE_URL}/api/notifications", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "notifications" in data
        assert "unread_count" in data
        print(f"Found {len(data['notifications'])} notifications, {data['unread_count']} unread")
    
    def test_get_notification_preferences(self, auth_headers):
        """Test getting notification preferences"""
        response = requests.get(f"{BASE_URL}/api/notifications/preferences", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "email_enabled" in data
        assert "in_app_enabled" in data


# ============== EMPLOYEE PORTAL TESTS ==============
class TestEmployeePortal:
    """Employee Portal Tests"""
    
    def test_my_dashboard(self, auth_headers):
        """Test employee portal dashboard"""
        response = requests.get(f"{BASE_URL}/api/portal/my-dashboard", headers=auth_headers)
        # May return 404 if user is not linked to employee
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            print("Employee portal dashboard accessible")
        else:
            print("User not linked to employee record")
    
    def test_my_profile(self, auth_headers):
        """Test my profile endpoint"""
        response = requests.get(f"{BASE_URL}/api/portal/my-profile", headers=auth_headers)
        assert response.status_code in [200, 404]


# ============== QUICK TRANSACTIONS TESTS ==============
class TestQuickTransactions:
    """Quick Transactions Tests"""
    
    def test_list_quick_transactions(self, auth_headers):
        """Test listing quick expense/revenue entries"""
        response = requests.get(f"{BASE_URL}/api/simple-finance/transactions", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} quick transactions")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
