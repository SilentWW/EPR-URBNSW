# E1 ERP System - Product Requirements Document

## Overview
A cloud-based, web ERP system designed for businesses with a modular architecture. Built with FastAPI backend and React frontend, featuring advanced finance and admin capabilities.

## Original Problem Statement
Build a cloud-based ERP system for business operations with the intention of selling as a SaaS product. System must be low-code/no-code, configurable, and user-friendly for non-technical users.

## User Personas
1. **Business Owner** - Needs overview of operations, financial reports, WooCommerce integration
2. **Accountant** - Needs Chart of Accounts, General Ledger, journal entries, financial reports
3. **Operations Manager** - Needs inventory, sales, purchase orders
4. **System Admin** - Needs backup/restore, data reset, user management

## Core Requirements

### Phase 1 - MVP (COMPLETED ✅)
- [x] User/Role/Company Management with JWT Authentication
- [x] Products & Inventory Management
- [x] Sales Orders & Invoicing
- [x] Customer Management (CRM)
- [x] Supplier/Purchasing Management
- [x] Basic Accounting (entries, receivables, payables)
- [x] Payments Tracking
- [x] Dashboard & Basic Reports
- [x] Notifications
- [x] WooCommerce Settings UI

### Phase 2 - Advanced Finance & Admin (COMPLETED ✅)
- [x] **Chart of Accounts** - 28 default accounts, configurable hierarchy
- [x] **Double-Entry Bookkeeping** - Validated journal entries
- [x] **General Ledger** - Transaction history with running balances
- [x] **Accounts Receivable** - Aging analysis
- [x] **Accounts Payable** - Aging analysis
- [x] **Financial Reports**:
  - [x] Trial Balance
  - [x] Profit & Loss Statement
  - [x] Balance Sheet
  - [x] Cash Flow Statement
- [x] **System Admin Controls**:
  - [x] Data Reset (transactional/full with confirmation)
  - [x] Backup (local storage, compressed)
  - [x] Restore (with preview and confirmation)
  - [x] System Information Dashboard
- [x] **WooCommerce Integration Backend** - Two-way sync logic
- [x] **WooCommerce Manual Sync UI** - Sync All, Products, Orders, Customers buttons
- [x] **WooCommerce Auto Sync** - Automatic hourly sync with background scheduler

### Phase 3 - GRN & Enhanced Products (COMPLETED ✅)
- [x] **GRN (Goods Received Note)** - Full inventory receipt workflow
  - [x] Auto-generate SKU (URBN0001, URBN0002...)
  - [x] Cost Price (COGS), Regular Price, Sale Price fields
  - [x] Product Description & Short Description
  - [x] Visibility (Public/Private)
  - [x] Tags (comma separated) with **SEO Tag Suggestions**
  - [x] Weight (kg)
  - [x] Stock Management enabled by default
  - [x] **Automatic Finance Entries** - Debit Inventory, Credit Accounts Payable
  - [x] **WooCommerce Sync** - Auto-sync products with stock management enabled
  - [x] **Link PO to GRN** - Create GRN from existing Purchase Order
  - [x] **SKU Field Logic** - SKU disabled when selecting existing product
  - [x] **WooCommerce Category Dropdown** - Select categories from WooCommerce
  - [x] **SEO Tags Button** - Generate SEO-friendly tags automatically

### Phase 4 - WooCommerce Order Sync with Finance (COMPLETED ✅)
- [x] **Order Sync from WooCommerce**
  - [x] Sync completed/processing orders as income
  - [x] **Double-entry accounting** for sales:
    - Debit: Accounts Receivable/Cash
    - Credit: Sales Revenue
  - [x] **COGS tracking**:
    - Debit: Cost of Goods Sold
    - Credit: Inventory
  - [x] **Returns/Cancellations handling**:
    - Reverse journal entries
    - Restore inventory
  - [x] Automatic customer creation from WooCommerce orders

