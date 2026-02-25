"""
Simple Finance Router
User-friendly financial transactions without accounting knowledge
Auto-creates double-entry journal entries using the same schema as finance.py
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
    bank_account_id: Optional[str] = None  # Bank/Cash account to receive funds
    payment_method: str = "bank"  # cash, bank, cheque
    reference: Optional[str] = None
    notes: Optional[str] = None
    date: Optional[str] = None

class SalaryPayment(BaseModel):
    employee_name: str
    amount: float
    month: str  # e.g., "January 2026"
    bank_account_id: Optional[str] = None  # Bank/Cash account to pay from
    payment_method: str = "bank"
    deductions: Optional[float] = 0
    allowances: Optional[float] = 0
    notes: Optional[str] = None
    date: Optional[str] = None

class ExpensePayment(BaseModel):
    expense_type: str  # utilities, rent, office_supplies, marketing, insurance, maintenance, other
    description: str
    amount: float
    bank_account_id: Optional[str] = None  # Bank/Cash account to pay from
    expense_account_code: Optional[str] = None  # Override expense account (e.g., "6100", "6200", "6900")
    payment_method: str = "bank"
    vendor: Optional[str] = None
    reference: Optional[str] = None
    notes: Optional[str] = None
    date: Optional[str] = None

class RevenueReceipt(BaseModel):
    revenue_type: str  # sales, service, interest, other
    description: str
    amount: float
    bank_account_id: Optional[str] = None  # Bank/Cash account to receive funds
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
    bank_account_id: Optional[str] = None  # Bank/Cash account
    interest_amount: Optional[float] = 0
    reference: Optional[str] = None
    notes: Optional[str] = None
    date: Optional[str] = None

class CapitalWithdrawal(BaseModel):
    investor_id: str
    amount: float
    reason: str
    bank_account_id: Optional[str] = None  # Bank/Cash account to pay from
    payment_method: str = "bank"
    reference: Optional[str] = None
    notes: Optional[str] = None
    date: Optional[str] = None


# ============== HELPER FUNCTIONS ==============

async def get_bank_cash_account(company_id: str, bank_account_id: str = None):
    """Get the appropriate bank/cash account for a transaction.
    If bank_account_id is provided, get that specific account.
    Otherwise, fall back to default Cash account (1100).
    """
    if bank_account_id:
        # Get the chart account linked to this bank account
        bank_account = await db.bank_accounts.find_one({
            "id": bank_account_id,
            "company_id": company_id
        })
        if bank_account and bank_account.get("chart_account_id"):
            chart_account = await db.accounts.find_one({"id": bank_account["chart_account_id"]})
            if chart_account:
                return chart_account
        # If bank account has a linked chart account code
        if bank_account:
            chart_account = await db.accounts.find_one({
                "company_id": company_id,
                "code": bank_account.get("chart_account_code")
            })
            if chart_account:
                return chart_account
    
    # Fall back to default Cash account
    return await get_or_create_account(
        company_id, "1100", "Cash", "asset", "cash", "1000"
    )

async def recalculate_share_percentages(company_id: str):
    """
    Recalculate share percentages for all investors based on their capital balances.
    Share % = (investor's capital balance / total capital of all investors) * 100
    """
    # Get all investors for this company
    investors = await db.investors.find({"company_id": company_id}).to_list(100)
    
    if not investors:
        return
    
    # Calculate total capital from all investor capital accounts
    total_capital = 0
    investor_balances = {}
    
    for investor in investors:
        account = await db.accounts.find_one({
            "company_id": company_id,
            "investor_id": investor["id"]
        })
        balance = account.get("current_balance", 0) if account else 0
        investor_balances[investor["id"]] = balance
        total_capital += balance
    
    # Update share percentages for each investor
    for investor in investors:
        balance = investor_balances.get(investor["id"], 0)
        if total_capital > 0:
            share_percentage = round((balance / total_capital) * 100, 2)
        else:
            share_percentage = 0
        
        await db.investors.update_one(
            {"id": investor["id"]},
            {"$set": {"share_percentage": share_percentage, "updated_at": get_current_timestamp()}}
        )


async def get_or_create_account(company_id: str, code: str, name: str, account_type: str, category: str, parent_code: str = None):
    """Get an existing account by code or create it if it doesn't exist"""
    account = await db.accounts.find_one({
        "company_id": company_id,
        "code": code
    })
    
    if account:
        return account
    
    # Get parent account ID if parent_code provided
    parent_account_id = None
    if parent_code:
        parent = await db.accounts.find_one({"company_id": company_id, "code": parent_code})
        if parent:
            parent_account_id = parent["id"]
    
    timestamp = get_current_timestamp()
    new_account = {
        "id": generate_id(),
        "company_id": company_id,
        "code": code,
        "name": name,
        "account_type": account_type,
        "category": category,
        "description": f"Auto-created for {name}",
        "parent_account_id": parent_account_id,
        "is_system": False,
        "is_active": True,
        "current_balance": 0.0,
        "created_at": timestamp,
        "updated_at": timestamp
    }
    await db.accounts.insert_one(new_account)
    return new_account


async def update_account_balance(account_id: str, debit: float, credit: float):
    """Update account balance based on account type and debit/credit - matches finance.py logic"""
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


async def create_journal_entry(
    company_id: str, 
    user_id: str,
    entry_date: str,
    description: str,
    lines: list,
    reference_type: str,
    reference_number: str = None,
    reference_id: str = None,
    notes: str = None,
    metadata: dict = None
):
    """
    Create a journal entry with the exact same schema as finance.py
    
    Args:
        lines: List of dicts with keys: account_id, account_code, account_name, debit, credit, description
    """
    entry_id = generate_id()
    entry_number = f"JE-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{entry_id[:4].upper()}"
    
    total_debit = sum(line["debit"] for line in lines)
    total_credit = sum(line["credit"] for line in lines)
    
    entry = {
        "id": entry_id,
        "entry_number": entry_number,
        "company_id": company_id,
        "entry_date": entry_date,
        "reference_number": reference_number,
        "description": description,
        "lines": lines,
        "total_debit": total_debit,
        "total_credit": total_credit,
        "is_balanced": round(total_debit, 2) == round(total_credit, 2),
        "is_auto_generated": True,
        "is_reversed": False,
        "reference_type": reference_type,
        "reference_id": reference_id,
        "notes": notes,
        "metadata": metadata,
        "transaction_type": reference_type,  # For quick transaction filtering
        "created_by": user_id,
        "created_at": get_current_timestamp()
    }
    await db.journal_entries.insert_one(entry)
    
    # Update account balances
    for line in lines:
        await update_account_balance(line["account_id"], line["debit"], line["credit"])
    
    return entry


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
    
    # Get parent equity account (3100 Owner's Capital or 3000 Equity)
    parent_account = await db.accounts.find_one({
        "company_id": company_id,
        "code": "3100"
    })
    if not parent_account:
        parent_account = await db.accounts.find_one({
            "company_id": company_id,
            "code": "3000"
        })
    parent_account_id = parent_account["id"] if parent_account else None
    
    # Generate unique account code for this investor in 31xx range
    existing_accounts = await db.accounts.find(
        {"company_id": company_id, "code": {"$regex": "^31"}},
        {"code": 1}
    ).to_list(100)
    
    existing_codes = [int(a["code"]) for a in existing_accounts if a["code"].isdigit() and int(a["code"]) > 3100]
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
    
    # Create investor record (share_percentage will be auto-calculated after first investment)
    investor = {
        "id": investor_id,
        "company_id": company_id,
        "name": data.name,
        "investor_type": data.investor_type,
        "email": data.email,
        "phone": data.phone,
        "id_number": data.id_number,
        "address": data.address,
        "share_percentage": 0,  # Will be auto-calculated based on capital
        "notes": data.notes,
        "account_code": str(next_code),
        "is_active": True,
        "created_at": timestamp,
        "updated_at": timestamp
    }
    await db.investors.insert_one(investor)
    
    # Create capital account for this investor (matching finance.py format exactly)
    account = {
        "id": generate_id(),
        "company_id": company_id,
        "code": str(next_code),
        "name": f"{type_label} Capital - {data.name}",
        "account_type": "equity",
        "category": "capital",
        "description": f"Capital account for {type_label.lower()} {data.name}",
        "parent_account_id": parent_account_id,
        "is_system": False,
        "is_active": True,
        "current_balance": 0.0,
        "investor_id": investor_id,
        "created_at": timestamp,
        "updated_at": timestamp
    }
    await db.accounts.insert_one(account)
    
    # Recalculate share percentages for all investors
    await recalculate_share_percentages(company_id)
    
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
        # Note: share_percentage is NOT updated here - it's auto-calculated based on capital
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
    
    # Get cash/bank account (use selected account or default)
    cash_account = await get_bank_cash_account(company_id, data.bank_account_id)
    
    entry_date = (data.date or get_current_timestamp())[:10]
    
    # Create double-entry journal entry
    # Debit: Cash/Bank (Asset increases)
    # Credit: Capital Account (Equity increases)
    lines = [
        {
            "account_id": cash_account["id"],
            "account_code": cash_account["code"],
            "account_name": cash_account["name"],
            "debit": data.amount,
            "credit": 0,
            "description": f"Capital received from {investor['name']}"
        },
        {
            "account_id": capital_account["id"],
            "account_code": capital_account["code"],
            "account_name": capital_account["name"],
            "debit": 0,
            "credit": data.amount,
            "description": f"Capital investment by {investor['name']}"
        }
    ]
    
    entry = await create_journal_entry(
        company_id=company_id,
        user_id=user_id,
        entry_date=entry_date,
        description=f"Capital Investment from {investor['name']} ({investor['investor_type'].title()})",
        lines=lines,
        reference_type="capital_investment",
        reference_number=data.reference,
        reference_id=data.investor_id,
        notes=data.notes,
        metadata={"payment_method": data.payment_method, "investor_name": investor["name"], "bank_account_id": data.bank_account_id}
    )
    
    # Update bank account balance if a specific account was selected
    if data.bank_account_id:
        await db.bank_accounts.update_one(
            {"id": data.bank_account_id},
            {"$inc": {"current_balance": data.amount}}
        )
    
    # Recalculate share percentages for all investors
    await recalculate_share_percentages(company_id)
    
    # Get updated capital balance
    updated_account = await db.accounts.find_one({"id": capital_account["id"]})
    
    # Get updated share percentage
    updated_investor = await db.investors.find_one({"id": data.investor_id})
    
    return {
        "message": f"Capital investment of LKR {data.amount:,.2f} recorded successfully",
        "journal_entry_id": entry["id"],
        "entry_number": entry["entry_number"],
        "investor": investor["name"],
        "new_capital_balance": updated_account.get("current_balance", 0),
        "new_share_percentage": updated_investor.get("share_percentage", 0)
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
    
    # Get cash/bank account (use selected account or default)
    cash_account = await get_bank_cash_account(company_id, data.bank_account_id)
    
    entry_date = (data.date or get_current_timestamp())[:10]
    
    # Debit: Capital Account (Equity decreases)
    # Credit: Cash/Bank (Asset decreases)
    lines = [
        {
            "account_id": capital_account["id"],
            "account_code": capital_account["code"],
            "account_name": capital_account["name"],
            "debit": data.amount,
            "credit": 0,
            "description": f"Capital withdrawal by {investor['name']}"
        },
        {
            "account_id": cash_account["id"],
            "account_code": cash_account["code"],
            "account_name": cash_account["name"],
            "debit": 0,
            "credit": data.amount,
            "description": f"Capital withdrawal to {investor['name']}"
        }
    ]
    
    entry = await create_journal_entry(
        company_id=company_id,
        user_id=user_id,
        entry_date=entry_date,
        description=f"Capital Withdrawal by {investor['name']} - {data.reason}",
        lines=lines,
        reference_type="capital_withdrawal",
        reference_number=data.reference,
        reference_id=data.investor_id,
        notes=data.notes,
        metadata={"payment_method": data.payment_method, "reason": data.reason, "bank_account_id": data.bank_account_id}
    )
    
    # Update bank account balance if specific account was selected
    if data.bank_account_id:
        await db.bank_accounts.update_one(
            {"id": data.bank_account_id},
            {"$inc": {"current_balance": -data.amount}}
        )
    
    # Recalculate share percentages for all investors
    await recalculate_share_percentages(company_id)
    
    return {
        "message": f"Capital withdrawal of LKR {data.amount:,.2f} recorded successfully",
        "journal_entry_id": entry["id"],
        "entry_number": entry["entry_number"]
    }

@router.post("/salary-payment")
async def record_salary_payment(
    data: SalaryPayment,
    current_user: dict = Depends(get_current_user)
):
    """Record salary payment - auto-creates journal entry"""
    company_id = current_user["company_id"]
    user_id = current_user["user_id"]
    entry_date = (data.date or get_current_timestamp())[:10]
    
    # Get or create salary expense account
    salary_account = await get_or_create_account(
        company_id, "6100", "Salaries & Wages", "expense", "operating_expense", "6000"
    )
    
    # Get cash/bank account (use selected account or default)
    cash_account = await get_bank_cash_account(company_id, data.bank_account_id)
    
    gross_salary = data.amount + (data.allowances or 0)
    net_salary = gross_salary - (data.deductions or 0)
    
    lines = [
        {
            "account_id": salary_account["id"],
            "account_code": salary_account["code"],
            "account_name": salary_account["name"],
            "debit": gross_salary,
            "credit": 0,
            "description": f"Salary expense for {data.employee_name}"
        },
        {
            "account_id": cash_account["id"],
            "account_code": cash_account["code"],
            "account_name": cash_account["name"],
            "debit": 0,
            "credit": net_salary,
            "description": f"Salary payment to {data.employee_name}"
        }
    ]
    
    # Handle deductions (if any) - credit to payable account
    if data.deductions and data.deductions > 0:
        deductions_account = await get_or_create_account(
            company_id, "2200", "Tax Payable", "liability", "current_liability", "2000"
        )
        lines.append({
            "account_id": deductions_account["id"],
            "account_code": deductions_account["code"],
            "account_name": deductions_account["name"],
            "debit": 0,
            "credit": data.deductions,
            "description": f"Deductions from {data.employee_name}'s salary"
        })
    
    # Update bank account balance if specific account was selected
    if data.bank_account_id:
        await db.bank_accounts.update_one(
            {"id": data.bank_account_id},
            {"$inc": {"current_balance": -net_salary}}
        )
    
    entry = await create_journal_entry(
        company_id=company_id,
        user_id=user_id,
        entry_date=entry_date,
        description=f"Salary Payment - {data.employee_name} ({data.month})",
        lines=lines,
        reference_type="salary_payment",
        notes=data.notes,
        metadata={
            "employee_name": data.employee_name,
            "month": data.month,
            "gross_salary": gross_salary,
            "deductions": data.deductions or 0,
            "allowances": data.allowances or 0,
            "net_salary": net_salary,
            "payment_method": data.payment_method
        }
    )
    
    return {
        "message": f"Salary payment of LKR {net_salary:,.2f} recorded for {data.employee_name}",
        "journal_entry_id": entry["id"],
        "entry_number": entry["entry_number"],
        "gross_salary": gross_salary,
        "deductions": data.deductions or 0,
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
    entry_date = (data.date or get_current_timestamp())[:10]
    
    # Map expense types to default account codes
    expense_accounts = {
        "utilities": {"code": "6300", "name": "Utilities Expense"},
        "rent": {"code": "6200", "name": "Rent Expense"},
        "office_supplies": {"code": "6500", "name": "Office Supplies"},
        "marketing": {"code": "6400", "name": "Marketing & Advertising"},
        "insurance": {"code": "6700", "name": "Insurance Expense"},
        "maintenance": {"code": "6750", "name": "Maintenance & Repairs"},
        "transport": {"code": "6800", "name": "Transport & Travel"},
        "communication": {"code": "6350", "name": "Communication Expense"},
        "professional_fees": {"code": "6450", "name": "Professional Fees"},
        "hosting": {"code": "6360", "name": "Hosting & Server Expense"},
        "domains": {"code": "6361", "name": "Domain Expense"},
        "software": {"code": "6362", "name": "Software & Subscriptions"},
        "it_services": {"code": "6363", "name": "IT Services"},
        "materials": {"code": "5150", "name": "Raw Materials"},
        "inventory": {"code": "5100", "name": "Inventory Purchases"},
        "equipment": {"code": "6850", "name": "Equipment & Tools"},
        "licenses": {"code": "6455", "name": "Licenses & Permits"},
        "bank_charges": {"code": "6380", "name": "Bank Charges"},
        "travel": {"code": "6810", "name": "Business Travel"},
        "fuel": {"code": "6820", "name": "Fuel & Vehicle"},
        "training": {"code": "6460", "name": "Training & Education"},
        "meals": {"code": "6470", "name": "Meals & Entertainment"},
        "other": {"code": "6900", "name": "Miscellaneous Expense"}
    }
    
    # If user selected a specific expense account, use that
    if data.expense_account_code:
        # Try to find existing account with this code
        existing_account = await db.accounts.find_one({
            "company_id": company_id,
            "code": data.expense_account_code
        })
        if existing_account:
            expense_info = {"code": existing_account["code"], "name": existing_account["name"]}
        else:
            # Use default mapping if account doesn't exist yet
            expense_info = expense_accounts.get(data.expense_type, expense_accounts["other"])
            expense_info["code"] = data.expense_account_code  # Override with selected code
    else:
        expense_info = expense_accounts.get(data.expense_type, expense_accounts["other"])
    
    # Get or create expense account
    expense_account = await get_or_create_account(
        company_id, expense_info["code"], expense_info["name"], "expense", "operating_expense", "6000"
    )
    
    # Get cash/bank account (use selected account or default)
    cash_account = await get_bank_cash_account(company_id, data.bank_account_id)
    
    lines = [
        {
            "account_id": expense_account["id"],
            "account_code": expense_account["code"],
            "account_name": expense_account["name"],
            "debit": data.amount,
            "credit": 0,
            "description": data.description
        },
        {
            "account_id": cash_account["id"],
            "account_code": cash_account["code"],
            "account_name": cash_account["name"],
            "debit": 0,
            "credit": data.amount,
            "description": f"Payment for {data.description}"
        }
    ]
    
    # Update bank account balance if specific account was selected
    if data.bank_account_id:
        await db.bank_accounts.update_one(
            {"id": data.bank_account_id},
            {"$inc": {"current_balance": -data.amount}}
        )
    
    entry = await create_journal_entry(
        company_id=company_id,
        user_id=user_id,
        entry_date=entry_date,
        description=f"{expense_info['name']} - {data.description}",
        lines=lines,
        reference_type="expense_payment",
        reference_number=data.reference,
        notes=data.notes,
        metadata={
            "expense_type": data.expense_type,
            "vendor": data.vendor,
            "payment_method": data.payment_method,
            "bank_account_id": data.bank_account_id
        }
    )
    
    return {
        "message": f"Expense of LKR {data.amount:,.2f} recorded for {data.description}",
        "journal_entry_id": entry["id"],
        "entry_number": entry["entry_number"],
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
    entry_date = (data.date or get_current_timestamp())[:10]
    
    # Map revenue types to account codes
    revenue_accounts = {
        "sales": {"code": "4100", "name": "Sales Revenue"},
        "service": {"code": "4200", "name": "Service Revenue"},
        "interest": {"code": "4300", "name": "Interest Income"},
        "commission": {"code": "4400", "name": "Commission Income"},
        "other": {"code": "4900", "name": "Other Income"}
    }
    
    revenue_info = revenue_accounts.get(data.revenue_type, revenue_accounts["other"])
    
    # Get or create revenue account
    revenue_account = await get_or_create_account(
        company_id, revenue_info["code"], revenue_info["name"], "income", "revenue", "4000"
    )
    
    # Get cash/bank account (use selected account or default)
    cash_account = await get_bank_cash_account(company_id, data.bank_account_id)
    
    lines = [
        {
            "account_id": cash_account["id"],
            "account_code": cash_account["code"],
            "account_name": cash_account["name"],
            "debit": data.amount,
            "credit": 0,
            "description": f"Revenue received for {data.description}"
        },
        {
            "account_id": revenue_account["id"],
            "account_code": revenue_account["code"],
            "account_name": revenue_account["name"],
            "debit": 0,
            "credit": data.amount,
            "description": data.description
        }
    ]
    
    # Update bank account balance if specific account was selected
    if data.bank_account_id:
        await db.bank_accounts.update_one(
            {"id": data.bank_account_id},
            {"$inc": {"current_balance": data.amount}}
        )
    
    entry = await create_journal_entry(
        company_id=company_id,
        user_id=user_id,
        entry_date=entry_date,
        description=f"{revenue_info['name']} - {data.description}",
        lines=lines,
        reference_type="revenue_receipt",
        reference_number=data.reference,
        notes=data.notes,
        metadata={
            "revenue_type": data.revenue_type,
            "customer": data.customer,
            "payment_method": data.payment_method,
            "bank_account_id": data.bank_account_id
        }
    )
    
    return {
        "message": f"Revenue of LKR {data.amount:,.2f} recorded for {data.description}",
        "journal_entry_id": entry["id"],
        "entry_number": entry["entry_number"]
    }

@router.post("/loan-transaction")
async def record_loan_transaction(
    data: LoanTransaction,
    current_user: dict = Depends(get_current_user)
):
    """Record loan received or repayment - auto-creates journal entry"""
    company_id = current_user["company_id"]
    user_id = current_user["user_id"]
    entry_date = (data.date or get_current_timestamp())[:10]
    
    # Map loan types to account codes
    loan_accounts = {
        "bank_loan": {"code": "2300", "name": "Loans Payable"},
        "director_loan": {"code": "2350", "name": "Director Loans Payable"},
        "finance_company": {"code": "2360", "name": "Finance Company Loans"},
        "other": {"code": "2390", "name": "Other Loans Payable"}
    }
    
    loan_info = loan_accounts.get(data.loan_type, loan_accounts["other"])
    
    # Get or create loan account
    loan_account = await get_or_create_account(
        company_id, loan_info["code"], loan_info["name"], "liability", "long_term_liability", "2000"
    )
    
    # Get cash/bank account (use selected account or default)
    cash_account = await get_bank_cash_account(company_id, data.bank_account_id)
    
    lines = []
    
    if data.transaction_type == "receive":
        # Loan Received
        # Debit: Cash/Bank
        # Credit: Loan Account
        lines = [
            {
                "account_id": cash_account["id"],
                "account_code": cash_account["code"],
                "account_name": cash_account["name"],
                "debit": data.amount,
                "credit": 0,
                "description": f"Loan received from {data.lender_name}"
            },
            {
                "account_id": loan_account["id"],
                "account_code": loan_account["code"],
                "account_name": loan_account["name"],
                "debit": 0,
                "credit": data.amount,
                "description": f"Loan from {data.lender_name}"
            }
        ]
        ref_type = "loan_received"
        description = f"Loan Received from {data.lender_name}"
        
        # Update bank account balance
        if data.bank_account_id:
            await db.bank_accounts.update_one(
                {"id": data.bank_account_id},
                {"$inc": {"current_balance": data.amount}}
            )
        
    else:
        # Loan Repayment
        total_payment = data.amount + (data.interest_amount or 0)
        
        lines = [
            {
                "account_id": loan_account["id"],
                "account_code": loan_account["code"],
                "account_name": loan_account["name"],
                "debit": data.amount,
                "credit": 0,
                "description": f"Principal repayment to {data.lender_name}"
            }
        ]
        
        # Add interest expense if applicable
        if data.interest_amount and data.interest_amount > 0:
            interest_account = await get_or_create_account(
                company_id, "6250", "Interest Expense", "expense", "operating_expense", "6000"
            )
            lines.append({
                "account_id": interest_account["id"],
                "account_code": interest_account["code"],
                "account_name": interest_account["name"],
                "debit": data.interest_amount,
                "credit": 0,
                "description": f"Interest expense to {data.lender_name}"
            })
        
        lines.append({
            "account_id": cash_account["id"],
            "account_code": cash_account["code"],
            "account_name": cash_account["name"],
            "debit": 0,
            "credit": total_payment,
            "description": f"Loan repayment to {data.lender_name}"
        })
        
        ref_type = "loan_repayment"
        description = f"Loan Repayment to {data.lender_name}"
        
        # Update bank account balance
        if data.bank_account_id:
            await db.bank_accounts.update_one(
                {"id": data.bank_account_id},
                {"$inc": {"current_balance": -total_payment}}
            )
    
    entry = await create_journal_entry(
        company_id=company_id,
        user_id=user_id,
        entry_date=entry_date,
        description=description,
        lines=lines,
        reference_type=ref_type,
        reference_number=data.reference,
        notes=data.notes,
        metadata={
            "lender_name": data.lender_name,
            "loan_type": data.loan_type,
            "principal": data.amount,
            "interest": data.interest_amount or 0,
            "bank_account_id": data.bank_account_id
        }
    )
    
    action = "received" if data.transaction_type == "receive" else "repaid"
    return {
        "message": f"Loan of LKR {data.amount:,.2f} {action} successfully",
        "journal_entry_id": entry["id"],
        "entry_number": entry["entry_number"]
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
            {"type": "utilities", "label": "Utilities (Electricity, Water)", "account": "6300"},
            {"type": "rent", "label": "Rent Payment", "account": "6200"},
            {"type": "office_supplies", "label": "Office Supplies", "account": "6500"},
            {"type": "marketing", "label": "Marketing & Advertising", "account": "6400"},
            {"type": "insurance", "label": "Insurance", "account": "6600"},
            {"type": "maintenance", "label": "Repairs & Maintenance", "account": "6700"},
            {"type": "transport", "label": "Transport & Travel", "account": "6800"},
            {"type": "communication", "label": "Phone & Internet", "account": "6350"},
            {"type": "professional_fees", "label": "Professional Fees", "account": "6450"},
            {"type": "other", "label": "Other Expenses", "account": "6900"}
        ],
        "revenue": [
            {"type": "sales", "label": "Sales Revenue", "account": "4100"},
            {"type": "service", "label": "Service Income", "account": "4200"},
            {"type": "interest", "label": "Interest Income", "account": "4300"},
            {"type": "commission", "label": "Commission Income", "account": "4400"},
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

@router.get("/expense-accounts")
async def get_expense_accounts(current_user: dict = Depends(get_current_user)):
    """Get available expense account categories for expense recording"""
    company_id = current_user["company_id"]
    
    # Get all expense accounts from the Chart of Accounts
    expense_accounts = await db.accounts.find(
        {
            "company_id": company_id,
            "account_type": "expense",
            "is_active": {"$ne": False}
        },
        {"_id": 0, "id": 1, "code": 1, "name": 1, "category": 1, "current_balance": 1}
    ).sort("code", 1).to_list(100)
    
    # If no expense accounts exist, return default categories
    if not expense_accounts:
        return {
            "accounts": [],
            "default_categories": [
                {"code": "6100", "name": "Salaries & Wages", "category": "Payroll"},
                {"code": "6200", "name": "Rent Expense", "category": "Operating"},
                {"code": "6300", "name": "Utilities Expense", "category": "Operating"},
                {"code": "6400", "name": "Marketing & Advertising", "category": "Operating"},
                {"code": "6500", "name": "Office Supplies", "category": "Operating"},
                {"code": "6600", "name": "Depreciation Expense", "category": "Operating"},
                {"code": "6700", "name": "Insurance Expense", "category": "Operating"},
                {"code": "6800", "name": "Professional Fees", "category": "Operating"},
                {"code": "6900", "name": "Miscellaneous Expense", "category": "Other"},
                {"code": "5100", "name": "Cost of Goods Sold", "category": "COGS"},
            ]
        }
    
    return {
        "accounts": expense_accounts,
        "default_categories": []
    }

@router.get("/recent-transactions")
async def get_recent_transactions(
    limit: int = 20,
    current_user: dict = Depends(get_current_user)
):
    """Get recent quick transactions (excluding reversed)"""
    transactions = await db.journal_entries.find(
        {
            "company_id": current_user["company_id"],
            "is_auto_generated": True,
            "transaction_type": {"$exists": True},
            "is_reversed": {"$ne": True}  # Exclude reversed transactions
        },
        {"_id": 0}
    ).sort("created_at", -1).to_list(limit)
    
    return transactions


@router.get("/all-transactions")
async def get_all_transactions(
    page: int = 1,
    per_page: int = 20,
    transaction_type: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Get ALL transactions with pagination including:
    - Quick transactions (expenses, salary, revenue, loans, capital)
    - PO payments
    - GRN return refunds
    - Additional charges
    - Sales payments
    """
    company_id = current_user["company_id"]
    all_transactions = []
    
    # 1. Get Quick Transactions (journal entries with transaction_type)
    quick_txn_query = {
        "company_id": company_id,
        "is_auto_generated": True,
        "transaction_type": {"$exists": True},
        "is_reversed": {"$ne": True}
    }
    quick_transactions = await db.journal_entries.find(
        quick_txn_query, {"_id": 0}
    ).sort("created_at", -1).to_list(1000)
    
    for tx in quick_transactions:
        all_transactions.append({
            "id": tx["id"],
            "date": tx.get("entry_date") or tx.get("date") or tx["created_at"],
            "description": tx.get("description", ""),
            "amount": tx.get("total_debit", 0),
            "transaction_type": tx.get("transaction_type", "other"),
            "category": "quick_transaction",
            "reference": tx.get("entry_number", ""),
            "source": "Quick Transaction",
            "created_at": tx["created_at"]
        })
    
    # 2. Get PO Payments
    payments = await db.payments.find(
        {"company_id": company_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(1000)
    
    for p in payments:
        ref_type = p.get("reference_type", "")
        all_transactions.append({
            "id": p["id"],
            "date": p.get("payment_date") or p["created_at"],
            "description": f"Payment for {ref_type.replace('_', ' ').title()} - {p.get('notes', '')}",
            "amount": p.get("amount", 0),
            "transaction_type": "po_payment" if ref_type == "purchase_order" else "so_payment",
            "category": "payment",
            "reference": p.get("reference_id", ""),
            "source": f"{ref_type.replace('_', ' ').title()} Payment",
            "created_at": p["created_at"]
        })
    
    # 3. Get GRN Return Transactions (from journal entries with GRNRET prefix)
    grn_returns = await db.journal_entries.find(
        {
            "company_id": company_id,
            "entry_number": {"$regex": "^GRNRET-"},
            "is_reversed": {"$ne": True}
        },
        {"_id": 0}
    ).sort("created_at", -1).to_list(500)
    
    for gr in grn_returns:
        all_transactions.append({
            "id": gr["id"],
            "date": gr.get("date") or gr["created_at"],
            "description": gr.get("description", "GRN Return"),
            "amount": gr.get("total_debit", 0),
            "transaction_type": "grn_return",
            "category": "grn_return",
            "reference": gr.get("entry_number", ""),
            "source": "GRN Return",
            "created_at": gr["created_at"]
        })
    
    # 4. Get Additional Charges (from journal entries with CHG prefix)
    charges = await db.journal_entries.find(
        {
            "company_id": company_id,
            "entry_number": {"$regex": "^CHG-"},
            "is_reversed": {"$ne": True}
        },
        {"_id": 0}
    ).sort("created_at", -1).to_list(500)
    
    for ch in charges:
        all_transactions.append({
            "id": ch["id"],
            "date": ch.get("date") or ch["created_at"],
            "description": ch.get("description", "Additional Charge"),
            "amount": ch.get("total_debit", 0),
            "transaction_type": "additional_charge",
            "category": "charge",
            "reference": ch.get("entry_number", ""),
            "source": "Additional Charge",
            "created_at": ch["created_at"]
        })
    
    # 5. Get Discount entries (from journal entries with DISC prefix)
    discounts = await db.journal_entries.find(
        {
            "company_id": company_id,
            "entry_number": {"$regex": "^DISC-"},
            "is_reversed": {"$ne": True}
        },
        {"_id": 0}
    ).sort("created_at", -1).to_list(500)
    
    for d in discounts:
        all_transactions.append({
            "id": d["id"],
            "date": d.get("date") or d["created_at"],
            "description": d.get("description", "Discount Received"),
            "amount": d.get("total_debit", 0),
            "transaction_type": "discount_received",
            "category": "income",
            "reference": d.get("entry_number", ""),
            "source": "Discount",
            "created_at": d["created_at"]
        })
    
    # 6. Get Sales Order Payments (from journal entries with REC prefix)
    sales_payments = await db.journal_entries.find(
        {
            "company_id": company_id,
            "entry_number": {"$regex": "^REC-"},
            "is_reversed": {"$ne": True}
        },
        {"_id": 0}
    ).sort("created_at", -1).to_list(500)
    
    for sp in sales_payments:
        all_transactions.append({
            "id": sp["id"],
            "date": sp.get("date") or sp["created_at"],
            "description": sp.get("description", "Sales Payment Received"),
            "amount": sp.get("total_debit", 0),
            "transaction_type": "sales_payment",
            "category": "income",
            "reference": sp.get("entry_number", ""),
            "source": "Sales Payment",
            "created_at": sp["created_at"]
        })
    
    # Remove duplicates based on id
    seen_ids = set()
    unique_transactions = []
    for tx in all_transactions:
        if tx["id"] not in seen_ids:
            seen_ids.add(tx["id"])
            unique_transactions.append(tx)
    
    # Sort by date descending
    unique_transactions.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    
    # Filter by transaction type if specified
    if transaction_type and transaction_type != "all":
        unique_transactions = [tx for tx in unique_transactions if tx["transaction_type"] == transaction_type]
    
    # Calculate pagination
    total = len(unique_transactions)
    total_pages = (total + per_page - 1) // per_page
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    
    paginated_transactions = unique_transactions[start_idx:end_idx]
    
    return {
        "transactions": paginated_transactions,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    }


@router.delete("/transaction/{transaction_id}")
async def delete_transaction(
    transaction_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a quick transaction and reverse its journal entry (Admin only).
    This will reverse all account balance changes made by the transaction.
    """
    # Check if user is admin
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=403, 
            detail="Only administrators can delete transactions"
        )
    
    company_id = current_user["company_id"]
    
    # Find the journal entry
    entry = await db.journal_entries.find_one({
        "id": transaction_id,
        "company_id": company_id,
        "is_auto_generated": True
    })
    
    if not entry:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    if entry.get("is_reversed"):
        raise HTTPException(status_code=400, detail="Transaction has already been reversed")
    
    # Reverse the account balances
    for line in entry.get("lines", []):
        account_id = line.get("account_id")
        if account_id:
            # Reverse: if original was debit, we credit; if original was credit, we debit
            await update_account_balance(
                account_id, 
                line.get("credit", 0),  # Reverse: original debit becomes credit
                line.get("debit", 0)    # Reverse: original credit becomes debit
            )
    
    # If this was a capital investment/withdrawal, recalculate share percentages
    if entry.get("transaction_type") in ["capital_investment", "capital_withdrawal"]:
        await recalculate_share_percentages(company_id)
    
    # Mark the entry as reversed instead of deleting (for audit trail)
    await db.journal_entries.update_one(
        {"id": transaction_id},
        {
            "$set": {
                "is_reversed": True,
                "reversed_at": get_current_timestamp(),
                "reversed_by": current_user["user_id"]
            }
        }
    )
    
    return {
        "message": "Transaction reversed successfully",
        "entry_number": entry.get("entry_number"),
        "amount_reversed": entry.get("total_debit", 0)
    }
