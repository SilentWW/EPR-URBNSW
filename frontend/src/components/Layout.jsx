import React, { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  LayoutDashboard,
  Package,
  Users,
  Truck,
  ShoppingCart,
  FileText,
  Receipt,
  CreditCard,
  PieChart,
  Settings,
  Bell,
  LogOut,
  Menu,
  X,
  ChevronDown,
  Building2,
  ClipboardList,
  Boxes,
  TrendingUp,
  BookOpen,
  Calculator,
  BarChart3,
  Shield,
  ChevronRight,
  PackageCheck,
  Wallet,
  Zap,
  UserPlus,
  PackageOpen,
  Factory,
  Hammer,
  ScrollText,
  Clock,
  FileSearch,
  Tags
} from 'lucide-react';
import { Button } from './ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from './ui/dropdown-menu';
import { Avatar, AvatarFallback } from './ui/avatar';
import { Badge } from './ui/badge';

const menuItems = [
  { icon: LayoutDashboard, label: 'Dashboard', path: '/dashboard', module: 'dashboard' },
  { icon: Package, label: 'Products', path: '/products', module: 'products' },
  { icon: Boxes, label: 'Inventory', path: '/inventory', module: 'inventory' },
  { icon: PackageCheck, label: 'GRN', path: '/grn', module: 'grn' },
  { icon: PackageOpen, label: 'Packaging Rules', path: '/packaging-rules', module: 'packaging-rules' },
  { icon: Users, label: 'Customers', path: '/customers', module: 'customers' },
  { icon: Truck, label: 'Suppliers', path: '/suppliers', module: 'suppliers' },
  { icon: ShoppingCart, label: 'Sales Orders', path: '/sales-orders', module: 'sales-orders' },
  { icon: FileText, label: 'Invoices', path: '/invoices', module: 'invoices' },
  { icon: ClipboardList, label: 'Purchase Orders', path: '/purchase-orders', module: 'purchase-orders' },
  { icon: CreditCard, label: 'Payments', path: '/payments', module: 'payments' },
  { icon: TrendingUp, label: 'Accounting', path: '/accounting', module: 'accounting' },
  { icon: PieChart, label: 'Reports', path: '/reports', module: 'reports' },
];

const manufacturingMenuItems = [
  { icon: LayoutDashboard, label: 'Manufacturing', path: '/manufacturing', module: 'manufacturing' },
  { icon: Hammer, label: 'Raw Materials', path: '/raw-materials', module: 'raw-materials' },
  { icon: Truck, label: 'RM Suppliers', path: '/rm-suppliers', module: 'rm-suppliers' },
  { icon: ClipboardList, label: 'RM Purchase Orders', path: '/rm-purchase-orders', module: 'rm-purchase-orders' },
  { icon: PackageCheck, label: 'RM GRN', path: '/rm-grn', module: 'rm-grn' },
  { icon: Receipt, label: 'RM GRN Returns', path: '/rm-grn-returns', module: 'rm-grn-returns' },
  { icon: ScrollText, label: 'Bill of Materials', path: '/bom', module: 'bill-of-materials' },
  { icon: Factory, label: 'Work Orders', path: '/work-orders', module: 'work-orders' },
];

const financeMenuItems = [
  { icon: Zap, label: 'Quick Transactions', path: '/quick-transactions', highlight: true, module: 'quick-transactions' },
  { icon: UserPlus, label: 'Investors', path: '/investors', module: 'investors' },
  { icon: Wallet, label: 'Bank Accounts', path: '/bank-accounts', module: 'bank-accounts' },
  { icon: BookOpen, label: 'Chart of Accounts', path: '/chart-of-accounts', module: 'chart-of-accounts' },
  { icon: Calculator, label: 'General Ledger', path: '/general-ledger', module: 'general-ledger' },
  { icon: BarChart3, label: 'Financial Reports', path: '/financial-reports', module: 'financial-reports' },
];

