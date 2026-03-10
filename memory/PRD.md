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
- `POST /backups/upload` - Upload backup file from local machine

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

### Packaging Rules Management (REFACTORED ✅) - March 2026
- [x] **Packaging Rules Module** (`/packaging-rules`)
  - [x] Define rules linking main products to their packaging materials
  - [x] Packaging materials are regular products (purchased via PO → GRN)
  - [x] On sale: Automatically reduce packaging product inventory based on rules
  - [x] On sale: Add packaging cost to COGS journal entry
  - [x] Backend API: `/api/packaging/rules` (GET, POST, PUT, DELETE)
- [x] **Refactoring Changes (March 10, 2026)**
  - [x] Removed separate `/api/packaging-items` endpoint
  - [x] Removed `PackagingItems.jsx` page and route
  - [x] Packaging materials now managed as regular products
  - [x] Rules link products to packaging using product IDs
  - [x] Fixed `packaging_cost` undefined bug in sales order creation

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

### Phase 14 - Product Variations & WooCommerce Variable Product Support (COMPLETED ✅) - Feb 2026
- [x] **Database Schema**
  - [x] `product_variations` collection for storing variation data
  - [x] `products` collection updated with `product_type` field (simple/variable)
  - [x] Variations linked to parent products via `parent_product_id`
  - [x] Each variation stores: SKU, attributes (Color, Size), cost_price, regular_price, sale_price, stock_quantity
- [x] **WooCommerce Variation Sync (Two-Way)**
  - [x] `POST /api/variations/sync/all` - Sync all variable products and their variations from WooCommerce
  - [x] `POST /api/variations/sync/product/{id}` - Sync variations for a specific product
  - [x] `GET /api/variations/product/{id}` - Get all variations for a product
  - [x] `GET /api/variations/attributes/list` - Get unique attribute names and values
  - [x] Background sync task for large catalogs
- [x] **Create Variable Products from ERP**
  - [x] `POST /api/variations/variable-product` - Create variable product with all variation combinations
  - [x] Auto-generates SKU suffixes (e.g., TROUSER-001-BLU-30)
  - [x] Supports multiple attributes (Color, Size, etc.)
  - [x] Auto-generates all variation combinations (e.g., 3 colors × 4 sizes = 12 variations)
  - [x] Syncs to WooCommerce automatically (creates product + all variations)
  - [x] **Fetches attributes from WooCommerce** - `GET /api/woocommerce/attributes` endpoint
  - [x] **Checkbox-based option selection** - Select Color/Size options from WooCommerce with checkboxes
  - [x] **Live preview** shows total variations count based on selected options
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
  - [x] "Sync from WooCommerce" button - pulls variable products
  - [x] "Create Variable Product" button (purple) - creates from ERP
  - [x] "Add Simple Product" button (blue) - existing simple product flow
  - [x] "Type" column showing Simple/Variable badge
  - [x] Expandable rows for variable products to show variations
  - [x] Per-product "Sync Variations" option in dropdown menu
  - [x] Variations display: name, SKU, attributes (Color, Size badges), prices, stock
- [x] **Create Variable Product Dialog**
  - [x] Auto-generated base SKU
  - [x] Product name, description, category fields
  - [x] Dynamic attribute management (add/remove attributes)
  - [x] Comma-separated options input for each attribute
  - [x] Live preview showing variation combinations and count
  - [x] Sync to WooCommerce checkbox

## Testing Status
- **Backend Tests**: 100% passed (iteration_17)
- **Frontend Tests**: 100% passed (all UI flows verified)
- **Payroll Module Tests**: 97% passed (36/37 - 1 test data conflict, not a bug)
- **Manufacturing Dashboard Tests**: 100% passed (iteration_12 - Feb 25, 2026)
- **Manufacturing Financial Integration Tests**: 100% passed (iteration_13 - Feb 25, 2026)
- **Raw Material Stock Financial Integration**: 100% passed (iteration_14 - Feb 25, 2026)
- **Consolidated Transaction List Tests**: 100% passed - 58 total transactions including 13 manufacturing
- **Last Test Run**: iteration_21.json (March 8, 2026)
- **Backup & Restore Tests**: 95% backend (18/19), 100% frontend - Upload, Download, Restore verified
- **Task-Based Payments Tests**: 100% passed (22/22 backend tests, all UI flows verified)
- **Attendance Tracking Tests**: 100% passed (17/17 backend tests, all UI flows verified)
- **OT Payroll Integration Tests**: 100% passed (11/11 backend tests, formula verified)
- **Lint Cleanup**: All Python lint issues fixed, JavaScript clean
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
- **Manufacturing Module**: Fully tested - Raw Materials, BOM, Work Orders, Dashboard with KPIs
- **Payroll Module**: Fully tested - Departments, Employees, Leave, Advances, Payroll processing, Reports