### Simplified Product Creation (COMPLETED ✅)
- [x] **Product form simplified** - Only SKU, Name, Category
- [x] Cost price, selling price, stock quantity set via GRN
- [x] WooCommerce category dropdown in product form

### Bug Fixes (Session - Jan 2026)
- [x] **Supplier Creation Bug** - Fixed React crash "Objects are not valid as a React child" when Pydantic validation errors occurred. Error handling now properly extracts error messages from array/object format.

### Phase 5 - Simple Finance & Investor Management (COMPLETED ✅) - Feb 2026
- [x] **Investor Management Module** (`/investors`)
  - [x] Add directors, shareholders, partners
  - [x] Auto-create capital accounts under Equity (31xx series)
  - [x] Track share percentages
  - [x] Record capital investments with automatic journal entries
  - [x] Record capital withdrawals
  - [x] **Auto-calculate share percentages** - Automatically recalculates all investor shares when investment is made
- [x] **Quick Transactions Module** (`/quick-transactions`)
  - [x] Pay Expense - auto-creates journal entry (Debit Expense, Credit Cash)
  - [x] Pay Salary - handles allowances/deductions (Debit Salaries, Credit Cash/Tax)
  - [x] Receive Revenue - auto-creates journal entry (Debit Cash, Credit Revenue)
  - [x] Loan Transactions - receive and repay loans from banks/financial companies
  - [x] **Date Picker** - All quick transactions now support date selection
  - [x] **Admin-only Delete** - Admin users can delete/reverse transactions
- [x] **Financial Data Integrity Fix** (Feb 16, 2026)
  - [x] Refactored `simple_finance.py` to use same schema as `finance.py`
  - [x] Journal entries now use `lines` array with `account_id` (not `entries`)
  - [x] Proper balance updates based on account type
  - [x] All transactions correctly appear in Chart of Accounts
  - [x] Financial Reports (Trial Balance, P&L, Balance Sheet) now accurate

### Phase 6 - Auto-generate Account Codes & Dynamic Business Name (COMPLETED ✅) - Feb 2026
- [x] **Auto-generate Account Codes**
  - [x] New endpoint: `GET /api/finance/chart-of-accounts/next-code/{account_type}`
  - [x] Account codes auto-generated based on type prefix:
    - Asset: 1xxx (e.g., 1501, 1502...)
    - Liability: 2xxx
    - Equity: 3xxx
    - Income: 4xxx
    - Expense: 6xxx (e.g., 6901, 6902...)
  - [x] Sequential code generation within each type
  - [x] Account code input is read-only in Add Account modal
  - [x] Code dynamically updates when account type changes
- [x] **Dynamic Business Name**
  - [x] `/api/auth/me` now returns `company_name` field
  - [x] Sidebar displays user's company name instead of static "E1 ERP"
  - [x] Company name truncated with ellipsis if too long

### Phase 7 - Bank & Cash Account Integration (COMPLETED ✅) - Feb 2026
- [x] **Bank & Cash Account Management Module** (`/bank-accounts`)
  - [x] Create multiple bank accounts and cash accounts
  - [x] Each account auto-creates a linked Chart of Accounts entry (Asset)
  - [x] Track opening balance and current balance
  - [x] Support deposits, withdrawals, and inter-account transfers
  - [x] All transactions create proper double-entry journal entries
- [x] **Bank Account Selection in All Transaction Forms**
  - [x] Investors - Add Investment modal: "Deposit To Account" selector
  - [x] Investors - Withdrawal modal: "Pay From Account" selector
  - [x] Quick Transactions - Pay Expense: "Pay From Account" selector
  - [x] Quick Transactions - Pay Salary: "Pay From Account" selector
  - [x] Quick Transactions - Receive Payment: "Deposit To Account" selector
  - [x] Quick Transactions - Loan Transaction: bank account selector
  - [x] Purchase Orders - Record Payment: "Pay From Account" selector
