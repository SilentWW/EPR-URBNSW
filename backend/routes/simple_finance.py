"""
Simple Finance Router
User-friendly financial transactions without accounting knowledge
Auto-creates double-entry journal entries
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone

from utils.helpers import serialize_doc, generate_id, get_current_timestamp
from utils.auth import get_current_user

router = APIRouter(prefix="/simple-finance", tags=["Simple Finance"])

db = None

def set_db(database):
    global db
    db = database


# ============== MODELS ==============

class InvestorCreate(BaseModel):
    name: str
    investor_type: str  # director, shareholder, partner
    email: Optional[str] = None
    phone: Optional[str] = None
    id_number: Optional[str] = None  # NIC or Passport
    address: Optional[str] = None
    share_percentage: Optional[float] = None
    notes: Optional[str] = None

class CapitalInvestment(BaseModel):
    investor_id: str
    amount: float
    payment_method: str = "bank"  # cash, bank, cheque
    reference: Optional[str] = None
    notes: Optional[str] = None
    date: Optional[str] = None

class SalaryPayment(BaseModel):
    employee_name: str
    amount: float
    month: str  # e.g., "January 2026"
    payment_method: str = "bank"
    deductions: Optional[float] = 0
    allowances: Optional[float] = 0
    notes: Optional[str] = None
    date: Optional[str] = None

class ExpensePayment(BaseModel):
    expense_type: str  # utilities, rent, office_supplies, marketing, insurance, maintenance, other
    description: str
    amount: float
    payment_method: str = "bank"
    vendor: Optional[str] = None
    reference: Optional[str] = None
    notes: Optional[str] = None
    date: Optional[str] = None

class RevenueReceipt(BaseModel):
    revenue_type: str  # sales, service, interest, other
    description: str
    amount: float
    payment_method: str = "bank"
    customer: Optional[str] = None
    reference: Optional[str] = None
    notes: Optional[str] = None
    date: Optional[str] = None

class LoanTransaction(BaseModel):
    transaction_type: str  # receive, repay
    loan_type: str  # bank_loan, director_loan, other
    lender_name: str
    amount: float
    interest_amount: Optional[float] = 0
    reference: Optional[str] = None
    notes: Optional[str] = None
    date: Optional[str] = None

class CapitalWithdrawal(BaseModel):
    investor_id: str
    amount: float
    reason: str
    payment_method: str = "bank"
    reference: Optional[str] = None
    notes: Optional[str] = None
    date: Optional[str] = None


# ============== INVESTORS MANAGEMENT ==============

@router.get("/investors")
async def get_investors(current_user: dict = Depends(get_current_user)):
    """Get all investors (directors, shareholders, partners)"""
    investors = await db.investors.find(
        {"company_id": current_user["company_id"]},
        {"_id": 0}
    ).sort("name", 1).to_list(100)
    
    # Get capital account balances for each investor
    for investor in investors:
        account = await db.accounts.find_one({
            "company_id": current_user["company_id"],
            "investor_id": investor["id"]
        })
        investor["capital_balance"] = account.get("current_balance", 0) if account else 0
        investor["account_code"] = account.get("code") if account else None
    
    return investors

@router.post("/investors")
async def create_investor(
    data: InvestorCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new investor with auto-generated capital account"""
    company_id = current_user["company_id"]
    
    # Generate unique account code for this investor
    # Get next available code in 31xx range for equity
    existing_accounts = await db.accounts.find(
        {"company_id": company_id, "code": {"$regex": "^31"}},
        {"code": 1}
    ).to_list(100)
    
    existing_codes = [int(a["code"]) for a in existing_accounts if a["code"].isdigit()]
    next_code = max(existing_codes) + 1 if existing_codes else 3101
    
    # Determine account name based on investor type
    type_labels = {
        "director": "Director",
        "shareholder": "Shareholder", 
        "partner": "Partner"
    }
    type_label = type_labels.get(data.investor_type, "Investor")
    
    investor_id = generate_id()
    timestamp = get_current_timestamp()
    
    # Create investor record
    investor = {
        "id": investor_id,
        "company_id": company_id,
        "name": data.name,
        "investor_type": data.investor_type,
        "email": data.email,
        "phone": data.phone,
        "id_number": data.id_number,
        "address": data.address,
        "share_percentage": data.share_percentage,
        "notes": data.notes,
        "account_code": str(next_code),
        "is_active": True,
        "created_at": timestamp,
        "updated_at": timestamp
    }
    await db.investors.insert_one(investor)
    
    # Create capital account for this investor (matching finance.py format)
    account = {
        "id": generate_id(),
        "company_id": company_id,
        "code": str(next_code),
        "name": f"{type_label} Capital - {data.name}",
        "account_type": "equity",
        "category": "capital",
        "description": f"Capital account for {type_label.lower()} {data.name}",
        "parent_account_id": None,
        "is_system": False,
        "is_active": True,
        "current_balance": 0,
        "investor_id": investor_id,
        "created_at": timestamp,
        "updated_at": timestamp
    }
    await db.accounts.insert_one(account)
    
    return {
        "message": f"Investor created with capital account {next_code}",
        "investor": serialize_doc(investor),
        "account_code": str(next_code)
    }

