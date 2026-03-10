#!/usr/bin/env python3
"""
Script to create designations for URBAN STREETWEARS company
"""
import requests
import json
import os

API_URL = os.popen("grep REACT_APP_BACKEND_URL /app/frontend/.env | cut -d '=' -f2").read().strip()

# Login to get token
login_response = requests.post(
    f"{API_URL}/api/auth/login",
    json={"email": "lahiruraja97@gmail.com", "password": "password123"}
)
TOKEN = login_response.json().get("access_token")

if not TOKEN:
    print("Failed to login!")
    exit(1)

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# Get existing departments
dept_response = requests.get(f"{API_URL}/api/payroll/departments", headers=HEADERS)
departments = {d["name"]: d["id"] for d in dept_response.json()}

print(f"Found {len(departments)} departments")

# Define designations per department
# Format: (name, description, role, level)
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
        print(f"  ✅ {name} (L{level}, {role})")
        return True
    elif "already exists" in response.text:
        print(f"  ⏭️  {name} (already exists)")
        return True
    else:
        print(f"  ❌ {name}: {response.text[:100]}")
        return False

def main():
    print("=" * 60)
    print("Creating Designations for URBAN STREETWEARS")
    print("=" * 60)
    print()
    
    total = 0
    for dept_name, designations in DESIGNATIONS.items():
        dept_id = departments.get(dept_name)
        if not dept_id:
            print(f"⚠️  Department not found: {dept_name}")
            continue
        
        print(f"\n📂 {dept_name}:")
        for name, description, role, level in designations:
            if create_designation(name, description, dept_id, role, level):
                total += 1
    
    print()
    print("=" * 60)
    print(f"🎉 Created {total} designations!")
    print("=" * 60)

if __name__ == "__main__":
    main()
