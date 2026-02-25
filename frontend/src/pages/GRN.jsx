import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import api from '../lib/api';
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
  Loader2
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

export default function GRN() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [grns, setGrns] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [products, setProducts] = useState([]);
  const [purchaseOrders, setPurchaseOrders] = useState([]);
  const [wooCategories, setWooCategories] = useState([]);
  const [wooTags, setWooTags] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [expandedGrn, setExpandedGrn] = useState(null);
  const [nextSku, setNextSku] = useState('');
  const [fromPO, setFromPO] = useState(null); // Track if GRN is being created from a PO
  
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
      const [grnsRes, suppliersRes, productsRes, skuRes, poRes, catRes, tagsRes] = await Promise.all([
        api.get('/grn'),
        api.get('/suppliers'),
        api.get('/products'),
        api.get('/grn/next-sku'),
        api.get('/purchase-orders'),
        api.get('/woocommerce/categories').catch(() => ({ data: [] })),
        api.get('/woocommerce/tags').catch(() => ({ data: [] }))
      ]);
      setGrns(grnsRes.data);
      setSuppliers(suppliersRes.data);
      setProducts(productsRes.data);
      setNextSku(skuRes.data.next_sku);
      setPurchaseOrders(poRes.data.filter(po => po.status === 'pending')); // Only pending POs
      setWooCategories(catRes.data || []);
      setWooTags(tagsRes.data || []);
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
                <button
                  onClick={() => setExpandedGrn(expandedGrn === grn.id ? null : grn.id)}
                  className="w-full p-4 flex items-center justify-between text-left"
                >
                  <div className="flex items-center gap-4">
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
                      </div>
                      <p className="text-sm text-slate-600">{grn.supplier_name}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-slate-500">{grn.received_date}</p>
                    <p className="font-semibold">{formatCurrency(grn.total_cost)}</p>
                    <p className="text-xs text-slate-400">{grn.items.length} items</p>
                  </div>
                </button>
                
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
                    
                    <div className="mt-3 flex justify-end gap-2">
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
    </div>
  );
}
