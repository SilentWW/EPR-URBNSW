import React, { useState, useEffect } from 'react';
import { rmProcurementAPI } from '../lib/api';
import api from '../lib/api';
import { useAuth } from '../context/AuthContext';
import { Card, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Textarea } from '../components/ui/textarea';
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
import { 
  Plus, MoreHorizontal, Eye, Loader2, ClipboardList, CreditCard, Trash2, 
  CheckCircle, AlertTriangle, FileInput, Pencil, Package
} from 'lucide-react';
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
  draft: 'bg-slate-100 text-slate-700',
  approved: 'bg-blue-100 text-blue-700',
  partially_received: 'bg-amber-100 text-amber-700',
  completed: 'bg-green-100 text-green-700',
  cancelled: 'bg-red-100 text-red-700',
};

const paymentColors = {
  unpaid: 'bg-red-100 text-red-700',
  partial: 'bg-amber-100 text-amber-700',
  paid: 'bg-green-100 text-green-700',
};

const priorityColors = {
  low: 'bg-slate-100 text-slate-600',
  normal: 'bg-blue-100 text-blue-600',
  high: 'bg-orange-100 text-orange-600',
  urgent: 'bg-red-100 text-red-600',
};

const PAYMENT_TERMS = [
  { value: 'immediate', label: 'Immediate' },
  { value: 'net_30', label: 'Net 30 Days' },
  { value: 'net_60', label: 'Net 60 Days' },
  { value: 'net_90', label: 'Net 90 Days' },
];

const PRIORITY_OPTIONS = [
  { value: 'low', label: 'Low' },
  { value: 'normal', label: 'Normal' },
  { value: 'high', label: 'High' },
  { value: 'urgent', label: 'Urgent' },
];

