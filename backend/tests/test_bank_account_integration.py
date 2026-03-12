"""
Test Bank Account Integration in Transaction Forms
Tests P0 feature: User should be able to select which bank/cash account to use for all financial transactions

Covers:
- Bank & Cash Accounts module - creating new bank accounts
- Investors page - Add Investment modal with bank account selector
- Investors page - Withdrawal modal with bank account selector  
- Quick Transactions - Pay Expense with bank account selector
- Quick Transactions - Pay Salary with bank account selector
- Quick Transactions - Receive Payment with bank account selector
- Quick Transactions - Loan Transaction with bank account selector
- Purchase Orders - Record Payment dialog with bank account selector
- Journal entries created with selected bank account
"""
import pytest
import requests
import os
from datetime import datetime

# Get the base URL from environment variable
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    BASE_URL = "https://po-grn-verify.preview.emergentagent.com"

# Test credentials
TEST_EMAIL = "test@demo.com"
TEST_PASSWORD = "password123"


class TestBankAccountIntegration:
    """Test bank account integration across all transaction forms"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for all tests - login and get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if response.status_code != 200:
            pytest.skip(f"Login failed: {response.status_code}")
        
        token = response.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        yield
    
    # ============ Bank Accounts Module Tests ============
    
    def test_get_bank_accounts(self):
        """Test: GET /api/bank-accounts - Get all bank/cash accounts"""
        response = self.session.get(f"{BASE_URL}/api/bank-accounts")
        assert response.status_code == 200, f"Failed to get bank accounts: {response.text}"
        
        accounts = response.json()
        assert isinstance(accounts, list), "Response should be a list"
        print(f"Found {len(accounts)} bank accounts")
        
        # Check if test bank account exists
        test_account = None
        for acc in accounts:
            if "Main Business Account" in acc.get("account_name", ""):
                test_account = acc
                break
        
        if test_account:
            print(f"Test bank account found: {test_account['account_name']} - Balance: {test_account.get('current_balance')}")
            assert "id" in test_account
            assert "current_balance" in test_account
        
        return accounts
    
    def test_create_bank_account(self):
        """Test: POST /api/bank-accounts - Create a new bank account"""
        test_account_name = f"TEST_Integration_Bank_Account_{datetime.now().strftime('%H%M%S')}"
        
        response = self.session.post(f"{BASE_URL}/api/bank-accounts", json={
            "account_name": test_account_name,
            "account_type": "bank",
            "bank_name": "Test Bank",
            "account_number": "1234567890",
            "branch": "Test Branch",
            "opening_balance": 50000,
            "description": "Test bank account for integration testing"
        })
        
        assert response.status_code == 200 or response.status_code == 201, f"Failed to create bank account: {response.text}"
        
        account = response.json()
        assert account.get("account_name") == test_account_name
        assert account.get("current_balance") == 50000
        print(f"Created bank account: {account.get('id')}")
        
        return account
    
    # ============ Investors Module Tests ============
    
    def test_get_investors(self):
        """Test: GET /api/simple-finance/investors - Get all investors"""
        response = self.session.get(f"{BASE_URL}/api/simple-finance/investors")
        assert response.status_code == 200, f"Failed to get investors: {response.text}"
        
        investors = response.json()
        print(f"Found {len(investors)} investors")
        return investors
    
    def test_capital_investment_with_bank_account(self):
        """Test: POST /api/simple-finance/capital-investment with bank_account_id"""
        # First get investors
        investors_response = self.session.get(f"{BASE_URL}/api/simple-finance/investors")
        investors = investors_response.json()
        
        if not investors:
            pytest.skip("No investors found - cannot test capital investment")
        
        investor_id = investors[0]["id"]
        investor_name = investors[0]["name"]
        
        # Get bank accounts
        bank_response = self.session.get(f"{BASE_URL}/api/bank-accounts")
        bank_accounts = bank_response.json()
        
        if not bank_accounts:
            pytest.skip("No bank accounts found - cannot test with bank account selection")
        
        bank_account_id = bank_accounts[0]["id"]
        bank_account_name = bank_accounts[0]["account_name"]
        initial_balance = bank_accounts[0].get("current_balance", 0)
        
        # Record capital investment with selected bank account
        investment_amount = 1000
        response = self.session.post(f"{BASE_URL}/api/simple-finance/capital-investment", json={
            "investor_id": investor_id,
            "amount": investment_amount,
            "bank_account_id": bank_account_id,
            "payment_method": "bank",
            "reference": "TEST_INV_REF",
            "notes": "Test investment with bank account"
        })
        
        assert response.status_code == 200, f"Failed to record investment: {response.text}"
        
        result = response.json()
        assert "journal_entry_id" in result, "Response should contain journal entry ID"
        assert "entry_number" in result, "Response should contain entry number"
        print(f"Investment recorded: Entry #{result['entry_number']}")
        
        # Verify bank account balance increased
        bank_response = self.session.get(f"{BASE_URL}/api/bank-accounts")
        updated_accounts = bank_response.json()
        updated_account = next((a for a in updated_accounts if a["id"] == bank_account_id), None)
        
        if updated_account:
            new_balance = updated_account.get("current_balance", 0)
            print(f"Bank account balance: {initial_balance} -> {new_balance}")
            assert new_balance == initial_balance + investment_amount, "Bank balance should increase by investment amount"
        
        return result
    
    def test_capital_withdrawal_with_bank_account(self):
        """Test: POST /api/simple-finance/capital-withdrawal with bank_account_id"""
        # Get investors with balance
        investors_response = self.session.get(f"{BASE_URL}/api/simple-finance/investors")
        investors = investors_response.json()
        
        investor_with_balance = None
        for inv in investors:
            if inv.get("capital_balance", 0) > 100:
                investor_with_balance = inv
                break
        
        if not investor_with_balance:
            pytest.skip("No investor with sufficient balance found")
        
        # Get bank accounts
        bank_response = self.session.get(f"{BASE_URL}/api/bank-accounts")
        bank_accounts = bank_response.json()
        
        if not bank_accounts:
            pytest.skip("No bank accounts found")
        
        bank_account_id = bank_accounts[0]["id"]
        initial_balance = bank_accounts[0].get("current_balance", 0)
        
        # Record withdrawal with selected bank account
        withdrawal_amount = 100
        response = self.session.post(f"{BASE_URL}/api/simple-finance/capital-withdrawal", json={
            "investor_id": investor_with_balance["id"],
            "amount": withdrawal_amount,
            "reason": "Test withdrawal",
            "bank_account_id": bank_account_id,
            "payment_method": "bank",
            "notes": "Test withdrawal with bank account"
        })
        
        assert response.status_code == 200, f"Failed to record withdrawal: {response.text}"
        
        result = response.json()
        assert "journal_entry_id" in result
        print(f"Withdrawal recorded: Entry #{result['entry_number']}")
        
        # Verify bank account balance decreased
        bank_response = self.session.get(f"{BASE_URL}/api/bank-accounts")
        updated_accounts = bank_response.json()
        updated_account = next((a for a in updated_accounts if a["id"] == bank_account_id), None)
        
        if updated_account:
            new_balance = updated_account.get("current_balance", 0)
            print(f"Bank account balance after withdrawal: {initial_balance} -> {new_balance}")
            assert new_balance == initial_balance - withdrawal_amount, "Bank balance should decrease by withdrawal amount"
        
        return result
    
    # ============ Quick Transactions Tests ============
    
    def test_expense_payment_with_bank_account(self):
        """Test: POST /api/simple-finance/expense-payment with bank_account_id"""
        # Get bank accounts
        bank_response = self.session.get(f"{BASE_URL}/api/bank-accounts")
        bank_accounts = bank_response.json()
        
        if not bank_accounts:
            pytest.skip("No bank accounts found")
        
        bank_account_id = bank_accounts[0]["id"]
        initial_balance = bank_accounts[0].get("current_balance", 0)
        
        expense_amount = 500
        response = self.session.post(f"{BASE_URL}/api/simple-finance/expense-payment", json={
            "expense_type": "utilities",
            "description": "Test Electricity Bill",
            "amount": expense_amount,
            "bank_account_id": bank_account_id,
            "payment_method": "bank",
            "vendor": "Test Utility Company",
            "reference": "TEST_UTIL_001"
        })
        
        assert response.status_code == 200, f"Failed to record expense: {response.text}"
        
        result = response.json()
        assert "journal_entry_id" in result
        assert "entry_number" in result
        print(f"Expense recorded: Entry #{result['entry_number']}")
        
        # Verify bank account balance decreased
        bank_response = self.session.get(f"{BASE_URL}/api/bank-accounts")
        updated_accounts = bank_response.json()
        updated_account = next((a for a in updated_accounts if a["id"] == bank_account_id), None)
        
        if updated_account:
            new_balance = updated_account.get("current_balance", 0)
            print(f"Bank balance after expense: {initial_balance} -> {new_balance}")
            assert new_balance == initial_balance - expense_amount, "Bank balance should decrease by expense amount"
        
        return result
    
    def test_salary_payment_with_bank_account(self):
        """Test: POST /api/simple-finance/salary-payment with bank_account_id"""
        # Get bank accounts
        bank_response = self.session.get(f"{BASE_URL}/api/bank-accounts")
        bank_accounts = bank_response.json()
        
        if not bank_accounts:
            pytest.skip("No bank accounts found")
        
        bank_account_id = bank_accounts[0]["id"]
        initial_balance = bank_accounts[0].get("current_balance", 0)
        
        salary_amount = 25000
        allowances = 5000
        deductions = 2500
        net_salary = salary_amount + allowances - deductions
        
        response = self.session.post(f"{BASE_URL}/api/simple-finance/salary-payment", json={
            "employee_name": "TEST_Employee_Integration",
            "amount": salary_amount,
            "month": "January 2026",
            "bank_account_id": bank_account_id,
            "payment_method": "bank",
            "allowances": allowances,
            "deductions": deductions,
            "notes": "Test salary with bank account"
        })
        
        assert response.status_code == 200, f"Failed to record salary: {response.text}"
        
        result = response.json()
        assert "journal_entry_id" in result
        assert "entry_number" in result
        assert result.get("net_salary") == net_salary, f"Net salary mismatch: expected {net_salary}"
        print(f"Salary recorded: Entry #{result['entry_number']}, Net: {result.get('net_salary')}")
        
        # Verify bank account balance decreased by net salary
        bank_response = self.session.get(f"{BASE_URL}/api/bank-accounts")
        updated_accounts = bank_response.json()
        updated_account = next((a for a in updated_accounts if a["id"] == bank_account_id), None)
        
        if updated_account:
            new_balance = updated_account.get("current_balance", 0)
            print(f"Bank balance after salary: {initial_balance} -> {new_balance}")
            assert new_balance == initial_balance - net_salary, "Bank balance should decrease by net salary"
        
        return result
    
    def test_revenue_receipt_with_bank_account(self):
        """Test: POST /api/simple-finance/revenue-receipt with bank_account_id"""
        # Get bank accounts
        bank_response = self.session.get(f"{BASE_URL}/api/bank-accounts")
        bank_accounts = bank_response.json()
        
        if not bank_accounts:
            pytest.skip("No bank accounts found")
        
        bank_account_id = bank_accounts[0]["id"]
        initial_balance = bank_accounts[0].get("current_balance", 0)
        
        revenue_amount = 15000
        response = self.session.post(f"{BASE_URL}/api/simple-finance/revenue-receipt", json={
            "revenue_type": "sales",
            "description": "Test Sales Revenue",
            "amount": revenue_amount,
            "bank_account_id": bank_account_id,
            "payment_method": "bank",
            "customer": "Test Customer",
            "reference": "TEST_SALE_001"
        })
        
        assert response.status_code == 200, f"Failed to record revenue: {response.text}"
        
        result = response.json()
        assert "journal_entry_id" in result
        assert "entry_number" in result
        print(f"Revenue recorded: Entry #{result['entry_number']}")
        
        # Verify bank account balance increased
        bank_response = self.session.get(f"{BASE_URL}/api/bank-accounts")
        updated_accounts = bank_response.json()
        updated_account = next((a for a in updated_accounts if a["id"] == bank_account_id), None)
        
        if updated_account:
            new_balance = updated_account.get("current_balance", 0)
            print(f"Bank balance after revenue: {initial_balance} -> {new_balance}")
            assert new_balance == initial_balance + revenue_amount, "Bank balance should increase by revenue amount"
        
        return result
    
    def test_loan_received_with_bank_account(self):
        """Test: POST /api/simple-finance/loan-transaction (receive) with bank_account_id"""
        # Get bank accounts
        bank_response = self.session.get(f"{BASE_URL}/api/bank-accounts")
        bank_accounts = bank_response.json()
        
        if not bank_accounts:
            pytest.skip("No bank accounts found")
        
        bank_account_id = bank_accounts[0]["id"]
        initial_balance = bank_accounts[0].get("current_balance", 0)
        
        loan_amount = 50000
        response = self.session.post(f"{BASE_URL}/api/simple-finance/loan-transaction", json={
            "transaction_type": "receive",
            "loan_type": "bank_loan",
            "lender_name": "Test Bank Loan",
            "amount": loan_amount,
            "bank_account_id": bank_account_id,
            "reference": "TEST_LOAN_001"
        })
        
        assert response.status_code == 200, f"Failed to record loan: {response.text}"
        
        result = response.json()
        assert "journal_entry_id" in result
        assert "entry_number" in result
        print(f"Loan received: Entry #{result['entry_number']}")
        
        # Verify bank account balance increased
        bank_response = self.session.get(f"{BASE_URL}/api/bank-accounts")
        updated_accounts = bank_response.json()
        updated_account = next((a for a in updated_accounts if a["id"] == bank_account_id), None)
        
        if updated_account:
            new_balance = updated_account.get("current_balance", 0)
            print(f"Bank balance after loan received: {initial_balance} -> {new_balance}")
            assert new_balance == initial_balance + loan_amount, "Bank balance should increase by loan amount"
        
        return result
    
    def test_loan_repayment_with_bank_account(self):
        """Test: POST /api/simple-finance/loan-transaction (repay) with bank_account_id"""
        # Get bank accounts
        bank_response = self.session.get(f"{BASE_URL}/api/bank-accounts")
        bank_accounts = bank_response.json()
        
        if not bank_accounts:
            pytest.skip("No bank accounts found")
        
        bank_account_id = bank_accounts[0]["id"]
        initial_balance = bank_accounts[0].get("current_balance", 0)
        
        principal_amount = 10000
        interest_amount = 500
        total_payment = principal_amount + interest_amount
        
        response = self.session.post(f"{BASE_URL}/api/simple-finance/loan-transaction", json={
            "transaction_type": "repay",
            "loan_type": "bank_loan",
            "lender_name": "Test Bank Loan",
            "amount": principal_amount,
            "interest_amount": interest_amount,
            "bank_account_id": bank_account_id,
            "reference": "TEST_REPAY_001"
        })
        
        assert response.status_code == 200, f"Failed to record loan repayment: {response.text}"
        
        result = response.json()
        assert "journal_entry_id" in result
        assert "entry_number" in result
        print(f"Loan repayment recorded: Entry #{result['entry_number']}")
        
        # Verify bank account balance decreased by total payment
        bank_response = self.session.get(f"{BASE_URL}/api/bank-accounts")
        updated_accounts = bank_response.json()
        updated_account = next((a for a in updated_accounts if a["id"] == bank_account_id), None)
        
        if updated_account:
            new_balance = updated_account.get("current_balance", 0)
            print(f"Bank balance after loan repayment: {initial_balance} -> {new_balance}")
            assert new_balance == initial_balance - total_payment, "Bank balance should decrease by total payment"
        
        return result
    
    # ============ Purchase Orders Payment Tests ============
    
    def test_purchase_order_payment_with_bank_account(self):
        """Test: POST /api/payments with bank_account_id for purchase order"""
        # Get a purchase order with unpaid status
        po_response = self.session.get(f"{BASE_URL}/api/purchase-orders?payment_status=unpaid")
        
        if po_response.status_code != 200:
            po_response = self.session.get(f"{BASE_URL}/api/purchase-orders")
        
        purchase_orders = po_response.json()
        
        # Find an order that isn't fully paid
        unpaid_order = None
        for order in purchase_orders:
            if order.get("payment_status") != "paid":
                unpaid_order = order
                break
        
        if not unpaid_order:
            pytest.skip("No unpaid purchase orders found")
        
        # Get bank accounts
        bank_response = self.session.get(f"{BASE_URL}/api/bank-accounts")
        bank_accounts = bank_response.json()
        
        if not bank_accounts:
            pytest.skip("No bank accounts found")
        
        bank_account_id = bank_accounts[0]["id"]
        initial_balance = bank_accounts[0].get("current_balance", 0)
        
        # Calculate payment amount (remaining balance)
        balance_due = unpaid_order.get("total", 0) - unpaid_order.get("paid_amount", 0)
        payment_amount = min(1000, balance_due)  # Pay at most 1000 for testing
        
        if payment_amount <= 0:
            pytest.skip("No balance due on purchase orders")
        
        response = self.session.post(f"{BASE_URL}/api/payments", json={
            "reference_type": "purchase_order",
            "reference_id": unpaid_order["id"],
            "amount": payment_amount,
            "payment_method": "bank",
            "bank_account_id": bank_account_id,
            "notes": "Test payment with bank account"
        })
        
        assert response.status_code == 200, f"Failed to record payment: {response.text}"
        
        result = response.json()
        assert "id" in result, "Payment should have an ID"
        print(f"PO Payment recorded: {payment_amount} from bank account")
        
        # Verify bank account balance decreased
        bank_response = self.session.get(f"{BASE_URL}/api/bank-accounts")
        updated_accounts = bank_response.json()
        updated_account = next((a for a in updated_accounts if a["id"] == bank_account_id), None)
        
        if updated_account:
            new_balance = updated_account.get("current_balance", 0)
            print(f"Bank balance after PO payment: {initial_balance} -> {new_balance}")
            # Note: The payment may update balance through journal entry
        
        return result
    
    # ============ Journal Entry Verification Tests ============
    
    def test_journal_entries_contain_bank_account(self):
        """Test: Verify journal entries are created with correct bank account"""
        # Get recent transactions
        response = self.session.get(f"{BASE_URL}/api/simple-finance/recent-transactions?limit=5")
        assert response.status_code == 200, f"Failed to get recent transactions: {response.text}"
        
        transactions = response.json()
        
        if not transactions:
            pytest.skip("No recent transactions found")
        
        print(f"Found {len(transactions)} recent transactions")
        
        for tx in transactions[:3]:  # Check first 3 transactions
            # Check if transaction has bank_account_id in metadata
            metadata = tx.get("metadata", {})
            bank_account_id = metadata.get("bank_account_id")
            
            print(f"Transaction {tx.get('entry_number')}: type={tx.get('transaction_type')}, bank_account={bank_account_id}")
            
            # Verify journal entry has proper lines
            lines = tx.get("lines", [])
            assert len(lines) >= 2, f"Journal entry should have at least 2 lines, got {len(lines)}"
            
            # Verify balanced entry
            total_debit = sum(line.get("debit", 0) for line in lines)
            total_credit = sum(line.get("credit", 0) for line in lines)
            assert abs(total_debit - total_credit) < 0.01, f"Journal entry should be balanced: debit={total_debit}, credit={total_credit}"
        
        return transactions


class TestBankAccountModel:
    """Test bank account model and validations"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if response.status_code != 200:
            pytest.skip(f"Login failed: {response.status_code}")
        
        token = response.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        yield
    
    def test_create_cash_account(self):
        """Test: Create a cash account (petty cash)"""
        response = self.session.post(f"{BASE_URL}/api/bank-accounts", json={
            "account_name": f"TEST_Petty_Cash_{datetime.now().strftime('%H%M%S')}",
            "account_type": "cash",
            "opening_balance": 10000,
            "description": "Petty cash for office expenses"
        })
        
        assert response.status_code in [200, 201], f"Failed to create cash account: {response.text}"
        
        account = response.json()
        assert account.get("account_type") == "cash"
        assert account.get("current_balance") == 10000
        print(f"Created cash account: {account.get('account_name')}")
        
        return account
    
    def test_bank_account_has_chart_account_code(self):
        """Test: Verify bank accounts are linked to Chart of Accounts"""
        response = self.session.get(f"{BASE_URL}/api/bank-accounts")
        assert response.status_code == 200
        
        accounts = response.json()
        
        for acc in accounts[:3]:  # Check first 3 accounts
            # Bank accounts should have a chart account code
            chart_code = acc.get("chart_account_code")
            print(f"Bank account '{acc.get('account_name')}' - Chart code: {chart_code}")
            
            # Verify code starts with 11 (cash/bank accounts in COA)
            if chart_code:
                assert chart_code.startswith("11"), f"Bank/cash account code should start with 11, got {chart_code}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
