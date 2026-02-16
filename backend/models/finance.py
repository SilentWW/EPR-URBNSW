"""
Finance module models - Chart of Accounts, Journal Entries, Double-Entry Accounting
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum

# Account Types for Chart of Accounts
class AccountType(str, Enum):
    ASSET = "asset"
    LIABILITY = "liability"
    EQUITY = "equity"
    INCOME = "income"
    EXPENSE = "expense"

# Account Category (sub-classification)
class AccountCategory(str, Enum):
    # Assets
    CURRENT_ASSET = "current_asset"
    FIXED_ASSET = "fixed_asset"
    BANK = "bank"
    CASH = "cash"
    ACCOUNTS_RECEIVABLE = "accounts_receivable"
    INVENTORY = "inventory"
    # Liabilities
    CURRENT_LIABILITY = "current_liability"
    LONG_TERM_LIABILITY = "long_term_liability"
    ACCOUNTS_PAYABLE = "accounts_payable"
    # Equity
    CAPITAL = "capital"
    RETAINED_EARNINGS = "retained_earnings"
    # Income
    REVENUE = "revenue"
    OTHER_INCOME = "other_income"
    # Expenses
    COST_OF_GOODS_SOLD = "cost_of_goods_sold"
    OPERATING_EXPENSE = "operating_expense"
    TAX_EXPENSE = "tax_expense"

# Chart of Accounts Models
class AccountCreate(BaseModel):
    code: Optional[str] = Field(None, description="Account code (auto-generated if not provided)")
    name: str = Field(..., description="Account name")
    account_type: AccountType
    category: AccountCategory
    description: Optional[str] = None
    parent_account_id: Optional[str] = None
    is_system: bool = False  # System accounts can't be deleted
    opening_balance: float = 0.0

class AccountUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class AccountResponse(BaseModel):
    id: str
    code: str
    name: str
    account_type: str
    category: str
    description: Optional[str]
    parent_account_id: Optional[str]
    is_system: bool
    is_active: bool
    current_balance: float
    created_at: str

# Journal Entry Models (Double-Entry)
class JournalLineItem(BaseModel):
    account_id: str
    account_code: Optional[str] = None
    account_name: Optional[str] = None
    debit: float = 0.0
    credit: float = 0.0
    description: Optional[str] = None

class JournalEntryCreate(BaseModel):
    entry_date: str
    reference_number: Optional[str] = None
    description: str
    lines: List[JournalLineItem]
    reference_type: Optional[str] = None  # sales_order, purchase_order, payment, manual
    reference_id: Optional[str] = None
    is_auto_generated: bool = False

class JournalEntryResponse(BaseModel):
    id: str
    entry_number: str
    entry_date: str
    reference_number: Optional[str]
    description: str
    lines: List[dict]
    total_debit: float
    total_credit: float
    is_balanced: bool
    is_auto_generated: bool
    is_reversed: bool
    created_by: str
    created_at: str

# Tax Management Models
class TaxRateCreate(BaseModel):
    name: str
    code: str
    rate: float  # Percentage (e.g., 15.0 for 15%)
    tax_type: str  # VAT, GST, Sales Tax, etc.
    is_inclusive: bool = False
    expense_account_id: Optional[str] = None
    liability_account_id: Optional[str] = None
    description: Optional[str] = None

class TaxRateUpdate(BaseModel):
    name: Optional[str] = None
    rate: Optional[float] = None
    is_active: Optional[bool] = None
    description: Optional[str] = None

# Financial Period Models
class FinancialPeriodCreate(BaseModel):
    name: str
    start_date: str
    end_date: str
    is_closed: bool = False

# AR/AP Aging Models
class AgingBucket(BaseModel):
    current: float = 0.0
    days_1_30: float = 0.0
    days_31_60: float = 0.0
    days_61_90: float = 0.0
    days_over_90: float = 0.0
    total: float = 0.0