- [x] **Backend Support**
  - [x] `PaymentCreate` model updated with `bank_account_id` field
  - [x] `create_payment` function uses selected bank account for journal entries
  - [x] All `simple_finance.py` endpoints accept `bank_account_id`
  - [x] Bank account balance automatically updated on transactions

## Technical Architecture

### Backend
- **Framework**: FastAPI
- **Database**: MongoDB
- **Authentication**: JWT
- **Structure**: Modular routers
  - `/app/backend/server.py` - Main application with existing routes
  - `/app/backend/routes/finance.py` - Finance module (Chart of Accounts, GL, Reports)
  - `/app/backend/routes/admin.py` - Admin module (Backup, Restore, Reset)
  - `/app/backend/routes/woocommerce.py` - WooCommerce integration

### Frontend
- **Framework**: React
- **UI Components**: Shadcn/UI
- **Routing**: React Router
- **State**: Context API
- **Styling**: Tailwind CSS

### Key Configuration
- **Currency**: LKR (Sri Lankan Rupee)
- **Timezone**: Asia/Colombo
- **Financial Year**: April 1 - March 31
- **Backup Storage**: Local (/app/backend/backups)

## API Endpoints

### Finance Module (/api/finance)
- `POST /chart-of-accounts/initialize` - Initialize default accounts
- `GET /chart-of-accounts` - List all accounts
- `GET /chart-of-accounts/next-code/{account_type}` - **NEW** Get next auto-generated account code
- `POST /chart-of-accounts` - Create account (code auto-generated if not provided)
- `PUT /chart-of-accounts/{id}` - Update account
- `DELETE /chart-of-accounts/{id}` - Delete account
- `GET /journal-entries` - List journal entries
- `POST /journal-entries` - Create journal entry
- `POST /journal-entries/{id}/reverse` - Reverse entry
- `GET /general-ledger` - Get general ledger
- `GET /reports/trial-balance` - Trial balance report
- `GET /reports/profit-loss` - P&L report
- `GET /reports/balance-sheet` - Balance sheet report
- `GET /reports/cash-flow` - Cash flow report

### Bank Accounts Module (/api/bank-accounts)
- `GET /` - List all bank/cash accounts
- `GET /{id}` - Get bank account details
- `POST /` - Create bank/cash account (auto-creates Chart of Accounts entry)
- `PUT /{id}` - Update bank account
- `DELETE /{id}` - Delete bank account
- `POST /deposit` - Record deposit into account
- `POST /withdraw` - Record withdrawal from account
- `POST /transfer` - Record transfer between accounts

### Simple Finance Module (/api/simple-finance)
- `GET /investors` - List all investors with capital balances
- `POST /investors` - Create investor with auto-generated capital account
- `PUT /investors/{id}` - Update investor details
- `DELETE /investors/{id}` - Delete investor (if balance is zero)
- `POST /capital-investment` - Record capital investment
- `POST /capital-withdrawal` - Record capital withdrawal
- `POST /salary-payment` - Record salary payment
- `POST /expense-payment` - Record expense payment
- `POST /revenue-receipt` - Record revenue receipt
- `POST /loan-transaction` - Record loan received or repayment
- `GET /transaction-types` - Get available transaction types
- `GET /recent-transactions` - Get recent quick transactions

### Admin Module (/api/admin)
- `GET /system-info` - System statistics
- `GET /backups` - List backups
- `POST /backups` - Create backup
- `GET /backups/{id}/download` - Download backup
- `DELETE /backups/{id}` - Delete backup
- `GET /data-reset/preview` - Preview reset impact
- `POST /data-reset` - Execute data reset
- `GET /restore/preview/{id}` - Preview restore
- `POST /restore` - Execute restore

### GRN Module (/api/grn)
- `GET /next-sku` - Get next available SKU (URBN0001...)
- `GET /report/summary` - GRN summary report
- `GET /` - List all GRNs
- `GET /{id}` - Get GRN details
- `POST /` - Create GRN (auto-creates products, inventory, finance entries, supports po_id to link PO)
- `POST /{id}/resync` - Re-sync GRN products to WooCommerce
- `DELETE /{id}` - Delete GRN

