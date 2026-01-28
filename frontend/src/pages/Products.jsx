import React, { useState, useEffect } from 'react';
import { productsAPI } from '../lib/api';
import api from '../lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
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
import { Plus, Search, MoreHorizontal, Pencil, Trash2, Loader2, Package, AlertTriangle } from 'lucide-react';
import { toast } from 'sonner';

const formatCurrency = (amount) => {
  return new Intl.NumberFormat('en-LK', {
    style: 'currency',
    currency: 'LKR',
    minimumFractionDigits: 0,
  }).format(amount);
};

const initialFormData = {
  sku: '',
  name: '',
  description: '',
  category: '',
  cost_price: '',
  selling_price: '',
  stock_quantity: '',
  low_stock_threshold: '10',
};

export const Products = () => {
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [formData, setFormData] = useState(initialFormData);
  const [submitting, setSubmitting] = useState(false);

  const fetchProducts = async () => {
    try {
      const params = {};
      if (search) params.search = search;
      if (categoryFilter && categoryFilter !== 'all') params.category = categoryFilter;
      
      const [productsRes, categoriesRes] = await Promise.all([
        productsAPI.getAll(params),
        productsAPI.getCategories(),
      ]);
      setProducts(productsRes.data);
      setCategories(categoriesRes.data);
    } catch (error) {
      toast.error('Failed to fetch products');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProducts();
  }, [search, categoryFilter]);

  const handleOpenDialog = async (product = null) => {
    if (product) {
      setSelectedProduct(product);
      setFormData({
        sku: product.sku,
        name: product.name,
        description: product.description || '',
        category: product.category || '',
        cost_price: product.cost_price.toString(),
        selling_price: product.selling_price.toString(),
        stock_quantity: product.stock_quantity.toString(),
        low_stock_threshold: product.low_stock_threshold.toString(),
      });
    } else {
      setSelectedProduct(null);
      // Fetch next available SKU for new product
      try {
        const skuRes = await api.get('/grn/next-sku');
        setFormData({
          ...initialFormData,
          sku: skuRes.data.next_sku
        });
      } catch (error) {
        setFormData(initialFormData);
      }
    }
    setDialogOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);

    try {
      const data = {
        ...formData,
        cost_price: parseFloat(formData.cost_price) || 0,
        selling_price: parseFloat(formData.selling_price) || 0,
        stock_quantity: parseInt(formData.stock_quantity) || 0,
        low_stock_threshold: parseInt(formData.low_stock_threshold) || 10,
      };

      if (selectedProduct) {
        await productsAPI.update(selectedProduct.id, data);
        toast.success('Product updated successfully');
      } else {
        await productsAPI.create(data);
        toast.success('Product created successfully');
      }

      setDialogOpen(false);
      fetchProducts();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Operation failed');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async () => {
    try {
      await productsAPI.delete(selectedProduct.id);
      toast.success('Product deleted successfully');
      setDeleteDialogOpen(false);
      fetchProducts();
    } catch (error) {
      toast.error('Failed to delete product');
    }
  };

  const getStockStatus = (product) => {
    if (product.stock_quantity <= 0) {
      return <Badge className="badge-error">Out of Stock</Badge>;
    }
    if (product.stock_quantity <= product.low_stock_threshold) {
      return <Badge className="badge-warning">Low Stock</Badge>;
    }
    return <Badge className="badge-success">In Stock</Badge>;
  };

  return (
    <div className="space-y-6" data-testid="products-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900" style={{ fontFamily: 'Outfit, sans-serif' }}>
            Products
          </h2>
          <p className="text-slate-500 mt-1">{products.length} products in inventory</p>
        </div>
        <Button onClick={() => handleOpenDialog()} className="gap-2 bg-indigo-600 hover:bg-indigo-700" data-testid="add-product-btn">
          <Plus className="w-4 h-4" />
          Add Product
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <Input
                placeholder="Search products..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9"
                data-testid="search-products"
              />
            </div>
            <Select value={categoryFilter} onValueChange={setCategoryFilter}>
              <SelectTrigger className="w-full sm:w-48" data-testid="category-filter">
                <SelectValue placeholder="All Categories" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Categories</SelectItem>
                {categories.map((cat) => (
                  <SelectItem key={cat} value={cat}>{cat}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Products Table */}
      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
            </div>
          ) : products.length === 0 ? (
            <div className="text-center py-16">
              <Package className="w-12 h-12 text-slate-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-slate-900">No products found</h3>
              <p className="text-slate-500 mt-1">Get started by adding your first product.</p>
              <Button onClick={() => handleOpenDialog()} className="mt-4 bg-indigo-600 hover:bg-indigo-700">
                Add Product
              </Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="table-header">
                  <TableHead className="table-header-cell">Product</TableHead>
                  <TableHead className="table-header-cell">SKU</TableHead>
                  <TableHead className="table-header-cell">Category</TableHead>
                  <TableHead className="table-header-cell text-right">Cost</TableHead>
                  <TableHead className="table-header-cell text-right">Price</TableHead>
                  <TableHead className="table-header-cell text-right">Stock</TableHead>
                  <TableHead className="table-header-cell">Status</TableHead>
                  <TableHead className="table-header-cell w-12"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {products.map((product) => (
                  <TableRow key={product.id} className="table-row" data-testid={`product-row-${product.id}`}>
                    <TableCell className="table-cell font-medium">{product.name}</TableCell>
                    <TableCell className="table-cell text-slate-500">{product.sku}</TableCell>
                    <TableCell className="table-cell">{product.category || '-'}</TableCell>
                    <TableCell className="table-cell text-right">{formatCurrency(product.cost_price)}</TableCell>
                    <TableCell className="table-cell text-right font-medium">{formatCurrency(product.selling_price)}</TableCell>
                    <TableCell className="table-cell text-right">
                      <span className={product.stock_quantity <= product.low_stock_threshold ? 'text-amber-600 font-medium' : ''}>
                        {product.stock_quantity}
                      </span>
                    </TableCell>
                    <TableCell className="table-cell">{getStockStatus(product)}</TableCell>
                    <TableCell className="table-cell">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon" data-testid={`product-menu-${product.id}`}>
                            <MoreHorizontal className="w-4 h-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => handleOpenDialog(product)}>
                            <Pencil className="w-4 h-4 mr-2" />
                            Edit
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            className="text-red-600"
                            onClick={() => {
                              setSelectedProduct(product);
                              setDeleteDialogOpen(true);
                            }}
                          >
                            <Trash2 className="w-4 h-4 mr-2" />
                            Delete
                          </DropdownMenuItem>
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

      {/* Add/Edit Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-lg" data-testid="product-dialog">
          <DialogHeader>
            <DialogTitle style={{ fontFamily: 'Outfit, sans-serif' }}>
              {selectedProduct ? 'Edit Product' : 'Add New Product'}
            </DialogTitle>
            <DialogDescription>
              {selectedProduct ? 'Update product details' : 'Add a new product to your inventory'}
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleSubmit}>
            <div className="grid gap-4 py-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="sku">SKU {!selectedProduct && '(Auto-generated)'}</Label>
                  <Input
                    id="sku"
                    value={formData.sku}
                    onChange={(e) => setFormData({ ...formData, sku: e.target.value })}
                    required
                    placeholder="URBN0001"
                    data-testid="product-sku"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="category">Category</Label>
                  <Input
                    id="category"
                    value={formData.category}
                    onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                    placeholder="e.g., Electronics"
                    data-testid="product-category"
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="name">Product Name *</Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  required
                  data-testid="product-name"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <Input
                  id="description"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  data-testid="product-description"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="cost_price">Cost Price (LKR)</Label>
                  <Input
                    id="cost_price"
                    type="number"
                    value={formData.cost_price}
                    onChange={(e) => setFormData({ ...formData, cost_price: e.target.value })}
                    data-testid="product-cost"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="selling_price">Selling Price (LKR) *</Label>
                  <Input
                    id="selling_price"
                    type="number"
                    value={formData.selling_price}
                    onChange={(e) => setFormData({ ...formData, selling_price: e.target.value })}
                    required
                    data-testid="product-price"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="stock_quantity">Stock Quantity</Label>
                  <Input
                    id="stock_quantity"
                    type="number"
                    value={formData.stock_quantity}
                    onChange={(e) => setFormData({ ...formData, stock_quantity: e.target.value })}
                    data-testid="product-stock"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="low_stock_threshold">Low Stock Alert</Label>
                  <Input
                    id="low_stock_threshold"
                    type="number"
                    value={formData.low_stock_threshold}
                    onChange={(e) => setFormData({ ...formData, low_stock_threshold: e.target.value })}
                    data-testid="product-threshold"
                  />
                </div>
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={submitting} className="bg-indigo-600 hover:bg-indigo-700" data-testid="product-submit">
                {submitting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                {selectedProduct ? 'Update' : 'Create'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent data-testid="delete-dialog">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-red-600">
              <AlertTriangle className="w-5 h-5" />
              Delete Product
            </DialogTitle>
            <DialogDescription>
              Are you sure you want to delete "{selectedProduct?.name}"? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteDialogOpen(false)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={handleDelete} data-testid="confirm-delete">
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Products;
