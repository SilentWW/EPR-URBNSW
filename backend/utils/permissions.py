"""
Role-Based Access Control (RBAC) Configuration
Defines permissions for each role in the system.
"""

# Role definitions with their allowed modules/features
ROLE_PERMISSIONS = {
    "admin": {
        "description": "Full access to everything",
        "modules": ["*"],  # Wildcard = all access
        "can_create_roles": ["admin", "manager", "accountant", "store", "employee"],
    },
    "manager": {
        "description": "HR, Inventory, Sales, Tasks, Reports (no System Admin)",
        "modules": [
            "dashboard",
            "products", "inventory", "grn", "packaging-rules",
            "customers", "suppliers", "sales-orders", "invoices", "purchase-orders", "payments",
            "manufacturing", "raw-materials", "bill-of-materials", "work-orders",
            "rm-suppliers", "rm-purchase-orders", "rm-grn", "rm-grn-returns",
            "departments", "employees", "attendance", "salary-structure", 
            "leave-management", "advances", "task-assignments", "payroll", "payroll-reports",
            "task-categories",
            "reports",
            "my-dashboard", "my-tasks",
            "settings",
        ],
        "can_create_roles": ["manager", "accountant", "store", "employee"],
    },
    "accountant": {
        "description": "Finance, Payments, Reports only",
        "modules": [
            "dashboard",
            "accounting", "chart-of-accounts", "general-ledger", "financial-reports",
            "invoices", "payments",
            "investors", "quick-transactions", "bank-accounts",
            "reports",
            "my-dashboard", "my-tasks",
        ],
        "can_create_roles": [],
    },
    "store": {
        "description": "Inventory, Products, GRN, Purchase Orders only",
        "modules": [
            "dashboard",
            "products", "inventory", "grn", "packaging-rules",
            "suppliers", "purchase-orders",
            "raw-materials", "rm-suppliers", "rm-purchase-orders", "rm-grn", "rm-grn-returns",
            "my-dashboard", "my-tasks",
        ],
        "can_create_roles": [],
    },
    "employee": {
        "description": "My Portal only (Dashboard, Tasks, Attendance, Leave)",
        "modules": [
            "my-dashboard", "my-tasks",
            "attendance", "leave-management",
        ],
        "can_create_roles": [],
    },
    # Legacy role mapping
    "staff": {
        "description": "Same as employee",
        "modules": [
            "my-dashboard", "my-tasks",
            "attendance", "leave-management",
        ],
        "can_create_roles": [],
    },
    "accounts": {
        "description": "Same as accountant (legacy)",
        "modules": [
            "dashboard",
            "accounting", "chart-of-accounts", "general-ledger", "financial-reports",
            "invoices", "payments",
            "investors", "quick-transactions", "bank-accounts",
            "reports",
            "my-dashboard", "my-tasks",
        ],
        "can_create_roles": [],
    },
}

# API route to module mapping
API_MODULE_MAPPING = {
    # Dashboard
    "/api/dashboard": "dashboard",
    
    # Products & Inventory
    "/api/products": "products",
    "/api/inventory": "inventory",
    "/api/grn": "grn",
    "/api/packaging": "packaging-rules",
    
    # Sales
    "/api/customers": "customers",
    "/api/sales-orders": "sales-orders",
    "/api/invoices": "invoices",
    
    # Purchasing
    "/api/suppliers": "suppliers",
    "/api/purchase-orders": "purchase-orders",
    "/api/payments": "payments",
    
    # Finance
    "/api/finance": "accounting",
    "/api/accounts": "chart-of-accounts",
    "/api/journal": "general-ledger",
    "/api/investors": "investors",
    "/api/quick-transactions": "quick-transactions",
    "/api/bank-accounts": "bank-accounts",
    
    # Manufacturing
    "/api/raw-materials": "raw-materials",
    "/api/bom": "bill-of-materials",
    "/api/work-orders": "work-orders",
    "/api/rm-suppliers": "rm-suppliers",
    "/api/rm-purchase-orders": "rm-purchase-orders",
    "/api/rm-grn": "rm-grn",
    
    # Payroll
    "/api/payroll/departments": "departments",
    "/api/payroll/employees": "employees",
    "/api/payroll/attendance": "attendance",
    "/api/payroll/salary": "salary-structure",
    "/api/payroll/leave": "leave-management",
    "/api/payroll/advances": "advances",
    "/api/payroll/tasks": "task-assignments",
    "/api/payroll/payroll": "payroll",
    
    # Portal
    "/api/portal/task-categories": "task-categories",
    "/api/portal/tasks": "my-tasks",
    "/api/portal/my-dashboard": "my-dashboard",
    "/api/portal/my-profile": "my-dashboard",
    
    # Reports
    "/api/reports": "reports",
    
    # Admin
    "/api/admin": "system-admin",
    "/api/audit-logs": "audit-logs",
    "/api/users": "user-management",
    
    # Settings
    "/api/settings": "settings",
    "/api/company": "settings",
}


def get_role_permissions(role: str) -> dict:
    """Get permissions for a given role"""
    return ROLE_PERMISSIONS.get(role, ROLE_PERMISSIONS.get("employee"))


def check_module_access(role: str, module: str) -> bool:
    """Check if a role has access to a specific module"""
    permissions = get_role_permissions(role)
    modules = permissions.get("modules", [])
    
    # Admin has access to everything
    if "*" in modules:
        return True
    
    return module in modules


def check_api_access(role: str, api_path: str) -> bool:
    """Check if a role has access to a specific API path"""
    # Find the matching module for this API path
    for api_prefix, module in API_MODULE_MAPPING.items():
        if api_path.startswith(api_prefix):
            return check_module_access(role, module)
    
    # Default: allow access to unmatched routes (health, auth, etc.)
    return True


def get_allowed_modules(role: str) -> list:
    """Get list of allowed modules for a role"""
    permissions = get_role_permissions(role)
    return permissions.get("modules", [])


def can_create_role(creator_role: str, target_role: str) -> bool:
    """Check if a role can create another role"""
    permissions = get_role_permissions(creator_role)
    allowed_roles = permissions.get("can_create_roles", [])
    return target_role in allowed_roles


# Available roles for user management dropdowns
AVAILABLE_ROLES = [
    {"value": "admin", "label": "Admin", "description": "Full access to everything"},
    {"value": "manager", "label": "Manager", "description": "HR, Inventory, Sales, Tasks, Reports"},
    {"value": "accountant", "label": "Accountant", "description": "Finance, Payments, Reports"},
    {"value": "store", "label": "Store Keeper", "description": "Inventory, Products, GRN, PO"},
    {"value": "employee", "label": "Employee", "description": "My Portal only"},
]