### WooCommerce Module (/api/woocommerce)
- `GET /test-connection` - Test WooCommerce connection
- `POST /products/sync` - Sync products
- `POST /orders/sync` - Sync orders
- `POST /customers/sync` - Sync customers
- `POST /full-sync` - Full two-way sync
- `GET /sync-logs` - Get sync history
- `GET /sync-status` - Get auto-sync status and next run time
- `POST /trigger-auto-sync` - Manually trigger auto-sync cycle

### Phase 8 - COGS Recognition on Sales (COMPLETED ✅) - Feb 2026
- [x] **Automatic COGS Journal Entries on Sale**
  - [x] When Sales Order created, system now creates TWO journal entries:
    - Revenue Entry: Debit Accounts Receivable (1300), Credit Sales Revenue (4100)
    - COGS Entry: Debit Cost of Goods Sold (5100), Credit Inventory (1400)
  - [x] COGS calculated from product `cost_price * quantity`
  - [x] Entry numbers use SALE- and COGS- prefixes
- [x] **COGS Reversal on Sales Return**
  - [x] When Sales Order returned, system reverses both entries:
    - Revenue Reversal (RET-): Debit Revenue, Credit AR
    - COGS Reversal (RCOGS-): Debit Inventory, Credit COGS
  - [x] Inventory balance restored on return
- [x] **Account Balance Updates**
  - [x] All account balances automatically updated with journal entries
  - [x] Proper double-entry accounting maintained

### Phase 9 - Sales Order Payment Integration (COMPLETED ✅) - Feb 2026
- [x] **Record Payment Modal Enhancement**
  - [x] Changed "Payment Method" dropdown to "Payment Received To"
  - [x] Dropdown lists all available bank and cash accounts
  - [x] Shows account name, type (Cash/Bank name), and current balance
- [x] **Payment Recording with Bank Account Integration**
  - [x] When payment recorded, selected bank account balance increases
  - [x] Proper journal entries created (Debit Cash/Bank, Credit AR)
  - [x] Sales order status updates to "paid" when fully paid
- [x] **Auto-create Missing Accounts**
  - [x] If required Chart of Accounts entries missing (AR 1300, Cash 1100), system auto-creates them
  - [x] Prevents silent failures in payment processing

### Packaging Items Management (COMPLETED ✅) - Feb 2026
- [x] **Packaging Items Module** (`/packaging-items`)
  - [x] Designate products as packaging items (bags, tags, cards)
  - [x] On sale: Automatically reduce packaging inventory (1 set per product sold)
  - [x] On sale: Add packaging cost to COGS journal entry
  - [x] Backend API: `/api/packaging-items` (GET, POST, DELETE)

### Phase 10 - Two-Way WooCommerce Product Sync (COMPLETED ✅) - Feb 2026
- [x] **ERP to WooCommerce Product Sync**
  - [x] When editing a product in ERP that is linked to WooCommerce, changes are automatically pushed to WooCommerce
  - [x] Categories updated in ERP are synced to WooCommerce in real-time
  - [x] Syncs: name, SKU, description, prices, stock, categories, tags, visibility
- [x] **Backend Implementation**
  - [x] New helper function `sync_product_to_woocommerce()` in `server.py`
  - [x] Uses WooCommerce REST API `PUT /products/{id}` endpoint
  - [x] Converts ERP category IDs to WooCommerce category IDs
  - [x] Non-blocking: sync failures logged but don't fail the product update
- [x] **Frontend Enhancement**
  - [x] Success toast shows "Product updated & synced to WooCommerce" for linked products
  - [x] Multi-category support with checkbox selection

### Phase 11 - Purchase Order Edit & Delete (COMPLETED ✅) - Feb 2026
- [x] **Role-Based Access Control**
  - [x] Only **admin** and **manager** roles can edit or delete purchase orders
  - [x] Other roles can still view, receive, and record payments
