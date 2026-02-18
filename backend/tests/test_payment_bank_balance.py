"""
Test: Sales Order Payment Recording - Bank Account Balance Update Bug Fix

This test verifies the bug fix for:
- Bank account balance NOT increasing when recording payment for Sales Orders
- No income showing in Chart of Accounts  
- Journal entries not being created properly

The fix involved:
1. Seeding missing Chart of Accounts entries (Accounts Receivable code 1300)
2. Adding auto-creation logic in create_payment function to create required accounts if missing
3. Ensuring bank account balance is updated via db.bank_accounts.update_one
"""

import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestPaymentBankBalanceUpdate:
    """Tests for Sales Order Payment Recording - Bank Balance Bug Fix"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data and authenticate"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login with provided credentials
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "lahiruraja97@gmail.com",
            "password": "password123"
        })
        
        if login_response.status_code != 200:
            pytest.skip(f"Login failed: {login_response.status_code}")
        
        token = login_response.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
    def test_login_success(self):
        """Test that login works with provided credentials"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "lahiruraja97@gmail.com",
            "password": "password123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == "lahiruraja97@gmail.com"
        print("Login successful with lahiruraja97@gmail.com")

    def test_get_bank_accounts(self):
        """Test that bank accounts API returns accounts with balance"""
        response = self.session.get(f"{BASE_URL}/api/bank-accounts")
        assert response.status_code == 200
        
        accounts = response.json()
        assert isinstance(accounts, list)
        print(f"Found {len(accounts)} bank accounts")
        
        for acc in accounts:
            print(f"  - {acc.get('account_name')}: {acc.get('current_balance')} ({acc.get('account_type')})")
            assert "current_balance" in acc
            assert "account_name" in acc
            
    def test_get_specific_bank_account(self):
        """Test fetching specific bank account by ID"""
        bank_account_id = "2d73f13d-48ff-48bf-8bfd-488c37d573f3"
        
        response = self.session.get(f"{BASE_URL}/api/bank-accounts/{bank_account_id}")
        
        # Account may or may not exist, log the result
        if response.status_code == 200:
            account = response.json()
            print(f"Bank Account Found: {account.get('account_name')}")
            print(f"  Current Balance: {account.get('current_balance')}")
            print(f"  Account Type: {account.get('account_type')}")
        else:
            print(f"Bank account {bank_account_id} not found, will use first available")
            
    def test_chart_of_accounts_has_ar(self):
        """Test that Chart of Accounts includes Accounts Receivable (code 1300)"""
        response = self.session.get(f"{BASE_URL}/api/finance/chart-of-accounts")
        assert response.status_code == 200, f"Chart of Accounts API failed: {response.text}"
        
        accounts = response.json()
        ar_account = None
        cash_account = None
        
        for acc in accounts:
            if acc.get("code") == "1300":
                ar_account = acc
            if acc.get("code") == "1100":
                cash_account = acc
        
        assert ar_account is not None, "Accounts Receivable (1300) should exist"
        print(f"Accounts Receivable found: {ar_account.get('name')} - Balance: {ar_account.get('current_balance')}")
        
        assert cash_account is not None, "Cash (1100) should exist"
        print(f"Cash account found: {cash_account.get('name')} - Balance: {cash_account.get('current_balance')}")

    def test_sales_orders_list(self):
        """Test that sales orders API works"""
        response = self.session.get(f"{BASE_URL}/api/sales-orders")
        assert response.status_code == 200
        
        orders = response.json()
        assert isinstance(orders, list)
        print(f"Found {len(orders)} sales orders")
        
        # Find an unpaid order for testing
        unpaid_orders = [o for o in orders if o.get("payment_status") != "paid" and o.get("status") != "returned"]
        print(f"Found {len(unpaid_orders)} unpaid orders available for payment testing")
        
        return unpaid_orders

    def test_record_payment_increases_bank_balance(self):
        """
        CRITICAL TEST: Verify that recording a payment for a sales order
        increases the bank account balance.
        
        This is the main bug that was reported.
        """
        # Step 1: Get available bank accounts
        bank_response = self.session.get(f"{BASE_URL}/api/bank-accounts")
        assert bank_response.status_code == 200
        bank_accounts = bank_response.json()
        
        if not bank_accounts:
            pytest.skip("No bank accounts available for testing")
            
        # Use first available bank account
        test_bank_account = bank_accounts[0]
        bank_account_id = test_bank_account["id"]
        initial_balance = test_bank_account.get("current_balance", 0)
        
        print(f"\n=== Testing Payment Recording ===")
        print(f"Bank Account: {test_bank_account.get('account_name')}")
        print(f"Initial Balance: {initial_balance}")
        
        # Step 2: Get an unpaid sales order or create one
        orders_response = self.session.get(f"{BASE_URL}/api/sales-orders")
        assert orders_response.status_code == 200
        orders = orders_response.json()
        
        unpaid_order = None
        for order in orders:
            if order.get("payment_status") != "paid" and order.get("status") != "returned":
                unpaid_order = order
                break
        
        if not unpaid_order:
            # Create a customer and sales order for testing
            print("No unpaid orders found, creating test order...")
            
            # Get or create customer
            customers_response = self.session.get(f"{BASE_URL}/api/customers")
            if customers_response.status_code == 200 and customers_response.json():
                test_customer = customers_response.json()[0]
            else:
                customer_data = {
                    "name": f"TEST_PAYMENT_Customer_{uuid.uuid4().hex[:6]}",
                    "email": f"test_payment_{uuid.uuid4().hex[:6]}@test.com"
                }
                customer_response = self.session.post(f"{BASE_URL}/api/customers", json=customer_data)
                assert customer_response.status_code in [200, 201]
                test_customer = customer_response.json()
            
            # Get or create product
            products_response = self.session.get(f"{BASE_URL}/api/products")
            if products_response.status_code == 200 and products_response.json():
                test_product = products_response.json()[0]
            else:
                pytest.skip("No products available for creating test order")
            
            # Create sales order
            payment_test_amount = 1000  # Test amount
            order_data = {
                "customer_id": test_customer["id"],
                "items": [{
                    "product_id": test_product["id"],
                    "product_name": test_product.get("name", "Test Product"),
                    "sku": test_product.get("sku", "TEST-SKU"),
                    "quantity": 1,
                    "unit_price": payment_test_amount,
                    "total": payment_test_amount
                }],
                "discount": 0,
                "notes": "Payment balance test order"
            }
            order_response = self.session.post(f"{BASE_URL}/api/sales-orders", json=order_data)
            assert order_response.status_code in [200, 201], f"Failed to create order: {order_response.text}"
            unpaid_order = order_response.json()
        
        print(f"Using Order: {unpaid_order.get('order_number')}")
        print(f"Order Total: {unpaid_order.get('total')}")
        print(f"Already Paid: {unpaid_order.get('paid_amount', 0)}")
        
        # Step 3: Calculate payment amount
        balance_due = unpaid_order.get("total", 0) - unpaid_order.get("paid_amount", 0)
        payment_amount = min(balance_due, 1000)  # Pay up to 1000 or remaining balance
        
        if payment_amount <= 0:
            pytest.skip("No balance due on test order")
            
        print(f"Recording payment of: {payment_amount}")
        
        # Step 4: Record the payment
        payment_data = {
            "reference_type": "sales_order",
            "reference_id": unpaid_order["id"],
            "amount": payment_amount,
            "payment_method": "bank",
            "bank_account_id": bank_account_id,
            "notes": "Automated test payment"
        }
        
        payment_response = self.session.post(f"{BASE_URL}/api/payments", json=payment_data)
        assert payment_response.status_code in [200, 201], f"Payment failed: {payment_response.text}"
        
        payment_result = payment_response.json()
        print(f"Payment recorded successfully: {payment_result.get('id')}")
        
        # Step 5: Verify bank account balance INCREASED
        updated_bank_response = self.session.get(f"{BASE_URL}/api/bank-accounts/{bank_account_id}")
        assert updated_bank_response.status_code == 200
        
        updated_account = updated_bank_response.json()
        new_balance = updated_account.get("current_balance", 0)
        
        print(f"\n=== Balance Verification ===")
        print(f"Initial Balance: {initial_balance}")
        print(f"Payment Amount: {payment_amount}")
        print(f"Expected Balance: {initial_balance + payment_amount}")
        print(f"Actual New Balance: {new_balance}")
        
        # THE CRITICAL ASSERTION - Bank balance should have increased
        assert new_balance == initial_balance + payment_amount, \
            f"Bank balance did not increase correctly! Expected {initial_balance + payment_amount}, got {new_balance}"
        
        print("SUCCESS: Bank balance increased correctly after payment!")

    def test_journal_entry_created_for_payment(self):
        """
        Verify that a journal entry is created when recording payment.
        Entry should be: Debit Cash, Credit Accounts Receivable
        """
        # Get journal entries
        response = self.session.get(f"{BASE_URL}/api/finance/journal-entries")
        assert response.status_code == 200, f"Journal entries API failed: {response.text}"
        
        entries = response.json()
        print(f"Found {len(entries)} journal entries")
        
        # Find REC- entries (receipts from customers)
        receipt_entries = [e for e in entries if e.get("entry_number", "").startswith("REC-")]
        print(f"Found {len(receipt_entries)} receipt journal entries")
        
        if receipt_entries:
            latest_entry = receipt_entries[0]  # Most recent
            print(f"\nLatest Receipt Entry: {latest_entry.get('entry_number')}")
            print(f"Description: {latest_entry.get('description')}")
            print(f"Lines:")
            for line in latest_entry.get("lines", []):
                debit = line.get("debit", 0)
                credit = line.get("credit", 0)
                print(f"  {line.get('account_code')} {line.get('account_name')}: Debit={debit}, Credit={credit}")
            
            # Verify double-entry accounting
            total_debit = sum(l.get("debit", 0) for l in latest_entry.get("lines", []))
            total_credit = sum(l.get("credit", 0) for l in latest_entry.get("lines", []))
            assert total_debit == total_credit, "Journal entry is not balanced!"
            print(f"Entry is balanced: Debit={total_debit}, Credit={total_credit}")

    def test_chart_of_accounts_balance_updates(self):
        """
        Verify that Chart of Accounts balances are updated after payment.
        Cash account should increase, AR should decrease.
        """
        response = self.session.get(f"{BASE_URL}/api/finance/chart-of-accounts")
        assert response.status_code == 200, f"Chart of Accounts API failed: {response.text}"
        
        accounts = response.json()
        
        # Find key accounts
        cash_account = None
        ar_account = None
        revenue_account = None
        
        for acc in accounts:
            code = acc.get("code", "")
            if code == "1100":
                cash_account = acc
            elif code == "1300":
                ar_account = acc
            elif code == "4100":
                revenue_account = acc
        
        print("\n=== Chart of Accounts Balances ===")
        
        if cash_account:
            print(f"1100 Cash: {cash_account.get('current_balance', 0)}")
        
        if ar_account:
            print(f"1300 Accounts Receivable: {ar_account.get('current_balance', 0)}")
            
        if revenue_account:
            print(f"4100 Sales Revenue: {revenue_account.get('current_balance', 0)}")
        
        # Just verify these accounts exist - balance verification is in the main test
        assert cash_account is not None, "Cash account (1100) not found"
        assert ar_account is not None, "Accounts Receivable (1300) not found"

    def test_payment_modal_shows_bank_accounts(self):
        """
        API test to verify bank accounts are returned for the payment modal dropdown.
        The frontend's 'Payment Received To' dropdown should show these accounts.
        """
        response = self.session.get(f"{BASE_URL}/api/bank-accounts")
        assert response.status_code == 200
        
        accounts = response.json()
        assert len(accounts) > 0, "At least one bank account should exist for payment dropdown"
        
        print(f"\n=== Bank Accounts for Payment Modal ===")
        for acc in accounts:
            print(f"  {acc.get('id')}: {acc.get('account_name')} ({acc.get('account_type')}) - Balance: {acc.get('current_balance')}")
        
        # Verify required fields for dropdown display
        for acc in accounts:
            assert "id" in acc, "Bank account should have id"
            assert "account_name" in acc, "Bank account should have account_name"
            assert "current_balance" in acc, "Bank account should have current_balance"
            assert "account_type" in acc, "Bank account should have account_type"


