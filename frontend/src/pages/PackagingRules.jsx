import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '../components/ui/dialog';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from '../components/ui/alert-dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { toast } from 'sonner';
import api from '../lib/api';
import { 
  Package, Plus, Edit2, Trash2, RefreshCw, Box, 
  Link as LinkIcon, AlertTriangle, CheckCircle, Search,
  PackagePlus, Settings2
} from 'lucide-react';

export default function PackagingRules() {
  const [activeTab, setActiveTab] = useState('items');
  const [packagingItems, setPackagingItems] = useState([]);
  const [packagingRules, setPackagingRules] = useState([]);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  
  // Item Modal State
  const [showItemModal, setShowItemModal] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [itemForm, setItemForm] = useState({
    name: '',
    sku: '',
    description: '',
    stock_quantity: 0,
    low_stock_threshold: 10,
    unit: 'pcs'
  });
  
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
  const [deleteTarget, setDeleteTarget] = useState({ type: '', id: '', name: '' });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [itemsRes, rulesRes, productsRes] = await Promise.all([
        api.get('/packaging/items'),
        api.get('/packaging/rules'),
        api.get('/products')
      ]);
      setPackagingItems(itemsRes.data);
      setPackagingRules(rulesRes.data);
      setProducts(productsRes.data);
    } catch (error) {
      toast.error('Failed to load packaging data');
    } finally {
      setLoading(false);
    }
  };

  // ==================== ITEM FUNCTIONS ====================
  
  const handleSaveItem = async () => {
    if (!itemForm.name) {
      toast.error('Please enter item name');
      return;
    }

    try {
      if (editingItem) {
        await api.put(`/packaging/items/${editingItem.id}`, itemForm);
        toast.success('Packaging item updated');
      } else {
        await api.post('/packaging/items', itemForm);
        toast.success('Packaging item created');
      }
      setShowItemModal(false);
      resetItemForm();
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save item');
    }
  };

  const handleEditItem = (item) => {
    setEditingItem(item);
    setItemForm({
      name: item.name,
      sku: item.sku || '',
      description: item.description || '',
      stock_quantity: item.stock_quantity,
      low_stock_threshold: item.low_stock_threshold,
      unit: item.unit || 'pcs'
    });
    setShowItemModal(true);
  };

  const resetItemForm = () => {
    setEditingItem(null);
    setItemForm({
      name: '',
      sku: '',
      description: '',
      stock_quantity: 0,
      low_stock_threshold: 10,
      unit: 'pcs'
    });
  };

  // ==================== RULE FUNCTIONS ====================

  const handleSaveRule = async () => {
    if (!ruleForm.product_id) {
      toast.error('Please select a product');
      return;
    }
    if (ruleForm.items.length === 0) {
      toast.error('Please add at least one packaging item');
      return;
    }

    try {
      const payload = {
        product_id: ruleForm.product_id,
        items: ruleForm.items.map(i => ({
          packaging_item_id: i.packaging_item_id,
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
        packaging_item_id: i.packaging_item_id,
        quantity: i.quantity,
        item_name: i.item_name
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

  const addItemToRule = (itemId) => {
    const item = packagingItems.find(i => i.id === itemId);
    if (!item) return;
    
    if (ruleForm.items.some(i => i.packaging_item_id === itemId)) {
      toast.error('Item already added');
      return;
    }
    
    setRuleForm({
      ...ruleForm,
      items: [...ruleForm.items, {
        packaging_item_id: itemId,
        quantity: 1,
        item_name: item.name
      }]
    });
  };

  const updateRuleItemQty = (itemId, qty) => {
    setRuleForm({
      ...ruleForm,
      items: ruleForm.items.map(i => 
        i.packaging_item_id === itemId ? { ...i, quantity: parseInt(qty) || 1 } : i
      )
    });
  };

  const removeItemFromRule = (itemId) => {
    setRuleForm({
      ...ruleForm,
      items: ruleForm.items.filter(i => i.packaging_item_id !== itemId)
    });
  };

  // ==================== DELETE FUNCTIONS ====================

  const confirmDelete = async () => {
    try {
      if (deleteTarget.type === 'item') {
        await api.delete(`/packaging/items/${deleteTarget.id}`);
        toast.success('Packaging item deleted');
      } else {
        await api.delete(`/packaging/rules/${deleteTarget.id}`);
        toast.success('Packaging rule deleted');
      }
      setShowDeleteDialog(false);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete');
    }
  };

  // Filter items and rules based on search
  const filteredItems = packagingItems.filter(item =>
    item.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    item.sku?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const filteredRules = packagingRules.filter(rule =>
    rule.product_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    rule.product_sku?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const lowStockItems = packagingItems.filter(i => i.stock_quantity <= i.low_stock_threshold);

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
            Manage packaging materials and assign them to products
          </p>
        </div>
        <Button onClick={fetchData} variant="outline" size="sm">
          <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Low Stock Warning */}
      {lowStockItems.length > 0 && (
        <Card className="border-orange-200 bg-orange-50">
          <CardContent className="py-3">
            <div className="flex items-center gap-2 text-orange-700">
              <AlertTriangle className="w-5 h-5" />
              <span className="font-medium">{lowStockItems.length} packaging item(s) with low stock:</span>
              <span>{lowStockItems.map(i => i.name).join(', ')}</span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Search */}
      <div className="relative max-w-md">
        <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
        <Input
          placeholder="Search items or products..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="pl-9"
        />
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="items" data-testid="items-tab">
            <Box className="w-4 h-4 mr-2" />
            Packaging Items ({packagingItems.length})
          </TabsTrigger>
          <TabsTrigger value="rules" data-testid="rules-tab">
            <LinkIcon className="w-4 h-4 mr-2" />
            Product Rules ({packagingRules.length})
          </TabsTrigger>
        </TabsList>

        {/* Packaging Items Tab */}
        <TabsContent value="items" className="mt-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-lg">Packaging Materials</CardTitle>
              <Button onClick={() => { resetItemForm(); setShowItemModal(true); }} data-testid="add-item-btn">
                <Plus className="w-4 h-4 mr-2" />
                Add Item
              </Button>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="text-center py-8 text-slate-500">
                  <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2" />
                  Loading...
                </div>
              ) : filteredItems.length === 0 ? (
                <div className="text-center py-8 text-slate-500">
                  <Box className="w-10 h-10 mx-auto mb-2 text-slate-300" />
                  No packaging items found. Add your first item.
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b bg-slate-50">
                        <th className="text-left p-3 font-medium text-slate-600">Item Name</th>
                        <th className="text-left p-3 font-medium text-slate-600">SKU</th>
                        <th className="text-right p-3 font-medium text-slate-600">Stock</th>
                        <th className="text-left p-3 font-medium text-slate-600">Unit</th>
                        <th className="text-left p-3 font-medium text-slate-600">Status</th>
                        <th className="text-right p-3 font-medium text-slate-600">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredItems.map((item) => (
                        <tr key={item.id} className="border-b hover:bg-slate-50">
                          <td className="p-3 font-medium">{item.name}</td>
                          <td className="p-3 text-slate-500 font-mono text-xs">{item.sku}</td>
                          <td className="p-3 text-right">{item.stock_quantity}</td>
                          <td className="p-3 text-slate-500">{item.unit}</td>
                          <td className="p-3">
                            {item.stock_quantity <= item.low_stock_threshold ? (
                              <Badge className="bg-red-100 text-red-700">Low Stock</Badge>
                            ) : (
                              <Badge className="bg-green-100 text-green-700">In Stock</Badge>
                            )}
                          </td>
                          <td className="p-3 text-right">
                            <Button size="sm" variant="ghost" onClick={() => handleEditItem(item)}>
                              <Edit2 className="w-4 h-4" />
                            </Button>
                            <Button 
                              size="sm" 
                              variant="ghost" 
                              className="text-red-600 hover:text-red-700"
                              onClick={() => {
                                setDeleteTarget({ type: 'item', id: item.id, name: item.name });
                                setShowDeleteDialog(true);
                              }}
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Packaging Rules Tab */}
        <TabsContent value="rules" className="mt-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-lg">Product Packaging Rules</CardTitle>
              <Button onClick={() => { resetRuleForm(); setShowRuleModal(true); }} data-testid="add-rule-btn">
                <Plus className="w-4 h-4 mr-2" />
                Add Rule
              </Button>
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
                  No packaging rules found. Create rules to assign packaging to products.
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
                                {item.item_name} × {item.quantity}
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
                              setDeleteTarget({ type: 'rule', id: rule.id, name: rule.product_name });
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
        </TabsContent>
      </Tabs>

      {/* Add/Edit Item Modal */}
      <Dialog open={showItemModal} onOpenChange={setShowItemModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editingItem ? 'Edit Packaging Item' : 'Add Packaging Item'}</DialogTitle>
            <DialogDescription>
              {editingItem ? 'Update packaging material details' : 'Create a new packaging material'}
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>Item Name *</Label>
              <Input
                value={itemForm.name}
                onChange={(e) => setItemForm({ ...itemForm, name: e.target.value })}
                placeholder="e.g., Thank You Card Design 1"
                data-testid="item-name-input"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>SKU</Label>
                <Input
                  value={itemForm.sku}
                  onChange={(e) => setItemForm({ ...itemForm, sku: e.target.value })}
                  placeholder="Auto-generated if empty"
                />
              </div>
              <div>
                <Label>Unit</Label>
                <Select value={itemForm.unit} onValueChange={(v) => setItemForm({ ...itemForm, unit: v })}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="pcs">Pieces</SelectItem>
                    <SelectItem value="rolls">Rolls</SelectItem>
                    <SelectItem value="meters">Meters</SelectItem>
                    <SelectItem value="sheets">Sheets</SelectItem>
                    <SelectItem value="boxes">Boxes</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Initial Stock</Label>
                <Input
                  type="number"
                  value={itemForm.stock_quantity}
                  onChange={(e) => setItemForm({ ...itemForm, stock_quantity: parseInt(e.target.value) || 0 })}
                />
              </div>
              <div>
                <Label>Low Stock Alert</Label>
                <Input
                  type="number"
                  value={itemForm.low_stock_threshold}
                  onChange={(e) => setItemForm({ ...itemForm, low_stock_threshold: parseInt(e.target.value) || 10 })}
                />
              </div>
            </div>
            <div>
              <Label>Description</Label>
              <Input
                value={itemForm.description}
                onChange={(e) => setItemForm({ ...itemForm, description: e.target.value })}
                placeholder="Optional description"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowItemModal(false)}>Cancel</Button>
            <Button onClick={handleSaveItem} data-testid="save-item-btn">
              {editingItem ? 'Update' : 'Create'} Item
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Add/Edit Rule Modal */}
      <Dialog open={showRuleModal} onOpenChange={setShowRuleModal}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>{editingRule ? 'Edit Packaging Rule' : 'Create Packaging Rule'}</DialogTitle>
            <DialogDescription>
              Assign packaging materials to a product
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>Product *</Label>
              <Select 
                value={ruleForm.product_id} 
                onValueChange={(v) => setRuleForm({ ...ruleForm, product_id: v })}
                disabled={!!editingRule}
              >
                <SelectTrigger data-testid="product-select">
                  <SelectValue placeholder="Select a product" />
                </SelectTrigger>
                <SelectContent>
                  {products.map(p => (
                    <SelectItem key={p.id} value={p.id}>
                      {p.name} ({p.sku})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label>Add Packaging Items</Label>
              <Select onValueChange={addItemToRule}>
                <SelectTrigger data-testid="add-packaging-select">
                  <SelectValue placeholder="Select item to add" />
                </SelectTrigger>
                <SelectContent>
                  {packagingItems.map(i => (
                    <SelectItem key={i.id} value={i.id}>
                      {i.name} (Stock: {i.stock_quantity})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {ruleForm.items.length > 0 && (
              <div className="border rounded-lg p-3 space-y-2">
                <Label className="text-sm text-slate-500">Packaging Items for this Product:</Label>
                {ruleForm.items.map((item) => (
                  <div key={item.packaging_item_id} className="flex items-center justify-between bg-slate-50 p-2 rounded">
                    <span className="font-medium">{item.item_name}</span>
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-slate-500">Qty:</span>
                      <Input
                        type="number"
                        min="1"
                        value={item.quantity}
                        onChange={(e) => updateRuleItemQty(item.packaging_item_id, e.target.value)}
                        className="w-16 h-8"
                      />
                      <Button 
                        size="sm" 
                        variant="ghost" 
                        className="text-red-600 h-8 w-8 p-0"
                        onClick={() => removeItemFromRule(item.packaging_item_id)}
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
            <AlertDialogTitle>Delete {deleteTarget.type === 'item' ? 'Packaging Item' : 'Packaging Rule'}</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete "{deleteTarget.name}"? This action cannot be undone.
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