@router.put("/investors/{investor_id}")
async def update_investor(
    investor_id: str,
    data: InvestorCreate,
    current_user: dict = Depends(get_current_user)
):
    """Update investor details"""
    company_id = current_user["company_id"]
    
    investor = await db.investors.find_one({
        "id": investor_id,
        "company_id": company_id
    })
    if not investor:
        raise HTTPException(status_code=404, detail="Investor not found")
    
    update_data = {
        "name": data.name,
        "investor_type": data.investor_type,
        "email": data.email,
        "phone": data.phone,
        "id_number": data.id_number,
        "address": data.address,
        "share_percentage": data.share_percentage,
        "notes": data.notes,
        "updated_at": get_current_timestamp()
    }
    
    await db.investors.update_one(
        {"id": investor_id},
        {"$set": update_data}
    )
    
    # Update account name if investor name changed
    type_labels = {"director": "Director", "shareholder": "Shareholder", "partner": "Partner"}
    type_label = type_labels.get(data.investor_type, "Investor")
    
    await db.accounts.update_one(
        {"investor_id": investor_id},
        {"$set": {"name": f"{type_label} Capital - {data.name}"}}
    )
    
    return {"message": "Investor updated successfully"}

@router.delete("/investors/{investor_id}")
async def delete_investor(
    investor_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete investor (only if capital balance is zero)"""
    company_id = current_user["company_id"]
    
    investor = await db.investors.find_one({
        "id": investor_id,
        "company_id": company_id
    })
    if not investor:
        raise HTTPException(status_code=404, detail="Investor not found")
    
    # Check if capital account has balance
    account = await db.accounts.find_one({
        "investor_id": investor_id,
        "company_id": company_id
    })
    
    if account and account.get("current_balance", 0) != 0:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot delete investor with capital balance of {account['current_balance']}"
        )
    
    await db.investors.delete_one({"id": investor_id})
    await db.accounts.delete_one({"investor_id": investor_id})
    
    return {"message": "Investor deleted successfully"}


# ============== QUICK TRANSACTIONS ==============

@router.post("/capital-investment")
async def record_capital_investment(
    data: CapitalInvestment,
    current_user: dict = Depends(get_current_user)
):
    """Record capital investment - auto-creates journal entry"""
    company_id = current_user["company_id"]
    user_id = current_user["user_id"]
    
    # Get investor
    investor = await db.investors.find_one({
        "id": data.investor_id,
        "company_id": company_id
    })
    if not investor:
        raise HTTPException(status_code=404, detail="Investor not found")
    
    # Get investor's capital account
    capital_account = await db.accounts.find_one({
        "investor_id": data.investor_id,
        "company_id": company_id
    })
    if not capital_account:
        raise HTTPException(status_code=404, detail="Capital account not found")
    
    # Get cash/bank account
    cash_account = await db.accounts.find_one({
        "company_id": company_id,
        "code": "1100"
    })
    if not cash_account:
        raise HTTPException(status_code=404, detail="Cash/Bank account not found")
    
    timestamp = data.date or get_current_timestamp()
    entry_id = generate_id()
    
    # Create double-entry journal entry
    # Debit: Cash/Bank (Asset increases)
    # Credit: Capital Account (Equity increases)
    journal_entry = {
        "id": entry_id,
        "company_id": company_id,
        "date": timestamp,
        "description": f"Capital Investment from {investor['name']} ({investor['investor_type'].title()})",
        "reference": data.reference,
        "reference_type": "capital_investment",
        "reference_id": data.investor_id,
        "entries": [
            {
                "account_code": "1100",
                "account_name": "Cash/Bank",
                "debit": data.amount,
                "credit": 0
            },
            {
                "account_code": capital_account["code"],
                "account_name": capital_account["name"],
                "debit": 0,
                "credit": data.amount
            }
        ],
        "total_debit": data.amount,
        "total_credit": data.amount,
        "status": "posted",
        "payment_method": data.payment_method,
        "notes": data.notes,
        "is_auto_generated": True,
        "transaction_type": "capital_investment",
        "created_by": user_id,
        "created_at": timestamp
    }
    await db.journal_entries.insert_one(journal_entry)
    
    # Update account balances
    await db.accounts.update_one(
        {"id": cash_account["id"]},
        {"$inc": {"current_balance": data.amount, "balance": data.amount}}
    )
    await db.accounts.update_one(
        {"id": capital_account["id"]},
        {"$inc": {"current_balance": data.amount, "balance": data.amount}}
    )
    
    return {
        "message": f"Capital investment of LKR {data.amount:,.2f} recorded successfully",
        "journal_entry_id": entry_id,
        "investor": investor["name"],
        "new_capital_balance": capital_account.get("current_balance", 0) + data.amount
    }

@router.post("/capital-withdrawal")
async def record_capital_withdrawal(
    data: CapitalWithdrawal,
    current_user: dict = Depends(get_current_user)
):
    """Record capital withdrawal - auto-creates journal entry"""
    company_id = current_user["company_id"]
    user_id = current_user["user_id"]
    
    investor = await db.investors.find_one({
        "id": data.investor_id,
        "company_id": company_id
    })
    if not investor:
        raise HTTPException(status_code=404, detail="Investor not found")
    
    capital_account = await db.accounts.find_one({
        "investor_id": data.investor_id,
        "company_id": company_id
    })
    
    # Check if sufficient balance
    if capital_account.get("current_balance", 0) < data.amount:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient capital balance. Available: LKR {capital_account.get('current_balance', 0):,.2f}"
        )
    
    cash_account = await db.accounts.find_one({
        "company_id": company_id,
        "code": "1100"
    })
    
    timestamp = data.date or get_current_timestamp()
    entry_id = generate_id()
    
    # Debit: Capital Account (Equity decreases)
    # Credit: Cash/Bank (Asset decreases)
    journal_entry = {
        "id": entry_id,
        "company_id": company_id,
        "date": timestamp,
        "description": f"Capital Withdrawal by {investor['name']} - {data.reason}",
        "reference": data.reference,
        "reference_type": "capital_withdrawal",
        "reference_id": data.investor_id,
        "entries": [
            {
                "account_code": capital_account["code"],
                "account_name": capital_account["name"],
                "debit": data.amount,
                "credit": 0
            },
            {
                "account_code": "1100",
                "account_name": "Cash/Bank",
                "debit": 0,
                "credit": data.amount
            }
        ],
        "total_debit": data.amount,
        "total_credit": data.amount,
        "status": "posted",
        "payment_method": data.payment_method,
        "notes": data.notes,
        "is_auto_generated": True,
        "transaction_type": "capital_withdrawal",
        "created_by": user_id,
        "created_at": timestamp
    }
    await db.journal_entries.insert_one(journal_entry)
    
    await db.accounts.update_one(
        {"id": cash_account["id"]},
        {"$inc": {"current_balance": -data.amount, "balance": -data.amount}}
    )
    await db.accounts.update_one(
        {"id": capital_account["id"]},
        {"$inc": {"current_balance": -data.amount, "balance": -data.amount}}
    )
    
    return {
        "message": f"Capital withdrawal of LKR {data.amount:,.2f} recorded successfully",
        "journal_entry_id": entry_id
    }

@router.post("/salary-payment")
async def record_salary_payment(
    data: SalaryPayment,
    current_user: dict = Depends(get_current_user)
):
    """Record salary payment - auto-creates journal entry"""
    company_id = current_user["company_id"]
    user_id = current_user["user_id"]
    timestamp = data.date or get_current_timestamp()
    
    # Get or create salary expense account (try 6100 first, then 5200)
    salary_account = await db.accounts.find_one({
        "company_id": company_id,
        "code": {"$in": ["6100", "5200"]}
    })
    
    if not salary_account:
        # Create salary expense account
        salary_account = {
            "id": generate_id(),
            "company_id": company_id,
            "code": "6100",
            "name": "Salaries & Wages",
            "account_type": "expense",
            "category": "operating_expense",
            "description": "Employee salaries and wages expense",
            "parent_account_id": None,
            "is_system": False,
            "is_active": True,
            "current_balance": 0,
            "created_at": timestamp,
            "updated_at": timestamp
        }
        await db.accounts.insert_one(salary_account)
    
    # Get or create cash account
    cash_account = await db.accounts.find_one({
        "company_id": company_id,
        "code": "1100"
    })
    
    if not cash_account:
        cash_account = {
            "id": generate_id(),
            "company_id": company_id,
            "code": "1100",
            "name": "Cash/Bank",
            "account_type": "asset",
            "category": "cash",
            "description": "Cash and bank accounts",
            "parent_account_id": None,
            "is_system": True,
            "is_active": True,
            "current_balance": 0,
            "created_at": timestamp,
            "updated_at": timestamp
        }
        await db.accounts.insert_one(cash_account)
    
    gross_salary = data.amount + data.allowances
    net_salary = gross_salary - data.deductions
    
    entry_id = generate_id()
    
    # Debit: Salaries & Wages Expense
    # Credit: Cash/Bank
    journal_entry = {
        "id": entry_id,
        "company_id": company_id,
        "date": timestamp,
        "description": f"Salary Payment - {data.employee_name} ({data.month})",
        "reference_type": "salary_payment",
        "entries": [
            {
                "account_code": salary_account["code"],
                "account_name": salary_account["name"],
                "debit": gross_salary,
                "credit": 0
            },
            {
                "account_code": "1100",
                "account_name": "Cash/Bank",
                "debit": 0,
                "credit": net_salary
            }
        ],
        "total_debit": gross_salary,
        "total_credit": net_salary,
        "status": "posted",
        "payment_method": data.payment_method,
        "notes": data.notes,
        "metadata": {
            "employee_name": data.employee_name,
            "month": data.month,
            "gross_salary": gross_salary,
            "deductions": data.deductions,
            "allowances": data.allowances,
            "net_salary": net_salary
        },
        "is_auto_generated": True,
        "transaction_type": "salary_payment",
        "created_by": user_id,
        "created_at": timestamp
    }
    
    # Handle deductions (if any) - credit to liability account
    if data.deductions > 0:
        journal_entry["entries"].append({
            "account_code": "2200",
            "account_name": "Accrued Expenses",
            "debit": 0,
            "credit": data.deductions
        })
        journal_entry["total_credit"] = gross_salary
    
    await db.journal_entries.insert_one(journal_entry)
    
    # Update account balances
    await db.accounts.update_one(
        {"id": salary_account["id"]},
        {"$inc": {"current_balance": gross_salary}}
    )
    await db.accounts.update_one(
        {"id": cash_account["id"]},
        {"$inc": {"current_balance": -net_salary}}
    )
    
    return {
        "message": f"Salary payment of LKR {net_salary:,.2f} recorded for {data.employee_name}",
        "journal_entry_id": entry_id,
        "gross_salary": gross_salary,
        "deductions": data.deductions,
        "net_salary": net_salary
    }

@router.post("/expense-payment")
async def record_expense_payment(
    data: ExpensePayment,
    current_user: dict = Depends(get_current_user)
):
    """Record expense payment - auto-creates journal entry"""
    company_id = current_user["company_id"]
    user_id = current_user["user_id"]
    timestamp = data.date or get_current_timestamp()
    
    # Map expense types to account codes (using 6xxx series for operating expenses)
    expense_accounts = {
        "utilities": {"code": "6300", "name": "Utilities Expense"},
        "rent": {"code": "6200", "name": "Rent Expense"},
        "office_supplies": {"code": "6500", "name": "Office Supplies"},
        "marketing": {"code": "6400", "name": "Marketing & Advertising"},
        "insurance": {"code": "6600", "name": "Insurance Expense"},
        "maintenance": {"code": "6700", "name": "Maintenance & Repairs"},
        "transport": {"code": "6800", "name": "Transport & Travel"},
        "communication": {"code": "6350", "name": "Communication Expense"},
        "professional_fees": {"code": "6450", "name": "Professional Fees"},
        "other": {"code": "6900", "name": "Other Expenses"}
    }
    
    expense_info = expense_accounts.get(data.expense_type, expense_accounts["other"])
    
    # Get or create expense account
    expense_account = await db.accounts.find_one({
        "company_id": company_id,
        "code": expense_info["code"]
    })
    
    if not expense_account:
        expense_account = {
            "id": generate_id(),
            "company_id": company_id,
            "code": expense_info["code"],
            "name": expense_info["name"],
            "account_type": "expense",
            "category": "operating_expense",
            "description": f"Operating expense - {expense_info['name']}",
            "parent_account_id": None,
            "is_system": False,
            "is_active": True,
            "current_balance": 0,
            "created_at": timestamp,
            "updated_at": timestamp
        }
        await db.accounts.insert_one(expense_account)
    
    # Get or create cash account
    cash_account = await db.accounts.find_one({
        "company_id": company_id,
        "code": "1100"
    })
    
    if not cash_account:
        cash_account = {
            "id": generate_id(),
            "company_id": company_id,
            "code": "1100",
            "name": "Cash/Bank",
            "account_type": "asset",
            "category": "cash",
            "description": "Cash and bank accounts",
            "parent_account_id": None,
            "is_system": True,
            "is_active": True,
            "current_balance": 0,
            "created_at": timestamp,
            "updated_at": timestamp
        }
        await db.accounts.insert_one(cash_account)
    
    entry_id = generate_id()
    
    # Debit: Expense Account
    # Credit: Cash/Bank
    journal_entry = {
        "id": entry_id,
        "company_id": company_id,
        "date": timestamp,
        "description": f"{expense_info['name']} - {data.description}",
        "reference": data.reference,
        "reference_type": "expense_payment",
        "entries": [
            {
                "account_code": expense_info["code"],
                "account_name": expense_info["name"],
                "debit": data.amount,
                "credit": 0
            },
            {
                "account_code": "1100",
                "account_name": "Cash/Bank",
                "debit": 0,
                "credit": data.amount
            }
        ],
        "total_debit": data.amount,
        "total_credit": data.amount,
        "status": "posted",
        "payment_method": data.payment_method,
        "notes": data.notes,
        "metadata": {
            "expense_type": data.expense_type,
            "vendor": data.vendor
        },
        "is_auto_generated": True,
        "transaction_type": "expense_payment",
        "created_by": user_id,
        "created_at": timestamp
    }
    await db.journal_entries.insert_one(journal_entry)
    
    await db.accounts.update_one(
        {"id": expense_account["id"]},
        {"$inc": {"current_balance": data.amount, "balance": data.amount}}
    )
    await db.accounts.update_one(
        {"id": cash_account["id"]},
        {"$inc": {"current_balance": -data.amount, "balance": -data.amount}}
    )
    
    return {
        "message": f"Expense of LKR {data.amount:,.2f} recorded for {data.description}",
        "journal_entry_id": entry_id,
        "expense_type": data.expense_type
    }

@router.post("/revenue-receipt")
async def record_revenue_receipt(
    data: RevenueReceipt,
    current_user: dict = Depends(get_current_user)
):
    """Record revenue receipt - auto-creates journal entry"""
    company_id = current_user["company_id"]
    user_id = current_user["user_id"]
    
    # Map revenue types to account codes
    revenue_accounts = {
        "sales": {"code": "4100", "name": "Sales Revenue"},
        "service": {"code": "4300", "name": "Service Revenue"},
        "interest": {"code": "4400", "name": "Interest Income"},
        "commission": {"code": "4500", "name": "Commission Income"},
        "other": {"code": "4900", "name": "Other Income"}
    }
    
    revenue_info = revenue_accounts.get(data.revenue_type, revenue_accounts["other"])
    
    # Ensure revenue account exists
    revenue_account = await db.accounts.find_one({
        "company_id": company_id,
        "code": revenue_info["code"]
    })
    
    if not revenue_account:
        revenue_account = {
            "id": generate_id(),
            "company_id": company_id,
            "code": revenue_info["code"],
            "name": revenue_info["name"],
            "category": "Revenue",
            "type": "credit",
            "balance": 0,
            "current_balance": 0,
            "is_system": True,
            "created_at": get_current_timestamp()
        }
        await db.accounts.insert_one(revenue_account)
    
    cash_account = await db.accounts.find_one({
        "company_id": company_id,
        "code": "1100"
    })
    
    timestamp = data.date or get_current_timestamp()
    entry_id = generate_id()
    
    # Debit: Cash/Bank
    # Credit: Revenue Account
    journal_entry = {
        "id": entry_id,
        "company_id": company_id,
        "date": timestamp,
        "description": f"{revenue_info['name']} - {data.description}",
        "reference": data.reference,
        "reference_type": "revenue_receipt",
        "entries": [
            {
                "account_code": "1100",
                "account_name": "Cash/Bank",
                "debit": data.amount,
                "credit": 0
            },
            {
                "account_code": revenue_info["code"],
                "account_name": revenue_info["name"],
                "debit": 0,
                "credit": data.amount
            }
        ],
        "total_debit": data.amount,
        "total_credit": data.amount,
        "status": "posted",
        "payment_method": data.payment_method,
        "notes": data.notes,
        "metadata": {
            "revenue_type": data.revenue_type,
            "customer": data.customer
        },
        "is_auto_generated": True,
        "transaction_type": "revenue_receipt",
        "created_by": user_id,
        "created_at": timestamp
    }
    await db.journal_entries.insert_one(journal_entry)
    
    await db.accounts.update_one(
        {"id": cash_account["id"]},
        {"$inc": {"current_balance": data.amount, "balance": data.amount}}
    )
    await db.accounts.update_one(
        {"id": revenue_account["id"]},
        {"$inc": {"current_balance": data.amount, "balance": data.amount}}
    )
    
    return {
        "message": f"Revenue of LKR {data.amount:,.2f} recorded for {data.description}",
        "journal_entry_id": entry_id
    }

@router.post("/loan-transaction")
async def record_loan_transaction(
    data: LoanTransaction,
    current_user: dict = Depends(get_current_user)
):
    """Record loan received or repayment - auto-creates journal entry"""
    company_id = current_user["company_id"]
    user_id = current_user["user_id"]
    
    # Map loan types to account codes
    loan_accounts = {
        "bank_loan": {"code": "2400", "name": "Bank Loans"},
        "director_loan": {"code": "2450", "name": "Director Loans"},
        "other": {"code": "2490", "name": "Other Loans"}
    }
    
    loan_info = loan_accounts.get(data.loan_type, loan_accounts["other"])
    
    # Ensure loan account exists
    loan_account = await db.accounts.find_one({
        "company_id": company_id,
        "code": loan_info["code"]
    })
    
    if not loan_account:
        loan_account = {
            "id": generate_id(),
            "company_id": company_id,
            "code": loan_info["code"],
            "name": loan_info["name"],
            "category": "Liabilities",
            "type": "credit",
            "balance": 0,
            "current_balance": 0,
            "is_system": True,
            "created_at": get_current_timestamp()
        }
        await db.accounts.insert_one(loan_account)
    
    cash_account = await db.accounts.find_one({
        "company_id": company_id,
        "code": "1100"
    })
    
    interest_account = await db.accounts.find_one({
        "company_id": company_id,
        "code": "5850"
    })
    
    if not interest_account and data.interest_amount > 0:
        interest_account = {
            "id": generate_id(),
            "company_id": company_id,
            "code": "5850",
            "name": "Interest Expense",
            "category": "Expenses",
            "type": "debit",
            "balance": 0,
            "current_balance": 0,
            "is_system": True,
            "created_at": get_current_timestamp()
        }
        await db.accounts.insert_one(interest_account)
    
    timestamp = data.date or get_current_timestamp()
    entry_id = generate_id()
    
    if data.transaction_type == "receive":
        # Loan Received
        # Debit: Cash/Bank
        # Credit: Loan Account
        journal_entry = {
            "id": entry_id,
            "company_id": company_id,
            "date": timestamp,
            "description": f"Loan Received from {data.lender_name}",
            "reference": data.reference,
            "reference_type": "loan_received",
            "entries": [
                {
                    "account_code": "1100",
                    "account_name": "Cash/Bank",
                    "debit": data.amount,
                    "credit": 0
                },
                {
                    "account_code": loan_info["code"],
                    "account_name": loan_info["name"],
                    "debit": 0,
                    "credit": data.amount
                }
            ],
            "total_debit": data.amount,
            "total_credit": data.amount,
            "status": "posted",
            "notes": data.notes,
            "metadata": {"lender": data.lender_name, "loan_type": data.loan_type},
            "is_auto_generated": True,
            "transaction_type": "loan_received",
            "created_by": user_id,
            "created_at": timestamp
        }
        
        await db.accounts.update_one(
            {"id": cash_account["id"]},
            {"$inc": {"current_balance": data.amount, "balance": data.amount}}
        )
        await db.accounts.update_one(
            {"id": loan_account["id"]},
            {"$inc": {"current_balance": data.amount, "balance": data.amount}}
        )
        
    else:
        # Loan Repayment
        # Debit: Loan Account (principal)
        # Debit: Interest Expense (if any)
        # Credit: Cash/Bank
        total_payment = data.amount + (data.interest_amount or 0)
        
        entries = [
            {
                "account_code": loan_info["code"],
                "account_name": loan_info["name"],
                "debit": data.amount,
                "credit": 0
            }
        ]
        
        if data.interest_amount > 0:
            entries.append({
                "account_code": "5850",
                "account_name": "Interest Expense",
                "debit": data.interest_amount,
                "credit": 0
            })
        
        entries.append({
            "account_code": "1100",
            "account_name": "Cash/Bank",
            "debit": 0,
            "credit": total_payment
        })
        
        journal_entry = {
            "id": entry_id,
            "company_id": company_id,
            "date": timestamp,
            "description": f"Loan Repayment to {data.lender_name}",
            "reference": data.reference,
            "reference_type": "loan_repayment",
            "entries": entries,
            "total_debit": total_payment,
            "total_credit": total_payment,
            "status": "posted",
            "notes": data.notes,
            "metadata": {
                "lender": data.lender_name,
                "principal": data.amount,
                "interest": data.interest_amount
            },
            "is_auto_generated": True,
            "transaction_type": "loan_repayment",
            "created_by": user_id,
            "created_at": timestamp
        }
        
        await db.accounts.update_one(
            {"id": loan_account["id"]},
            {"$inc": {"current_balance": -data.amount, "balance": -data.amount}}
        )
        await db.accounts.update_one(
            {"id": cash_account["id"]},
            {"$inc": {"current_balance": -total_payment, "balance": -total_payment}}
        )
        if data.interest_amount > 0 and interest_account:
            await db.accounts.update_one(
                {"id": interest_account["id"]},
                {"$inc": {"current_balance": data.interest_amount, "balance": data.interest_amount}}
            )
    
    await db.journal_entries.insert_one(journal_entry)
    
    action = "received" if data.transaction_type == "receive" else "repaid"
    return {
        "message": f"Loan of LKR {data.amount:,.2f} {action} successfully",
        "journal_entry_id": entry_id
    }


# ============== TRANSACTION SUMMARY ==============

@router.get("/transaction-types")
async def get_transaction_types():
    """Get available quick transaction types"""
    return {
        "capital": [
            {"type": "capital_investment", "label": "Capital Investment", "description": "Record investor putting money into business"},
            {"type": "capital_withdrawal", "label": "Capital Withdrawal", "description": "Record investor taking money out"}
        ],
        "expenses": [
            {"type": "utilities", "label": "Utilities (Electricity, Water)", "account": "5400"},
            {"type": "rent", "label": "Rent Payment", "account": "5300"},
            {"type": "office_supplies", "label": "Office Supplies", "account": "5600"},
            {"type": "marketing", "label": "Marketing & Advertising", "account": "5500"},
            {"type": "insurance", "label": "Insurance", "account": "5800"},
            {"type": "maintenance", "label": "Repairs & Maintenance", "account": "5900"},
            {"type": "transport", "label": "Transport & Travel", "account": "5950"},
            {"type": "communication", "label": "Phone & Internet", "account": "5960"},
            {"type": "professional_fees", "label": "Professional Fees", "account": "5970"},
            {"type": "other", "label": "Other Expenses", "account": "5999"}
        ],
        "revenue": [
            {"type": "sales", "label": "Sales Revenue", "account": "4100"},
            {"type": "service", "label": "Service Income", "account": "4300"},
            {"type": "interest", "label": "Interest Income", "account": "4400"},
            {"type": "commission", "label": "Commission Income", "account": "4500"},
            {"type": "other", "label": "Other Income", "account": "4900"}
        ],
        "payroll": [
            {"type": "salary_payment", "label": "Salary Payment", "description": "Pay employee salary"}
        ],
        "loans": [
            {"type": "loan_receive", "label": "Receive Loan", "description": "Record loan received"},
            {"type": "loan_repay", "label": "Repay Loan", "description": "Record loan repayment with interest"}
        ]
    }

@router.get("/recent-transactions")
async def get_recent_transactions(
    limit: int = 20,
    current_user: dict = Depends(get_current_user)
):
    """Get recent quick transactions"""
    transactions = await db.journal_entries.find(
        {
            "company_id": current_user["company_id"],
            "is_auto_generated": True,
            "transaction_type": {"$exists": True}
        },
        {"_id": 0}
    ).sort("created_at", -1).to_list(limit)
    
    return transactions