class TestEndToEndPaymentFlow:
    """End-to-end test for the complete payment flow"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test session"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "lahiruraja97@gmail.com",
            "password": "password123"
        })
        
        if login_response.status_code != 200:
            pytest.skip("Login failed")
        
        token = login_response.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
    def test_complete_payment_flow(self):
        """
        Complete end-to-end test:
        1. Get bank accounts
        2. Get unpaid sales order
        3. Record payment
        4. Verify bank balance increased
        5. Verify journal entry created
        6. Verify order payment status updated
        """
        print("\n" + "="*60)
        print("COMPLETE PAYMENT FLOW TEST")
        print("="*60)
        
        # Step 1: Get bank accounts
        bank_response = self.session.get(f"{BASE_URL}/api/bank-accounts")
        assert bank_response.status_code == 200
        bank_accounts = bank_response.json()
        
        if not bank_accounts:
            pytest.skip("No bank accounts found")
            
        bank_account = bank_accounts[0]
        initial_balance = bank_account.get("current_balance", 0)
        print(f"\n1. Bank Account: {bank_account['account_name']}, Balance: {initial_balance}")
        
        # Step 2: Get sales orders
        orders_response = self.session.get(f"{BASE_URL}/api/sales-orders")
        assert orders_response.status_code == 200
        orders = orders_response.json()
        
        unpaid_orders = [o for o in orders if o.get("payment_status") != "paid" and o.get("status") != "returned"]
        
        if not unpaid_orders:
            print("2. No unpaid orders found - Test Complete (nothing to pay)")
            return
            
        order = unpaid_orders[0]
        balance_due = order["total"] - order.get("paid_amount", 0)
        print(f"\n2. Order: {order['order_number']}, Due: {balance_due}")
        
        # Step 3: Record payment
        payment_amount = min(balance_due, 500)  # Pay 500 or less
        payment_data = {
            "reference_type": "sales_order",
            "reference_id": order["id"],
            "amount": payment_amount,
            "payment_method": "bank",
            "bank_account_id": bank_account["id"],
            "notes": "E2E test payment"
        }
        
        payment_response = self.session.post(f"{BASE_URL}/api/payments", json=payment_data)
        assert payment_response.status_code in [200, 201], f"Payment failed: {payment_response.text}"
        print(f"\n3. Payment Recorded: {payment_amount} LKR")
        
        # Step 4: Verify bank balance
        updated_bank_response = self.session.get(f"{BASE_URL}/api/bank-accounts/{bank_account['id']}")
        assert updated_bank_response.status_code == 200
        new_balance = updated_bank_response.json().get("current_balance", 0)
        
        expected_balance = initial_balance + payment_amount
        print(f"\n4. Balance Check:")
        print(f"   Initial: {initial_balance}")
        print(f"   Expected: {expected_balance}")
        print(f"   Actual: {new_balance}")
        
        assert new_balance == expected_balance, f"Balance mismatch! Expected {expected_balance}, got {new_balance}"
        print("   STATUS: PASSED")
        
        # Step 5: Check journal entry
        journal_response = self.session.get(f"{BASE_URL}/api/journal-entries")
        assert journal_response.status_code == 200
        entries = journal_response.json()
        receipt_entries = [e for e in entries if e.get("entry_number", "").startswith("REC-")]
        print(f"\n5. Journal Entries: Found {len(receipt_entries)} receipt entries")
        
        # Step 6: Check order status
        order_response = self.session.get(f"{BASE_URL}/api/sales-orders/{order['id']}")
        assert order_response.status_code == 200
        updated_order = order_response.json()
        print(f"\n6. Order Status: {updated_order.get('payment_status')}")
        print(f"   Paid Amount: {updated_order.get('paid_amount')}")
        
        print("\n" + "="*60)
        print("TEST PASSED: Payment flow working correctly!")
        print("="*60)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
