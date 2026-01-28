"""
Backend Tests for ERP System - Phase 2 Finance & Admin Features
Tests: Chart of Accounts, Journal Entries, Financial Reports, Admin Controls
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


class TestAuthFlow:
    """Authentication tests"""
    
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
        assert data["user"]["email"] == TEST_EMAIL
        assert data["user"]["role"] == "admin"
        print(f"✓ Login successful for {TEST_EMAIL}")
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "wrong@example.com",
            "password": "wrongpass"
        })
        assert response.status_code == 401
        print("✓ Invalid credentials rejected correctly")
    
    def test_get_current_user(self, auth_token):
        """Test getting current user info"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == TEST_EMAIL
        print(f"✓ Current user retrieved: {data['full_name']}")


class TestChartOfAccounts:
    """Chart of Accounts CRUD tests"""
    
    def test_get_chart_of_accounts(self, auth_token):
        """Test retrieving chart of accounts"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/finance/chart-of-accounts", headers=headers)
        assert response.status_code == 200
        accounts = response.json()
        assert isinstance(accounts, list)
        assert len(accounts) >= 28, f"Expected at least 28 default accounts, got {len(accounts)}"
        print(f"✓ Retrieved {len(accounts)} accounts")
        
        # Verify account structure
        if accounts:
            account = accounts[0]
            assert "id" in account
            assert "code" in account
            assert "name" in account
            assert "account_type" in account
            assert "is_system" in account
    
    def test_get_accounts_by_type(self, auth_token):
        """Test filtering accounts by type"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Test asset accounts
        response = requests.get(f"{BASE_URL}/api/finance/chart-of-accounts?account_type=asset", headers=headers)
        assert response.status_code == 200
        assets = response.json()
        assert all(a["account_type"] == "asset" for a in assets)
        print(f"✓ Retrieved {len(assets)} asset accounts")
        
        # Test expense accounts
        response = requests.get(f"{BASE_URL}/api/finance/chart-of-accounts?account_type=expense", headers=headers)
        assert response.status_code == 200
        expenses = response.json()
        assert all(e["account_type"] == "expense" for e in expenses)
        print(f"✓ Retrieved {len(expenses)} expense accounts")
    
    def test_create_account(self, auth_token):
        """Test creating a new account"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Create a test account
        test_account = {
            "code": "TEST001",
            "name": "TEST Test Account",
            "account_type": "expense",
            "category": "operating_expense",
            "description": "Test account for automated testing",
            "is_system": False,
            "opening_balance": 0
        }
        
        response = requests.post(f"{BASE_URL}/api/finance/chart-of-accounts", 
                                headers=headers, json=test_account)
        
        if response.status_code == 400 and "already exists" in response.text:
            print("✓ Account already exists (from previous test)")
            return
        
        assert response.status_code == 200, f"Create account failed: {response.text}"
        data = response.json()
        assert data["code"] == "TEST001"
        assert data["name"] == "TEST Test Account"
        print(f"✓ Created account: {data['name']}")
    
    def test_update_account(self, auth_token):
        """Test updating an account"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Get accounts to find a non-system account
        response = requests.get(f"{BASE_URL}/api/finance/chart-of-accounts", headers=headers)
        accounts = response.json()
        
        # Find a non-system account
        non_system = [a for a in accounts if not a.get("is_system")]
        if not non_system:
            print("⚠ No non-system accounts to update")
            return
        
        account = non_system[0]
        update_data = {"description": f"Updated at {datetime.now().isoformat()}"}
        
        response = requests.put(f"{BASE_URL}/api/finance/chart-of-accounts/{account['id']}", 
                               headers=headers, json=update_data)
        assert response.status_code == 200
        print(f"✓ Updated account: {account['name']}")
    
    def test_cannot_delete_system_account(self, auth_token):
        """Test that system accounts cannot be deleted"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Get accounts
        response = requests.get(f"{BASE_URL}/api/finance/chart-of-accounts", headers=headers)
        accounts = response.json()
        
        # Find a system account
        system_accounts = [a for a in accounts if a.get("is_system")]
        if not system_accounts:
            print("⚠ No system accounts found")
            return
        
        account = system_accounts[0]
        response = requests.delete(f"{BASE_URL}/api/finance/chart-of-accounts/{account['id']}", 
                                  headers=headers)
        assert response.status_code == 400
        assert "system account" in response.text.lower()
        print(f"✓ System account deletion correctly blocked: {account['name']}")


class TestJournalEntries:
    """Journal Entry tests with double-entry validation"""
    
    def test_create_balanced_journal_entry(self, auth_token):
        """Test creating a balanced journal entry"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Get accounts for the entry
        response = requests.get(f"{BASE_URL}/api/finance/chart-of-accounts", headers=headers)
        accounts = response.json()
        
        # Find cash and expense accounts
        cash_account = next((a for a in accounts if a["code"] == "1100"), None)
        expense_account = next((a for a in accounts if a["code"] == "6100"), None)
        
        if not cash_account or not expense_account:
            print("⚠ Required accounts not found")
            return
        
        # Create balanced entry (debit expense, credit cash)
        entry_data = {
            "entry_date": datetime.now().strftime("%Y-%m-%d"),
            "reference_number": f"TEST-{datetime.now().strftime('%H%M%S')}",
            "description": "TEST Salary payment",
            "lines": [
                {
                    "account_id": expense_account["id"],
                    "debit": 10000,
                    "credit": 0,
                    "description": "Salary expense"
                },
                {
                    "account_id": cash_account["id"],
                    "debit": 0,
                    "credit": 10000,
                    "description": "Cash payment"
                }
            ],
            "is_auto_generated": False
        }
        
        response = requests.post(f"{BASE_URL}/api/finance/journal-entries", 
                                headers=headers, json=entry_data)
        assert response.status_code == 200, f"Create entry failed: {response.text}"
        data = response.json()
        assert data["is_balanced"] == True
        assert data["total_debit"] == 10000
        assert data["total_credit"] == 10000
        print(f"✓ Created balanced journal entry: {data['entry_number']}")
    
    def test_reject_unbalanced_entry(self, auth_token):
        """Test that unbalanced entries are rejected"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Get accounts
        response = requests.get(f"{BASE_URL}/api/finance/chart-of-accounts", headers=headers)
        accounts = response.json()
        
        cash_account = next((a for a in accounts if a["code"] == "1100"), None)
        expense_account = next((a for a in accounts if a["code"] == "6100"), None)
        
        if not cash_account or not expense_account:
            print("⚠ Required accounts not found")
            return
        
        # Create unbalanced entry
        entry_data = {
            "entry_date": datetime.now().strftime("%Y-%m-%d"),
            "reference_number": f"UNBAL-{datetime.now().strftime('%H%M%S')}",
            "description": "Unbalanced test entry",
            "lines": [
                {
                    "account_id": expense_account["id"],
                    "debit": 10000,
                    "credit": 0,
                    "description": "Expense"
                },
                {
                    "account_id": cash_account["id"],
                    "debit": 0,
                    "credit": 5000,  # Intentionally unbalanced
                    "description": "Cash"
                }
            ],
            "is_auto_generated": False
        }
        
        response = requests.post(f"{BASE_URL}/api/finance/journal-entries", 
                                headers=headers, json=entry_data)
        assert response.status_code == 400
        assert "not balanced" in response.text.lower()
        print("✓ Unbalanced entry correctly rejected")
    
    def test_get_journal_entries(self, auth_token):
        """Test retrieving journal entries"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/finance/journal-entries", headers=headers)
        assert response.status_code == 200
        entries = response.json()
        assert isinstance(entries, list)
        print(f"✓ Retrieved {len(entries)} journal entries")


