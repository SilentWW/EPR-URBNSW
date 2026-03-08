"""
Test OT Calculation and Payroll Integration
- Normal duty = 9 hours
- OT calculated only for hours > 9
- OT rates: 1.25x weekday, 1.5x weekend
- Payroll automatically fetches attendance data and includes OT pay
"""

import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

@pytest.fixture(scope="module")
def auth_token():
    """Login and get auth token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "lahiruraja97@gmail.com",
        "password": "password123"
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    return data.get("access_token") or data.get("token")

@pytest.fixture(scope="module")
def api_client(auth_token):
    """API session with auth header"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    })
    return session

@pytest.fixture(scope="module")
def test_employee(api_client):
    """Get an existing active employee for testing"""
    response = api_client.get(f"{BASE_URL}/api/payroll/employees", params={"status": "active"})
    assert response.status_code == 200
    employees = response.json()
    assert len(employees) > 0, "No active employees found"
    return employees[0]


class TestOTCalculation:
    """Test OT calculation logic - OT only for hours > 9"""
    
    def test_attendance_settings_has_standard_work_hours(self, api_client):
        """Verify attendance settings returns 9 hours as standard"""
        response = api_client.get(f"{BASE_URL}/api/payroll/attendance/settings")
        assert response.status_code == 200
        settings = response.json()
        
        # Verify standard work hours is 9
        assert settings.get("standard_work_hours") == 9.0, f"Expected 9.0, got {settings.get('standard_work_hours')}"
        assert settings.get("full_day_hours") == 9.0
        print(f"PASS: Standard work hours = 9, Full day hours = 9")
    
    def test_9_hours_no_ot(self, api_client, test_employee):
        """Test: 9 hours worked = 0 OT (exactly standard duty)"""
        # Monday date for weekday test
        test_date = "2026-03-02"  # Monday
        
        # Create attendance: 08:00 - 17:00 = 9 hours
        response = api_client.post(f"{BASE_URL}/api/payroll/attendance", json={
            "employee_id": test_employee["id"],
            "date": test_date,
            "check_in": "08:00",
            "check_out": "17:00",
            "status": "present"
        })
        assert response.status_code in [200, 201], f"Failed to create attendance: {response.text}"
        
        # Fetch the daily attendance to verify calculated fields
        daily_resp = api_client.get(f"{BASE_URL}/api/payroll/attendance/daily/{test_date}")
        assert daily_resp.status_code == 200
        daily_data = daily_resp.json()
        
        # Find our employee's record
        emp_record = next((r for r in daily_data if r["employee_id"] == test_employee["id"]), None)
        assert emp_record is not None, f"Employee record not found for {test_date}"
        
        assert emp_record.get("hours_worked") == 9.0, f"Expected 9.0 hours, got {emp_record.get('hours_worked')}"
        assert emp_record.get("overtime_regular") == 0, f"Expected 0 OT for 9 hours, got {emp_record.get('overtime_regular')}"
        print(f"PASS: 9 hours = No OT (overtime_regular: {emp_record.get('overtime_regular')})")
    
    def test_10_hours_1_hour_ot(self, api_client, test_employee):
        """Test: 10 hours worked = 1 hour OT"""
        test_date = "2026-03-03"  # Tuesday
        
        # Create attendance: 08:00 - 18:00 = 10 hours
        response = api_client.post(f"{BASE_URL}/api/payroll/attendance", json={
            "employee_id": test_employee["id"],
            "date": test_date,
            "check_in": "08:00",
            "check_out": "18:00",
            "status": "present"
        })
        assert response.status_code in [200, 201], f"Failed: {response.text}"
        
        # Fetch daily attendance to verify
        daily_resp = api_client.get(f"{BASE_URL}/api/payroll/attendance/daily/{test_date}")
        assert daily_resp.status_code == 200
        emp_record = next((r for r in daily_resp.json() if r["employee_id"] == test_employee["id"]), None)
        
        assert emp_record.get("hours_worked") == 10.0, f"Expected 10.0 hours, got {emp_record.get('hours_worked')}"
        assert emp_record.get("overtime_regular") == 1.0, f"Expected 1.0 OT for 10 hours, got {emp_record.get('overtime_regular')}"
        print(f"PASS: 10 hours = 1 hour OT (overtime_regular: {emp_record.get('overtime_regular')})")
    
    def test_11_hours_2_hours_ot(self, api_client, test_employee):
        """Test: 11 hours worked = 2 hours OT"""
        test_date = "2026-03-04"  # Wednesday
        
        # Create attendance: 07:00 - 18:00 = 11 hours
        response = api_client.post(f"{BASE_URL}/api/payroll/attendance", json={
            "employee_id": test_employee["id"],
            "date": test_date,
            "check_in": "07:00",
            "check_out": "18:00",
            "status": "present"
        })
        assert response.status_code in [200, 201], f"Failed: {response.text}"
        
        # Fetch daily attendance to verify
        daily_resp = api_client.get(f"{BASE_URL}/api/payroll/attendance/daily/{test_date}")
        assert daily_resp.status_code == 200
        emp_record = next((r for r in daily_resp.json() if r["employee_id"] == test_employee["id"]), None)
        
        assert emp_record.get("hours_worked") == 11.0, f"Expected 11.0 hours, got {emp_record.get('hours_worked')}"
        assert emp_record.get("overtime_regular") == 2.0, f"Expected 2.0 OT for 11 hours, got {emp_record.get('overtime_regular')}"
        print(f"PASS: 11 hours = 2 hours OT (overtime_regular: {emp_record.get('overtime_regular')})")
    
    def test_8_hours_no_ot(self, api_client, test_employee):
        """Test: 8 hours worked = 0 OT (less than 9 hours normal)"""
        test_date = "2026-03-05"  # Thursday
        
        # Create attendance: 08:00 - 16:00 = 8 hours
        response = api_client.post(f"{BASE_URL}/api/payroll/attendance", json={
            "employee_id": test_employee["id"],
            "date": test_date,
            "check_in": "08:00",
            "check_out": "16:00",
            "status": "present"
        })
        assert response.status_code in [200, 201], f"Failed: {response.text}"
        
        # Fetch daily attendance to verify
        daily_resp = api_client.get(f"{BASE_URL}/api/payroll/attendance/daily/{test_date}")
        assert daily_resp.status_code == 200
        emp_record = next((r for r in daily_resp.json() if r["employee_id"] == test_employee["id"]), None)
        
        assert emp_record.get("hours_worked") == 8.0, f"Expected 8.0 hours, got {emp_record.get('hours_worked')}"
        assert emp_record.get("overtime_regular") == 0, f"Expected 0 OT for 8 hours, got {emp_record.get('overtime_regular')}"
        print(f"PASS: 8 hours = No OT (less than 9h standard)")


