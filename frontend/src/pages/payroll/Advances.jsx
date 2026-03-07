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
import { Plus, Loader2, Banknote, CheckCircle, Clock } from 'lucide-react';
import { toast } from 'sonner';

const formatCurrency = (amount) => {
  return new Intl.NumberFormat('en-LK', {
    style: 'currency',
    currency: 'LKR',
    minimumFractionDigits: 0,
  }).format(amount || 0);
};

const statusColors = {
  active: 'bg-amber-100 text-amber-700',
  fully_paid: 'bg-green-100 text-green-700',
};

export const Advances = () => {
  const [advances, setAdvances] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [bankAccounts, setBankAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('all');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const [formData, setFormData] = useState({
    employee_id: '',
    amount: '',
    type: 'advance',
    monthly_deduction: '',
    reason: '',
    bank_account_id: '',
  });

  const fetchData = async () => {
    try {
      const params = {};
      if (statusFilter && statusFilter !== 'all') params.status = statusFilter;

      const [advancesRes, employeesRes, bankRes] = await Promise.all([
        payrollAPI.getAdvances(params),
        payrollAPI.getEmployees({ status: 'active' }),
        api.get('/bank-accounts'),
      ]);
      setAdvances(advancesRes.data);
      setEmployees(employeesRes.data);
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

  const handleCreateAdvance = async () => {
    if (!formData.employee_id || !formData.amount || !formData.monthly_deduction) {
      toast.error('Please fill all required fields');
      return;
    }

    setSubmitting(true);
    try {
      const response = await payrollAPI.createAdvance({
        employee_id: formData.employee_id,
        amount: parseFloat(formData.amount),
        type: formData.type,
        monthly_deduction: parseFloat(formData.monthly_deduction),
        reason: formData.reason || null,
        bank_account_id: formData.bank_account_id || null,
      });
      toast.success(`Advance ${response.data.advance_number} issued successfully`);
      setDialogOpen(false);
      setFormData({
        employee_id: '',
        amount: '',
        type: 'advance',
        monthly_deduction: '',
        reason: '',
        bank_account_id: '',
      });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create advance');
    } finally {
      setSubmitting(false);
    }
  };

  // Calculate stats
  const totalActive = advances.filter(a => a.status === 'active').reduce((sum, a) => sum + a.remaining_amount, 0);
  const totalIssued = advances.reduce((sum, a) => sum + a.amount, 0);
  const totalRecovered = advances.reduce((sum, a) => sum + a.total_deducted, 0);

  return (
    <div className="space-y-6" data-testid="advances-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900" style={{ fontFamily: 'Outfit, sans-serif' }}>
            Advances & Loans
          </h2>
          <p className="text-slate-500 mt-1">{advances.length} advances issued</p>
        </div>
        <Button onClick={() => setDialogOpen(true)} className="gap-2 bg-indigo-600 hover:bg-indigo-700" data-testid="issue-advance-btn">
          <Plus className="w-4 h-4" />
          Issue Advance
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-indigo-100 rounded-lg">
                <Banknote className="w-5 h-5 text-indigo-600" />
              </div>
              <div>
                <p className="text-sm text-slate-500">Total Issued</p>
                <p className="text-xl font-bold">{formatCurrency(totalIssued)}</p>
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
                <p className="text-sm text-slate-500">Outstanding</p>
                <p className="text-xl font-bold text-amber-600">{formatCurrency(totalActive)}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 rounded-lg">
                <CheckCircle className="w-5 h-5 text-green-600" />
              </div>
              <div>
                <p className="text-sm text-slate-500">Recovered</p>
                <p className="text-xl font-bold text-green-600">{formatCurrency(totalRecovered)}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div>
              <p className="text-sm text-slate-500">Active Advances</p>
              <p className="text-2xl font-bold">{advances.filter(a => a.status === 'active').length}</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-40">
              <SelectValue placeholder="All Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Status</SelectItem>
              <SelectItem value="active">Active</SelectItem>
              <SelectItem value="fully_paid">Fully Paid</SelectItem>
            </SelectContent>
          </Select>
        </CardContent>
      </Card>

      {/* Advances Table */}
      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
            </div>
          ) : advances.length === 0 ? (
            <div className="text-center py-16">
              <Banknote className="w-12 h-12 text-slate-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-slate-900">No advances yet</h3>
              <p className="text-slate-500 mt-1">Issue an advance to an employee.</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="table-header">
                  <TableHead className="table-header-cell">Advance #</TableHead>
                  <TableHead className="table-header-cell">Employee</TableHead>
                  <TableHead className="table-header-cell">Type</TableHead>
                  <TableHead className="table-header-cell text-right">Amount</TableHead>
                  <TableHead className="table-header-cell text-right">Monthly</TableHead>
                  <TableHead className="table-header-cell text-right">Remaining</TableHead>
                  <TableHead className="table-header-cell">Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {advances.map((advance) => (
                  <TableRow key={advance.id} className="table-row" data-testid={`advance-row-${advance.id}`}>
                    <TableCell className="table-cell font-medium">{advance.advance_number}</TableCell>
                    <TableCell className="table-cell">
                      <div>{advance.employee_name}</div>
                      <span className="text-xs text-slate-400">{advance.employee_code}</span>
                    </TableCell>
                    <TableCell className="table-cell capitalize">{advance.type}</TableCell>
                    <TableCell className="table-cell text-right">{formatCurrency(advance.amount)}</TableCell>
                    <TableCell className="table-cell text-right">{formatCurrency(advance.monthly_deduction)}</TableCell>
                    <TableCell className="table-cell text-right font-medium">
                      <span className={advance.remaining_amount > 0 ? 'text-amber-600' : 'text-green-600'}>
                        {formatCurrency(advance.remaining_amount)}
                      </span>
                    </TableCell>
                    <TableCell className="table-cell">
                      <Badge className={statusColors[advance.status]}>{advance.status.replace('_', ' ')}</Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Issue Advance Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent data-testid="advance-dialog">
          <DialogHeader>
            <DialogTitle style={{ fontFamily: 'Outfit, sans-serif' }}>Issue Advance / Loan</DialogTitle>
            <DialogDescription>Issue a salary advance or loan to an employee</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Employee *</Label>
              <Select 
                value={formData.employee_id} 
                onValueChange={(v) => setFormData({ ...formData, employee_id: v })}
              >
                <SelectTrigger data-testid="advance-employee-select">
                  <SelectValue placeholder="Select employee" />
                </SelectTrigger>
                <SelectContent>
                  {employees.map((emp) => (
                    <SelectItem key={emp.id} value={emp.id}>
                      {emp.employee_id} - {emp.full_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Type</Label>
                <Select 
                  value={formData.type} 
                  onValueChange={(v) => setFormData({ ...formData, type: v })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="advance">Salary Advance</SelectItem>
                    <SelectItem value="loan">Loan</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Amount (LKR) *</Label>
                <Input
                  type="number"
                  value={formData.amount}
                  onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                  placeholder="0.00"
                  data-testid="advance-amount"
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label>Monthly Deduction (LKR) *</Label>
              <Input
                type="number"
                value={formData.monthly_deduction}
                onChange={(e) => setFormData({ ...formData, monthly_deduction: e.target.value })}
                placeholder="Amount to deduct from each payroll"
                data-testid="advance-monthly"
              />
              {formData.amount && formData.monthly_deduction && (
                <p className="text-sm text-slate-500">
                  Will be recovered in ~{Math.ceil(parseFloat(formData.amount) / parseFloat(formData.monthly_deduction))} months
                </p>
              )}
            </div>
            <div className="space-y-2">
              <Label>Pay From Account</Label>
              <Select 
                value={formData.bank_account_id} 
                onValueChange={(v) => setFormData({ ...formData, bank_account_id: v })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select account (optional)" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">No payment now</SelectItem>
                  {bankAccounts.map((acc) => (
                    <SelectItem key={acc.id} value={acc.id}>
                      {acc.account_name} - {formatCurrency(acc.current_balance)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className="text-xs text-slate-500">Select to pay immediately and record financial entry</p>
            </div>
            <div className="space-y-2">
              <Label>Reason</Label>
              <Textarea
                value={formData.reason}
                onChange={(e) => setFormData({ ...formData, reason: e.target.value })}
                placeholder="Optional reason for advance..."
                rows={2}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)}>Cancel</Button>
            <Button onClick={handleCreateAdvance} disabled={submitting} className="bg-indigo-600 hover:bg-indigo-700" data-testid="submit-advance-btn">
              {submitting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
              Issue Advance
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Advances;
