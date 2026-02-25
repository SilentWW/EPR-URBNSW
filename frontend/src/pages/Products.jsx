import React, { useState, useEffect } from 'react';
import { productsAPI } from '../lib/api';
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
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '../components/ui/dropdown-menu';
import { 
  Plus, Search, MoreHorizontal, Pencil, Trash2, Loader2, Package, AlertTriangle, 
  RefreshCw, ChevronDown, ChevronRight, Layers, Box 
} from 'lucide-react';
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
  category: '',
  categories: [],
  category_names: [],
};

const initialVariableFormData = {
  name: '',
  sku: '',
  description: '',
  category: '',
  attributes: [],  // Will be populated from WooCommerce
  generate_variations: true,
  sync_to_woo: true
};

export const Products = () => {
  const [products, setProducts] = useState([]);
  const [variations, setVariations] = useState({});
  const [categories, setCategories] = useState([]);
  const [wooCategories, setWooCategories] = useState([]);
  const [wooAttributes, setWooAttributes] = useState([]);  // WooCommerce attributes (Color, Size, etc.)
  const [loadingWooAttributes, setLoadingWooAttributes] = useState(false);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [variableDialogOpen, setVariableDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [formData, setFormData] = useState(initialFormData);
  const [variableFormData, setVariableFormData] = useState(initialVariableFormData);
  const [submitting, setSubmitting] = useState(false);
  const [selectedCategories, setSelectedCategories] = useState([]);
  const [expandedProducts, setExpandedProducts] = useState({});
  const [syncingVariations, setSyncingVariations] = useState(false);
  const [loadingVariations, setLoadingVariations] = useState({});

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

  const fetchWooCategories = async () => {
    try {
      const response = await api.get('/woocommerce/categories');
      setWooCategories(response.data);
    } catch (error) {
      console.error('Failed to fetch WooCommerce categories:', error);
    }
  };

  const fetchWooAttributes = async () => {
    setLoadingWooAttributes(true);
    try {
      const response = await api.get('/woocommerce/attributes');
      setWooAttributes(response.data || []);
    } catch (error) {
      console.error('Failed to fetch WooCommerce attributes:', error);
      setWooAttributes([]);
    } finally {
      setLoadingWooAttributes(false);
    }
  };

  const fetchVariations = async (productId) => {
    setLoadingVariations(prev => ({ ...prev, [productId]: true }));
    try {
      const response = await api.get(`/variations/product/${productId}`);
      setVariations(prev => ({
        ...prev,
        [productId]: response.data.variations
      }));
    } catch (error) {
      console.error('Failed to fetch variations:', error);
      toast.error('Failed to load variations');
    } finally {
      setLoadingVariations(prev => ({ ...prev, [productId]: false }));
    }
  };

  const syncAllVariations = async () => {
    setSyncingVariations(true);
    try {
      await api.post('/variations/sync/all');
      toast.success('Variation sync started. This may take a few minutes.');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to sync variations');
    } finally {
      setSyncingVariations(false);
    }
  };

  const toggleExpanded = (productId) => {
    const isExpanding = !expandedProducts[productId];
    setExpandedProducts(prev => ({
      ...prev,
      [productId]: isExpanding
    }));
    
    // Fetch variations if expanding and not already loaded
    if (isExpanding && !variations[productId]) {
      fetchVariations(productId);
    }
  };

  useEffect(() => {
    fetchProducts();
  }, [search, categoryFilter]);

  useEffect(() => {
    fetchWooCategories();
  }, []);

  const handleOpenDialog = async (product = null) => {
    if (product) {
      setSelectedProduct(product);
      setFormData({
        sku: product.sku,
        name: product.name,
        category: product.category || '',
        categories: product.categories || [],
        category_names: product.category_names || [],
      });
      setSelectedCategories(product.categories || []);
    } else {
      setSelectedProduct(null);
      setSelectedCategories([]);
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

  const handleOpenVariableDialog = async () => {
    try {
      const skuRes = await api.get('/grn/next-sku');
      setVariableFormData({
        ...initialVariableFormData,
        sku: skuRes.data.next_sku
      });
    } catch (error) {
      setVariableFormData(initialVariableFormData);
    }
    setVariableDialogOpen(true);
  };

  const handleVariableAttributeChange = (index, field, value) => {
    const newAttributes = [...variableFormData.attributes];
    newAttributes[index] = { ...newAttributes[index], [field]: value };
    setVariableFormData({ ...variableFormData, attributes: newAttributes });
  };

  const addVariableAttribute = () => {
    setVariableFormData({
      ...variableFormData,
      attributes: [...variableFormData.attributes, { name: '', options: '' }]
    });
  };

  const removeVariableAttribute = (index) => {
    const newAttributes = variableFormData.attributes.filter((_, i) => i !== index);
    setVariableFormData({ ...variableFormData, attributes: newAttributes });
  };

  const handleVariableSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);

    try {
      // Validate attributes
      const validAttributes = variableFormData.attributes
        .filter(attr => attr.name.trim() && attr.options.trim())
        .map(attr => ({
          name: attr.name.trim(),
          options: attr.options.split(',').map(o => o.trim()).filter(o => o)
        }));

      if (validAttributes.length === 0) {
        toast.error('Please add at least one attribute with options');
        setSubmitting(false);
        return;
      }

      const data = {
        name: variableFormData.name,
        sku: variableFormData.sku,
        description: variableFormData.description,
        category: variableFormData.category,
        attributes: validAttributes,
        generate_variations: variableFormData.generate_variations,
        sync_to_woo: variableFormData.sync_to_woo
      };

      const response = await api.post('/variations/variable-product', data);
      
      toast.success(
        `Variable product created with ${response.data.variations_created} variations!` +
        (data.sync_to_woo ? ' Syncing to WooCommerce...' : '')
      );
      
      setVariableDialogOpen(false);
      setVariableFormData(initialVariableFormData);
      fetchProducts();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create variable product');
    } finally {
      setSubmitting(false);
    }
  };

  const handleCategoryToggle = (categoryId, categoryName) => {
    setSelectedCategories(prev => {
      const isSelected = prev.includes(categoryId);
      if (isSelected) {
        const newCategories = prev.filter(id => id !== categoryId);
        const newNames = formData.category_names.filter(name => name !== categoryName);
        setFormData(f => ({ ...f, categories: newCategories, category_names: newNames }));
        return newCategories;
      } else {
        const newCategories = [...prev, categoryId];
        const newNames = [...(formData.category_names || []), categoryName];
        setFormData(f => ({ ...f, categories: newCategories, category_names: newNames }));
        return newCategories;
      }
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);

    try {
      const data = {
        sku: formData.sku,
        name: formData.name,
        category: formData.category || (formData.category_names && formData.category_names[0]) || '',
        categories: selectedCategories,
        category_names: formData.category_names || [],
        cost_price: 0,
        selling_price: 0,
        stock_quantity: 0,
        low_stock_threshold: 10,
      };

      if (selectedProduct) {
        await productsAPI.update(selectedProduct.id, {
          name: formData.name,
          category: formData.category || (formData.category_names && formData.category_names[0]) || '',
          categories: selectedCategories,
          category_names: formData.category_names || []
        });
        if (selectedProduct.woo_product_id) {
          toast.success('Product updated & synced to WooCommerce');
        } else {
          toast.success('Product updated successfully');
        }
      } else {
        await productsAPI.create(data);
        toast.success('Product created successfully');
      }

      setDialogOpen(false);
      setSelectedCategories([]);
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

  const getStockStatus = (quantity, threshold) => {
    if (quantity <= 0) {
      return <Badge className="badge-error">Out of Stock</Badge>;
    }
    if (quantity <= threshold) {
      return <Badge className="badge-warning">Low Stock</Badge>;
    }
    return <Badge className="badge-success">In Stock</Badge>;
  };

  const getProductTypeBadge = (product) => {
    if (product.product_type === 'variable') {
      return <Badge variant="outline" className="text-purple-600 border-purple-200 bg-purple-50">Variable</Badge>;
    }
    return <Badge variant="outline" className="text-gray-600">Simple</Badge>;
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
        <div className="flex gap-2 flex-wrap">
          <Button 
            variant="outline" 
            onClick={syncAllVariations}
            disabled={syncingVariations}
            className="gap-2"
            data-testid="sync-variations-btn"
          >
            {syncingVariations ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
            Sync from WooCommerce
          </Button>
          <Button 
            onClick={handleOpenVariableDialog} 
            className="gap-2 bg-purple-600 hover:bg-purple-700" 
            data-testid="add-variable-product-btn"
          >
            <Layers className="w-4 h-4" />
            Create Variable Product
          </Button>
          <Button onClick={() => handleOpenDialog()} className="gap-2 bg-indigo-600 hover:bg-indigo-700" data-testid="add-product-btn">
            <Plus className="w-4 h-4" />
            Add Simple Product
          </Button>
        </div>
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
                  <TableHead className="table-header-cell w-8"></TableHead>
                  <TableHead className="table-header-cell">Product</TableHead>
                  <TableHead className="table-header-cell">SKU</TableHead>
                  <TableHead className="table-header-cell">Type</TableHead>
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
                  <React.Fragment key={product.id}>
                    {/* Main Product Row */}
                    <TableRow className="table-row" data-testid={`product-row-${product.id}`}>
                      <TableCell className="table-cell">
                        {product.product_type === 'variable' ? (
                          <Button
                            variant="ghost"
                            size="sm"
                            className="p-0 h-6 w-6"
                            onClick={() => toggleExpanded(product.id)}
                            data-testid={`expand-btn-${product.id}`}
                          >
                            {expandedProducts[product.id] ? (
                              <ChevronDown className="w-4 h-4" />
                            ) : (
                              <ChevronRight className="w-4 h-4" />
                            )}
                          </Button>
                        ) : (
                          <Box className="w-4 h-4 text-slate-300" />
                        )}
                      </TableCell>
                      <TableCell className="table-cell font-medium">{product.name}</TableCell>
                      <TableCell className="table-cell text-slate-500">{product.sku}</TableCell>
                      <TableCell className="table-cell">{getProductTypeBadge(product)}</TableCell>
                      <TableCell className="table-cell">
                        {product.category_names && product.category_names.length > 0 ? (
                          <div className="flex flex-wrap gap-1">
                            {product.category_names.map((cat, idx) => (
                              <Badge key={idx} variant="outline" className="text-xs">
                                {cat}
                              </Badge>
                            ))}
                          </div>
                        ) : product.category ? (
                          <Badge variant="outline" className="text-xs">{product.category}</Badge>
                        ) : (
                          <span className="text-gray-400">-</span>
                        )}
                      </TableCell>
                      <TableCell className="table-cell text-right">{formatCurrency(product.cost_price)}</TableCell>
                      <TableCell className="table-cell text-right font-medium">{formatCurrency(product.selling_price)}</TableCell>
                      <TableCell className="table-cell text-right">
                        <span className={product.stock_quantity <= product.low_stock_threshold ? 'text-amber-600 font-medium' : ''}>
                          {product.stock_quantity}
                        </span>
                      </TableCell>
                      <TableCell className="table-cell">{getStockStatus(product.stock_quantity, product.low_stock_threshold)}</TableCell>
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
                            {product.product_type === 'variable' && product.woo_product_id && (
                              <DropdownMenuItem onClick={() => {
                                api.post(`/variations/sync/product/${product.id}`)
                                  .then(() => {
                                    toast.success('Syncing variations...');
                                    setTimeout(() => fetchVariations(product.id), 3000);
                                  })
                                  .catch(() => toast.error('Sync failed'));
                              }}>
                                <RefreshCw className="w-4 h-4 mr-2" />
                                Sync Variations
                              </DropdownMenuItem>
                            )}
                            <DropdownMenuSeparator />
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

                    {/* Variations Rows (Expanded) */}
                    {expandedProducts[product.id] && (
                      <>
                        {loadingVariations[product.id] ? (
                          <TableRow className="bg-slate-50">
                            <TableCell colSpan={10} className="py-4 text-center">
                              <Loader2 className="w-5 h-5 animate-spin mx-auto text-indigo-600" />
                              <span className="text-sm text-slate-500 ml-2">Loading variations...</span>
                            </TableCell>
                          </TableRow>
                        ) : variations[product.id]?.length > 0 ? (
                          variations[product.id].map((variation) => (
                            <TableRow 
                              key={variation.id} 
                              className="bg-slate-50 border-l-4 border-l-purple-200"
                              data-testid={`variation-row-${variation.id}`}
                            >
                              <TableCell className="table-cell">
                                <Layers className="w-4 h-4 text-purple-400 ml-2" />
                              </TableCell>
                              <TableCell className="table-cell pl-8">
                                <div className="flex flex-col">
                                  <span className="font-medium text-slate-700">{variation.variation_name}</span>
                                  <div className="flex gap-1 mt-1">
                                    {variation.attributes?.map((attr, idx) => (
                                      <Badge key={idx} variant="secondary" className="text-xs">
                                        {attr.name}: {attr.option}
                                      </Badge>
                                    ))}
                                  </div>
                                </div>
                              </TableCell>
                              <TableCell className="table-cell text-slate-500">{variation.sku}</TableCell>
                              <TableCell className="table-cell">
                                <Badge variant="outline" className="text-purple-500 text-xs">Variation</Badge>
                              </TableCell>
                              <TableCell className="table-cell text-slate-400">-</TableCell>
                              <TableCell className="table-cell text-right">{formatCurrency(variation.cost_price)}</TableCell>
                              <TableCell className="table-cell text-right font-medium">{formatCurrency(variation.selling_price)}</TableCell>
                              <TableCell className="table-cell text-right">
                                <span className={variation.stock_quantity <= 5 ? 'text-amber-600 font-medium' : ''}>
                                  {variation.stock_quantity}
                                </span>
                              </TableCell>
                              <TableCell className="table-cell">{getStockStatus(variation.stock_quantity, 5)}</TableCell>
                              <TableCell className="table-cell"></TableCell>
                            </TableRow>
                          ))
                        ) : (
                          <TableRow className="bg-slate-50">
                            <TableCell colSpan={10} className="py-4 text-center text-slate-500">
                              No variations found. Click &quot;Sync Variations&quot; to fetch from WooCommerce.
                            </TableCell>
                          </TableRow>
                        )}
                      </>
                    )}
                  </React.Fragment>
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
              {selectedProduct ? 'Update product details' : 'Create product placeholder - add stock via GRN'}
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
                    disabled={!!selectedProduct}
                    placeholder="URBN0001"
                    data-testid="product-sku"
                    className={selectedProduct ? 'bg-slate-100' : ''}
                  />
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
              </div>
              <div className="space-y-2">
                <Label>Product Categories (Select Multiple)</Label>
                <div className="border rounded-lg p-3 max-h-48 overflow-y-auto bg-slate-50">
                  {wooCategories.length > 0 ? (
                    <div className="grid grid-cols-2 gap-2">
                      {wooCategories.map((cat) => (
                        <label 
                          key={cat.woo_id || cat.id} 
                          className="flex items-center gap-2 p-2 rounded hover:bg-white cursor-pointer"
                        >
                          <input
                            type="checkbox"
                            checked={selectedCategories.includes(cat.woo_id || String(cat.id))}
                            onChange={() => handleCategoryToggle(cat.woo_id || String(cat.id), cat.name)}
                            className="w-4 h-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                          />
                          <span className="text-sm">{cat.name}</span>
                          {cat.count > 0 && (
                            <span className="text-xs text-gray-400">({cat.count})</span>
                          )}
                        </label>
                      ))}
                    </div>
                  ) : categories.length > 0 ? (
                    <div className="grid grid-cols-2 gap-2">
                      {categories.map((cat, idx) => (
                        <label 
                          key={idx} 
                          className="flex items-center gap-2 p-2 rounded hover:bg-white cursor-pointer"
                        >
                          <input
                            type="checkbox"
                            checked={selectedCategories.includes(String(idx))}
                            onChange={() => handleCategoryToggle(String(idx), cat)}
                            className="w-4 h-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                          />
                          <span className="text-sm">{cat}</span>
                        </label>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-gray-500 text-center py-4">
                      No categories found. Sync from WooCommerce or create products with categories.
                    </p>
                  )}
                </div>
                {selectedCategories.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {formData.category_names?.map((name, idx) => (
                      <Badge key={idx} variant="secondary" className="text-xs">
                        {name}
                      </Badge>
                    ))}
                  </div>
                )}
              </div>
              <p className="text-sm text-slate-500 bg-blue-50 p-3 rounded-lg">
                💡 Cost price, selling price, and stock quantity are set when receiving goods via GRN (Goods Received Note).
              </p>
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
              Are you sure you want to delete &quot;{selectedProduct?.name}&quot;? This action cannot be undone.
              {selectedProduct?.product_type === 'variable' && (
                <span className="block mt-2 text-amber-600">
                  Warning: This will also delete all associated variations.
                </span>
              )}
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

      {/* Create Variable Product Dialog */}
      <Dialog open={variableDialogOpen} onOpenChange={setVariableDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto" data-testid="variable-product-dialog">
          <DialogHeader>
            <DialogTitle style={{ fontFamily: 'Outfit, sans-serif' }} className="flex items-center gap-2">
              <Layers className="w-5 h-5 text-purple-600" />
              Create Variable Product
            </DialogTitle>
            <DialogDescription>
              Create a product with variations (e.g., different colors and sizes). 
              All variation combinations will be auto-generated.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleVariableSubmit}>
            <div className="grid gap-4 py-4">
              {/* Basic Info */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="var-sku">SKU (Base) *</Label>
                  <Input
                    id="var-sku"
                    value={variableFormData.sku}
                    onChange={(e) => setVariableFormData({ ...variableFormData, sku: e.target.value })}
                    required
                    placeholder="TROUSER-001"
                    data-testid="variable-product-sku"
                  />
                  <p className="text-xs text-slate-400">Variations will have suffixes like -BLU-S, -BLK-M</p>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="var-name">Product Name *</Label>
                  <Input
                    id="var-name"
                    value={variableFormData.name}
                    onChange={(e) => setVariableFormData({ ...variableFormData, name: e.target.value })}
                    required
                    placeholder="Classic Trouser"
                    data-testid="variable-product-name"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="var-desc">Description</Label>
                <Input
                  id="var-desc"
                  value={variableFormData.description}
                  onChange={(e) => setVariableFormData({ ...variableFormData, description: e.target.value })}
                  placeholder="Product description for WooCommerce"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="var-cat">Category</Label>
                <Select
                  value={variableFormData.category}
                  onValueChange={(value) => setVariableFormData({ ...variableFormData, category: value })}
                >
                  <SelectTrigger data-testid="variable-product-category">
                    <SelectValue placeholder="Select category" />
                  </SelectTrigger>
                  <SelectContent>
                    {wooCategories.length > 0 ? (
                      wooCategories.map((cat) => (
                        <SelectItem key={cat.woo_id || cat.id} value={cat.name}>
                          {cat.name}
                        </SelectItem>
                      ))
                    ) : categories.length > 0 ? (
                      categories.map((cat, idx) => (
                        <SelectItem key={idx} value={cat}>{cat}</SelectItem>
                      ))
                    ) : (
                      <SelectItem value="Clothing">Clothing</SelectItem>
                    )}
                  </SelectContent>
                </Select>
              </div>

              {/* Attributes Section */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <Label className="text-base font-medium">Variation Attributes</Label>
                  <Button 
                    type="button" 
                    variant="outline" 
                    size="sm" 
                    onClick={addVariableAttribute}
                    className="gap-1"
                  >
                    <Plus className="w-3 h-3" /> Add Attribute
                  </Button>
                </div>
                <p className="text-sm text-slate-500">
                  Define attributes like Color, Size. Enter options separated by commas.
                </p>
                
                <div className="space-y-3 border rounded-lg p-4 bg-slate-50">
                  {variableFormData.attributes.map((attr, idx) => (
                    <div key={idx} className="flex gap-3 items-start">
                      <div className="flex-1">
                        <Label className="text-xs text-slate-500">Attribute Name</Label>
                        <Input
                          value={attr.name}
                          onChange={(e) => handleVariableAttributeChange(idx, 'name', e.target.value)}
                          placeholder="e.g., Color, Size"
                          data-testid={`attr-name-${idx}`}
                        />
                      </div>
                      <div className="flex-[2]">
                        <Label className="text-xs text-slate-500">Options (comma separated)</Label>
                        <Input
                          value={attr.options}
                          onChange={(e) => handleVariableAttributeChange(idx, 'options', e.target.value)}
                          placeholder="e.g., Blue, Black, Red or S, M, L, XL"
                          data-testid={`attr-options-${idx}`}
                        />
                      </div>
                      {variableFormData.attributes.length > 1 && (
                        <Button
                          type="button"
                          variant="ghost"
                          size="icon"
                          onClick={() => removeVariableAttribute(idx)}
                          className="mt-5 text-red-500 hover:text-red-600"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      )}
                    </div>
                  ))}
                </div>

                {/* Preview */}
                {variableFormData.attributes.filter(a => a.name && a.options).length > 0 && (
                  <div className="bg-purple-50 border border-purple-200 rounded-lg p-3">
                    <p className="text-sm font-medium text-purple-700 mb-2">Preview: Variations to be created</p>
                    <div className="flex flex-wrap gap-1">
                      {(() => {
                        const validAttrs = variableFormData.attributes
                          .filter(a => a.name.trim() && a.options.trim())
                          .map(a => ({
                            name: a.name,
                            options: a.options.split(',').map(o => o.trim()).filter(o => o)
                          }));
                        
                        if (validAttrs.length === 0) return null;
                        
                        // Calculate total combinations
                        const totalCombos = validAttrs.reduce((acc, attr) => acc * attr.options.length, 1);
                        
                        // Show first few combinations
                        const firstOptions = validAttrs.map(a => a.options.slice(0, 2));
                        const sampleCombos = [];
                        
                        const generateSamples = (current, attrIdx) => {
                          if (attrIdx >= firstOptions.length) {
                            sampleCombos.push(current.join(' - '));
                            return;
                          }
                          for (const opt of firstOptions[attrIdx]) {
                            if (sampleCombos.length < 4) {
                              generateSamples([...current, opt], attrIdx + 1);
                            }
                          }
                        };
                        generateSamples([], 0);
                        
                        return (
                          <>
                            {sampleCombos.map((combo, i) => (
                              <Badge key={i} variant="secondary" className="text-xs">
                                {variableFormData.name || 'Product'} - {combo}
                              </Badge>
                            ))}
                            {totalCombos > 4 && (
                              <Badge variant="outline" className="text-xs text-purple-600">
                                +{totalCombos - 4} more
                              </Badge>
                            )}
                            <span className="text-xs text-purple-600 ml-2">
                              Total: {totalCombos} variations
                            </span>
                          </>
                        );
                      })()}
                    </div>
                  </div>
                )}
              </div>

              {/* Options */}
              <div className="flex items-center gap-4 pt-2">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={variableFormData.sync_to_woo}
                    onChange={(e) => setVariableFormData({ ...variableFormData, sync_to_woo: e.target.checked })}
                    className="w-4 h-4 rounded border-gray-300 text-purple-600 focus:ring-purple-500"
                  />
                  <span className="text-sm">Sync to WooCommerce</span>
                </label>
              </div>

              <p className="text-sm text-slate-500 bg-purple-50 p-3 rounded-lg">
                💡 After creating, use Purchase Orders and GRN to add stock and set prices for each variation.
              </p>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setVariableDialogOpen(false)}>
                Cancel
              </Button>
              <Button 
                type="submit" 
                disabled={submitting} 
                className="bg-purple-600 hover:bg-purple-700" 
                data-testid="variable-product-submit"
              >
                {submitting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Layers className="w-4 h-4 mr-2" />}
                Create Variable Product
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Products;