## Test Credentials
- **Email**: test@demo.com
- **Password**: password123
- **Company Name**: My Test Company

## Known Limitations
1. WooCommerce integration requires actual store credentials to test
2. Scheduled backups UI exists but scheduler not implemented
3. Reports based on current account balances (period filtering needs enhancement)

### Phase 15 - Manufacturing Module (COMPLETED ✅) - Feb 2026
- [x] **Raw Materials Management**
  - [x] Separate Raw Materials inventory (distinct from finished products)
  - [x] SKU auto-generation (RM0001, RM0002...)
  - [x] Categories: Fabric, Thread, Buttons, Zippers, Labels, Packaging, Accessories
  - [x] Unit of measure support: piece, meter, kg, liter, roll, sheet, etc.
  - [x] Low stock alerts
  - [x] Add stock functionality with reference tracking
  - [x] Stock movement history
- [x] **Bill of Materials (BOM)**
  - [x] Define raw materials needed for each finished product
  - [x] Support for variable products (per variation BOM)
  - [x] Quantity per unit with wastage % allowance
  - [x] Labor cost per unit
  - [x] Overhead % calculation (% of material + labor)
  - [x] Auto-calculate total production cost per unit
  - [x] Expandable view showing component breakdown
- [x] **Work Orders**
  - [x] Create production orders for Stock or Customer Orders
  - [x] Status flow: Draft → Materials Issued → In Progress → QC Pending → Completed
  - [x] **Issue Materials**: Deduct raw materials from stock, charge to WIP
  - [x] **Record Production**: Track completed quantities with labor cost
  - [x] **QC Inspection**: Pass/Fail quantities with rejection reasons
  - [x] **Cancel Order**: Return materials to stock with reversal entries
  - [x] Cost tracking: Material, Labor, Overhead per unit
- [x] **Financial Integration**
  - [x] Material Issue: Dr. WIP, Cr. Raw Materials Inventory
  - [x] Labor Cost: Dr. WIP, Cr. Manufacturing Labor
  - [x] Production Complete: Dr. Finished Goods, Cr. WIP
  - [x] QC Rejection/Scrap: Dr. Manufacturing Loss, Cr. WIP
  - [x] Auto-create Chart of Accounts entries (1400 WIP, 1200 Raw Materials, etc.)
- [x] **WooCommerce Integration**
  - [x] Finished goods automatically sync to WooCommerce after QC completion
  - [x] Updates product stock in WooCommerce
- [x] **UI Pages**
  - [x] `/manufacturing` - Manufacturing Dashboard with KPIs (added Feb 25, 2026)
  - [x] `/raw-materials` - Raw Materials management
  - [x] `/bom` - Bill of Materials management
  - [x] `/work-orders` - Work Order management
  - [x] Manufacturing section in sidebar navigation

### Phase 16 - Manufacturing Dashboard (COMPLETED ✅) - Feb 25, 2026
- [x] **KPI Cards**
  - [x] This Month Production value and units produced
  - [x] Orders Completed count
  - [x] Active Orders count (in progress)
  - [x] Low Stock Alerts count
- [x] **Work Order Status Breakdown**
  - [x] Visual progress bars for all statuses
  - [x] Status counts: Draft, Materials Issued, In Progress, QC Pending, Completed, Cancelled
  - [x] Total work orders summary
- [x] **Raw Material Stock Alerts**
  - [x] Display low stock materials with threshold info
  - [x] "All materials in stock" message when no alerts
- [x] **Recent Work Orders Table**
  - [x] Shows WO Number, Product, Quantity, Completed, Est. Cost, Status
  - [x] Clickable rows navigate to Work Orders page
