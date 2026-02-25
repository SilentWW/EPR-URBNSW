import React, { useState, useEffect } from 'react';
import { purchaseOrdersAPI, suppliersAPI, productsAPI, paymentsAPI } from '../lib/api';
import api from '../lib/api';
import { useAuth } from '../context/AuthContext';
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
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '../components/ui/dropdown-menu';
import { Switch } from '../components/ui/switch';
import { Plus, MoreHorizontal, Eye, Loader2, ClipboardList, CreditCard, PackageCheck, Trash2, FileInput, Pencil, AlertTriangle, Receipt, TruckIcon } from 'lucide-react';
import { toast } from 'sonner';
import { useNavigate } from 'react-router-dom';

const formatCurrency = (amount) => {
  return new Intl.NumberFormat('en-LK', {
    style: 'currency',
    currency: 'LKR',
    minimumFractionDigits: 0,
  }).format(amount);
};

const statusColors = {
  pending: 'badge-warning',
  received: 'badge-success',
};

const paymentColors = {
  unpaid: 'badge-error',
  partial: 'badge-warning',
  paid: 'badge-success',
};

export const PurchaseOrders = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [orders, setOrders] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [products, setProducts] = useState([]);
  const [bankAccounts, setBankAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('all');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [paymentDialogOpen, setPaymentDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  // Check if user can edit/delete (admin or manager)
  const canEditDelete = user?.role === 'admin' || user?.role === 'manager';

  const [formData, setFormData] = useState({
    supplier_id: '',
    items: [],
    notes: '',
  });

  const [editFormData, setEditFormData] = useState({
    supplier_id: '',
    items: [],
    notes: '',
  });

  // Additional charges state
  const [chargesDialogOpen, setChargesDialogOpen] = useState(false);
  const [chargeTypes, setChargeTypes] = useState([]);
  const [additionalCharges, setAdditionalCharges] = useState([]);
  const [newCharge, setNewCharge] = useState({
    charge_type: '',
    description: '',
    amount: '',
    pay_immediately: false,
    bank_account_id: ''
  });

  const [newItem, setNewItem] = useState({
    product_id: '',
    quantity: 1,
    unit_price: '',
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

      const [ordersRes, suppliersRes, productsRes, bankAccountsRes, chargeTypesRes] = await Promise.all([
        purchaseOrdersAPI.getAll(params),
        suppliersAPI.getAll(),
        productsAPI.getAll(),
        api.get('/bank-accounts'),
        api.get('/grn/charge-types').catch(() => ({ data: [] })),
      ]);
      setOrders(ordersRes.data);
      setSuppliers(suppliersRes.data);
      setProducts(productsRes.data);
      setBankAccounts(bankAccountsRes.data);
      setChargeTypes(chargeTypesRes.data || []);
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

    const unitPrice = parseFloat(newItem.unit_price) || product.cost_price;
    const item = {
      product_id: product.id,
      product_name: product.name,
      sku: product.sku,
      quantity: parseInt(newItem.quantity),
      unit_price: unitPrice,
      total: unitPrice * parseInt(newItem.quantity),
    };

    setFormData({
      ...formData,
      items: [...formData.items, item],
    });

    setNewItem({ product_id: '', quantity: 1, unit_price: '' });
  };

  const handleRemoveItem = (index) => {
    setFormData({
      ...formData,
      items: formData.items.filter((_, i) => i !== index),
    });
  };

  const calculateTotal = () => {
    return formData.items.reduce((sum, item) => sum + item.total, 0);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (formData.items.length === 0) {
      toast.error('Please add at least one item');
      return;
    }

    setSubmitting(true);
    try {
      await purchaseOrdersAPI.create(formData);
      toast.success('Purchase order created successfully');
      setDialogOpen(false);
      setFormData({ supplier_id: '', items: [], notes: '' });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create order');
    } finally {
      setSubmitting(false);
    }
  };

  const handleViewOrder = async (order) => {
    try {
      const response = await purchaseOrdersAPI.getOne(order.id);
      setSelectedOrder(response.data);
      setViewDialogOpen(true);
    } catch (error) {
      toast.error('Failed to load order details');
    }
  };

  const handleReceiveOrder = async (order) => {
    if (!window.confirm('Mark this order as received? This will add items to inventory.')) return;
    try {
      await purchaseOrdersAPI.receive(order.id);
      toast.success('Goods received successfully');
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to receive order');
    }
  };

  const handleRecordPayment = async () => {
    setSubmitting(true);
    try {
      await paymentsAPI.create({
        reference_type: 'purchase_order',
        reference_id: selectedOrder.id,
        amount: parseFloat(paymentData.amount),
        payment_method: paymentData.payment_method,
        bank_account_id: paymentData.bank_account_id || null,
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

  // Edit handlers
  const [editItem, setEditItem] = useState({
    product_id: '',
    quantity: 1,
    unit_price: '',
  });

  const handleOpenEditDialog = async (order) => {
    try {
      const response = await purchaseOrdersAPI.getOne(order.id);
      const orderData = response.data;
      setSelectedOrder(orderData);
      setEditFormData({
        supplier_id: orderData.supplier_id,
        items: orderData.items || [],
        notes: orderData.notes || '',
      });
      setEditDialogOpen(true);
    } catch (error) {
      toast.error('Failed to load order details');
    }
  };

  const handleAddEditItem = () => {
    const product = products.find((p) => p.id === editItem.product_id);
    if (!product) return;

    const unitPrice = parseFloat(editItem.unit_price) || product.cost_price;
    const item = {
      product_id: product.id,
      product_name: product.name,
      sku: product.sku,
      quantity: parseInt(editItem.quantity),
      unit_price: unitPrice,
      total: unitPrice * parseInt(editItem.quantity),
    };

    setEditFormData({
      ...editFormData,
      items: [...editFormData.items, item],
    });

    setEditItem({ product_id: '', quantity: 1, unit_price: '' });
  };

  const handleRemoveEditItem = (index) => {
    setEditFormData({
      ...editFormData,
      items: editFormData.items.filter((_, i) => i !== index),
    });
  };

  const calculateEditTotal = () => {
    return editFormData.items.reduce((sum, item) => sum + item.total, 0);
  };

  const handleEditSubmit = async (e) => {
    e.preventDefault();
    if (editFormData.items.length === 0) {
      toast.error('Please add at least one item');
      return;
    }

    setSubmitting(true);
    try {
      await purchaseOrdersAPI.update(selectedOrder.id, editFormData);
      toast.success('Purchase order updated successfully');
      setEditDialogOpen(false);
      setEditFormData({ supplier_id: '', items: [], notes: '' });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update order');
    } finally {
      setSubmitting(false);
    }
  };

  // Delete handler
  const handleDeleteOrder = async () => {
    setSubmitting(true);
    try {
      await purchaseOrdersAPI.delete(selectedOrder.id);
      toast.success('Purchase order deleted successfully');
      setDeleteDialogOpen(false);
      setSelectedOrder(null);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete order');
    } finally {
      setSubmitting(false);
    }
  };

  // Additional charges handlers
  const handleOpenChargesDialog = (order) => {
    setSelectedOrder(order);
    setAdditionalCharges(order.additional_charges || []);
    setNewCharge({
      charge_type: '',
      description: '',
      amount: '',
      pay_immediately: false,
      bank_account_id: ''
    });
    setChargesDialogOpen(true);
  };

  const handleAddCharge = () => {
    if (!newCharge.charge_type || !newCharge.amount) {
      toast.error('Please select charge type and enter amount');
      return;
    }
    if (newCharge.pay_immediately && !newCharge.bank_account_id) {
      toast.error('Please select a bank account for immediate payment');
      return;
    }
    
    const chargeType = chargeTypes.find(ct => ct.id === newCharge.charge_type);
    setAdditionalCharges([
      ...additionalCharges,
      {
        ...newCharge,
        amount: parseFloat(newCharge.amount),
        charge_type_name: chargeType?.name || newCharge.charge_type
      }
    ]);
    setNewCharge({
      charge_type: '',
      description: '',
      amount: '',
      pay_immediately: false,
      bank_account_id: ''
    });
  };

  const handleRemoveCharge = (index) => {
    setAdditionalCharges(additionalCharges.filter((_, i) => i !== index));
  };

  const handleSubmitCharges = async () => {
    if (additionalCharges.length === 0) {
      toast.error('Please add at least one charge');
      return;
    }

    // Filter only new charges (ones not yet saved)
    const existingChargeCount = (selectedOrder.additional_charges || []).length;
    const newCharges = additionalCharges.slice(existingChargeCount);
    
    if (newCharges.length === 0) {
      toast.info('No new charges to add');
      setChargesDialogOpen(false);
      return;
    }

    setSubmitting(true);
    try {
      await api.post(`/purchase-orders/${selectedOrder.id}/additional-charges`, {
        additional_charges: newCharges
      });
      toast.success('Additional charges added successfully');
      setChargesDialogOpen(false);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to add charges');
    } finally {
      setSubmitting(false);
    }
  };

  const calculateChargesTotal = () => {
    const expenses = additionalCharges
      .filter(c => c.charge_type !== 'discount')
      .reduce((sum, c) => sum + (parseFloat(c.amount) || 0), 0);
    const discounts = additionalCharges
      .filter(c => c.charge_type === 'discount')
      .reduce((sum, c) => sum + (parseFloat(c.amount) || 0), 0);
    return { expenses, discounts, net: expenses - discounts };
  };

  return (
    <div className="space-y-6" data-testid="purchase-orders-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900" style={{ fontFamily: 'Outfit, sans-serif' }}>
            Purchase Orders
          </h2>
          <p className="text-slate-500 mt-1">{orders.length} orders</p>
        </div>
        <Button onClick={() => setDialogOpen(true)} className="gap-2 bg-indigo-600 hover:bg-indigo-700" data-testid="create-po-btn">
          <Plus className="w-4 h-4" />
          New Purchase Order
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-48" data-testid="po-status-filter">
              <SelectValue placeholder="All Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Status</SelectItem>
              <SelectItem value="pending">Pending</SelectItem>
              <SelectItem value="received">Received</SelectItem>
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
              <ClipboardList className="w-12 h-12 text-slate-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-slate-900">No purchase orders found</h3>
              <p className="text-slate-500 mt-1">Create your first purchase order.</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="table-header">
                  <TableHead className="table-header-cell">Order #</TableHead>
                  <TableHead className="table-header-cell">Supplier</TableHead>
                  <TableHead className="table-header-cell">Date</TableHead>
                  <TableHead className="table-header-cell text-right">Total</TableHead>
                  <TableHead className="table-header-cell">Status</TableHead>
                  <TableHead className="table-header-cell">Payment</TableHead>
                  <TableHead className="table-header-cell w-12"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {orders.map((order) => (
                  <TableRow key={order.id} className="table-row" data-testid={`po-row-${order.id}`}>
                    <TableCell className="table-cell font-medium">{order.order_number}</TableCell>
                    <TableCell className="table-cell">{order.supplier_name}</TableCell>
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
                          {order.status === 'pending' && (
                            <>
                              <DropdownMenuItem onClick={() => navigate(`/grn?po_id=${order.id}`)}>
                                <FileInput className="w-4 h-4 mr-2" />
                                Receive as GRN
                              </DropdownMenuItem>
                              <DropdownMenuItem onClick={() => handleReceiveOrder(order)}>
                                <PackageCheck className="w-4 h-4 mr-2" />
                                Quick Receive
                              </DropdownMenuItem>
                            </>
                          )}
                          {order.payment_status !== 'paid' && (
                            <DropdownMenuItem onClick={() => {
                              setSelectedOrder(order);
                              setPaymentData({ amount: (order.total - order.paid_amount).toString(), payment_method: 'bank', bank_account_id: '', notes: '' });
                              setPaymentDialogOpen(true);
                            }}>
                              <CreditCard className="w-4 h-4 mr-2" />
                              Record Payment
                            </DropdownMenuItem>
                          )}
                          {/* Edit and Delete - only for admin and manager */}
                          {canEditDelete && order.status === 'pending' && (
                            <>
                              <DropdownMenuSeparator />
                              <DropdownMenuItem onClick={() => handleOpenEditDialog(order)}>
                                <Pencil className="w-4 h-4 mr-2" />
                                Edit Order
                              </DropdownMenuItem>
                              {order.paid_amount === 0 && (
                                <DropdownMenuItem 
                                  className="text-red-600"
                                  onClick={() => {
                                    setSelectedOrder(order);
                                    setDeleteDialogOpen(true);
                                  }}
                                >
                                  <Trash2 className="w-4 h-4 mr-2" />
                                  Delete Order
                                </DropdownMenuItem>
                              )}
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

      {/* Create PO Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-2xl" data-testid="create-po-dialog">
          <DialogHeader>
            <DialogTitle style={{ fontFamily: 'Outfit, sans-serif' }}>Create Purchase Order</DialogTitle>
            <DialogDescription>Add items to create a new purchase order</DialogDescription>
          </DialogHeader>
          <form onSubmit={handleSubmit}>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>Supplier *</Label>
                <Select value={formData.supplier_id} onValueChange={(v) => setFormData({ ...formData, supplier_id: v })}>
                  <SelectTrigger data-testid="select-supplier">
                    <SelectValue placeholder="Select supplier" />
                  </SelectTrigger>
                  <SelectContent>
                    {suppliers.map((s) => (
                      <SelectItem key={s.id} value={s.id}>{s.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Add Item */}
              <div className="flex gap-2">
                <Select value={newItem.product_id} onValueChange={(v) => {
                  const product = products.find(p => p.id === v);
                  setNewItem({ ...newItem, product_id: v, unit_price: product?.cost_price.toString() || '' });
                }}>
                  <SelectTrigger className="flex-1" data-testid="select-po-product">
                    <SelectValue placeholder="Select product" />
                  </SelectTrigger>
                  <SelectContent>
                    {products.map((p) => (
                      <SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Input
                  type="number"
                  value={newItem.unit_price}
                  onChange={(e) => setNewItem({ ...newItem, unit_price: e.target.value })}
                  className="w-28"
                  placeholder="Price"
                />
                <Input
                  type="number"
                  min="1"
                  value={newItem.quantity}
                  onChange={(e) => setNewItem({ ...newItem, quantity: e.target.value })}
                  className="w-20"
                  placeholder="Qty"
                />
                <Button type="button" onClick={handleAddItem} variant="outline">Add</Button>
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

              <div className="flex justify-end">
                <div className="text-right">
                  <p className="text-sm text-slate-500">Total</p>
                  <p className="text-2xl font-bold">{formatCurrency(calculateTotal())}</p>
                </div>
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>Cancel</Button>
              <Button type="submit" disabled={submitting || !formData.supplier_id} className="bg-indigo-600 hover:bg-indigo-700" data-testid="submit-po-btn">
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
              Purchase Order {selectedOrder?.order_number}
            </DialogTitle>
          </DialogHeader>
          {selectedOrder && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-slate-500">Supplier</p>
                  <p className="font-medium">{selectedOrder.supplier?.name || selectedOrder.supplier_name}</p>
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
                  <p className="text-lg font-bold">Total: {formatCurrency(selectedOrder.total)}</p>
                  <p className="text-sm text-emerald-600">Paid: {formatCurrency(selectedOrder.paid_amount)}</p>
                  <p className="text-sm text-amber-600">Balance: {formatCurrency(selectedOrder.total - selectedOrder.paid_amount)}</p>
                </div>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Payment Dialog */}
      <Dialog open={paymentDialogOpen} onOpenChange={setPaymentDialogOpen}>
        <DialogContent>
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
                data-testid="payment-amount-input"
              />
            </div>
            <div className="space-y-2">
              <Label>Pay From Account *</Label>
              <Select 
                value={paymentData.bank_account_id} 
                onValueChange={(v) => setPaymentData({ ...paymentData, bank_account_id: v })}
              >
                <SelectTrigger data-testid="payment-bank-account-select">
                  <SelectValue placeholder="Select bank/cash account" />
                </SelectTrigger>
                <SelectContent>
                  {bankAccounts.map((acc) => (
                    <SelectItem key={acc.id} value={acc.id}>
                      {acc.account_name} ({acc.account_type === 'bank' ? acc.bank_name : 'Cash'}) - {formatCurrency(acc.current_balance)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Payment Method</Label>
              <Select value={paymentData.payment_method} onValueChange={(v) => setPaymentData({ ...paymentData, payment_method: v })}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="cash">Cash</SelectItem>
                  <SelectItem value="bank">Bank Transfer</SelectItem>
                  <SelectItem value="card">Card</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="bg-amber-50 p-3 rounded-lg text-sm text-amber-800">
              <strong>This will:</strong><br />
              • Reduce selected account balance<br />
              • Increase inventory value<br />
              • Create journal entry
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setPaymentDialogOpen(false)}>Cancel</Button>
            <Button onClick={handleRecordPayment} disabled={submitting || !paymentData.amount} className="bg-indigo-600 hover:bg-indigo-700" data-testid="submit-payment-btn">
              {submitting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
              Record Payment
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit PO Dialog */}
      <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
        <DialogContent className="max-w-2xl" data-testid="edit-po-dialog">
          <DialogHeader>
            <DialogTitle style={{ fontFamily: 'Outfit, sans-serif' }}>Edit Purchase Order</DialogTitle>
            <DialogDescription>
              {selectedOrder?.order_number} - Modify order details
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleEditSubmit}>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>Supplier *</Label>
                <Select value={editFormData.supplier_id} onValueChange={(v) => setEditFormData({ ...editFormData, supplier_id: v })}>
                  <SelectTrigger data-testid="edit-select-supplier">
                    <SelectValue placeholder="Select supplier" />
                  </SelectTrigger>
                  <SelectContent>
                    {suppliers.map((s) => (
                      <SelectItem key={s.id} value={s.id}>{s.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Add Item */}
              <div className="flex gap-2">
                <Select value={editItem.product_id} onValueChange={(v) => {
                  const product = products.find(p => p.id === v);
                  setEditItem({ ...editItem, product_id: v, unit_price: product?.cost_price.toString() || '' });
                }}>
                  <SelectTrigger className="flex-1" data-testid="edit-select-product">
                    <SelectValue placeholder="Select product" />
                  </SelectTrigger>
                  <SelectContent>
                    {products.map((p) => (
                      <SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Input
                  type="number"
                  value={editItem.unit_price}
                  onChange={(e) => setEditItem({ ...editItem, unit_price: e.target.value })}
                  className="w-28"
                  placeholder="Price"
                />
                <Input
                  type="number"
                  min="1"
                  value={editItem.quantity}
                  onChange={(e) => setEditItem({ ...editItem, quantity: e.target.value })}
                  className="w-20"
                  placeholder="Qty"
                />
                <Button type="button" onClick={handleAddEditItem} variant="outline">Add</Button>
              </div>

              {/* Items List */}
              {editFormData.items.length > 0 && (
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
                      {editFormData.items.map((item, index) => (
                        <TableRow key={index}>
                          <TableCell>{item.product_name}</TableCell>
                          <TableCell className="text-right">{formatCurrency(item.unit_price)}</TableCell>
                          <TableCell className="text-right">{item.quantity}</TableCell>
                          <TableCell className="text-right font-medium">{formatCurrency(item.total)}</TableCell>
                          <TableCell>
                            <Button variant="ghost" size="icon" onClick={() => handleRemoveEditItem(index)}>
                              <Trash2 className="w-4 h-4 text-red-500" />
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              )}

              <div className="space-y-2">
                <Label>Notes</Label>
                <Input
                  value={editFormData.notes}
                  onChange={(e) => setEditFormData({ ...editFormData, notes: e.target.value })}
                  placeholder="Optional notes"
                />
              </div>

              <div className="flex justify-end">
                <div className="text-right">
                  <p className="text-sm text-slate-500">Total</p>
                  <p className="text-2xl font-bold">{formatCurrency(calculateEditTotal())}</p>
                </div>
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setEditDialogOpen(false)}>Cancel</Button>
              <Button type="submit" disabled={submitting || !editFormData.supplier_id} className="bg-indigo-600 hover:bg-indigo-700" data-testid="submit-edit-po-btn">
                {submitting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                Update Order
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent data-testid="delete-po-dialog">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-red-600">
              <AlertTriangle className="w-5 h-5" />
              Delete Purchase Order
            </DialogTitle>
            <DialogDescription>
              Are you sure you want to delete order <strong>{selectedOrder?.order_number}</strong>?
              This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <div className="bg-red-50 p-3 rounded-lg text-sm text-red-800">
              <strong>Warning:</strong> This will permanently delete the purchase order.
              {selectedOrder?.paid_amount > 0 && (
                <p className="mt-2 font-medium">This order has payments recorded and cannot be deleted.</p>
              )}
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
            <Button 
              variant="destructive" 
              onClick={handleDeleteOrder} 
              disabled={submitting || (selectedOrder?.paid_amount > 0)}
              data-testid="confirm-delete-po-btn"
            >
              {submitting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
              Delete Order
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default PurchaseOrders;