export const RMPurchaseOrders = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [orders, setOrders] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [rawMaterials, setRawMaterials] = useState([]);
  const [bankAccounts, setBankAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('all');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [paymentDialogOpen, setPaymentDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const canEditDelete = user?.role === 'admin' || user?.role === 'manager';

  const [formData, setFormData] = useState({
    supplier_id: '',
    items: [],
    payment_terms: 'net_30',
    priority: 'normal',
    expected_delivery_date: '',
    expiry_date: '',
    notes: '',
  });

  const [newItem, setNewItem] = useState({
    raw_material_id: '',
    quantity: 1,
    unit_price: '',
  });

  const [paymentData, setPaymentData] = useState({
    amount: '',
    bank_account_id: '',
    notes: '',
  });

  const fetchData = async () => {
    try {
      const params = {};
      if (statusFilter && statusFilter !== 'all') params.status = statusFilter;

      const [ordersRes, suppliersRes, materialsRes, bankRes] = await Promise.all([
        rmProcurementAPI.getPurchaseOrders(params),
        rmProcurementAPI.getSuppliers(),
        api.get('/manufacturing/raw-materials'),
        api.get('/bank-accounts'),
      ]);
      
      setOrders(ordersRes.data);
      setSuppliers(suppliersRes.data);
      setRawMaterials(materialsRes.data);
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

  const handleSupplierSelect = (supplierId) => {
    const supplier = suppliers.find(s => s.id === supplierId);
    setFormData({
      ...formData,
      supplier_id: supplierId,
      payment_terms: supplier?.default_payment_terms || 'net_30',
    });
  };

  const handleAddItem = () => {
    const material = rawMaterials.find(m => m.id === newItem.raw_material_id);
    if (!material) {
      toast.error('Please select a raw material');
      return;
    }

    const unitPrice = parseFloat(newItem.unit_price) || material.cost_price || 0;
    const quantity = parseFloat(newItem.quantity) || 1;
    const item = {
      raw_material_id: material.id,
      raw_material_name: material.name,
      raw_material_sku: material.sku,
      unit: material.unit,
      quantity,
      unit_price: unitPrice,
      line_total: quantity * unitPrice,
    };

    setFormData({
      ...formData,
      items: [...formData.items, item],
    });

    setNewItem({ raw_material_id: '', quantity: 1, unit_price: '' });
  };

  const handleRemoveItem = (index) => {
    setFormData({
      ...formData,
      items: formData.items.filter((_, i) => i !== index),
    });
  };

  const calculateTotal = () => {
    return formData.items.reduce((sum, item) => sum + item.line_total, 0);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (formData.items.length === 0) {
      toast.error('Please add at least one item');
      return;
    }

    setSubmitting(true);
    try {
      const payload = {
        supplier_id: formData.supplier_id,
        items: formData.items.map(item => ({
          raw_material_id: item.raw_material_id,
          quantity: item.quantity,
          unit_price: item.unit_price,
        })),
        payment_terms: formData.payment_terms,
        priority: formData.priority,
        expected_delivery_date: formData.expected_delivery_date || null,
        expiry_date: formData.expiry_date || null,
        notes: formData.notes || null,
      };

      await rmProcurementAPI.createPurchaseOrder(payload);
      toast.success('Purchase order created successfully');
      setDialogOpen(false);
      setFormData({
        supplier_id: '',
        items: [],
        payment_terms: 'net_30',
        priority: 'normal',
        expected_delivery_date: '',
        expiry_date: '',
        notes: '',
      });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create order');
    } finally {
      setSubmitting(false);
    }
  };

  const handleViewOrder = async (order) => {
    try {
      const response = await rmProcurementAPI.getPurchaseOrder(order.id);
      setSelectedOrder(response.data);
      setViewDialogOpen(true);
    } catch (error) {
      toast.error('Failed to load order details');
    }
  };

  const handleApproveOrder = async (order) => {
    try {
      await rmProcurementAPI.approvePurchaseOrder(order.id);
      toast.success('Purchase order approved');
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to approve order');
    }
  };

  const handleRecordPayment = async () => {
    setSubmitting(true);
    try {
      await rmProcurementAPI.recordPayment(selectedOrder.id, {
        amount: parseFloat(paymentData.amount),
        bank_account_id: paymentData.bank_account_id,
        notes: paymentData.notes || undefined,
      });
      toast.success('Payment recorded successfully');
      setPaymentDialogOpen(false);
      setPaymentData({ amount: '', bank_account_id: '', notes: '' });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to record payment');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteOrder = async () => {
    setSubmitting(true);
    try {
      await rmProcurementAPI.deletePurchaseOrder(selectedOrder.id);
      toast.success('Purchase order deleted');
      setDeleteDialogOpen(false);
      setSelectedOrder(null);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete order');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6" data-testid="rm-purchase-orders-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900" style={{ fontFamily: 'Outfit, sans-serif' }}>
            RM Purchase Orders
          </h2>
          <p className="text-slate-500 mt-1">{orders.length} orders</p>
        </div>
        <Button onClick={() => setDialogOpen(true)} className="gap-2 bg-indigo-600 hover:bg-indigo-700" data-testid="create-rm-po-btn">
          <Plus className="w-4 h-4" />
          New Purchase Order
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-48" data-testid="rm-po-status-filter">
              <SelectValue placeholder="All Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Status</SelectItem>
              <SelectItem value="draft">Draft</SelectItem>
              <SelectItem value="approved">Approved</SelectItem>
              <SelectItem value="partially_received">Partially Received</SelectItem>
              <SelectItem value="completed">Completed</SelectItem>
              <SelectItem value="cancelled">Cancelled</SelectItem>
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
              <p className="text-slate-500 mt-1">Create your first RM purchase order.</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="table-header">
                  <TableHead className="table-header-cell">PO #</TableHead>
                  <TableHead className="table-header-cell">Supplier</TableHead>
                  <TableHead className="table-header-cell">Date</TableHead>
                  <TableHead className="table-header-cell">Priority</TableHead>
                  <TableHead className="table-header-cell text-right">Total</TableHead>
                  <TableHead className="table-header-cell">Status</TableHead>
                  <TableHead className="table-header-cell">Payment</TableHead>
                  <TableHead className="table-header-cell w-12"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {orders.map((order) => (
                  <TableRow key={order.id} className="table-row" data-testid={`rm-po-row-${order.id}`}>
                    <TableCell className="table-cell font-medium">{order.po_number}</TableCell>
                    <TableCell className="table-cell">{order.supplier_name}</TableCell>
                    <TableCell className="table-cell text-slate-500">
                      {new Date(order.created_at).toLocaleDateString()}
                    </TableCell>
                    <TableCell className="table-cell">
                      <Badge className={priorityColors[order.priority]}>{order.priority}</Badge>
                    </TableCell>
                    <TableCell className="table-cell text-right font-medium">{formatCurrency(order.total)}</TableCell>
                    <TableCell className="table-cell">
                      <Badge className={statusColors[order.status]}>{order.status.replace('_', ' ')}</Badge>
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
                          {order.status === 'draft' && canEditDelete && (
                            <>
                              <DropdownMenuItem onClick={() => handleApproveOrder(order)}>
                                <CheckCircle className="w-4 h-4 mr-2" />
                                Approve
                              </DropdownMenuItem>
                              <DropdownMenuSeparator />
                              <DropdownMenuItem 
                                className="text-red-600"
                                onClick={() => {
                                  setSelectedOrder(order);
                                  setDeleteDialogOpen(true);
                                }}
                              >
                                <Trash2 className="w-4 h-4 mr-2" />
                                Delete
                              </DropdownMenuItem>
                            </>
                          )}
                          {(order.status === 'approved' || order.status === 'partially_received') && (
                            <DropdownMenuItem onClick={() => navigate(`/rm-grn?po_id=${order.id}`)}>
                              <FileInput className="w-4 h-4 mr-2" />
                              Receive Goods
                            </DropdownMenuItem>
                          )}
                          {order.payment_status !== 'paid' && order.status !== 'draft' && (
                            <DropdownMenuItem onClick={() => {
                              setSelectedOrder(order);
                              setPaymentData({ 
                                amount: (order.total - (order.paid_amount || 0)).toString(), 
                                bank_account_id: '', 
                                notes: '' 
                              });
                              setPaymentDialogOpen(true);
                            }}>
                              <CreditCard className="w-4 h-4 mr-2" />
                              Record Payment
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

      {/* Create PO Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-2xl" data-testid="create-rm-po-dialog">
          <DialogHeader>
            <DialogTitle style={{ fontFamily: 'Outfit, sans-serif' }}>Create RM Purchase Order</DialogTitle>
            <DialogDescription>Add items to create a new raw material purchase order</DialogDescription>
          </DialogHeader>
          <form onSubmit={handleSubmit}>
            <div className="space-y-4 py-4 max-h-[60vh] overflow-y-auto">
              {/* Supplier Selection */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Supplier *</Label>
                  <Select value={formData.supplier_id} onValueChange={handleSupplierSelect}>
                    <SelectTrigger data-testid="select-rm-supplier">
                      <SelectValue placeholder="Select supplier" />
                    </SelectTrigger>
                    <SelectContent>
                      {suppliers.map((s) => (
                        <SelectItem key={s.id} value={s.id}>{s.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Payment Terms</Label>
                  <Select value={formData.payment_terms} onValueChange={(v) => setFormData({ ...formData, payment_terms: v })}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {PAYMENT_TERMS.map((t) => (
                        <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label>Priority</Label>
                  <Select value={formData.priority} onValueChange={(v) => setFormData({ ...formData, priority: v })}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {PRIORITY_OPTIONS.map((p) => (
                        <SelectItem key={p.value} value={p.value}>{p.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Expected Delivery</Label>
                  <Input
                    type="date"
                    value={formData.expected_delivery_date}
                    onChange={(e) => setFormData({ ...formData, expected_delivery_date: e.target.value })}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Expiry Date</Label>
                  <Input
                    type="date"
                    value={formData.expiry_date}
                    onChange={(e) => setFormData({ ...formData, expiry_date: e.target.value })}
                  />
                </div>
              </div>

              {/* Add Item */}
              <div className="space-y-2 pt-4 border-t">
                <Label>Add Items</Label>
                <div className="flex gap-2">
                  <Select 
                    value={newItem.raw_material_id} 
                    onValueChange={(v) => {
                      const material = rawMaterials.find(m => m.id === v);
                      setNewItem({ 
                        ...newItem, 
                        raw_material_id: v, 
                        unit_price: material?.cost_price?.toString() || '' 
                      });
                    }}
                  >
                    <SelectTrigger className="flex-1" data-testid="select-rm-material">
                      <SelectValue placeholder="Select raw material" />
                    </SelectTrigger>
                    <SelectContent>
                      {rawMaterials.map((m) => (
                        <SelectItem key={m.id} value={m.id}>
                          {m.sku} - {m.name} ({m.unit})
                        </SelectItem>
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
                    min="0.01"
                    step="0.01"
                    value={newItem.quantity}
                    onChange={(e) => setNewItem({ ...newItem, quantity: e.target.value })}
                    className="w-20"
                    placeholder="Qty"
                  />
                  <Button type="button" onClick={handleAddItem} variant="outline">Add</Button>
                </div>
              </div>

              {/* Items List */}
              {formData.items.length > 0 && (
                <div className="border rounded-lg overflow-hidden">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Material</TableHead>
                        <TableHead className="text-right">Price</TableHead>
                        <TableHead className="text-right">Qty</TableHead>
                        <TableHead className="text-right">Total</TableHead>
                        <TableHead className="w-10"></TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {formData.items.map((item, index) => (
                        <TableRow key={index}>
                          <TableCell>
                            <div>{item.raw_material_name}</div>
                            <span className="text-xs text-slate-400">{item.raw_material_sku} ({item.unit})</span>
                          </TableCell>
                          <TableCell className="text-right">{formatCurrency(item.unit_price)}</TableCell>
                          <TableCell className="text-right">{item.quantity}</TableCell>
                          <TableCell className="text-right font-medium">{formatCurrency(item.line_total)}</TableCell>
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

              <div className="space-y-2">
                <Label>Notes</Label>
                <Textarea
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  placeholder="Additional notes..."
                  rows={2}
                />
              </div>

              <div className="flex justify-end pt-4 border-t">
                <div className="text-right">
                  <p className="text-sm text-slate-500">Total</p>
                  <p className="text-2xl font-bold">{formatCurrency(calculateTotal())}</p>
                </div>
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>Cancel</Button>
              <Button type="submit" disabled={submitting || !formData.supplier_id} className="bg-indigo-600 hover:bg-indigo-700" data-testid="submit-rm-po-btn">
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
              RM Purchase Order {selectedOrder?.po_number}
            </DialogTitle>
          </DialogHeader>
          {selectedOrder && (
            <div className="space-y-4 max-h-[60vh] overflow-y-auto">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-slate-500">Supplier</p>
                  <p className="font-medium">{selectedOrder.supplier_name}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-500">Date</p>
                  <p className="font-medium">{new Date(selectedOrder.created_at).toLocaleString()}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-500">Status</p>
                  <Badge className={statusColors[selectedOrder.status]}>{selectedOrder.status.replace('_', ' ')}</Badge>
                </div>
                <div>
                  <p className="text-sm text-slate-500">Payment</p>
                  <Badge className={paymentColors[selectedOrder.payment_status]}>{selectedOrder.payment_status}</Badge>
                </div>
                <div>
                  <p className="text-sm text-slate-500">Payment Terms</p>
                  <p className="font-medium">{PAYMENT_TERMS.find(t => t.value === selectedOrder.payment_terms)?.label}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-500">Priority</p>
                  <Badge className={priorityColors[selectedOrder.priority]}>{selectedOrder.priority}</Badge>
                </div>
              </div>

              <div className="border rounded-lg overflow-hidden">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Material</TableHead>
                      <TableHead className="text-right">Price</TableHead>
                      <TableHead className="text-right">Ordered</TableHead>
                      <TableHead className="text-right">Received</TableHead>
                      <TableHead className="text-right">Total</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {selectedOrder.items.map((item, index) => (
                      <TableRow key={index}>
                        <TableCell>
                          <div>{item.raw_material_name}</div>
                          <span className="text-xs text-slate-400">{item.raw_material_sku}</span>
                        </TableCell>
                        <TableCell className="text-right">{formatCurrency(item.unit_price)}</TableCell>
                        <TableCell className="text-right">{item.quantity} {item.unit}</TableCell>
                        <TableCell className="text-right">
                          <span className={item.received_quantity >= item.quantity ? 'text-green-600' : 'text-amber-600'}>
                            {item.received_quantity || 0}
                          </span>
                        </TableCell>
                        <TableCell className="text-right font-medium">{formatCurrency(item.line_total)}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>

              <div className="flex justify-end">
                <div className="text-right space-y-1">
                  <p className="text-lg font-bold">Total: {formatCurrency(selectedOrder.total)}</p>
                  <p className="text-sm text-emerald-600">Paid: {formatCurrency(selectedOrder.paid_amount || 0)}</p>
                  <p className="text-sm text-amber-600">Balance: {formatCurrency(selectedOrder.total - (selectedOrder.paid_amount || 0))}</p>
                </div>
              </div>

              {selectedOrder.notes && (
                <div className="p-3 bg-slate-50 rounded-lg">
                  <p className="text-sm text-slate-500">Notes</p>
                  <p className="text-sm">{selectedOrder.notes}</p>
                </div>
              )}
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
              Balance due: {formatCurrency((selectedOrder?.total || 0) - (selectedOrder?.paid_amount || 0))}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Amount (LKR) *</Label>
              <Input
                type="number"
                value={paymentData.amount}
                onChange={(e) => setPaymentData({ ...paymentData, amount: e.target.value })}
                data-testid="rm-payment-amount"
              />
            </div>
            <div className="space-y-2">
              <Label>Pay From Account *</Label>
              <Select 
                value={paymentData.bank_account_id} 
                onValueChange={(v) => setPaymentData({ ...paymentData, bank_account_id: v })}
              >
                <SelectTrigger data-testid="rm-payment-account">
                  <SelectValue placeholder="Select account" />
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
            <div className="space-y-2">
              <Label>Notes</Label>
              <Textarea
                value={paymentData.notes}
                onChange={(e) => setPaymentData({ ...paymentData, notes: e.target.value })}
                placeholder="Payment reference..."
                rows={2}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setPaymentDialogOpen(false)}>Cancel</Button>
            <Button 
              onClick={handleRecordPayment} 
              disabled={submitting || !paymentData.amount || !paymentData.bank_account_id} 
              className="bg-indigo-600 hover:bg-indigo-700"
              data-testid="submit-rm-payment"
            >
              {submitting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
              Record Payment
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
              Delete Purchase Order
            </DialogTitle>
            <DialogDescription>
              Are you sure you want to delete order <strong>{selectedOrder?.po_number}</strong>?
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
            <Button variant="destructive" onClick={handleDeleteOrder} disabled={submitting}>
              {submitting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default RMPurchaseOrders;
