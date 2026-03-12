"""
Payroll Module Backend Tests
Tests for: Departments, Employees, Salary Structure, Leave Management, Advances, Payroll Processing
"""

import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://po-grn-verify.preview.emergentagent.com').rstrip('/')

# Test data tracking for cleanup
created_departments = []
created_employees = []
created_leave_requests = []
created_advances = []
created_payrolls = []


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "lahiruraja97@gmail.com",
        "password": "password123"
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json()["access_token"]


@pytest.fixture(scope="module")
def headers(auth_token):
    """Get headers with auth token"""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }


# ============== DEPARTMENTS TESTS ==============

class TestDepartments:
    """Departments CRUD tests"""
    
    def test_get_departments(self, headers):
        """Test getting all departments"""
        response = requests.get(f"{BASE_URL}/api/payroll/departments", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} departments")
    
    def test_create_department(self, headers):
        """Test creating a new department"""
        dept_data = {
            "name": f"TEST_Dept_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "description": "Test department for payroll testing"
        }
        response = requests.post(f"{BASE_URL}/api/payroll/departments", json=dept_data, headers=headers)
        assert response.status_code == 200, f"Create department failed: {response.text}"
        data = response.json()
        assert "id" in data
        created_departments.append(data["id"])
        print(f"Created department: {data['id']}")
    
    def test_create_duplicate_department_fails(self, headers):
        """Test that duplicate department name fails"""
        # Get existing department
        response = requests.get(f"{BASE_URL}/api/payroll/departments", headers=headers)
        depts = response.json()
        if depts:
            existing_name = depts[0]["name"]
            response = requests.post(f"{BASE_URL}/api/payroll/departments", 
                                    json={"name": existing_name}, headers=headers)
            assert response.status_code == 400
            print("Duplicate department name correctly rejected")
    
    def test_update_department(self, headers):
        """Test updating a department"""
        if not created_departments:
            pytest.skip("No test department created")
        
        dept_id = created_departments[0]
        update_data = {"description": "Updated description for testing"}
        response = requests.put(f"{BASE_URL}/api/payroll/departments/{dept_id}", 
                               json=update_data, headers=headers)
        assert response.status_code == 200
        print(f"Updated department: {dept_id}")


# ============== EMPLOYEES TESTS ==============

