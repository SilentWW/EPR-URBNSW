import React from 'react';
import '@/App.css';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'sonner';
import { AuthProvider, useAuth } from './context/AuthContext';

// Pages
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Products from './pages/Products';
import Inventory from './pages/Inventory';
import Customers from './pages/Customers';
import Suppliers from './pages/Suppliers';
import SalesOrders from './pages/SalesOrders';
import Invoices from './pages/Invoices';
import PurchaseOrders from './pages/PurchaseOrders';
import Payments from './pages/Payments';
import Accounting from './pages/Accounting';
import Reports from './pages/Reports';
import Settings from './pages/Settings';
import Notifications from './pages/Notifications';
import GRN from './pages/GRN';

// Advanced Finance Pages
import ChartOfAccounts from './pages/ChartOfAccounts';
import GeneralLedger from './pages/GeneralLedger';
import FinancialReports from './pages/FinancialReports';

// Admin Pages
import SystemAdmin from './pages/SystemAdmin';
import AuditLogs from './pages/AuditLogs';
import UserManagement from './pages/UserManagement';
import PackagingRules from './pages/PackagingRules';

// Documentation
import Documentation from './pages/Documentation';

// Simple Finance Pages
import Investors from './pages/Investors';
import QuickTransactions from './pages/QuickTransactions';
import BankAccounts from './pages/BankAccounts';

// Manufacturing Pages
import RawMaterials from './pages/RawMaterials';
import BillOfMaterials from './pages/BillOfMaterials';
import WorkOrders from './pages/WorkOrders';
import ManufacturingDashboard from './pages/ManufacturingDashboard';

// RM Procurement Pages
import RMSuppliers from './pages/RMSuppliers';
import RMPurchaseOrders from './pages/RMPurchaseOrders';
import RMGRN from './pages/RMGRN';
import RMGRNReturns from './pages/RMGRNReturns';

// Payroll Pages
import Departments from './pages/payroll/Departments';
import Designations from './pages/payroll/Designations';
import Employees from './pages/payroll/Employees';
import SalaryStructure from './pages/payroll/SalaryStructure';
import LeaveManagement from './pages/payroll/LeaveManagement';
import Advances from './pages/payroll/Advances';
import Payroll from './pages/payroll/Payroll';
import PayrollReports from './pages/payroll/PayrollReports';
import TaskAssignments from './pages/payroll/TaskAssignments';
import AttendanceTracking from './pages/payroll/AttendanceTracking';

// Employee Portal Pages
import MyDashboard from './pages/MyDashboard';
import MyTasks from './pages/MyTasks';
import TaskCategories from './pages/TaskCategories';
import MyProfile from './pages/MyProfile';

// Layout
import Layout from './components/Layout';

// Protected Route Component
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="spinner"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <Layout>{children}</Layout>;
};

// Public Route (redirect if already authenticated)
const PublicRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="spinner"></div>
      </div>
    );
  }

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return children;
};

