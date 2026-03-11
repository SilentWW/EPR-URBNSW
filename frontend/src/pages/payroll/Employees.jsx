import React, { useState, useEffect } from 'react';
import { payrollAPI } from '../../lib/api';
import api from '../../lib/api';
import { Card, CardContent } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Badge } from '../../components/ui/badge';
import { Textarea } from '../../components/ui/textarea';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../../components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../../components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../../components/ui/table';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '../../components/ui/dropdown-menu';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs';
import { Checkbox } from '../../components/ui/checkbox';
import { 
  Plus, MoreHorizontal, Pencil, Trash2, Loader2, Users, Eye, Search, 
  UserCheck, UserX, Briefcase, AlertTriangle, Shield, ChevronDown, ChevronRight
} from 'lucide-react';
import { toast } from 'sonner';

const formatCurrency = (amount) => {
  return new Intl.NumberFormat('en-LK', {
    style: 'currency',
    currency: 'LKR',
    minimumFractionDigits: 0,
  }).format(amount || 0);
};

// Permission modules configuration
const PERMISSION_MODULES = {
  'Main Menu': [
    { module: 'dashboard', label: 'Dashboard' },
    { module: 'products', label: 'Products' },
    { module: 'inventory', label: 'Inventory' },
    { module: 'grn', label: 'GRN' },
    { module: 'packaging-rules', label: 'Packaging Rules' },
    { module: 'customers', label: 'Customers' },
    { module: 'suppliers', label: 'Suppliers' },
    { module: 'sales-orders', label: 'Sales Orders' },
    { module: 'invoices', label: 'Invoices' },
    { module: 'purchase-orders', label: 'Purchase Orders' },
    { module: 'payments', label: 'Payments' },
    { module: 'reports', label: 'Reports' },
  ],
  'Manufacturing': [
    { module: 'manufacturing', label: 'Manufacturing Dashboard' },
    { module: 'raw-materials', label: 'Raw Materials' },
    { module: 'rm-suppliers', label: 'RM Suppliers' },
    { module: 'rm-purchase-orders', label: 'RM Purchase Orders' },
    { module: 'rm-grn', label: 'RM GRN' },
    { module: 'rm-grn-returns', label: 'RM GRN Returns' },
    { module: 'bill-of-materials', label: 'Bill of Materials' },
    { module: 'work-orders', label: 'Work Orders' },
  ],
  'Finance / Accounts': [
    { module: 'quick-transactions', label: 'Quick Transactions' },
    { module: 'investors', label: 'Investors' },
    { module: 'bank-accounts', label: 'Bank Accounts' },
    { module: 'chart-of-accounts', label: 'Chart of Accounts' },
    { module: 'general-ledger', label: 'General Ledger' },
    { module: 'financial-reports', label: 'Financial Reports' },
    { module: 'accounting', label: 'Accounting' },
  ],
  'HR / Payroll': [
    { module: 'departments', label: 'Departments' },
    { module: 'designations', label: 'Designations' },
    { module: 'employees', label: 'Employees' },
    { module: 'attendance', label: 'Attendance' },
    { module: 'salary-structure', label: 'Salary Structure' },
    { module: 'leave-management', label: 'Leave Management' },
    { module: 'advances', label: 'Advances & Loans' },
    { module: 'task-assignments', label: 'Task Assignments' },
    { module: 'payroll', label: 'Payroll' },
    { module: 'payroll-reports', label: 'Payroll Reports' },
    { module: 'task-categories', label: 'Task Categories' },
  ],
  'Employee Portal': [
    { module: 'my-dashboard', label: 'My Dashboard' },
    { module: 'my-tasks', label: 'My Tasks' },
  ],
  'Admin / Settings': [
    { module: 'settings', label: 'Settings' },
    { module: 'notifications', label: 'Notifications' },
    { module: 'user-management', label: 'User Management' },
    { module: 'system-admin', label: 'System Admin' },
    { module: 'audit-logs', label: 'Audit Logs' },
    { module: 'documentation', label: 'Documentation' },
  ],
};