- [x] **Edit Purchase Order**
  - [x] Can modify supplier, items, quantities, prices, and notes
  - [x] Cannot edit received orders (inventory already affected)
  - [x] Totals automatically recalculated when items change
- [x] **Delete Purchase Order**
  - [x] Only pending orders without payments can be deleted
  - [x] Received orders cannot be deleted
  - [x] Orders with recorded payments cannot be deleted
- [x] **Backend Implementation**
  - [x] Updated `PurchaseOrderUpdate` model to include `supplier_id` and `items`
  - [x] `PUT /api/purchase-orders/{id}` - Full edit with role check
  - [x] `DELETE /api/purchase-orders/{id}` - Delete with role check
- [x] **Frontend Implementation**
  - [x] Edit dialog with supplier selector, item management, notes
  - [x] Delete confirmation dialog with warning message
  - [x] Edit/Delete options only visible to admin/manager roles in dropdown menu

### Phase 12 - GRN Additional Charges (COMPLETED ✅) - Feb 2026
- [x] **Additional Charge Types Supported**
  - [x] Shipping Charges → Operating Expenses (6000)
  - [x] Courier Fees → Operating Expenses (6000)
  - [x] Customs/Import Duties → Operating Expenses (6000)
  - [x] Handling Fees → Operating Expenses (6000)
  - [x] Other Charges → Operating Expenses (6000)
  - [x] Discount Received → Other Income (4900) - reduces total payable
- [x] **Payment Options**
  - [x] Add to Accounts Payable (pay later with PO payment)
  - [x] Pay immediately from bank/cash account
  - [x] Account dropdown shows ALL cash/bank accounts (from both Bank Accounts and Chart of Accounts)
- [x] **Available in Both PO and GRN Pages**
  - [x] Purchase Orders page: "Add Charges" in dropdown menu
  - [x] GRN page: "Add Charges" button in expanded GRN view (for GRNs linked to PO)
  - [x] Shows existing charges with running totals
- [x] **Journal Entries Created**
  - [x] Expenses: Debit Operating Expenses, Credit AP (or Bank if paid immediately)
  - [x] Discounts: Debit AP (reduce payable), Credit Other Income
- [x] **Backend Implementation**
  - [x] `AdditionalCharge` Pydantic model
  - [x] `POST /api/purchase-orders/{id}/additional-charges` endpoint
  - [x] `GET /api/grn/charge-types` endpoint
  - [x] `process_additional_charges()` helper function
- [x] **Frontend Implementation**
  - [x] "Add Charges" option in PO dropdown menu
  - [x] "Add Charges" button in GRN expanded view
  - [x] Additional Charges dialog with charge type, amount, pay now toggle

### Phase 13 - GRN View & Return (COMPLETED ✅) - Feb 2026
- [x] **GRN View Details**
  - [x] View detailed GRN information in modal dialog
  - [x] Shows GRN number, supplier, date, linked PO
  - [x] Items table with SKU, product, qty, prices, line totals
  - [x] Total Cost (COGS) summary
  - [x] Notes and return history (if any)
- [x] **GRN Return - Full or Partial**
  - [x] Full Return: Return all items in GRN
  - [x] Partial Return: Select specific items and quantities to return
  - [x] Return reasons: "Return to Supplier" or "Damaged/Written Off"
- [x] **GRN Return - Settlement Options (for Return to Supplier)**
  - [x] **Supplier Returns Money (Refund)**: 
    - Select bank/cash account to receive refund
    - Journal entry: Debit Bank/Cash, Credit Inventory
    - Bank account balance increased
  - [x] **Supplier Sends More Qty (Credit)**:
    - Creates supplier credit record for future orders
    - Journal entry: Debit AP, Credit Inventory
    - Supplier credit balance tracked
