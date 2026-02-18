import React, { useState, useEffect } from 'react';
import api from '../lib/api';
import { toast } from 'sonner';
import {
  Package,
  Plus,
  Pencil,
  Trash2,
  Loader2,
  AlertTriangle,
  Check,
  X,
  Box,
  ShoppingBag
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
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
import { Badge } from '../components/ui/badge';
import { Switch } from '../components/ui/switch';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle
} from '../components/ui/alert-dialog';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow
} from '../components/ui/table';

const formatCurrency = (amount) => {
  return new Intl.NumberFormat('en-LK', {
    style: 'currency',
    currency: 'LKR',
    minimumFractionDigits: 2
  }).format(amount || 0);
};

export default function PackagingItems() {
  const [packagingItems, setPackagingItems] = useState([]);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [itemToDelete, setItemToDelete] = useState(null);
  
  const [formData, setFormData] = useState({
    product_id: '',
    name: '',
    description: '',
    is_active: true
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [itemsRes, productsRes] = await Promise.all([
        api.get('/packaging-items'),
        api.get('/products')
      ]);
      setPackagingItems(itemsRes.data);
      setProducts(productsRes.data);
    } catch (error) {
      toast.error('Failed to fetch data');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenDialog = (item = null) => {
    if (item) {
      setEditingItem(item);
      setFormData({
        product_id: item.product_id,
        name: item.name,
        description: item.description || '',
        is_active: item.is_active
      });
    } else {
      setEditingItem(null);
      setFormData({
        product_id: '',
        name: '',
        description: '',
        is_active: true
      });
    }
    setDialogOpen(true);
  };

  const handleProductChange = (productId) => {
    const product = products.find(p => p.id === productId);
    setFormData({
      ...formData,
      product_id: productId,
      name: product ? product.name : ''
    });
  };

  const handleSubmit = async () => {
    if (!formData.product_id || !formData.name) {
      toast.error('Please fill in all required fields');
      return;
    }

    setSubmitting(true);
    try {
      if (editingItem) {
        await api.put(`/packaging-items/${editingItem.id}`, formData);
        toast.success('Packaging item updated');
      } else {
        await api.post('/packaging-items', formData);
        toast.success('Packaging item added');
      }
      setDialogOpen(false);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save packaging item');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async () => {
    if (!itemToDelete) return;
    
    try {
      await api.delete(`/packaging-items/${itemToDelete.id}`);
      toast.success('Packaging item removed');
      setDeleteDialogOpen(false);
      setItemToDelete(null);
      fetchData();
    } catch (error) {
      toast.error('Failed to delete packaging item');
    }
  };

  const handleToggleActive = async (item) => {
    try {
      await api.put(`/packaging-items/${item.id}`, {
        is_active: !item.is_active
      });
      toast.success(item.is_active ? 'Item deactivated' : 'Item activated');
      fetchData();
    } catch (error) {
      toast.error('Failed to update status');
    }
  };

  // Get available products (not already configured as packaging)
  const availableProducts = products.filter(
    p => !packagingItems.some(pkg => pkg.product_id === p.id) || 
         (editingItem && editingItem.product_id === p.id)
  );

  // Calculate totals
  const totalValue = packagingItems
    .filter(item => item.is_active)
    .reduce((sum, item) => sum + (item.cost_price || 0) * (item.stock_quantity || 0), 0);

  const totalCostPerSale = packagingItems
    .filter(item => item.is_active)
    .reduce((sum, item) => sum + (item.cost_price || 0), 0);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold" style={{ fontFamily: 'Outfit, sans-serif' }}>
            Packaging Items
          </h1>
          <p className="text-gray-500 text-sm mt-1">
            Configure items that are automatically deducted with every sale
          </p>
        </div>
        <Button onClick={() => handleOpenDialog()} className="bg-indigo-600 hover:bg-indigo-700">
          <Plus className="w-4 h-4 mr-2" />
          Add Packaging Item
        </Button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Active Items</p>
                <p className="text-2xl font-bold text-indigo-600">
                  {packagingItems.filter(i => i.is_active).length}
                </p>
              </div>
              <Package className="w-10 h-10 text-indigo-200" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Total Inventory Value</p>
                <p className="text-2xl font-bold text-green-600">
                  {formatCurrency(totalValue)}
                </p>
              </div>
              <Box className="w-10 h-10 text-green-200" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Packaging Cost per Sale</p>
                <p className="text-2xl font-bold text-amber-600">
                  {formatCurrency(totalCostPerSale)}
                </p>
              </div>
              <ShoppingBag className="w-10 h-10 text-amber-200" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Info Box */}
      <Card className="bg-blue-50 border-blue-200">
        <CardContent className="pt-4">
          <div className="flex gap-3">
            <Package className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-blue-800">
              <p className="font-medium">How it works:</p>
              <ul className="mt-1 space-y-1 list-disc list-inside text-blue-700">
                <li>When a customer buys products, each active packaging item's inventory is reduced by the <strong>total quantity of products sold</strong></li>
                <li>Example: Customer buys 3 T-shirts → 3 ziplock bags, 3 courier bags, 3 thank you cards are deducted</li>
                <li>Packaging costs are automatically added to <strong>Cost of Goods Sold (COGS)</strong> in your accounting</li>
                <li>Add products to your inventory first, then configure them here as packaging items</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Packaging Items Table */}
      <Card>
        <CardHeader>
          <CardTitle>Configured Packaging Items</CardTitle>
          <CardDescription>
            These items will be automatically deducted when sales are made
          </CardDescription>
        </CardHeader>
        <CardContent>
          {packagingItems.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <Package className="w-12 h-12 mx-auto mb-4 text-gray-300" />
              <p>No packaging items configured yet</p>
              <p className="text-sm mt-1">Add packaging items to automatically track their usage with sales</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Item Name</TableHead>
                  <TableHead>Product SKU</TableHead>
                  <TableHead className="text-right">Stock</TableHead>
                  <TableHead className="text-right">Cost Price</TableHead>
                  <TableHead className="text-right">Total Value</TableHead>
                  <TableHead className="text-center">Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {packagingItems.map((item) => (
                  <TableRow key={item.id} className={!item.is_active ? 'opacity-50' : ''}>
                    <TableCell>
                      <div>
                        <p className="font-medium">{item.name}</p>
                        {item.description && (
                          <p className="text-xs text-gray-500">{item.description}</p>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <code className="text-xs bg-gray-100 px-2 py-1 rounded">
                        {item.product_sku || 'N/A'}
                      </code>
                    </TableCell>
                    <TableCell className="text-right">
                      <span className={item.stock_quantity < 10 ? 'text-red-600 font-medium' : ''}>
                        {item.stock_quantity || 0}
                      </span>
                      {item.stock_quantity < 10 && (
                        <AlertTriangle className="w-4 h-4 text-amber-500 inline ml-1" />
                      )}
                    </TableCell>
                    <TableCell className="text-right">
                      {formatCurrency(item.cost_price)}
                    </TableCell>
                    <TableCell className="text-right">
                      {formatCurrency((item.cost_price || 0) * (item.stock_quantity || 0))}
                    </TableCell>
                    <TableCell className="text-center">
                      <Switch
                        checked={item.is_active}
                        onCheckedChange={() => handleToggleActive(item)}
                      />
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleOpenDialog(item)}
                        >
                          <Pencil className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-red-600 hover:text-red-700"
                          onClick={() => {
                            setItemToDelete(item);
                            setDeleteDialogOpen(true);
                          }}
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Add/Edit Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle style={{ fontFamily: 'Outfit, sans-serif' }}>
              {editingItem ? 'Edit Packaging Item' : 'Add Packaging Item'}
            </DialogTitle>
            <DialogDescription>
              {editingItem 
                ? 'Update the packaging item configuration'
                : 'Select a product from your inventory to configure as a packaging item'
              }
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Select Product *</Label>
              <Select 
                value={formData.product_id} 
                onValueChange={handleProductChange}
              >
                <SelectTrigger data-testid="select-packaging-product">
                  <SelectValue placeholder="Choose a product from inventory" />
                </SelectTrigger>
                <SelectContent>
                  {availableProducts.map((product) => (
                    <SelectItem key={product.id} value={product.id}>
                      <div className="flex justify-between items-center w-full">
                        <span>{product.name}</span>
                        <span className="text-gray-500 text-xs ml-2">
                          Stock: {product.stock_quantity} | Cost: {formatCurrency(product.cost_price)}
                        </span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className="text-xs text-gray-500">
                Product must exist in inventory with a cost price set from GRN
              </p>
            </div>
            
            <div className="space-y-2">
              <Label>Display Name *</Label>
              <Input
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="e.g., Black Frosted Ziplock Bag"
              />
            </div>
            
            <div className="space-y-2">
              <Label>Description</Label>
              <Textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="Optional description..."
                rows={2}
              />
            </div>
            
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div>
                <p className="font-medium">Active</p>
                <p className="text-xs text-gray-500">
                  Only active items are deducted from inventory on sales
                </p>
              </div>
              <Switch
                checked={formData.is_active}
                onCheckedChange={(checked) => setFormData({ ...formData, is_active: checked })}
              />
            </div>
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)}>
              Cancel
            </Button>
            <Button 
              onClick={handleSubmit} 
              disabled={submitting}
              className="bg-indigo-600 hover:bg-indigo-700"
            >
              {submitting && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
              {editingItem ? 'Update' : 'Add'} Item
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Remove Packaging Item?</AlertDialogTitle>
            <AlertDialogDescription>
              This will remove "{itemToDelete?.name}" from your packaging items configuration.
              The product will remain in your inventory.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              className="bg-red-600 hover:bg-red-700"
            >
              Remove
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
