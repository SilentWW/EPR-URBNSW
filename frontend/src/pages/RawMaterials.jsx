import React, { useState, useEffect } from 'react';
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
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '../components/ui/dropdown-menu';
import { 
  Plus, Search, MoreHorizontal, Pencil, Trash2, Loader2, Package, AlertTriangle, 
  PackagePlus, Boxes, Building2
} from 'lucide-react';
import { toast } from 'sonner';

const formatCurrency = (amount) => {
  return new Intl.NumberFormat('en-LK', {
    style: 'currency',
    currency: 'LKR',
    minimumFractionDigits: 0,
  }).format(amount);
};

const UNIT_OPTIONS = [
  { value: 'piece', label: 'Piece' },
  { value: 'meter', label: 'Meter' },
  { value: 'kg', label: 'Kilogram (kg)' },
  { value: 'gram', label: 'Gram' },
  { value: 'liter', label: 'Liter' },
  { value: 'roll', label: 'Roll' },
  { value: 'sheet', label: 'Sheet' },
  { value: 'box', label: 'Box' },
  { value: 'pair', label: 'Pair' },
  { value: 'set', label: 'Set' },
];

const CATEGORY_OPTIONS = [
  'Fabric',
  'Thread',
  'Buttons',
  'Zippers',
  'Labels',
  'Packaging',
  'Accessories',
  'Chemicals',
  'Other'
];

const initialFormData = {
  sku: '',
  name: '',
  description: '',
  category: '',
  unit: 'piece',
  cost_price: '',
  stock_quantity: '',
  low_stock_threshold: '10',
  supplier_id: ''
};

