import { useState, useEffect, useRef } from 'react';
import { Card, CardContent } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Button } from '../components/ui/button';
import { 
  Search, BookOpen, ChevronRight, ChevronUp, 
  LayoutDashboard, Package, Users, Truck, ShoppingCart, 
  FileText, CreditCard, Settings, Factory, Calculator,
  Globe, BarChart3, HelpCircle, Clock, ClipboardList
} from 'lucide-react';

const Documentation = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [activeSection, setActiveSection] = useState('getting-started');
  const [showBackToTop, setShowBackToTop] = useState(false);
  const contentRef = useRef(null);

  // Table of Contents
  const tableOfContents = [
    { id: 'getting-started', title: 'Getting Started', icon: BookOpen },
    { id: 'dashboard', title: 'Dashboard Overview', icon: LayoutDashboard },
    { id: 'user-management', title: 'User Management', icon: Users },
    { id: 'products-inventory', title: 'Products & Inventory', icon: Package },
    { id: 'suppliers-po', title: 'Suppliers & Purchase Orders', icon: Truck },
    { id: 'grn', title: 'Goods Received Notes (GRN)', icon: ClipboardList },
    { id: 'sales-orders', title: 'Sales Orders & Invoices', icon: ShoppingCart },
    { id: 'payments', title: 'Payments', icon: CreditCard },
    { id: 'woocommerce', title: 'WooCommerce Integration', icon: Globe },
    { id: 'manufacturing', title: 'Manufacturing', icon: Factory },
    { id: 'payroll', title: 'Payroll Management', icon: Calculator },
    { id: 'attendance', title: 'Attendance Tracking', icon: Clock },
    { id: 'finance', title: 'Finance & Accounting', icon: FileText },
    { id: 'reports', title: 'Reports', icon: BarChart3 },
    { id: 'settings', title: 'System Settings', icon: Settings },
    { id: 'faq', title: 'FAQ & Troubleshooting', icon: HelpCircle },
  ];

  // Documentation content
  const documentationContent = {
    'getting-started': {
      title: 'Getting Started',
      content: `
## Welcome to the ERP System

This comprehensive ERP (Enterprise Resource Planning) system helps you manage all aspects of your business including inventory, sales, purchases, manufacturing, payroll, and finances.

### First Time Login

1. Open the application in your web browser
2. Enter your email address and password
3. Click "Sign In"
4. You will be redirected to the Dashboard

### Initial Setup Checklist

After your first login, complete these steps:

1. **Company Settings** - Go to Settings and update your company name
2. **Chart of Accounts** - Review the default accounts in Accounting > Chart of Accounts
3. **Bank Accounts** - Add your bank accounts in Accounting > Bank Accounts
4. **Categories** - Set up product categories in Products > Categories
5. **Suppliers** - Add your suppliers in Suppliers menu
6. **Customers** - Add your customers in Customers menu

### Navigation

- **Sidebar Menu**: Access all modules from the left sidebar
- **Top Bar**: Shows your company name and user profile
- **Quick Actions**: Most pages have action buttons in the top-right corner

### Understanding the Interface

Each module follows a consistent pattern:
- **List View**: Shows all records with filters and search
- **Create/Edit**: Forms to add or modify records
- **Details View**: Click on any record to see full details
- **Actions Menu**: Three-dot menu for additional options
      `
    },
    'dashboard': {
      title: 'Dashboard Overview',
      content: `
## Dashboard

The Dashboard provides a quick overview of your business performance.

### Key Metrics

- **Total Revenue**: Sum of all paid invoices
- **Total Expenses**: Sum of all purchase payments
- **Net Profit**: Revenue minus Expenses
- **Pending Orders**: Orders awaiting fulfillment

### Recent Activity

The dashboard shows:
- Recent sales orders
- Low stock alerts
- Pending purchase orders
- Recent payments

### Quick Actions

From the dashboard, you can:
- Create new sales order
- Create new purchase order
- View financial reports
- Check inventory status
      `
    },
    'user-management': {
      title: 'User Management',
      content: `
## User Management

Manage user accounts and access permissions.

### Creating a New User

1. Go to **Settings** > **Users**
2. Click **Add User**
3. Fill in the details:
   - Email address (used for login)
   - Password (minimum 8 characters)
   - Full name
   - Role (Admin, Manager, Staff)
4. Click **Save**

### User Roles

- **Admin**: Full access to all features including settings
- **Manager**: Can manage operations, approve transactions
- **Staff**: Basic access to assigned modules

### Password Reset

1. On the login page, click "Forgot Password"
2. Enter your email address
3. Check your email for reset link
4. Create a new password

### Deactivating a User

1. Go to Settings > Users
2. Find the user and click Edit
3. Change status to "Inactive"
4. The user will no longer be able to login
      `
    },
    'products-inventory': {
      title: 'Products & Inventory',
      content: `
## Products & Inventory Management

Manage your product catalog and track inventory levels.

### Adding a New Product

1. Go to **Products** menu
2. Click **Add Product**
3. Fill in the details:
   - **SKU**: Unique product code
   - **Name**: Product name
   - **Category**: Select or create category
   - **Cost Price**: Your purchase cost
   - **Selling Price**: Price for customers
   - **Initial Stock**: Current quantity
   - **Reorder Level**: Low stock alert threshold
4. Click **Save**

### Product Variations

For products with variations (size, color):
1. Enable "Has Variations" when creating product
2. Add variation attributes (e.g., Size: S, M, L)
3. Set individual prices and stock for each variation

### Inventory Tracking

Stock is automatically updated when:
- GRN is received (stock increases)
- Sales order is fulfilled (stock decreases)
- Returns are processed
- Manual adjustments are made

### Stock Adjustments

To manually adjust stock:
1. Go to Inventory menu
2. Click on the product
3. Click "Adjust Stock"
4. Enter new quantity and reason
5. Stock and adjustment history are recorded

### Low Stock Alerts

Products below reorder level appear in:
- Dashboard alerts
- Low Stock report
- Can trigger automatic PO creation (if enabled)

### Categories

Organize products with categories:
1. Go to Products > Categories
2. Create hierarchical categories
3. Categories sync with WooCommerce if connected
      `
    },
    'suppliers-po': {
      title: 'Suppliers & Purchase Orders',
      content: `
## Suppliers & Purchase Orders

Manage your suppliers and create purchase orders.

### Adding a Supplier

1. Go to **Suppliers** menu
2. Click **Add Supplier**
3. Fill in details:
   - Company name
   - Contact person
   - Email and phone
   - Address
   - Payment terms (Immediate, 30 days, etc.)
4. Click **Save**

### Creating a Purchase Order

1. Go to **Purchase Orders**
2. Click **Create PO**
3. Select supplier
4. Add items:
   - Search and select products
   - Enter quantity and unit price
   - Line total calculates automatically
5. Add additional charges if any:
   - Shipping costs
   - Handling fees
   - Customs duties
6. Review total amount
7. Click **Save as Draft** or **Submit**

### Purchase Order Status

- **Draft**: Can be edited or deleted
- **Submitted**: Sent to supplier, awaiting goods
- **Partial**: Some items received via GRN
- **Completed**: All items received
- **Cancelled**: Order cancelled

### Editing a Purchase Order

Only Draft POs can be edited:
1. Open the PO
2. Click Edit
3. Modify items or details
4. Save changes

### PO Approval Workflow

If approval is required:
1. Staff creates PO as Draft
2. Manager reviews and Approves
3. Approved PO can be sent to supplier
4. GRN can be created against approved PO

### Payment Terms

- **Immediate**: Pay when goods received
- **Net 30/60/90**: Pay within specified days
- **Partial payments**: Pay in installments
      `
    },
    'grn': {
      title: 'Goods Received Notes (GRN)',
      content: `
## Goods Received Notes (GRN)

Record goods received against purchase orders.

### Creating a GRN

1. Go to **GRN** menu
2. Click **Create GRN**
3. Select the Purchase Order
4. For each item, enter:
   - Quantity received
   - Any damaged/rejected quantity
5. Add any additional charges:
   - Freight costs
   - Insurance
   - Custom duties
6. Select which charges to pay immediately vs add to payable
7. Click **Save**

### Partial Receipts

You can receive goods in multiple deliveries:
1. Create GRN for first batch
2. Create another GRN for remaining items
3. PO status shows "Partial" until complete
4. Each GRN updates inventory separately

### GRN with Additional Charges

Additional charges can be:
- **Pay Immediately**: Deducted from bank account now
- **Add to Payable**: Added to supplier balance for later payment

Each charge creates appropriate journal entries.

### GRN Returns

To return goods to supplier:
1. Go to GRN menu
2. Find the original GRN
3. Click "Create Return"
4. Select items to return
5. Enter return quantities
6. Select return reason
7. Submit return

Returns automatically:
- Reduce inventory
- Create credit note
- Update supplier balance

### Verifying GRN

1. Check physical goods against GRN
2. Verify quantities match
3. Check for damage
4. Sign off on GRN
5. Stock is updated in system
      `
    },
    'sales-orders': {
      title: 'Sales Orders & Invoices',
      content: `
## Sales Orders & Invoices

Create and manage customer orders and invoices.

### Creating a Sales Order

1. Go to **Sales Orders**
2. Click **Create Order**
3. Select customer (or create new)
4. Add products:
   - Search by name or SKU
   - Enter quantity
   - Adjust price if needed
   - Apply discounts
5. Add order notes if needed
6. Click **Save**

### Sales Order Status

- **Draft**: Can be edited
- **Confirmed**: Order confirmed, awaiting fulfillment
- **Processing**: Being prepared
- **Shipped**: Dispatched to customer
- **Delivered**: Received by customer
- **Cancelled**: Order cancelled

### Fulfillment Process

1. Confirm order when ready to process
2. Pick items from inventory
3. Pack the order
4. Mark as Shipped (enter tracking if available)
5. Mark as Delivered when customer confirms

### Creating an Invoice

Invoices are automatically created when:
1. Order is confirmed
2. Manual invoice creation from Sales Orders
3. Click "Generate Invoice" on any order

### Invoice Details

Each invoice includes:
- Invoice number (auto-generated)
- Customer details
- Line items with prices
- Subtotal, discounts, taxes
- Total amount due
- Payment status

### Recording Payment

1. Open the invoice
2. Click "Record Payment"
3. Enter:
   - Amount received
   - Payment method
   - Bank account (if applicable)
   - Reference number
4. Payment is recorded and invoice updated

### Sales Returns

To process a return:
1. Open the original order
2. Click "Create Return"
3. Select items being returned
4. Enter quantities and reason
5. Process refund if applicable
6. Stock is automatically updated
      `
    },
    'payments': {
      title: 'Payments',
      content: `
## Payments Management

Track payments for both sales and purchases.

### Recording Customer Payments

1. Go to **Payments** or open the Sales Order
2. Click **Record Payment**
3. Fill in:
   - Payment amount
   - Payment date
   - Payment method (Cash, Bank, Card)
   - Bank account (for deposits)
   - Reference number
4. Click Save

### Recording Supplier Payments

1. Open the Purchase Order
2. Click **Record Payment**
3. Enter payment details
4. Select the bank account for withdrawal
5. Payment reduces accounts payable

### Payment Methods

- **Cash**: Physical cash payment
- **Bank Transfer**: Direct bank payment
- **Card**: Credit/debit card
- **Cheque**: Paper cheque
- **Online**: Digital payment

### Partial Payments

Both sales and purchases support partial payments:
- Make multiple payments against one order
- System tracks paid vs outstanding amount
- Payment status: Unpaid > Partial > Paid

### Payment Reports

View payment history in:
- Payments menu (all payments)
- Customer statement (per customer)
- Supplier statement (per supplier)
- Cash flow report

### Bank Reconciliation

Match payments with bank statements:
1. Go to Accounting > Bank Accounts
2. Select account
3. View transactions
4. Match with bank statement entries
      `
    },
    'woocommerce': {
      title: 'WooCommerce Integration',
      content: `
## WooCommerce Integration

Connect your ERP with WooCommerce store for automatic sync.

### Setting Up WooCommerce

1. Go to **Settings** > **Integrations**
2. Click **WooCommerce**
3. Enter your credentials:
   - **Store URL**: Your WooCommerce store URL (e.g., https://yourstore.com)
   - **Consumer Key**: From WooCommerce > Settings > REST API
   - **Consumer Secret**: From the same location
4. Click **Test Connection**
5. If successful, click **Save**

### Getting WooCommerce API Keys

In your WordPress admin:
1. Go to WooCommerce > Settings > Advanced > REST API
2. Click "Add Key"
3. Enter description (e.g., "ERP Integration")
4. Select User with admin access
5. Permissions: Read/Write
6. Generate API Key
7. Copy the Consumer Key and Secret

### What Syncs Automatically

**From ERP to WooCommerce:**
- Product creation and updates
- Price changes
- Stock quantity updates
- Category changes

**From WooCommerce to ERP:**
- New orders
- Order status updates
- New customers

### Manual Sync

To manually sync:
1. Go to Settings > Integrations
2. Click "Sync Now" for:
   - Products
   - Categories
   - Orders
   - Customers

### Sync Settings

Configure sync behavior:
- **Auto-sync interval**: How often to check for changes
- **Stock sync**: Enable/disable stock updates
- **Price sync**: Enable/disable price updates
- **Order import**: Auto-import new orders

### Troubleshooting Sync Issues

Common issues and solutions:

**Products not syncing:**
- Check API credentials are correct
- Verify product has SKU
- Check WooCommerce error logs

**Stock mismatch:**
- Run manual stock sync
- Check for pending orders
- Verify no duplicate SKUs

**Orders not importing:**
- Check order status in WooCommerce
- Verify API has read permissions
- Check date range settings
      `
    },
    'manufacturing': {
      title: 'Manufacturing',
      content: `
## Manufacturing Module

Manage raw materials, bill of materials, and production work orders.

### Raw Materials

Raw materials are inputs used in manufacturing:

1. Go to **Manufacturing** > **Raw Materials**
2. Click **Add Raw Material**
3. Enter:
   - Material code and name
   - Unit of measure
   - Cost per unit
   - Current stock
   - Reorder level
4. Save

### RM Suppliers

Manage raw material suppliers separately:
1. Go to Manufacturing > RM Suppliers
2. Add supplier details
3. Track supplier-specific pricing

### RM Purchase Orders

Create purchase orders for raw materials:
1. Go to Manufacturing > RM Purchase Orders
2. Select RM supplier
3. Add raw materials needed
4. Submit PO

### RM GRN (Goods Received)

Record raw materials received:
1. Create RM GRN against RM PO
2. Enter quantities received
3. Stock is updated automatically

### Bill of Materials (BOM)

BOM defines what raw materials are needed to make a product:

1. Go to **Manufacturing** > **Bill of Materials**
2. Click **Create BOM**
3. Select the finished product
4. Add raw material components:
   - Select raw material
   - Enter quantity needed
   - Specify unit
5. Set total output quantity
6. Save BOM

Example BOM for "T-Shirt":
- Fabric: 1.5 meters
- Thread: 100 meters
- Buttons: 5 pieces
- Label: 1 piece

### Work Orders

Work orders track production jobs:

1. Go to **Manufacturing** > **Work Orders**
2. Click **Create Work Order**
3. Select product to manufacture
4. Enter quantity to produce
5. System calculates raw materials needed
6. Set scheduled start/end dates
7. Assign to production team
8. Save

### Work Order Status

- **Draft**: Planning stage
- **Confirmed**: Ready to start
- **In Progress**: Production ongoing
- **Completed**: Finished, stock updated
- **Cancelled**: Work order cancelled

### Manufacturing Dashboard

View production KPIs:
- Work orders by status
- Production efficiency
- Raw material usage
- Completed vs planned
      `
    },
    'payroll': {
      title: 'Payroll Management',
      content: `
## Payroll Management

Manage employees, salaries, and payroll processing.

### Departments

Organize employees by department:
1. Go to **Payroll** > **Departments**
2. Click **Add Department**
3. Enter department name
4. Save

### Adding Employees

1. Go to **Payroll** > **Employees**
2. Click **Add Employee**
3. Fill in details:
   - **Employee ID**: Auto-generated (EMP0001, etc.)
   - **Personal Info**: Name, NIC, contact
   - **Employment**: Type (Permanent/Casual/Freelancer/Contract)
   - **Department**: Select department
   - **Salary**: Basic salary, hourly rate
   - **Bank Details**: For salary payment
4. Save

### Employee Types

- **Permanent**: Fixed monthly salary + benefits
- **Casual**: Daily or hourly rate
- **Freelancer**: Task-based payment
- **Contract**: Fixed-term employment

### Salary Structure

Configure salary components:
1. Go to **Payroll** > **Salary Structure**
2. Set statutory rates:
   - EPF Employee: 8%
   - EPF Employer: 12%
   - ETF Employer: 3%
3. Set overtime rates:
   - Weekday OT: 1.25x
   - Weekend OT: 1.5x
4. Add allowances:
   - Transport allowance
   - Meal allowance
   - Other fixed allowances

### Leave Management

1. Go to **Payroll** > **Leave Management**
2. View employee leave balances:
   - Annual leave
   - Sick leave
   - Casual leave
3. Process leave requests:
   - Approve or reject
   - Balance auto-deducts on approval

### Advances & Loans

Issue salary advances:
1. Go to **Payroll** > **Advances**
2. Click **Issue Advance**
3. Select employee
4. Enter amount
5. Set monthly deduction amount
6. System calculates recovery period
7. Deductions auto-apply in payroll

### Task Assignments

For task-based payments:
1. Go to **Payroll** > **Task Assignments**
2. Click **Assign Task**
3. Select employee
4. Enter task details and payment amount
5. Set due date
6. Employee marks complete
7. Manager verifies
8. Payment added to next payroll

### Running Payroll

1. Go to **Payroll** > **Payroll**
2. Click **Run Payroll**
3. Select period (month)
4. System calculates for all employees:
   - Basic salary
   - Allowances
   - Overtime (from attendance)
   - Task payments
   - EPF/ETF deductions
   - Tax (PAYE)
   - Advance deductions
5. Review and adjust if needed
6. Submit for approval
7. Approve payroll
8. Process payment

### Payroll Reports

Generate reports:
- Payslips (per employee)
- EPF/ETF summary
- Department salary breakdown
- Monthly payroll summary
      `
    },
    'attendance': {
      title: 'Attendance Tracking',
      content: `
## Attendance Tracking

Record daily attendance and calculate overtime.

### Attendance Rules

- **Full Day**: 9 hours (8 hrs work + 1 hr break)
- **Half Day**: 5 hours
- **Overtime**: Hours worked beyond 9 hours

### Daily Entry

1. Go to **Payroll** > **Attendance**
2. Select date
3. For each employee:
   - Select status (Present/Absent/Half Day/Late/On Leave)
   - Enter check-in time
   - Enter check-out time
   - Hours auto-calculate
4. Click **Save All**

### Status Types

- **Present**: Full day worked
- **Absent**: Did not come to work
- **Half Day**: Worked half day
- **Late**: Came late (still counts as present)
- **On Leave**: On approved leave

### Overtime Calculation

System automatically calculates OT:
- Work > 9 hours = Overtime
- Example: 10 hours = 1 hour OT
- Weekday OT: 1.25x rate
- Weekend OT: 1.5x rate

### Monthly Report

View attendance summary:
1. Click **Monthly Report** tab
2. Select month
3. See for each employee:
   - Present days
   - Absent days
   - Half days
   - Late days
   - Leave days
   - Total hours
   - Overtime hours

### Payroll Integration

Attendance data flows to payroll:
- Working days for salary calculation
- Overtime hours for OT pay
- Unpaid leave for deductions
      `
    },
    'finance': {
      title: 'Finance & Accounting',
      content: `
## Finance & Accounting

Manage your chart of accounts, journal entries, and financial reporting.

### Chart of Accounts

The chart of accounts is pre-configured with standard accounts:

**Asset Accounts (1xxx):**
- 1100 Cash
- 1200 Bank Account
- 1300 Accounts Receivable
- 1400 Inventory

**Liability Accounts (2xxx):**
- 2100 Accounts Payable
- 2200 EPF Payable
- 2300 ETF Payable

**Equity Accounts (3xxx):**
- 3100 Owner's Capital
- 3200 Retained Earnings

**Revenue Accounts (4xxx):**
- 4100 Sales Revenue
- 4200 Other Income

**Expense Accounts (5xxx):**
- 5100 Cost of Goods Sold
- 5200 Salaries Expense
- 5300 Rent Expense

### Adding New Accounts

1. Go to **Accounting** > **Chart of Accounts**
2. Click **Add Account**
3. Enter:
   - Account code (follow numbering system)
   - Account name
   - Category (Asset/Liability/Equity/Revenue/Expense)
   - Sub-category
4. Save

### Bank Accounts

Set up your bank accounts:
1. Go to **Accounting** > **Bank Accounts**
2. Click **Add Bank Account**
3. Enter:
   - Bank name
   - Account number
   - Account type
   - Opening balance
   - Link to chart account
4. Save

### Journal Entries

Most journal entries are created automatically:
- Sales create revenue entries
- Purchases create expense entries
- Payments update bank balances
- Payroll creates salary entries

For manual entries:
1. Go to **Accounting** > **Journal Entries**
2. Click **New Entry**
3. Select date and description
4. Add debit and credit lines (must balance)
5. Save

### Automatic Journal Entries

The system creates entries for:

**Sales Order:**
- Debit: Accounts Receivable
- Credit: Sales Revenue
- Debit: Cost of Goods Sold
- Credit: Inventory

**Purchase Payment:**
- Debit: Inventory
- Credit: Bank/Cash

**Payroll:**
- Debit: Salary Expense
- Credit: Bank (net pay)
- Credit: EPF Payable
- Credit: Tax Payable

### Financial Period

Close periods to prevent changes:
1. Go to Accounting > Settings
2. Set financial year start
3. Close completed periods
4. Closed periods cannot be modified

### Audit Trail

All financial transactions are logged:
- Who created/modified
- When changes were made
- Previous values
      `
    },
    'reports': {
      title: 'Reports',
      content: `
## Reports

Generate financial and operational reports.

### Financial Reports

**Profit & Loss Statement:**
1. Go to **Reports** > **Profit & Loss**
2. Select date range
3. View:
   - Total Revenue
   - Cost of Goods Sold
   - Gross Profit
   - Operating Expenses
   - Net Profit

**Balance Sheet:**
1. Go to **Reports** > **Balance Sheet**
2. Select as-of date
3. View:
   - Assets (Current & Fixed)
   - Liabilities
   - Equity
   - Verify: Assets = Liabilities + Equity

**Cash Flow Statement:**
1. Go to **Reports** > **Cash Flow**
2. Select period
3. View:
   - Operating activities
   - Investing activities
   - Financing activities
   - Net cash change

**Trial Balance:**
1. Go to **Reports** > **Trial Balance**
2. View all accounts with balances
3. Verify debits equal credits

### Sales Reports

- Sales by period
- Sales by customer
- Sales by product
- Top selling products
- Sales trends

### Purchase Reports

- Purchases by supplier
- Outstanding payables
- Purchase history
- Supplier performance

### Inventory Reports

- Stock valuation
- Stock movement
- Low stock report
- Dead stock report

### Payroll Reports

- Monthly payroll summary
- EPF/ETF contribution report
- Department salary report
- Individual payslips

### Exporting Reports

All reports can be exported:
- PDF format
- Excel format
- Print directly

### Custom Date Ranges

Most reports support:
- Today
- This week
- This month
- This year
- Custom date range
      `
    },
    'settings': {
      title: 'System Settings',
      content: `
## System Settings

Configure your ERP system settings.

### Company Settings

1. Go to **Settings** > **Company**
2. Update:
   - Company name
   - Address
   - Phone/Email
   - Tax registration number
   - Logo

### User Preferences

Each user can set:
- Language preference
- Date format
- Number format
- Default dashboard view

### Invoice Settings

Configure invoice appearance:
- Invoice prefix (e.g., INV-)
- Starting number
- Terms and conditions
- Bank details
- Footer notes

### Email Settings

For sending invoices/reports:
- SMTP server details
- Sender email
- Email templates

### Backup Settings

Protect your data:
- Automatic daily backups
- Manual backup option
- Backup retention period

### Integration Settings

Manage external connections:
- WooCommerce
- Payment gateways
- SMS providers
      `
    },
    'faq': {
      title: 'FAQ & Troubleshooting',
      content: `
## Frequently Asked Questions

### General

**Q: How do I reset my password?**
A: Click "Forgot Password" on login page, enter your email, and follow the reset link.

**Q: Can multiple users work simultaneously?**
A: Yes, the system supports multiple concurrent users.

**Q: Is my data backed up?**
A: Yes, automatic backups run daily.

### Inventory

**Q: Why is my stock showing negative?**
A: This happens when sales exceed available stock. Check for:
- Pending GRNs not yet received
- Incorrect opening stock
- Missing stock adjustments

**Q: How do I correct wrong stock?**
A: Go to Inventory > Find product > Adjust Stock > Enter correct quantity with reason.

### Sales & Invoices

**Q: Can I edit a paid invoice?**
A: No, paid invoices cannot be edited. Create a credit note for corrections.

**Q: How do I give a discount?**
A: On the sales order, enter discount percentage or amount before saving.

### Purchases & GRN

**Q: Can I receive more than ordered?**
A: Yes, you can receive extra quantities. The system will record the variance.

**Q: How do I return goods to supplier?**
A: Open the GRN > Click "Create Return" > Select items > Submit.

### Payroll

**Q: How is overtime calculated?**
A: OT is calculated for hours worked beyond 9 hours (normal duty).
   - Weekday OT: 1.25x hourly rate
   - Weekend OT: 1.5x hourly rate

**Q: When are advances deducted?**
A: Automatically in each payroll run until fully recovered.

### Finance

**Q: Why doesn't my Balance Sheet balance?**
A: Check for:
- Unbalanced journal entries
- Missing transactions
- Incorrect account categories

**Q: How do I correct a wrong journal entry?**
A: Create a reversing entry, then create the correct entry.

### WooCommerce

**Q: Products not syncing to WooCommerce?**
A: Verify:
- API credentials are correct
- Product has a SKU
- WooCommerce is accessible

**Q: Orders not importing?**
A: Check:
- API has read permissions
- Order date is within sync range
- No duplicate order numbers

### Getting Help

If you can't find the answer:
1. Check this documentation
2. Contact your system administrator
3. Email support for assistance
      `
    }
  };

  useEffect(() => {
    const handleScroll = () => {
      setShowBackToTop(window.scrollY > 300);
      
      // Update active section based on scroll position
      const sections = document.querySelectorAll('[data-section]');
      sections.forEach(section => {
        const rect = section.getBoundingClientRect();
        if (rect.top <= 100 && rect.bottom >= 100) {
          setActiveSection(section.getAttribute('data-section'));
        }
      });
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const scrollToSection = (sectionId) => {
    const element = document.getElementById(sectionId);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' });
      setActiveSection(sectionId);
    }
  };

  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // Filter content based on search
  const filteredSections = searchQuery
    ? tableOfContents.filter(section => {
        const content = documentationContent[section.id];
        return (
          section.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
          content.content.toLowerCase().includes(searchQuery.toLowerCase())
        );
      })
    : tableOfContents;

  const highlightText = (text, query) => {
    if (!query) return text;
    const parts = text.split(new RegExp(`(${query})`, 'gi'));
    return parts.map((part, i) => 
      part.toLowerCase() === query.toLowerCase() 
        ? <mark key={i} className="bg-yellow-200">{part}</mark> 
        : part
    );
  };

  return (
    <div className="min-h-screen bg-gray-50" data-testid="documentation-page">
      {/* Header */}
      <div className="bg-white border-b sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <BookOpen className="h-8 w-8 text-blue-600" />
              <div>
                <h1 className="text-xl font-bold text-gray-900">Documentation</h1>
                <p className="text-sm text-gray-500">Learn how to use the ERP system</p>
              </div>
            </div>
            <div className="relative w-80">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                type="text"
                placeholder="Search documentation..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
                data-testid="doc-search"
              />
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-6">
        <div className="flex gap-6">
          {/* Sidebar - Table of Contents */}
          <div className="w-64 flex-shrink-0">
            <div className="sticky top-24">
              <Card>
                <CardContent className="p-4">
                  <h3 className="font-semibold text-gray-900 mb-3">Contents</h3>
                  <nav className="space-y-1">
                    {filteredSections.map(section => {
                      const Icon = section.icon;
                      return (
                        <button
                          key={section.id}
                          onClick={() => scrollToSection(section.id)}
                          className={`w-full flex items-center gap-2 px-3 py-2 text-sm rounded-md transition-colors text-left ${
                            activeSection === section.id
                              ? 'bg-blue-50 text-blue-700 font-medium'
                              : 'text-gray-600 hover:bg-gray-100'
                          }`}
                          data-testid={`toc-${section.id}`}
                        >
                          <Icon className="h-4 w-4 flex-shrink-0" />
                          <span className="truncate">{section.title}</span>
                          {activeSection === section.id && (
                            <ChevronRight className="h-4 w-4 ml-auto" />
                          )}
                        </button>
                      );
                    })}
                  </nav>
                </CardContent>
              </Card>
            </div>
          </div>

          {/* Main Content */}
          <div className="flex-1 min-w-0" ref={contentRef}>
            {filteredSections.length === 0 ? (
              <Card>
                <CardContent className="p-8 text-center">
                  <Search className="h-12 w-12 mx-auto text-gray-400 mb-4" />
                  <h3 className="text-lg font-medium text-gray-900">No results found</h3>
                  <p className="text-gray-500 mt-2">Try searching with different keywords</p>
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-8">
                {filteredSections.map(section => {
                  const content = documentationContent[section.id];
                  const Icon = section.icon;
                  return (
                    <Card 
                      key={section.id} 
                      id={section.id}
                      data-section={section.id}
                      className="scroll-mt-24"
                    >
                      <CardContent className="p-6">
                        <div className="flex items-center gap-3 mb-4 pb-4 border-b">
                          <div className="p-2 bg-blue-100 rounded-lg">
                            <Icon className="h-6 w-6 text-blue-600" />
                          </div>
                          <h2 className="text-2xl font-bold text-gray-900">
                            {highlightText(content.title, searchQuery)}
                          </h2>
                        </div>
                        <div 
                          className="prose prose-slate max-w-none
                            prose-headings:text-gray-900 prose-headings:font-semibold
                            prose-h2:text-xl prose-h2:mt-6 prose-h2:mb-4
                            prose-h3:text-lg prose-h3:mt-4 prose-h3:mb-2
                            prose-p:text-gray-600 prose-p:leading-relaxed
                            prose-li:text-gray-600
                            prose-strong:text-gray-900
                            prose-code:bg-gray-100 prose-code:px-1 prose-code:rounded
                          "
                          dangerouslySetInnerHTML={{ 
                            __html: content.content
                              // First handle inline bold (anywhere in text)
                              .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                              // Then handle headers
                              .replace(/^## (.*$)/gm, '<h2>$1</h2>')
                              .replace(/^### (.*$)/gm, '<h3>$1</h3>')
                              // Handle lists
                              .replace(/^- (.*$)/gm, '<li>$1</li>')
                              .replace(/^\d+\. (.*$)/gm, '<li>$1</li>')
                              // Wrap consecutive list items
                              .replace(/(<li>.*<\/li>\n?)+/g, (match) => `<ul>${match}</ul>`)
                              // Handle paragraphs (lines that aren't already HTML)
                              .split('\n')
                              .map(line => {
                                line = line.trim();
                                if (!line) return '';
                                if (line.startsWith('<')) return line;
                                return `<p>${line}</p>`;
                              })
                              .join('\n')
                              // Clean up nested ul tags
                              .replace(/<\/ul>\s*<ul>/g, '')
                          }}
                        />
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Back to Top Button */}
      {showBackToTop && (
        <Button
          onClick={scrollToTop}
          className="fixed bottom-6 right-6 rounded-full shadow-lg"
          size="icon"
          data-testid="back-to-top"
        >
          <ChevronUp className="h-5 w-5" />
        </Button>
      )}
    </div>
  );
};

export default Documentation;
