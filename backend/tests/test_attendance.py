"""
Test Attendance Tracking API Endpoints
Tests daily attendance entry, bulk attendance, monthly reports
"""
import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "lahiruraja97@gmail.com"
TEST_PASSWORD = "password123"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json()["access_token"]


@pytest.fixture(scope="module")
def api_client(auth_token):
    """Session with auth header"""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    })
    return session


@pytest.fixture(scope="module")
def employee_id(api_client):
    """Get first active employee ID for testing"""
    response = api_client.get(f"{BASE_URL}/api/payroll/employees")
    assert response.status_code == 200
    employees = response.json()
    assert len(employees) > 0, "No employees found for testing"
    return employees[0]["id"]


class TestAttendanceSettings:
    """Test attendance settings endpoint"""

    def test_get_attendance_settings(self, api_client):
        """GET /attendance/settings - Returns attendance configuration"""
        response = api_client.get(f"{BASE_URL}/api/payroll/attendance/settings")
        assert response.status_code == 200
        
        data = response.json()
        assert "full_day_hours" in data
        assert "half_day_hours" in data
        assert "standard_work_hours" in data
        assert "statuses" in data
        
        # Verify expected values
        assert data["full_day_hours"] == 9.0
        assert data["half_day_hours"] == 5.0
        assert data["standard_work_hours"] == 8.0
        
        # Verify statuses
        statuses = data["statuses"]
        assert len(statuses) == 5
        status_values = [s["value"] for s in statuses]
        assert "present" in status_values
        assert "absent" in status_values
        assert "half_day" in status_values
        assert "late" in status_values
        assert "on_leave" in status_values
        print(f"Attendance settings: Full day={data['full_day_hours']}h, Half day={data['half_day_hours']}h")


class TestDailyAttendance:
    """Test daily attendance endpoints"""

    def test_get_daily_attendance(self, api_client):
        """GET /attendance/daily/{date} - Returns all employees for date"""
        today = datetime.now().strftime("%Y-%m-%d")
        response = api_client.get(f"{BASE_URL}/api/payroll/attendance/daily/{today}")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        
        if len(data) > 0:
            emp = data[0]
            assert "employee_id" in emp
            assert "employee_code" in emp
            assert "employee_name" in emp
            assert "department_name" in emp
            assert "date" in emp
            assert "check_in" in emp
            assert "check_out" in emp
            assert "status" in emp
            print(f"Daily attendance for {today}: {len(data)} employees")
            
            # Check John Doe's attendance (should be present from seed data)
            john_doe = next((e for e in data if "John" in e.get("employee_name", "")), None)
            if john_doe:
                print(f"John Doe: status={john_doe['status']}, check_in={john_doe['check_in']}, check_out={john_doe['check_out']}")
                if john_doe['status'] == 'present':
                    assert john_doe['check_in'] is not None
                    assert john_doe['check_out'] is not None

    def test_get_daily_attendance_with_weekend_detection(self, api_client):
        """Verify date shows correctly with weekend indicator available"""
        # Test with today's date (March 8, 2026 is Sunday)
        sunday = "2026-03-08"
        response = api_client.get(f"{BASE_URL}/api/payroll/attendance/daily/{sunday}")
        assert response.status_code == 200
        print(f"Weekend test date {sunday}: Response OK")


