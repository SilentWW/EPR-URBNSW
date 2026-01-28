# E1 ERP System - Product Requirements Document

## Project Overview
A cloud-based, web ERP system optimized for online sellers, WooCommerce businesses, and small/medium enterprises. Built with multi-tenant SaaS architecture.

## Technology Stack
- **Backend**: FastAPI (Python)
- **Frontend**: React with Tailwind CSS + Shadcn UI
- **Database**: MongoDB
- **Authentication**: JWT-based
- **Currency**: LKR (Sri Lankan Rupee)
- **Timezone**: Asia/Colombo

## User Personas
1. **Admin** - Full access to all modules including user management
2. **Manager** - Access to operations and reports
3. **Accounts** - Access to financial modules
4. **Store** - Access to inventory and sales
5. **Staff** - Basic access

## Core Requirements (Static)

### 1. User & Role Management
- User registration with company creation
- JWT authentication (24-hour token)
- Role-based permissions (Admin, Manager, Accounts, Store, Staff)
- Activity audit logs

### 2. Company Settings
- Company profile (name, address, email, phone)
- Currency configuration
- Timezone settings
- Tax rate configuration

### 3. WooCommerce Integration (Configurable)
- Store URL, Consumer Key, Consumer Secret fields
- Enable/disable toggle
- Designed for two-way sync (products, orders, customers, stock)

### 4. Product & Inventory Management
- Product master (SKU, name, category, cost/selling price)
- Stock quantity tracking
- Low stock alerts
- Inventory movements (in/out/adjustment)
- Inventory valuation report

### 5. Customer Management (CRM)
- Customer database with contact details
- Order history per customer
- Outstanding balance tracking

### 6. Supplier Management
- Supplier master with contact info
- Purchase order history
- Payables tracking

### 7. Sales Management
- Sales orders (manual + WooCommerce)
- Auto-invoice generation
- Discounts support
- Returns handling (stock restoration + accounting reversal)
- Payment status tracking

### 8. Purchase Management
- Purchase orders
- Goods received functionality
- Supplier invoices
- Cost price updates

### 9. Basic Accounting
- Income tracking (auto from sales)
- Expense tracking (auto from purchases + manual)
- Profit & Loss summary with charts
- Customer receivables
- Supplier payables

### 10. Payments & Banking
- Multiple payment methods (cash, bank, card, online)
- Payment recording against orders
- Cash/bank balance tracking

### 11. Dashboard & Reporting
- Business overview dashboard
- Sales metrics & trends (7/30 days)
- Top selling products
- Low stock alerts
- Export to CSV

### 12. Notifications
- Low stock alerts
- Pending payment alerts

## What's Been Implemented (January 2026)

### Backend (server.py)
- [x] JWT Authentication (register, login, me)
- [x] Company management with WooCommerce settings
- [x] User management (CRUD + role updates)
- [x] Products CRUD with categories
- [x] Inventory movements with stock tracking
- [x] Customers CRUD with order history
- [x] Suppliers CRUD with purchase history
- [x] Sales Orders with auto-inventory deduction
- [x] Purchase Orders with goods received
- [x] Payments with bank/cash ledger
- [x] Accounting entries with P&L
- [x] Dashboard summary & charts
- [x] Reports with date filtering
- [x] Notifications API
- [x] Demo data seeding

### Frontend Pages
- [x] Login & Registration
- [x] Dashboard with charts
- [x] Products (list, add, edit, delete)
- [x] Inventory movements & valuation
- [x] Customers (list, add, edit, delete)
- [x] Suppliers (list, add, edit, delete)
- [x] Sales Orders (create, view, payment, return)
- [x] Invoices list
- [x] Purchase Orders (create, view, receive, payment)
- [x] Payments with balance summary
- [x] Accounting with P&L charts
- [x] Reports with export
- [x] Settings (company, WooCommerce, users)
- [x] Notifications

## Prioritized Backlog

### P0 (Critical - Done)
- [x] Core authentication
- [x] Dashboard
- [x] Product management
- [x] Sales & Purchase orders
- [x] Basic accounting

### P1 (High Priority - Future)
- [ ] Actual WooCommerce API sync implementation
- [ ] Webhook handlers for real-time Woo updates
- [ ] PDF invoice generation
- [ ] Email notifications

### P2 (Medium Priority - Future)
- [ ] Multi-warehouse support
- [ ] Advanced reporting
- [ ] Subscription billing for SaaS
- [ ] Mobile responsive improvements

### P3 (Low Priority - Future)
- [ ] Payroll module
- [ ] Manufacturing module
- [ ] Advanced accounting (double-entry)
- [ ] Mobile app

## Next Action Items
1. Implement actual WooCommerce API integration (currently UI-ready)
2. Add PDF invoice generation
3. Email notifications for alerts
4. Date range filters on all reports
5. Export functionality for all data tables
