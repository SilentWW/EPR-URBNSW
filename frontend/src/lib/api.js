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

// Seed Demo Data
export const seedDemoData = () => api.post('/seed-demo-data');

export default api;
