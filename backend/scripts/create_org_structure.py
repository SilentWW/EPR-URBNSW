#!/usr/bin/env python3
"""
Script to create departments and designations for a clothing brand company
"""
import requests
import json
import os

API_URL = os.popen("grep REACT_APP_BACKEND_URL /app/frontend/.env | cut -d '=' -f2").read().strip()
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiZmI4NDQ2OTYtZDIyOC00MThiLTkzZWQtOTBlN2UxNzM3MzdmIiwiZW1haWwiOiJ0ZXN0YWRtaW5AZXhhbXBsZS5jb20iLCJyb2xlIjoiYWRtaW4iLCJjb21wYW55X2lkIjoiYTQxZWJlMjAtOTFiNi00NTUzLWJmZGUtZjkxNTQzMWMxMGM4IiwiZXhwIjoxNzczMjU2MDk1fQ.qTo3H0I_FQrEozQQDhi_FM-grYQTPa69FNJnJ6_k8GI"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Define all departments
DEPARTMENTS = [
    {"name": "Executive / Leadership", "description": "Decision-making level of the company"},
    {"name": "Design & Product Development", "description": "Heart of the clothing brand - designs and product creation"},
    {"name": "Production & Manufacturing", "description": "Garment production and quality control"},
    {"name": "Marketing & Brand", "description": "Brand identity and marketing campaigns"},
    {"name": "E-Commerce & Sales", "description": "Online store and sales management"},
    {"name": "Logistics & Inventory", "description": "Stock management and order fulfillment"},
    {"name": "Customer Experience", "description": "Customer support and satisfaction"},
    {"name": "Finance & Accounting", "description": "Financial management and records"},
    {"name": "Human Resources", "description": "Employee recruitment and management"},
    {"name": "Legal & Compliance", "description": "Legal matters and regulatory compliance"},
]

# Define designations per department
# Format: (name, description, role, level)
# role: admin, manager, accountant, store, employee
# level: 1-10 (10 = highest)
DESIGNATIONS = {
    "Executive / Leadership": [
        ("Founder / Creative Director", "Define brand vision, approve designs, set strategy, lead creative teams", "admin", 10),
        ("Chief Executive Officer (CEO)", "Manage entire business, lead department heads, set goals, build partnerships", "admin", 10),
        ("Operations Director", "Oversee daily operations, ensure efficiency, manage timelines", "manager", 9),
    ],
    "Design & Product Development": [
        ("Head of Design", "Lead design team, plan collections, approve final designs", "manager", 8),
        ("Fashion Designer", "Create clothing concepts, develop silhouettes, work on collections", "employee", 6),
        ("Graphic Designer", "Create t-shirt artwork, prepare print files, design packaging", "employee", 5),
        ("Product Developer", "Convert designs to products, choose fabrics, coordinate with manufacturers", "employee", 6),
        ("Technical Designer", "Create technical specs, size charts, fit corrections", "employee", 5),
    ],
    "Production & Manufacturing": [
        ("Production Manager", "Manage garment production, coordinate factories, control schedules", "manager", 7),
        ("Print Production Specialist", "Handle screen printing/DTF, ensure print quality", "employee", 5),
        ("Quality Control Manager", "Inspect garments, check stitching/prints/fabric, approve products", "manager", 6),
        ("Sourcing Manager", "Find fabric suppliers, negotiate prices with manufacturers", "employee", 6),
    ],
    "Marketing & Brand": [
        ("Brand Manager", "Maintain brand identity, plan campaigns, control messaging", "manager", 7),
        ("Social Media Manager", "Manage Instagram/TikTok/Facebook, post content, engage audience", "employee", 5),
        ("Content Creator", "Shoot photos/videos, create reels and campaign visuals", "employee", 4),
        ("Influencer & Partnership Manager", "Manage influencer collaborations, arrange brand partnerships", "employee", 5),
        ("Marketing Analyst", "Study customer behavior, track marketing performance", "employee", 5),
    ],
    "E-Commerce & Sales": [
        ("E-Commerce Manager", "Manage online store, handle website performance, track sales", "manager", 7),
        ("Sales Manager", "Manage retail/wholesale sales, build store partnerships", "manager", 7),
        ("Order Management Executive", "Process customer orders, handle shipping updates", "employee", 4),
    ],
    "Logistics & Inventory": [
        ("Inventory Manager", "Track stock levels, manage warehouse storage", "store", 6),
        ("Fulfillment Coordinator", "Pack and ship orders, coordinate courier deliveries", "store", 4),
        ("Supply Chain Manager", "Manage product movement, ensure smooth supply chain", "manager", 7),
    ],
    "Customer Experience": [
        ("Customer Support Manager", "Handle customer inquiries, manage returns and exchanges", "manager", 6),
        ("Customer Experience Specialist", "Improve customer satisfaction, manage loyalty programs", "employee", 5),
    ],
    "Finance & Accounting": [
        ("Finance Manager", "Manage budgets and profits, control company spending", "accountant", 7),
        ("Accountant", "Maintain financial records, manage tax payments", "accountant", 5),
        ("Financial Analyst", "Analyze company performance, plan growth strategies", "accountant", 6),
    ],
    "Human Resources": [
        ("HR Manager", "Recruit employees, manage staff performance", "manager", 7),
        ("HR Executive", "Handle payroll and employee relations", "employee", 5),
    ],
    "Legal & Compliance": [
        ("Legal Advisor", "Handle contracts, protect intellectual property", "manager", 7),
        ("Compliance Officer", "Ensure company follows laws and regulations", "employee", 6),
    ],
}

