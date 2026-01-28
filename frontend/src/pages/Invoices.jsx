import React, { useState, useEffect } from 'react';
import { invoicesAPI } from '../lib/api';
import { Card, CardContent } from '../components/ui/card';
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
import { Loader2, FileText } from 'lucide-react';
import { toast } from 'sonner';

const formatCurrency = (amount) => {
  return new Intl.NumberFormat('en-LK', {
    style: 'currency',
    currency: 'LKR',
    minimumFractionDigits: 0,
  }).format(amount);
};

const statusColors = {
  unpaid: 'badge-error',
  partial: 'badge-warning',
  paid: 'badge-success',
};

export const Invoices = () => {
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('all');

  const fetchInvoices = async () => {
    try {
      const status = statusFilter !== 'all' ? statusFilter : undefined;
      const response = await invoicesAPI.getAll(status);
      setInvoices(response.data);
    } catch (error) {
      toast.error('Failed to fetch invoices');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInvoices();
  }, [statusFilter]);

  return (
    <div className="space-y-6" data-testid="invoices-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900" style={{ fontFamily: 'Outfit, sans-serif' }}>
            Invoices
          </h2>
          <p className="text-slate-500 mt-1">{invoices.length} invoices</p>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-48" data-testid="invoice-status-filter">
              <SelectValue placeholder="All Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Status</SelectItem>
              <SelectItem value="unpaid">Unpaid</SelectItem>
              <SelectItem value="partial">Partial</SelectItem>
              <SelectItem value="paid">Paid</SelectItem>
            </SelectContent>
          </Select>
        </CardContent>
      </Card>

      {/* Invoices Table */}
      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
            </div>
          ) : invoices.length === 0 ? (
            <div className="text-center py-16">
              <FileText className="w-12 h-12 text-slate-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-slate-900">No invoices found</h3>
              <p className="text-slate-500 mt-1">Invoices are generated from sales orders.</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="table-header">
                  <TableHead className="table-header-cell">Invoice #</TableHead>
                  <TableHead className="table-header-cell">Customer</TableHead>
                  <TableHead className="table-header-cell">Date</TableHead>
                  <TableHead className="table-header-cell text-right">Total</TableHead>
                  <TableHead className="table-header-cell text-right">Paid</TableHead>
                  <TableHead className="table-header-cell text-right">Balance</TableHead>
                  <TableHead className="table-header-cell">Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {invoices.map((invoice) => (
                  <TableRow key={invoice.id} className="table-row" data-testid={`invoice-row-${invoice.id}`}>
                    <TableCell className="table-cell font-medium">{invoice.invoice_number}</TableCell>
                    <TableCell className="table-cell">{invoice.customer_name}</TableCell>
                    <TableCell className="table-cell text-slate-500">
                      {new Date(invoice.date).toLocaleDateString()}
                    </TableCell>
                    <TableCell className="table-cell text-right font-medium">{formatCurrency(invoice.total)}</TableCell>
                    <TableCell className="table-cell text-right text-emerald-600">{formatCurrency(invoice.paid_amount)}</TableCell>
                    <TableCell className="table-cell text-right text-amber-600">{formatCurrency(invoice.balance)}</TableCell>
                    <TableCell className="table-cell">
                      <Badge className={statusColors[invoice.status]}>{invoice.status}</Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default Invoices;