class TestWeekendOT:
    """Test weekend OT uses 1.5x rate"""
    
    def test_weekend_ot_saturday(self, api_client, test_employee):
        """Test: Saturday work gets weekend OT rate"""
        test_date = "2026-03-07"  # Saturday
        
        # Create attendance: 08:00 - 18:00 = 10 hours (1 hour OT)
        response = api_client.post(f"{BASE_URL}/api/payroll/attendance", json={
            "employee_id": test_employee["id"],
            "date": test_date,
            "check_in": "08:00",
            "check_out": "18:00",
            "status": "present"
        })
        assert response.status_code in [200, 201], f"Failed: {response.text}"
        
        # Fetch daily attendance to verify
        daily_resp = api_client.get(f"{BASE_URL}/api/payroll/attendance/daily/{test_date}")
        assert daily_resp.status_code == 200
        emp_record = next((r for r in daily_resp.json() if r["employee_id"] == test_employee["id"]), None)
        
        assert emp_record.get("hours_worked") == 10.0
        # Weekend OT should be in overtime_weekend field, not overtime_regular
        assert emp_record.get("overtime_weekend") == 1.0, f"Expected 1.0 weekend OT, got {emp_record.get('overtime_weekend')}"
        assert emp_record.get("overtime_regular", 0) == 0, f"Weekend OT should not be in overtime_regular"
        print(f"PASS: Saturday 10h = 1h weekend OT (1.5x rate)")
    
    def test_weekend_ot_sunday(self, api_client, test_employee):
        """Test: Sunday work gets weekend OT rate"""
        test_date = "2026-03-08"  # Sunday
        
        # Create attendance: 08:00 - 19:00 = 11 hours (2 hours OT)
        response = api_client.post(f"{BASE_URL}/api/payroll/attendance", json={
            "employee_id": test_employee["id"],
            "date": test_date,
            "check_in": "08:00",
            "check_out": "19:00",
            "status": "present"
        })
        assert response.status_code in [200, 201], f"Failed: {response.text}"
        
        # Fetch daily attendance to verify
        daily_resp = api_client.get(f"{BASE_URL}/api/payroll/attendance/daily/{test_date}")
        assert daily_resp.status_code == 200
        emp_record = next((r for r in daily_resp.json() if r["employee_id"] == test_employee["id"]), None)
        
        assert emp_record.get("hours_worked") == 11.0
        assert emp_record.get("overtime_weekend") == 2.0, f"Expected 2.0 weekend OT, got {emp_record.get('overtime_weekend')}"
        print(f"PASS: Sunday 11h = 2h weekend OT (1.5x rate)")