class TestGeneralLedger:
    """General Ledger tests"""
    
    def test_get_general_ledger(self, auth_token):
        """Test retrieving general ledger"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/finance/general-ledger", headers=headers)
        assert response.status_code == 200
        ledger = response.json()
        assert isinstance(ledger, list)
        print(f"✓ Retrieved general ledger with {len(ledger)} accounts")
        
        # Verify ledger structure
        if ledger:
            entry = ledger[0]
            assert "account_id" in entry
            assert "account_code" in entry
            assert "account_name" in entry
            assert "transactions" in entry
            assert "closing_balance" in entry
    
    def test_get_ledger_by_account(self, auth_token):
        """Test filtering ledger by account"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Get accounts first
        response = requests.get(f"{BASE_URL}/api/finance/chart-of-accounts", headers=headers)
        accounts = response.json()
        
        if accounts:
            account_id = accounts[0]["id"]
            response = requests.get(f"{BASE_URL}/api/finance/general-ledger?account_id={account_id}", 
                                   headers=headers)
            assert response.status_code == 200
            ledger = response.json()
            assert len(ledger) <= 1  # Should only return one account
            print(f"✓ Retrieved ledger for specific account")


class TestFinancialReports:
    """Financial Reports tests"""
    
    def test_trial_balance(self, auth_token):
        """Test trial balance report"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/finance/reports/trial-balance", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "as_of_date" in data
        assert "accounts" in data
        assert "total_debit" in data
        assert "total_credit" in data
        assert "is_balanced" in data
        
        # Trial balance should be balanced
        assert data["is_balanced"] == True, "Trial balance is not balanced!"
        print(f"✓ Trial balance retrieved - Balanced: {data['is_balanced']}")
    
    def test_profit_loss_report(self, auth_token):
        """Test profit & loss report"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/finance/reports/profit-loss", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "period" in data
        assert "income" in data
        assert "expenses" in data
        assert "net_profit" in data
        print(f"✓ P&L report retrieved - Net Profit: {data['net_profit']}")
    
    def test_balance_sheet(self, auth_token):
        """Test balance sheet report"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/finance/reports/balance-sheet", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "as_of_date" in data
        assert "assets" in data
        assert "liabilities" in data
        assert "equity" in data
        assert "total_assets" in data
        assert "total_liabilities_equity" in data
        print(f"✓ Balance sheet retrieved - Assets: {data['total_assets']}")
    
    def test_cash_flow_report(self, auth_token):
        """Test cash flow report"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/finance/reports/cash-flow", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "period" in data
        assert "operating_activities" in data
        assert "opening_cash_balance" in data
        assert "closing_cash_balance" in data
        print(f"✓ Cash flow report retrieved - Closing balance: {data['closing_cash_balance']}")


