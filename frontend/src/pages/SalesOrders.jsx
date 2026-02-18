import React, { useState, useEffect } from 'react';
import { salesOrdersAPI, customersAPI, productsAPI, paymentsAPI } from '../lib/api';
import api from '../lib/api';
import { Card, CardContent } from '../components/ui/card';
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
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '../components/ui/dropdown-menu';
import { Plus, Search, MoreHorizontal, Eye, Loader2, ShoppingCart, CreditCard, RotateCcw, Trash2 } from 'lucide-react';
import { toast } from 'sonner';

const formatCurrency = (amount) => {
  return new Intl.NumberFormat('en-LK', {
    style: 'currency',
    currency: 'LKR',
    minimumFractionDigits: 0,
  }).format(amount);
};

const statusColors = {
  pending: 'badge-warning',
  completed: 'badge-success',
  returned: 'badge-error',
};

const paymentColors = {
  unpaid: 'badge-error',
  partial: 'badge-warning',
  paid: 'badge-success',
};

export const SalesOrders = () => {
  const [orders, setOrders] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [products, setProducts] = useState([]);
  const [bankAccounts, setBankAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('all');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [paymentDialogOpen, setPaymentDialogOpen] = useState(false);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const [formData, setFormData] = useState({
    customer_id: '',
    items: [],
    discount: 0,
    notes: '',
  });

  const [newItem, setNewItem] = useState({
    product_id: '',
    quantity: 1,
  });

  const [paymentData, setPaymentData] = useState({
    amount: '',
    payment_method: 'bank',
    bank_account_id: '',
    notes: '',
  });

  const fetchData = async () => {
    try {
      const params = {};
      if (statusFilter && statusFilter !== 'all') params.status = statusFilter;

      const [ordersRes, customersRes, productsRes, bankAccountsRes] = await Promise.all([
        salesOrdersAPI.getAll(params),
        customersAPI.getAll(),
        productsAPI.getAll(),
        api.get('/bank-accounts'),
      ]);
      setOrders(ordersRes.data);
      setCustomers(customersRes.data);
      setProducts(productsRes.data);
      setBankAccounts(bankAccountsRes.data);
    } catch (error) {
      toast.error('Failed to fetch data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [statusFilter]);

  const handleAddItem = () => {
    const product = products.find((p) => p.id === newItem.product_id);
    if (!product) return;

    const item = {
      product_id: product.id,
      product_name: product.name,
      sku: product.sku,
      quantity: parseInt(newItem.quantity),
      unit_price: product.selling_price,
      total: product.selling_price * parseInt(newItem.quantity),
    };

    setFormData({
      ...formData,
      items: [...formData.items, item],
    });

    setNewItem({ product_id: '', quantity: 1 });
  };

  const handleRemoveItem = (index) => {
    setFormData({
      ...formData,
      items: formData.items.filter((_, i) => i !== index),
    });
  };

  const calculateTotal = () => {
    const subtotal = formData.items.reduce((sum, item) => sum + item.total, 0);
    return subtotal - (parseFloat(formData.discount) || 0);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (formData.items.length === 0) {
      toast.error('Please add at least one item');
      return;
    }

    setSubmitting(true);
    try {
      await salesOrdersAPI.create(formData);
      toast.success('Sales order created successfully');
      setDialogOpen(false);
      setFormData({ customer_id: '', items: [], discount: 0, notes: '' });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create order');
    } finally {
      setSubmitting(false);
    }
  };

  const handleViewOrder = async (order) => {
    try {
      const response = await salesOrdersAPI.getOne(order.id);
      setSelectedOrder(response.data);
      setViewDialogOpen(true);
    } catch (error) {
      toast.error('Failed to load order details');
    }
  };

  const handleRecordPayment = async () => {
    if (!paymentData.bank_account_id) {
      toast.error('Please select an account to receive payment');
      return;
    }
    setSubmitting(true);
    try {
      await paymentsAPI.create({
        reference_type: 'sales_order',
        reference_id: selectedOrder.id,
        amount: parseFloat(paymentData.amount),
        payment_method: paymentData.payment_method,
        bank_account_id: paymentData.bank_account_id,
        notes: paymentData.notes,
      });
      toast.success('Payment recorded successfully');
      setPaymentDialogOpen(false);
      setPaymentData({ amount: '', payment_method: 'bank', bank_account_id: '', notes: '' });
      fetchData();
    } catch (error) {
      toast.error('Failed to record payment');
    } finally {
      setSubmitting(false);
    }
  };

  const handleReturn = async (order) => {
    if (!window.confirm('Are you sure you want to return this order?')) return;
    try {
      await salesOrdersAPI.return(order.id);
      toast.success('Order returned successfully');
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to return order');
    }
  };

  return (
    <div className="space-y-6" data-testid="sales-orders-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900" style={{ fontFamily: 'Outfit, sans-serif' }}>
            Sales Orders
          </h2>
          <p className="text-slate-500 mt-1">{orders.length} orders</p>
        </div>
        <Button onClick={() => setDialogOpen(true)} className="gap-2 bg-indigo-600 hover:bg-indigo-700" data-testid="create-order-btn">
          <Plus className="w-4 h-4" />
          New Order
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-48" data-testid="status-filter">
              <SelectValue placeholder="All Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Status</SelectItem>
              <SelectItem value="pending">Pending</SelectItem>
              <SelectItem value="completed">Completed</SelectItem>
              <SelectItem value="returned">Returned</SelectItem>
            </SelectContent>
          </Select>
        </CardContent>
      </Card>

      {/* Orders Table */}
      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
            </div>
          ) : orders.length === 0 ? (
            <div className="text-center py-16">
              <ShoppingCart className="w-12 h-12 text-slate-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-slate-900">No orders found</h3>
              <p className="text-slate-500 mt-1">Create your first sales order.</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="table-header">
                  <TableHead className="table-header-cell">Order #</TableHead>
                  <TableHead className="table-header-cell">Customer</TableHead>
                  <TableHead className="table-header-cell">Date</TableHead>
                  <TableHead className="table-header-cell text-right">Total</TableHead>
                  <TableHead className="table-header-cell">Status</TableHead>
                  <TableHead className="table-header-cell">Payment</TableHead>
                  <TableHead className="table-header-cell w-12"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {orders.map((order) => (
                  <TableRow key={order.id} className="table-row" data-testid={`order-row-${order.id}`}>
                    <TableCell className="table-cell font-medium">{order.order_number}</TableCell>
                    <TableCell className="table-cell">{order.customer_name}</TableCell>
                    <TableCell className="table-cell text-slate-500">
                      {new Date(order.created_at).toLocaleDateString()}
                    </TableCell>
                    <TableCell className="table-cell text-right font-medium">{formatCurrency(order.total)}</TableCell>
                    <TableCell className="table-cell">
                      <Badge className={statusColors[order.status]}>{order.status}</Badge>
                    </TableCell>
                    <TableCell className="table-cell">
                      <Badge className={paymentColors[order.payment_status]}>{order.payment_status}</Badge>
                    </TableCell>
                    <TableCell className="table-cell">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon">
                            <MoreHorizontal className="w-4 h-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => handleViewOrder(order)}>
                            <Eye className="w-4 h-4 mr-2" />
                            View Details
                          </DropdownMenuItem>
                          {order.payment_status !== 'paid' && order.status !== 'returned' && (
                            <DropdownMenuItem onClick={() => {
                              setSelectedOrder(order);
                              setPaymentData({ ...paymentData, amount: (order.total - order.paid_amount).toString() });
                              setPaymentDialogOpen(true);
                            }}>
                              <CreditCard className="w-4 h-4 mr-2" />
                              Record Payment
                            </DropdownMenuItem>
                          )}
                          {order.status !== 'returned' && (
                            <DropdownMenuItem className="text-amber-600" onClick={() => handleReturn(order)}>
                              <RotateCcw className="w-4 h-4 mr-2" />
                              Return Order
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

      {/* Create Order Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-2xl" data-testid="create-order-dialog">
          <DialogHeader>
            <DialogTitle style={{ fontFamily: 'Outfit, sans-serif' }}>Create Sales Order</DialogTitle>
            <DialogDescription>Add items to create a new sales order</DialogDescription>
          </DialogHeader>
          <form onSubmit={handleSubmit}>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>Customer *</Label>
                <Select value={formData.customer_id} onValueChange={(v) => setFormData({ ...formData, customer_id: v })}>
                  <SelectTrigger data-testid="select-customer">
                    <SelectValue placeholder="Select customer" />
                  </SelectTrigger>
                  <SelectContent>
                    {customers.map((c) => (
                      <SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Add Item */}
              <div className="flex gap-2">
                <Select value={newItem.product_id} onValueChange={(v) => setNewItem({ ...newItem, product_id: v })}>
                  <SelectTrigger className="flex-1" data-testid="select-product">
                    <SelectValue placeholder="Select product" />
                  </SelectTrigger>
                  <SelectContent>
                    {products.map((p) => (
                      <SelectItem key={p.id} value={p.id}>
                        {p.name} - {formatCurrency(p.selling_price)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Input
                  type="number"
                  min="1"
                  value={newItem.quantity}
                  onChange={(e) => setNewItem({ ...newItem, quantity: e.target.value })}
                  className="w-24"
                  placeholder="Qty"
                  data-testid="item-quantity"
                />
                <Button type="button" onClick={handleAddItem} variant="outline" data-testid="add-item-btn">
                  Add
                </Button>
              </div>

              {/* Items List */}
              {formData.items.length > 0 && (
                <div className="border rounded-lg overflow-hidden">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Product</TableHead>
                        <TableHead className="text-right">Price</TableHead>
                        <TableHead className="text-right">Qty</TableHead>
                        <TableHead className="text-right">Total</TableHead>
                        <TableHead className="w-10"></TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {formData.items.map((item, index) => (
                        <TableRow key={index}>
                          <TableCell>{item.product_name}</TableCell>
                          <TableCell className="text-right">{formatCurrency(item.unit_price)}</TableCell>
                          <TableCell className="text-right">{item.quantity}</TableCell>
                          <TableCell className="text-right font-medium">{formatCurrency(item.total)}</TableCell>
                          <TableCell>
                            <Button variant="ghost" size="icon" onClick={() => handleRemoveItem(index)}>
                              <Trash2 className="w-4 h-4 text-red-500" />
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              )}

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Label>Discount:</Label>
                  <Input
                    type="number"
                    value={formData.discount}
                    onChange={(e) => setFormData({ ...formData, discount: e.target.value })}
                    className="w-32"
                    data-testid="order-discount"
                  />
                </div>
                <div className="text-right">
                  <p className="text-sm text-slate-500">Total</p>
                  <p className="text-2xl font-bold">{formatCurrency(calculateTotal())}</p>
                </div>
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>Cancel</Button>
              <Button type="submit" disabled={submitting || !formData.customer_id} className="bg-indigo-600 hover:bg-indigo-700" data-testid="submit-order-btn">
                {submitting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                Create Order
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* View Order Dialog */}
      <Dialog open={viewDialogOpen} onOpenChange={setViewDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle style={{ fontFamily: 'Outfit, sans-serif' }}>
              Order {selectedOrder?.order_number}
            </DialogTitle>
          </DialogHeader>
          {selectedOrder && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-slate-500">Customer</p>
                  <p className="font-medium">{selectedOrder.customer?.name || selectedOrder.customer_name}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-500">Date</p>
                  <p className="font-medium">{new Date(selectedOrder.created_at).toLocaleString()}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-500">Status</p>
                  <Badge className={statusColors[selectedOrder.status]}>{selectedOrder.status}</Badge>
                </div>
                <div>
                  <p className="text-sm text-slate-500">Payment</p>
                  <Badge className={paymentColors[selectedOrder.payment_status]}>{selectedOrder.payment_status}</Badge>
                </div>
              </div>

              <div className="border rounded-lg overflow-hidden">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Product</TableHead>
                      <TableHead className="text-right">Price</TableHead>
                      <TableHead className="text-right">Qty</TableHead>
                      <TableHead className="text-right">Total</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {selectedOrder.items.map((item, index) => (
                      <TableRow key={index}>
                        <TableCell>{item.product_name}</TableCell>
                        <TableCell className="text-right">{formatCurrency(item.unit_price)}</TableCell>
                        <TableCell className="text-right">{item.quantity}</TableCell>
                        <TableCell className="text-right font-medium">{formatCurrency(item.total)}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>

              <div className="flex justify-end">
                <div className="text-right space-y-1">
                  <p className="text-sm"><span className="text-slate-500">Subtotal:</span> {formatCurrency(selectedOrder.subtotal)}</p>
                  <p className="text-sm"><span className="text-slate-500">Discount:</span> -{formatCurrency(selectedOrder.discount)}</p>
                  <p className="text-lg font-bold"><span className="text-slate-500">Total:</span> {formatCurrency(selectedOrder.total)}</p>
                  <p className="text-sm text-emerald-600"><span className="text-slate-500">Paid:</span> {formatCurrency(selectedOrder.paid_amount)}</p>
                  <p className="text-sm text-amber-600"><span className="text-slate-500">Balance:</span> {formatCurrency(selectedOrder.total - selectedOrder.paid_amount)}</p>
                </div>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Payment Dialog */}
      <Dialog open={paymentDialogOpen} onOpenChange={setPaymentDialogOpen}>
        <DialogContent data-testid="payment-dialog">
          <DialogHeader>
            <DialogTitle style={{ fontFamily: 'Outfit, sans-serif' }}>Record Payment</DialogTitle>
            <DialogDescription>
              Balance due: {formatCurrency(selectedOrder?.total - selectedOrder?.paid_amount || 0)}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Amount (LKR) *</Label>
              <Input
                type="number"
                value={paymentData.amount}
                onChange={(e) => setPaymentData({ ...paymentData, amount: e.target.value })}
                data-testid="payment-amount"
              />
            </div>
            <div className="space-y-2">
              <Label>Payment Received To *</Label>
              <Select 
                value={paymentData.bank_account_id} 
                onValueChange={(v) => setPaymentData({ ...paymentData, bank_account_id: v })}
              >
                <SelectTrigger data-testid="payment-account-select">
                  <SelectValue placeholder="Select receiving account" />
                </SelectTrigger>
                <SelectContent>
                  {bankAccounts.map((acc) => (
                    <SelectItem key={acc.id} value={acc.id}>
                      {acc.account_name} ({acc.account_type === 'cash' ? 'Cash' : acc.bank_name}) - {formatCurrency(acc.current_balance)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className="text-xs text-gray-500">
                Select the bank or cash account where payment was received
              </p>
            </div>
            <div className="space-y-2">
              <Label>Payment Method</Label>
              <Select value={paymentData.payment_method} onValueChange={(v) => setPaymentData({ ...paymentData, payment_method: v })}>
                <SelectTrigger data-testid="payment-method">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="cash">Cash</SelectItem>
                  <SelectItem value="bank">Bank Transfer</SelectItem>
                  <SelectItem value="card">Card</SelectItem>
                  <SelectItem value="online">Online Payment</SelectItem>
                  <SelectItem value="cheque">Cheque</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Notes</Label>
              <Input
                value={paymentData.notes}
                onChange={(e) => setPaymentData({ ...paymentData, notes: e.target.value })}
                placeholder="Payment reference, cheque number, etc."
              />
            </div>
            <div className="bg-green-50 p-3 rounded-lg text-sm text-green-800">
              <strong>This will:</strong><br />
              • Increase selected account balance<br />
              • Reduce Accounts Receivable<br />
              • Create journal entry in General Ledger
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setPaymentDialogOpen(false)}>Cancel</Button>
            <Button onClick={handleRecordPayment} disabled={submitting || !paymentData.amount || !paymentData.bank_account_id} className="bg-indigo-600 hover:bg-indigo-700" data-testid="submit-payment-btn">
              {submitting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
              Record Payment
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default SalesOrders;