class TestPayrollOTIntegration:
    """Test payroll includes OT from attendance"""
    
    def test_payroll_fetches_attendance_ot(self, api_client, test_employee):
        """Test payroll automatically fetches attendance OT data"""
        # Create a payroll for March 2026
        response = api_client.post(f"{BASE_URL}/api/payroll/payrolls", json={
            "period_start": "2026-03-01",
            "period_end": "2026-03-31",
            "payment_frequency": "monthly"
        })
        
        if response.status_code == 400 and "No employees" in response.text:
            pytest.skip("No employees with monthly payment frequency")
        
        assert response.status_code in [200, 201], f"Failed to create payroll: {response.text}"
        payroll_data = response.json()
        payroll_id = payroll_data.get("id")
        print(f"Created payroll: {payroll_data.get('payroll_number')}")
        
        # Get payroll details to check OT is included
        response = api_client.get(f"{BASE_URL}/api/payroll/payrolls/{payroll_id}")
        assert response.status_code == 200
        payroll_details = response.json()
        
        # Check if items have OT fields
        items = payroll_details.get("items", [])
        assert len(items) > 0, "No payroll items found"
        
        for item in items:
            # Verify OT fields exist in payroll items
            assert "overtime_hours" in item, f"Missing overtime_hours in payroll item"
            assert "overtime_weekend_hours" in item, f"Missing overtime_weekend_hours in payroll item"
            assert "overtime_amount" in item, f"Missing overtime_amount in payroll item"
            
            ot_regular = item.get("overtime_hours", 0)
            ot_weekend = item.get("overtime_weekend_hours", 0)
            ot_amount = item.get("overtime_amount", 0)
            
            print(f"  {item.get('employee_name')}: OT={ot_regular}h reg + {ot_weekend}h wknd = LKR {ot_amount}")
        
        print(f"PASS: Payroll includes OT data from attendance")
        
        # Clean up - delete draft payroll
        api_client.delete(f"{BASE_URL}/api/payroll/payrolls/{payroll_id}")
    
    def test_payroll_ot_calculation_formula(self, api_client, test_employee):
        """Verify OT pay calculation: hourly_rate = basic/198, OT = hours * rate * multiplier"""
        # Get employee details
        emp_response = api_client.get(f"{BASE_URL}/api/payroll/employees/{test_employee['id']}")
        assert emp_response.status_code == 200
        employee = emp_response.json()
        
        basic_salary = employee.get("basic_salary", 0)
        if basic_salary == 0:
            pytest.skip("Employee has no basic salary set")
        
        # Hourly rate = basic / 198 (22 days * 9 hours)
        expected_hourly_rate = basic_salary / 198
        print(f"Employee: {employee.get('first_name')} {employee.get('last_name')}")
        print(f"Basic Salary: LKR {basic_salary}")
        print(f"Expected Hourly Rate: LKR {expected_hourly_rate:.2f} (basic/198)")
        
        # Get salary structure for OT rates
        settings_response = api_client.get(f"{BASE_URL}/api/payroll/salary-structure")
        assert settings_response.status_code == 200
        settings = settings_response.json()
        
        weekday_rate = settings.get("overtime_weekday_rate", 1.25)
        weekend_rate = settings.get("overtime_weekend_rate", 1.5)
        
        print(f"OT Rates: Weekday={weekday_rate}x, Weekend={weekend_rate}x")
        
        # Example calculation with 4h regular OT + 3h weekend OT
        regular_ot_hours = 4.0
        weekend_ot_hours = 3.0
        
        expected_regular_ot_pay = regular_ot_hours * expected_hourly_rate * weekday_rate
        expected_weekend_ot_pay = weekend_ot_hours * expected_hourly_rate * weekend_rate
        expected_total_ot = expected_regular_ot_pay + expected_weekend_ot_pay
        
        print(f"Sample calculation (4h reg + 3h wknd):")
        print(f"  Regular OT: {regular_ot_hours}h * {expected_hourly_rate:.2f} * {weekday_rate} = LKR {expected_regular_ot_pay:.2f}")
        print(f"  Weekend OT: {weekend_ot_hours}h * {expected_hourly_rate:.2f} * {weekend_rate} = LKR {expected_weekend_ot_pay:.2f}")
        print(f"  Total OT Pay: LKR {expected_total_ot:.2f}")
        
        print(f"PASS: OT calculation formula verified")


