import React, { useState, useEffect } from 'react';
import api from '../lib/api';
import { toast } from 'sonner';
import {
  Wallet,
  Receipt,
  Users,
  Building,
  Zap,
  CreditCard,
  TrendingUp,
  TrendingDown,
  Loader2,
  CheckCircle,
  Clock,
  DollarSign,
  Banknote,
  FileText,
  Pencil,
  Trash2,
  Calendar,
  AlertTriangle
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription
} from '../components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from '../components/ui/select';
import { Badge } from '../components/ui/badge';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle
} from '../components/ui/alert-dialog';

const formatCurrency = (amount) => {
  return new Intl.NumberFormat('en-LK', {
    style: 'currency',
    currency: 'LKR',
    minimumFractionDigits: 0
  }).format(amount);
};

const formatDate = (dateStr) => {
  return new Date(dateStr).toLocaleDateString('en-LK', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  });
};

export default function QuickTransactions() {
  const [investors, setInvestors] = useState([]);
  const [recentTransactions, setRecentTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [transactionToDelete, setTransactionToDelete] = useState(null);
  
  const [activeModal, setActiveModal] = useState(null);
  
  // Get today's date in YYYY-MM-DD format
  const getTodayDate = () => new Date().toISOString().split('T')[0];
  
  // Form states
  const [expenseForm, setExpenseForm] = useState({
    expense_type: '',
    description: '',
    amount: '',
    vendor: '',
    payment_method: 'bank',
    reference: '',
    notes: '',
    date: getTodayDate()
  });
  
  const [salaryForm, setSalaryForm] = useState({
    employee_name: '',
    amount: '',
    month: '',
    allowances: '0',
    deductions: '0',
    payment_method: 'bank',
    notes: '',
    date: getTodayDate()
  });
  
  const [revenueForm, setRevenueForm] = useState({
    revenue_type: 'sales',
    description: '',
    amount: '',
    customer: '',
    payment_method: 'bank',
    reference: '',
    notes: '',
    date: getTodayDate()
  });
  
  const [loanForm, setLoanForm] = useState({
    transaction_type: 'receive',
    loan_type: 'bank_loan',
    lender_name: '',
    amount: '',
    interest_amount: '0',
    reference: '',
    notes: '',
    date: getTodayDate()
  });

  useEffect(() => {
    fetchData();
    fetchCurrentUser();
  }, []);

  const fetchCurrentUser = async () => {
    try {
      const response = await api.get('/auth/me');
      setCurrentUser(response.data);
    } catch (error) {
      console.error('Failed to fetch current user:', error);
    }
  };

  const isAdmin = currentUser?.role === 'admin';

  const fetchData = async () => {
    try {
      setLoading(true);
      const [investorsRes, transactionsRes] = await Promise.all([
        api.get('/simple-finance/investors'),
        api.get('/simple-finance/recent-transactions')
      ]);
      setInvestors(investorsRes.data);
      setRecentTransactions(transactionsRes.data);
    } catch (error) {
      console.error('Failed to fetch data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleExpenseSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const response = await api.post('/simple-finance/expense-payment', {
        ...expenseForm,
        amount: parseFloat(expenseForm.amount)
      });
      toast.success(response.data.message);
      setActiveModal(null);
      setExpenseForm({ expense_type: '', description: '', amount: '', vendor: '', payment_method: 'bank', reference: '', notes: '', date: getTodayDate() });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to record expense');
    } finally {
      setSubmitting(false);
    }
  };

  const handleSalarySubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const response = await api.post('/simple-finance/salary-payment', {
        ...salaryForm,
        amount: parseFloat(salaryForm.amount),
        allowances: parseFloat(salaryForm.allowances) || 0,
        deductions: parseFloat(salaryForm.deductions) || 0
      });
      toast.success(response.data.message);
      setActiveModal(null);
      setSalaryForm({ employee_name: '', amount: '', month: '', allowances: '0', deductions: '0', payment_method: 'bank', notes: '', date: getTodayDate() });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to record salary');
    } finally {
      setSubmitting(false);
    }
  };

  const handleRevenueSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const response = await api.post('/simple-finance/revenue-receipt', {
        ...revenueForm,
        amount: parseFloat(revenueForm.amount)
      });
      toast.success(response.data.message);
      setActiveModal(null);
      setRevenueForm({ revenue_type: 'sales', description: '', amount: '', customer: '', payment_method: 'bank', reference: '', notes: '', date: getTodayDate() });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to record revenue');
    } finally {
      setSubmitting(false);
    }
  };

  const handleLoanSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const response = await api.post('/simple-finance/loan-transaction', {
        ...loanForm,
        amount: parseFloat(loanForm.amount),
        interest_amount: parseFloat(loanForm.interest_amount) || 0
      });
      toast.success(response.data.message);
      setActiveModal(null);
      setLoanForm({ transaction_type: 'receive', loan_type: 'bank_loan', lender_name: '', amount: '', interest_amount: '0', reference: '', notes: '', date: getTodayDate() });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to record loan transaction');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteTransaction = async () => {
    if (!transactionToDelete) return;
    
    setSubmitting(true);
    try {
      await api.delete(`/simple-finance/transaction/${transactionToDelete.id}`);
      toast.success('Transaction deleted and reversed successfully');
      setDeleteDialogOpen(false);
      setTransactionToDelete(null);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete transaction');
    } finally {
      setSubmitting(false);
    }
  };

  const expenseTypes = [
    { value: 'utilities', label: 'Utilities (Electricity, Water)', icon: '💡' },
    { value: 'rent', label: 'Rent Payment', icon: '🏢' },
    { value: 'office_supplies', label: 'Office Supplies', icon: '📎' },
    { value: 'marketing', label: 'Marketing & Advertising', icon: '📢' },
    { value: 'insurance', label: 'Insurance', icon: '🛡️' },
    { value: 'maintenance', label: 'Repairs & Maintenance', icon: '🔧' },
    { value: 'transport', label: 'Transport & Travel', icon: '🚗' },
    { value: 'communication', label: 'Phone & Internet', icon: '📱' },
    { value: 'professional_fees', label: 'Professional Fees', icon: '👔' },
    { value: 'other', label: 'Other Expenses', icon: '📋' }
  ];

  const revenueTypes = [
    { value: 'sales', label: 'Sales Revenue' },
    { value: 'service', label: 'Service Income' },
    { value: 'interest', label: 'Interest Income' },
    { value: 'commission', label: 'Commission Income' },
    { value: 'other', label: 'Other Income' }
  ];

  const getTransactionIcon = (type) => {
    switch (type) {
      case 'capital_investment': return <TrendingUp className="w-4 h-4 text-green-600" />;
      case 'capital_withdrawal': return <TrendingDown className="w-4 h-4 text-amber-600" />;
      case 'expense_payment': return <Receipt className="w-4 h-4 text-red-600" />;
      case 'salary_payment': return <Users className="w-4 h-4 text-blue-600" />;
      case 'revenue_receipt': return <DollarSign className="w-4 h-4 text-green-600" />;
      case 'loan_received': return <Banknote className="w-4 h-4 text-purple-600" />;
      case 'loan_repayment': return <CreditCard className="w-4 h-4 text-orange-600" />;
      default: return <FileText className="w-4 h-4 text-gray-600" />;
    }
  };

  const getTransactionColor = (type) => {
    switch (type) {
      case 'capital_investment': 
      case 'revenue_receipt':
        return 'bg-green-50 border-green-200';
      case 'capital_withdrawal':
      case 'expense_payment':
      case 'salary_payment':
      case 'loan_repayment':
        return 'bg-red-50 border-red-200';
      default:
        return 'bg-slate-50 border-slate-200';
    }
  };

  const quickActions = [
    {
      id: 'expense',
      title: 'Pay Expense',
      description: 'Utilities, rent, supplies, etc.',
      icon: Receipt,
      color: 'bg-red-500',
      onClick: () => setActiveModal('expense')
    },
    {
      id: 'salary',
      title: 'Pay Salary',
      description: 'Employee salary payment',
      icon: Users,
      color: 'bg-blue-500',
      onClick: () => setActiveModal('salary')
    },
    {
      id: 'revenue',
      title: 'Receive Payment',
      description: 'Sales, service income, etc.',
      icon: DollarSign,
      color: 'bg-green-500',
      onClick: () => setActiveModal('revenue')
    },
    {
      id: 'loan',
      title: 'Loan Transaction',
      description: 'Receive or repay loan',
      icon: Banknote,
      color: 'bg-purple-500',
      onClick: () => setActiveModal('loan')
    }
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Quick Transactions</h1>
        <p className="text-slate-500 mt-1">Record financial transactions easily - no accounting knowledge needed!</p>
      </div>

      {/* Quick Action Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {quickActions.map((action) => (
          <Card 
            key={action.id}
            className="cursor-pointer hover:shadow-lg transition-shadow border-2 hover:border-indigo-300"
            onClick={action.onClick}
          >
            <CardContent className="pt-6">
              <div className="flex items-start gap-4">
                <div className={`w-12 h-12 ${action.color} rounded-xl flex items-center justify-center`}>
                  <action.icon className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h3 className="font-semibold text-slate-900">{action.title}</h3>
                  <p className="text-sm text-slate-500">{action.description}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Info Banner */}
      <Card className="bg-gradient-to-r from-indigo-50 to-purple-50 border-indigo-200">
        <CardContent className="pt-6">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-indigo-100 rounded-full flex items-center justify-center">
              <Zap className="w-6 h-6 text-indigo-600" />
            </div>
            <div>
              <h3 className="font-semibold text-slate-900">Automatic Double-Entry</h3>
              <p className="text-sm text-slate-600">
                All transactions automatically create proper journal entries. No need to know debits and credits!
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Recent Transactions */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="w-5 h-5" />
            Recent Quick Transactions
          </CardTitle>
          {isAdmin && (
            <p className="text-xs text-slate-500">As admin, you can delete transactions</p>
          )}
        </CardHeader>
        <CardContent>
          {recentTransactions.length === 0 ? (
            <div className="text-center py-8">
              <Receipt className="w-12 h-12 mx-auto text-slate-300 mb-4" />
              <p className="text-slate-500">No transactions recorded yet</p>
              <p className="text-sm text-slate-400">Use the quick actions above to record your first transaction</p>
            </div>
          ) : (
            <div className="space-y-3">
              {recentTransactions.slice(0, 10).map((tx) => (
                <div 
                  key={tx.id}
                  className={`flex items-center justify-between p-3 rounded-lg border ${getTransactionColor(tx.transaction_type)}`}
                >
                  <div className="flex items-center gap-3">
                    {getTransactionIcon(tx.transaction_type)}
                    <div>
                      <p className="font-medium text-slate-900">{tx.description}</p>
                      <div className="flex items-center gap-2 text-sm text-slate-500">
                        <Calendar className="w-3 h-3" />
                        {formatDate(tx.entry_date || tx.created_at)}
                        {tx.entry_number && (
                          <span className="text-xs text-slate-400">({tx.entry_number})</span>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="text-right">
                      <p className={`font-semibold ${
                        ['capital_investment', 'revenue_receipt', 'loan_received'].includes(tx.transaction_type)
                          ? 'text-green-600'
                          : 'text-red-600'
                      }`}>
                        {['capital_investment', 'revenue_receipt', 'loan_received'].includes(tx.transaction_type) ? '+' : '-'}
                        {formatCurrency(tx.total_debit)}
                      </p>
                      <Badge variant="outline" className="text-xs">
                        {tx.transaction_type.replace(/_/g, ' ')}
                      </Badge>
                    </div>
                    {isAdmin && (
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8 text-red-600 hover:text-red-700 hover:bg-red-50"
                        onClick={() => {
                          setTransactionToDelete(tx);
                          setDeleteDialogOpen(true);
                        }}
                        data-testid={`delete-transaction-${tx.id}`}
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Expense Payment Modal */}
      <Dialog open={activeModal === 'expense'} onOpenChange={() => setActiveModal(null)}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Receipt className="w-5 h-5 text-red-600" />
              Pay Expense
            </DialogTitle>
            <DialogDescription>
              Record any business expense payment
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleExpenseSubmit}>
            <div className="grid gap-4 py-4">
              <div className="space-y-2">
                <Label>Expense Type *</Label>
                <Select
                  value={expenseForm.expense_type}
                  onValueChange={(value) => setExpenseForm({ ...expenseForm, expense_type: value })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="What type of expense?" />
                  </SelectTrigger>
                  <SelectContent>
                    {expenseTypes.map((type) => (
                      <SelectItem key={type.value} value={type.value}>
                        <span className="flex items-center gap-2">
                          <span>{type.icon}</span>
                          {type.label}
                        </span>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Description *</Label>
                <Input
                  value={expenseForm.description}
                  onChange={(e) => setExpenseForm({ ...expenseForm, description: e.target.value })}
                  placeholder="e.g., January electricity bill"
                  required
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Amount (LKR) *</Label>
                  <Input
                    type="number"
                    min="0"
                    step="0.01"
                    value={expenseForm.amount}
                    onChange={(e) => setExpenseForm({ ...expenseForm, amount: e.target.value })}
                    placeholder="0.00"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label>Payment Method</Label>
                  <Select
                    value={expenseForm.payment_method}
                    onValueChange={(value) => setExpenseForm({ ...expenseForm, payment_method: value })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="bank">Bank Transfer</SelectItem>
                      <SelectItem value="cash">Cash</SelectItem>
                      <SelectItem value="cheque">Cheque</SelectItem>
                      <SelectItem value="card">Card</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Transaction Date *</Label>
                  <Input
                    type="date"
                    value={expenseForm.date}
                    onChange={(e) => setExpenseForm({ ...expenseForm, date: e.target.value })}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label>Vendor/Payee</Label>
                  <Input
                    value={expenseForm.vendor}
                    onChange={(e) => setExpenseForm({ ...expenseForm, vendor: e.target.value })}
                    placeholder="Who did you pay?"
                  />
                </div>
              </div>
              <div className="bg-red-50 p-3 rounded-lg text-sm text-red-800">
                <strong>This will:</strong><br />
                • Reduce Cash/Bank balance<br />
                • Record as business expense
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setActiveModal(null)}>Cancel</Button>
              <Button type="submit" disabled={submitting} className="bg-red-600 hover:bg-red-700">
                {submitting && <Loader2 className="w-4 h-4 animate-spin mr-2" />}
                Record Expense
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Salary Payment Modal */}
      <Dialog open={activeModal === 'salary'} onOpenChange={() => setActiveModal(null)}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Users className="w-5 h-5 text-blue-600" />
              Pay Salary
            </DialogTitle>
            <DialogDescription>
              Record employee salary payment
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleSalarySubmit}>
            <div className="grid gap-4 py-4">
              <div className="space-y-2">
                <Label>Employee Name *</Label>
                <Input
                  value={salaryForm.employee_name}
                  onChange={(e) => setSalaryForm({ ...salaryForm, employee_name: e.target.value })}
                  placeholder="Full name"
                  required
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Basic Salary (LKR) *</Label>
                  <Input
                    type="number"
                    min="0"
                    value={salaryForm.amount}
                    onChange={(e) => setSalaryForm({ ...salaryForm, amount: e.target.value })}
                    placeholder="Basic salary"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label>For Month *</Label>
                  <Input
                    value={salaryForm.month}
                    onChange={(e) => setSalaryForm({ ...salaryForm, month: e.target.value })}
                    placeholder="e.g., January 2026"
                    required
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Payment Date *</Label>
                  <Input
                    type="date"
                    value={salaryForm.date}
                    onChange={(e) => setSalaryForm({ ...salaryForm, date: e.target.value })}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label>Payment Method</Label>
                  <Select
                    value={salaryForm.payment_method}
                    onValueChange={(value) => setSalaryForm({ ...salaryForm, payment_method: value })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="bank">Bank Transfer</SelectItem>
                      <SelectItem value="cash">Cash</SelectItem>
                      <SelectItem value="cheque">Cheque</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Allowances</Label>
                  <Input
                    type="number"
                    min="0"
                    value={salaryForm.allowances}
                    onChange={(e) => setSalaryForm({ ...salaryForm, allowances: e.target.value })}
                    placeholder="0"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Deductions</Label>
                  <Input
                    type="number"
                    min="0"
                    value={salaryForm.deductions}
                    onChange={(e) => setSalaryForm({ ...salaryForm, deductions: e.target.value })}
                    placeholder="0"
                  />
                </div>
              </div>
              {salaryForm.amount && (
                <div className="bg-blue-50 p-3 rounded-lg">
                  <div className="flex justify-between text-sm">
                    <span>Basic Salary:</span>
                    <span>{formatCurrency(parseFloat(salaryForm.amount) || 0)}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>+ Allowances:</span>
                    <span>{formatCurrency(parseFloat(salaryForm.allowances) || 0)}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>- Deductions:</span>
                    <span>{formatCurrency(parseFloat(salaryForm.deductions) || 0)}</span>
                  </div>
                  <hr className="my-2" />
                  <div className="flex justify-between font-semibold">
                    <span>Net Pay:</span>
                    <span>{formatCurrency(
                      (parseFloat(salaryForm.amount) || 0) + 
                      (parseFloat(salaryForm.allowances) || 0) - 
                      (parseFloat(salaryForm.deductions) || 0)
                    )}</span>
                  </div>
                </div>
              )}
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setActiveModal(null)}>Cancel</Button>
              <Button type="submit" disabled={submitting} className="bg-blue-600 hover:bg-blue-700">
                {submitting && <Loader2 className="w-4 h-4 animate-spin mr-2" />}
                Pay Salary
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Revenue Receipt Modal */}
      <Dialog open={activeModal === 'revenue'} onOpenChange={() => setActiveModal(null)}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <DollarSign className="w-5 h-5 text-green-600" />
              Receive Payment
            </DialogTitle>
            <DialogDescription>
              Record income or payment received
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleRevenueSubmit}>
            <div className="grid gap-4 py-4">
              <div className="space-y-2">
                <Label>Income Type *</Label>
                <Select
                  value={revenueForm.revenue_type}
                  onValueChange={(value) => setRevenueForm({ ...revenueForm, revenue_type: value })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {revenueTypes.map((type) => (
                      <SelectItem key={type.value} value={type.value}>{type.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Description *</Label>
                <Input
                  value={revenueForm.description}
                  onChange={(e) => setRevenueForm({ ...revenueForm, description: e.target.value })}
                  placeholder="What is this payment for?"
                  required
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Amount (LKR) *</Label>
                  <Input
                    type="number"
                    min="0"
                    step="0.01"
                    value={revenueForm.amount}
                    onChange={(e) => setRevenueForm({ ...revenueForm, amount: e.target.value })}
                    placeholder="0.00"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label>Payment Method</Label>
                  <Select
                    value={revenueForm.payment_method}
                    onValueChange={(value) => setRevenueForm({ ...revenueForm, payment_method: value })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="bank">Bank Transfer</SelectItem>
                      <SelectItem value="cash">Cash</SelectItem>
                      <SelectItem value="cheque">Cheque</SelectItem>
                      <SelectItem value="card">Card</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Receipt Date *</Label>
                  <Input
                    type="date"
                    value={revenueForm.date}
                    onChange={(e) => setRevenueForm({ ...revenueForm, date: e.target.value })}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label>Customer/Payer</Label>
                  <Input
                    value={revenueForm.customer}
                    onChange={(e) => setRevenueForm({ ...revenueForm, customer: e.target.value })}
                    placeholder="Who paid?"
                  />
                </div>
              </div>
              <div className="bg-green-50 p-3 rounded-lg text-sm text-green-800">
                <strong>This will:</strong><br />
                • Increase Cash/Bank balance<br />
                • Record as business income
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setActiveModal(null)}>Cancel</Button>
              <Button type="submit" disabled={submitting} className="bg-green-600 hover:bg-green-700">
                {submitting && <Loader2 className="w-4 h-4 animate-spin mr-2" />}
                Record Payment
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Loan Transaction Modal */}
      <Dialog open={activeModal === 'loan'} onOpenChange={() => setActiveModal(null)}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Banknote className="w-5 h-5 text-purple-600" />
              Loan Transaction
            </DialogTitle>
            <DialogDescription>
              Record loan received or repayment
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleLoanSubmit}>
            <div className="grid gap-4 py-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Transaction Type *</Label>
                  <Select
                    value={loanForm.transaction_type}
                    onValueChange={(value) => setLoanForm({ ...loanForm, transaction_type: value })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="receive">Receive Loan</SelectItem>
                      <SelectItem value="repay">Repay Loan</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Loan Type *</Label>
                  <Select
                    value={loanForm.loan_type}
                    onValueChange={(value) => setLoanForm({ ...loanForm, loan_type: value })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="bank_loan">Bank Loan</SelectItem>
                      <SelectItem value="finance_company">Finance Company Loan</SelectItem>
                      <SelectItem value="director_loan">Director Loan</SelectItem>
                      <SelectItem value="other">Other Loan</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Lender Name *</Label>
                  <Input
                    value={loanForm.lender_name}
                    onChange={(e) => setLoanForm({ ...loanForm, lender_name: e.target.value })}
                    placeholder="Bank name or person"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label>Transaction Date *</Label>
                  <Input
                    type="date"
                    value={loanForm.date}
                    onChange={(e) => setLoanForm({ ...loanForm, date: e.target.value })}
                    required
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Principal Amount (LKR) *</Label>
                  <Input
                    type="number"
                    min="0"
                    value={loanForm.amount}
                    onChange={(e) => setLoanForm({ ...loanForm, amount: e.target.value })}
                    placeholder="Loan amount"
                    required
                  />
                </div>
                {loanForm.transaction_type === 'repay' && (
                  <div className="space-y-2">
                    <Label>Interest Amount</Label>
                    <Input
                      type="number"
                      min="0"
                      value={loanForm.interest_amount}
                      onChange={(e) => setLoanForm({ ...loanForm, interest_amount: e.target.value })}
                      placeholder="0"
                    />
                  </div>
                )}
              </div>
              <div className={`p-3 rounded-lg text-sm ${
                loanForm.transaction_type === 'receive' ? 'bg-purple-50 text-purple-800' : 'bg-orange-50 text-orange-800'
              }`}>
                {loanForm.transaction_type === 'receive' ? (
                  <>
                    <strong>Loan Received will:</strong><br />
                    • Increase Cash/Bank balance<br />
                    • Create loan liability
                  </>
                ) : (
                  <>
                    <strong>Loan Repayment will:</strong><br />
                    • Reduce Cash/Bank balance<br />
                    • Reduce loan liability<br />
                    {loanForm.interest_amount && parseFloat(loanForm.interest_amount) > 0 && (
                      <>• Record interest expense</>
                    )}
                  </>
                )}
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setActiveModal(null)}>Cancel</Button>
              <Button 
                type="submit" 
                disabled={submitting} 
                className={loanForm.transaction_type === 'receive' ? 'bg-purple-600 hover:bg-purple-700' : 'bg-orange-600 hover:bg-orange-700'}
              >
                {submitting && <Loader2 className="w-4 h-4 animate-spin mr-2" />}
                {loanForm.transaction_type === 'receive' ? 'Record Loan' : 'Record Repayment'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-red-600" />
              Delete Transaction
            </AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete this transaction?
              <div className="mt-3 p-3 bg-slate-50 rounded-lg">
                <p className="font-medium text-slate-900">{transactionToDelete?.description}</p>
                <p className="text-sm text-slate-600">
                  Amount: {transactionToDelete && formatCurrency(transactionToDelete.total_debit)}
                </p>
                <p className="text-sm text-slate-500">
                  Entry: {transactionToDelete?.entry_number}
                </p>
              </div>
              <p className="mt-3 text-sm text-red-600">
                <strong>Warning:</strong> This will reverse all associated journal entries and update account balances. This action cannot be undone.
              </p>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteTransaction}
              className="bg-red-600 hover:bg-red-700"
              disabled={submitting}
            >
              {submitting && <Loader2 className="w-4 h-4 animate-spin mr-2" />}
              Delete Transaction
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