export const RawMaterials = () => {
  const [materials, setMaterials] = useState([]);
  const [categories, setCategories] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [bankAccounts, setBankAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [addStockDialogOpen, setAddStockDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedMaterial, setSelectedMaterial] = useState(null);
  const [formData, setFormData] = useState(initialFormData);
  const [addStockData, setAddStockData] = useState({ quantity: '', cost_price: '', total_cost: '', reference: '', bank_account_id: '' });
  const [submitting, setSubmitting] = useState(false);

  const fetchMaterials = async () => {
    try {
      const params = {};
      if (search) params.search = search;
      if (categoryFilter && categoryFilter !== 'all') params.category = categoryFilter;
      
      const [materialsRes, categoriesRes, suppliersRes, bankAccountsRes] = await Promise.all([
        api.get('/manufacturing/raw-materials', { params }),
        api.get('/manufacturing/raw-materials/categories'),
        api.get('/suppliers'),
        api.get('/bank-accounts')
      ]);
      
      setMaterials(materialsRes.data);
      setCategories(categoriesRes.data);
      setSuppliers(suppliersRes.data);
      setBankAccounts(bankAccountsRes.data || []);
    } catch (error) {
      toast.error('Failed to fetch raw materials');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMaterials();
  }, [search, categoryFilter]);

  const handleOpenDialog = async (material = null) => {
    if (material) {
      setSelectedMaterial(material);
      setFormData({
        sku: material.sku,
        name: material.name,
        description: material.description || '',
        category: material.category || '',
        unit: material.unit || 'piece',
        cost_price: material.cost_price?.toString() || '',
        stock_quantity: material.stock_quantity?.toString() || '',
        low_stock_threshold: material.low_stock_threshold?.toString() || '10',
        supplier_id: material.supplier_id || ''
      });
    } else {
      setSelectedMaterial(null);
      try {
        const skuRes = await api.get('/manufacturing/raw-materials/next-sku');
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

  const handleOpenAddStock = (material) => {
    setSelectedMaterial(material);
    const unitCost = material.cost_price || 0;
    setAddStockData({ 
      quantity: '', 
      cost_price: unitCost.toString(), 
      total_cost: '',
      reference: '',
      bank_account_id: ''
    });
    setAddStockDialogOpen(true);
  };

  // Calculate total cost when quantity or unit price changes
  const handleAddStockQuantityChange = (quantity) => {
    const qty = parseFloat(quantity) || 0;
    const unitPrice = parseFloat(addStockData.cost_price) || 0;
    setAddStockData({ 
      ...addStockData, 
      quantity,
      total_cost: (qty * unitPrice).toFixed(2)
    });
  };

  const handleAddStockCostChange = (cost_price) => {
    const qty = parseFloat(addStockData.quantity) || 0;
    const unitPrice = parseFloat(cost_price) || 0;
    setAddStockData({ 
      ...addStockData, 
      cost_price,
      total_cost: (qty * unitPrice).toFixed(2)
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);

    try {
      const data = {
        ...formData,
        cost_price: parseFloat(formData.cost_price) || 0,
        stock_quantity: parseFloat(formData.stock_quantity) || 0,
        low_stock_threshold: parseFloat(formData.low_stock_threshold) || 10,
        supplier_id: formData.supplier_id || null
      };

      if (selectedMaterial) {
        await api.put(`/manufacturing/raw-materials/${selectedMaterial.id}`, data);
        toast.success('Raw material updated successfully');
      } else {
        await api.post('/manufacturing/raw-materials', data);
        toast.success('Raw material created successfully');
      }

      setDialogOpen(false);
      fetchMaterials();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Operation failed');
    } finally {
      setSubmitting(false);
    }
  };

  const handleAddStock = async (e) => {
    e.preventDefault();
    setSubmitting(true);

    try {
      const params = {
        quantity: parseFloat(addStockData.quantity),
        total_cost: parseFloat(addStockData.total_cost) || 0
      };
      
      if (addStockData.cost_price) {
        params.cost_price = parseFloat(addStockData.cost_price);
      }
      if (addStockData.reference) {
        params.reference = addStockData.reference;
      }
      if (addStockData.bank_account_id && addStockData.bank_account_id !== 'none') {
        params.bank_account_id = addStockData.bank_account_id;
      }
      
      const response = await api.post(`/manufacturing/raw-materials/${selectedMaterial.id}/add-stock`, null, { params });
      
      if (response.data.journal_entry_created) {
        toast.success('Stock added and payment recorded');
      } else {
        toast.success('Stock added successfully');
      }
      setAddStockDialogOpen(false);
      fetchMaterials();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to add stock');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async () => {
    try {
      await api.delete(`/manufacturing/raw-materials/${selectedMaterial.id}`);
      toast.success('Raw material deleted successfully');
      setDeleteDialogOpen(false);
      fetchMaterials();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete raw material');
    }
  };

  const getStockStatus = (quantity, threshold) => {
    if (quantity <= 0) {
      return <Badge className="bg-red-100 text-red-700">Out of Stock</Badge>;
    }
    if (quantity <= threshold) {
      return <Badge className="bg-amber-100 text-amber-700">Low Stock</Badge>;
    }
    return <Badge className="bg-green-100 text-green-700">In Stock</Badge>;
  };

  return (
    <div className="space-y-6" data-testid="raw-materials-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900" style={{ fontFamily: 'Outfit, sans-serif' }}>
            Raw Materials
          </h2>
          <p className="text-slate-500 mt-1">{materials.length} materials in inventory</p>
        </div>
        <Button 
          onClick={() => handleOpenDialog()} 
          className="gap-2 bg-orange-600 hover:bg-orange-700" 
          data-testid="add-raw-material-btn"
        >
          <Plus className="w-4 h-4" />
          Add Raw Material
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <Input
                placeholder="Search raw materials..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9"
                data-testid="search-raw-materials"
              />
            </div>
            <Select value={categoryFilter} onValueChange={setCategoryFilter}>
              <SelectTrigger className="w-full sm:w-48" data-testid="category-filter">
                <SelectValue placeholder="All Categories" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Categories</SelectItem>
                {[...new Set([...categories, ...CATEGORY_OPTIONS])].map((cat) => (
                  <SelectItem key={cat} value={cat}>{cat}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Materials Table */}
      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <Loader2 className="w-8 h-8 animate-spin text-orange-600" />
            </div>
          ) : materials.length === 0 ? (
            <div className="text-center py-16">
              <Boxes className="w-12 h-12 text-slate-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-slate-900">No raw materials found</h3>
              <p className="text-slate-500 mt-1">Get started by adding your first raw material.</p>
              <Button onClick={() => handleOpenDialog()} className="mt-4 bg-orange-600 hover:bg-orange-700">
                Add Raw Material
              </Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="bg-slate-50">
                  <TableHead>Material</TableHead>
                  <TableHead>SKU</TableHead>
                  <TableHead>Category</TableHead>
                  <TableHead>Unit</TableHead>
                  <TableHead className="text-right">Cost Price</TableHead>
                  <TableHead className="text-right">Stock</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="w-12"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {materials.map((material) => (
                  <TableRow key={material.id} data-testid={`material-row-${material.id}`}>
                    <TableCell className="font-medium">
                      <div>
                        {material.name}
                        {material.description && (
                          <p className="text-xs text-slate-400 mt-0.5">{material.description}</p>
                        )}
                      </div>
                    </TableCell>
                    <TableCell className="text-slate-500">{material.sku}</TableCell>
                    <TableCell>
                      {material.category ? (
                        <Badge variant="outline">{material.category}</Badge>
                      ) : (
                        <span className="text-slate-400">-</span>
                      )}
                    </TableCell>
                    <TableCell className="capitalize">{material.unit}</TableCell>
                    <TableCell className="text-right">{formatCurrency(material.cost_price)}</TableCell>
                    <TableCell className="text-right">
                      <span className={material.stock_quantity <= material.low_stock_threshold ? 'text-amber-600 font-medium' : ''}>
                        {material.stock_quantity} {material.unit}
                      </span>
                    </TableCell>
                    <TableCell>{getStockStatus(material.stock_quantity, material.low_stock_threshold)}</TableCell>
                    <TableCell>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon" data-testid={`material-menu-${material.id}`}>
                            <MoreHorizontal className="w-4 h-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => handleOpenAddStock(material)}>
                            <PackagePlus className="w-4 h-4 mr-2" />
                            Add Stock
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => handleOpenDialog(material)}>
                            <Pencil className="w-4 h-4 mr-2" />
                            Edit
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem
                            className="text-red-600"
                            onClick={() => {
                              setSelectedMaterial(material);
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
        <DialogContent className="max-w-lg" data-testid="material-dialog">
          <DialogHeader>
            <DialogTitle style={{ fontFamily: 'Outfit, sans-serif' }}>
              {selectedMaterial ? 'Edit Raw Material' : 'Add Raw Material'}
            </DialogTitle>
            <DialogDescription>
              {selectedMaterial ? 'Update raw material details' : 'Add a new raw material to your inventory'}
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleSubmit}>
            <div className="grid gap-4 py-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="sku">SKU *</Label>
                  <Input
                    id="sku"
                    value={formData.sku}
                    onChange={(e) => setFormData({ ...formData, sku: e.target.value })}
                    required
                    disabled={!!selectedMaterial}
                    placeholder="RM0001"
                    data-testid="material-sku"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="name">Material Name *</Label>
                  <Input
                    id="name"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    required
                    placeholder="Blue Cotton Fabric"
                    data-testid="material-name"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <Input
                  id="description"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Optional description"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Category</Label>
                  <Select
                    value={formData.category}
                    onValueChange={(value) => setFormData({ ...formData, category: value })}
                  >
                    <SelectTrigger data-testid="material-category">
                      <SelectValue placeholder="Select category" />
                    </SelectTrigger>
                    <SelectContent>
                      {CATEGORY_OPTIONS.map((cat) => (
                        <SelectItem key={cat} value={cat}>{cat}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Unit of Measure</Label>
                  <Select
                    value={formData.unit}
                    onValueChange={(value) => setFormData({ ...formData, unit: value })}
                  >
                    <SelectTrigger data-testid="material-unit">
                      <SelectValue placeholder="Select unit" />
                    </SelectTrigger>
                    <SelectContent>
                      {UNIT_OPTIONS.map((unit) => (
                        <SelectItem key={unit.value} value={unit.value}>{unit.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="cost_price">Cost Price</Label>
                  <Input
                    id="cost_price"
                    type="number"
                    step="0.01"
                    value={formData.cost_price}
                    onChange={(e) => setFormData({ ...formData, cost_price: e.target.value })}
                    placeholder="0.00"
                    data-testid="material-cost"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="stock_quantity">Initial Stock</Label>
                  <Input
                    id="stock_quantity"
                    type="number"
                    step="0.01"
                    value={formData.stock_quantity}
                    onChange={(e) => setFormData({ ...formData, stock_quantity: e.target.value })}
                    placeholder="0"
                    data-testid="material-stock"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="low_stock_threshold">Low Stock Alert</Label>
                  <Input
                    id="low_stock_threshold"
                    type="number"
                    step="0.01"
                    value={formData.low_stock_threshold}
                    onChange={(e) => setFormData({ ...formData, low_stock_threshold: e.target.value })}
                    placeholder="10"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label>Supplier (optional)</Label>
                <Select
                  value={formData.supplier_id || "none"}
                  onValueChange={(value) => setFormData({ ...formData, supplier_id: value === "none" ? "" : value })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select supplier" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">No supplier</SelectItem>
                    {suppliers.map((supplier) => (
                      <SelectItem key={supplier.id} value={supplier.id}>{supplier.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={submitting} className="bg-orange-600 hover:bg-orange-700" data-testid="material-submit">
                {submitting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                {selectedMaterial ? 'Update' : 'Create'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Add Stock Dialog */}
      <Dialog open={addStockDialogOpen} onOpenChange={setAddStockDialogOpen}>
        <DialogContent data-testid="add-stock-dialog">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <PackagePlus className="w-5 h-5 text-green-600" />
              Add Stock
            </DialogTitle>
            <DialogDescription>
              Add stock for: <strong>{selectedMaterial?.name}</strong>
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleAddStock}>
            <div className="grid gap-4 py-4">
              <div className="space-y-2">
                <Label>Quantity to Add *</Label>
                <div className="flex gap-2">
                  <Input
                    type="number"
                    step="0.01"
                    value={addStockData.quantity}
                    onChange={(e) => handleAddStockQuantityChange(e.target.value)}
                    required
                    placeholder="Enter quantity"
                    className="flex-1"
                    data-testid="add-stock-quantity"
                  />
                  <span className="flex items-center px-3 bg-slate-100 rounded-md text-sm capitalize">
                    {selectedMaterial?.unit}
                  </span>
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Unit Cost Price</Label>
                  <Input
                    type="number"
                    step="0.01"
                    value={addStockData.cost_price}
                    onChange={(e) => handleAddStockCostChange(e.target.value)}
                    placeholder="0.00"
                    data-testid="add-stock-cost"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Total Cost</Label>
                  <Input
                    type="number"
                    step="0.01"
                    value={addStockData.total_cost}
                    onChange={(e) => setAddStockData({ ...addStockData, total_cost: e.target.value })}
                    placeholder="0.00"
                    className="font-medium"
                    data-testid="add-stock-total"
                  />
                </div>
              </div>
              
              <div className="space-y-2">
                <Label className="flex items-center gap-2">
                  <Building2 className="w-4 h-4" />
                  Pay From Account
                </Label>
                <Select
                  value={addStockData.bank_account_id || "none"}
                  onValueChange={(value) => setAddStockData({ ...addStockData, bank_account_id: value === "none" ? "" : value })}
                >
                  <SelectTrigger data-testid="add-stock-bank">
                    <SelectValue placeholder="Select account (optional)" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">No immediate payment</SelectItem>
                    {bankAccounts.map((account) => (
                      <SelectItem key={account.id} value={account.id}>
                        {account.account_name} ({formatCurrency(account.current_balance)})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <p className="text-xs text-slate-500">
                  {addStockData.bank_account_id && addStockData.bank_account_id !== 'none' 
                    ? 'Payment will be deducted from selected account' 
                    : 'Select an account to record immediate payment'}
                </p>
              </div>
              
              <div className="space-y-2">
                <Label>Reference (optional)</Label>
                <Input
                  value={addStockData.reference}
                  onChange={(e) => setAddStockData({ ...addStockData, reference: e.target.value })}
                  placeholder="e.g., Invoice #123, PO-2026-001"
                />
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setAddStockDialogOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={submitting} className="bg-green-600 hover:bg-green-700" data-testid="confirm-add-stock">
                {submitting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <PackagePlus className="w-4 h-4 mr-2" />}
                Add Stock
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
              Delete Raw Material
            </DialogTitle>
            <DialogDescription>
              Are you sure you want to delete &quot;{selectedMaterial?.name}&quot;? This action cannot be undone.
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

export default RawMaterials;
