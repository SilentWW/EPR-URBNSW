"""
Backend Tests for Simple Finance Module (Phase 2)
Tests: Investor Management, Capital Investment, Quick Transactions, Financial Reports
"""
import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "admin@example.com"
TEST_PASSWORD = "admin123"


class TestInvestorManagement:
    """Investor CRUD and capital account tests"""
    
    def test_get_investors(self, auth_token):
        """Test getting investors list"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{BASE_URL}/api/simple-finance/investors", headers=headers)
        assert response.status_code == 200, f"Get investors failed: {response.text}"
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Retrieved {len(data)} investors")
        return data
    
    def test_create_investor_with_capital_account(self, auth_token):
        """Test creating investor - should auto-create capital account under Equity (31xx series)"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        investor_data = {
            "name": f"TEST Shareholder {datetime.now().strftime('%H%M%S')}",
            "investor_type": "shareholder",
            "email": f"test{datetime.now().strftime('%H%M%S')}@investor.com",
            "phone": "0771234567",
            "share_percentage": 25.5
        }
        
        response = requests.post(f"{BASE_URL}/api/simple-finance/investors", headers=headers, json=investor_data)
        assert response.status_code == 200, f"Create investor failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "investor" in data
        assert "account_code" in data
        
        # Verify account code is in 31xx series
        account_code = data["account_code"]
        assert account_code.startswith("31"), f"Account code should be in 31xx series, got {account_code}"
        
        print(f"✓ Created investor: {data['investor']['name']} with capital account {account_code}")
        return data["investor"]["id"]
    
    def test_investor_capital_account_in_chart_of_accounts(self, auth_token):
        """Test that investor capital accounts appear under Equity in COA"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Get equity accounts
        response = requests.get(f"{BASE_URL}/api/finance/chart-of-accounts?account_type=equity", headers=headers)
        assert response.status_code == 200
        accounts = response.json()
        
        # Check for investor capital accounts (31xx series, excluding 3100 and 3200)
        capital_accounts = [a for a in accounts if a["code"].startswith("31") and a["code"] not in ["3100"]]
        
        print(f"✓ Found {len(capital_accounts)} investor capital accounts in Equity section")
        for acc in capital_accounts:
            print(f"  - {acc['code']}: {acc['name']} (Balance: {acc.get('current_balance', 0)})")
        
        return len(capital_accounts) > 0


class TestCapitalInvestment:
    """Capital Investment recording tests"""
    
    def test_record_capital_investment(self, auth_token):
        """Test recording capital investment - should debit Cash (1100), credit Capital Account"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Get existing investor
        investors_response = requests.get(f"{BASE_URL}/api/simple-finance/investors", headers=headers)
        investors = investors_response.json()
        
        if not investors:
            pytest.skip("No investors available for investment test")
        
        investor = investors[0]
        
        investment_data = {
            "investor_id": investor["id"],
            "amount": 50000,
            "payment_method": "bank",
            "reference": f"INV-{datetime.now().strftime('%H%M%S')}",
            "notes": "Test capital investment"
        }
        
        response = requests.post(f"{BASE_URL}/api/simple-finance/capital-investment", headers=headers, json=investment_data)
        assert response.status_code == 200, f"Capital investment failed: {response.text}"
        data = response.json()
        
        assert "journal_entry_id" in data
        assert "entry_number" in data
        assert data["investor"] == investor["name"]
        
        print(f"✓ Recorded capital investment: {data['message']}")
        return data["journal_entry_id"]
    
    def test_capital_investment_journal_entry_structure(self, auth_token):
        """Verify capital investment creates proper double-entry"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Get recent journal entries for capital investment
        response = requests.get(f"{BASE_URL}/api/finance/journal-entries?reference_type=capital_investment", headers=headers)
        assert response.status_code == 200
        entries = response.json()
        
        if not entries:
            pytest.skip("No capital investment entries found")
        
        entry = entries[0]
        assert entry["is_balanced"] == True
        
        # Verify journal entry lines
        lines = entry["lines"]
        debit_line = next((l for l in lines if l["debit"] > 0), None)
        credit_line = next((l for l in lines if l["credit"] > 0), None)
        
        assert debit_line is not None, "Should have a debit line"
        assert credit_line is not None, "Should have a credit line"
        
        # Debit should be Cash (1100)
        assert debit_line["account_code"] == "1100", f"Debit should be Cash (1100), got {debit_line['account_code']}"
        
        # Credit should be capital account (31xx)
        assert credit_line["account_code"].startswith("31"), f"Credit should be capital account (31xx), got {credit_line['account_code']}"
        
        print(f"✓ Capital investment journal entry verified:")
        print(f"  - Debit: {debit_line['account_name']} ({debit_line['account_code']}) - {debit_line['debit']}")
        print(f"  - Credit: {credit_line['account_name']} ({credit_line['account_code']}) - {credit_line['credit']}")


class TestQuickTransactions:
    """Quick transaction tests - salary, expense, revenue, loan"""
    
    def test_pay_salary(self, auth_token):
        """Test salary payment - should debit Salaries & Wages (6100), credit Cash"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        salary_data = {
            "employee_name": f"TEST Employee {datetime.now().strftime('%H%M%S')}",
            "amount": 45000,
            "month": "January 2026",
            "payment_method": "bank",
            "allowances": 3000,
            "deductions": 1500
        }
        
        response = requests.post(f"{BASE_URL}/api/simple-finance/salary-payment", headers=headers, json=salary_data)
        assert response.status_code == 200, f"Salary payment failed: {response.text}"
        data = response.json()
        
        assert "journal_entry_id" in data
        assert data["gross_salary"] == 48000  # 45000 + 3000 allowances
        assert data["net_salary"] == 46500    # 48000 - 1500 deductions
        
        print(f"✓ Salary payment recorded: {data['message']}")
        return data["journal_entry_id"]
    
    def test_salary_journal_entry_structure(self, auth_token):
        """Verify salary payment creates proper double-entry"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.get(f"{BASE_URL}/api/finance/journal-entries?reference_type=salary_payment", headers=headers)
        assert response.status_code == 200
        entries = response.json()
        
        if not entries:
            pytest.skip("No salary payment entries found")
        
        entry = entries[0]
        assert entry["is_balanced"] == True
        
        lines = entry["lines"]
        expense_line = next((l for l in lines if l.get("account_code") == "6100"), None)
        
        assert expense_line is not None, "Should have Salaries & Wages expense line"
        assert expense_line["debit"] > 0, "Salary expense should be debited"
        
        print(f"✓ Salary journal entry verified - Expense: {expense_line['debit']}")
    
    def test_pay_expense(self, auth_token):
        """Test expense payment - should debit Expense account, credit Cash"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        expense_data = {
            "expense_type": "utilities",
            "description": f"Electricity Bill {datetime.now().strftime('%H%M%S')}",
            "amount": 15000,
            "payment_method": "bank",
            "vendor": "CEB"
        }
        
        response = requests.post(f"{BASE_URL}/api/simple-finance/expense-payment", headers=headers, json=expense_data)
        assert response.status_code == 200, f"Expense payment failed: {response.text}"
        data = response.json()
        
        assert "journal_entry_id" in data
        assert data["expense_type"] == "utilities"
        
        print(f"✓ Expense payment recorded: {data['message']}")
        return data["journal_entry_id"]
    
    def test_expense_journal_entry_structure(self, auth_token):
        """Verify expense payment creates proper double-entry"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.get(f"{BASE_URL}/api/finance/journal-entries?reference_type=expense_payment", headers=headers)
        assert response.status_code == 200
        entries = response.json()
        
        if not entries:
            pytest.skip("No expense payment entries found")
        
        entry = entries[0]
        assert entry["is_balanced"] == True
        
        lines = entry["lines"]
        debit_line = next((l for l in lines if l["debit"] > 0), None)
        credit_line = next((l for l in lines if l["credit"] > 0), None)
        
        # Credit should be Cash (1100)
        assert credit_line["account_code"] == "1100", f"Credit should be Cash, got {credit_line['account_code']}"
        
        # Debit should be an expense account (6xxx)
        assert debit_line["account_code"].startswith("6"), f"Debit should be expense (6xxx), got {debit_line['account_code']}"
        
        print(f"✓ Expense journal entry verified:")
        print(f"  - Debit: {debit_line['account_name']} - {debit_line['debit']}")
        print(f"  - Credit: {credit_line['account_name']} - {credit_line['credit']}")
    
    def test_receive_revenue(self, auth_token):
        """Test revenue receipt - should debit Cash, credit Revenue account"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        revenue_data = {
            "revenue_type": "sales",
            "description": f"Product Sales {datetime.now().strftime('%H%M%S')}",
            "amount": 75000,
            "payment_method": "bank",
            "customer": "Test Customer"
        }
        
        response = requests.post(f"{BASE_URL}/api/simple-finance/revenue-receipt", headers=headers, json=revenue_data)
        assert response.status_code == 200, f"Revenue receipt failed: {response.text}"
        data = response.json()
        
        assert "journal_entry_id" in data
        
        print(f"✓ Revenue receipt recorded: {data['message']}")
        return data["journal_entry_id"]
    
    def test_revenue_journal_entry_structure(self, auth_token):
        """Verify revenue receipt creates proper double-entry"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.get(f"{BASE_URL}/api/finance/journal-entries?reference_type=revenue_receipt", headers=headers)
        assert response.status_code == 200
        entries = response.json()
        
        if not entries:
            pytest.skip("No revenue receipt entries found")
        
        entry = entries[0]
        assert entry["is_balanced"] == True
        
        lines = entry["lines"]
        debit_line = next((l for l in lines if l["debit"] > 0), None)
        credit_line = next((l for l in lines if l["credit"] > 0), None)
        
        # Debit should be Cash (1100)
        assert debit_line["account_code"] == "1100", f"Debit should be Cash, got {debit_line['account_code']}"
        
        # Credit should be a revenue account (4xxx)
        assert credit_line["account_code"].startswith("4"), f"Credit should be revenue (4xxx), got {credit_line['account_code']}"
        
        print(f"✓ Revenue journal entry verified:")
        print(f"  - Debit: {debit_line['account_name']} - {debit_line['debit']}")
        print(f"  - Credit: {credit_line['account_name']} - {credit_line['credit']}")
    
    def test_loan_receive(self, auth_token):
        """Test loan receive - should debit Cash, credit Loans Payable"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        loan_data = {
            "transaction_type": "receive",
            "loan_type": "bank_loan",
            "lender_name": f"Test Bank {datetime.now().strftime('%H%M%S')}",
            "amount": 200000,
            "reference": f"LOAN-{datetime.now().strftime('%H%M%S')}"
        }
        
        response = requests.post(f"{BASE_URL}/api/simple-finance/loan-transaction", headers=headers, json=loan_data)
        assert response.status_code == 200, f"Loan receive failed: {response.text}"
        data = response.json()
        
        assert "journal_entry_id" in data
        
        print(f"✓ Loan received: {data['message']}")
        return data["journal_entry_id"]
    
    def test_loan_journal_entry_structure(self, auth_token):
        """Verify loan receive creates proper double-entry"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.get(f"{BASE_URL}/api/finance/journal-entries?reference_type=loan_received", headers=headers)
        assert response.status_code == 200
        entries = response.json()
        
        if not entries:
            pytest.skip("No loan received entries found")
        
        entry = entries[0]
        assert entry["is_balanced"] == True
        
        lines = entry["lines"]
        debit_line = next((l for l in lines if l["debit"] > 0), None)
        credit_line = next((l for l in lines if l["credit"] > 0), None)
        
        # Debit should be Cash (1100)
        assert debit_line["account_code"] == "1100", f"Debit should be Cash, got {debit_line['account_code']}"
        
        # Credit should be Loans Payable (23xx)
        assert credit_line["account_code"].startswith("23"), f"Credit should be Loans Payable (23xx), got {credit_line['account_code']}"
        
        print(f"✓ Loan journal entry verified:")
        print(f"  - Debit: {debit_line['account_name']} - {debit_line['debit']}")
        print(f"  - Credit: {credit_line['account_name']} - {credit_line['credit']}")


class TestFinancialReports:
    """Financial reports accuracy tests"""
    
    def test_trial_balance_is_balanced(self, auth_token):
        """Test Trial Balance - should be balanced (total debit = total credit)"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.get(f"{BASE_URL}/api/finance/reports/trial-balance", headers=headers)
        assert response.status_code == 200, f"Trial balance failed: {response.text}"
        data = response.json()
        
        assert "is_balanced" in data
        assert "total_debit" in data
        assert "total_credit" in data
        
        # Trial balance should be balanced
        assert data["is_balanced"] == True, f"Trial balance not balanced! Debit: {data['total_debit']}, Credit: {data['total_credit']}"
        
        print(f"✓ Trial Balance is balanced:")
        print(f"  - Total Debit: {data['total_debit']}")
        print(f"  - Total Credit: {data['total_credit']}")
    
    def test_profit_loss_report(self, auth_token):
        """Test P&L - should show Income and Expenses correctly"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.get(f"{BASE_URL}/api/finance/reports/profit-loss", headers=headers)
        assert response.status_code == 200, f"P&L report failed: {response.text}"
        data = response.json()
        
        assert "income" in data
        assert "expenses" in data
        assert "net_profit" in data
        
        # Verify calculation
        calculated_profit = data["income"]["total"] - data["expenses"]["total"]
        assert abs(calculated_profit - data["net_profit"]) < 0.01, "Net profit calculation mismatch"
        
        print(f"✓ P&L Report:")
        print(f"  - Income: {data['income']['total']}")
        print(f"  - Expenses: {data['expenses']['total']}")
        print(f"  - Net Profit: {data['net_profit']}")
    
    def test_balance_sheet_equation(self, auth_token):
        """Test Balance Sheet - Assets = Liabilities + Equity"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.get(f"{BASE_URL}/api/finance/reports/balance-sheet", headers=headers)
        assert response.status_code == 200, f"Balance sheet failed: {response.text}"
        data = response.json()
        
        assert "total_assets" in data
        assert "total_liabilities_equity" in data
        assert "is_balanced" in data
        
        # Balance sheet should balance
        assert data["is_balanced"] == True, f"Balance sheet not balanced! Assets: {data['total_assets']}, Liabilities+Equity: {data['total_liabilities_equity']}"
        
        print(f"✓ Balance Sheet is balanced:")
        print(f"  - Total Assets: {data['total_assets']}")
        print(f"  - Total Liabilities + Equity: {data['total_liabilities_equity']}")
    
    def test_recent_transactions(self, auth_token):
        """Test recent quick transactions endpoint"""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        response = requests.get(f"{BASE_URL}/api/simple-finance/recent-transactions", headers=headers)
        assert response.status_code == 200, f"Recent transactions failed: {response.text}"
        data = response.json()
        
        assert isinstance(data, list)
        
        if data:
            # Verify transaction structure
            tx = data[0]
            assert "transaction_type" in tx
            assert "is_balanced" in tx
            assert tx["is_balanced"] == True, "Transaction should be balanced"
        
        print(f"✓ Retrieved {len(data)} recent quick transactions")


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
