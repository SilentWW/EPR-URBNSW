"""
Finance Router - Advanced Accounting Module
Double-entry bookkeeping, Chart of Accounts, GL, AR/AP, Tax Management, Financial Reports
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List
from datetime import datetime, timezone, timedelta
import uuid

from models.finance import (
    AccountCreate, AccountUpdate, AccountType, AccountCategory,
    JournalEntryCreate, JournalLineItem,
    TaxRateCreate, TaxRateUpdate,
    FinancialPeriodCreate, AgingBucket
)
from utils.helpers import serialize_doc, generate_id, get_current_timestamp, get_financial_year_dates
from utils.auth import get_current_user

router = APIRouter(prefix="/finance", tags=["Finance"])

# Database will be injected from main app
db = None

def set_db(database):
    global db
    db = database

def set_auth_dependency(auth_func):
    # Not needed with shared auth module
    pass

# ============== CHART OF ACCOUNTS ==============

DEFAULT_CHART_OF_ACCOUNTS = [
    # Assets (1xxx)
    {"code": "1000", "name": "Assets", "account_type": "asset", "category": "current_asset", "is_system": True},
    {"code": "1100", "name": "Cash", "account_type": "asset", "category": "cash", "is_system": True, "parent": "1000"},
    {"code": "1110", "name": "Petty Cash", "account_type": "asset", "category": "cash", "is_system": False, "parent": "1100"},
    {"code": "1200", "name": "Bank Accounts", "account_type": "asset", "category": "bank", "is_system": True, "parent": "1000"},
    {"code": "1210", "name": "Main Bank Account", "account_type": "asset", "category": "bank", "is_system": False, "parent": "1200"},
    {"code": "1300", "name": "Accounts Receivable", "account_type": "asset", "category": "accounts_receivable", "is_system": True, "parent": "1000"},
    {"code": "1400", "name": "Inventory", "account_type": "asset", "category": "inventory", "is_system": True, "parent": "1000"},
    {"code": "1500", "name": "Fixed Assets", "account_type": "asset", "category": "fixed_asset", "is_system": True, "parent": "1000"},
    
    # Liabilities (2xxx)
    {"code": "2000", "name": "Liabilities", "account_type": "liability", "category": "current_liability", "is_system": True},
    {"code": "2100", "name": "Accounts Payable", "account_type": "liability", "category": "accounts_payable", "is_system": True, "parent": "2000"},
    {"code": "2200", "name": "Tax Payable", "account_type": "liability", "category": "current_liability", "is_system": True, "parent": "2000"},
    {"code": "2300", "name": "Loans Payable", "account_type": "liability", "category": "long_term_liability", "is_system": False, "parent": "2000"},
    
    # Equity (3xxx)
    {"code": "3000", "name": "Equity", "account_type": "equity", "category": "capital", "is_system": True},
    {"code": "3100", "name": "Owner's Capital", "account_type": "equity", "category": "capital", "is_system": True, "parent": "3000"},
    {"code": "3200", "name": "Retained Earnings", "account_type": "equity", "category": "retained_earnings", "is_system": True, "parent": "3000"},
    
    # Income (4xxx)
    {"code": "4000", "name": "Income", "account_type": "income", "category": "revenue", "is_system": True},
    {"code": "4100", "name": "Sales Revenue", "account_type": "income", "category": "revenue", "is_system": True, "parent": "4000"},
    {"code": "4200", "name": "Service Revenue", "account_type": "income", "category": "revenue", "is_system": False, "parent": "4000"},
    {"code": "4900", "name": "Other Income", "account_type": "income", "category": "other_income", "is_system": False, "parent": "4000"},
    
    # Expenses (5xxx-6xxx)
    {"code": "5000", "name": "Cost of Goods Sold", "account_type": "expense", "category": "cost_of_goods_sold", "is_system": True},
    {"code": "5100", "name": "Purchases", "account_type": "expense", "category": "cost_of_goods_sold", "is_system": True, "parent": "5000"},
    {"code": "6000", "name": "Operating Expenses", "account_type": "expense", "category": "operating_expense", "is_system": True},
    {"code": "6100", "name": "Salaries & Wages", "account_type": "expense", "category": "operating_expense", "is_system": False, "parent": "6000"},
    {"code": "6200", "name": "Rent Expense", "account_type": "expense", "category": "operating_expense", "is_system": False, "parent": "6000"},
    {"code": "6300", "name": "Utilities", "account_type": "expense", "category": "operating_expense", "is_system": False, "parent": "6000"},
    {"code": "6400", "name": "Marketing & Advertising", "account_type": "expense", "category": "operating_expense", "is_system": False, "parent": "6000"},
    {"code": "6500", "name": "Office Supplies", "account_type": "expense", "category": "operating_expense", "is_system": False, "parent": "6000"},
    {"code": "6900", "name": "Tax Expense", "account_type": "expense", "category": "tax_expense", "is_system": True, "parent": "6000"},
]

@router.post("/chart-of-accounts/initialize")
async def initialize_chart_of_accounts(current_user: dict = Depends(get_current_user)):
    """Initialize default chart of accounts for the company"""
    company_id = current_user["company_id"]
    
    # Check if already initialized
    existing = await db.accounts.count_documents({"company_id": company_id})
    if existing > 0:
        return {"message": "Chart of accounts already initialized", "count": existing}
    
    # Create account ID mapping for parent references
    account_ids = {}
    
    for account in DEFAULT_CHART_OF_ACCOUNTS:
        account_id = generate_id()
        account_ids[account["code"]] = account_id
        
        parent_id = None
        if "parent" in account and account["parent"] in account_ids:
            parent_id = account_ids[account["parent"]]
        
        await db.accounts.insert_one({
            "id": account_id,
            "company_id": company_id,
            "code": account["code"],
            "name": account["name"],
            "account_type": account["account_type"],
            "category": account["category"],
            "description": None,
            "parent_account_id": parent_id,
            "is_system": account["is_system"],
            "is_active": True,
            "current_balance": 0.0,
            "created_at": get_current_timestamp(),
            "updated_at": get_current_timestamp()
        })
    
    return {"message": "Chart of accounts initialized", "count": len(DEFAULT_CHART_OF_ACCOUNTS)}

@router.get("/chart-of-accounts")
async def get_chart_of_accounts(
    account_type: Optional[str] = None,
    include_inactive: bool = False,
    current_user: dict = Depends(get_current_user)
):
    """Get all accounts in the chart of accounts"""
    query = {"company_id": current_user["company_id"]}
    
    if account_type:
        query["account_type"] = account_type
    if not include_inactive:
        query["is_active"] = True
    
    accounts = await db.accounts.find(query, {"_id": 0}).sort("code", 1).to_list(500)
    return accounts

@router.get("/chart-of-accounts/{account_id}")
async def get_account(account_id: str, current_user: dict = Depends(get_current_user)):
    """Get single account details with transaction history"""
    account = await db.accounts.find_one(
        {"id": account_id, "company_id": current_user["company_id"]},
        {"_id": 0}
    )
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Get recent transactions for this account
    journal_entries = await db.journal_entries.find(
        {
            "company_id": current_user["company_id"],
            "lines.account_id": account_id
        },
        {"_id": 0}
    ).sort("entry_date", -1).to_list(50)
    
    return {**account, "recent_transactions": journal_entries}

@router.post("/chart-of-accounts")
async def create_account(data: AccountCreate, current_user: dict = Depends(get_current_user)):
    """Create a new account"""
    company_id = current_user["company_id"]
    
    # Check for duplicate code
    existing = await db.accounts.find_one({"company_id": company_id, "code": data.code})
    if existing:
        raise HTTPException(status_code=400, detail="Account code already exists")
    
    account_id = generate_id()
    account = {
        "id": account_id,
        "company_id": company_id,
        "code": data.code,
        "name": data.name,
        "account_type": data.account_type.value,
        "category": data.category.value,
        "description": data.description,
        "parent_account_id": data.parent_account_id,
        "is_system": data.is_system,
        "is_active": True,
        "current_balance": data.opening_balance,
        "created_at": get_current_timestamp(),
        "updated_at": get_current_timestamp()
    }
    await db.accounts.insert_one(account)
    
    # If opening balance, create journal entry
    if data.opening_balance != 0:
        await _create_opening_balance_entry(company_id, account_id, data.opening_balance, data.account_type.value, current_user["user_id"])
    
    return serialize_doc(account)

@router.put("/chart-of-accounts/{account_id}")
async def update_account(account_id: str, data: AccountUpdate, current_user: dict = Depends(get_current_user)):
    """Update an account"""
    account = await db.accounts.find_one(
        {"id": account_id, "company_id": current_user["company_id"]}
    )
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    update_data["updated_at"] = get_current_timestamp()
    
    await db.accounts.update_one({"id": account_id}, {"$set": update_data})
    return await db.accounts.find_one({"id": account_id}, {"_id": 0})

@router.delete("/chart-of-accounts/{account_id}")
async def delete_account(account_id: str, current_user: dict = Depends(get_current_user)):
    """Delete an account (only if not system account and no transactions)"""
    account = await db.accounts.find_one(
        {"id": account_id, "company_id": current_user["company_id"]}
    )
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    if account.get("is_system"):
        raise HTTPException(status_code=400, detail="Cannot delete system account")
    
    # Check for transactions
    has_transactions = await db.journal_entries.find_one({"lines.account_id": account_id})
    if has_transactions:
        raise HTTPException(status_code=400, detail="Cannot delete account with transactions. Deactivate instead.")
    
    await db.accounts.delete_one({"id": account_id})
    return {"message": "Account deleted successfully"}

async def _create_opening_balance_entry(company_id: str, account_id: str, amount: float, account_type: str, user_id: str):
    """Helper to create opening balance journal entry"""
    # Get retained earnings account for balancing
    retained_earnings = await db.accounts.find_one({"company_id": company_id, "code": "3200"})
    if not retained_earnings:
        return
    
    entry_id = generate_id()
    entry_number = f"OB-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{entry_id[:4].upper()}"
    
    # Determine debit/credit based on account type
    if account_type in ["asset", "expense"]:
        lines = [
            {"account_id": account_id, "debit": abs(amount), "credit": 0, "description": "Opening balance"},
            {"account_id": retained_earnings["id"], "debit": 0, "credit": abs(amount), "description": "Opening balance offset"}
        ]
    else:
        lines = [
            {"account_id": account_id, "debit": 0, "credit": abs(amount), "description": "Opening balance"},
            {"account_id": retained_earnings["id"], "debit": abs(amount), "credit": 0, "description": "Opening balance offset"}
        ]
    
    entry = {
        "id": entry_id,
        "entry_number": entry_number,
        "company_id": company_id,
        "entry_date": get_current_timestamp()[:10],
        "reference_number": "OPENING",
        "description": "Opening Balance Entry",
        "lines": lines,
        "total_debit": abs(amount),
        "total_credit": abs(amount),
        "is_balanced": True,
        "is_auto_generated": True,
        "is_reversed": False,
        "reference_type": "opening_balance",
        "reference_id": account_id,
        "created_by": user_id,
        "created_at": get_current_timestamp()
    }
    await db.journal_entries.insert_one(entry)

# ============== JOURNAL ENTRIES (DOUBLE-ENTRY) ==============

@router.get("/journal-entries")
async def get_journal_entries(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    account_id: Optional[str] = None,
    reference_type: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get journal entries with optional filters"""
    query = {"company_id": current_user["company_id"]}
    
    if start_date:
        query["entry_date"] = {"$gte": start_date}
    if end_date:
        if "entry_date" in query:
            query["entry_date"]["$lte"] = end_date
        else:
            query["entry_date"] = {"$lte": end_date}
    if account_id:
        query["lines.account_id"] = account_id
    if reference_type:
        query["reference_type"] = reference_type
    
    entries = await db.journal_entries.find(query, {"_id": 0}).sort("entry_date", -1).to_list(500)
    return entries

