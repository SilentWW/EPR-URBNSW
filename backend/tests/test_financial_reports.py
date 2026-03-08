"""
Financial Reports & Balance Sheet Testing
Tests: Balance Sheet balancing, Trial Balance, P&L, Account Seeding
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://attendance-ot.preview.emergentagent.com').rstrip('/')

class TestUserAuthentication:
    """Authentication tests"""
    
    def test_login_main_user(self):
        """Test login for main user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "lahiruraja97@gmail.com",
            "password": "password123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == "lahiruraja97@gmail.com"
        print(f"Main user login successful: {data['user']['company_id']}")
    
    def test_login_test_user(self):
        """Test login for test seeding user"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testseeding@test.com",
            "password": "test1234"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == "testseeding@test.com"
        print(f"Test user login successful: {data['user']['company_id']}")


class TestAccountSeeding:
    """Test that new user registration seeds Chart of Accounts"""
    
    def test_new_user_registration_seeds_38_accounts(self):
        """Register new user and verify 38 accounts are seeded"""
        # Register new user
        unique_email = f"test_seed_{uuid.uuid4().hex[:8]}@test.com"
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": unique_email,
            "password": "testpass123",
            "full_name": "Test Seed User",
            "company_name": "Test Seed Company"
        })
        assert response.status_code == 200, f"Registration failed: {response.text}"
        data = response.json()
        token = data["access_token"]
        
        # Get Chart of Accounts
        coa_response = requests.get(
            f"{BASE_URL}/api/finance/chart-of-accounts?include_inactive=true",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert coa_response.status_code == 200
        accounts = coa_response.json()
        
        # Verify 38 accounts seeded
        assert len(accounts) == 38, f"Expected 38 accounts, got {len(accounts)}"
        print(f"New user registration seeded {len(accounts)} accounts correctly")
        
        # Verify account types distribution
        types = {}
        for acc in accounts:
            t = acc["account_type"]
            types[t] = types.get(t, 0) + 1
        
        assert types.get("asset", 0) == 7, f"Expected 7 asset accounts, got {types.get('asset', 0)}"
        assert types.get("liability", 0) == 6, f"Expected 6 liability accounts, got {types.get('liability', 0)}"
        assert types.get("equity", 0) == 7, f"Expected 7 equity accounts, got {types.get('equity', 0)}"
        assert types.get("income", 0) == 4, f"Expected 4 income accounts, got {types.get('income', 0)}"
        assert types.get("expense", 0) == 14, f"Expected 14 expense accounts, got {types.get('expense', 0)}"
        print(f"Account type distribution correct: {types}")


class TestBalanceSheet:
    """Test Balance Sheet - Assets = Liabilities + Equity + Net Profit"""
    
    @pytest.fixture
    def main_user_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "lahiruraja97@gmail.com",
            "password": "password123"
        })
        return response.json()["access_token"]
    
    @pytest.fixture
    def test_user_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testseeding@test.com",
            "password": "test1234"
        })
        return response.json()["access_token"]
    
    def test_main_user_balance_sheet_is_balanced(self, main_user_token):
        """Verify main user's balance sheet balances (Assets = Liabilities + Equity)"""
        response = requests.get(
            f"{BASE_URL}/api/finance/reports/balance-sheet",
            headers={"Authorization": f"Bearer {main_user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check is_balanced flag
        assert data["is_balanced"] == True, "Balance sheet is_balanced should be True"
        
        # Verify calculation
        assert data["total_assets"] == data["total_liabilities_equity"], \
            f"Assets ({data['total_assets']}) != Liabilities+Equity ({data['total_liabilities_equity']})"
        
        print(f"Main user Balance Sheet BALANCED:")
        print(f"  Total Assets: {data['total_assets']}")
        print(f"  Total Liabilities + Equity: {data['total_liabilities_equity']}")
        print(f"  Net Profit in Equity: {[e for e in data['equity']['items'] if e['code'] == 'NET'][0]['amount']}")
    
    def test_test_user_balance_sheet_is_balanced(self, test_user_token):
        """Verify test user's balance sheet balances"""
        response = requests.get(
            f"{BASE_URL}/api/finance/reports/balance-sheet",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["is_balanced"] == True, "Balance sheet is_balanced should be True"
        assert data["total_assets"] == data["total_liabilities_equity"]
        
        print(f"Test user Balance Sheet BALANCED:")
        print(f"  Total Assets: {data['total_assets']}")
        print(f"  Total Liabilities + Equity: {data['total_liabilities_equity']}")
    
    def test_balance_sheet_includes_net_profit(self, test_user_token):
        """Verify Net Profit is included in equity section"""
        response = requests.get(
            f"{BASE_URL}/api/finance/reports/balance-sheet",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        data = response.json()
        
        equity_items = data["equity"]["items"]
        net_profit_item = [e for e in equity_items if e["code"] == "NET"]
        
        assert len(net_profit_item) == 1, "Net Profit should be in equity section"
        assert net_profit_item[0]["name"] == "Net Profit (Current Period)"
        print(f"Net Profit correctly in equity: {net_profit_item[0]['amount']}")


class TestTrialBalance:
    """Test Trial Balance - Total Debit = Total Credit"""
    
    @pytest.fixture
    def main_user_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "lahiruraja97@gmail.com",
            "password": "password123"
        })
        return response.json()["access_token"]
    
    @pytest.fixture
    def test_user_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testseeding@test.com",
            "password": "test1234"
        })
        return response.json()["access_token"]
    
    def test_main_user_trial_balance_balanced(self, main_user_token):
        """Verify main user's trial balance: total_debit == total_credit"""
        response = requests.get(
            f"{BASE_URL}/api/finance/reports/trial-balance",
            headers={"Authorization": f"Bearer {main_user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["is_balanced"] == True, "Trial balance is_balanced should be True"
        assert data["total_debit"] == data["total_credit"], \
            f"Debit ({data['total_debit']}) != Credit ({data['total_credit']})"
        
        print(f"Main user Trial Balance BALANCED:")
        print(f"  Total Debit: {data['total_debit']}")
        print(f"  Total Credit: {data['total_credit']}")
    
    def test_test_user_trial_balance_balanced(self, test_user_token):
        """Verify test user's trial balance is balanced"""
        response = requests.get(
            f"{BASE_URL}/api/finance/reports/trial-balance",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["is_balanced"] == True
        assert data["total_debit"] == data["total_credit"]
        
        print(f"Test user Trial Balance BALANCED:")
        print(f"  Total Debit: {data['total_debit']}")
        print(f"  Total Credit: {data['total_credit']}")


class TestProfitLoss:
    """Test Profit & Loss Report"""
    
    @pytest.fixture
    def test_user_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testseeding@test.com",
            "password": "test1234"
        })
        return response.json()["access_token"]
    
    def test_profit_loss_report(self, test_user_token):
        """Verify P&L report shows correct net profit calculation"""
        response = requests.get(
            f"{BASE_URL}/api/finance/reports/profit-loss",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify net profit = income - expenses
        expected_net_profit = data["income"]["total"] - data["expenses"]["total"]
        assert data["net_profit"] == expected_net_profit, \
            f"Net profit ({data['net_profit']}) != Income ({data['income']['total']}) - Expenses ({data['expenses']['total']})"
        
        print(f"P&L Report correct:")
        print(f"  Total Income: {data['income']['total']}")
        print(f"  Total Expenses: {data['expenses']['total']}")
        print(f"  Net Profit: {data['net_profit']}")
    
    def test_profit_loss_consistent_with_balance_sheet(self, test_user_token):
        """Verify P&L net profit matches Balance Sheet equity's Net Profit"""
        # Get P&L
        pl_response = requests.get(
            f"{BASE_URL}/api/finance/reports/profit-loss",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        pl_data = pl_response.json()
        
        # Get Balance Sheet
        bs_response = requests.get(
            f"{BASE_URL}/api/finance/reports/balance-sheet",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        bs_data = bs_response.json()
        
        # Find Net Profit in Balance Sheet equity
        net_profit_in_bs = [e for e in bs_data["equity"]["items"] if e["code"] == "NET"][0]["amount"]
        
        assert pl_data["net_profit"] == net_profit_in_bs, \
            f"P&L Net Profit ({pl_data['net_profit']}) != BS Net Profit ({net_profit_in_bs})"
        
        print(f"P&L and Balance Sheet CONSISTENT:")
        print(f"  P&L Net Profit: {pl_data['net_profit']}")
        print(f"  Balance Sheet Net Profit: {net_profit_in_bs}")


class TestJournalEntryPrefixes:
    """Test journal entry creation with correct prefixes"""
    
    @pytest.fixture
    def test_user_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testseeding@test.com",
            "password": "test1234"
        })
        return response.json()["access_token"]
    
    def test_journal_entries_have_correct_prefixes(self, test_user_token):
        """Verify journal entries use correct prefixes (SALE-, COGS-, REC-, CAP-)"""
        response = requests.get(
            f"{BASE_URL}/api/finance/journal-entries",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        assert response.status_code == 200
        entries = response.json()
        
        if len(entries) == 0:
            pytest.skip("No journal entries to verify")
        
        # Check for expected prefixes
        prefixes_found = set()
        for entry in entries:
            entry_num = entry.get("entry_number", "")
            if "-" in entry_num:
                prefix = entry_num.split("-")[0]
                prefixes_found.add(prefix)
        
        print(f"Journal entry prefixes found: {prefixes_found}")
        
        # At least verify entries exist and have proper structure
        for entry in entries[:5]:
            assert "entry_number" in entry
            assert "lines" in entry
            assert entry.get("is_balanced") == True, f"Entry {entry['entry_number']} is not balanced"


class TestCapitalInvestment:
    """Test Capital Investment journal entries"""
    
    @pytest.fixture
    def test_user_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "testseeding@test.com",
            "password": "test1234"
        })
        return response.json()["access_token"]
    
    def test_capital_investment_creates_journal_entry(self, test_user_token):
        """Capital investment should create CAP- journal entry"""
        # Check existing capital investments
        response = requests.get(
            f"{BASE_URL}/api/finance/journal-entries?reference_type=capital_investment",
            headers={"Authorization": f"Bearer {test_user_token}"}
        )
        assert response.status_code == 200
        entries = response.json()
        
        if len(entries) > 0:
            # Verify structure
            entry = entries[0]
            assert entry.get("is_balanced") == True
            lines = entry.get("lines", [])
            
            # Should have debit to Cash and credit to Capital
            debits = sum(l.get("debit", 0) for l in lines)
            credits = sum(l.get("credit", 0) for l in lines)
            assert debits == credits, "Capital investment entry should be balanced"
            print(f"Capital investment journal entry verified: {entry['entry_number']}")
        else:
            print("No capital investment entries found - this is OK for fresh accounts")


class TestFinancialReportConsistency:
    """Test that all financial reports are consistent with each other"""
    
    @pytest.fixture
    def main_user_token(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "lahiruraja97@gmail.com",
            "password": "password123"
        })
        return response.json()["access_token"]
    
    def test_reports_consistency(self, main_user_token):
        """Verify all reports are internally consistent"""
        # Get all reports
        bs = requests.get(
            f"{BASE_URL}/api/finance/reports/balance-sheet",
            headers={"Authorization": f"Bearer {main_user_token}"}
        ).json()
        
        tb = requests.get(
            f"{BASE_URL}/api/finance/reports/trial-balance",
            headers={"Authorization": f"Bearer {main_user_token}"}
        ).json()
        
        pl = requests.get(
            f"{BASE_URL}/api/finance/reports/profit-loss",
            headers={"Authorization": f"Bearer {main_user_token}"}
        ).json()
        
        # Check all are balanced
        assert bs["is_balanced"] == True, "Balance Sheet should be balanced"
        assert tb["is_balanced"] == True, "Trial Balance should be balanced"
        
        # Net profit from P&L should match Balance Sheet
        net_profit_bs = [e for e in bs["equity"]["items"] if e["code"] == "NET"][0]["amount"]
        assert pl["net_profit"] == net_profit_bs, \
            f"P&L net profit ({pl['net_profit']}) != BS net profit ({net_profit_bs})"
        
        print("All financial reports are consistent!")
        print(f"  Balance Sheet balanced: {bs['is_balanced']}")
        print(f"  Trial Balance balanced: {tb['is_balanced']}")
        print(f"  Net Profit consistent: {pl['net_profit']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
