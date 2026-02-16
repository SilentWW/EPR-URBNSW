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
- [x] **Quick Transactions Module** (`/quick-transactions`)
  - [x] Pay Expense - auto-creates journal entry (Debit Expense, Credit Cash)
  - [x] Pay Salary - handles allowances/deductions (Debit Salaries, Credit Cash/Tax)
  - [x] Receive Revenue - auto-creates journal entry (Debit Cash, Credit Revenue)
  - [x] Loan Transactions - receive and repay loans from banks/financial companies
- [x] **Financial Data Integrity Fix** (Feb 16, 2026)
  - [x] Refactored `simple_finance.py` to use same schema as `finance.py`
  - [x] Journal entries now use `lines` array with `account_id` (not `entries`)
  - [x] Proper balance updates based on account type
  - [x] All transactions correctly appear in Chart of Accounts
  - [x] Financial Reports (Trial Balance, P&L, Balance Sheet) now accurate

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
- `POST /chart-of-accounts` - Create account
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

## Testing Status
- **Backend Tests**: 39/39 passed (100%)
- **Frontend Tests**: 26/26 passed (100%)
- **Last Test Run**: iteration_5.json (Feb 16, 2026)
- **Finance Module**: Fully tested - Chart of Accounts, Journal Entries, P&L, Balance Sheet, Cash Flow
- **Simple Finance Module**: Fully tested - Investors, Capital Investment, Quick Transactions, Financial Reports

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
*Last Updated: January 28, 2026*
*Version: 2.0.0*