- [x] **Quick Action Cards**
  - [x] Navigate to Raw Materials, BOM, Work Orders pages
- [x] **Dashboard Actions**
  - [x] Refresh button to reload data
  - [x] View Work Orders button

### Phase 17 - Manufacturing Financial Integration & Consolidated Transactions (COMPLETED ✅) - Feb 25, 2026
- [x] **Manufacturing Transactions in Consolidated List**
  - [x] Material Issue transactions (mfg_material_issue)
  - [x] Labor Cost transactions (mfg_labor)
  - [x] Production Complete transactions (mfg_production)
  - [x] Scrap/Reject transactions (mfg_scrap)
  - [x] Manufacturing Reversal transactions (mfg_reversal)
  - [x] Raw Material Purchase transactions (raw_material_purchase)
- [x] **Quick Transactions Page Enhancements**
  - [x] Manufacturing filter option in dropdown
  - [x] Proper icons for each manufacturing transaction type
  - [x] Color coding: Production (green), Material Issue/Labor (indigo), Scrap (red)
  - [x] Labels: Material Issue, Labor Cost, Production, Scrap/Reject, RM Purchase
- [x] **Backend Integration**
  - [x] GET /api/simple-finance/all-transactions includes MFG- and RM- prefix journal entries
  - [x] Filter by "manufacturing" shows all manufacturing-related transaction types

### Phase 18 - Raw Material Stock Financial Integration (COMPLETED ✅) - Feb 25, 2026
- [x] **Bug Fix: Raw Material Cost Not Deducting from Accounts**
  - [x] Added bank account selector to Add Stock dialog
  - [x] Total Cost field auto-calculates (Quantity × Unit Cost)
  - [x] When bank account selected:
    - Creates journal entry (Dr: Raw Materials Inventory 1200, Cr: Bank/Cash)
    - Reduces bank account balance
    - Updates Chart of Accounts balances
  - [x] Without bank account: Works as before (no financial entry)
- [x] **Journal Entry Details**
  - [x] Entry number format: RM-{SKU}-{movement_id}
  - [x] Reference type: raw_material_receipt
  - [x] Appears in Quick Transactions with "RM Purchase" label

### Phase 19 - Raw Material Procurement Module (COMPLETED ✅) - March 7, 2026
- [x] **RM Suppliers** (`/rm-suppliers`)
  - [x] Separate supplier list for raw materials (not shared with product suppliers)
  - [x] Fields: Name, Contact Person, Email, Phone, Address, Default Payment Terms, Notes
  - [x] CRUD operations with search functionality
  - [x] Supplier stats: Total orders, total amount, outstanding balance
- [x] **RM Purchase Orders** (`/rm-purchase-orders`)
  - [x] Create PO linked to RM Supplier with line items (raw materials)
  - [x] Fields: Priority (low/normal/high/urgent), Expected Delivery Date, Expiry Date, Notes
  - [x] Payment Terms: Immediate or Credit (Net 30/60/90 days)
  - [x] Status flow: Draft → Approved → Partially Received → Completed
  - [x] PO Number auto-generated: RMPO-YYYYMM-0001
  - [x] Role-based approval (admin/manager only)
- [x] **RM GRN (Goods Received Note)** (`/rm-grn`)
  - [x] Receive goods against approved RM Purchase Orders
  - [x] Partial receiving support (receive part now, rest later)
  - [x] Auto-update raw material stock on receive
  - [x] GRN Number auto-generated: RMGRN-YYYYMM-0001
  - [x] Financial integration:
    - Immediate payment: Bank account selector, creates journal entry (Dr: Inventory, Cr: Bank)
    - Credit terms: Creates Accounts Payable entry
- [x] **RM GRN Returns** (`/rm-grn-returns`)
  - [x] Return defective materials to supplier
  - [x] Return Number auto-generated: RMRET-YYYYMM-0001
  - [x] Settlement options: Refund (credit to bank) or Supplier Credit Note
  - [x] Reason field required for each returned item
  - [x] Auto-deduct stock and reverse financial entries
- [x] **Navigation Integration**
  - [x] All 4 pages under Manufacturing section in sidebar
  - [x] Menu order: Manufacturing → Raw Materials → RM Suppliers → RM Purchase Orders → RM GRN → RM GRN Returns → BOM → Work Orders