class TestCreateAttendance:
    """Test attendance creation endpoints"""

    def test_create_single_attendance(self, api_client, employee_id):
        """POST /attendance - Create/update single attendance record"""
        # Use a test date
        test_date = "2026-03-07"  # A weekday for testing
        
        response = api_client.post(
            f"{BASE_URL}/api/payroll/attendance",
            json={
                "employee_id": employee_id,
                "date": test_date,
                "check_in": "09:00",
                "check_out": "17:30",
                "status": "present",
                "notes": "TEST_attendance_record"
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "id" in data
        print(f"Created attendance: {data['message']}, id={data['id']}")
        
        # Verify by fetching
        verify_resp = api_client.get(f"{BASE_URL}/api/payroll/attendance/daily/{test_date}")
        assert verify_resp.status_code == 200
        records = verify_resp.json()
        
        emp_record = next((r for r in records if r["employee_id"] == employee_id), None)
        assert emp_record is not None
        assert emp_record["status"] == "present"
        assert emp_record["check_in"] == "09:00"
        assert emp_record["check_out"] == "17:30"
        
        # Hours should be calculated (17:30 - 09:00 = 8.5 hours)
        assert emp_record.get("hours_worked", 0) == 8.5

    def test_create_half_day_attendance(self, api_client, employee_id):
        """POST /attendance - Create half day attendance"""
        test_date = "2026-03-06"
        
        response = api_client.post(
            f"{BASE_URL}/api/payroll/attendance",
            json={
                "employee_id": employee_id,
                "date": test_date,
                "check_in": "08:00",
                "check_out": "13:00",
                "status": "half_day",
                "notes": "TEST_half_day"
            }
        )
        assert response.status_code == 200
        print(f"Half day attendance created for {test_date}")
        
        # Verify hours (13:00 - 08:00 = 5 hours)
        verify_resp = api_client.get(f"{BASE_URL}/api/payroll/attendance/daily/{test_date}")
        records = verify_resp.json()
        emp_record = next((r for r in records if r["employee_id"] == employee_id), None)
        assert emp_record is not None
        assert emp_record["status"] == "half_day"
        assert emp_record.get("hours_worked", 0) == 5.0

    def test_create_late_attendance(self, api_client, employee_id):
        """POST /attendance - Create late attendance with overtime"""
        test_date = "2026-03-05"
        
        response = api_client.post(
            f"{BASE_URL}/api/payroll/attendance",
            json={
                "employee_id": employee_id,
                "date": test_date,
                "check_in": "09:30",
                "check_out": "18:30",
                "status": "late",
                "notes": "TEST_late_arrival"
            }
        )
        assert response.status_code == 200
        print(f"Late attendance created for {test_date}")
        
        # Verify (18:30 - 09:30 = 9 hours, 1h overtime)
        verify_resp = api_client.get(f"{BASE_URL}/api/payroll/attendance/daily/{test_date}")
        records = verify_resp.json()
        emp_record = next((r for r in records if r["employee_id"] == employee_id), None)
        assert emp_record is not None
        assert emp_record["status"] == "late"
        assert emp_record.get("hours_worked", 0) == 9.0
        # Overtime is hours > 8
        assert emp_record.get("overtime_regular", 0) == 1.0

    def test_create_absent_attendance(self, api_client, employee_id):
        """POST /attendance - Create absent record"""
        test_date = "2026-03-04"
        
        response = api_client.post(
            f"{BASE_URL}/api/payroll/attendance",
            json={
                "employee_id": employee_id,
                "date": test_date,
                "check_in": None,
                "check_out": None,
                "status": "absent",
                "notes": "TEST_absent"
            }
        )
        assert response.status_code == 200
        print(f"Absent attendance created for {test_date}")

    def test_create_on_leave_attendance(self, api_client, employee_id):
        """POST /attendance - Create on_leave record"""
        test_date = "2026-03-03"
        
        response = api_client.post(
            f"{BASE_URL}/api/payroll/attendance",
            json={
                "employee_id": employee_id,
                "date": test_date,
                "check_in": None,
                "check_out": None,
                "status": "on_leave",
                "notes": "TEST_on_leave"
            }
        )
        assert response.status_code == 200
        print(f"On leave attendance created for {test_date}")


class TestBulkAttendance:
    """Test bulk attendance creation"""

    def test_create_bulk_attendance(self, api_client):
        """POST /attendance/bulk - Save multiple employees at once"""
        # Get employees
        emp_resp = api_client.get(f"{BASE_URL}/api/payroll/employees")
        employees = emp_resp.json()
        
        if len(employees) < 1:
            pytest.skip("No employees to test bulk attendance")
        
        test_date = "2026-03-02"
        
        # Create records for each employee
        records = []
        for emp in employees[:3]:  # Max 3 employees
            records.append({
                "employee_id": emp["id"],
                "status": "present",
                "check_in": "08:00",
                "check_out": "17:00",
                "notes": "TEST_bulk_attendance"
            })
        
        response = api_client.post(
            f"{BASE_URL}/api/payroll/attendance/bulk",
            json={
                "date": test_date,
                "records": records
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        print(f"Bulk attendance result: {data['message']}")
        
        # Verify records
        verify_resp = api_client.get(f"{BASE_URL}/api/payroll/attendance/daily/{test_date}")
        assert verify_resp.status_code == 200
        daily_records = verify_resp.json()
        
        # Check that our employees have records
        for rec in records:
            emp_record = next((r for r in daily_records if r["employee_id"] == rec["employee_id"]), None)
            assert emp_record is not None, f"Record not found for employee {rec['employee_id']}"
            assert emp_record["status"] == "present"


class TestOvertimeCalculation:
    """Test overtime calculation including weekend rates"""

    def test_weekday_overtime(self, api_client, employee_id):
        """Verify weekday overtime is calculated correctly"""
        # March 2, 2026 is Monday (weekday)
        test_date = "2026-03-02"
        
        # 10 hours worked = 2 hours overtime
        response = api_client.post(
            f"{BASE_URL}/api/payroll/attendance",
            json={
                "employee_id": employee_id,
                "date": test_date,
                "check_in": "08:00",
                "check_out": "18:00",  # 10 hours
                "status": "present",
                "notes": "TEST_weekday_overtime"
            }
        )
        assert response.status_code == 200
        
        # Verify overtime calculation
        verify_resp = api_client.get(f"{BASE_URL}/api/payroll/attendance/daily/{test_date}")
        records = verify_resp.json()
        emp_record = next((r for r in records if r["employee_id"] == employee_id), None)
        
        assert emp_record is not None
        assert emp_record.get("hours_worked", 0) == 10.0
        assert emp_record.get("overtime_regular", 0) == 2.0  # 10 - 8 = 2 OT
        assert emp_record.get("overtime_weekend", 0) == 0  # No weekend OT
        print(f"Weekday overtime: {emp_record['overtime_regular']}h (expected 2h)")

    def test_weekend_overtime(self, api_client, employee_id):
        """Verify weekend overtime is calculated with 1.5x rate indicator"""
        # March 8, 2026 is Sunday (weekend)
        test_date = "2026-03-08"
        
        # First check if there's already an existing record
        get_resp = api_client.get(f"{BASE_URL}/api/payroll/attendance/daily/{test_date}")
        records = get_resp.json()
        emp_record = next((r for r in records if r["employee_id"] == employee_id), None)
        
        if emp_record and emp_record.get("has_record"):
            # Record exists, verify weekend OT is tracked
            hours_worked = emp_record.get("hours_worked", 0)
            overtime_weekend = emp_record.get("overtime_weekend", 0)
            print(f"Weekend record exists: {hours_worked}h, weekend OT={overtime_weekend}h")
            
            if hours_worked > 8:
                assert overtime_weekend > 0, "Weekend overtime should be recorded"
        else:
            # Create a weekend attendance
            response = api_client.post(
                f"{BASE_URL}/api/payroll/attendance",
                json={
                    "employee_id": employee_id,
                    "date": test_date,
                    "check_in": "08:00",
                    "check_out": "17:30",  # 9.5 hours
                    "status": "present",
                    "notes": "TEST_weekend_overtime"
                }
            )
            assert response.status_code == 200
            
            # Verify weekend overtime
            verify_resp = api_client.get(f"{BASE_URL}/api/payroll/attendance/daily/{test_date}")
            records = verify_resp.json()
            emp_record = next((r for r in records if r["employee_id"] == employee_id), None)
            
            assert emp_record is not None
            assert emp_record.get("overtime_weekend", 0) == 1.5  # 9.5 - 8 = 1.5 weekend OT
            print(f"Weekend overtime: {emp_record['overtime_weekend']}h (expected 1.5h)")


class TestEmployeeAttendanceSummary:
    """Test individual employee attendance summary"""

    def test_get_employee_summary(self, api_client, employee_id):
        """GET /attendance/summary/{employee_id} - Monthly summary"""
        month = "2026-03"
        
        response = api_client.get(
            f"{BASE_URL}/api/payroll/attendance/summary/{employee_id}",
            params={"month": month}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "employee_id" in data
        assert "month" in data
        assert "present_days" in data
        assert "half_days" in data
        assert "absent_days" in data
        assert "late_days" in data
        assert "leave_days" in data
        assert "total_hours_worked" in data
        assert "overtime_regular_hours" in data
        assert "overtime_weekend_hours" in data
        assert "total_overtime_hours" in data
        
        print(f"Summary for {month}: Present={data['present_days']}, Half={data['half_days']}, "
              f"Absent={data['absent_days']}, Late={data['late_days']}, Leave={data['leave_days']}")
        print(f"Hours: Total={data['total_hours_worked']}h, OT Regular={data['overtime_regular_hours']}h, "
              f"OT Weekend={data['overtime_weekend_hours']}h")


class TestMonthlyAttendanceReport:
    """Test monthly attendance report"""

    def test_get_monthly_report(self, api_client):
        """GET /attendance/monthly-report - All employees summary"""
        month = "2026-03"
        
        response = api_client.get(
            f"{BASE_URL}/api/payroll/attendance/monthly-report",
            params={"month": month}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        
        if len(data) > 0:
            emp = data[0]
            assert "employee_id" in emp
            assert "employee_code" in emp
            assert "employee_name" in emp
            assert "department_name" in emp
            assert "present_days" in emp
            assert "half_days" in emp
            assert "absent_days" in emp
            assert "late_days" in emp
            assert "leave_days" in emp
            assert "working_days" in emp
            assert "total_hours" in emp
            assert "total_overtime" in emp
            
            print(f"Monthly report for {month}: {len(data)} employees")
            for e in data:
                print(f"  {e['employee_name']}: P={e['present_days']}, H={e['half_days']}, "
                      f"A={e['absent_days']}, L={e['late_days']}, WD={e['working_days']}, "
                      f"Hrs={e['total_hours']}, OT={e['total_overtime']}")

    def test_get_monthly_report_with_department_filter(self, api_client):
        """GET /attendance/monthly-report with department filter"""
        # Get departments
        dept_resp = api_client.get(f"{BASE_URL}/api/payroll/departments")
        departments = dept_resp.json()
        
        if len(departments) == 0:
            pytest.skip("No departments to filter by")
        
        month = "2026-03"
        dept_id = departments[0]["id"]
        
        response = api_client.get(
            f"{BASE_URL}/api/payroll/attendance/monthly-report",
            params={"month": month, "department_id": dept_id}
        )
        assert response.status_code == 200
        
        data = response.json()
        print(f"Monthly report filtered by department {departments[0]['name']}: {len(data)} employees")


class TestAttendanceValidation:
    """Test validation and error cases"""

    def test_invalid_employee_id(self, api_client):
        """POST /attendance - Invalid employee returns 404"""
        response = api_client.post(
            f"{BASE_URL}/api/payroll/attendance",
            json={
                "employee_id": "invalid-id-12345",
                "date": "2026-03-01",
                "check_in": "08:00",
                "check_out": "17:00",
                "status": "present"
            }
        )
        assert response.status_code == 404

    def test_update_existing_attendance(self, api_client, employee_id):
        """POST /attendance - Update existing record"""
        test_date = "2026-03-01"
        
        # Create initial record
        response1 = api_client.post(
            f"{BASE_URL}/api/payroll/attendance",
            json={
                "employee_id": employee_id,
                "date": test_date,
                "check_in": "08:00",
                "check_out": "17:00",
                "status": "present"
            }
        )
        assert response1.status_code == 200
        
        # Update same date
        response2 = api_client.post(
            f"{BASE_URL}/api/payroll/attendance",
            json={
                "employee_id": employee_id,
                "date": test_date,
                "check_in": "08:30",
                "check_out": "18:00",
                "status": "late"
            }
        )
        assert response2.status_code == 200
        assert "updated" in response2.json().get("message", "").lower() or response2.json().get("id")
        
        # Verify update
        verify_resp = api_client.get(f"{BASE_URL}/api/payroll/attendance/daily/{test_date}")
        records = verify_resp.json()
        emp_record = next((r for r in records if r["employee_id"] == employee_id), None)
        
        assert emp_record is not None
        assert emp_record["check_in"] == "08:30"
        assert emp_record["check_out"] == "18:00"
        assert emp_record["status"] == "late"
        print("Update existing attendance: SUCCESS")


class TestCleanup:
    """Cleanup test data"""

    def test_cleanup_test_records(self, api_client):
        """Delete TEST_ records"""
        # Get all attendance records
        response = api_client.get(
            f"{BASE_URL}/api/payroll/attendance",
            params={"month": "2026-03"}
        )
        
        if response.status_code == 200:
            records = response.json()
            deleted = 0
            for rec in records:
                if rec.get("notes") and "TEST_" in rec.get("notes", ""):
                    del_resp = api_client.delete(
                        f"{BASE_URL}/api/payroll/attendance/{rec['id']}"
                    )
                    if del_resp.status_code == 200:
                        deleted += 1
            print(f"Cleaned up {deleted} test records")