class TestEmployees:
    """Employees CRUD tests"""
    
    def test_get_employees(self, headers):
        """Test getting all employees"""
        response = requests.get(f"{BASE_URL}/api/payroll/employees", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} employees")
    
    def test_get_next_employee_id(self, headers):
        """Test getting next employee ID"""
        response = requests.get(f"{BASE_URL}/api/payroll/employees/next-id/generate", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "next_id" in data
        print(f"Next employee ID: {data['next_id']}")
    
    def test_create_permanent_employee(self, headers):
        """Test creating a permanent employee"""
        # Get departments first
        dept_response = requests.get(f"{BASE_URL}/api/payroll/departments", headers=headers)
        depts = dept_response.json()
        dept_id = depts[0]["id"] if depts else None
        
        # Get next ID
        id_response = requests.get(f"{BASE_URL}/api/payroll/employees/next-id/generate", headers=headers)
        next_id = id_response.json()["next_id"]
        
        emp_data = {
            "employee_id": f"TEST_{next_id}",
            "first_name": "Test",
            "last_name": "Employee",
            "email": "test.employee@example.com",
            "phone": "0771234567",
            "nic": "991234567V",
            "department_id": dept_id,
            "employee_type": "permanent",
            "payment_frequency": "monthly",
            "basic_salary": 50000,
            "bank_name": "Test Bank",
            "bank_account_number": "1234567890",
            "bank_branch": "Test Branch"
        }
        response = requests.post(f"{BASE_URL}/api/payroll/employees", json=emp_data, headers=headers)
        assert response.status_code == 200, f"Create employee failed: {response.text}"
        data = response.json()
        assert "id" in data
        created_employees.append(data["id"])
        print(f"Created permanent employee: {data['id']}")
    
    def test_create_casual_employee(self, headers):
        """Test creating a casual employee"""
        emp_data = {
            "employee_id": f"TEST_CASUAL_{datetime.now().strftime('%H%M%S')}",
            "first_name": "Casual",
            "last_name": "Worker",
            "employee_type": "casual",
            "payment_frequency": "daily",
            "daily_rate": 2500
        }
        response = requests.post(f"{BASE_URL}/api/payroll/employees", json=emp_data, headers=headers)
        assert response.status_code == 200, f"Create casual employee failed: {response.text}"
        data = response.json()
        created_employees.append(data["id"])
        print(f"Created casual employee: {data['id']}")
    
    def test_create_freelancer_employee(self, headers):
        """Test creating a freelancer employee"""
        emp_data = {
            "employee_id": f"TEST_FREE_{datetime.now().strftime('%H%M%S')}",
            "first_name": "Freelance",
            "last_name": "Dev",
            "employee_type": "freelancer",
            "payment_frequency": "per_task",
            "hourly_rate": 3000
        }
        response = requests.post(f"{BASE_URL}/api/payroll/employees", json=emp_data, headers=headers)
        assert response.status_code == 200, f"Create freelancer employee failed: {response.text}"
        data = response.json()
        created_employees.append(data["id"])
        print(f"Created freelancer employee: {data['id']}")
    
    def test_create_contract_employee(self, headers):
        """Test creating a contract employee"""
        emp_data = {
            "employee_id": f"TEST_CONT_{datetime.now().strftime('%H%M%S')}",
            "first_name": "Contract",
            "last_name": "Staff",
            "employee_type": "contract",
            "payment_frequency": "monthly",
            "basic_salary": 60000,
            "contract_end_date": (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")
        }
        response = requests.post(f"{BASE_URL}/api/payroll/employees", json=emp_data, headers=headers)
        assert response.status_code == 200, f"Create contract employee failed: {response.text}"
        data = response.json()
        created_employees.append(data["id"])
        print(f"Created contract employee: {data['id']}")
    
    def test_get_employee_details(self, headers):
        """Test getting employee details with leave balance"""
        if not created_employees:
            pytest.skip("No test employees created")
        
        emp_id = created_employees[0]
        response = requests.get(f"{BASE_URL}/api/payroll/employees/{emp_id}", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "leave_balance" in data
        assert "full_name" in data
        print(f"Employee details retrieved: {data['full_name']}, Leave balance: {data['leave_balance']}")
    
    def test_update_employee(self, headers):
        """Test updating an employee"""
        if not created_employees:
            pytest.skip("No test employees created")
        
        emp_id = created_employees[0]
        update_data = {
            "phone": "0779876543",
            "address": "Test Address, Colombo"
        }
        response = requests.put(f"{BASE_URL}/api/payroll/employees/{emp_id}", 
                               json=update_data, headers=headers)
        assert response.status_code == 200
        print(f"Updated employee: {emp_id}")
    
    def test_filter_employees_by_type(self, headers):
        """Test filtering employees by type"""
        response = requests.get(f"{BASE_URL}/api/payroll/employees?employee_type=permanent", headers=headers)
        assert response.status_code == 200
        data = response.json()
        for emp in data:
            assert emp["employee_type"] == "permanent"
        print(f"Filter by type working: Found {len(data)} permanent employees")


# ============== SALARY STRUCTURE TESTS ==============

class TestSalaryStructure:
    """Salary Structure tests"""
    
    def test_get_salary_structure(self, headers):
        """Test getting salary structure"""
        response = requests.get(f"{BASE_URL}/api/payroll/salary-structure", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        # Verify default rates
        assert "epf_employee_rate" in data
        assert "epf_employer_rate" in data
        assert "etf_employer_rate" in data
        assert "overtime_weekday_rate" in data
        assert "overtime_weekend_rate" in data
        assert "allowances" in data
        assert "tax_slabs" in data
        
        print(f"Salary Structure: EPF Employee={data['epf_employee_rate']}%, EPF Employer={data['epf_employer_rate']}%, ETF={data['etf_employer_rate']}%")
    
    def test_update_statutory_rates(self, headers):
        """Test updating EPF/ETF rates"""
        update_data = {
            "epf_employee_rate": 8.0,
            "epf_employer_rate": 12.0,
            "etf_employer_rate": 3.0,
            "overtime_weekday_rate": 1.25,
            "overtime_weekend_rate": 1.5
        }
        response = requests.put(f"{BASE_URL}/api/payroll/salary-structure", 
                               json=update_data, headers=headers)
        assert response.status_code == 200
        print("Statutory rates updated successfully")
        
        # Verify update
        response = requests.get(f"{BASE_URL}/api/payroll/salary-structure", headers=headers)
        data = response.json()
        assert data["epf_employee_rate"] == 8.0
        assert data["epf_employer_rate"] == 12.0
    
    def test_add_allowance(self, headers):
        """Test adding a new allowance"""
        allowance_data = {
            "name": f"TEST_Allowance_{datetime.now().strftime('%H%M%S')}",
            "type": "fixed",
            "value": 5000,
            "is_taxable": True,
            "applies_to": []
        }
        response = requests.post(f"{BASE_URL}/api/payroll/salary-structure/allowances", 
                                json=allowance_data, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        print(f"Added allowance: {allowance_data['name']}")
    
    def test_delete_allowance(self, headers):
        """Test deleting an allowance"""
        # First add a test allowance
        allowance_data = {
            "name": f"TEST_ToDelete_{datetime.now().strftime('%H%M%S')}",
            "type": "fixed",
            "value": 1000,
            "is_taxable": True,
            "applies_to": []
        }
        add_response = requests.post(f"{BASE_URL}/api/payroll/salary-structure/allowances", 
                                    json=allowance_data, headers=headers)
        allowance_id = add_response.json()["id"]
        
        # Delete it
        response = requests.delete(f"{BASE_URL}/api/payroll/salary-structure/allowances/{allowance_id}", 
                                  headers=headers)
        assert response.status_code == 200
        print(f"Deleted allowance: {allowance_id}")


# ============== LEAVE MANAGEMENT TESTS ==============

class TestLeaveManagement:
    """Leave Management tests"""
    
    def test_get_leave_balances(self, headers):
        """Test getting leave balances"""
        response = requests.get(f"{BASE_URL}/api/payroll/leave/balances", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if data:
            assert "annual" in data[0]
            assert "sick" in data[0]
            assert "casual" in data[0]
        print(f"Found {len(data)} employee leave balances")
    
    def test_create_leave_request(self, headers):
        """Test creating a leave request"""
        # Get an employee first
        emp_response = requests.get(f"{BASE_URL}/api/payroll/employees?status=active", headers=headers)
        employees = emp_response.json()
        if not employees:
            pytest.skip("No active employees to create leave request")
        
        emp_id = employees[0]["id"]
        
        leave_data = {
            "employee_id": emp_id,
            "leave_type": "annual",
            "start_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
            "end_date": (datetime.now() + timedelta(days=8)).strftime("%Y-%m-%d"),
            "reason": "Test leave request"
        }
        response = requests.post(f"{BASE_URL}/api/payroll/leave/requests", 
                                json=leave_data, headers=headers)
        assert response.status_code == 200, f"Create leave request failed: {response.text}"
        data = response.json()
        assert "id" in data
        assert "days" in data
        created_leave_requests.append(data["id"])
        print(f"Created leave request: {data['id']} for {data['days']} days")
    
    def test_get_leave_requests(self, headers):
        """Test getting leave requests"""
        response = requests.get(f"{BASE_URL}/api/payroll/leave/requests", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} leave requests")
    
    def test_approve_leave_request(self, headers):
        """Test approving a leave request"""
        if not created_leave_requests:
            pytest.skip("No test leave requests created")
        
        request_id = created_leave_requests[0]
        response = requests.post(f"{BASE_URL}/api/payroll/leave/requests/{request_id}/approve", 
                                headers=headers)
        assert response.status_code == 200
        print(f"Approved leave request: {request_id}")
    
    def test_update_leave_balance(self, headers):
        """Test updating leave balance"""
        emp_response = requests.get(f"{BASE_URL}/api/payroll/employees?status=active", headers=headers)
        employees = emp_response.json()
        if not employees:
            pytest.skip("No active employees")
        
        emp_id = employees[0]["id"]
        
        balance_data = {
            "annual": 14,
            "sick": 7,
            "casual": 7
        }
        response = requests.put(f"{BASE_URL}/api/payroll/leave/balances/{emp_id}", 
                               json=balance_data, headers=headers)
        assert response.status_code == 200
        print(f"Updated leave balance for employee: {emp_id}")


# ============== ADVANCES & LOANS TESTS ==============

class TestAdvances:
    """Advances & Loans tests"""
    
    def test_get_advances(self, headers):
        """Test getting all advances"""
        response = requests.get(f"{BASE_URL}/api/payroll/advances", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} advances/loans")
    
    def test_create_advance(self, headers):
        """Test issuing an advance"""
        # Get an employee first
        emp_response = requests.get(f"{BASE_URL}/api/payroll/employees?status=active", headers=headers)
        employees = emp_response.json()
        if not employees:
            pytest.skip("No active employees to issue advance")
        
        emp_id = employees[0]["id"]
        
        advance_data = {
            "employee_id": emp_id,
            "amount": 10000,
            "type": "advance",
            "monthly_deduction": 2500,
            "reason": "Test salary advance"
        }
        response = requests.post(f"{BASE_URL}/api/payroll/advances", 
                                json=advance_data, headers=headers)
        assert response.status_code == 200, f"Create advance failed: {response.text}"
        data = response.json()
        assert "id" in data
        assert "advance_number" in data
        created_advances.append(data["id"])
        print(f"Created advance: {data['advance_number']}")
    
    def test_create_loan(self, headers):
        """Test issuing a loan"""
        emp_response = requests.get(f"{BASE_URL}/api/payroll/employees?status=active", headers=headers)
        employees = emp_response.json()
        if not employees:
            pytest.skip("No active employees to issue loan")
        
        emp_id = employees[0]["id"]
        
        loan_data = {
            "employee_id": emp_id,
            "amount": 50000,
            "type": "loan",
            "monthly_deduction": 5000,
            "reason": "Test loan"
        }
        response = requests.post(f"{BASE_URL}/api/payroll/advances", 
                                json=loan_data, headers=headers)
        assert response.status_code == 200, f"Create loan failed: {response.text}"
        data = response.json()
        created_advances.append(data["id"])
        print(f"Created loan: {data['advance_number']}")


# ============== PAYROLL PROCESSING TESTS ==============

class TestPayrollProcessing:
    """Payroll Processing tests"""
    
    def test_get_payrolls(self, headers):
        """Test getting all payrolls"""
        response = requests.get(f"{BASE_URL}/api/payroll/payrolls", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} payroll runs")
    
    def test_create_payroll(self, headers):
        """Test creating a payroll run"""
        now = datetime.now()
        payroll_data = {
            "period_start": now.replace(day=1).strftime("%Y-%m-%d"),
            "period_end": (now.replace(day=28) if now.month == 2 else now.replace(day=30)).strftime("%Y-%m-%d"),
            "payment_frequency": "monthly"
        }
        response = requests.post(f"{BASE_URL}/api/payroll/payrolls", 
                                json=payroll_data, headers=headers)
        assert response.status_code == 200, f"Create payroll failed: {response.text}"
        data = response.json()
        assert "id" in data
        assert "payroll_number" in data
        assert "employee_count" in data
        created_payrolls.append(data["id"])
        print(f"Created payroll: {data['payroll_number']} with {data['employee_count']} employees")
    
    def test_get_payroll_details(self, headers):
        """Test getting payroll details"""
        if not created_payrolls:
            pytest.skip("No test payrolls created")
        
        payroll_id = created_payrolls[0]
        response = requests.get(f"{BASE_URL}/api/payroll/payrolls/{payroll_id}", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total_gross" in data
        assert "total_net" in data
        print(f"Payroll details: {data['employee_count']} employees, Gross: {data['total_gross']}, Net: {data['total_net']}")
    
    def test_submit_payroll_for_approval(self, headers):
        """Test submitting payroll for approval"""
        if not created_payrolls:
            pytest.skip("No test payrolls created")
        
        payroll_id = created_payrolls[0]
        response = requests.post(f"{BASE_URL}/api/payroll/payrolls/{payroll_id}/submit", headers=headers)
        assert response.status_code == 200
        print(f"Submitted payroll for approval: {payroll_id}")
    
    def test_approve_payroll(self, headers):
        """Test approving payroll"""
        if not created_payrolls:
            pytest.skip("No test payrolls created")
        
        payroll_id = created_payrolls[0]
        response = requests.post(f"{BASE_URL}/api/payroll/payrolls/{payroll_id}/approve", headers=headers)
        assert response.status_code == 200
        print(f"Approved payroll: {payroll_id}")
    
    def test_process_payroll(self, headers):
        """Test processing and paying payroll"""
        if not created_payrolls:
            pytest.skip("No test payrolls created")
        
        # Get bank account
        bank_response = requests.get(f"{BASE_URL}/api/bank-accounts", headers=headers)
        bank_accounts = bank_response.json()
        if not bank_accounts:
            pytest.skip("No bank accounts for payroll processing")
        
        bank_id = bank_accounts[0]["id"]
        payroll_id = created_payrolls[0]
        
        response = requests.post(
            f"{BASE_URL}/api/payroll/payrolls/{payroll_id}/process?bank_account_id={bank_id}", 
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "journal_entry_id" in data
        print(f"Processed payroll: {payroll_id}, Journal Entry: {data['journal_entry_id']}")


# ============== REPORTS TESTS ==============

class TestPayrollReports:
    """Payroll Reports tests"""
    
    def test_get_payroll_summary(self, headers):
        """Test getting payroll summary report"""
        now = datetime.now()
        params = {
            "period_start": now.replace(day=1).strftime("%Y-%m-%d"),
            "period_end": now.strftime("%Y-%m-%d")
        }
        response = requests.get(f"{BASE_URL}/api/payroll/reports/summary", 
                               params=params, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_payrolls" in data
        assert "total_gross" in data
        assert "total_net" in data
        print(f"Summary: {data['total_payrolls']} payrolls, Gross: {data['total_gross']}, Net: {data['total_net']}")
    
    def test_get_epf_etf_report(self, headers):
        """Test getting EPF/ETF report"""
        now = datetime.now()
        params = {
            "period_start": now.replace(day=1).strftime("%Y-%m-%d"),
            "period_end": now.strftime("%Y-%m-%d")
        }
        response = requests.get(f"{BASE_URL}/api/payroll/reports/epf-etf", 
                               params=params, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "contributions" in data
        assert "totals" in data
        print(f"EPF/ETF Report: {len(data['contributions'])} employee contributions")
    
    def test_get_department_report(self, headers):
        """Test getting department salary report"""
        now = datetime.now()
        params = {
            "period_start": now.replace(day=1).strftime("%Y-%m-%d"),
            "period_end": now.strftime("%Y-%m-%d")
        }
        response = requests.get(f"{BASE_URL}/api/payroll/reports/department", 
                               params=params, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "departments" in data
        print(f"Department Report: {len(data['departments'])} departments")


# ============== CLEANUP ==============

class TestCleanup:
    """Cleanup test data"""
    
    def test_delete_test_payrolls(self, headers):
        """Delete test payrolls (only draft status)"""
        # Note: Can only delete draft payrolls, processed payrolls cannot be deleted
        response = requests.get(f"{BASE_URL}/api/payroll/payrolls?status=draft", headers=headers)
        payrolls = response.json()
        for payroll in payrolls:
            if "TEST" in str(payroll.get("payroll_number", "")):
                requests.delete(f"{BASE_URL}/api/payroll/payrolls/{payroll['id']}", headers=headers)
                print(f"Deleted test payroll: {payroll['id']}")
    
    def test_terminate_test_employees(self, headers):
        """Terminate test employees"""
        response = requests.get(f"{BASE_URL}/api/payroll/employees", headers=headers)
        employees = response.json()
        for emp in employees:
            if emp["employee_id"].startswith("TEST_"):
                requests.delete(f"{BASE_URL}/api/payroll/employees/{emp['id']}", headers=headers)
                print(f"Terminated test employee: {emp['employee_id']}")
    
    def test_delete_test_departments(self, headers):
        """Delete test departments"""
        response = requests.get(f"{BASE_URL}/api/payroll/departments", headers=headers)
        depts = response.json()
        for dept in depts:
            if dept["name"].startswith("TEST_"):
                del_response = requests.delete(
                    f"{BASE_URL}/api/payroll/departments/{dept['id']}", 
                    headers=headers
                )
                if del_response.status_code == 200:
                    print(f"Deleted test department: {dept['name']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