const employeeTypeColors = {
  permanent: 'bg-blue-100 text-blue-700',
  casual: 'bg-amber-100 text-amber-700',
  freelancer: 'bg-purple-100 text-purple-700',
  contract: 'bg-emerald-100 text-emerald-700',
};

const statusColors = {
  active: 'bg-green-100 text-green-700',
  inactive: 'bg-slate-100 text-slate-700',
  terminated: 'bg-red-100 text-red-700',
};

const EMPLOYEE_TYPES = [
  { value: 'permanent', label: 'Permanent Staff' },
  { value: 'casual', label: 'Casual Staff' },
  { value: 'freelancer', label: 'Freelancer' },
  { value: 'contract', label: 'Contract Staff' },
];

const PAYMENT_FREQUENCIES = [
  { value: 'monthly', label: 'Monthly' },
  { value: 'weekly', label: 'Weekly' },
  { value: 'daily', label: 'Daily' },
  { value: 'per_task', label: 'Per Task' },
];

const initialFormData = {
  employee_id: '',
  first_name: '',
  last_name: '',
  email: '',
  phone: '',
  nic: '',
  address: '',
  department_id: 'none',
  designation_id: 'none',  // Link to designation
  employee_type: 'permanent',
  payment_frequency: 'monthly',
  basic_salary: '',
  hourly_rate: '',
  daily_rate: '',
  bank_name: '',
  bank_account_number: '',
  bank_branch: '',
  join_date: '',
  contract_end_date: '',
  notes: '',
  user_id: 'none',  // Link to user account
  permissions: [],  // Employee-specific permissions
};

