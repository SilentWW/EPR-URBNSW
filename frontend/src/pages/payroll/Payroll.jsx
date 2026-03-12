import React, { useState, useEffect } from 'react';
import { payrollAPI } from '../../lib/api';
import api from '../../lib/api';
import { useAuth } from '../../context/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Badge } from '../../components/ui/badge';
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
import { 
  Plus, MoreHorizontal, Eye, Loader2, Calculator, CheckCircle, Send, 
  CreditCard, Trash2, FileText, AlertTriangle, Clock, Download
} from 'lucide-react';
import { toast } from 'sonner';

const formatCurrency = (amount) => {
  return new Intl.NumberFormat('en-LK', {
    style: 'currency',
    currency: 'LKR',
    minimumFractionDigits: 0,
  }).format(amount || 0);
};

const statusColors = {
  draft: 'bg-slate-100 text-slate-700',
  pending_approval: 'bg-amber-100 text-amber-700',
  approved: 'bg-blue-100 text-blue-700',
  processed: 'bg-emerald-100 text-emerald-700',
  paid: 'bg-green-100 text-green-700',
};

const statusLabels = {
  draft: 'Draft',
  pending_approval: 'Pending Approval',
  approved: 'Approved',
  processed: 'Processed',
  paid: 'Paid',
};

const PAYMENT_FREQUENCIES = [
  { value: 'monthly', label: 'Monthly' },
  { value: 'weekly', label: 'Weekly' },
  { value: 'daily', label: 'Daily' },
];