@router.get("/journal-entries/{entry_id}")
async def get_journal_entry(entry_id: str, current_user: dict = Depends(get_current_user)):
    """Get single journal entry with full details"""
    entry = await db.journal_entries.find_one(
        {"id": entry_id, "company_id": current_user["company_id"]},
        {"_id": 0}
    )
    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    
    # Enrich with account names
    for line in entry.get("lines", []):
        account = await db.accounts.find_one({"id": line["account_id"]}, {"_id": 0, "code": 1, "name": 1})
        if account:
            line["account_code"] = account["code"]
            line["account_name"] = account["name"]
    
    return entry

@router.post("/journal-entries")
async def create_journal_entry(data: JournalEntryCreate, current_user: dict = Depends(get_current_user)):
    """Create a manual journal entry with double-entry validation"""
    company_id = current_user["company_id"]
    
    # Validate double-entry (debits must equal credits)
    total_debit = sum(line.debit for line in data.lines)
    total_credit = sum(line.credit for line in data.lines)
    
    if round(total_debit, 2) != round(total_credit, 2):
        raise HTTPException(
            status_code=400, 
            detail=f"Entry not balanced. Debits: {total_debit}, Credits: {total_credit}"
        )
    
    # Validate accounts exist
    for line in data.lines:
        account = await db.accounts.find_one({"id": line.account_id, "company_id": company_id})
        if not account:
            raise HTTPException(status_code=400, detail=f"Account {line.account_id} not found")
    
    entry_id = generate_id()
    entry_number = f"JE-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{entry_id[:4].upper()}"
    
    # Build lines with account info
    lines = []
    for line in data.lines:
        account = await db.accounts.find_one({"id": line.account_id}, {"_id": 0})
        lines.append({
            "account_id": line.account_id,
            "account_code": account["code"],
            "account_name": account["name"],
            "debit": line.debit,
            "credit": line.credit,
            "description": line.description
        })
    
    entry = {
        "id": entry_id,
        "entry_number": entry_number,
        "company_id": company_id,
        "entry_date": data.entry_date,
        "reference_number": data.reference_number,
        "description": data.description,
        "lines": lines,
        "total_debit": total_debit,
        "total_credit": total_credit,
        "is_balanced": True,
        "is_auto_generated": data.is_auto_generated,
        "is_reversed": False,
        "reference_type": data.reference_type or "manual",
        "reference_id": data.reference_id,
        "created_by": current_user["user_id"],
        "created_at": get_current_timestamp()
    }
    await db.journal_entries.insert_one(entry)
    
    # Update account balances
    for line in lines:
        await _update_account_balance(line["account_id"], line["debit"], line["credit"])
    
    return serialize_doc(entry)