#### RM Procurement API Endpoints (/api/rm-procurement)
- `GET /suppliers` - List RM suppliers
- `GET /suppliers/{id}` - Get supplier with stats
- `POST /suppliers` - Create RM supplier
- `PUT /suppliers/{id}` - Update supplier
- `DELETE /suppliers/{id}` - Delete supplier
- `GET /purchase-orders` - List RM POs with status filter
- `GET /purchase-orders/{id}` - Get PO with items and GRN history
- `POST /purchase-orders` - Create RM PO
- `PUT /purchase-orders/{id}` - Update draft PO
- `POST /purchase-orders/{id}/approve` - Approve PO
- `DELETE /purchase-orders/{id}` - Delete draft PO
- `POST /purchase-orders/{id}/record-payment` - Record payment for credit PO
- `GET /grn` - List RM GRNs
- `GET /grn/{id}` - Get GRN with returns
- `POST /grn` - Receive goods against PO
- `GET /grn-returns` - List RM GRN returns
- `POST /grn-returns` - Create return with refund/credit
- `GET /accounts-payable` - RM accounts payable summary

### Phase 20 - Payroll Module (COMPLETED ✅) - March 7, 2026
- [x] **Departments Management**
  - [x] CRUD operations for departments
  - [x] Employee count per department
  - [x] Prevent deletion of departments with employees
- [x] **Employee Management**
  - [x] Employee types: Permanent, Casual, Freelancer, Contract
  - [x] Auto-generated Employee ID (EMP0001, EMP0002...)
  - [x] Personal details, NIC, bank account info
  - [x] Department assignment
  - [x] Payment frequency: Monthly, Weekly, Daily, Per Task
  - [x] Basic salary, hourly rate, daily rate
  - [x] Employee termination with status tracking
- [x] **Salary Structure Configuration**
  - [x] EPF rates: 8% employee, 12% employer (20% total)
  - [x] ETF rate: 3% employer
  - [x] Overtime rates: 1.25x weekday, 1.5x weekend
  - [x] Configurable allowances (fixed or percentage)
  - [x] Sri Lanka PAYE tax slabs
- [x] **Leave Management**
  - [x] Leave types: Annual, Sick, Casual, Maternity, Paternity
  - [x] Leave request creation with balance check
  - [x] Leave approval/rejection workflow
  - [x] Auto-deduct from balance on approval
  - [x] Manual balance editing
- [x] **Advances & Loans**
  - [x] Issue salary advances and loans
  - [x] Monthly deduction configuration
  - [x] Recovery period calculation
  - [x] Optional immediate payment via bank account
  - [x] Financial integration (journal entry creation)
  - [x] Track remaining balance
- [x] **Payroll Processing**
  - [x] Run payroll for period with payment frequency filter
  - [x] Auto-calculate gross, deductions, net pay per employee
  - [x] EPF/ETF calculations
  - [x] PAYE tax calculation
  - [x] Advance deductions
  - [x] Payroll workflow: Draft → Submit → Approve → Process & Pay
  - [x] Financial integration (journal entries for salaries, EPF, ETF, tax)
  - [x] Bank account selection for payment
  - [x] Auto-update advance balances
- [x] **Task Payments (Freelancers)**
  - [x] One-time task payment creation
  - [x] Financial integration
- [x] **Payroll Reports**
  - [x] Summary report (payrolls, gross, deductions, net)
  - [x] EPF/ETF contribution report by employee
  - [x] Department salary breakdown report
  - [x] Individual payslips
- [x] **UI Pages**
  - [x] `/departments` - Department management
  - [x] `/employees` - Employee management with filters
  - [x] `/salary-structure` - EPF/ETF/OT rates, allowances
  - [x] `/leave-management` - Leave requests and balances
  - [x] `/advances` - Advances & loans
  - [x] `/payroll` - Payroll runs with workflow
  - [x] `/payroll-reports` - Summary, EPF/ETF, Department reports
- [x] **Bug Fix: Advances.jsx Select.Item empty value**
  - [x] Fixed runtime error with empty string value in Select.Item

