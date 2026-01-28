import React, { useState, useEffect } from 'react';
import { paymentsAPI } from '../lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
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
import { Loader2, CreditCard, Banknote, Building2, Wallet } from 'lucide-react';
import { toast } from 'sonner';

const formatCurrency = (amount) => {
  return new Intl.NumberFormat('en-LK', {
    style: 'currency',
    currency: 'LKR',
    minimumFractionDigits: 0,
  }).format(amount);
};

const methodIcons = {
  cash: Banknote,
  bank: Building2,
  card: CreditCard,
  online: Wallet,
};

const methodColors = {
  cash: 'bg-emerald-100 text-emerald-700',
  bank: 'bg-blue-100 text-blue-700',
  card: 'bg-violet-100 text-violet-700',
  online: 'bg-amber-100 text-amber-700',
};

export const Payments = () => {
  const [payments, setPayments] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [methodFilter, setMethodFilter] = useState('all');

  const fetchData = async () => {
    try {
      const params = methodFilter !== 'all' ? { payment_method: methodFilter } : {};
      const [paymentsRes, summaryRes] = await Promise.all([
        paymentsAPI.getAll(params),
        paymentsAPI.getSummary(),
      ]);
      setPayments(paymentsRes.data);
      setSummary(summaryRes.data);
    } catch (error) {
      toast.error('Failed to fetch payments');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [methodFilter]);

  return (
    <div className="space-y-6" data-testid="payments-page">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-slate-900" style={{ fontFamily: 'Outfit, sans-serif' }}>
          Payments
        </h2>
        <p className="text-slate-500 mt-1">Payment records and cash/bank balances</p>
      </div>

      {/* Balance Cards */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card className="stat-card">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm font-medium text-slate-500">Cash Balance</p>
                <p className="text-2xl font-bold text-slate-900 mt-1">{formatCurrency(summary.cash_balance)}</p>
              </div>
              <div className="stat-icon bg-emerald-600">
                <Banknote className="w-6 h-6 text-white" />
              </div>
            </div>
          </Card>
          <Card className="stat-card">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm font-medium text-slate-500">Bank Balance</p>
                <p className="text-2xl font-bold text-slate-900 mt-1">{formatCurrency(summary.bank_balance)}</p>
              </div>
              <div className="stat-icon bg-blue-600">
                <Building2 className="w-6 h-6 text-white" />
              </div>
            </div>
          </Card>
          <Card className="stat-card">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm font-medium text-slate-500">Total Balance</p>
                <p className="text-2xl font-bold text-slate-900 mt-1">{formatCurrency(summary.total_balance)}</p>
              </div>
              <div className="stat-icon bg-indigo-600">
                <Wallet className="w-6 h-6 text-white" />
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <Select value={methodFilter} onValueChange={setMethodFilter}>
            <SelectTrigger className="w-48" data-testid="payment-method-filter">
              <SelectValue placeholder="All Methods" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Methods</SelectItem>
              <SelectItem value="cash">Cash</SelectItem>
              <SelectItem value="bank">Bank Transfer</SelectItem>
              <SelectItem value="card">Card</SelectItem>
              <SelectItem value="online">Online</SelectItem>
            </SelectContent>
          </Select>
        </CardContent>
      </Card>

      {/* Payments Table */}
      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
            </div>
          ) : payments.length === 0 ? (
            <div className="text-center py-16">
              <CreditCard className="w-12 h-12 text-slate-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-slate-900">No payments recorded</h3>
              <p className="text-slate-500 mt-1">Payments will appear here when recorded.</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="table-header">
                  <TableHead className="table-header-cell">Date</TableHead>
                  <TableHead className="table-header-cell">Reference</TableHead>
                  <TableHead className="table-header-cell">Type</TableHead>
                  <TableHead className="table-header-cell">Method</TableHead>
                  <TableHead className="table-header-cell text-right">Amount</TableHead>
                  <TableHead className="table-header-cell">Notes</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {payments.map((payment) => {
                  const MethodIcon = methodIcons[payment.payment_method] || CreditCard;
                  return (
                    <TableRow key={payment.id} className="table-row" data-testid={`payment-row-${payment.id}`}>
                      <TableCell className="table-cell text-slate-500">
                        {new Date(payment.created_at).toLocaleDateString()}
                      </TableCell>
                      <TableCell className="table-cell font-medium">{payment.reference_number}</TableCell>
                      <TableCell className="table-cell">
                        <Badge className={payment.reference_type === 'sales_order' ? 'badge-success' : 'badge-warning'}>
                          {payment.reference_type === 'sales_order' ? 'Sales' : 'Purchase'}
                        </Badge>
                      </TableCell>
                      <TableCell className="table-cell">
                        <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${methodColors[payment.payment_method]}`}>
                          <MethodIcon className="w-3.5 h-3.5" />
                          <span className="capitalize">{payment.payment_method}</span>
                        </div>
                      </TableCell>
                      <TableCell className="table-cell text-right font-medium">
                        <span className={payment.reference_type === 'sales_order' ? 'text-emerald-600' : 'text-red-600'}>
                          {payment.reference_type === 'sales_order' ? '+' : '-'}
                          {formatCurrency(payment.amount)}
                        </span>
                      </TableCell>
                      <TableCell className="table-cell text-slate-500 max-w-xs truncate">
                        {payment.notes || '-'}
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default Payments;