- [x] **GRN Return - Financial Impact**
  - [x] Return to Supplier (Refund): Debit Bank, Credit Inventory
  - [x] Return to Supplier (Credit): Debit AP, Credit Inventory + Create Supplier Credit
  - [x] Damaged/Written Off: Debit Operating Expenses (loss), Credit Inventory
  - [x] Journal entries created with GRNRET- prefix
- [x] **GRN Return - Inventory & WooCommerce Sync**
  - [x] Inventory quantities reduced automatically
  - [x] Inventory movements recorded
  - [x] Stock auto-synced to WooCommerce after return
- [x] **PO Payment Status Display**
  - [x] Shows linked PO payment status in return dialog
  - [x] Displays PO number, total, paid amount, "Fully Paid" badge
- [x] **Role-Based Access Control**
  - [x] Only Admin and Manager can process GRN returns
  - [x] All users can view GRN details
- [x] **Backend Implementation**
  - [x] `GRNReturn` model with `settlement_type` and `refund_account_id`
  - [x] `POST /api/grn/{id}/return` endpoint with all settlement logic
  - [x] Creates `supplier_credits` collection for credit tracking
  - [x] WooCommerce stock sync on return
- [x] **Frontend Implementation**
  - [x] Actions dropdown with View Details and Return GRN options
  - [x] View Details dialog with comprehensive GRN info
  - [x] Return GRN dialog with:
    - PO payment status display
    - Return type (full/partial)
    - Return reason dropdown
    - Settlement options (Refund/Credit) with descriptions
    - Bank account selector for refunds
    - Item selection for partial returns
    - Warning about irreversible action

### Bug Fixes (Session - Feb 18, 2026)
- [x] **Sales Order Payment Not Updating Bank Balance** - FIXED
  - Root cause: Missing Chart of Accounts entries (specifically Accounts Receivable code 1300)
  - Fix: 1) Seeded missing accounts for existing company, 2) Added auto-creation logic in `create_payment` function
  - Result: Bank balance now correctly increases when sales payment recorded
- [x] **Expanded Expense Categories in Quick Transactions** - COMPLETED
  - Added comprehensive list: Hosting, Domain, Materials, Raw Materials, Equipment, Office Supplies, Utilities, Transportation, etc.

### Phase 14 - Product Variations & WooCommerce Variable Product Support (IN PROGRESS 🔄) - Feb 2026
- [x] **Database Schema**
  - [x] `product_variations` collection for storing variation data
  - [x] `products` collection updated with `product_type` field (simple/variable)
  - [x] Variations linked to parent products via `parent_product_id`
  - [x] Each variation stores: SKU, attributes (Color, Size), cost_price, regular_price, sale_price, stock_quantity
- [x] **WooCommerce Variation Sync**
  - [x] `POST /api/variations/sync/all` - Sync all variable products and their variations from WooCommerce
  - [x] `POST /api/variations/sync/product/{id}` - Sync variations for a specific product
  - [x] `GET /api/variations/product/{id}` - Get all variations for a product
  - [x] `GET /api/variations/attributes/list` - Get unique attribute names and values
  - [x] Background sync task for large catalogs
- [x] **Inventory at Variation Level**
  - [x] GRN supports variation selection for variable products
  - [x] Stock quantity tracked per variation (e.g., Trouser Blue Size 32: 10 units)
  - [x] Parent product shows total stock (sum of all variations)
  - [x] WooCommerce stock sync at variation level
- [x] **Purchase Order Variation Support**
  - [x] Product selector shows "(Variable)" indicator for variable products
  - [x] Variation dropdown appears when variable product selected
  - [x] Variation dropdown shows: variation name, SKU, current stock
  - [x] PO items store both `product_id` and `variation_id`
- [x] **GRN Variation Support**
  - [x] When creating GRN from PO, variation information preserved
  - [x] Manual GRN allows variation selection for variable products
  - [x] Stock updates at variation level with WooCommerce sync