def create_department(name, description):
    """Create a department and return its ID"""
    response = requests.post(
        f"{API_URL}/api/payroll/departments",
        headers=HEADERS,
        json={"name": name, "description": description}
    )
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Created department: {name}")
        return data.get("id")
    else:
        print(f"❌ Failed to create department {name}: {response.text}")
        return None

def create_designation(name, description, department_id, role, level):
    """Create a designation"""
    response = requests.post(
        f"{API_URL}/api/payroll/designations",
        headers=HEADERS,
        json={
            "name": name,
            "description": description,
            "department_id": department_id,
            "role": role,
            "level": level
        }
    )
    if response.status_code == 200:
        print(f"  ✅ Created designation: {name} (Level {level}, Role: {role})")
        return True
    else:
        print(f"  ❌ Failed to create designation {name}: {response.text}")
        return False

def main():
    print("=" * 60)
    print("Creating Departments and Designations for Clothing Brand")
    print("=" * 60)
    print()
    
    department_ids = {}
    
    # Step 1: Create all departments
    print("📁 CREATING DEPARTMENTS...")
    print("-" * 40)
    for dept in DEPARTMENTS:
        dept_id = create_department(dept["name"], dept["description"])
        if dept_id:
            department_ids[dept["name"]] = dept_id
    
    print()
    print(f"✅ Created {len(department_ids)} departments")
    print()
    
    # Step 2: Create all designations
    print("👔 CREATING DESIGNATIONS...")
    print("-" * 40)
    
    total_designations = 0
    for dept_name, designations in DESIGNATIONS.items():
        dept_id = department_ids.get(dept_name)
        if not dept_id:
            print(f"⚠️  Skipping designations for {dept_name} (department not found)")
            continue
        
        print(f"\n📂 {dept_name}:")
        for name, description, role, level in designations:
            if create_designation(name, description, dept_id, role, level):
                total_designations += 1
    
    print()
    print("=" * 60)
    print(f"🎉 COMPLETE!")
    print(f"   Departments created: {len(department_ids)}")
    print(f"   Designations created: {total_designations}")
    print("=" * 60)

if __name__ == "__main__":
    main()
