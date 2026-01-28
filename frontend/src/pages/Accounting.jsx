import React, { useState, useEffect } from 'react';
import { accountingAPI } from '../lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Plus, Loader2, TrendingUp, TrendingDown, DollarSign, ArrowUpRight, ArrowDownRight } from 'lucide-react';
import { toast } from 'sonner';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';

const formatCurrency = (amount) => {
  return new Intl.NumberFormat('en-LK', {
    style: 'currency',
    currency: 'LKR',
    minimumFractionDigits: 0,
  }).format(amount);
};

const COLORS = ['#4f46e5', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'];

export const Accounting = () => {
  const [entries, setEntries] = useState([]);
  const [profitLoss, setProfitLoss] = useState(null);
  const [receivables, setReceivables] = useState(null);
  const [payables, setPayables] = useState(null);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [typeFilter, setTypeFilter] = useState('all');

  const [formData, setFormData] = useState({
    entry_type: 'income',
    category: '',
    amount: '',
    description: '',
  });

  const fetchData = async () => {
    try {
      const params = typeFilter !== 'all' ? { entry_type: typeFilter } : {};
      const [entriesRes, plRes, recRes, payRes] = await Promise.all([
        accountingAPI.getEntries(params),
        accountingAPI.getProfitLoss(),
        accountingAPI.getReceivables(),
        accountingAPI.getPayables(),
      ]);
      setEntries(entriesRes.data);
      setProfitLoss(plRes.data);
      setReceivables(recRes.data);
      setPayables(payRes.data);
    } catch (error) {
      toast.error('Failed to fetch accounting data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [typeFilter]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);

    try {
      await accountingAPI.createEntry({
        ...formData,
        amount: parseFloat(formData.amount),
      });
      toast.success('Entry created successfully');
      setDialogOpen(false);
      setFormData({ entry_type: 'income', category: '', amount: '', description: '' });
      fetchData();
    } catch (error) {
      toast.error('Failed to create entry');
    } finally {
      setSubmitting(false);
    }
  };

  const incomeChartData = profitLoss
    ? Object.entries(profitLoss.income_by_category).map(([name, value]) => ({ name, value }))
    : [];

  const expenseChartData = profitLoss
    ? Object.entries(profitLoss.expense_by_category).map(([name, value]) => ({ name, value }))
    : [];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="accounting-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900" style={{ fontFamily: 'Outfit, sans-serif' }}>
            Accounting
          </h2>
          <p className="text-slate-500 mt-1">Income, expenses, and financial summary</p>
        </div>
        <Button onClick={() => setDialogOpen(true)} className="gap-2 bg-indigo-600 hover:bg-indigo-700" data-testid="add-entry-btn">
          <Plus className="w-4 h-4" />
          Add Entry
        </Button>
      </div>

      {/* Summary Cards */}
      {profitLoss && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <Card className="stat-card">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm font-medium text-slate-500">Total Income</p>
                <p className="text-2xl font-bold text-emerald-600 mt-1">{formatCurrency(profitLoss.total_income)}</p>
              </div>
              <div className="stat-icon bg-emerald-600">
                <ArrowUpRight className="w-6 h-6 text-white" />
              </div>
            </div>
          </Card>
          <Card className="stat-card">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm font-medium text-slate-500">Total Expenses</p>
                <p className="text-2xl font-bold text-red-600 mt-1">{formatCurrency(profitLoss.total_expenses)}</p>
              </div>
              <div className="stat-icon bg-red-600">
                <ArrowDownRight className="w-6 h-6 text-white" />
              </div>
            </div>
          </Card>
          <Card className="stat-card">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm font-medium text-slate-500">Net Profit</p>
                <p className={`text-2xl font-bold mt-1 ${profitLoss.net_profit >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                  {formatCurrency(profitLoss.net_profit)}
                </p>
              </div>
              <div className={`stat-icon ${profitLoss.net_profit >= 0 ? 'bg-emerald-600' : 'bg-red-600'}`}>
                <DollarSign className="w-6 h-6 text-white" />
              </div>
            </div>
          </Card>
          <Card className="stat-card">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm font-medium text-slate-500">Outstanding</p>
                <p className="text-2xl font-bold text-amber-600 mt-1">
                  {formatCurrency((receivables?.total_receivables || 0) - (payables?.total_payables || 0))}
                </p>
                <p className="text-xs text-slate-500 mt-1">
                  Rec: {formatCurrency(receivables?.total_receivables || 0)} | Pay: {formatCurrency(payables?.total_payables || 0)}
                </p>
              </div>
              <div className="stat-icon bg-amber-600">
                <TrendingUp className="w-6 h-6 text-white" />
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="p-6">
          <CardHeader className="p-0 pb-4">
            <CardTitle className="text-lg font-semibold" style={{ fontFamily: 'Outfit, sans-serif' }}>
              Income by Category
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            {incomeChartData.length > 0 ? (
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={incomeChartData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={80}
                      fill="#8884d8"
                      paddingAngle={5}
                      dataKey="value"
                    >
                      {incomeChartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value) => formatCurrency(value)} />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="h-64 flex items-center justify-center text-slate-500">No income data</div>
            )}
          </CardContent>
        </Card>

        <Card className="p-6">
          <CardHeader className="p-0 pb-4">
            <CardTitle className="text-lg font-semibold" style={{ fontFamily: 'Outfit, sans-serif' }}>
              Expenses by Category
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            {expenseChartData.length > 0 ? (
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={expenseChartData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={80}
                      fill="#8884d8"
                      paddingAngle={5}
                      dataKey="value"
                    >
                      {expenseChartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value) => formatCurrency(value)} />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="h-64 flex items-center justify-center text-slate-500">No expense data</div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="entries" className="space-y-4">
        <TabsList>
          <TabsTrigger value="entries">All Entries</TabsTrigger>
          <TabsTrigger value="receivables">Receivables ({receivables?.items?.length || 0})</TabsTrigger>
          <TabsTrigger value="payables">Payables ({payables?.items?.length || 0})</TabsTrigger>
        </TabsList>

        <TabsContent value="entries">
          <Card>
            <CardHeader className="pb-0">
              <Select value={typeFilter} onValueChange={setTypeFilter}>
                <SelectTrigger className="w-48">
                  <SelectValue placeholder="All Types" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Types</SelectItem>
                  <SelectItem value="income">Income</SelectItem>
                  <SelectItem value="expense">Expense</SelectItem>
                </SelectContent>
              </Select>
            </CardHeader>
            <CardContent className="p-0 pt-4">
              <Table>
                <TableHeader>
                  <TableRow className="table-header">
                    <TableHead className="table-header-cell">Date</TableHead>
                    <TableHead className="table-header-cell">Type</TableHead>
                    <TableHead className="table-header-cell">Category</TableHead>
                    <TableHead className="table-header-cell">Description</TableHead>
                    <TableHead className="table-header-cell text-right">Amount</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {entries.slice(0, 50).map((entry) => (
                    <TableRow key={entry.id} className="table-row">
                      <TableCell className="table-cell text-slate-500">
                        {new Date(entry.created_at).toLocaleDateString()}
                      </TableCell>
                      <TableCell className="table-cell">
                        <Badge className={entry.entry_type === 'income' ? 'badge-success' : 'badge-error'}>
                          {entry.entry_type}
                        </Badge>
                      </TableCell>
                      <TableCell className="table-cell font-medium">{entry.category}</TableCell>
                      <TableCell className="table-cell text-slate-500 max-w-xs truncate">{entry.description}</TableCell>
                      <TableCell className="table-cell text-right font-medium">
                        <span className={entry.entry_type === 'income' ? 'text-emerald-600' : 'text-red-600'}>
                          {entry.entry_type === 'income' ? '+' : '-'}
                          {formatCurrency(entry.amount)}
                        </span>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="receivables">
          <Card>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow className="table-header">
                    <TableHead className="table-header-cell">Order #</TableHead>
                    <TableHead className="table-header-cell">Customer</TableHead>
                    <TableHead className="table-header-cell">Date</TableHead>
                    <TableHead className="table-header-cell text-right">Total</TableHead>
                    <TableHead className="table-header-cell text-right">Paid</TableHead>
                    <TableHead className="table-header-cell text-right">Balance</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {receivables?.items?.map((item) => (
                    <TableRow key={item.order_id} className="table-row">
                      <TableCell className="table-cell font-medium">{item.order_number}</TableCell>
                      <TableCell className="table-cell">{item.customer_name}</TableCell>
                      <TableCell className="table-cell text-slate-500">
                        {new Date(item.date).toLocaleDateString()}
                      </TableCell>
                      <TableCell className="table-cell text-right">{formatCurrency(item.total)}</TableCell>
                      <TableCell className="table-cell text-right text-emerald-600">{formatCurrency(item.paid)}</TableCell>
                      <TableCell className="table-cell text-right font-medium text-amber-600">{formatCurrency(item.balance)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="payables">
          <Card>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow className="table-header">
                    <TableHead className="table-header-cell">Order #</TableHead>
                    <TableHead className="table-header-cell">Supplier</TableHead>
                    <TableHead className="table-header-cell">Date</TableHead>
                    <TableHead className="table-header-cell text-right">Total</TableHead>
                    <TableHead className="table-header-cell text-right">Paid</TableHead>
                    <TableHead className="table-header-cell text-right">Balance</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {payables?.items?.map((item) => (
                    <TableRow key={item.order_id} className="table-row">
                      <TableCell className="table-cell font-medium">{item.order_number}</TableCell>
                      <TableCell className="table-cell">{item.supplier_name}</TableCell>
                      <TableCell className="table-cell text-slate-500">
                        {new Date(item.date).toLocaleDateString()}
                      </TableCell>
                      <TableCell className="table-cell text-right">{formatCurrency(item.total)}</TableCell>
                      <TableCell className="table-cell text-right text-emerald-600">{formatCurrency(item.paid)}</TableCell>
                      <TableCell className="table-cell text-right font-medium text-red-600">{formatCurrency(item.balance)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Add Entry Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent data-testid="entry-dialog">
          <DialogHeader>
            <DialogTitle style={{ fontFamily: 'Outfit, sans-serif' }}>Add Accounting Entry</DialogTitle>
            <DialogDescription>Record a manual income or expense entry</DialogDescription>
          </DialogHeader>
          <form onSubmit={handleSubmit}>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>Type *</Label>
                <Select value={formData.entry_type} onValueChange={(v) => setFormData({ ...formData, entry_type: v })}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="income">Income</SelectItem>
                    <SelectItem value="expense">Expense</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Category *</Label>
                <Input
                  value={formData.category}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                  placeholder="e.g., Sales, Rent, Utilities"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label>Amount (LKR) *</Label>
                <Input
                  type="number"
                  value={formData.amount}
                  onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label>Description *</Label>
                <Input
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  required
                />
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>Cancel</Button>
              <Button type="submit" disabled={submitting} className="bg-indigo-600 hover:bg-indigo-700">
                {submitting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                Add Entry
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Accounting;