export const Payroll = () => {
  const { user } = useAuth();
  const [payrolls, setPayrolls] = useState([]);
  const [bankAccounts, setBankAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('all');
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [processDialogOpen, setProcessDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedPayroll, setSelectedPayroll] = useState(null);
  const [payrollDetails, setPayrollDetails] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const canApprove = user?.role === 'admin' || user?.role === 'manager';

  const [createForm, setCreateForm] = useState({
    period_start: '',
    period_end: '',
    payment_frequency: 'monthly',
  });

  const [processForm, setProcessForm] = useState({
    bank_account_id: '',
  });

  // Set default period dates
  useEffect(() => {
    const now = new Date();
    const year = now.getFullYear();
    const month = now.getMonth();
    const firstDay = new Date(year, month, 1).toISOString().split('T')[0];
    const lastDay = new Date(year, month + 1, 0).toISOString().split('T')[0];
    setCreateForm(prev => ({
      ...prev,
      period_start: firstDay,
      period_end: lastDay,
    }));
  }, []);

  const fetchData = async () => {
    try {
      const params = {};
      if (statusFilter && statusFilter !== 'all') params.status = statusFilter;

      const [payrollRes, bankRes] = await Promise.all([
        payrollAPI.getPayrolls(params),
        api.get('/bank-accounts'),
      ]);
      setPayrolls(payrollRes.data);
      setBankAccounts(bankRes.data || []);
    } catch (error) {
      toast.error('Failed to fetch data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [statusFilter]);

  const handleCreatePayroll = async () => {
    setSubmitting(true);
    try {
      const response = await payrollAPI.createPayroll(createForm);
      toast.success(`Payroll ${response.data.payroll_number} created with ${response.data.employee_count} employees`);
      setCreateDialogOpen(false);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create payroll');
    } finally {
      setSubmitting(false);
    }
  };

  const handleViewPayroll = async (payroll) => {
    try {
      const response = await payrollAPI.getPayroll(payroll.id);
      setPayrollDetails(response.data);
      setSelectedPayroll(payroll);
      setViewDialogOpen(true);
    } catch (error) {
      toast.error('Failed to load payroll details');
    }
  };

  const handleSubmitForApproval = async (payroll) => {
    try {
      await payrollAPI.submitPayroll(payroll.id);
      toast.success('Payroll submitted for approval');
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to submit payroll');
    }
  };

  const handleApprove = async (payroll) => {
    try {
      await payrollAPI.approvePayroll(payroll.id);
      toast.success('Payroll approved');
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to approve payroll');
    }
  };

  const handleProcess = async () => {
    if (!processForm.bank_account_id) {
      toast.error('Please select a bank account');
      return;
    }
    setSubmitting(true);
    try {
      await payrollAPI.processPayroll(selectedPayroll.id, processForm.bank_account_id);
      toast.success('Payroll processed and paid successfully');
      setProcessDialogOpen(false);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to process payroll');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async () => {
    try {
      await payrollAPI.deletePayroll(selectedPayroll.id);
      toast.success('Payroll deleted');
      setDeleteDialogOpen(false);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete payroll');
    }
  };

  // Calculate summary stats
  const stats = {
    draft: payrolls.filter(p => p.status === 'draft').length,
    pending: payrolls.filter(p => p.status === 'pending_approval').length,
    approved: payrolls.filter(p => p.status === 'approved').length,
    paid: payrolls.filter(p => p.status === 'paid').length,
    totalPaid: payrolls.filter(p => p.status === 'paid').reduce((sum, p) => sum + p.total_net, 0),
  };

  return (
    <div className="space-y-6" data-testid="payroll-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900" style={{ fontFamily: 'Outfit, sans-serif' }}>
            Payroll
          </h2>
          <p className="text-slate-500 mt-1">{payrolls.length} payroll runs</p>
        </div>
        <Button onClick={() => setCreateDialogOpen(true)} className="gap-2 bg-indigo-600 hover:bg-indigo-700" data-testid="create-payroll-btn">
          <Plus className="w-4 h-4" />
          Run Payroll
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-slate-100 rounded-lg">
                <FileText className="w-5 h-5 text-slate-600" />
              </div>
              <div>
                <p className="text-sm text-slate-500">Draft</p>
                <p className="text-2xl font-bold">{stats.draft}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-amber-100 rounded-lg">
                <Clock className="w-5 h-5 text-amber-600" />
              </div>
              <div>
                <p className="text-sm text-slate-500">Pending</p>
                <p className="text-2xl font-bold">{stats.pending}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <CheckCircle className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-slate-500">Approved</p>
                <p className="text-2xl font-bold">{stats.approved}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 rounded-lg">
                <CreditCard className="w-5 h-5 text-green-600" />
              </div>
              <div>
                <p className="text-sm text-slate-500">Paid</p>
                <p className="text-2xl font-bold">{stats.paid}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div>
              <p className="text-sm text-slate-500">Total Paid (YTD)</p>
              <p className="text-xl font-bold text-green-600">{formatCurrency(stats.totalPaid)}</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-48" data-testid="payroll-status-filter">
              <SelectValue placeholder="All Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Status</SelectItem>
              <SelectItem value="draft">Draft</SelectItem>
              <SelectItem value="pending_approval">Pending Approval</SelectItem>
              <SelectItem value="approved">Approved</SelectItem>
              <SelectItem value="paid">Paid</SelectItem>
            </SelectContent>
          </Select>
        </CardContent>
      </Card>

      {/* Payroll Table */}
      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
            </div>
          ) : payrolls.length === 0 ? (
            <div className="text-center py-16">
              <Calculator className="w-12 h-12 text-slate-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-slate-900">No payroll runs yet</h3>
              <p className="text-slate-500 mt-1">Run your first payroll to get started.</p>
              <Button onClick={() => setCreateDialogOpen(true)} className="mt-4 bg-indigo-600 hover:bg-indigo-700">
                Run Payroll
              </Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="table-header">
                  <TableHead className="table-header-cell">Payroll #</TableHead>
                  <TableHead className="table-header-cell">Period</TableHead>
                  <TableHead className="table-header-cell">Frequency</TableHead>
                  <TableHead className="table-header-cell text-center">Employees</TableHead>
                  <TableHead className="table-header-cell text-right">Gross</TableHead>
                  <TableHead className="table-header-cell text-right">Net Pay</TableHead>
                  <TableHead className="table-header-cell">Status</TableHead>
                  <TableHead className="table-header-cell w-12"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {payrolls.map((payroll) => (
                  <TableRow key={payroll.id} className="table-row" data-testid={`payroll-row-${payroll.id}`}>
                    <TableCell className="table-cell font-medium">{payroll.payroll_number}</TableCell>
                    <TableCell className="table-cell text-slate-500">
                      {payroll.period_start} to {payroll.period_end}
                    </TableCell>
                    <TableCell className="table-cell capitalize">{payroll.payment_frequency}</TableCell>
                    <TableCell className="table-cell text-center">{payroll.employee_count}</TableCell>
                    <TableCell className="table-cell text-right">{formatCurrency(payroll.total_gross)}</TableCell>
                    <TableCell className="table-cell text-right font-medium">{formatCurrency(payroll.total_net)}</TableCell>
                    <TableCell className="table-cell">
                      <Badge className={statusColors[payroll.status]}>{statusLabels[payroll.status]}</Badge>
                    </TableCell>
                    <TableCell className="table-cell">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon">
                            <MoreHorizontal className="w-4 h-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => handleViewPayroll(payroll)}>
                            <Eye className="w-4 h-4 mr-2" />
                            View Details
                          </DropdownMenuItem>
                          {payroll.status === 'draft' && (
                            <>
                              <DropdownMenuItem onClick={() => handleSubmitForApproval(payroll)}>
                                <Send className="w-4 h-4 mr-2" />
                                Submit for Approval
                              </DropdownMenuItem>
                              <DropdownMenuSeparator />
                              <DropdownMenuItem
                                className="text-red-600"
                                onClick={() => {
                                  setSelectedPayroll(payroll);
                                  setDeleteDialogOpen(true);
                                }}
                              >
                                <Trash2 className="w-4 h-4 mr-2" />
                                Delete
                              </DropdownMenuItem>
                            </>
                          )}
                          {payroll.status === 'pending_approval' && canApprove && (
                            <DropdownMenuItem onClick={() => handleApprove(payroll)}>
                              <CheckCircle className="w-4 h-4 mr-2" />
                              Approve
                            </DropdownMenuItem>
                          )}
                          {payroll.status === 'approved' && (
                            <DropdownMenuItem onClick={() => {
                              setSelectedPayroll(payroll);
                              setProcessDialogOpen(true);
                            }}>
                              <CreditCard className="w-4 h-4 mr-2" />
                              Process & Pay
                            </DropdownMenuItem>
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

      {/* Create Payroll Dialog */}
      <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
        <DialogContent data-testid="create-payroll-dialog">
          <DialogHeader>
            <DialogTitle style={{ fontFamily: 'Outfit, sans-serif' }}>Run Payroll</DialogTitle>
            <DialogDescription>Create a new payroll run for the selected period</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Payment Frequency</Label>
              <Select 
                value={createForm.payment_frequency} 
                onValueChange={(v) => setCreateForm({ ...createForm, payment_frequency: v })}
              >
                <SelectTrigger data-testid="payroll-frequency">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {PAYMENT_FREQUENCIES.map(f => (
                    <SelectItem key={f.value} value={f.value}>{f.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Period Start</Label>
                <Input
                  type="date"
                  value={createForm.period_start}
                  onChange={(e) => setCreateForm({ ...createForm, period_start: e.target.value })}
                  data-testid="payroll-start-date"
                />
              </div>
              <div className="space-y-2">
                <Label>Period End</Label>
                <Input
                  type="date"
                  value={createForm.period_end}
                  onChange={(e) => setCreateForm({ ...createForm, period_end: e.target.value })}
                  data-testid="payroll-end-date"
                />
              </div>
            </div>
            <p className="text-sm text-slate-500">
              All active employees with "{createForm.payment_frequency}" payment frequency will be included.
            </p>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateDialogOpen(false)}>Cancel</Button>
            <Button onClick={handleCreatePayroll} disabled={submitting} className="bg-indigo-600 hover:bg-indigo-700" data-testid="submit-payroll-btn">
              {submitting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
              Create Payroll
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* View Payroll Dialog */}
      <Dialog open={viewDialogOpen} onOpenChange={setViewDialogOpen}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle style={{ fontFamily: 'Outfit, sans-serif' }}>
              Payroll {payrollDetails?.payroll_number}
            </DialogTitle>
          </DialogHeader>
          {payrollDetails && (
            <div className="space-y-4">
              {/* Summary */}
              <div className="grid grid-cols-4 gap-4">
                <div className="p-3 bg-slate-50 rounded-lg">
                  <p className="text-sm text-slate-500">Employees</p>
                  <p className="text-xl font-bold">{payrollDetails.employee_count}</p>
                </div>
                <div className="p-3 bg-blue-50 rounded-lg">
                  <p className="text-sm text-slate-500">Gross Salary</p>
                  <p className="text-xl font-bold text-blue-600">{formatCurrency(payrollDetails.total_gross)}</p>
                </div>
                <div className="p-3 bg-amber-50 rounded-lg">
                  <p className="text-sm text-slate-500">Deductions</p>
                  <p className="text-xl font-bold text-amber-600">{formatCurrency(payrollDetails.total_deductions)}</p>
                </div>
                <div className="p-3 bg-green-50 rounded-lg">
                  <p className="text-sm text-slate-500">Net Pay</p>
                  <p className="text-xl font-bold text-green-600">{formatCurrency(payrollDetails.total_net)}</p>
                </div>
              </div>

              {/* Employee Items */}
              <div className="border rounded-lg overflow-hidden">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Employee</TableHead>
                      <TableHead className="text-right">Basic</TableHead>
                      <TableHead className="text-right">Allowances</TableHead>
                      <TableHead className="text-right">Task Pay</TableHead>
                      <TableHead className="text-right">OT Pay</TableHead>
                      <TableHead className="text-right">Gross</TableHead>
                      <TableHead className="text-right">EPF</TableHead>
                      <TableHead className="text-right">Tax</TableHead>
                      <TableHead className="text-right">Advances</TableHead>
                      <TableHead className="text-right">Net Pay</TableHead>
                      <TableHead className="text-center">Payslip</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {payrollDetails.items?.map((item) => (
                      <TableRow key={item.id}>
                        <TableCell>
                          <div>{item.employee_name}</div>
                          <span className="text-xs text-slate-400">{item.employee_code}</span>
                          {item.attendance_days > 0 && (
                            <span className="text-xs text-blue-500 block">{item.attendance_days} days</span>
                          )}
                        </TableCell>
                        <TableCell className="text-right">{formatCurrency(item.basic_salary)}</TableCell>
                        <TableCell className="text-right">{formatCurrency(item.total_allowances)}</TableCell>
                        <TableCell className="text-right">
                          {item.task_payments_amount > 0 ? (
                            <span className="text-purple-600" title={item.task_payments?.map(t => t.title).join(', ')}>
                              {formatCurrency(item.task_payments_amount)}
                            </span>
                          ) : '-'}
                        </TableCell>
                        <TableCell className="text-right">
                          {item.overtime_amount > 0 ? (
                            <span className="text-orange-600" title={`${item.overtime_hours || 0}h regular + ${item.overtime_weekend_hours || 0}h weekend`}>
                              {formatCurrency(item.overtime_amount)}
                            </span>
                          ) : '-'}
                        </TableCell>
                        <TableCell className="text-right">{formatCurrency(item.gross_salary)}</TableCell>
                        <TableCell className="text-right text-amber-600">{formatCurrency(item.epf_employee)}</TableCell>
                        <TableCell className="text-right text-amber-600">{formatCurrency(item.tax)}</TableCell>
                        <TableCell className="text-right text-red-600">
                          {item.advance_deduction > 0 ? formatCurrency(item.advance_deduction) : '-'}
                        </TableCell>
                        <TableCell className="text-right font-medium text-green-600">{formatCurrency(item.net_salary)}</TableCell>
                        <TableCell className="text-center">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => payrollAPI.downloadPayslipPdf(payrollDetails.id, item.employee_id)}
                            className="text-indigo-600 hover:text-indigo-800 hover:bg-indigo-50"
                            data-testid={`download-payslip-${item.employee_id}`}
                          >
                            <Download className="w-4 h-4" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>

              {/* Earnings Summary */}
              <div className="p-4 bg-green-50 rounded-lg">
                <h4 className="font-medium text-green-900 mb-2">Earnings Summary</h4>
                <div className="grid grid-cols-5 gap-4 text-sm">
                  <div>
                    <p className="text-green-600">Basic Salary</p>
                    <p className="font-medium">{formatCurrency(payrollDetails.items?.reduce((sum, i) => sum + (i.basic_salary || 0), 0))}</p>
                  </div>
                  <div>
                    <p className="text-green-600">Allowances</p>
                    <p className="font-medium">{formatCurrency(payrollDetails.items?.reduce((sum, i) => sum + (i.total_allowances || 0), 0))}</p>
                  </div>
                  <div>
                    <p className="text-green-600">Task Payments</p>
                    <p className="font-medium">{formatCurrency(payrollDetails.items?.reduce((sum, i) => sum + (i.task_payments_amount || 0), 0))}</p>
                  </div>
                  <div>
                    <p className="text-orange-600">Overtime Pay</p>
                    <p className="font-medium">{formatCurrency(payrollDetails.items?.reduce((sum, i) => sum + (i.overtime_amount || 0), 0))}</p>
                    <p className="text-xs text-gray-500">
                      {payrollDetails.items?.reduce((sum, i) => sum + (i.overtime_hours || 0), 0).toFixed(1)}h reg + {payrollDetails.items?.reduce((sum, i) => sum + (i.overtime_weekend_hours || 0), 0).toFixed(1)}h wknd
                    </p>
                  </div>
                  <div>
                    <p className="text-green-600">Total Gross</p>
                    <p className="font-bold">{formatCurrency(payrollDetails.total_gross)}</p>
                  </div>
                </div>
              </div>

              {/* Deductions Summary */}
              <div className="p-4 bg-red-50 rounded-lg">
                <h4 className="font-medium text-red-900 mb-2">Deductions Summary</h4>
                <div className="grid grid-cols-4 gap-4 text-sm">
                  <div>
                    <p className="text-red-600">EPF (8%)</p>
                    <p className="font-medium">{formatCurrency(payrollDetails.items?.reduce((sum, i) => sum + (i.epf_employee || 0), 0))}</p>
                  </div>
                  <div>
                    <p className="text-red-600">PAYE Tax</p>
                    <p className="font-medium">{formatCurrency(payrollDetails.items?.reduce((sum, i) => sum + (i.tax || 0), 0))}</p>
                  </div>
                  <div>
                    <p className="text-red-600">Advance Deductions</p>
                    <p className="font-medium">{formatCurrency(payrollDetails.items?.reduce((sum, i) => sum + (i.advance_deduction || 0), 0))}</p>
                  </div>
                  <div>
                    <p className="text-red-600">Total Deductions</p>
                    <p className="font-bold">{formatCurrency(payrollDetails.total_deductions)}</p>
                  </div>
                </div>
              </div>

              {/* Employer Costs */}
              <div className="p-4 bg-indigo-50 rounded-lg">
                <h4 className="font-medium text-indigo-900 mb-2">Employer Contributions</h4>
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <p className="text-indigo-600">EPF (12%)</p>
                    <p className="font-medium">{formatCurrency(payrollDetails.items?.reduce((sum, i) => sum + (i.epf_employer || 0), 0))}</p>
                  </div>
                  <div>
                    <p className="text-indigo-600">ETF (3%)</p>
                    <p className="font-medium">{formatCurrency(payrollDetails.items?.reduce((sum, i) => sum + (i.etf || 0), 0))}</p>
                  </div>
                  <div>
                    <p className="text-indigo-600">Total Employer Cost</p>
                    <p className="font-bold">{formatCurrency(payrollDetails.total_employer_cost)}</p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Process & Pay Dialog */}
      <Dialog open={processDialogOpen} onOpenChange={setProcessDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle style={{ fontFamily: 'Outfit, sans-serif' }}>Process & Pay</DialogTitle>
            <DialogDescription>
              Process payroll {selectedPayroll?.payroll_number} and pay {formatCurrency(selectedPayroll?.total_net)} to employees.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Pay From Account *</Label>
              <Select 
                value={processForm.bank_account_id} 
                onValueChange={(v) => setProcessForm({ bank_account_id: v })}
              >
                <SelectTrigger data-testid="payroll-bank-account">
                  <SelectValue placeholder="Select bank account" />
                </SelectTrigger>
                <SelectContent>
                  {bankAccounts.map((acc) => (
                    <SelectItem key={acc.id} value={acc.id}>
                      {acc.account_name} - {formatCurrency(acc.current_balance)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="p-4 bg-amber-50 rounded-lg border border-amber-200">
              <div className="flex items-center gap-2 text-amber-700">
                <AlertTriangle className="w-4 h-4" />
                <span className="font-medium">This action will:</span>
              </div>
              <ul className="text-sm text-amber-600 mt-2 space-y-1 ml-6 list-disc">
                <li>Deduct {formatCurrency(selectedPayroll?.total_net)} from selected account</li>
                <li>Create journal entries for salaries and statutory contributions</li>
                <li>Update employee advance balances</li>
                <li>Mark payroll as paid</li>
              </ul>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setProcessDialogOpen(false)}>Cancel</Button>
            <Button onClick={handleProcess} disabled={submitting} className="bg-green-600 hover:bg-green-700" data-testid="process-payroll-btn">
              {submitting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <CreditCard className="w-4 h-4 mr-2" />}
              Process & Pay
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-red-600">
              <AlertTriangle className="w-5 h-5" />
              Delete Payroll
            </DialogTitle>
            <DialogDescription>
              Are you sure you want to delete payroll {selectedPayroll?.payroll_number}? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
            <Button variant="destructive" onClick={handleDelete}>Delete</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Payroll;