class TestAdminSystemInfo:
    """Admin System Info tests"""
    
    def test_get_system_info(self, auth_token):
        """Test retrieving system information"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/system-info", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "collection_stats" in data
        assert "total_records" in data
        assert "backup_count" in data
        print(f"✓ System info retrieved - Total records: {data['total_records']}")
    
    def test_get_backups_list(self, auth_token):
        """Test retrieving backups list"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/backups", headers=headers)
        assert response.status_code == 200
        backups = response.json()
        assert isinstance(backups, list)
        print(f"✓ Retrieved {len(backups)} backups")


class TestAdminBackup:
    """Admin Backup functionality tests"""
    
    def test_create_backup(self, auth_token):
        """Test creating a backup"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        backup_data = {
            "name": f"TEST-backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "description": "Automated test backup",
            "backup_type": "full"
        }
        
        response = requests.post(f"{BASE_URL}/api/admin/backups", 
                                headers=headers, json=backup_data)
        assert response.status_code == 200, f"Backup creation failed: {response.text}"
        data = response.json()
        assert "id" in data
        assert data["status"] == "completed"
        print(f"✓ Backup created: {data['name']}")
        return data["id"]
    
    def test_get_backup_details(self, auth_token):
        """Test getting backup details"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # First create a backup
        backup_data = {
            "name": f"TEST-detail-{datetime.now().strftime('%H%M%S')}",
            "backup_type": "full"
        }
        create_response = requests.post(f"{BASE_URL}/api/admin/backups", 
                                       headers=headers, json=backup_data)
        if create_response.status_code != 200:
            print("⚠ Could not create backup for detail test")
            return
        
        backup_id = create_response.json()["id"]
        
        # Get backup details
        response = requests.get(f"{BASE_URL}/api/admin/backups/{backup_id}", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == backup_id
        print(f"✓ Retrieved backup details: {data['name']}")


class TestAdminDataReset:
    """Admin Data Reset tests"""
    
    def test_reset_preview(self, auth_token):
        """Test data reset preview"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/data-reset/preview?reset_type=transactional", 
                               headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        assert "collections" in data
        assert "warnings" in data
        print(f"✓ Reset preview retrieved - Collections: {len(data['collections'])}")
    
    def test_reset_requires_confirmation(self, auth_token):
        """Test that reset requires correct confirmation code"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Try with wrong confirmation code
        reset_data = {
            "reset_type": "transactional",
            "confirmation_code": "WRONG",
            "keep_users": True,
            "keep_company_settings": True
        }
        
        response = requests.post(f"{BASE_URL}/api/admin/data-reset", 
                                headers=headers, json=reset_data)
        assert response.status_code == 400
        assert "confirmation" in response.text.lower()
        print("✓ Reset correctly requires proper confirmation code")


class TestRestorePreview:
    """Restore preview tests"""
    
    def test_restore_preview(self, auth_token):
        """Test restore preview functionality"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # First get backups
        response = requests.get(f"{BASE_URL}/api/admin/backups", headers=headers)
        backups = response.json()
        
        if not backups:
            print("⚠ No backups available for restore preview test")
            return
        
        backup_id = backups[0]["id"]
        response = requests.get(f"{BASE_URL}/api/admin/restore/preview/{backup_id}", 
                               headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "collections" in data
        print(f"✓ Restore preview retrieved for backup: {backups[0]['name']}")


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