const payrollMenuItems = [
  { icon: Building2, label: 'Departments', path: '/departments', module: 'departments' },
  { icon: Users, label: 'Employees', path: '/employees', module: 'employees' },
  { icon: Clock, label: 'Attendance', path: '/attendance', module: 'attendance' },
  { icon: Calculator, label: 'Salary Structure', path: '/salary-structure', module: 'salary-structure' },
  { icon: Receipt, label: 'Leave Management', path: '/leave-management', module: 'leave-management' },
  { icon: Wallet, label: 'Advances & Loans', path: '/advances', module: 'advances' },
  { icon: ClipboardList, label: 'Task Assignments', path: '/task-assignments', module: 'task-assignments' },
  { icon: CreditCard, label: 'Payroll', path: '/payroll', module: 'payroll' },
  { icon: BarChart3, label: 'Payroll Reports', path: '/payroll-reports', module: 'payroll-reports' },
  { icon: Tags, label: 'Task Categories', path: '/task-categories', module: 'task-categories' },
];

// Employee Portal menu items (visible to all employees)
const employeePortalItems = [
  { icon: LayoutDashboard, label: 'My Dashboard', path: '/my-dashboard', module: 'my-dashboard' },
  { icon: ClipboardList, label: 'My Tasks', path: '/my-tasks', module: 'my-tasks' },
  { icon: Users, label: 'My Profile', path: '/my-profile', module: 'my-dashboard' },
];

const adminMenuItems = [
  { icon: Settings, label: 'Settings', path: '/settings', module: 'settings' },
  { icon: Users, label: 'User Management', path: '/user-management', module: 'user-management' },
  { icon: Shield, label: 'System Admin', path: '/system-admin', module: 'system-admin' },
  { icon: FileSearch, label: 'Audit Logs', path: '/audit-logs', module: 'audit-logs' },
  { icon: BookOpen, label: 'Documentation', path: '/documentation', module: 'documentation' },
];

// Role-based module access configuration
const ROLE_MODULES = {
  admin: ['*'], // All access
  manager: [
    'dashboard', 'products', 'inventory', 'grn', 'packaging-rules',
    'customers', 'suppliers', 'sales-orders', 'invoices', 'purchase-orders', 'payments',
    'manufacturing', 'raw-materials', 'bill-of-materials', 'work-orders',
    'rm-suppliers', 'rm-purchase-orders', 'rm-grn', 'rm-grn-returns',
    'departments', 'employees', 'attendance', 'salary-structure',
    'leave-management', 'advances', 'task-assignments', 'payroll', 'payroll-reports',
    'task-categories', 'reports', 'my-dashboard', 'my-tasks', 'settings',
    'user-management', 'documentation'
  ],
  accountant: [
    'dashboard', 'accounting', 'chart-of-accounts', 'general-ledger', 'financial-reports',
    'invoices', 'payments', 'investors', 'quick-transactions', 'bank-accounts',
    'reports', 'my-dashboard', 'my-tasks', 'documentation'
  ],
  accounts: [ // Legacy alias
    'dashboard', 'accounting', 'chart-of-accounts', 'general-ledger', 'financial-reports',
    'invoices', 'payments', 'investors', 'quick-transactions', 'bank-accounts',
    'reports', 'my-dashboard', 'my-tasks', 'documentation'
  ],
  store: [
    'dashboard', 'products', 'inventory', 'grn', 'packaging-rules',
    'suppliers', 'purchase-orders',
    'raw-materials', 'rm-suppliers', 'rm-purchase-orders', 'rm-grn', 'rm-grn-returns',
    'my-dashboard', 'my-tasks', 'documentation'
  ],
  employee: [
    'my-dashboard', 'my-tasks', 'attendance', 'leave-management', 'documentation'
  ],
  staff: [ // Legacy alias
    'my-dashboard', 'my-tasks', 'attendance', 'leave-management', 'documentation'
  ]
};

// Check if user has access to a module
const hasModuleAccess = (role, module) => {
  const modules = ROLE_MODULES[role] || ROLE_MODULES.employee;
  return modules.includes('*') || modules.includes(module);
};

// Filter menu items based on role
const filterMenuByRole = (items, role) => {
  return items.filter(item => {
    if (!item.module) return true;
    return hasModuleAccess(role, item.module);
  });
};