function AppRoutes() {
  return (
    <Routes>
      {/* Public Routes */}
      <Route path="/login" element={<PublicRoute><Login /></PublicRoute>} />
      <Route path="/register" element={<PublicRoute><Register /></PublicRoute>} />

      {/* Protected Routes */}
      <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
      <Route path="/products" element={<ProtectedRoute><Products /></ProtectedRoute>} />
      <Route path="/inventory" element={<ProtectedRoute><Inventory /></ProtectedRoute>} />
      <Route path="/customers" element={<ProtectedRoute><Customers /></ProtectedRoute>} />
      <Route path="/suppliers" element={<ProtectedRoute><Suppliers /></ProtectedRoute>} />
      <Route path="/sales-orders" element={<ProtectedRoute><SalesOrders /></ProtectedRoute>} />
      <Route path="/invoices" element={<ProtectedRoute><Invoices /></ProtectedRoute>} />
      <Route path="/purchase-orders" element={<ProtectedRoute><PurchaseOrders /></ProtectedRoute>} />
      <Route path="/grn" element={<ProtectedRoute><GRN /></ProtectedRoute>} />
      <Route path="/payments" element={<ProtectedRoute><Payments /></ProtectedRoute>} />
      <Route path="/accounting" element={<ProtectedRoute><Accounting /></ProtectedRoute>} />
      <Route path="/reports" element={<ProtectedRoute><Reports /></ProtectedRoute>} />
      <Route path="/settings" element={<ProtectedRoute><Settings /></ProtectedRoute>} />
      <Route path="/notifications" element={<ProtectedRoute><Notifications /></ProtectedRoute>} />

      {/* Advanced Finance Routes */}
      <Route path="/chart-of-accounts" element={<ProtectedRoute><ChartOfAccounts /></ProtectedRoute>} />
      <Route path="/general-ledger" element={<ProtectedRoute><GeneralLedger /></ProtectedRoute>} />
      <Route path="/financial-reports" element={<ProtectedRoute><FinancialReports /></ProtectedRoute>} />

      {/* Admin Routes */}
      <Route path="/system-admin" element={<ProtectedRoute><SystemAdmin /></ProtectedRoute>} />

      {/* Simple Finance Routes */}
      <Route path="/investors" element={<ProtectedRoute><Investors /></ProtectedRoute>} />
      <Route path="/quick-transactions" element={<ProtectedRoute><QuickTransactions /></ProtectedRoute>} />
      <Route path="/bank-accounts" element={<ProtectedRoute><BankAccounts /></ProtectedRoute>} />

      {/* Manufacturing Routes */}
      <Route path="/manufacturing" element={<ProtectedRoute><ManufacturingDashboard /></ProtectedRoute>} />
      <Route path="/raw-materials" element={<ProtectedRoute><RawMaterials /></ProtectedRoute>} />
      <Route path="/bom" element={<ProtectedRoute><BillOfMaterials /></ProtectedRoute>} />
      <Route path="/work-orders" element={<ProtectedRoute><WorkOrders /></ProtectedRoute>} />

      {/* RM Procurement Routes */}
      <Route path="/rm-suppliers" element={<ProtectedRoute><RMSuppliers /></ProtectedRoute>} />
      <Route path="/rm-purchase-orders" element={<ProtectedRoute><RMPurchaseOrders /></ProtectedRoute>} />
      <Route path="/rm-grn" element={<ProtectedRoute><RMGRN /></ProtectedRoute>} />
      <Route path="/rm-grn-returns" element={<ProtectedRoute><RMGRNReturns /></ProtectedRoute>} />

      {/* Payroll Routes */}
      <Route path="/departments" element={<ProtectedRoute><Departments /></ProtectedRoute>} />
      <Route path="/designations" element={<ProtectedRoute><Designations /></ProtectedRoute>} />
      <Route path="/employees" element={<ProtectedRoute><Employees /></ProtectedRoute>} />
      <Route path="/salary-structure" element={<ProtectedRoute><SalaryStructure /></ProtectedRoute>} />
      <Route path="/leave-management" element={<ProtectedRoute><LeaveManagement /></ProtectedRoute>} />
      <Route path="/advances" element={<ProtectedRoute><Advances /></ProtectedRoute>} />
      <Route path="/payroll" element={<ProtectedRoute><Payroll /></ProtectedRoute>} />
      <Route path="/payroll-reports" element={<ProtectedRoute><PayrollReports /></ProtectedRoute>} />
      <Route path="/task-assignments" element={<ProtectedRoute><TaskAssignments /></ProtectedRoute>} />
      <Route path="/attendance" element={<ProtectedRoute><AttendanceTracking /></ProtectedRoute>} />
      <Route path="/documentation" element={<ProtectedRoute><Documentation /></ProtectedRoute>} />
      <Route path="/audit-logs" element={<ProtectedRoute><AuditLogs /></ProtectedRoute>} />
      <Route path="/user-management" element={<ProtectedRoute><UserManagement /></ProtectedRoute>} />
      <Route path="/packaging-rules" element={<ProtectedRoute><PackagingRules /></ProtectedRoute>} />

      {/* Employee Portal Routes */}
      <Route path="/my-dashboard" element={<ProtectedRoute><MyDashboard /></ProtectedRoute>} />
      <Route path="/my-tasks" element={<ProtectedRoute><MyTasks /></ProtectedRoute>} />
      <Route path="/my-profile" element={<ProtectedRoute><MyProfile /></ProtectedRoute>} />
      <Route path="/task-categories" element={<ProtectedRoute><TaskCategories /></ProtectedRoute>} />

      {/* Default redirect */}
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
        <Toaster 
          position="top-right" 
          richColors 
          closeButton
          toastOptions={{
            style: {
              fontFamily: 'Inter, sans-serif',
            },
          }}
        />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
