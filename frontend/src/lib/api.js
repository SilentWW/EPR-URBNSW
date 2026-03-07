import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API_BASE = `${BACKEND_URL}/api`;

// Create axios instance
const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('erp_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('erp_token');
      localStorage.removeItem('erp_user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  login: (email, password) => api.post('/auth/login', { email, password }),
  register: (data) => api.post('/auth/register', data),
  getMe: () => api.get('/auth/me'),
};

// Company API
export const companyAPI = {
  get: () => api.get('/company'),
  update: (data) => api.put('/company', data),
  getWooSettings: () => api.get('/company/woocommerce'),
  updateWooSettings: (data) => api.put('/company/woocommerce', data),
};

// Users API
export const usersAPI = {
  getAll: () => api.get('/users'),
  create: (data) => api.post('/users', data),
  updateRole: (userId, role) => api.put(`/users/${userId}/role?role=${role}`),
  delete: (userId) => api.delete(`/users/${userId}`),
};

// Products API
export const productsAPI = {
  getAll: (params) => api.get('/products', { params }),
  getOne: (id) => api.get(`/products/${id}`),
  create: (data) => api.post('/products', data),
  update: (id, data) => api.put(`/products/${id}`, data),
  delete: (id) => api.delete(`/products/${id}`),
  getCategories: () => api.get('/products/categories/list'),
};

// Inventory API
export const inventoryAPI = {
  getMovements: (productId) => api.get('/inventory/movements', { params: { product_id: productId } }),
  createMovement: (data) => api.post('/inventory/movements', data),
  getLowStock: () => api.get('/inventory/low-stock'),
  getValuation: () => api.get('/inventory/valuation'),
};

// Customers API
export const customersAPI = {
  getAll: (search) => api.get('/customers', { params: { search } }),
  getOne: (id) => api.get(`/customers/${id}`),
  create: (data) => api.post('/customers', data),
  update: (id, data) => api.put(`/customers/${id}`, data),
  delete: (id) => api.delete(`/customers/${id}`),
};

// Suppliers API
export const suppliersAPI = {
  getAll: (search) => api.get('/suppliers', { params: { search } }),
  getOne: (id) => api.get(`/suppliers/${id}`),
  create: (data) => api.post('/suppliers', data),
  update: (id, data) => api.put(`/suppliers/${id}`, data),
  delete: (id) => api.delete(`/suppliers/${id}`),
};

// Sales Orders API
export const salesOrdersAPI = {
  getAll: (params) => api.get('/sales-orders', { params }),
  getOne: (id) => api.get(`/sales-orders/${id}`),
  create: (data) => api.post('/sales-orders', data),
  update: (id, data) => api.put(`/sales-orders/${id}`, data),
  return: (id) => api.post(`/sales-orders/${id}/return`),
};

// Invoices API
export const invoicesAPI = {
  getAll: (status) => api.get('/invoices', { params: { status } }),
  getOne: (id) => api.get(`/invoices/${id}`),
};

// Purchase Orders API
export const purchaseOrdersAPI = {
  getAll: (params) => api.get('/purchase-orders', { params }),
  getOne: (id) => api.get(`/purchase-orders/${id}`),
  create: (data) => api.post('/purchase-orders', data),
  update: (id, data) => api.put(`/purchase-orders/${id}`, data),
  delete: (id) => api.delete(`/purchase-orders/${id}`),
  receive: (id) => api.post(`/purchase-orders/${id}/receive`),
};

// Payments API
export const paymentsAPI = {
  getAll: (params) => api.get('/payments', { params }),
  create: (data) => api.post('/payments', data),
  getSummary: () => api.get('/payments/summary'),
};

// Accounting API
export const accountingAPI = {
  getEntries: (params) => api.get('/accounting/entries', { params }),
  createEntry: (data) => api.post('/accounting/entries', data),
  getProfitLoss: (params) => api.get('/accounting/profit-loss', { params }),
  getReceivables: () => api.get('/accounting/receivables'),
  getPayables: () => api.get('/accounting/payables'),
};

// Dashboard API
export const dashboardAPI = {
  getSummary: () => api.get('/dashboard/summary'),
  getSalesChart: (period) => api.get('/dashboard/sales-chart', { params: { period } }),
  getTopProducts: (limit) => api.get('/dashboard/top-products', { params: { limit } }),
};

// Notifications API
export const notificationsAPI = {
  getAll: () => api.get('/notifications'),
};

// Audit Logs API
export const auditLogsAPI = {
  getAll: (limit) => api.get('/audit-logs', { params: { limit } }),
};

// Reports API
export const reportsAPI = {
  getSales: (params) => api.get('/reports/sales', { params }),
};

// RM Procurement API
export const rmProcurementAPI = {
  // RM Suppliers
  getSuppliers: (search) => api.get('/rm-procurement/suppliers', { params: { search } }),
  getSupplier: (id) => api.get(`/rm-procurement/suppliers/${id}`),
  createSupplier: (data) => api.post('/rm-procurement/suppliers', data),
  updateSupplier: (id, data) => api.put(`/rm-procurement/suppliers/${id}`, data),
  deleteSupplier: (id) => api.delete(`/rm-procurement/suppliers/${id}`),
  
  // RM Purchase Orders
  getPurchaseOrders: (params) => api.get('/rm-procurement/purchase-orders', { params }),
  getPurchaseOrder: (id) => api.get(`/rm-procurement/purchase-orders/${id}`),
  createPurchaseOrder: (data) => api.post('/rm-procurement/purchase-orders', data),
  updatePurchaseOrder: (id, data) => api.put(`/rm-procurement/purchase-orders/${id}`, data),
  approvePurchaseOrder: (id) => api.post(`/rm-procurement/purchase-orders/${id}/approve`),
  deletePurchaseOrder: (id) => api.delete(`/rm-procurement/purchase-orders/${id}`),
  recordPayment: (id, data) => api.post(`/rm-procurement/purchase-orders/${id}/record-payment`, null, { params: data }),
  
  // RM GRN
  getGRNs: (params) => api.get('/rm-procurement/grn', { params }),
  getGRN: (id) => api.get(`/rm-procurement/grn/${id}`),
  createGRN: (data) => api.post('/rm-procurement/grn', data),
  
  // RM GRN Returns
  getGRNReturns: (params) => api.get('/rm-procurement/grn-returns', { params }),
  createGRNReturn: (data) => api.post('/rm-procurement/grn-returns', data),
  
  // Accounts Payable
  getAccountsPayable: (params) => api.get('/rm-procurement/accounts-payable', { params }),
};

// Payroll API
export const payrollAPI = {
  // Departments
  getDepartments: () => api.get('/payroll/departments'),
  createDepartment: (data) => api.post('/payroll/departments', data),
  updateDepartment: (id, data) => api.put(`/payroll/departments/${id}`, data),
  deleteDepartment: (id) => api.delete(`/payroll/departments/${id}`),
  
  // Employees
  getEmployees: (params) => api.get('/payroll/employees', { params }),
  getEmployee: (id) => api.get(`/payroll/employees/${id}`),
  getNextEmployeeId: () => api.get('/payroll/employees/next-id/generate'),
  createEmployee: (data) => api.post('/payroll/employees', data),
  updateEmployee: (id, data) => api.put(`/payroll/employees/${id}`, data),
  terminateEmployee: (id) => api.delete(`/payroll/employees/${id}`),
  
  // Salary Structure
  getSalaryStructure: () => api.get('/payroll/salary-structure'),
  updateSalaryStructure: (data) => api.put('/payroll/salary-structure', data),
  addAllowance: (data) => api.post('/payroll/salary-structure/allowances', data),
  deleteAllowance: (id) => api.delete(`/payroll/salary-structure/allowances/${id}`),
  
  // Leave Management
  getLeaveBalances: (params) => api.get('/payroll/leave/balances', { params }),
  updateLeaveBalance: (employeeId, data) => api.put(`/payroll/leave/balances/${employeeId}`, data),
  getLeaveRequests: (params) => api.get('/payroll/leave/requests', { params }),
  createLeaveRequest: (data) => api.post('/payroll/leave/requests', data),
  approveLeave: (id) => api.post(`/payroll/leave/requests/${id}/approve`),
  rejectLeave: (id, reason) => api.post(`/payroll/leave/requests/${id}/reject`, null, { params: { reason } }),
  
  // Advances & Loans
  getAdvances: (params) => api.get('/payroll/advances', { params }),
  createAdvance: (data) => api.post('/payroll/advances', data),
  
  // Payroll Processing
  getPayrolls: (params) => api.get('/payroll/payrolls', { params }),
  getPayroll: (id) => api.get(`/payroll/payrolls/${id}`),
  createPayroll: (data) => api.post('/payroll/payrolls', data),
  updatePayrollItem: (payrollId, itemId, data) => api.put(`/payroll/payrolls/${payrollId}/items/${itemId}`, data),
  submitPayroll: (id) => api.post(`/payroll/payrolls/${id}/submit`),
  approvePayroll: (id) => api.post(`/payroll/payrolls/${id}/approve`),
  processPayroll: (id, bankAccountId) => api.post(`/payroll/payrolls/${id}/process`, null, { params: { bank_account_id: bankAccountId } }),
  deletePayroll: (id) => api.delete(`/payroll/payrolls/${id}`),
  
  // Task Payments
  getTaskPayments: (params) => api.get('/payroll/task-payments', { params }),
  createTaskPayment: (data) => api.post('/payroll/task-payments', data),
  
  // Reports
  getPayslip: (payrollId, employeeId) => api.get(`/payroll/reports/payslip/${payrollId}/${employeeId}`),
  getPayrollSummary: (params) => api.get('/payroll/reports/summary', { params }),
  getEpfEtfReport: (params) => api.get('/payroll/reports/epf-etf', { params }),
  getDepartmentReport: (params) => api.get('/payroll/reports/department', { params }),
};

// Seed Demo Data
export const seedDemoData = () => api.post('/seed-demo-data');

export default api;