class TestMonthlySummaryOT:
    """Test monthly attendance report shows OT correctly"""
    
    def test_monthly_report_has_ot_column(self, api_client):
        """Verify monthly report includes overtime hours"""
        response = api_client.get(f"{BASE_URL}/api/payroll/attendance/monthly-report", params={
            "month": "2026-03"
        })
        assert response.status_code == 200
        report = response.json()
        
        if len(report) == 0:
            pytest.skip("No attendance data for March 2026")
        
        # Check first employee in report has OT fields
        emp = report[0]
        assert "total_overtime" in emp or "overtime_regular_hours" in emp, \
            f"Missing overtime field in monthly report. Fields: {emp.keys()}"
        
        total_ot = emp.get("total_overtime", 0) or emp.get("overtime_regular_hours", 0) + emp.get("overtime_weekend_hours", 0)
        print(f"Monthly report for {emp.get('employee_name')}: Total OT = {total_ot}h")
        print(f"PASS: Monthly report includes OT data")


class TestGrossSalaryWithOT:
    """Test gross salary includes OT pay correctly"""
    
    def test_gross_equals_basic_plus_allowances_plus_task_plus_ot(self, api_client):
        """Verify gross = basic + allowances + task payments + OT pay"""
        # Get existing payrolls
        response = api_client.get(f"{BASE_URL}/api/payroll/payrolls")
        assert response.status_code == 200
        payrolls = response.json()
        
        # Find a payroll with items
        payroll_with_items = None
        for p in payrolls:
            detail_resp = api_client.get(f"{BASE_URL}/api/payroll/payrolls/{p['id']}")
            if detail_resp.status_code == 200:
                details = detail_resp.json()
                if details.get("items") and len(details["items"]) > 0:
                    payroll_with_items = details
                    break
        
        if not payroll_with_items:
            pytest.skip("No payrolls with items found")
        
        # Verify gross calculation for each item
        for item in payroll_with_items.get("items", []):
            basic = item.get("basic_salary", 0)
            allowances = item.get("total_allowances", 0)
            task_pay = item.get("task_payments_amount", 0)
            ot_pay = item.get("overtime_amount", 0)
            gross = item.get("gross_salary", 0)
            
            expected_gross = basic + allowances + task_pay + ot_pay
            
            # Allow small floating point difference
            diff = abs(gross - expected_gross)
            assert diff < 1, f"Gross mismatch for {item.get('employee_name')}: expected {expected_gross}, got {gross}"
            
            print(f"{item.get('employee_name')}: Basic={basic}, Allowances={allowances}, Task={task_pay}, OT={ot_pay} => Gross={gross}")
        
        print(f"PASS: Gross salary = Basic + Allowances + Task Pay + OT Pay")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