#### Payroll API Endpoints (/api/payroll)
- `GET/POST /departments` - Manage departments
- `PUT/DELETE /departments/{id}` - Update/delete department
- `GET/POST /employees` - Manage employees
- `GET /employees/{id}` - Get employee with leave balances and advances
- `GET /employees/next-id/generate` - Auto-generate next employee ID
- `PUT /employees/{id}` - Update employee
- `DELETE /employees/{id}` - Terminate employee
- `GET/PUT /salary-structure` - Salary structure settings
- `POST /salary-structure/allowances` - Add allowance
- `DELETE /salary-structure/allowances/{id}` - Delete allowance
- `GET /leave/balances` - Get leave balances
- `PUT /leave/balances/{employee_id}` - Update leave balance
- `GET/POST /leave/requests` - Leave requests
- `POST /leave/requests/{id}/approve` - Approve leave
- `POST /leave/requests/{id}/reject` - Reject leave
- `GET/POST /advances` - Manage advances/loans
- `GET/POST /payrolls` - Manage payroll runs
- `GET /payrolls/{id}` - Get payroll with items
- `PUT /payrolls/{id}/items/{item_id}` - Adjust payroll item
- `POST /payrolls/{id}/submit` - Submit for approval
- `POST /payrolls/{id}/approve` - Approve payroll
- `POST /payrolls/{id}/process` - Process and pay
- `DELETE /payrolls/{id}` - Delete draft payroll
- `GET/POST /task-payments` - Task payments for freelancers
- `GET /reports/payslip/{payroll_id}/{employee_id}` - Individual payslip
- `GET /reports/summary` - Payroll summary
- `GET /reports/epf-etf` - EPF/ETF report
- `GET /reports/department` - Department salary breakdown

### Phase 21 - Task-Based Payments (COMPLETED ✅) - March 8, 2026
- [x] **Task Assignment System**
  - [x] Assign tasks to any employee with payment amount
  - [x] Task categories: Design, Development, Marketing, Production, Admin, Other
  - [x] Due dates for tasks
  - [x] Admin/Manager only can assign and verify tasks
- [x] **Task Status Workflow**
  - [x] Assigned → In Progress (employee starts)
  - [x] In Progress → Completed (employee marks complete)
  - [x] Completed → Verified (manager approves)
  - [x] Reject option to send back for revision
  - [x] Cancel task option
- [x] **Payroll Integration**
  - [x] Verified tasks automatically included in next payroll run
  - [x] Task payments added to gross salary
  - [x] Task Pay column in payroll details
  - [x] Tasks marked as paid after payroll processing
- [x] **Task Assignments UI Page** (`/task-assignments`)
  - [x] Stats cards: Total, Assigned, In Progress, Awaiting Verification, Verified (Unpaid), Pending Payment Amount
  - [x] Filters by status, category, employee
  - [x] Task table with all details
  - [x] Action buttons: Start, Complete, Verify, Reject, Cancel
  - [x] View task details dialog
  - [x] Create/Edit task dialog
- [x] **API Endpoints**
  - [x] `GET /payroll/tasks` - List tasks with filters
  - [x] `GET /payroll/tasks/pending-payment` - Verified unpaid tasks
  - [x] `GET /payroll/tasks/categories` - Task categories
  - [x] `GET /payroll/tasks/{id}` - Task details
  - [x] `POST /payroll/tasks` - Create task
  - [x] `PUT /payroll/tasks/{id}` - Update task
  - [x] `POST /payroll/tasks/{id}/start` - Start task
  - [x] `POST /payroll/tasks/{id}/complete` - Mark complete
  - [x] `POST /payroll/tasks/{id}/verify` - Verify task
  - [x] `POST /payroll/tasks/{id}/reject` - Reject task
  - [x] `POST /payroll/tasks/{id}/cancel` - Cancel task
  - [x] `GET /payroll/tasks/employee/{id}/summary` - Employee task summary

### Phase 22 - Attendance Tracking (COMPLETED ✅) - March 8, 2026
- [x] **Attendance Recording**
  - [x] Full day = 9 hours (8 hrs work + 1 hr break) - normal duty
  - [x] Half day = 5 hours (with break)
  - [x] Standard work hours = 9 hours (OT only for hours > 9)
  - [x] Status types: Present, Absent, Half Day, Late, On Leave