- [x] **Products Page Enhancements**
  - [x] "Sync Variations from WooCommerce" button
  - [x] "Type" column showing Simple/Variable badge
  - [x] Expandable rows for variable products to show variations
  - [x] Per-product "Sync Variations" option in dropdown menu
  - [x] Variations display: name, SKU, attributes, prices, stock

**Note**: This feature requires variable products to exist in WooCommerce. The sync pulls variation data (Color, Size attributes) from WooCommerce and enables variation-level inventory management in the ERP.

## Testing Status
- **Backend Tests**: 100% passed (iteration_10)
- **Frontend Tests**: 100% passed (all UI flows verified)
- **Last Test Run**: iteration_10.json (Feb 18, 2026)
- **Finance Module**: Fully tested - Chart of Accounts, Auto-generate Codes, Journal Entries, P&L, Balance Sheet, Cash Flow
- **Simple Finance Module**: Fully tested - Investors, Capital Investment, Quick Transactions, Financial Reports
- **Bank Account Integration**: Fully tested - All transaction forms have bank account selectors, balance updates verified
- **Dynamic Business Name**: Fully tested - Company name displays in sidebar
- **COGS Recognition**: Fully tested - Sales orders create SALE- and COGS- journal entries, returns create RET- and RCOGS- reversal entries
- **Sales Order Payment**: Fully tested - Payment recording updates bank balance, creates journal entries (REC- prefix)
- **Sample Data Seeding**: Fully tested - New user registration seeds 38 default accounts, Balance Sheet balances correctly
- **Financial Reports Consistency**: Verified - Balance Sheet balanced, Trial Balance balanced, Net Profit consistent across reports
- **Two-Way WooCommerce Sync**: Verified - Product category updates sync from ERP to WooCommerce successfully
- **Purchase Order Edit/Delete**: Verified - Role-based access (admin/manager only), business rules enforced
- **GRN Additional Charges**: Verified - Journal entries created correctly (CHG- prefix), account balances updated


## Test Credentials
- **Email**: test@demo.com
- **Password**: password123
- **Company Name**: My Test Company

## Known Limitations
1. WooCommerce integration requires actual store credentials to test
2. Scheduled backups UI exists but scheduler not implemented
3. Reports based on current account balances (period filtering needs enhancement)

## Future/Backlog (P2)
- [ ] Payroll Module
- [ ] Manufacturing Module
- [ ] SaaS Subscription Billing
- [ ] Multi-Warehouse Support
- [ ] Mobile App
- [ ] PDF Export for Reports
- [ ] Scheduled Backup Automation
- [ ] Multi-Currency Support
- [ ] Bank Reconciliation
- [ ] WooCommerce End-to-End Testing

## Test Credentials
- **Email**: admin@example.com
- **Password**: admin123

## File Structure
```
/app/
├── backend/
│   ├── server.py          # Main FastAPI application
│   ├── routes/
│   │   ├── finance.py     # Finance module routes
│   │   ├── simple_finance.py # Simplified accounting for non-accountants
│   │   ├── admin.py       # Admin module routes
│   │   └── woocommerce.py # WooCommerce integration
│   ├── models/
│   │   ├── finance.py     # Finance data models
│   │   └── admin.py       # Admin data models
│   ├── utils/
│   │   ├── helpers.py     # Common utilities
│   │   └── auth.py        # Authentication utilities
│   └── backups/           # Backup storage
├── frontend/
│   └── src/
│       ├── pages/
│       │   ├── ChartOfAccounts.jsx
│       │   ├── GeneralLedger.jsx
│       │   ├── FinancialReports.jsx
│       │   ├── Investors.jsx      # Investor management
│       │   ├── QuickTransactions.jsx # Simplified accounting
│       │   └── SystemAdmin.jsx
│       └── components/
│           └── Layout.jsx # Main navigation
└── memory/
    └── PRD.md            # This file
```

---
*Last Updated: February 25, 2026*
*Version: 2.5.0*
