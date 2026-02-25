import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import api from '../lib/api';
import { useAuth } from '../context/AuthContext';
import { toast } from 'sonner';
import {
  Plus,
  Package,
  Truck,
  FileText,
  RefreshCw,
  ChevronDown,
  ChevronRight,
  Trash2,
  CheckCircle,
  XCircle,
  Clock,
  Search,
  Download,
  ClipboardList,
  TruckIcon,
  Loader2,
  Eye,
  RotateCcw,
  AlertTriangle,
  MoreHorizontal
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import { Badge } from '../components/ui/badge';
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
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger
} from '../components/ui/dropdown-menu';
import { Switch } from '../components/ui/switch';
import { Label } from '../components/ui/label';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow
} from '../components/ui/table';
import { Checkbox } from '../components/ui/checkbox';

export default function GRN() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [grns, setGrns] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [products, setProducts] = useState([]);
  const [purchaseOrders, setPurchaseOrders] = useState([]);
  const [allPurchaseOrders, setAllPurchaseOrders] = useState([]); // All POs for charges lookup
  const [wooCategories, setWooCategories] = useState([]);
  const [wooTags, setWooTags] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [expandedGrn, setExpandedGrn] = useState(null);
  const [nextSku, setNextSku] = useState('');
  const [fromPO, setFromPO] = useState(null); // Track if GRN is being created from a PO
  
  // Check if user can return (admin or manager)
  const canReturn = user?.role === 'admin' || user?.role === 'manager';
  
  // View dialog state
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [selectedGrn, setSelectedGrn] = useState(null);
  
  // Return dialog state
  const [returnDialogOpen, setReturnDialogOpen] = useState(false);
  const [returnType, setReturnType] = useState('full'); // 'full' or 'partial'
  const [returnReason, setReturnReason] = useState('supplier'); // 'supplier' or 'damaged'
  const [returnSettlement, setReturnSettlement] = useState('refund'); // 'refund' or 'credit'
  const [refundAccountId, setRefundAccountId] = useState('');
  const [returnNotes, setReturnNotes] = useState('');
  const [returnItems, setReturnItems] = useState([]); // For partial returns
  const [linkedPODetails, setLinkedPODetails] = useState(null); // PO payment status
  
  // Additional charges state
  const [chargesDialogOpen, setChargesDialogOpen] = useState(false);
  const [chargeTypes, setChargeTypes] = useState([]);
  const [bankAccounts, setBankAccounts] = useState([]);
  const [selectedPO, setSelectedPO] = useState(null);
  const [additionalCharges, setAdditionalCharges] = useState([]);
  const [submitting, setSubmitting] = useState(false);
  const [newCharge, setNewCharge] = useState({
    charge_type: '',
    description: '',
    amount: '',
    pay_immediately: false,
    bank_account_id: ''
  });
  
  const [formData, setFormData] = useState({
    supplier_id: '',
    reference_number: '',
    received_date: new Date().toISOString().split('T')[0],
    notes: '',
    sync_to_woo: true,
    items: [],
    po_id: null
  });

  const emptyItem = {
    product_id: '',
    product_name: '',
    sku: '',
    description: '',
    short_description: '',
    category: '',
    quantity: 1,
    cost_price: 0,
    regular_price: 0,
    sale_price: '',
    weight: '',
    visibility: 'public',
    tags: '',
    attributes: []
  };

  useEffect(() => {
    fetchData();
  }, []);

  // Check if coming from a PO
  useEffect(() => {
    const poId = searchParams.get('po_id');
    if (poId && purchaseOrders.length > 0) {
      const po = purchaseOrders.find(p => p.id === poId);
      if (po) {
        createGRNFromPO(po);
        // Clear the URL parameter
        navigate('/grn', { replace: true });
      }
    }
  }, [searchParams, purchaseOrders, navigate]);

  const createGRNFromPO = (po) => {
    setFromPO(po);
    
    // Map PO items to GRN items
    const grnItems = po.items.map(item => ({
      product_id: item.product_id,
      product_name: item.product_name,
      sku: item.sku || '',
      description: '',
      short_description: '',
      category: '',
      quantity: item.quantity,
      cost_price: item.unit_price,
      regular_price: item.unit_price * 1.3, // Default 30% markup
      sale_price: '',
      weight: '',
      visibility: 'public',
      tags: '',
      attributes: []
    }));

    setFormData({
      supplier_id: po.supplier_id,
      reference_number: po.order_number,
      received_date: new Date().toISOString().split('T')[0],
      notes: `Created from Purchase Order ${po.order_number}`,
      sync_to_woo: true,
      items: grnItems,
      po_id: po.id
    });
    
    setIsModalOpen(true);
  };

  const fetchData = async () => {
    try {
      setLoading(true);
      const [grnsRes, suppliersRes, productsRes, skuRes, poRes, catRes, tagsRes, chargeTypesRes, bankAccountsRes, chartAccountsRes] = await Promise.all([
        api.get('/grn'),
        api.get('/suppliers'),
        api.get('/products'),
        api.get('/grn/next-sku'),
        api.get('/purchase-orders'),
        api.get('/woocommerce/categories').catch(() => ({ data: [] })),
        api.get('/woocommerce/tags').catch(() => ({ data: [] })),
        api.get('/grn/charge-types').catch(() => ({ data: [] })),
        api.get('/bank-accounts').catch(() => ({ data: [] })),
        api.get('/finance/chart-of-accounts').catch(() => ({ data: [] }))
      ]);
      setGrns(grnsRes.data);
      setSuppliers(suppliersRes.data);
      setProducts(productsRes.data);
      setNextSku(skuRes.data.next_sku);
      setAllPurchaseOrders(poRes.data); // Store all POs
      setPurchaseOrders(poRes.data.filter(po => po.status === 'pending')); // Only pending POs for GRN creation
      setWooCategories(catRes.data || []);
      setWooTags(tagsRes.data || []);
      setChargeTypes(chargeTypesRes.data || []);
      
      // Combine bank accounts with cash/bank chart accounts
      const bankAccts = (bankAccountsRes.data || []).map(a => ({
        id: a.id,
        name: a.account_name,
        type: a.account_type,
        balance: a.current_balance,
        source: 'bank_account'
      }));
      
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
    } catch (error) {
      toast.error('Failed to fetch data');
    } finally {
      setLoading(false);
    }
  };

  const handleAddItem = () => {
    setFormData({
      ...formData,
      items: [...formData.items, { ...emptyItem, sku: nextSku }]
    });
    // Increment next SKU preview
    const num = parseInt(nextSku.replace('URBN', '')) + formData.items.length + 1;
    setNextSku(`URBN${num.toString().padStart(4, '0')}`);
  };

  const handleRemoveItem = (index) => {
    setFormData({
      ...formData,
      items: formData.items.filter((_, i) => i !== index)
    });
  };

  const handleItemChange = (index, field, value) => {
    const newItems = [...formData.items];
    newItems[index] = { ...newItems[index], [field]: value };
    
    // If selecting existing product, fill in details
    if (field === 'product_id' && value) {
      const product = products.find(p => p.id === value);
      if (product) {
        newItems[index] = {
          ...newItems[index],
          product_name: product.name,
          sku: product.sku,
          description: product.description || '',
          short_description: product.short_description || '',
          category: product.category || '',
          cost_price: product.cost_price || 0,
          regular_price: product.regular_price || product.selling_price || 0,
          sale_price: product.sale_price || '',
          weight: product.weight || '',
          visibility: product.visibility || 'public',
          tags: product.tags || ''
        };
      }
    }
    
    setFormData({ ...formData, items: newItems });
  };

  const suggestTags = async (idx) => {
    const item = formData.items[idx];
    if (!item.product_name) {
      toast.error('Please enter a product name first');
      return;
    }
    
    try {
      const response = await api.get('/woocommerce/suggest-tags', {
        params: {
          product_name: item.product_name,
          category: item.category
        }
      });
      
      const newItems = [...formData.items];
      newItems[idx] = {
        ...newItems[idx],
        tags: response.data.tags_string
      };
      setFormData({ ...formData, items: newItems });
      toast.success('SEO tags suggested!');
    } catch (error) {
      toast.error('Failed to suggest tags');
    }
  };

  const calculateTotals = () => {
    return formData.items.reduce((sum, item) => sum + (item.quantity * item.cost_price), 0);
  };

  // Additional charges handlers
  const handleOpenChargesDialog = (grn) => {
    // Find the linked PO
    const linkedPO = allPurchaseOrders.find(po => po.id === grn.po_id);
    if (!linkedPO) {
      toast.error('No linked Purchase Order found for this GRN');
      return;
    }
    setSelectedPO(linkedPO);
    setAdditionalCharges(linkedPO.additional_charges || []);
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

    const existingChargeCount = (selectedPO.additional_charges || []).length;
    const newCharges = additionalCharges.slice(existingChargeCount);
    
    if (newCharges.length === 0) {
      toast.info('No new charges to add');
      setChargesDialogOpen(false);
      return;
    }

    setSubmitting(true);
    try {
      await api.post(`/purchase-orders/${selectedPO.id}/additional-charges`, {
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

  // View GRN handler
  const handleViewGrn = (grn) => {
    setSelectedGrn(grn);
    setViewDialogOpen(true);
  };

  // Return GRN handlers
  const handleOpenReturnDialog = (grn) => {
    if (grn.status === 'returned') {
      toast.error('This GRN has already been returned');
      return;
    }
    setSelectedGrn(grn);
    setReturnType('full');
    setReturnReason('supplier');
    setReturnSettlement('refund');
    setRefundAccountId('');
    setReturnNotes('');
    
    // Get linked PO details for payment status
    if (grn.po_id) {
      const linkedPO = allPurchaseOrders.find(po => po.id === grn.po_id);
      setLinkedPODetails(linkedPO);
    } else {
      setLinkedPODetails(null);
    }
    
    // Initialize return items with all items selected for full return
    setReturnItems(grn.items.map(item => ({
      ...item,
      selected: true,
      return_quantity: item.quantity
    })));
    setReturnDialogOpen(true);
  };

  const handleReturnItemChange = (index, field, value) => {
    const updated = [...returnItems];
    updated[index][field] = value;
    // If quantity changed, ensure it doesn't exceed original
    if (field === 'return_quantity') {
      const maxQty = selectedGrn.items[index].quantity;
      updated[index].return_quantity = Math.min(Math.max(0, parseInt(value) || 0), maxQty);
    }
    setReturnItems(updated);
  };

  const handleSubmitReturn = async () => {
    // Validate
    const itemsToReturn = returnType === 'full' 
      ? selectedGrn.items.map(item => ({ ...item, return_quantity: item.quantity }))
      : returnItems.filter(item => item.selected && item.return_quantity > 0);
    
    if (itemsToReturn.length === 0) {
      toast.error('Please select at least one item to return');
      return;
    }
    
    // Validate refund account if returning to supplier with refund
    if (returnReason === 'supplier' && returnSettlement === 'refund' && !refundAccountId) {
      toast.error('Please select an account to receive the refund');
      return;
    }

    setSubmitting(true);
    try {
      await api.post(`/grn/${selectedGrn.id}/return`, {
        return_type: returnType,
        return_reason: returnReason,
        settlement_type: returnReason === 'supplier' ? returnSettlement : null,
        refund_account_id: returnSettlement === 'refund' ? refundAccountId : null,
        notes: returnNotes,
        items: itemsToReturn.map(item => ({
          product_id: item.product_id,
          product_name: item.product_name,
          sku: item.sku,
          quantity: item.return_quantity || item.quantity,
          cost_price: item.cost_price
        }))
      });
      toast.success('GRN return processed successfully');
      setReturnDialogOpen(false);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to process return');
    } finally {
      setSubmitting(false);
    }
  };

  const calculateReturnTotal = () => {
    if (returnType === 'full') {
      return selectedGrn?.items.reduce((sum, item) => sum + (item.quantity * item.cost_price), 0) || 0;
    }
    return returnItems
      .filter(item => item.selected && item.return_quantity > 0)
      .reduce((sum, item) => sum + (item.return_quantity * item.cost_price), 0);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.supplier_id) {
      toast.error('Please select a supplier');
      return;
    }
    
    if (formData.items.length === 0) {
      toast.error('Please add at least one item');
      return;
    }
    
    // Validate items
    for (let i = 0; i < formData.items.length; i++) {
      const item = formData.items[i];
      if (!item.product_name) {
        toast.error(`Item ${i + 1}: Product name is required`);
        return;
      }
      if (item.quantity <= 0) {
        toast.error(`Item ${i + 1}: Quantity must be greater than 0`);
        return;
      }
      if (item.cost_price < 0 || item.regular_price < 0) {
        toast.error(`Item ${i + 1}: Prices cannot be negative`);
        return;
      }
    }
    
    try {
      const response = await api.post('/grn', {
        ...formData,
        items: formData.items.map(item => ({
          ...item,
          sale_price: item.sale_price ? parseFloat(item.sale_price) : null,
          weight: item.weight ? parseFloat(item.weight) : null,
          product_id: item.product_id || null
        }))
      });
      
      toast.success(`GRN ${response.data.grn_number} created successfully`);
      setIsModalOpen(false);
      resetForm();
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create GRN');
    }
  };

  const resetForm = () => {
    setFormData({
      supplier_id: '',
      reference_number: '',
      received_date: new Date().toISOString().split('T')[0],
      notes: '',
      sync_to_woo: true,
      items: [],
      po_id: null
    });
    setFromPO(null);
  };

  const handleResync = async (grnId) => {
    try {
      await api.post(`/grn/${grnId}/resync`);
      toast.success('Re-sync initiated');
      fetchData();
    } catch (error) {
      toast.error('Failed to re-sync');
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-LK', {
      style: 'currency',
      currency: 'LKR',
      minimumFractionDigits: 2
    }).format(amount || 0);
  };

  const getSyncStatusBadge = (status) => {
    switch (status) {
      case 'synced':
        return <Badge className="bg-green-100 text-green-700"><CheckCircle className="w-3 h-3 mr-1" />Synced</Badge>;
      case 'pending':
        return <Badge className="bg-yellow-100 text-yellow-700"><Clock className="w-3 h-3 mr-1" />Pending</Badge>;
      case 'failed':
        return <Badge className="bg-red-100 text-red-700"><XCircle className="w-3 h-3 mr-1" />Failed</Badge>;
      case 'partial':
        return <Badge className="bg-orange-100 text-orange-700">Partial</Badge>;
      default:
        return <Badge variant="secondary">Not Synced</Badge>;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-slate-900"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="grn-page">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Goods Received Notes</h1>
          <p className="text-slate-500 mt-1">Manage inventory receipts and WooCommerce sync</p>
        </div>
        <div className="flex gap-2">
          {purchaseOrders.length > 0 && (
            <Select
              onValueChange={(poId) => {
                const po = purchaseOrders.find(p => p.id === poId);
                if (po) createGRNFromPO(po);
              }}
            >
              <SelectTrigger className="w-48" data-testid="create-from-po-select">
                <div className="flex items-center gap-2">
                  <ClipboardList className="w-4 h-4" />
                  <span>Create from PO</span>
                </div>
              </SelectTrigger>
              <SelectContent>
                {purchaseOrders.map(po => (
                  <SelectItem key={po.id} value={po.id}>
                    {po.order_number} - {po.supplier_name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
          <Button onClick={() => { resetForm(); handleAddItem(); setIsModalOpen(true); }} data-testid="create-grn-btn">
            <Plus className="w-4 h-4 mr-2" />
            New GRN
          </Button>
        </div>
      </div>

      {/* GRN List */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        {grns.length === 0 ? (
          <div className="p-8 text-center text-slate-500">
            <Package className="w-12 h-12 mx-auto mb-4 text-slate-300" />
            <p>No GRNs found</p>
            <p className="text-sm mt-1">Create your first GRN to receive goods</p>
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {grns.map((grn) => (
              <div key={grn.id} className="hover:bg-slate-50" data-testid={`grn-${grn.grn_number}`}>
                <div className="p-4 flex items-center justify-between">
                  <button
                    onClick={() => setExpandedGrn(expandedGrn === grn.id ? null : grn.id)}
                    className="flex items-center gap-4 text-left flex-1"
                  >
                    <div className="flex items-center gap-2">
                      {expandedGrn === grn.id ? (
                        <ChevronDown className="w-4 h-4 text-slate-400" />
                      ) : (
                        <ChevronRight className="w-4 h-4 text-slate-400" />
                      )}
                      <Truck className="w-5 h-5 text-slate-400" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-semibold">{grn.grn_number}</span>
                        {getSyncStatusBadge(grn.woo_sync_status)}
                        {grn.status === 'returned' && (
                          <Badge variant="destructive" className="bg-red-100 text-red-800">Returned</Badge>
                        )}
                        {grn.status === 'partial_return' && (
                          <Badge variant="warning" className="bg-amber-100 text-amber-800">Partial Return</Badge>
                        )}
                      </div>
                      <p className="text-sm text-slate-600">{grn.supplier_name}</p>
                    </div>
                  </button>
                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <p className="text-sm text-slate-500">{grn.received_date}</p>
                      <p className="font-semibold">{formatCurrency(grn.total_cost)}</p>
                      <p className="text-xs text-slate-400">{grn.items.length} items</p>
                    </div>
                    {/* Actions dropdown */}
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon" data-testid={`grn-actions-${grn.id}`}>
                          <MoreHorizontal className="w-4 h-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={() => handleViewGrn(grn)}>
                          <Eye className="w-4 h-4 mr-2" />
                          View Details
                        </DropdownMenuItem>
                        {canReturn && grn.status !== 'returned' && (
                          <>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem 
                              onClick={() => handleOpenReturnDialog(grn)}
                              className="text-red-600"
                            >
                              <RotateCcw className="w-4 h-4 mr-2" />
                              Return GRN
                            </DropdownMenuItem>
                          </>
                        )}
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </div>
                
                {expandedGrn === grn.id && (
                  <div className="px-4 pb-4 border-t border-slate-100">
                    <table className="w-full text-sm mt-4">
                      <thead className="bg-slate-100">
                        <tr>
                          <th className="text-left p-2">SKU</th>
                          <th className="text-left p-2">Product</th>
                          <th className="text-right p-2">Qty</th>
                          <th className="text-right p-2">Cost</th>
                          <th className="text-right p-2">Regular Price</th>
                          <th className="text-right p-2">Sale Price</th>
                          <th className="text-right p-2">Line Total</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {grn.items.map((item, idx) => (
                          <tr key={idx}>
                            <td className="p-2 font-mono text-xs">{item.sku}</td>
                            <td className="p-2">{item.product_name}</td>
                            <td className="p-2 text-right">{item.quantity}</td>
                            <td className="p-2 text-right">{formatCurrency(item.cost_price)}</td>
                            <td className="p-2 text-right">{formatCurrency(item.regular_price)}</td>
                            <td className="p-2 text-right">{item.sale_price ? formatCurrency(item.sale_price) : '-'}</td>
                            <td className="p-2 text-right font-medium">{formatCurrency(item.line_total)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                    
                    {grn.notes && (
                      <div className="mt-3 p-2 bg-slate-50 rounded text-sm text-slate-600">
                        <strong>Notes:</strong> {grn.notes}
                      </div>
                    )}
                    
                    {/* Show additional charges if any exist on linked PO */}
                    {grn.po_id && (() => {
                      const linkedPO = allPurchaseOrders.find(po => po.id === grn.po_id);
                      if (linkedPO && linkedPO.additional_charges && linkedPO.additional_charges.length > 0) {
                        return (
                          <div className="mt-3 p-3 bg-amber-50 rounded-lg">
                            <p className="text-sm font-medium text-amber-800 mb-2">Additional Charges (from PO)</p>
                            <div className="space-y-1">
                              {linkedPO.additional_charges.map((charge, idx) => (
                                <div key={idx} className="flex justify-between text-sm">
                                  <span className="text-slate-600">{charge.charge_type_name || charge.charge_type}</span>
                                  <span className={charge.charge_type === 'discount' ? 'text-green-600' : 'text-slate-800'}>
                                    {charge.charge_type === 'discount' ? '-' : ''}{formatCurrency(charge.amount)}
                                  </span>
                                </div>
                              ))}
                              <div className="border-t border-amber-200 pt-1 mt-1 flex justify-between font-medium">
                                <span>Net Charges</span>
                                <span>{formatCurrency(linkedPO.total_expenses - linkedPO.total_discounts)}</span>
                              </div>
                            </div>
                          </div>
                        );
                      }
                      return null;
                    })()}
                    
                    <div className="mt-3 flex justify-end gap-2">
                      {/* Add Charges button - only for GRNs linked to a PO */}
                      {grn.po_id && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleOpenChargesDialog(grn)}
                          data-testid={`add-charges-${grn.id}`}
                        >
                          <TruckIcon className="w-4 h-4 mr-1" />
                          Add Charges
                        </Button>
                      )}
                      {grn.woo_sync_status !== 'synced' && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleResync(grn.id)}
                          data-testid={`resync-${grn.id}`}
                        >
                          <RefreshCw className="w-4 h-4 mr-1" />
                          Re-sync to WooCommerce
                        </Button>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Create GRN Modal */}
      <Dialog open={isModalOpen} onOpenChange={(open) => { setIsModalOpen(open); if (!open) resetForm(); }}>
        <DialogContent className="sm:max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {fromPO ? (
                <div className="flex items-center gap-2">
                  <ClipboardList className="w-5 h-5 text-indigo-600" />
                  Create GRN from {fromPO.order_number}
                </div>
              ) : (
                'Create Goods Received Note'
              )}
            </DialogTitle>
            {fromPO && (
              <p className="text-sm text-slate-500 mt-1">
                Receiving goods from supplier: {fromPO.supplier_name}
              </p>
            )}
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Header Info */}
            <div className="grid grid-cols-3 gap-4">
              <div>
                <Label>Supplier *</Label>
                <Select
                  value={formData.supplier_id}
                  onValueChange={(value) => setFormData({ ...formData, supplier_id: value })}
                >
                  <SelectTrigger data-testid="grn-supplier">
                    <SelectValue placeholder="Select supplier" />
                  </SelectTrigger>
                  <SelectContent>
                    {suppliers.map(s => (
                      <SelectItem key={s.id} value={s.id}>{s.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Received Date</Label>
                <Input
                  type="date"
                  value={formData.received_date}
                  onChange={(e) => setFormData({ ...formData, received_date: e.target.value })}
                  data-testid="grn-date"
                />
              </div>
              <div>
                <Label>Reference Number</Label>
                <Input
                  value={formData.reference_number}
                  onChange={(e) => setFormData({ ...formData, reference_number: e.target.value })}
                  placeholder="Invoice/PO number"
                  data-testid="grn-reference"
                />
              </div>
            </div>

            {/* Sync Option */}
            <div className="flex items-center justify-between p-4 bg-slate-50 rounded-lg">
              <div>
                <p className="font-medium">Sync to WooCommerce</p>
                <p className="text-sm text-slate-500">Automatically sync products to your store</p>
              </div>
              <Switch
                checked={formData.sync_to_woo}
                onCheckedChange={(checked) => setFormData({ ...formData, sync_to_woo: checked })}
                data-testid="grn-sync-toggle"
              />
            </div>

            {/* Items */}
            <div>
              <div className="flex justify-between items-center mb-4">
                <Label className="text-base font-semibold">Items</Label>
                <Button type="button" variant="outline" size="sm" onClick={handleAddItem}>
                  <Plus className="w-4 h-4 mr-1" />
                  Add Item
                </Button>
              </div>

              {formData.items.length === 0 ? (
                <div className="text-center py-8 bg-slate-50 rounded-lg text-slate-500">
                  <Package className="w-8 h-8 mx-auto mb-2" />
                  <p>No items added</p>
                  <Button type="button" variant="outline" size="sm" className="mt-2" onClick={handleAddItem}>
                    Add First Item
                  </Button>
                </div>
              ) : (
                <div className="space-y-4">
                  {formData.items.map((item, idx) => (
                    <div key={idx} className="p-4 border rounded-lg bg-white space-y-4">
                      <div className="flex justify-between items-center">
                        <span className="font-medium text-slate-600">Item {idx + 1}</span>
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={() => handleRemoveItem(idx)}
                          className="text-red-500 hover:text-red-600"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>

                      {/* Existing Product Selection */}
                      <div>
                        <Label className="text-sm">Existing Product (optional)</Label>
                        <Select
                          value={item.product_id || "new"}
                          onValueChange={(value) => handleItemChange(idx, 'product_id', value === "new" ? "" : value)}
                        >
                          <SelectTrigger>
                            <SelectValue placeholder="Select existing or create new" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="new">Create New Product</SelectItem>
                            {products.map(p => (
                              <SelectItem key={p.id} value={p.id}>{p.sku} - {p.name}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>

                      {/* Product Details Row 1 */}
                      <div className="grid grid-cols-3 gap-4">
                        <div>
                          <Label className="text-sm">Product Name *</Label>
                          <Input
                            value={item.product_name}
                            onChange={(e) => handleItemChange(idx, 'product_name', e.target.value)}
                            placeholder="Product name"
                            required
                            disabled={!!item.product_id}
                          />
                        </div>
                        <div>
                          <Label className="text-sm">SKU {item.product_id ? '(from product)' : ''}</Label>
                          <Input
                            value={item.sku}
                            onChange={(e) => handleItemChange(idx, 'sku', e.target.value)}
                            placeholder="Auto-generated"
                            disabled={!!item.product_id}
                            className={item.product_id ? 'bg-slate-100' : ''}
                          />
                        </div>
                        <div>
                          <Label className="text-sm">Category (WooCommerce)</Label>
                          <Select
                            value={item.category}
                            onValueChange={(value) => handleItemChange(idx, 'category', value)}
                            disabled={!!item.product_id}
                          >
                            <SelectTrigger className={item.product_id ? 'bg-slate-100' : ''}>
                              <SelectValue placeholder="Select category" />
                            </SelectTrigger>
                            <SelectContent>
                              {wooCategories.length > 0 ? (
                                wooCategories.map((cat) => (
                                  <SelectItem key={cat.id} value={cat.name}>
                                    {cat.name}
                                  </SelectItem>
                                ))
                              ) : (
                                <>
                                  <SelectItem value="Clothing">Clothing</SelectItem>
                                  <SelectItem value="Electronics">Electronics</SelectItem>
                                  <SelectItem value="Home & Garden">Home & Garden</SelectItem>
                                  <SelectItem value="Sports">Sports</SelectItem>
                                  <SelectItem value="Beauty">Beauty</SelectItem>
                                  <SelectItem value="Food & Beverages">Food & Beverages</SelectItem>
                                </>
                              )}
                            </SelectContent>
                          </Select>
                        </div>
                      </div>

                      {/* Product Details Row 2 - Pricing */}
                      <div className="grid grid-cols-4 gap-4">
                        <div>
                          <Label className="text-sm">Quantity *</Label>
                          <Input
                            type="number"
                            value={item.quantity}
                            onChange={(e) => handleItemChange(idx, 'quantity', parseInt(e.target.value) || 0)}
                            min="1"
                            required
                          />
                        </div>
                        <div>
                          <Label className="text-sm">Cost Price (COGS) *</Label>
                          <Input
                            type="number"
                            value={item.cost_price}
                            onChange={(e) => handleItemChange(idx, 'cost_price', parseFloat(e.target.value) || 0)}
                            step="0.01"
                            min="0"
                            required
                          />
                        </div>
                        <div>
                          <Label className="text-sm">Regular Price *</Label>
                          <Input
                            type="number"
                            value={item.regular_price}
                            onChange={(e) => handleItemChange(idx, 'regular_price', parseFloat(e.target.value) || 0)}
                            step="0.01"
                            min="0"
                            required
                          />
                        </div>
                        <div>
                          <Label className="text-sm">Sale Price</Label>
                          <Input
                            type="number"
                            value={item.sale_price}
                            onChange={(e) => handleItemChange(idx, 'sale_price', e.target.value)}
                            step="0.01"
                            min="0"
                            placeholder="Optional"
                          />
                        </div>
                      </div>

                      {/* Product Details Row 3 - Descriptions */}
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <Label className="text-sm">Description</Label>
                          <Textarea
                            value={item.description}
                            onChange={(e) => handleItemChange(idx, 'description', e.target.value)}
                            placeholder="Full product description"
                            rows={2}
                          />
                        </div>
                        <div>
                          <Label className="text-sm">Short Description</Label>
                          <Textarea
                            value={item.short_description}
                            onChange={(e) => handleItemChange(idx, 'short_description', e.target.value)}
                            placeholder="Brief description for listings"
                            rows={2}
                          />
                        </div>
                      </div>

                      {/* Product Details Row 4 - WooCommerce */}
                      <div className="grid grid-cols-4 gap-4">
                        <div>
                          <Label className="text-sm">Weight (kg)</Label>
                          <Input
                            type="number"
                            value={item.weight}
                            onChange={(e) => handleItemChange(idx, 'weight', e.target.value)}
                            step="0.01"
                            min="0"
                            placeholder="0.00"
                          />
                        </div>
                        <div>
                          <Label className="text-sm">Visibility</Label>
                          <Select
                            value={item.visibility}
                            onValueChange={(value) => handleItemChange(idx, 'visibility', value)}
                          >
                            <SelectTrigger>
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="public">Public</SelectItem>
                              <SelectItem value="private">Private</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                        <div className="col-span-2">
                          <div className="flex justify-between items-center mb-1">
                            <Label className="text-sm">Tags (SEO - comma separated)</Label>
                            <Button
                              type="button"
                              variant="ghost"
                              size="sm"
                              onClick={() => suggestTags(idx)}
                              className="text-xs text-indigo-600 hover:text-indigo-800 h-6 px-2"
                            >
                              ✨ Suggest SEO Tags
                            </Button>
                          </div>
                          <Input
                            value={item.tags}
                            onChange={(e) => handleItemChange(idx, 'tags', e.target.value)}
                            placeholder="fashion, clothing, style..."
                          />
                          {wooTags.length > 0 && (
                            <p className="text-xs text-slate-400 mt-1">
                              Popular: {wooTags.slice(0, 5).map(t => t.name).join(', ')}
                            </p>
                          )}
                        </div>
                      </div>

                      {/* Line Total */}
                      <div className="text-right pt-2 border-t">
                        <span className="text-sm text-slate-500">Line Total: </span>
                        <span className="font-semibold text-lg">
                          {formatCurrency(item.quantity * item.cost_price)}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Notes */}
            <div>
              <Label>Notes</Label>
              <Textarea
                value={formData.notes}
                onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                placeholder="Additional notes..."
                rows={2}
              />
            </div>

            {/* Total */}
            {formData.items.length > 0 && (
              <div className="p-4 bg-slate-100 rounded-lg flex justify-between items-center">
                <span className="font-semibold">Total Cost (COGS)</span>
                <span className="text-2xl font-bold">{formatCurrency(calculateTotals())}</span>
              </div>
            )}

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setIsModalOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" data-testid="save-grn-btn">
                Create GRN
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Additional Charges Dialog */}
      <Dialog open={chargesDialogOpen} onOpenChange={setChargesDialogOpen}>
        <DialogContent className="max-w-2xl" data-testid="grn-charges-dialog">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2" style={{ fontFamily: 'Outfit, sans-serif' }}>
              <TruckIcon className="w-5 h-5" />
              Additional Charges
            </DialogTitle>
            <DialogDescription>
              Add shipping, customs, handling fees or discounts for {selectedPO?.order_number}
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
                  <SelectTrigger data-testid="grn-charge-type-select">
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
                    id="grn-pay-immediately"
                    checked={newCharge.pay_immediately}
                    onCheckedChange={(v) => setNewCharge({ ...newCharge, pay_immediately: v })}
                  />
                  <Label htmlFor="grn-pay-immediately" className="text-xs">Pay Now</Label>
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
                          {acc.name} ({acc.type})
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
                      const isExisting = index < (selectedPO?.additional_charges?.length || 0);
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
                  <p className="text-lg font-semibold">{formatCurrency(selectedPO?.subtotal || 0)}</p>
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
                    {formatCurrency((selectedPO?.subtotal || 0) + calculateChargesTotal().net)}
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
              disabled={submitting || additionalCharges.length === (selectedPO?.additional_charges?.length || 0)}
              className="bg-indigo-600 hover:bg-indigo-700"
              data-testid="grn-submit-charges-btn"
            >
              {submitting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
              Save Charges
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* View GRN Dialog */}
      <Dialog open={viewDialogOpen} onOpenChange={setViewDialogOpen}>
        <DialogContent className="max-w-3xl" data-testid="view-grn-dialog">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2" style={{ fontFamily: 'Outfit, sans-serif' }}>
              <FileText className="w-5 h-5" />
              GRN Details - {selectedGrn?.grn_number}
            </DialogTitle>
            <DialogDescription>
              Received on {selectedGrn?.received_date} from {selectedGrn?.supplier_name}
            </DialogDescription>
          </DialogHeader>
          
          {selectedGrn && (
            <div className="space-y-4 py-4">
              {/* Status badges */}
              <div className="flex gap-2">
                {getSyncStatusBadge(selectedGrn.woo_sync_status)}
                {selectedGrn.status === 'returned' && (
                  <Badge variant="destructive" className="bg-red-100 text-red-800">Returned</Badge>
                )}
                {selectedGrn.status === 'partial_return' && (
                  <Badge variant="warning" className="bg-amber-100 text-amber-800">Partial Return</Badge>
                )}
                {selectedGrn.po_id && (
                  <Badge variant="outline">From PO</Badge>
                )}
              </div>

              {/* GRN Info */}
              <div className="grid grid-cols-3 gap-4 p-4 bg-slate-50 rounded-lg">
                <div>
                  <p className="text-sm text-slate-500">GRN Number</p>
                  <p className="font-semibold">{selectedGrn.grn_number}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-500">Supplier</p>
                  <p className="font-semibold">{selectedGrn.supplier_name}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-500">Received Date</p>
                  <p className="font-semibold">{selectedGrn.received_date}</p>
                </div>
                {selectedGrn.po_id && (
                  <div>
                    <p className="text-sm text-slate-500">Purchase Order</p>
                    <p className="font-semibold">
                      {allPurchaseOrders.find(po => po.id === selectedGrn.po_id)?.order_number || 'N/A'}
                    </p>
                  </div>
                )}
              </div>

              {/* Items Table */}
              <div className="border rounded-lg overflow-hidden">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>SKU</TableHead>
                      <TableHead>Product</TableHead>
                      <TableHead className="text-right">Qty</TableHead>
                      <TableHead className="text-right">Cost Price</TableHead>
                      <TableHead className="text-right">Regular Price</TableHead>
                      <TableHead className="text-right">Line Total</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {selectedGrn.items.map((item, index) => (
                      <TableRow key={index}>
                        <TableCell className="font-mono text-sm">{item.sku}</TableCell>
                        <TableCell>{item.product_name}</TableCell>
                        <TableCell className="text-right">{item.quantity}</TableCell>
                        <TableCell className="text-right">{formatCurrency(item.cost_price)}</TableCell>
                        <TableCell className="text-right">{formatCurrency(item.regular_price)}</TableCell>
                        <TableCell className="text-right font-medium">
                          {formatCurrency(item.quantity * item.cost_price)}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>

              {/* Total */}
              <div className="flex justify-end">
                <div className="bg-indigo-50 p-4 rounded-lg text-right">
                  <p className="text-sm text-slate-500">Total Cost (COGS)</p>
                  <p className="text-2xl font-bold text-indigo-600">{formatCurrency(selectedGrn.total_cost)}</p>
                </div>
              </div>

              {/* Notes */}
              {selectedGrn.notes && (
                <div className="p-3 bg-slate-50 rounded-lg">
                  <p className="text-sm text-slate-500 mb-1">Notes</p>
                  <p className="text-sm">{selectedGrn.notes}</p>
                </div>
              )}

              {/* Return History */}
              {selectedGrn.returns && selectedGrn.returns.length > 0 && (
                <div className="border-t pt-4">
                  <p className="font-semibold mb-2 text-red-600">Return History</p>
                  {selectedGrn.returns.map((ret, idx) => (
                    <div key={idx} className="p-3 bg-red-50 rounded-lg mb-2">
                      <div className="flex justify-between">
                        <span className="text-sm font-medium">
                          {ret.return_reason === 'supplier' ? 'Returned to Supplier' : 'Written Off (Damaged)'}
                        </span>
                        <span className="text-sm text-slate-500">{ret.return_date}</span>
                      </div>
                      <p className="text-sm text-slate-600 mt-1">
                        {ret.items.length} items, Total: {formatCurrency(ret.total_value)}
                      </p>
                      {ret.notes && <p className="text-xs text-slate-500 mt-1">{ret.notes}</p>}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          <DialogFooter>
            <Button variant="outline" onClick={() => setViewDialogOpen(false)}>Close</Button>
            {canReturn && selectedGrn?.status !== 'returned' && (
              <Button 
                variant="destructive"
                onClick={() => {
                  setViewDialogOpen(false);
                  handleOpenReturnDialog(selectedGrn);
                }}
              >
                <RotateCcw className="w-4 h-4 mr-2" />
                Return GRN
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Return GRN Dialog */}
      <Dialog open={returnDialogOpen} onOpenChange={setReturnDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto" data-testid="return-grn-dialog">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-red-600" style={{ fontFamily: 'Outfit, sans-serif' }}>
              <RotateCcw className="w-5 h-5" />
              Return GRN - {selectedGrn?.grn_number}
            </DialogTitle>
            <DialogDescription>
              Process a return for goods received. This will reverse inventory and financial entries.
            </DialogDescription>
          </DialogHeader>
          
          {selectedGrn && (
            <div className="space-y-4 py-4">
              {/* PO Payment Status */}
              {linkedPODetails && (
                <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
                  <p className="text-sm font-medium text-blue-800 mb-2">Purchase Order Payment Status</p>
                  <div className="grid grid-cols-3 gap-2 text-sm">
                    <div>
                      <span className="text-blue-600">PO Number:</span>
                      <span className="ml-1 font-medium">{linkedPODetails.order_number}</span>
                    </div>
                    <div>
                      <span className="text-blue-600">Total:</span>
                      <span className="ml-1 font-medium">{formatCurrency(linkedPODetails.total)}</span>
                    </div>
                    <div>
                      <span className="text-blue-600">Paid:</span>
                      <span className="ml-1 font-medium">{formatCurrency(linkedPODetails.paid_amount)}</span>
                      {linkedPODetails.paid_amount >= linkedPODetails.total && (
                        <Badge className="ml-2 bg-green-100 text-green-800">Fully Paid</Badge>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Return Type */}
              <div className="space-y-2">
                <Label>Return Type</Label>
                <div className="flex gap-4">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="radio"
                      name="returnType"
                      value="full"
                      checked={returnType === 'full'}
                      onChange={() => setReturnType('full')}
                      className="w-4 h-4"
                    />
                    <span>Full Return (All Items)</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="radio"
                      name="returnType"
                      value="partial"
                      checked={returnType === 'partial'}
                      onChange={() => setReturnType('partial')}
                      className="w-4 h-4"
                    />
                    <span>Partial Return (Select Items)</span>
                  </label>
                </div>
              </div>

              {/* Return Reason */}
              <div className="space-y-2">
                <Label>Return Reason</Label>
                <Select value={returnReason} onValueChange={setReturnReason}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="supplier">Return to Supplier</SelectItem>
                    <SelectItem value="damaged">Damaged / Written Off</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Settlement Type - Only for Return to Supplier */}
              {returnReason === 'supplier' && (
                <div className="space-y-3 p-4 bg-slate-50 rounded-lg border">
                  <Label className="text-base font-medium">How will supplier settle this return?</Label>
                  <div className="space-y-3">
                    <label className="flex items-start gap-3 cursor-pointer p-3 rounded-lg border bg-white hover:bg-slate-50">
                      <input
                        type="radio"
                        name="settlementType"
                        value="refund"
                        checked={returnSettlement === 'refund'}
                        onChange={() => setReturnSettlement('refund')}
                        className="w-4 h-4 mt-1"
                      />
                      <div>
                        <span className="font-medium">Supplier Returns Money (Refund)</span>
                        <p className="text-xs text-slate-500 mt-1">
                          Supplier will refund the amount to your bank/cash account
                        </p>
                      </div>
                    </label>
                    <label className="flex items-start gap-3 cursor-pointer p-3 rounded-lg border bg-white hover:bg-slate-50">
                      <input
                        type="radio"
                        name="settlementType"
                        value="credit"
                        checked={returnSettlement === 'credit'}
                        onChange={() => setReturnSettlement('credit')}
                        className="w-4 h-4 mt-1"
                      />
                      <div>
                        <span className="font-medium">Supplier Sends More Qty (Credit)</span>
                        <p className="text-xs text-slate-500 mt-1">
                          Amount will be tracked as credit with supplier for future orders
                        </p>
                      </div>
                    </label>
                  </div>

                  {/* Refund Account Selection */}
                  {returnSettlement === 'refund' && (
                    <div className="mt-3">
                      <Label>Receive Refund To</Label>
                      <Select value={refundAccountId} onValueChange={setRefundAccountId}>
                        <SelectTrigger className="mt-1">
                          <SelectValue placeholder="Select account to receive refund" />
                        </SelectTrigger>
                        <SelectContent>
                          {bankAccounts.map((acc) => (
                            <SelectItem key={acc.id} value={acc.id}>
                              {acc.name} ({acc.type}) - {formatCurrency(acc.balance)}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  )}
                </div>
              )}

              {/* Damaged/Written Off Info */}
              {returnReason === 'damaged' && (
                <div className="p-3 bg-amber-50 rounded-lg text-sm text-amber-800">
                  <p className="font-medium">Damaged / Written Off</p>
                  <p className="text-xs mt-1">Goods will be written off as a loss. Inventory reduced, Loss expense recorded.</p>
                </div>
              )}

              {/* Items Selection (for partial return) */}
              {returnType === 'partial' && (
                <div className="border rounded-lg overflow-hidden">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="w-10"></TableHead>
                        <TableHead>Product</TableHead>
                        <TableHead className="text-right">Received</TableHead>
                        <TableHead className="text-right">Return Qty</TableHead>
                        <TableHead className="text-right">Value</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {returnItems.map((item, index) => (
                        <TableRow key={index}>
                          <TableCell>
                            <Checkbox
                              checked={item.selected}
                              onCheckedChange={(checked) => handleReturnItemChange(index, 'selected', checked)}
                            />
                          </TableCell>
                          <TableCell>
                            <div>
                              <p className="font-medium">{item.product_name}</p>
                              <p className="text-xs text-slate-500">{item.sku}</p>
                            </div>
                          </TableCell>
                          <TableCell className="text-right">{item.quantity}</TableCell>
                          <TableCell className="text-right">
                            <Input
                              type="number"
                              min="0"
                              max={item.quantity}
                              value={item.return_quantity}
                              onChange={(e) => handleReturnItemChange(index, 'return_quantity', e.target.value)}
                              disabled={!item.selected}
                              className="w-20 text-right"
                            />
                          </TableCell>
                          <TableCell className="text-right font-medium">
                            {item.selected ? formatCurrency(item.return_quantity * item.cost_price) : '-'}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              )}

              {/* Full Return Summary */}
              {returnType === 'full' && (
                <div className="border rounded-lg overflow-hidden">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Product</TableHead>
                        <TableHead className="text-right">Qty</TableHead>
                        <TableHead className="text-right">Value</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {selectedGrn.items.map((item, index) => (
                        <TableRow key={index}>
                          <TableCell>
                            <div>
                              <p className="font-medium">{item.product_name}</p>
                              <p className="text-xs text-slate-500">{item.sku}</p>
                            </div>
                          </TableCell>
                          <TableCell className="text-right">{item.quantity}</TableCell>
                          <TableCell className="text-right font-medium">
                            {formatCurrency(item.quantity * item.cost_price)}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              )}

              {/* Notes */}
              <div className="space-y-2">
                <Label>Return Notes</Label>
                <Textarea
                  value={returnNotes}
                  onChange={(e) => setReturnNotes(e.target.value)}
                  placeholder="Optional notes about this return..."
                  rows={2}
                />
              </div>

              {/* Return Summary */}
              <div className="bg-red-50 p-4 rounded-lg">
                <div className="flex justify-between items-center">
                  <div>
                    <p className="text-sm text-red-800 font-medium">Total Return Value</p>
                    <p className="text-xs text-red-600">
                      {returnReason === 'damaged' && 'Will record as Loss/Write-off expense'}
                      {returnReason === 'supplier' && returnSettlement === 'refund' && 'Supplier will refund to your account'}
                      {returnReason === 'supplier' && returnSettlement === 'credit' && 'Will be tracked as supplier credit'}
                    </p>
                  </div>
                  <p className="text-2xl font-bold text-red-600">{formatCurrency(calculateReturnTotal())}</p>
                </div>
              </div>

              {/* Warning */}
              <div className="flex items-start gap-2 p-3 bg-amber-50 rounded-lg">
                <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
                <div className="text-sm text-amber-800">
                  <p className="font-medium">This action will:</p>
                  <ul className="list-disc list-inside mt-1">
                    <li>Reduce inventory quantities</li>
                    <li>Create reversal journal entries</li>
                    {returnReason === 'supplier' && <li>Reduce Accounts Payable to supplier</li>}
                    {returnReason === 'damaged' && <li>Record a loss/write-off expense</li>}
                    <li>This action cannot be undone</li>
                  </ul>
                </div>
              </div>
            </div>
          )}

          <DialogFooter>
            <Button variant="outline" onClick={() => setReturnDialogOpen(false)}>Cancel</Button>
            <Button 
              variant="destructive"
              onClick={handleSubmitReturn}
              disabled={submitting || calculateReturnTotal() === 0}
              data-testid="confirm-return-btn"
            >
              {submitting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
              Process Return
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