- [x] **Overtime Calculation**
  - [x] OT calculated only for hours > 9 (normal duty)
  - [x] 9 hours = no OT, 10 hours = 1 hr OT, 11 hours = 2 hrs OT
  - [x] Regular OT (weekday): 1.25x rate
  - [x] Weekend OT (Sat/Sun): 1.5x rate
  - [x] Separate tracking for regular and weekend overtime
- [x] **Payroll Integration** ✅
  - [x] Payroll automatically fetches attendance data for period
  - [x] Calculates overtime hours from attendance records
  - [x] Calculates OT pay using hourly rate and OT rates
  - [x] OT Pay column in payroll details table
  - [x] Earnings Summary shows OT breakdown (X.Xh reg + X.Xh wknd)
  - [x] Gross = Basic + Allowances + Task Pay + OT Pay
  - [x] Hourly rate = basic_salary / 198 (22 days × 9 hours)
- [x] **Daily Entry Tab**
  - [x] Date navigation (Previous/Next/Date picker)
  - [x] Weekend detection with "1.5x OT rate" indicator
  - [x] Stats cards: Total, Present, Absent, Half Day, Late, On Leave, Not Marked
  - [x] Employee table with Status dropdown, Check In/Out times
  - [x] Auto-fill times based on status (Present: 08:00-17:00, Half Day: 08:00-13:00)
  - [x] Auto-calculate hours worked and overtime
  - [x] Bulk save with "Save All" button
  - [x] Shows approved leave status from Leave Management
- [x] **Monthly Report Tab**
  - [x] Month picker and department filter
  - [x] Employee attendance summary table
  - [x] Columns: Present, Half Day, Absent, Late, Leave, Work Days, Total Hours, OT Hours
  - [x] Totals row at bottom
- [x] **Overtime Calculation**
  - [x] Regular OT for weekdays (hours > 8)
  - [x] Weekend OT for Saturdays/Sundays
  - [x] Separate tracking for regular and weekend overtime
- [x] **API Endpoints**
  - [x] `GET /payroll/attendance/settings` - Get attendance constants
  - [x] `GET /payroll/attendance/daily/{date}` - Get daily attendance for all employees
  - [x] `POST /payroll/attendance` - Create/update single record
  - [x] `POST /payroll/attendance/bulk` - Bulk save multiple employees
  - [x] `PUT /payroll/attendance/{id}` - Update record
  - [x] `DELETE /payroll/attendance/{id}` - Delete record
  - [x] `GET /payroll/attendance/summary/{employee_id}` - Individual monthly summary
  - [x] `GET /payroll/attendance/monthly-report` - All employees monthly summary
- [x] **UI Page** (`/attendance`)
  - [x] Navigation link under Payroll section (Clock icon)
  - [x] Tabs: Daily Entry, Monthly Report

### Phase 23 - Lint/Code Cleanup (COMPLETED ✅) - March 8, 2026
- [x] **Backend Python Lint Fixes**
  - [x] Fixed bare `except` clauses in `payroll.py` (2 occurrences)
  - [x] Fixed bare `except` clause in `grn.py`
  - [x] Fixed `status` import shadowing in `server.py` (renamed to `http_status`)
  - [x] Removed unused `category` variables in `server.py` (2 occurrences)
  - [x] Fixed parameter naming conflict (`date` → `att_date`) in `payroll.py`
  - [x] Fixed `payment_date` field naming in `TaskPaymentCreate` model
- [x] **Frontend JavaScript Lint**
  - [x] All checks passed (no issues found)

### Phase 24 - Documentation/Help Center (COMPLETED ✅) - March 8, 2026
- [x] **In-App Documentation Page** (`/documentation`)
  - [x] Searchable documentation with instant filtering
  - [x] Table of contents with 16 sections
  - [x] Sticky sidebar navigation
  - [x] Active section highlighting on scroll
  - [x] Back to top button
- [x] **Comprehensive Coverage** (All Modules)
  - [x] Getting Started, Dashboard, User Management
  - [x] Products & Inventory, Suppliers & PO, GRN
  - [x] Sales Orders & Invoices, Payments
  - [x] WooCommerce Integration
  - [x] Manufacturing (Raw Materials, BOM, Work Orders)
  - [x] Payroll Management, Attendance Tracking
  - [x] Finance & Accounting, Reports
  - [x] System Settings, FAQ & Troubleshooting