@router.post("/journal-entries/{entry_id}/reverse")
async def reverse_journal_entry(entry_id: str, current_user: dict = Depends(get_current_user)):
    """Create a reversing entry for a journal entry"""
    original = await db.journal_entries.find_one(
        {"id": entry_id, "company_id": current_user["company_id"]}
    )
    if not original:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    
    if original.get("is_reversed"):
        raise HTTPException(status_code=400, detail="Entry already reversed")
    
    # Create reversing entry (swap debits and credits)
    reverse_id = generate_id()
    reverse_number = f"REV-{original['entry_number']}"
    
    reverse_lines = []
    for line in original["lines"]:
        reverse_lines.append({
            **line,
            "debit": line["credit"],
            "credit": line["debit"],
            "description": f"Reversal: {line.get('description', '')}"
        })
    
    reverse_entry = {
        "id": reverse_id,
        "entry_number": reverse_number,
        "company_id": current_user["company_id"],
        "entry_date": get_current_timestamp()[:10],
        "reference_number": f"REV-{original.get('reference_number', '')}",
        "description": f"Reversal of {original['entry_number']}: {original['description']}",
        "lines": reverse_lines,
        "total_debit": original["total_credit"],
        "total_credit": original["total_debit"],
        "is_balanced": True,
        "is_auto_generated": True,
        "is_reversed": False,
        "reference_type": "reversal",
        "reference_id": entry_id,
        "created_by": current_user["user_id"],
        "created_at": get_current_timestamp()
    }
    await db.journal_entries.insert_one(reverse_entry)
    
    # Mark original as reversed
    await db.journal_entries.update_one(
        {"id": entry_id},
        {"$set": {"is_reversed": True, "reversed_by": reverse_id}}
    )
    
    # Update account balances
    for line in reverse_lines:
        await _update_account_balance(line["account_id"], line["debit"], line["credit"])
    
    return serialize_doc(reverse_entry)

