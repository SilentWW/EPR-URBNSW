import React, { useState } from 'react';
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
  PackageCheck
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
  { icon: LayoutDashboard, label: 'Dashboard', path: '/dashboard' },
  { icon: Package, label: 'Products', path: '/products' },
  { icon: Boxes, label: 'Inventory', path: '/inventory' },
  { icon: PackageCheck, label: 'GRN', path: '/grn' },
  { icon: Users, label: 'Customers', path: '/customers' },
  { icon: Truck, label: 'Suppliers', path: '/suppliers' },
  { icon: ShoppingCart, label: 'Sales Orders', path: '/sales-orders' },
  { icon: FileText, label: 'Invoices', path: '/invoices' },
  { icon: ClipboardList, label: 'Purchase Orders', path: '/purchase-orders' },
  { icon: CreditCard, label: 'Payments', path: '/payments' },
  { icon: TrendingUp, label: 'Accounting', path: '/accounting' },
  { icon: PieChart, label: 'Reports', path: '/reports' },
];

const financeMenuItems = [
  { icon: BookOpen, label: 'Chart of Accounts', path: '/chart-of-accounts' },
  { icon: Calculator, label: 'General Ledger', path: '/general-ledger' },
  { icon: BarChart3, label: 'Financial Reports', path: '/financial-reports' },
];

const adminMenuItems = [
  { icon: Settings, label: 'Settings', path: '/settings' },
  { icon: Shield, label: 'System Admin', path: '/system-admin' },
];

export const Layout = ({ children }) => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [notifications] = useState(3);

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
              <span className="text-xl font-semibold text-slate-900" style={{ fontFamily: 'Outfit, sans-serif' }}>
                E1 ERP
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
            <ul className="space-y-1">
              {menuItems.map((item) => {
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

            {/* Finance Section */}
            <div className="mt-6 pt-4 border-t border-slate-100">
              <p className="px-3 mb-2 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Finance
              </p>
              <ul className="space-y-1">
                {financeMenuItems.map((item) => {
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

            {/* Admin Section */}
            {user?.role === 'admin' && (
              <div className="mt-6 pt-4 border-t border-slate-100">
                <p className="px-3 mb-2 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  Administration
                </p>
                <ul className="space-y-1">
                  {adminMenuItems.map((item) => {
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
              {[...menuItems, ...financeMenuItems, ...adminMenuItems].find((item) => item.path === location.pathname)?.label || 'Dashboard'}
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
