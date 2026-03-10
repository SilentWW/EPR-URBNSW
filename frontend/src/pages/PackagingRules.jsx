import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '../components/ui/dialog';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from '../components/ui/alert-dialog';
import { toast } from 'sonner';
import api from '../lib/api';
import { 
  Package, Plus, Edit2, Trash2, RefreshCw, 
  Link as LinkIcon, AlertTriangle, Search, Box
} from 'lucide-react';

export default function PackagingRules() {
  const [packagingRules, setPackagingRules] = useState([]);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  
  // Rule Modal State
  const [showRuleModal, setShowRuleModal] = useState(false);
  const [editingRule, setEditingRule] = useState(null);
  const [ruleForm, setRuleForm] = useState({
    product_id: '',
    items: [],
    is_active: true
  });
  
  // Delete Dialog State
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState({ id: '', name: '' });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [rulesRes, productsRes] = await Promise.all([
        api.get('/packaging/rules'),
        api.get('/products')
      ]);
      setPackagingRules(rulesRes.data);
      setProducts(productsRes.data);
    } catch (error) {
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  // Get products that already have rules
  const productsWithRules = packagingRules.map(r => r.product_id);
  
  // Get products available for new rules (excluding those with existing rules)
  const availableProductsForRule = products.filter(p => 
    editingRule ? true : !productsWithRules.includes(p.id)
  );

  const handleSaveRule = async () => {
    if (!ruleForm.product_id) {
      toast.error('Please select a product');
      return;
    }
    if (ruleForm.items.length === 0) {
      toast.error('Please add at least one packaging product');
      return;
    }

    try {
      const payload = {
        product_id: ruleForm.product_id,
        items: ruleForm.items.map(i => ({
          product_id: i.product_id,
          quantity: i.quantity
        })),
        is_active: ruleForm.is_active
      };

      if (editingRule) {
        await api.put(`/packaging/rules/${editingRule.id}`, payload);
        toast.success('Packaging rule updated');
      } else {
        await api.post('/packaging/rules', payload);
        toast.success('Packaging rule created');
      }
      setShowRuleModal(false);
      resetRuleForm();
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save rule');
    }
  };

  const handleEditRule = (rule) => {
    setEditingRule(rule);
    setRuleForm({
      product_id: rule.product_id,
      items: rule.items.map(i => ({
        product_id: i.product_id,
        quantity: i.quantity,
        product_name: i.product_name
      })),
      is_active: rule.is_active
    });
    setShowRuleModal(true);
  };

  const resetRuleForm = () => {
    setEditingRule(null);
    setRuleForm({
      product_id: '',
      items: [],
      is_active: true
    });
  };

  const addProductToRule = (productId) => {
    const product = products.find(p => p.id === productId);
    if (!product) return;
    
    if (ruleForm.items.some(i => i.product_id === productId)) {
      toast.error('Product already added');
      return;
    }

    // Don't allow adding the main product as packaging
    if (productId === ruleForm.product_id) {
      toast.error('Cannot add the same product as its own packaging');
      return;
    }
    
    setRuleForm({
      ...ruleForm,
      items: [...ruleForm.items, {
        product_id: productId,
        quantity: 1,
        product_name: product.name
      }]
    });
  };

  const updateRuleItemQty = (productId, qty) => {
    setRuleForm({
      ...ruleForm,
      items: ruleForm.items.map(i => 
        i.product_id === productId ? { ...i, quantity: parseInt(qty) || 1 } : i
      )
    });
  };

  const removeProductFromRule = (productId) => {
    setRuleForm({
      ...ruleForm,
      items: ruleForm.items.filter(i => i.product_id !== productId)
    });
  };

  const confirmDelete = async () => {
    try {
      await api.delete(`/packaging/rules/${deleteTarget.id}`);
      toast.success('Packaging rule deleted');
      setShowDeleteDialog(false);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete');
    }
  };

  // Filter rules based on search
  const filteredRules = packagingRules.filter(rule =>
    rule.product_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    rule.product_sku?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Get low stock packaging products (products used in packaging rules)
  const packagingProductIds = [...new Set(packagingRules.flatMap(r => r.items.map(i => i.product_id)))];
  const lowStockPackaging = products.filter(p => 
    packagingProductIds.includes(p.id) && p.stock_quantity <= p.low_stock_threshold
  );

  return (
    <div className="space-y-6" data-testid="packaging-rules-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
            <Package className="w-6 h-6 text-orange-600" />
            Packaging Rules
          </h1>
          <p className="text-slate-500 text-sm mt-1">
            Link products to their packaging materials (auto-deducted when orders are created)
          </p>
        </div>
        <div className="flex gap-2">
          <Button onClick={fetchData} variant="outline" size="sm">
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button onClick={() => { resetRuleForm(); setShowRuleModal(true); }} data-testid="add-rule-btn">
            <Plus className="w-4 h-4 mr-2" />
            Add Rule
          </Button>
        </div>
      </div>

      {/* Info Card */}
      <Card className="bg-blue-50 border-blue-200">
        <CardContent className="py-4">
          <div className="flex items-start gap-3">
            <Box className="w-6 h-6 text-blue-600 mt-0.5" />
            <div className="text-sm text-blue-700">
              <p className="font-medium">How Packaging Rules Work:</p>
              <ul className="mt-1 list-disc list-inside space-y-1">
                <li>Create packaging materials as regular <strong>Products</strong> (e.g., Courier Bag, Thank You Card D1)</li>
                <li>Buy them using normal <strong>PO → GRN</strong> flow</li>
                <li>Link them to your main products using rules below</li>
                <li>When a sales order is created, packaging is <strong>auto-deducted</strong> from inventory</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Low Stock Warning */}
      {lowStockPackaging.length > 0 && (
        <Card className="border-orange-200 bg-orange-50">
          <CardContent className="py-3">
            <div className="flex items-center gap-2 text-orange-700">
              <AlertTriangle className="w-5 h-5" />
              <span className="font-medium">Low stock packaging products:</span>
              <span>{lowStockPackaging.map(p => `${p.name} (${p.stock_quantity})`).join(', ')}</span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Search */}
      <div className="relative max-w-md">
        <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
        <Input
          placeholder="Search products..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="pl-9"
        />
      </div>

      {/* Rules List */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-lg flex items-center gap-2">
            <LinkIcon className="w-5 h-5" />
            Product Packaging Rules ({packagingRules.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8 text-slate-500">
              <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2" />
              Loading...
            </div>
          ) : filteredRules.length === 0 ? (
            <div className="text-center py-8 text-slate-500">
              <LinkIcon className="w-10 h-10 mx-auto mb-2 text-slate-300" />
              <p>No packaging rules found.</p>
              <p className="text-sm mt-1">Create rules to link products with their packaging materials.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {filteredRules.map((rule) => (
                <div key={rule.id} className="border rounded-lg p-4 hover:bg-slate-50">
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="font-medium">{rule.product_name}</h3>
                        <code className="text-xs bg-slate-100 px-2 py-0.5 rounded">{rule.product_sku}</code>
                        {rule.is_active ? (
                          <Badge className="bg-green-100 text-green-700">Active</Badge>
                        ) : (
                          <Badge className="bg-slate-100 text-slate-600">Inactive</Badge>
                        )}
                      </div>
                      <div className="mt-2 flex flex-wrap gap-2">
                        {rule.items.map((item, idx) => (
                          <div key={idx} className="flex items-center gap-1 bg-orange-50 text-orange-700 px-2 py-1 rounded text-sm">
                            <Package className="w-3 h-3" />
                            {item.product_name} × {item.quantity}
                            {item.stock_quantity !== undefined && (
                              <span className={`ml-1 text-xs ${item.stock_quantity <= 10 ? 'text-red-600' : 'text-slate-500'}`}>
                                (Stock: {item.stock_quantity})
                              </span>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                    <div className="flex gap-1">
                      <Button size="sm" variant="ghost" onClick={() => handleEditRule(rule)}>
                        <Edit2 className="w-4 h-4" />
                      </Button>
                      <Button 
                        size="sm" 
                        variant="ghost" 
                        className="text-red-600 hover:text-red-700"
                        onClick={() => {
                          setDeleteTarget({ id: rule.id, name: rule.product_name });
                          setShowDeleteDialog(true);
                        }}
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Add/Edit Rule Modal */}
      <Dialog open={showRuleModal} onOpenChange={setShowRuleModal}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>{editingRule ? 'Edit Packaging Rule' : 'Create Packaging Rule'}</DialogTitle>
            <DialogDescription>
              Select a product and add its packaging materials
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>Main Product *</Label>
              <Select 
                value={ruleForm.product_id} 
                onValueChange={(v) => setRuleForm({ ...ruleForm, product_id: v })}
                disabled={!!editingRule}
              >
                <SelectTrigger data-testid="product-select">
                  <SelectValue placeholder="Select a product" />
                </SelectTrigger>
                <SelectContent>
                  {availableProductsForRule.map(p => (
                    <SelectItem key={p.id} value={p.id}>
                      {p.name} ({p.sku})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {editingRule && (
                <p className="text-xs text-slate-500 mt-1">Product cannot be changed. Delete and create new rule if needed.</p>
              )}
            </div>

            <div>
              <Label>Add Packaging Products</Label>
              <Select onValueChange={addProductToRule}>
                <SelectTrigger data-testid="add-packaging-select">
                  <SelectValue placeholder="Select packaging product to add" />
                </SelectTrigger>
                <SelectContent>
                  {products
                    .filter(p => p.id !== ruleForm.product_id && !ruleForm.items.some(i => i.product_id === p.id))
                    .map(p => (
                      <SelectItem key={p.id} value={p.id}>
                        {p.name} ({p.sku}) - Stock: {p.stock_quantity}
                      </SelectItem>
                    ))
                  }
                </SelectContent>
              </Select>
            </div>

            {ruleForm.items.length > 0 && (
              <div className="border rounded-lg p-3 space-y-2">
                <Label className="text-sm text-slate-500">Packaging for this Product:</Label>
                {ruleForm.items.map((item) => (
                  <div key={item.product_id} className="flex items-center justify-between bg-slate-50 p-2 rounded">
                    <span className="font-medium text-sm">{item.product_name}</span>
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-slate-500">Qty:</span>
                      <Input
                        type="number"
                        min="1"
                        value={item.quantity}
                        onChange={(e) => updateRuleItemQty(item.product_id, e.target.value)}
                        className="w-16 h-8"
                      />
                      <Button 
                        size="sm" 
                        variant="ghost" 
                        className="text-red-600 h-8 w-8 p-0"
                        onClick={() => removeProductFromRule(item.product_id)}
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}

            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="is_active"
                checked={ruleForm.is_active}
                onChange={(e) => setRuleForm({ ...ruleForm, is_active: e.target.checked })}
                className="rounded"
              />
              <Label htmlFor="is_active" className="cursor-pointer">Rule is active</Label>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowRuleModal(false)}>Cancel</Button>
            <Button onClick={handleSaveRule} data-testid="save-rule-btn">
              {editingRule ? 'Update' : 'Create'} Rule
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation */}
      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Packaging Rule</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete the packaging rule for "{deleteTarget.name}"? This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={confirmDelete} className="bg-red-600 hover:bg-red-700">
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
