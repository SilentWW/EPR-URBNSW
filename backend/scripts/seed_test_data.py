#!/usr/bin/env python3
"""
Comprehensive Test Data Seeder for E1 ERP System
Creates all necessary test data for full system testing
"""
import asyncio
import os
import uuid
import random
from datetime import datetime, timezone, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# MongoDB connection
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = 'test_database'

def generate_id():
    return str(uuid.uuid4())

def get_timestamp():
    return datetime.now(timezone.utc).isoformat()

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

async def seed_database():
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    print("=" * 70)
    print("🌱 E1 ERP SYSTEM - COMPREHENSIVE TEST DATA SEEDER")
    print("=" * 70)
    print()
    
    # ============== 1. CREATE COMPANY & USER ==============
    print("👤 Creating Company & User...")
    
    company_id = generate_id()
    company = {
        "id": company_id,
        "name": "URBAN STREETWEARS (PVT) LTD",
        "address": "123 Fashion Street, Colombo 03",
        "phone": "+94 11 234 5678",
        "email": "info@urbanstreetwears.com",
        "currency": "LKR",
        "created_at": get_timestamp()
    }
    await db.companies.insert_one(company)
    print(f"  ✅ Company: {company['name']}")
    
    user_id = generate_id()
    user = {
        "id": user_id,
        "email": "lahiruraja97@gmail.com",
        "password": hash_password("password123"),
        "full_name": "Lahiru Rajapaksha",
        "role": "admin",
        "company_id": company_id,
        "status": "approved",
        "created_at": get_timestamp()
    }
    await db.users.insert_one(user)
    print(f"  ✅ User: {user['email']} (admin)")
    
    # ============== 2. CREATE DEPARTMENTS ==============
    print("\n📁 Creating Departments...")
    
    departments_data = [
        ("Executive / Leadership", "Decision-making level of the company"),
        ("Design & Product Development", "Heart of the clothing brand"),
        ("Production & Manufacturing", "Garment production and quality control"),
        ("Marketing & Brand", "Brand identity and marketing campaigns"),
        ("E-Commerce & Sales", "Online store and sales management"),
        ("Logistics & Inventory", "Stock management and order fulfillment"),
        ("Customer Experience", "Customer support and satisfaction"),
        ("Finance & Accounting", "Financial management and records"),
        ("Human Resources", "Employee recruitment and management"),
        ("Legal & Compliance", "Legal matters and regulatory compliance"),
    ]
    
    departments = {}
    for name, desc in departments_data:
        dept_id = generate_id()
        dept = {
            "id": dept_id,
            "company_id": company_id,
            "name": name,
            "description": desc,
            "created_at": get_timestamp()
        }
        await db.departments.insert_one(dept)
        departments[name] = dept_id
        print(f"  ✅ {name}")
    
    # ============== 3. CREATE DESIGNATIONS ==============
    print("\n👔 Creating Designations...")
    
    designations_data = [
        ("Founder / Creative Director", "Executive / Leadership", "admin", 10),
        ("CEO", "Executive / Leadership", "admin", 10),
        ("Operations Director", "Executive / Leadership", "manager", 9),
        ("Head of Design", "Design & Product Development", "manager", 8),
        ("Fashion Designer", "Design & Product Development", "employee", 6),
        ("Graphic Designer", "Design & Product Development", "employee", 5),
        ("Production Manager", "Production & Manufacturing", "manager", 7),
        ("Quality Control Manager", "Production & Manufacturing", "manager", 6),
        ("Brand Manager", "Marketing & Brand", "manager", 7),
        ("Social Media Manager", "Marketing & Brand", "employee", 5),
        ("E-Commerce Manager", "E-Commerce & Sales", "manager", 7),
        ("Sales Manager", "E-Commerce & Sales", "manager", 7),
        ("Inventory Manager", "Logistics & Inventory", "store", 6),
        ("Fulfillment Coordinator", "Logistics & Inventory", "store", 4),
        ("Finance Manager", "Finance & Accounting", "accountant", 7),
        ("Accountant", "Finance & Accounting", "accountant", 5),
        ("HR Manager", "Human Resources", "manager", 7),
        ("HR Executive", "Human Resources", "employee", 5),
    ]
    
    designations = {}
    for name, dept_name, role, level in designations_data:
        desig_id = generate_id()
        desig = {
            "id": desig_id,
            "company_id": company_id,
            "name": name,
            "department_id": departments.get(dept_name),
            "role": role,
            "level": level,
            "is_active": True,
            "created_at": get_timestamp()
        }
        await db.designations.insert_one(desig)
        designations[name] = desig_id
    print(f"  ✅ Created {len(designations_data)} designations")
    
    # ============== 4. CREATE CHART OF ACCOUNTS ==============
    print("\n📊 Creating Chart of Accounts...")
    
    accounts_data = [
        # Assets (1xxx)
        ("1000", "Cash", "asset", 0),
        ("1100", "Petty Cash", "asset", 0),
        ("1200", "Bank - Commercial Bank", "asset", 0),
        ("1300", "Accounts Receivable", "asset", 0),
        ("1400", "Inventory", "asset", 0),
        ("1500", "Raw Materials", "asset", 0),
        # Liabilities (2xxx)
        ("2000", "Accounts Payable", "liability", 0),
        ("2100", "Salaries Payable", "liability", 0),
        ("2200", "Tax Payable", "liability", 0),
        ("2300", "Bank Loan", "liability", 0),
        # Equity (3xxx)
        ("3000", "Owner's Capital", "equity", 500000),
        ("3100", "Retained Earnings", "equity", 0),
        # Income (4xxx)
        ("4000", "Sales Revenue", "income", 0),
        ("4100", "Service Revenue", "income", 0),
        ("4200", "Other Income", "income", 0),
        # Expenses (5xxx/6xxx)
        ("5000", "Cost of Goods Sold", "expense", 0),
        ("6000", "Salaries Expense", "expense", 0),
        ("6100", "Rent Expense", "expense", 0),
        ("6200", "Utilities Expense", "expense", 0),
        ("6300", "Marketing Expense", "expense", 0),
        ("6400", "Office Supplies", "expense", 0),
        ("6500", "Transportation", "expense", 0),
    ]
    
    accounts = {}
    for code, name, acc_type, balance in accounts_data:
        acc_id = generate_id()
        acc = {
            "id": acc_id,
            "company_id": company_id,
            "code": code,
            "name": name,
            "type": acc_type,
            "balance": balance,
            "is_active": True,
            "created_at": get_timestamp()
        }
        await db.accounts.insert_one(acc)
        accounts[code] = acc_id
    print(f"  ✅ Created {len(accounts_data)} accounts")
    
    # ============== 5. CREATE BANK ACCOUNTS ==============
    print("\n🏦 Creating Bank Accounts...")
    
    bank_accounts_data = [
        ("Main Cash Account", "cash", 100000, "1000"),
        ("Commercial Bank - Current", "bank", 500000, "1200"),
        ("Petty Cash", "cash", 25000, "1100"),
    ]
    
    bank_accounts = {}
    for name, acc_type, balance, linked_code in bank_accounts_data:
        ba_id = generate_id()
        ba = {
            "id": ba_id,
            "company_id": company_id,
            "name": name,
            "account_type": acc_type,
            "bank_name": "Commercial Bank" if acc_type == "bank" else None,
            "account_number": f"100{random.randint(1000000, 9999999)}" if acc_type == "bank" else None,
            "opening_balance": balance,
            "current_balance": balance,
            "linked_account_id": accounts.get(linked_code),
            "is_active": True,
            "created_at": get_timestamp()
        }
        await db.bank_accounts.insert_one(ba)
        bank_accounts[name] = ba_id
        print(f"  ✅ {name}: LKR {balance:,.0f}")
    
    # ============== 6. CREATE SUPPLIERS ==============
    print("\n🏭 Creating Suppliers...")
    
    suppliers_data = [
        ("Fabric World Lanka", "No. 45, Pettah, Colombo", "+94 11 234 0001", "Fabrics & Textiles"),
        ("Print Masters", "Industrial Zone, Ja-Ela", "+94 11 234 0002", "Printing Services"),
        ("Thread & Needle Co", "Moratuwa Industrial Area", "+94 11 234 0003", "Accessories"),
        ("PackPro Solutions", "Kelaniya", "+94 11 234 0004", "Packaging Materials"),
        ("Label King", "Colombo 10", "+94 11 234 0005", "Labels & Tags"),
    ]
    
    suppliers = {}
    for name, address, phone, category in suppliers_data:
        sup_id = generate_id()
        sup = {
            "id": sup_id,
            "company_id": company_id,
            "name": name,
            "address": address,
            "phone": phone,
            "email": f"{name.lower().replace(' ', '')}@example.com",
            "category": category,
            "payment_terms": random.choice([15, 30, 45]),
            "balance": 0,
            "created_at": get_timestamp()
        }
        await db.suppliers.insert_one(sup)
        suppliers[name] = sup_id
        print(f"  ✅ {name}")
    
    # ============== 7. CREATE CUSTOMERS ==============
    print("\n👥 Creating Customers...")
    
    customers_data = [
        ("Fashion Hub Colombo", "Colombo 03", "+94 77 123 4501", "Retailer"),
        ("Style Station", "Kandy", "+94 77 123 4502", "Retailer"),
        ("Urban Outfitters LK", "Negombo", "+94 77 123 4503", "Wholesaler"),
        ("Trend Setters", "Galle", "+94 77 123 4504", "Retailer"),
        ("Online Fashion Store", "Colombo 05", "+94 77 123 4505", "E-Commerce"),
    ]
    
    customers = {}
    for name, address, phone, cust_type in customers_data:
        cust_id = generate_id()
        cust = {
            "id": cust_id,
            "company_id": company_id,
            "name": name,
            "address": address,
            "phone": phone,
            "email": f"orders@{name.lower().replace(' ', '')}.com",
            "customer_type": cust_type,
            "credit_limit": random.choice([100000, 250000, 500000]),
            "balance": 0,
            "created_at": get_timestamp()
        }
        await db.customers.insert_one(cust)
        customers[name] = cust_id
        print(f"  ✅ {name}")
    
    # ============== 8. CREATE PRODUCTS ==============
    print("\n👕 Creating Products...")
    
    products_data = [
        ("URBN-TS001", "Classic Logo Tee", "T-Shirts", 850, 2500, 50),
        ("URBN-TS002", "Streetwear Graphic Tee", "T-Shirts", 950, 2800, 40),
        ("URBN-TS003", "Oversized Drop Shoulder", "T-Shirts", 1100, 3200, 35),
        ("URBN-HD001", "Essential Hoodie", "Hoodies", 1800, 4500, 25),
        ("URBN-HD002", "Zip-Up Hoodie", "Hoodies", 2000, 5000, 20),
        ("URBN-JK001", "Denim Jacket", "Jackets", 2500, 6500, 15),
        ("URBN-PT001", "Cargo Pants", "Pants", 1500, 3800, 30),
        ("URBN-PT002", "Jogger Pants", "Pants", 1200, 3200, 35),
        ("URBN-CP001", "Snapback Cap", "Accessories", 450, 1500, 60),
        ("URBN-BG001", "Canvas Tote Bag", "Accessories", 650, 1800, 40),
        ("URBN-SK001", "Crew Socks (3-Pack)", "Accessories", 350, 950, 100),
        ("URBN-SH001", "Shorts - Summer Edition", "Shorts", 900, 2400, 45),
    ]
    
    products = {}
    for sku, name, category, cost, price, stock in products_data:
        prod_id = generate_id()
        prod = {
            "id": prod_id,
            "company_id": company_id,
            "sku": sku,
            "name": name,
            "category": category,
            "description": f"High-quality {name.lower()} from Urban Streetwears",
            "cost_price": cost,
            "regular_price": price,
            "sale_price": None,
            "stock_quantity": stock,
            "low_stock_threshold": 10,
            "is_active": True,
            "created_at": get_timestamp()
        }
        await db.products.insert_one(prod)
        products[sku] = {"id": prod_id, "name": name, "cost": cost, "price": price}
        print(f"  ✅ {sku}: {name} (Stock: {stock})")
    
    # ============== 9. CREATE EMPLOYEES ==============
    print("\n👨‍💼 Creating Employees...")
    
    employees_data = [
        ("EMP001", "Lahiru", "Rajapaksha", "CEO", "Executive / Leadership", 150000, "permanent"),
        ("EMP002", "Kasun", "Perera", "Production Manager", "Production & Manufacturing", 85000, "permanent"),
        ("EMP003", "Nimali", "Fernando", "Finance Manager", "Finance & Accounting", 95000, "permanent"),
        ("EMP004", "Saman", "Silva", "Fashion Designer", "Design & Product Development", 65000, "permanent"),
        ("EMP005", "Priya", "Jayawardena", "HR Manager", "Human Resources", 75000, "permanent"),
        ("EMP006", "Nuwan", "Bandara", "Inventory Manager", "Logistics & Inventory", 55000, "permanent"),
        ("EMP007", "Dilini", "Wijesinghe", "Sales Manager", "E-Commerce & Sales", 70000, "permanent"),
        ("EMP008", "Chamara", "Rathnayake", "Graphic Designer", "Design & Product Development", 50000, "permanent"),
        ("EMP009", "Tharushi", "Mendis", "Accountant", "Finance & Accounting", 45000, "permanent"),
        ("EMP010", "Ashan", "Gunasekara", "Quality Control Manager", "Production & Manufacturing", 60000, "permanent"),
    ]
    
    employees = {}
    for emp_id, first, last, desig, dept, salary, emp_type in employees_data:
        eid = generate_id()
        emp = {
            "id": eid,
            "company_id": company_id,
            "employee_id": emp_id,
            "first_name": first,
            "last_name": last,
            "email": f"{first.lower()}.{last.lower()}@urbanstreetwears.com",
            "phone": f"+94 77 {random.randint(1000000, 9999999)}",
            "department_id": departments.get(dept),
            "designation_id": designations.get(desig),
            "designation": desig,
            "employee_type": emp_type,
            "payment_frequency": "monthly",
            "basic_salary": salary,
            "join_date": (datetime.now() - timedelta(days=random.randint(30, 730))).strftime("%Y-%m-%d"),
            "status": "active",
            "created_at": get_timestamp()
        }
        await db.employees.insert_one(emp)
        employees[emp_id] = {"id": eid, "name": f"{first} {last}", "salary": salary}
        print(f"  ✅ {emp_id}: {first} {last} - {desig}")
        
        # Create leave balance
        leave_balance = {
            "id": generate_id(),
            "company_id": company_id,
            "employee_id": eid,
            "annual": 14,
            "sick": 7,
            "casual": 7,
            "used_annual": random.randint(0, 5),
            "used_sick": random.randint(0, 2),
            "used_casual": random.randint(0, 3),
            "year": 2026,
            "created_at": get_timestamp()
        }
        await db.leave_balances.insert_one(leave_balance)
    
    # ============== 10. CREATE ALLOWANCES & DEDUCTIONS ==============
    print("\n💰 Creating Allowances & Deductions...")
    
    allowances = [
        {"name": "Transport Allowance", "type": "fixed", "value": 5000, "is_taxable": False},
        {"name": "Meal Allowance", "type": "fixed", "value": 3000, "is_taxable": False},
        {"name": "Performance Bonus", "type": "percentage", "value": 10, "is_taxable": True},
    ]
    
    for allow in allowances:
        allow["id"] = generate_id()
        allow["company_id"] = company_id
        allow["created_at"] = get_timestamp()
        await db.allowances.insert_one(allow)
        print(f"  ✅ Allowance: {allow['name']}")
    
    deductions = [
        {"name": "EPF (Employee)", "type": "percentage", "value": 8, "is_statutory": True},
        {"name": "ETF", "type": "percentage", "value": 3, "is_statutory": True},
        {"name": "PAYE Tax", "type": "percentage", "value": 6, "is_statutory": True},
    ]
    
    for ded in deductions:
        ded["id"] = generate_id()
        ded["company_id"] = company_id
        ded["created_at"] = get_timestamp()
        await db.deductions.insert_one(ded)
        print(f"  ✅ Deduction: {ded['name']}")
    
    # ============== 11. CREATE PURCHASE ORDERS & GRNs ==============
    print("\n📦 Creating Purchase Orders & GRNs...")
    
    po_number = 1
    grn_number = 1
    supplier_list = list(suppliers.items())
    
    for i in range(5):
        sup_name, sup_id = supplier_list[i % len(supplier_list)]
        po_id = generate_id()
        
        # Select random products for PO
        po_products = random.sample(list(products.items()), random.randint(2, 4))
        po_items = []
        po_total = 0
        
        for sku, prod_info in po_products:
            qty = random.randint(20, 50)
            line_total = prod_info["cost"] * qty
            po_total += line_total
            po_items.append({
                "product_id": prod_info["id"],
                "product_name": prod_info["name"],
                "sku": sku,
                "quantity": qty,
                "unit_price": prod_info["cost"],
                "total": line_total
            })
        
        po = {
            "id": po_id,
            "company_id": company_id,
            "po_number": f"PO-2026-{po_number:04d}",
            "supplier_id": sup_id,
            "supplier_name": sup_name,
            "items": po_items,
            "subtotal": po_total,
            "tax": po_total * 0.08,
            "total": po_total * 1.08,
            "status": "received",
            "payment_status": random.choice(["pending", "partial", "paid"]),
            "paid_amount": random.choice([0, po_total * 0.5, po_total * 1.08]),
            "notes": f"Purchase order for {sup_name}",
            "created_at": (datetime.now() - timedelta(days=random.randint(5, 30))).isoformat()
        }
        await db.purchase_orders.insert_one(po)
        print(f"  ✅ PO-2026-{po_number:04d} from {sup_name}")
        po_number += 1
        
        # Create GRN for this PO
        grn_id = generate_id()
        grn = {
            "id": grn_id,
            "company_id": company_id,
            "grn_number": f"GRN-2026-{grn_number:04d}",
            "po_id": po_id,
            "po_number": po["po_number"],
            "supplier_id": sup_id,
            "supplier_name": sup_name,
            "items": po_items,
            "total_cost": po_total,
            "status": "completed",
            "received_by": user_id,
            "received_date": get_timestamp(),
            "created_at": get_timestamp()
        }
        await db.grns.insert_one(grn)
        print(f"  ✅ GRN-2026-{grn_number:04d}")
        grn_number += 1
    
    # ============== 12. CREATE SALES ORDERS ==============
    print("\n🛒 Creating Sales Orders...")
    
    so_number = 1
    customer_list = list(customers.items())
    
    for i in range(8):
        cust_name, cust_id = customer_list[i % len(customer_list)]
        so_id = generate_id()
        
        # Select random products for SO
        so_products = random.sample(list(products.items()), random.randint(1, 4))
        so_items = []
        so_total = 0
        
        for sku, prod_info in so_products:
            qty = random.randint(5, 20)
            line_total = prod_info["price"] * qty
            so_total += line_total
            so_items.append({
                "product_id": prod_info["id"],
                "product_name": prod_info["name"],
                "sku": sku,
                "quantity": qty,
                "unit_price": prod_info["price"],
                "total": line_total
            })
        
        so = {
            "id": so_id,
            "company_id": company_id,
            "order_number": f"SO-2026-{so_number:04d}",
            "customer_id": cust_id,
            "customer_name": cust_name,
            "items": so_items,
            "subtotal": so_total,
            "discount": random.choice([0, so_total * 0.05, so_total * 0.1]),
            "tax": so_total * 0.08,
            "total": so_total * 1.08,
            "status": random.choice(["pending", "processing", "shipped", "delivered"]),
            "payment_status": random.choice(["pending", "partial", "paid"]),
            "paid_amount": random.choice([0, so_total * 0.5, so_total * 1.08]),
            "notes": f"Order from {cust_name}",
            "created_at": (datetime.now() - timedelta(days=random.randint(1, 20))).isoformat()
        }
        await db.sales_orders.insert_one(so)
        print(f"  ✅ SO-2026-{so_number:04d} - {cust_name} (LKR {so_total:,.0f})")
        so_number += 1
    
    # ============== 13. CREATE QUICK TRANSACTIONS ==============
    print("\n💳 Creating Quick Transactions (Journal Entries)...")
    
    transactions = [
        ("Revenue Receipt", "4000", "1200", 125000, "Sales revenue - Week 1"),
        ("Revenue Receipt", "4000", "1200", 95000, "Sales revenue - Week 2"),
        ("Expense Payment", "6100", "1200", 75000, "Monthly rent payment"),
        ("Expense Payment", "6200", "1200", 15000, "Electricity bill"),
        ("Expense Payment", "6300", "1200", 25000, "Social media advertising"),
        ("Expense Payment", "6400", "1000", 8500, "Office supplies"),
        ("Expense Payment", "6500", "1000", 12000, "Courier charges"),
        ("Revenue Receipt", "4100", "1000", 35000, "Design consultation fee"),
    ]
    
    for i, (trans_type, debit_code, credit_code, amount, desc) in enumerate(transactions):
        je_id = generate_id()
        je = {
            "id": je_id,
            "company_id": company_id,
            "entry_number": f"JE-2026-{i+1:04d}",
            "date": (datetime.now() - timedelta(days=random.randint(1, 25))).strftime("%Y-%m-%d"),
            "description": desc,
            "lines": [
                {"account_id": accounts[debit_code], "account_code": debit_code, "debit": amount if trans_type == "Expense Payment" else 0, "credit": amount if trans_type == "Revenue Receipt" else 0},
                {"account_id": accounts[credit_code], "account_code": credit_code, "debit": amount if trans_type == "Revenue Receipt" else 0, "credit": amount if trans_type == "Expense Payment" else 0},
            ],
            "total_debit": amount,
            "total_credit": amount,
            "status": "posted",
            "created_by": user_id,
            "created_at": get_timestamp()
        }
        await db.journal_entries.insert_one(je)
        print(f"  ✅ {trans_type}: {desc} (LKR {amount:,.0f})")
    
    # ============== 14. CREATE EMPLOYEE ADVANCES (LOANS) ==============
    print("\n💵 Creating Employee Advances/Loans...")
    
    advances_data = [
        ("EMP002", 50000, 5000, "Personal loan"),
        ("EMP004", 25000, 2500, "Medical emergency"),
        ("EMP006", 30000, 3000, "Education loan"),
    ]
    
    for emp_code, amount, monthly_ded, reason in advances_data:
        emp_info = employees[emp_code]
        adv_id = generate_id()
        adv = {
            "id": adv_id,
            "company_id": company_id,
            "employee_id": emp_info["id"],
            "employee_name": emp_info["name"],
            "amount": amount,
            "remaining_balance": amount - monthly_ded * 2,  # Assume 2 months paid
            "monthly_deduction": monthly_ded,
            "type": "loan",
            "reason": reason,
            "status": "active",
            "disbursement_date": (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d"),
            "created_at": get_timestamp()
        }
        await db.employee_advances.insert_one(adv)
        print(f"  ✅ {emp_info['name']}: LKR {amount:,.0f} ({reason})")
    
    # ============== 15. CREATE LEAVE REQUESTS ==============
    print("\n🏖️ Creating Leave Requests...")
    
    leave_data = [
        ("EMP003", "annual", "2026-03-15", "2026-03-18", "Family vacation", "approved"),
        ("EMP005", "sick", "2026-03-10", "2026-03-11", "Medical appointment", "approved"),
        ("EMP007", "casual", "2026-03-20", "2026-03-20", "Personal work", "pending"),
        ("EMP008", "annual", "2026-04-01", "2026-04-05", "Holiday trip", "pending"),
    ]
    
    for emp_code, leave_type, start, end, reason, status in leave_data:
        emp_info = employees[emp_code]
        leave_id = generate_id()
        leave = {
            "id": leave_id,
            "company_id": company_id,
            "employee_id": emp_info["id"],
            "employee_name": emp_info["name"],
            "leave_type": leave_type,
            "start_date": start,
            "end_date": end,
            "days": (datetime.strptime(end, "%Y-%m-%d") - datetime.strptime(start, "%Y-%m-%d")).days + 1,
            "reason": reason,
            "status": status,
            "approved_by": user_id if status == "approved" else None,
            "created_at": get_timestamp()
        }
        await db.leave_requests.insert_one(leave)
        print(f"  ✅ {emp_info['name']}: {leave_type} ({start} to {end}) - {status.upper()}")
    
    # ============== 16. CREATE TASK CATEGORIES ==============
    print("\n📋 Creating Task Categories...")
    
    categories = [
        ("Production", "#3B82F6", "Manufacturing and production tasks"),
        ("Design", "#8B5CF6", "Design and creative tasks"),
        ("Quality Control", "#EF4444", "QC and inspection tasks"),
        ("Packing", "#10B981", "Packing and shipping tasks"),
        ("Admin", "#F59E0B", "Administrative tasks"),
    ]
    
    task_categories = {}
    for name, color, desc in categories:
        cat_id = generate_id()
        cat = {
            "id": cat_id,
            "company_id": company_id,
            "name": name,
            "color": color,
            "description": desc,
            "created_at": get_timestamp()
        }
        await db.task_categories.insert_one(cat)
        task_categories[name] = cat_id
        print(f"  ✅ {name}")
    
    # ============== 17. CREATE TASK ASSIGNMENTS ==============
    print("\n✅ Creating Task Assignments...")
    
    tasks_data = [
        ("EMP004", "Design new summer collection", "Design", "high", 5000, "completed", "verified"),
        ("EMP002", "Oversee batch production #45", "Production", "high", 0, "completed", "verified"),
        ("EMP010", "Quality check - T-shirt batch", "Quality Control", "medium", 2000, "completed", "completed"),
        ("EMP006", "Inventory stock count", "Admin", "medium", 1500, "in_progress", None),
        ("EMP008", "Create social media graphics", "Design", "low", 3000, "assigned", None),
        ("EMP002", "Machine maintenance schedule", "Production", "medium", 0, "in_progress", None),
    ]
    
    for emp_code, title, category, priority, amount, status, verified in tasks_data:
        emp_info = employees[emp_code]
        task_id = generate_id()
        task = {
            "id": task_id,
            "company_id": company_id,
            "employee_id": emp_info["id"],
            "employee_name": emp_info["name"],
            "title": title,
            "description": f"Task: {title}",
            "category_id": task_categories.get(category),
            "category": category,
            "priority": priority,
            "amount": amount,
            "status": status,
            "verified_status": verified,
            "due_date": (datetime.now() + timedelta(days=random.randint(1, 14))).strftime("%Y-%m-%d"),
            "assigned_by": user_id,
            "created_at": get_timestamp()
        }
        await db.employee_tasks.insert_one(task)
        status_icon = "✅" if status == "completed" else "🔄" if status == "in_progress" else "📋"
        print(f"  {status_icon} {emp_info['name']}: {title}")
    
    # ============== 18. CREATE PAYROLL RUN ==============
    print("\n💰 Creating Payroll Run...")
    
    payroll_id = generate_id()
    payroll = {
        "id": payroll_id,
        "company_id": company_id,
        "payroll_number": "PAY-2026-02",
        "period_start": "2026-02-01",
        "period_end": "2026-02-28",
        "payment_frequency": "monthly",
        "status": "processed",
        "total_gross": 0,
        "total_deductions": 0,
        "total_net": 0,
        "processed_by": user_id,
        "processed_date": "2026-02-28",
        "created_at": get_timestamp()
    }
    
    total_gross = 0
    total_deductions = 0
    
    for emp_code, emp_info in employees.items():
        salary = emp_info["salary"]
        allowances_amt = 8000  # Transport + Meal
        gross = salary + allowances_amt
        epf = salary * 0.08
        etf = salary * 0.03
        deductions_amt = epf + etf
        net = gross - deductions_amt
        
        total_gross += gross
        total_deductions += deductions_amt
        
        payroll_item = {
            "id": generate_id(),
            "company_id": company_id,
            "payroll_id": payroll_id,
            "employee_id": emp_info["id"],
            "employee_name": emp_info["name"],
            "basic_salary": salary,
            "allowances": allowances_amt,
            "gross_salary": gross,
            "deductions": deductions_amt,
            "net_salary": net,
            "status": "paid"
        }
        await db.payroll_items.insert_one(payroll_item)
    
    payroll["total_gross"] = total_gross
    payroll["total_deductions"] = total_deductions
    payroll["total_net"] = total_gross - total_deductions
    await db.payrolls.insert_one(payroll)
    print(f"  ✅ February 2026 Payroll: LKR {total_gross:,.0f} gross, LKR {payroll['total_net']:,.0f} net")
    
    # ============== 19. CREATE ATTENDANCE RECORDS ==============
    print("\n📅 Creating Attendance Records...")
    
    attendance_count = 0
    for emp_code, emp_info in employees.items():
        for day in range(1, 11):  # Last 10 days
            att_date = (datetime.now() - timedelta(days=day)).strftime("%Y-%m-%d")
            status = random.choices(
                ["present", "present", "present", "late", "half_day"],
                weights=[70, 15, 10, 3, 2]
            )[0]
            
            att = {
                "id": generate_id(),
                "company_id": company_id,
                "employee_id": emp_info["id"],
                "date": att_date,
                "status": status,
                "check_in": "09:00" if status == "present" else "09:30" if status == "late" else "09:00",
                "check_out": "17:00" if status != "half_day" else "13:00",
                "created_at": get_timestamp()
            }
            await db.attendance.insert_one(att)
            attendance_count += 1
    
    print(f"  ✅ Created {attendance_count} attendance records")
    
    # ============== SUMMARY ==============
    print()
    print("=" * 70)
    print("🎉 TEST DATA SEEDING COMPLETE!")
    print("=" * 70)
    print()
    print("📊 SUMMARY:")
    print(f"   • Company: URBAN STREETWEARS (PVT) LTD")
    print(f"   • User: lahiruraja97@gmail.com / password123")
    print(f"   • Departments: 10")
    print(f"   • Designations: {len(designations_data)}")
    print(f"   • Employees: {len(employees)}")
    print(f"   • Products: {len(products)}")
    print(f"   • Suppliers: {len(suppliers)}")
    print(f"   • Customers: {len(customers)}")
    print(f"   • Purchase Orders: 5")
    print(f"   • GRNs: 5")
    print(f"   • Sales Orders: 8")
    print(f"   • Journal Entries: {len(transactions)}")
    print(f"   • Employee Advances: 3")
    print(f"   • Leave Requests: 4")
    print(f"   • Task Assignments: 6")
    print(f"   • Payroll Processed: February 2026")
    print(f"   • Attendance Records: {attendance_count}")
    print(f"   • Chart of Accounts: {len(accounts_data)}")
    print(f"   • Bank Accounts: 3")
    print()
    print("✅ System is ready for testing!")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(seed_database())