export const Employees = () => {
  const [employees, setEmployees] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [designations, setDesignations] = useState([]);  // Available designations
  const [users, setUsers] = useState([]);  // Available users for linking
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('active');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [terminateDialogOpen, setTerminateDialogOpen] = useState(false);
  const [selectedEmployee, setSelectedEmployee] = useState(null);
  const [employeeDetails, setEmployeeDetails] = useState(null);
  const [formData, setFormData] = useState(initialFormData);
  const [submitting, setSubmitting] = useState(false);

  const fetchData = async () => {
    try {
      const [empRes, deptRes, desigRes, usersRes] = await Promise.all([
        payrollAPI.getEmployees({ search, employee_type: typeFilter, status: statusFilter }),
        payrollAPI.getDepartments(),
        api.get('/payroll/designations').catch(() => ({ data: [] })),  // Fetch designations
        api.get('/users').catch(() => ({ data: [] })),  // Fetch users for linking
      ]);
      setEmployees(empRes.data);
      setDepartments(deptRes.data);
      setDesignations(desigRes.data || []);
      setUsers(usersRes.data || []);
    } catch (error) {
      toast.error('Failed to fetch data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [search, typeFilter, statusFilter]);

  const handleOpenDialog = async (employee = null) => {
    if (employee) {
      setSelectedEmployee(employee);
      setFormData({
        employee_id: employee.employee_id,
        first_name: employee.first_name,
        last_name: employee.last_name,
        email: employee.email || '',
        phone: employee.phone || '',
        nic: employee.nic || '',
        address: employee.address || '',
        department_id: employee.department_id || 'none',
        designation_id: employee.designation_id || 'none',
        employee_type: employee.employee_type,
        payment_frequency: employee.payment_frequency,
        basic_salary: employee.basic_salary?.toString() || '',
        hourly_rate: employee.hourly_rate?.toString() || '',
        daily_rate: employee.daily_rate?.toString() || '',
        bank_name: employee.bank_name || '',
        bank_account_number: employee.bank_account_number || '',
        bank_branch: employee.bank_branch || '',
        join_date: employee.join_date || '',
        contract_end_date: employee.contract_end_date || '',
        notes: employee.notes || '',
        user_id: employee.user_id || 'none',
        permissions: employee.permissions || [],
      });
    } else {
      setSelectedEmployee(null);
      // Get next employee ID
      try {
        const response = await payrollAPI.getNextEmployeeId();
        setFormData({ ...initialFormData, employee_id: response.data.next_id });
      } catch {
        setFormData(initialFormData);
      }
    }
    setDialogOpen(true);
  };

  const handleViewEmployee = async (employee) => {
    try {
      const response = await payrollAPI.getEmployee(employee.id);
      setEmployeeDetails(response.data);
      setViewDialogOpen(true);
    } catch (error) {
      toast.error('Failed to load employee details');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);

    try {
      const payload = {
        ...formData,
        basic_salary: parseFloat(formData.basic_salary) || 0,
        hourly_rate: parseFloat(formData.hourly_rate) || 0,
        daily_rate: parseFloat(formData.daily_rate) || 0,
        department_id: formData.department_id === 'none' ? null : (formData.department_id || null),
        designation_id: formData.designation_id === 'none' ? null : (formData.designation_id || null),
        user_id: formData.user_id === 'none' ? null : (formData.user_id || null),
      };

      if (selectedEmployee) {
        await payrollAPI.updateEmployee(selectedEmployee.id, payload);
        toast.success('Employee updated successfully');
      } else {
        await payrollAPI.createEmployee(payload);
        toast.success('Employee created successfully');
      }
      setDialogOpen(false);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Operation failed');
    } finally {
      setSubmitting(false);
    }
  };

  const handleTerminate = async () => {
    try {
      await payrollAPI.terminateEmployee(selectedEmployee.id);
      toast.success('Employee terminated successfully');
      setTerminateDialogOpen(false);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to terminate employee');
    }
  };

  const stats = {
    total: employees.length,
    permanent: employees.filter(e => e.employee_type === 'permanent').length,
    casual: employees.filter(e => e.employee_type === 'casual').length,
    freelancer: employees.filter(e => e.employee_type === 'freelancer').length,
  };

  return (
    <div className="space-y-6" data-testid="employees-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900" style={{ fontFamily: 'Outfit, sans-serif' }}>
            Employees
          </h2>
          <p className="text-slate-500 mt-1">{employees.length} employees</p>
        </div>
        <Button onClick={() => handleOpenDialog()} className="gap-2 bg-indigo-600 hover:bg-indigo-700" data-testid="add-employee-btn">
          <Plus className="w-4 h-4" />
          Add Employee
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-indigo-100 rounded-lg">
                <Users className="w-5 h-5 text-indigo-600" />
              </div>
              <div>
                <p className="text-sm text-slate-500">Total</p>
                <p className="text-2xl font-bold">{stats.total}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <UserCheck className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-slate-500">Permanent</p>
                <p className="text-2xl font-bold">{stats.permanent}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-amber-100 rounded-lg">
                <Briefcase className="w-5 h-5 text-amber-600" />
              </div>
              <div>
                <p className="text-sm text-slate-500">Casual</p>
                <p className="text-2xl font-bold">{stats.casual}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 rounded-lg">
                <Users className="w-5 h-5 text-purple-600" />
              </div>
              <div>
                <p className="text-sm text-slate-500">Freelancer</p>
                <p className="text-2xl font-bold">{stats.freelancer}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-wrap gap-4">
            <div className="relative flex-1 min-w-[200px] max-w-md">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <Input
                placeholder="Search employees..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9"
                data-testid="search-employees"
              />
            </div>
            <Select value={typeFilter} onValueChange={setTypeFilter}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                {EMPLOYEE_TYPES.map(t => (
                  <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="active">Active</SelectItem>
                <SelectItem value="inactive">Inactive</SelectItem>
                <SelectItem value="terminated">Terminated</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Employees Table */}
      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
            </div>
          ) : employees.length === 0 ? (
            <div className="text-center py-16">
              <Users className="w-12 h-12 text-slate-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-slate-900">No employees found</h3>
              <p className="text-slate-500 mt-1">Add your first employee to get started.</p>
              <Button onClick={() => handleOpenDialog()} className="mt-4 bg-indigo-600 hover:bg-indigo-700">
                Add Employee
              </Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="table-header">
                  <TableHead className="table-header-cell">Employee ID</TableHead>
                  <TableHead className="table-header-cell">Name</TableHead>
                  <TableHead className="table-header-cell">Department</TableHead>
                  <TableHead className="table-header-cell">Type</TableHead>
                  <TableHead className="table-header-cell text-right">Basic Salary</TableHead>
                  <TableHead className="table-header-cell">Status</TableHead>
                  <TableHead className="table-header-cell w-12"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {employees.map((emp) => (
                  <TableRow key={emp.id} className="table-row" data-testid={`emp-row-${emp.id}`}>
                    <TableCell className="table-cell font-medium">{emp.employee_id}</TableCell>
                    <TableCell className="table-cell">{emp.full_name}</TableCell>
                    <TableCell className="table-cell text-slate-500">{emp.department_name}</TableCell>
                    <TableCell className="table-cell">
                      <Badge className={employeeTypeColors[emp.employee_type]}>{emp.employee_type}</Badge>
                    </TableCell>
                    <TableCell className="table-cell text-right">{formatCurrency(emp.basic_salary)}</TableCell>
                    <TableCell className="table-cell">
                      <Badge className={statusColors[emp.status]}>{emp.status}</Badge>
                    </TableCell>
                    <TableCell className="table-cell">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon">
                            <MoreHorizontal className="w-4 h-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => handleViewEmployee(emp)}>
                            <Eye className="w-4 h-4 mr-2" />
                            View Details
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => handleOpenDialog(emp)}>
                            <Pencil className="w-4 h-4 mr-2" />
                            Edit
                          </DropdownMenuItem>
                          {emp.status === 'active' && (
                            <>
                              <DropdownMenuSeparator />
                              <DropdownMenuItem
                                className="text-red-600"
                                onClick={() => {
                                  setSelectedEmployee(emp);
                                  setTerminateDialogOpen(true);
                                }}
                              >
                                <UserX className="w-4 h-4 mr-2" />
                                Terminate
                              </DropdownMenuItem>
                            </>
                          )}
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Add/Edit Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto" data-testid="employee-dialog">
          <DialogHeader>
            <DialogTitle style={{ fontFamily: 'Outfit, sans-serif' }}>
              {selectedEmployee ? 'Edit Employee' : 'Add Employee'}
            </DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit}>
            <Tabs defaultValue="basic" className="w-full">
              <TabsList className="grid w-full grid-cols-4">
                <TabsTrigger value="basic">Basic Info</TabsTrigger>
                <TabsTrigger value="salary">Salary & Bank</TabsTrigger>
                <TabsTrigger value="other">Other</TabsTrigger>
                <TabsTrigger value="permissions" className="flex items-center gap-1">
                  <Shield className="w-3 h-3" /> Permissions
                </TabsTrigger>
              </TabsList>

              <TabsContent value="basic" className="space-y-4 mt-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Employee ID *</Label>
                    <Input
                      value={formData.employee_id}
                      onChange={(e) => setFormData({ ...formData, employee_id: e.target.value })}
                      placeholder="EMP0001"
                      required
                      disabled={!!selectedEmployee}
                      data-testid="emp-id-input"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Department</Label>
                    <Select 
                      value={formData.department_id} 
                      onValueChange={(v) => setFormData({ ...formData, department_id: v })}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select department" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="none">No Department</SelectItem>
                        {departments.map(d => (
                          <SelectItem key={d.id} value={d.id}>{d.name}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Link to User Account</Label>
                    <Select 
                      value={formData.user_id} 
                      onValueChange={(v) => setFormData({ ...formData, user_id: v })}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select user account" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="none">Not Linked</SelectItem>
                        {users.map(u => (
                          <SelectItem key={u.id} value={u.id}>
                            {u.full_name || u.email} ({u.email})
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <p className="text-xs text-slate-500">Link this employee to a user account for portal access</p>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Designation</Label>
                  <Select 
                    value={formData.designation_id} 
                    onValueChange={(v) => setFormData({ ...formData, designation_id: v })}
                  >
                    <SelectTrigger data-testid="emp-designation-select">
                      <SelectValue placeholder="Select designation" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">No Designation</SelectItem>
                      {designations
                        .filter(d => !formData.department_id || formData.department_id === 'none' || !d.department_id || d.department_id === formData.department_id)
                        .map(d => (
                          <SelectItem key={d.id} value={d.id}>
                            {d.name} {d.department_name && d.department_name !== 'All Departments' ? `(${d.department_name})` : ''}
                          </SelectItem>
                        ))}
                    </SelectContent>
                  </Select>
                  <p className="text-xs text-slate-500">Job title and permission level</p>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>First Name *</Label>
                    <Input
                      value={formData.first_name}
                      onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                      required
                      data-testid="emp-firstname"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Last Name *</Label>
                    <Input
                      value={formData.last_name}
                      onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                      required
                      data-testid="emp-lastname"
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Email</Label>
                    <Input
                      type="email"
                      value={formData.email}
                      onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Phone</Label>
                    <Input
                      value={formData.phone}
                      onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>NIC Number</Label>
                    <Input
                      value={formData.nic}
                      onChange={(e) => setFormData({ ...formData, nic: e.target.value })}
                      placeholder="National ID"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Employee Type *</Label>
                    <Select 
                      value={formData.employee_type} 
                      onValueChange={(v) => setFormData({ ...formData, employee_type: v })}
                    >
                      <SelectTrigger data-testid="emp-type-select">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {EMPLOYEE_TYPES.map(t => (
                          <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="salary" className="space-y-4 mt-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Payment Frequency</Label>
                    <Select 
                      value={formData.payment_frequency} 
                      onValueChange={(v) => setFormData({ ...formData, payment_frequency: v })}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {PAYMENT_FREQUENCIES.map(f => (
                          <SelectItem key={f.value} value={f.value}>{f.label}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Basic Salary (Monthly)</Label>
                    <Input
                      type="number"
                      value={formData.basic_salary}
                      onChange={(e) => setFormData({ ...formData, basic_salary: e.target.value })}
                      placeholder="0.00"
                      data-testid="emp-basic-salary"
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Hourly Rate</Label>
                    <Input
                      type="number"
                      value={formData.hourly_rate}
                      onChange={(e) => setFormData({ ...formData, hourly_rate: e.target.value })}
                      placeholder="0.00"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Daily Rate</Label>
                    <Input
                      type="number"
                      value={formData.daily_rate}
                      onChange={(e) => setFormData({ ...formData, daily_rate: e.target.value })}
                      placeholder="0.00"
                    />
                  </div>
                </div>
                <div className="pt-4 border-t">
                  <h4 className="font-medium mb-3">Bank Details</h4>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Bank Name</Label>
                      <Input
                        value={formData.bank_name}
                        onChange={(e) => setFormData({ ...formData, bank_name: e.target.value })}
                        placeholder="e.g., Commercial Bank"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Branch</Label>
                      <Input
                        value={formData.bank_branch}
                        onChange={(e) => setFormData({ ...formData, bank_branch: e.target.value })}
                        placeholder="Branch name"
                      />
                    </div>
                  </div>
                  <div className="space-y-2 mt-4">
                    <Label>Account Number</Label>
                    <Input
                      value={formData.bank_account_number}
                      onChange={(e) => setFormData({ ...formData, bank_account_number: e.target.value })}
                      placeholder="Bank account number"
                    />
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="other" className="space-y-4 mt-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label>Join Date</Label>
                    <Input
                      type="date"
                      value={formData.join_date}
                      onChange={(e) => setFormData({ ...formData, join_date: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Contract End Date</Label>
                    <Input
                      type="date"
                      value={formData.contract_end_date}
                      onChange={(e) => setFormData({ ...formData, contract_end_date: e.target.value })}
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label>Address</Label>
                  <Textarea
                    value={formData.address}
                    onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                    rows={2}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Notes</Label>
                  <Textarea
                    value={formData.notes}
                    onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                    rows={2}
                  />
                </div>
              </TabsContent>

              <TabsContent value="permissions" className="space-y-4 mt-4">
                <div className="text-sm text-slate-500 mb-4">
                  Select which modules this employee can access. Only checked items will be visible in their menu.
                </div>
                
                {Object.entries(PERMISSION_MODULES).map(([category, modules]) => {
                  const categoryModules = modules.map(m => m.module);
                  const checkedInCategory = categoryModules.filter(m => formData.permissions?.includes(m));
                  const allChecked = checkedInCategory.length === categoryModules.length;
                  const someChecked = checkedInCategory.length > 0 && !allChecked;
                  
                  return (
                    <div key={category} className="border rounded-lg p-4">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-2">
                          <Checkbox
                            checked={allChecked}
                            ref={(el) => {
                              if (el && someChecked) {
                                el.dataset.state = 'indeterminate';
                              }
                            }}
                            onCheckedChange={(checked) => {
                              if (checked) {
                                setFormData({
                                  ...formData,
                                  permissions: [...new Set([...(formData.permissions || []), ...categoryModules])]
                                });
                              } else {
                                setFormData({
                                  ...formData,
                                  permissions: (formData.permissions || []).filter(p => !categoryModules.includes(p))
                                });
                              }
                            }}
                          />
                          <span className="font-medium text-slate-900">{category}</span>
                          <span className="text-xs text-slate-400">
                            ({checkedInCategory.length}/{categoryModules.length})
                          </span>
                        </div>
                        <span className="text-xs text-slate-500">Select All</span>
                      </div>
                      
                      <div className="grid grid-cols-2 md:grid-cols-3 gap-2 pl-6">
                        {modules.map(({ module, label }) => (
                          <div key={module} className="flex items-center space-x-2">
                            <Checkbox
                              id={`perm-${module}`}
                              checked={formData.permissions?.includes(module)}
                              onCheckedChange={(checked) => {
                                if (checked) {
                                  setFormData({
                                    ...formData,
                                    permissions: [...(formData.permissions || []), module]
                                  });
                                } else {
                                  setFormData({
                                    ...formData,
                                    permissions: (formData.permissions || []).filter(p => p !== module)
                                  });
                                }
                              }}
                            />
                            <label
                              htmlFor={`perm-${module}`}
                              className="text-sm cursor-pointer select-none"
                            >
                              {label}
                            </label>
                          </div>
                        ))}
                      </div>
                    </div>
                  );
                })}
                
                <div className="pt-3 border-t">
                  <div className="flex gap-2">
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        const allPermissions = Object.values(PERMISSION_MODULES).flat().map(m => m.module);
                        setFormData({ ...formData, permissions: allPermissions });
                      }}
                    >
                      Select All
                    </Button>
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => setFormData({ ...formData, permissions: [] })}
                    >
                      Clear All
                    </Button>
                  </div>
                  <p className="text-xs text-slate-500 mt-2">
                    {formData.permissions?.length || 0} permissions selected
                  </p>
                </div>
              </TabsContent>
            </Tabs>

            <DialogFooter className="mt-6">
              <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={submitting} className="bg-indigo-600 hover:bg-indigo-700" data-testid="emp-submit-btn">
                {submitting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                {selectedEmployee ? 'Update' : 'Create'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* View Employee Dialog */}
      <Dialog open={viewDialogOpen} onOpenChange={setViewDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle style={{ fontFamily: 'Outfit, sans-serif' }}>Employee Details</DialogTitle>
          </DialogHeader>
          {employeeDetails && (
            <div className="space-y-4">
              <div className="flex items-center gap-4 p-4 bg-slate-50 rounded-lg">
                <div className="w-16 h-16 bg-indigo-100 rounded-full flex items-center justify-center">
                  <span className="text-2xl font-bold text-indigo-600">
                    {employeeDetails.first_name[0]}{employeeDetails.last_name[0]}
                  </span>
                </div>
                <div>
                  <h3 className="text-lg font-bold">{employeeDetails.full_name}</h3>
                  <p className="text-slate-500">{employeeDetails.employee_id} - {employeeDetails.department_name}</p>
                  <div className="flex gap-2 mt-1">
                    <Badge className={employeeTypeColors[employeeDetails.employee_type]}>{employeeDetails.employee_type}</Badge>
                    <Badge className={statusColors[employeeDetails.status]}>{employeeDetails.status}</Badge>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-slate-500">Email</p>
                  <p className="font-medium">{employeeDetails.email || '-'}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-500">Phone</p>
                  <p className="font-medium">{employeeDetails.phone || '-'}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-500">NIC</p>
                  <p className="font-medium">{employeeDetails.nic || '-'}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-500">Join Date</p>
                  <p className="font-medium">{employeeDetails.join_date || '-'}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-500">Basic Salary</p>
                  <p className="font-medium">{formatCurrency(employeeDetails.basic_salary)}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-500">Payment Frequency</p>
                  <p className="font-medium capitalize">{employeeDetails.payment_frequency}</p>
                </div>
              </div>

              {/* Leave Balance */}
              {employeeDetails.leave_balance && (
                <div className="pt-4 border-t">
                  <h4 className="font-medium mb-3">Leave Balance</h4>
                  <div className="grid grid-cols-4 gap-4">
                    <div className="text-center p-3 bg-blue-50 rounded-lg">
                      <p className="text-2xl font-bold text-blue-600">{employeeDetails.leave_balance.annual || 0}</p>
                      <p className="text-xs text-slate-500">Annual</p>
                    </div>
                    <div className="text-center p-3 bg-amber-50 rounded-lg">
                      <p className="text-2xl font-bold text-amber-600">{employeeDetails.leave_balance.sick || 0}</p>
                      <p className="text-xs text-slate-500">Sick</p>
                    </div>
                    <div className="text-center p-3 bg-emerald-50 rounded-lg">
                      <p className="text-2xl font-bold text-emerald-600">{employeeDetails.leave_balance.casual || 0}</p>
                      <p className="text-xs text-slate-500">Casual</p>
                    </div>
                    <div className="text-center p-3 bg-purple-50 rounded-lg">
                      <p className="text-2xl font-bold text-purple-600">{employeeDetails.leave_balance.maternity || employeeDetails.leave_balance.paternity || 0}</p>
                      <p className="text-xs text-slate-500">Mat/Pat</p>
                    </div>
                  </div>
                </div>
              )}

              {/* Advances */}
              {employeeDetails.total_advance_balance > 0 && (
                <div className="pt-4 border-t">
                  <h4 className="font-medium mb-2">Outstanding Advances</h4>
                  <p className="text-lg font-bold text-amber-600">{formatCurrency(employeeDetails.total_advance_balance)}</p>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Terminate Confirmation */}
      <Dialog open={terminateDialogOpen} onOpenChange={setTerminateDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-red-600">
              <AlertTriangle className="w-5 h-5" />
              Terminate Employee
            </DialogTitle>
            <DialogDescription>
              Are you sure you want to terminate {selectedEmployee?.full_name}? This will mark them as inactive.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setTerminateDialogOpen(false)}>Cancel</Button>
            <Button variant="destructive" onClick={handleTerminate}>Terminate</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Employees;