- [x] **Features**
  - [x] Markdown-style formatting (headers, lists, bold)
  - [x] Search with text highlighting
  - [x] Navigation link in Admin menu

### Phase 25 - Backup & Restore Enhancement (COMPLETED ✅) - March 8, 2026
- [x] **Backup Upload Feature**
  - [x] Upload previously downloaded backup files (.json or .json.gz)
  - [x] Validate backup file structure (metadata, collections)
  - [x] Show "Uploaded" badge on uploaded backups
  - [x] Upload modal with file picker and format guidance
- [x] **Backend Enhancements**
  - [x] `POST /api/admin/backups/upload` - Upload backup file endpoint
  - [x] Proper error handling (400 for malformed files, not 500)
  - [x] Extract and display backup statistics (collections, total records)
  - [x] Re-raises HTTPException properly instead of converting to 500
- [x] **Frontend Enhancements**
  - [x] "Upload Backup" button in System Admin page
  - [x] Upload backup modal with drag-and-drop style file picker
  - [x] Purple "Uploaded" badge for uploaded backups
  - [x] Fixed HTML nesting warnings in AlertDialogDescription (asChild prop)
  - [x] AdminAPI functions added to api.js
- [x] **Testing**
  - [x] Backend tests: 95% pass (18/19)
  - [x] Frontend tests: 100% pass
  - [x] Manual API testing verified

## Future/Backlog (P2)
- [ ] SaaS Subscription Billing
- [ ] Multi-Warehouse Support
- [ ] Mobile App
- [ ] PDF Export for Reports
- [ ] Scheduled Backup Automation
- [ ] Multi-Currency Support
- [ ] Bank Reconciliation
- [ ] WooCommerce End-to-End Testing
- [ ] Credit-based payment schemes (30, 60, 90 days) for regular purchase orders
- [ ] WooCommerce conflict resolution & batch import

## Test Credentials
- **Email**: lahiruraja97@gmail.com
- **Password**: password123

## File Structure
```
/app/
├── backend/
│   ├── server.py          # Main FastAPI application
│   ├── routes/
│   │   ├── finance.py     # Finance module routes
│   │   ├── simple_finance.py # Simplified accounting for non-accountants
│   │   ├── admin.py       # Admin module routes
│   │   ├── woocommerce.py # WooCommerce integration
│   │   ├── variations.py  # Product variations management (NEW)
│   │   ├── grn.py         # Goods Received Note routes
│   │   ├── purchasing.py  # Purchase Order routes
│   │   ├── manufacturing.py # Manufacturing module routes
│   │   ├── rm_procurement.py # Raw Material Procurement routes
│   │   ├── payroll.py      # Payroll module routes
│   │   └── transactions.py # Consolidated transactions
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
│       │   ├── Products.jsx        # Product list with variations support
│       │   ├── PurchaseOrders.jsx  # PO with variation selection
│       │   ├── GRN.jsx             # GRN with variation support
│       │   ├── ChartOfAccounts.jsx
│       │   ├── GeneralLedger.jsx
│       │   ├── FinancialReports.jsx
│       │   ├── Investors.jsx      # Investor management
│       │   ├── QuickTransactions.jsx # Simplified accounting
│       │   ├── RMSuppliers.jsx    # RM Suppliers
│       │   ├── RMPurchaseOrders.jsx # RM Purchase Orders
│       │   ├── RMGRN.jsx          # RM Goods Received
│       │   ├── RMGRNReturns.jsx   # RM GRN Returns
│       │   ├── payroll/           # Payroll Module
│       │   │   ├── Departments.jsx
│       │   │   ├── Employees.jsx
│       │   │   ├── SalaryStructure.jsx
│       │   │   ├── LeaveManagement.jsx
│       │   │   ├── Advances.jsx
│       │   │   ├── Payroll.jsx
│       │   │   └── PayrollReports.jsx
│       │   └── SystemAdmin.jsx
│       └── components/
│           └── Layout.jsx # Main navigation
└── memory/
    └── PRD.md            # This file
```

---
*Last Updated: March 10, 2026*
*Version: 4.2.0*