async def _update_account_balance(account_id: str, debit: float, credit: float):
    """Update account balance based on account type and debit/credit"""
    account = await db.accounts.find_one({"id": account_id})
    if not account:
        return
    
    # For asset/expense accounts: debit increases, credit decreases
    # For liability/equity/income accounts: credit increases, debit decreases
    if account["account_type"] in ["asset", "expense"]:
        balance_change = debit - credit
    else:
        balance_change = credit - debit
    
    new_balance = account.get("current_balance", 0) + balance_change
    await db.accounts.update_one(
        {"id": account_id},
        {"$set": {"current_balance": new_balance, "updated_at": get_current_timestamp()}}
    )

# ============== GENERAL LEDGER ==============

@router.get("/general-ledger")
async def get_general_ledger(
    account_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get general ledger with running balances"""
    company_id = current_user["company_id"]
    
    # Get accounts
    account_query = {"company_id": company_id, "is_active": True}
    if account_id:
        account_query["id"] = account_id
    
    accounts = await db.accounts.find(account_query, {"_id": 0}).sort("code", 1).to_list(500)
    
    ledger = []
    for account in accounts:
        # Get transactions for this account
        entry_query = {
            "company_id": company_id,
            "lines.account_id": account["id"]
        }
        if start_date:
            entry_query["entry_date"] = {"$gte": start_date}
        if end_date:
            if "entry_date" in entry_query:
                entry_query["entry_date"]["$lte"] = end_date
            else:
                entry_query["entry_date"] = {"$lte": end_date}
        
        entries = await db.journal_entries.find(entry_query, {"_id": 0}).sort("entry_date", 1).to_list(1000)
        
        # Calculate running balance
        transactions = []
        running_balance = 0
        
        for entry in entries:
            for line in entry["lines"]:
                if line["account_id"] == account["id"]:
                    if account["account_type"] in ["asset", "expense"]:
                        balance_change = line["debit"] - line["credit"]
                    else:
                        balance_change = line["credit"] - line["debit"]
                    
                    running_balance += balance_change
                    transactions.append({
                        "entry_id": entry["id"],
                        "entry_number": entry["entry_number"],
                        "date": entry["entry_date"],
                        "description": entry["description"],
                        "debit": line["debit"],
                        "credit": line["credit"],
                        "balance": running_balance
                    })
        
        ledger.append({
            "account_id": account["id"],
            "account_code": account["code"],
            "account_name": account["name"],
            "account_type": account["account_type"],
            "opening_balance": 0,  # Would need period start balance
            "transactions": transactions,
            "closing_balance": running_balance
        })
    
    return ledger

# ============== TAX MANAGEMENT ==============

@router.get("/tax-rates")
async def get_tax_rates(current_user: dict = Depends(get_current_user)):
    """Get all tax rates"""
    rates = await db.tax_rates.find(
        {"company_id": current_user["company_id"]},
        {"_id": 0}
    ).to_list(100)
    return rates

@router.post("/tax-rates")
async def create_tax_rate(data: TaxRateCreate, current_user: dict = Depends(get_current_user)):
    """Create a new tax rate"""
    company_id = current_user["company_id"]
    
    # Check for duplicate code
    existing = await db.tax_rates.find_one({"company_id": company_id, "code": data.code})
    if existing:
        raise HTTPException(status_code=400, detail="Tax code already exists")
    
    rate_id = generate_id()
    rate = {
        "id": rate_id,
        "company_id": company_id,
        **data.model_dump(),
        "is_active": True,
        "created_at": get_current_timestamp()
    }
    await db.tax_rates.insert_one(rate)
    return serialize_doc(rate)

@router.put("/tax-rates/{rate_id}")
async def update_tax_rate(rate_id: str, data: TaxRateUpdate, current_user: dict = Depends(get_current_user)):
    """Update a tax rate"""
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    update_data["updated_at"] = get_current_timestamp()
    
    result = await db.tax_rates.update_one(
        {"id": rate_id, "company_id": current_user["company_id"]},
        {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Tax rate not found")
    
    return await db.tax_rates.find_one({"id": rate_id}, {"_id": 0})

# ============== ACCOUNTS RECEIVABLE ==============

@router.get("/accounts-receivable")
async def get_accounts_receivable(current_user: dict = Depends(get_current_user)):
    """Get accounts receivable with aging"""
    company_id = current_user["company_id"]
    
    # Get unpaid sales orders
    orders = await db.sales_orders.find(
        {"company_id": company_id, "payment_status": {"$ne": "paid"}},
        {"_id": 0}
    ).to_list(1000)
    
    today = datetime.now(timezone.utc)
    receivables = []
    aging_totals = AgingBucket()
    
    for order in orders:
        balance = order["total"] - order.get("paid_amount", 0)
        if balance <= 0:
            continue
        
        # Calculate age
        order_date = datetime.fromisoformat(order["created_at"].replace('Z', '+00:00'))
        days_old = (today - order_date).days
        
        # Categorize by aging bucket
        if days_old <= 0:
            aging_totals.current += balance
            bucket = "current"
        elif days_old <= 30:
            aging_totals.days_1_30 += balance
            bucket = "1-30 days"
        elif days_old <= 60:
            aging_totals.days_31_60 += balance
            bucket = "31-60 days"
        elif days_old <= 90:
            aging_totals.days_61_90 += balance
            bucket = "61-90 days"
        else:
            aging_totals.days_over_90 += balance
            bucket = "Over 90 days"
        
        receivables.append({
            "order_id": order["id"],
            "order_number": order["order_number"],
            "customer_name": order["customer_name"],
            "date": order["created_at"][:10],
            "total": order["total"],
            "paid": order.get("paid_amount", 0),
            "balance": balance,
            "days_outstanding": days_old,
            "aging_bucket": bucket
        })
    
    aging_totals.total = (
        aging_totals.current + aging_totals.days_1_30 + aging_totals.days_31_60 +
        aging_totals.days_61_90 + aging_totals.days_over_90
    )
    
    return {
        "items": receivables,
        "aging_summary": aging_totals.model_dump(),
        "total_receivables": aging_totals.total
    }

# ============== ACCOUNTS PAYABLE ==============

@router.get("/accounts-payable")
async def get_accounts_payable(current_user: dict = Depends(get_current_user)):
    """Get accounts payable with aging"""
    company_id = current_user["company_id"]
    
    # Get unpaid purchase orders
    orders = await db.purchase_orders.find(
        {"company_id": company_id, "payment_status": {"$ne": "paid"}},
        {"_id": 0}
    ).to_list(1000)
    
    today = datetime.now(timezone.utc)
    payables = []
    aging_totals = AgingBucket()
    
    for order in orders:
        balance = order["total"] - order.get("paid_amount", 0)
        if balance <= 0:
            continue
        
        order_date = datetime.fromisoformat(order["created_at"].replace('Z', '+00:00'))
        days_old = (today - order_date).days
        
        if days_old <= 0:
            aging_totals.current += balance
            bucket = "current"
        elif days_old <= 30:
            aging_totals.days_1_30 += balance
            bucket = "1-30 days"
        elif days_old <= 60:
            aging_totals.days_31_60 += balance
            bucket = "31-60 days"
        elif days_old <= 90:
            aging_totals.days_61_90 += balance
            bucket = "61-90 days"
        else:
            aging_totals.days_over_90 += balance
            bucket = "Over 90 days"
        
        payables.append({
            "order_id": order["id"],
            "order_number": order["order_number"],
            "supplier_name": order["supplier_name"],
            "date": order["created_at"][:10],
            "total": order["total"],
            "paid": order.get("paid_amount", 0),
            "balance": balance,
            "days_outstanding": days_old,
            "aging_bucket": bucket
        })
    
    aging_totals.total = (
        aging_totals.current + aging_totals.days_1_30 + aging_totals.days_31_60 +
        aging_totals.days_61_90 + aging_totals.days_over_90
    )
    
    return {
        "items": payables,
        "aging_summary": aging_totals.model_dump(),
        "total_payables": aging_totals.total
    }

# ============== FINANCIAL REPORTS ==============

@router.get("/reports/trial-balance")
async def get_trial_balance(
    as_of_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Generate trial balance report"""
    company_id = current_user["company_id"]
    
    if not as_of_date:
        as_of_date = get_current_timestamp()[:10]
    
    # Get all active accounts with balances
    accounts = await db.accounts.find(
        {"company_id": company_id, "is_active": True},
        {"_id": 0}
    ).sort("code", 1).to_list(500)
    
    trial_balance = []
    total_debit = 0
    total_credit = 0
    
    for account in accounts:
        balance = account.get("current_balance", 0)
        
        if balance == 0:
            continue
        
        # Determine debit/credit based on account type and balance sign
        if account["account_type"] in ["asset", "expense"]:
            if balance >= 0:
                debit = balance
                credit = 0
            else:
                debit = 0
                credit = abs(balance)
        else:  # liability, equity, income
            if balance >= 0:
                debit = 0
                credit = balance
            else:
                debit = abs(balance)
                credit = 0
        
        total_debit += debit
        total_credit += credit
        
        trial_balance.append({
            "account_code": account["code"],
            "account_name": account["name"],
            "account_type": account["account_type"],
            "debit": debit,
            "credit": credit
        })
    
    return {
        "as_of_date": as_of_date,
        "accounts": trial_balance,
        "total_debit": round(total_debit, 2),
        "total_credit": round(total_credit, 2),
        "is_balanced": round(total_debit, 2) == round(total_credit, 2)
    }

@router.get("/reports/profit-loss")
async def get_profit_loss_report(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Generate Profit & Loss (Income Statement) report"""
    company_id = current_user["company_id"]
    
    # Default to current financial year
    if not start_date or not end_date:
        fy_start, fy_end = get_financial_year_dates(fy_start_month=4)
        start_date = start_date or fy_start.strftime("%Y-%m-%d")
        end_date = end_date or fy_end.strftime("%Y-%m-%d")
    
    # Get income accounts
    income_accounts = await db.accounts.find(
        {"company_id": company_id, "account_type": "income", "is_active": True},
        {"_id": 0}
    ).to_list(100)
    
    # Get expense accounts
    expense_accounts = await db.accounts.find(
        {"company_id": company_id, "account_type": "expense", "is_active": True},
        {"_id": 0}
    ).to_list(100)
    
    income_items = []
    total_income = 0
    
    for acc in income_accounts:
        balance = abs(acc.get("current_balance", 0))
        if balance > 0:
            income_items.append({
                "code": acc["code"],
                "name": acc["name"],
                "amount": balance
            })
            total_income += balance
    
    expense_items = []
    total_expenses = 0
    
    for acc in expense_accounts:
        balance = abs(acc.get("current_balance", 0))
        if balance > 0:
            expense_items.append({
                "code": acc["code"],
                "name": acc["name"],
                "amount": balance
            })
            total_expenses += balance
    
    net_profit = total_income - total_expenses
    
    return {
        "period": {"start_date": start_date, "end_date": end_date},
        "income": {
            "items": income_items,
            "total": round(total_income, 2)
        },
        "expenses": {
            "items": expense_items,
            "total": round(total_expenses, 2)
        },
        "net_profit": round(net_profit, 2),
        "gross_margin_percent": round((net_profit / total_income * 100) if total_income > 0 else 0, 2)
    }

@router.get("/reports/balance-sheet")
async def get_balance_sheet(
    as_of_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Generate Balance Sheet report"""
    company_id = current_user["company_id"]
    
    if not as_of_date:
        as_of_date = get_current_timestamp()[:10]
    
    # Get accounts by type
    accounts = await db.accounts.find(
        {"company_id": company_id, "is_active": True},
        {"_id": 0}
    ).to_list(500)
    
    assets = {"items": [], "total": 0}
    liabilities = {"items": [], "total": 0}
    equity = {"items": [], "total": 0}
    
    for acc in accounts:
        balance = acc.get("current_balance", 0)
        if balance == 0:
            continue
        
        item = {
            "code": acc["code"],
            "name": acc["name"],
            "category": acc["category"],
            "amount": abs(balance)
        }
        
        if acc["account_type"] == "asset":
            assets["items"].append(item)
            assets["total"] += abs(balance)
        elif acc["account_type"] == "liability":
            liabilities["items"].append(item)
            liabilities["total"] += abs(balance)
        elif acc["account_type"] == "equity":
            equity["items"].append(item)
            equity["total"] += abs(balance)
    
    # Add net profit to retained earnings (simplified)
    income_total = sum(acc.get("current_balance", 0) for acc in accounts if acc["account_type"] == "income")
    expense_total = sum(acc.get("current_balance", 0) for acc in accounts if acc["account_type"] == "expense")
    net_profit = abs(income_total) - abs(expense_total)
    
    equity["items"].append({
        "code": "NET",
        "name": "Net Profit (Current Period)",
        "category": "retained_earnings",
        "amount": net_profit
    })
    equity["total"] += net_profit
    
    return {
        "as_of_date": as_of_date,
        "assets": assets,
        "liabilities": liabilities,
        "equity": equity,
        "total_assets": round(assets["total"], 2),
        "total_liabilities_equity": round(liabilities["total"] + equity["total"], 2),
        "is_balanced": round(assets["total"], 2) == round(liabilities["total"] + equity["total"], 2)
    }

@router.get("/reports/cash-flow")
async def get_cash_flow_report(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Generate Cash Flow Statement"""
    company_id = current_user["company_id"]
    
    if not start_date or not end_date:
        fy_start, fy_end = get_financial_year_dates(fy_start_month=4)
        start_date = start_date or fy_start.strftime("%Y-%m-%d")
        end_date = end_date or fy_end.strftime("%Y-%m-%d")
    
    # Get bank transactions for the period
    transactions = await db.bank_transactions.find(
        {
            "company_id": company_id,
            "created_at": {"$gte": start_date, "$lte": end_date + "T23:59:59"}
        },
        {"_id": 0}
    ).to_list(10000)
    
    # Operating activities (from sales and purchases)
    operating_inflows = sum(t["amount"] for t in transactions if t["type"] == "credit" and t.get("reference_type") in ["sales_order", None])
    operating_outflows = sum(t["amount"] for t in transactions if t["type"] == "debit" and t.get("reference_type") in ["purchase_order", None])
    net_operating = operating_inflows - operating_outflows
    
    # Get payment summary
    payments = await db.payments.find(
        {"company_id": company_id, "created_at": {"$gte": start_date}},
        {"_id": 0}
    ).to_list(10000)
    
    cash_from_customers = sum(p["amount"] for p in payments if p["reference_type"] == "sales_order")
    cash_to_suppliers = sum(p["amount"] for p in payments if p["reference_type"] == "purchase_order")
    
    # Cash balance
    all_transactions = await db.bank_transactions.find(
        {"company_id": company_id},
        {"_id": 0}
    ).to_list(10000)
    
    opening_cash = sum(
        t["amount"] if t["type"] == "credit" else -t["amount"]
        for t in all_transactions
        if t["created_at"] < start_date
    )
    
    period_change = sum(
        t["amount"] if t["type"] == "credit" else -t["amount"]
        for t in transactions
    )
    
    closing_cash = opening_cash + period_change
    
    return {
        "period": {"start_date": start_date, "end_date": end_date},
        "operating_activities": {
            "cash_from_customers": round(cash_from_customers, 2),
            "cash_to_suppliers": round(cash_to_suppliers, 2),
            "net_operating_cash": round(net_operating, 2)
        },
        "investing_activities": {
            "items": [],
            "net_investing_cash": 0
        },
        "financing_activities": {
            "items": [],
            "net_financing_cash": 0
        },
        "opening_cash_balance": round(opening_cash, 2),
        "net_change_in_cash": round(period_change, 2),
        "closing_cash_balance": round(closing_cash, 2)
    }

# ============== FINANCIAL PERIODS ==============

@router.get("/financial-periods")
async def get_financial_periods(current_user: dict = Depends(get_current_user)):
    """Get all financial periods"""
    periods = await db.financial_periods.find(
        {"company_id": current_user["company_id"]},
        {"_id": 0}
    ).sort("start_date", -1).to_list(50)
    return periods

@router.post("/financial-periods")
async def create_financial_period(data: FinancialPeriodCreate, current_user: dict = Depends(get_current_user)):
    """Create a new financial period"""
    company_id = current_user["company_id"]
    
    period_id = generate_id()
    period = {
        "id": period_id,
        "company_id": company_id,
        **data.model_dump(),
        "created_at": get_current_timestamp()
    }
    await db.financial_periods.insert_one(period)
    return serialize_doc(period)

@router.post("/financial-periods/{period_id}/close")
async def close_financial_period(period_id: str, current_user: dict = Depends(get_current_user)):
    """Close a financial period (prevents further entries)"""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    result = await db.financial_periods.update_one(
        {"id": period_id, "company_id": current_user["company_id"]},
        {"$set": {"is_closed": True, "closed_at": get_current_timestamp(), "closed_by": current_user["user_id"]}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Period not found")
    
    return {"message": "Financial period closed successfully"}