export const Layout = ({ children }) => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [notifications] = useState(3);

  // Dynamic page title based on company name
  useEffect(() => {
    const companyName = user?.company_name || 'Business';
    document.title = `${companyName} ERP`;
  }, [user?.company_name]);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const getInitials = (name) => {
    return name
      .split(' ')
      .map((n) => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  return (
    <div className="erp-container">
      {/* Mobile Overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-30 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`erp-sidebar ${sidebarOpen ? 'open' : ''} lg:translate-x-0`}
        data-testid="sidebar"
      >
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="h-16 flex items-center px-6 border-b border-slate-100">
            <Link to="/dashboard" className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center">
                <Building2 className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-semibold text-slate-900 truncate max-w-[160px]" style={{ fontFamily: 'Outfit, sans-serif' }} title={user?.company_name || 'My Business'}>
                {user?.company_name || 'My Business'}
              </span>
            </Link>
            <button
              className="ml-auto lg:hidden"
              onClick={() => setSidebarOpen(false)}
            >
              <X className="w-5 h-5 text-slate-500" />
            </button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-6 overflow-y-auto">
            {/* Main Menu - filtered by role */}
            {filterMenuByRole(menuItems, user?.role).length > 0 && (
              <ul className="space-y-1">
                {filterMenuByRole(menuItems, user?.role).map((item) => {
                  const isActive = location.pathname === item.path;
                  return (
                    <li key={item.path}>
                      <Link
                        to={item.path}
                        className={`sidebar-item ${isActive ? 'sidebar-item-active' : ''}`}
                        onClick={() => setSidebarOpen(false)}
                        data-testid={`nav-${item.path.slice(1)}`}
                      >
                        <item.icon className="w-5 h-5" />
                        <span className="font-medium">{item.label}</span>
                      </Link>
                    </li>
                  );
                })}
              </ul>
            )}

            {/* Manufacturing Section - filtered by role */}
            {filterMenuByRole(manufacturingMenuItems, user?.role).length > 0 && (
              <div className="mt-6 pt-4 border-t border-slate-100">
                <p className="px-3 mb-2 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  Manufacturing
                </p>
                <ul className="space-y-1">
                  {filterMenuByRole(manufacturingMenuItems, user?.role).map((item) => {
                    const isActive = location.pathname === item.path;
                    return (
                      <li key={item.path}>
                        <Link
                          to={item.path}
                          className={`sidebar-item ${isActive ? 'sidebar-item-active' : ''}`}
                          onClick={() => setSidebarOpen(false)}
                          data-testid={`nav-${item.path.slice(1)}`}
                        >
                          <item.icon className="w-5 h-5" />
                          <span className="font-medium">{item.label}</span>
                        </Link>
                      </li>
                    );
                  })}
                </ul>
              </div>
            )}

            {/* Finance Section - filtered by role */}
            {filterMenuByRole(financeMenuItems, user?.role).length > 0 && (
              <div className="mt-6 pt-4 border-t border-slate-100">
                <p className="px-3 mb-2 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  Finance
                </p>
                <ul className="space-y-1">
                  {filterMenuByRole(financeMenuItems, user?.role).map((item) => {
                    const isActive = location.pathname === item.path;
                    return (
                      <li key={item.path}>
                        <Link
                          to={item.path}
                          className={`sidebar-item ${isActive ? 'sidebar-item-active' : ''}`}
                          onClick={() => setSidebarOpen(false)}
                          data-testid={`nav-${item.path.slice(1)}`}
                        >
                          <item.icon className="w-5 h-5" />
                          <span className="font-medium">{item.label}</span>
                        </Link>
                      </li>
                    );
                  })}
                </ul>
              </div>
            )}

            {/* HR/Payroll Section - filtered by role */}
            {filterMenuByRole(payrollMenuItems, user?.role).length > 0 && (
              <div className="mt-6 pt-4 border-t border-slate-100">
                <p className="px-3 mb-2 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  HR / Payroll
                </p>
                <ul className="space-y-1">
                  {filterMenuByRole(payrollMenuItems, user?.role).map((item) => {
                    const isActive = location.pathname === item.path;
                    return (
                      <li key={item.path}>
                        <Link
                          to={item.path}
                          className={`sidebar-item ${isActive ? 'sidebar-item-active' : ''}`}
                          onClick={() => setSidebarOpen(false)}
                          data-testid={`nav-${item.path.slice(1)}`}
                        >
                          <item.icon className="w-5 h-5" />
                          <span className="font-medium">{item.label}</span>
                        </Link>
                      </li>
                    );
                  })}
                </ul>
              </div>
            )}

            {/* Employee Portal Section - always visible */}
            <div className="mt-6 pt-4 border-t border-slate-100">
              <p className="px-3 mb-2 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                My Portal
              </p>
              <ul className="space-y-1">
                {filterMenuByRole(employeePortalItems, user?.role).map((item) => {
                  const isActive = location.pathname === item.path;
                  return (
                    <li key={item.path}>
                      <Link
                        to={item.path}
                        className={`sidebar-item ${isActive ? 'sidebar-item-active' : ''}`}
                        onClick={() => setSidebarOpen(false)}
                        data-testid={`nav-${item.path.slice(1)}`}
                      >
                        <item.icon className="w-5 h-5" />
                        <span className="font-medium">{item.label}</span>
                      </Link>
                    </li>
                  );
                })}
              </ul>
            </div>

            {/* Admin Section - filtered by role */}
            {filterMenuByRole(adminMenuItems, user?.role).length > 0 && (
              <div className="mt-6 pt-4 border-t border-slate-100">
                <p className="px-3 mb-2 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  Administration
                </p>
                <ul className="space-y-1">
                  {filterMenuByRole(adminMenuItems, user?.role).map((item) => {
                    const isActive = location.pathname === item.path;
                    return (
                      <li key={item.path}>
                        <Link
                          to={item.path}
                          className={`sidebar-item ${isActive ? 'sidebar-item-active' : ''}`}
                          onClick={() => setSidebarOpen(false)}
                          data-testid={`nav-${item.path.slice(1)}`}
                        >
                          <item.icon className="w-5 h-5" />
                          <span className="font-medium">{item.label}</span>
                        </Link>
                      </li>
                    );
                  })}
                </ul>
              </div>
            )}
          </nav>

          {/* User Info */}
          <div className="p-4 border-t border-slate-100">
            <div className="flex items-center gap-3 px-2">
              <Avatar className="h-9 w-9">
                <AvatarFallback className="bg-indigo-100 text-indigo-700 text-sm font-medium">
                  {user ? getInitials(user.full_name) : 'U'}
                </AvatarFallback>
              </Avatar>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-slate-900 truncate">
                  {user?.full_name}
                </p>
                <p className="text-xs text-slate-500 truncate capitalize">
                  {user?.role}
                </p>
              </div>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="erp-main">
        {/* Header */}
        <header className="erp-header flex items-center justify-between px-6" data-testid="header">
          <div className="flex items-center gap-4">
            <button
              className="mobile-menu-btn p-2 rounded-lg hover:bg-slate-100 lg:hidden"
              onClick={() => setSidebarOpen(true)}
              data-testid="mobile-menu-btn"
            >
              <Menu className="w-5 h-5 text-slate-600" />
            </button>
            <h1 className="text-lg font-semibold text-slate-900" style={{ fontFamily: 'Outfit, sans-serif' }}>
              {[...menuItems, ...manufacturingMenuItems, ...financeMenuItems, ...payrollMenuItems, ...employeePortalItems, ...adminMenuItems].find((item) => item.path === location.pathname)?.label || 'Dashboard'}
            </h1>
          </div>

          <div className="flex items-center gap-3">
            {/* Notifications */}
            <Link to="/notifications" className="relative">
              <Button variant="ghost" size="icon" className="relative" data-testid="notifications-btn">
                <Bell className="w-5 h-5 text-slate-600" />
                {notifications > 0 && (
                  <Badge className="absolute -top-1 -right-1 h-5 w-5 flex items-center justify-center p-0 bg-red-500 text-white text-xs">
                    {notifications}
                  </Badge>
                )}
              </Button>
            </Link>

            {/* User Menu */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="flex items-center gap-2" data-testid="user-menu-btn">
                  <Avatar className="h-8 w-8">
                    <AvatarFallback className="bg-indigo-100 text-indigo-700 text-sm font-medium">
                      {user ? getInitials(user.full_name) : 'U'}
                    </AvatarFallback>
                  </Avatar>
                  <ChevronDown className="w-4 h-4 text-slate-500" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56">
                <DropdownMenuLabel>
                  <div>
                    <p className="font-medium">{user?.full_name}</p>
                    <p className="text-xs text-slate-500">{user?.email}</p>
                  </div>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={() => navigate('/settings')}>
                  <Settings className="w-4 h-4 mr-2" />
                  Settings
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={handleLogout} className="text-red-600" data-testid="logout-btn">
                  <LogOut className="w-4 h-4 mr-2" />
                  Logout
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </header>

        {/* Page Content */}
        <div className="erp-content animate-fade-in">
          {children}
        </div>
      </main>
    </div>
  );
};

export default Layout;
