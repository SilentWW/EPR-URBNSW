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
    variation_id: '',
    quantity: 1,
    unit_price: '',
  });

  // State for variations when selecting a variable product
  const [productVariations, setProductVariations] = useState([]);
  const [loadingVariations, setLoadingVariations] = useState(false);

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

      const [ordersRes, suppliersRes, productsRes, bankAccountsRes, chargeTypesRes, chartAccountsRes] = await Promise.all([
        purchaseOrdersAPI.getAll(params),
        suppliersAPI.getAll(),
        productsAPI.getAll(),
        api.get('/bank-accounts'),
        api.get('/grn/charge-types').catch(() => ({ data: [] })),
        api.get('/finance/chart-of-accounts').catch(() => ({ data: [] })),
      ]);
      setOrders(ordersRes.data);
      setSuppliers(suppliersRes.data);
      setProducts(productsRes.data);
      
      // Combine bank accounts with cash/bank chart accounts
      const bankAccts = bankAccountsRes.data.map(a => ({
        id: a.id,
        name: a.account_name,
        type: a.account_type,
        balance: a.current_balance,
        source: 'bank_account'
      }));
      
      // Add cash/bank accounts from Chart of Accounts that aren't already linked
      const cashBankCodes = ['1100', '1101', '1110', '1200', '1210'];
      const chartCashBank = (chartAccountsRes.data || [])
        .filter(a => cashBankCodes.includes(a.code))
        .filter(a => !bankAccts.some(b => b.name === a.name))
        .map(a => ({
          id: a.id,
          name: a.name,
          type: a.code.startsWith('11') ? 'cash' : 'bank',
          balance: a.balance || 0,
          source: 'chart_account',
          code: a.code
        }));
      
      setBankAccounts([...bankAccts, ...chartCashBank]);
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

  // Fetch variations when a variable product is selected
  const fetchProductVariations = async (productId) => {
    setLoadingVariations(true);
    try {
      const response = await api.get(`/variations/product/${productId}`);
      setProductVariations(response.data.variations || []);
    } catch (error) {
      console.error('Failed to fetch variations:', error);
      setProductVariations([]);
    } finally {
      setLoadingVariations(false);
    }
  };

  const handleProductSelect = (productId) => {
    const product = products.find(p => p.id === productId);
    if (product?.product_type === 'variable') {
      // Fetch variations for this product
      fetchProductVariations(productId);
      setNewItem({ 
        ...newItem, 
        product_id: productId, 
        variation_id: '',
        unit_price: '' 
      });
    } else {
      setProductVariations([]);
      setNewItem({ 
        ...newItem, 
        product_id: productId, 
        variation_id: '',
        unit_price: product?.cost_price?.toString() || '' 
      });
    }
  };

  const handleVariationSelect = (variationId) => {
    const variation = productVariations.find(v => v.id === variationId);
    setNewItem({ 
      ...newItem, 
      variation_id: variationId,
      unit_price: variation?.cost_price?.toString() || '' 
    });
  };

  const handleAddItem = () => {
    const product = products.find((p) => p.id === newItem.product_id);
    if (!product) return;

    // For variable products, variation must be selected
    if (product.product_type === 'variable' && !newItem.variation_id) {
      toast.error('Please select a variation for this variable product');
      return;
    }

    let itemName = product.name;
    let itemSku = product.sku;
    let costPrice = product.cost_price;

    // If variation selected, use variation details
    if (newItem.variation_id) {
      const variation = productVariations.find(v => v.id === newItem.variation_id);
      if (variation) {
        itemName = variation.variation_name;
        itemSku = variation.sku;
        costPrice = variation.cost_price;
      }
    }

    const unitPrice = parseFloat(newItem.unit_price) || costPrice;
    const item = {
      product_id: product.id,
      variation_id: newItem.variation_id || null,
      product_name: itemName,
      sku: itemSku,
      quantity: parseInt(newItem.quantity),
      unit_price: unitPrice,
      total: unitPrice * parseInt(newItem.quantity),
    };

    setFormData({
      ...formData,
      items: [...formData.items, item],
    });

    setNewItem({ product_id: '', variation_id: '', quantity: 1, unit_price: '' });
    setProductVariations([]);
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
                              <DropdownMenuItem onClick={() => handleOpenChargesDialog(order)}>
                                <TruckIcon className="w-4 h-4 mr-2" />
                                Add Charges
                              </DropdownMenuItem>
                            </>
                          )}
                          {order.status === 'received' && (
                            <DropdownMenuItem onClick={() => handleOpenChargesDialog(order)}>
                              <TruckIcon className="w-4 h-4 mr-2" />
                              Add Charges
                            </DropdownMenuItem>
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
              <div className="space-y-2">
                <div className="flex gap-2">
                  <Select value={newItem.product_id} onValueChange={handleProductSelect}>
                    <SelectTrigger className="flex-1" data-testid="select-po-product">
                      <SelectValue placeholder="Select product" />
                    </SelectTrigger>
                    <SelectContent>
                      {products.map((p) => (
                        <SelectItem key={p.id} value={p.id}>
                          {p.name} {p.product_type === 'variable' && <span className="text-purple-500 ml-1">(Variable)</span>}
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
                    min="1"
                    value={newItem.quantity}
                    onChange={(e) => setNewItem({ ...newItem, quantity: e.target.value })}
                    className="w-20"
                    placeholder="Qty"
                  />
                  <Button type="button" onClick={handleAddItem} variant="outline">Add</Button>
                </div>
                
                {/* Variation Selector (for variable products) */}
                {newItem.product_id && products.find(p => p.id === newItem.product_id)?.product_type === 'variable' && (
                  <div className="pl-2 border-l-2 border-purple-200">
                    {loadingVariations ? (
                      <div className="flex items-center gap-2 text-sm text-slate-500 py-2">
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Loading variations...
                      </div>
                    ) : productVariations.length > 0 ? (
                      <Select value={newItem.variation_id} onValueChange={handleVariationSelect}>
                        <SelectTrigger className="w-full" data-testid="select-po-variation">
                          <SelectValue placeholder="Select variation (Color, Size...)" />
                        </SelectTrigger>
                        <SelectContent>
                          {productVariations.map((v) => (
                            <SelectItem key={v.id} value={v.id}>
                              <div className="flex items-center gap-2">
                                <span>{v.variation_name}</span>
                                <span className="text-xs text-slate-400">({v.sku})</span>
                                <span className="text-xs text-green-600">Stock: {v.stock_quantity}</span>
                              </div>
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    ) : (
                      <p className="text-sm text-amber-600 py-2">
                        No variations found. Sync variations from WooCommerce first.
                      </p>
                    )}
                  </div>
                )}
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
                          <TableCell>
                            <div>
                              {item.product_name}
                              {item.variation_id && (
                                <span className="text-xs text-purple-500 ml-1">(Variation)</span>
                              )}
                            </div>
                            <span className="text-xs text-slate-400">{item.sku}</span>
                          </TableCell>
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
                      {acc.name} ({acc.type === 'bank' ? 'Bank' : 'Cash'}) - {formatCurrency(acc.balance)}
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

      {/* Additional Charges Dialog */}
      <Dialog open={chargesDialogOpen} onOpenChange={setChargesDialogOpen}>
        <DialogContent className="max-w-2xl" data-testid="charges-dialog">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2" style={{ fontFamily: 'Outfit, sans-serif' }}>
              <TruckIcon className="w-5 h-5" />
              Additional Charges
            </DialogTitle>
            <DialogDescription>
              Add shipping, customs, handling fees or discounts for {selectedOrder?.order_number}
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            {/* Add new charge form */}
            <div className="grid grid-cols-12 gap-2 items-end">
              <div className="col-span-3">
                <Label className="text-xs">Charge Type</Label>
                <Select 
                  value={newCharge.charge_type} 
                  onValueChange={(v) => setNewCharge({ ...newCharge, charge_type: v })}
                >
                  <SelectTrigger data-testid="charge-type-select">
                    <SelectValue placeholder="Select type" />
                  </SelectTrigger>
                  <SelectContent>
                    {chargeTypes.map((ct) => (
                      <SelectItem key={ct.id} value={ct.id}>
                        {ct.name} {ct.type === 'income' && '(-)'}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="col-span-3">
                <Label className="text-xs">Description</Label>
                <Input
                  value={newCharge.description}
                  onChange={(e) => setNewCharge({ ...newCharge, description: e.target.value })}
                  placeholder="Optional"
                />
              </div>
              <div className="col-span-2">
                <Label className="text-xs">Amount</Label>
                <Input
                  type="number"
                  value={newCharge.amount}
                  onChange={(e) => setNewCharge({ ...newCharge, amount: e.target.value })}
                  placeholder="0.00"
                />
              </div>
              <div className="col-span-3">
                <div className="flex items-center gap-2 mb-1">
                  <Switch
                    id="pay-immediately"
                    checked={newCharge.pay_immediately}
                    onCheckedChange={(v) => setNewCharge({ ...newCharge, pay_immediately: v })}
                  />
                  <Label htmlFor="pay-immediately" className="text-xs">Pay Now</Label>
                </div>
                {newCharge.pay_immediately && (
                  <Select 
                    value={newCharge.bank_account_id} 
                    onValueChange={(v) => setNewCharge({ ...newCharge, bank_account_id: v })}
                  >
                    <SelectTrigger className="h-8">
                      <SelectValue placeholder="Account" />
                    </SelectTrigger>
                    <SelectContent>
                      {bankAccounts.map((acc) => (
                        <SelectItem key={acc.id} value={acc.id}>
                          {acc.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
              </div>
              <div className="col-span-1">
                <Button type="button" onClick={handleAddCharge} size="sm" className="w-full">
                  <Plus className="w-4 h-4" />
                </Button>
              </div>
            </div>

            {/* Charges list */}
            {additionalCharges.length > 0 && (
              <div className="border rounded-lg overflow-hidden">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Type</TableHead>
                      <TableHead>Description</TableHead>
                      <TableHead className="text-right">Amount</TableHead>
                      <TableHead>Payment</TableHead>
                      <TableHead className="w-10"></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {additionalCharges.map((charge, index) => {
                      const chargeType = chargeTypes.find(ct => ct.id === charge.charge_type);
                      const isDiscount = charge.charge_type === 'discount';
                      const isExisting = index < (selectedOrder?.additional_charges?.length || 0);
                      return (
                        <TableRow key={index} className={isExisting ? 'opacity-60' : ''}>
                          <TableCell>
                            <Badge variant={isDiscount ? 'success' : 'default'} className={isDiscount ? 'bg-green-100 text-green-800' : ''}>
                              {chargeType?.name || charge.charge_type_name || charge.charge_type}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-slate-600">{charge.description || '-'}</TableCell>
                          <TableCell className={`text-right font-medium ${isDiscount ? 'text-green-600' : ''}`}>
                            {isDiscount ? '-' : ''}{formatCurrency(charge.amount)}
                          </TableCell>
                          <TableCell>
                            <span className="text-xs text-slate-500">
                              {charge.pay_immediately ? 'Paid' : 'To Payable'}
                            </span>
                          </TableCell>
                          <TableCell>
                            {!isExisting && (
                              <Button variant="ghost" size="icon" onClick={() => handleRemoveCharge(index)}>
                                <Trash2 className="w-4 h-4 text-red-500" />
                              </Button>
                            )}
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </div>
            )}

            {/* Summary */}
            <div className="bg-slate-50 p-4 rounded-lg">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-slate-500">PO Subtotal</p>
                  <p className="text-lg font-semibold">{formatCurrency(selectedOrder?.subtotal || 0)}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-500">Additional Expenses</p>
                  <p className="text-lg font-semibold">{formatCurrency(calculateChargesTotal().expenses)}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-500">Discounts Received</p>
                  <p className="text-lg font-semibold text-green-600">-{formatCurrency(calculateChargesTotal().discounts)}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-500">New Total</p>
                  <p className="text-2xl font-bold text-indigo-600">
                    {formatCurrency((selectedOrder?.subtotal || 0) + calculateChargesTotal().net)}
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-amber-50 p-3 rounded-lg text-sm text-amber-800">
              <strong>Journal Entries Created:</strong>
              <ul className="mt-1 list-disc list-inside">
                <li>Expenses → Operating Expenses (Debit), {newCharge.pay_immediately ? 'Bank (Credit)' : 'Accounts Payable (Credit)'}</li>
                <li>Discounts → Accounts Payable (Debit), Other Income (Credit)</li>
              </ul>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setChargesDialogOpen(false)}>Cancel</Button>
            <Button 
              onClick={handleSubmitCharges} 
              disabled={submitting || additionalCharges.length === (selectedOrder?.additional_charges?.length || 0)}
              className="bg-indigo-600 hover:bg-indigo-700"
              data-testid="submit-charges-btn"
            >
              {submitting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
              Save Charges
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default PurchaseOrders;
