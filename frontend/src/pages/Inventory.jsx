import React, { useState, useEffect } from 'react';
import { inventoryAPI, productsAPI } from '../lib/api';
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Plus, Loader2, Boxes, ArrowDownToLine, ArrowUpFromLine, RefreshCw, Package } from 'lucide-react';
import { toast } from 'sonner';

const formatCurrency = (amount) => {
  return new Intl.NumberFormat('en-LK', {
    style: 'currency',
    currency: 'LKR',
    minimumFractionDigits: 0,
  }).format(amount);
};

export const Inventory = () => {
  const [movements, setMovements] = useState([]);
  const [valuation, setValuation] = useState(null);
  const [lowStock, setLowStock] = useState([]);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const [formData, setFormData] = useState({
    product_id: '',
    movement_type: 'in',
    quantity: '',
    reason: '',
  });

  const fetchData = async () => {
    try {
      const [movementsRes, valuationRes, lowStockRes, productsRes] = await Promise.all([
        inventoryAPI.getMovements(),
        inventoryAPI.getValuation(),
        inventoryAPI.getLowStock(),
        productsAPI.getAll(),
      ]);
      setMovements(movementsRes.data);
      setValuation(valuationRes.data);
      setLowStock(lowStockRes.data);
      setProducts(productsRes.data);
    } catch (error) {
      toast.error('Failed to fetch inventory data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);

    try {
      await inventoryAPI.createMovement({
        ...formData,
        quantity: parseInt(formData.quantity),
      });
      toast.success('Inventory movement recorded');
      setDialogOpen(false);
      setFormData({ product_id: '', movement_type: 'in', quantity: '', reason: '' });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to record movement');
    } finally {
      setSubmitting(false);
    }
  };

  const getMovementIcon = (type) => {
    switch (type) {
      case 'in':
        return <ArrowDownToLine className="w-4 h-4 text-emerald-600" />;
      case 'out':
        return <ArrowUpFromLine className="w-4 h-4 text-red-600" />;
      default:
        return <RefreshCw className="w-4 h-4 text-blue-600" />;
    }
  };

  const getMovementBadge = (type) => {
    switch (type) {
      case 'in':
        return <Badge className="badge-success">Stock In</Badge>;
      case 'out':
        return <Badge className="badge-error">Stock Out</Badge>;
      default:
        return <Badge className="badge-neutral">Adjustment</Badge>;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="inventory-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900" style={{ fontFamily: 'Outfit, sans-serif' }}>
            Inventory
          </h2>
          <p className="text-slate-500 mt-1">Manage stock levels and movements</p>
        </div>
        <Button onClick={() => setDialogOpen(true)} className="gap-2 bg-indigo-600 hover:bg-indigo-700" data-testid="add-movement-btn">
          <Plus className="w-4 h-4" />
          Add Movement
        </Button>
      </div>

      {/* Valuation Cards */}
      {valuation && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card className="stat-card">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm font-medium text-slate-500">Total Products</p>
                <p className="text-2xl font-bold text-slate-900 mt-1">{valuation.total_products}</p>
              </div>
              <div className="stat-icon bg-indigo-600">
                <Package className="w-6 h-6 text-white" />
              </div>
            </div>
          </Card>
          <Card className="stat-card">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm font-medium text-slate-500">Total Items</p>
                <p className="text-2xl font-bold text-slate-900 mt-1">{valuation.total_items.toLocaleString()}</p>
              </div>
              <div className="stat-icon bg-emerald-600">
                <Boxes className="w-6 h-6 text-white" />
              </div>
            </div>
          </Card>
          <Card className="stat-card">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm font-medium text-slate-500">Cost Value</p>
                <p className="text-2xl font-bold text-slate-900 mt-1">{formatCurrency(valuation.total_cost_value)}</p>
              </div>
              <div className="stat-icon bg-blue-600">
                <ArrowDownToLine className="w-6 h-6 text-white" />
              </div>
            </div>
          </Card>
          <Card className="stat-card">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm font-medium text-slate-500">Retail Value</p>
                <p className="text-2xl font-bold text-slate-900 mt-1">{formatCurrency(valuation.total_retail_value)}</p>
              </div>
              <div className="stat-icon bg-violet-600">
                <ArrowUpFromLine className="w-6 h-6 text-white" />
              </div>
            </div>
          </Card>
        </div>
      )}

      <Tabs defaultValue="movements" className="space-y-4">
        <TabsList>
          <TabsTrigger value="movements" data-testid="movements-tab">Movements</TabsTrigger>
          <TabsTrigger value="low-stock" data-testid="low-stock-tab">
            Low Stock ({lowStock.length})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="movements">
          <Card>
            <CardContent className="p-0">
              {movements.length === 0 ? (
                <div className="text-center py-16">
                  <Boxes className="w-12 h-12 text-slate-300 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-slate-900">No movements recorded</h3>
                  <p className="text-slate-500 mt-1">Stock movements will appear here.</p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow className="table-header">
                      <TableHead className="table-header-cell">Date</TableHead>
                      <TableHead className="table-header-cell">Product</TableHead>
                      <TableHead className="table-header-cell">Type</TableHead>
                      <TableHead className="table-header-cell text-right">Qty</TableHead>
                      <TableHead className="table-header-cell text-right">Before</TableHead>
                      <TableHead className="table-header-cell text-right">After</TableHead>
                      <TableHead className="table-header-cell">Reason</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {movements.slice(0, 50).map((movement) => (
                      <TableRow key={movement.id} className="table-row">
                        <TableCell className="table-cell text-slate-500">
                          {new Date(movement.created_at).toLocaleDateString()}
                        </TableCell>
                        <TableCell className="table-cell font-medium">{movement.product_name}</TableCell>
                        <TableCell className="table-cell">{getMovementBadge(movement.movement_type)}</TableCell>
                        <TableCell className="table-cell text-right">
                          <span className={movement.movement_type === 'in' ? 'text-emerald-600' : movement.movement_type === 'out' ? 'text-red-600' : ''}>
                            {movement.movement_type === 'in' ? '+' : movement.movement_type === 'out' ? '-' : ''}
                            {movement.quantity}
                          </span>
                        </TableCell>
                        <TableCell className="table-cell text-right text-slate-500">{movement.previous_stock}</TableCell>
                        <TableCell className="table-cell text-right font-medium">{movement.new_stock}</TableCell>
                        <TableCell className="table-cell text-slate-500 max-w-xs truncate">{movement.reason}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="low-stock">
          <Card>
            <CardContent className="p-0">
              {lowStock.length === 0 ? (
                <div className="text-center py-16">
                  <Package className="w-12 h-12 text-slate-300 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-slate-900">All stocked up!</h3>
                  <p className="text-slate-500 mt-1">No products are running low.</p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow className="table-header">
                      <TableHead className="table-header-cell">Product</TableHead>
                      <TableHead className="table-header-cell">SKU</TableHead>
                      <TableHead className="table-header-cell">Category</TableHead>
                      <TableHead className="table-header-cell text-right">Current Stock</TableHead>
                      <TableHead className="table-header-cell text-right">Threshold</TableHead>
                      <TableHead className="table-header-cell">Status</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {lowStock.map((product) => (
                      <TableRow key={product.id} className="table-row">
                        <TableCell className="table-cell font-medium">{product.name}</TableCell>
                        <TableCell className="table-cell text-slate-500">{product.sku}</TableCell>
                        <TableCell className="table-cell">{product.category || '-'}</TableCell>
                        <TableCell className="table-cell text-right">
                          <span className="text-amber-600 font-medium">{product.stock_quantity}</span>
                        </TableCell>
                        <TableCell className="table-cell text-right text-slate-500">{product.low_stock_threshold}</TableCell>
                        <TableCell className="table-cell">
                          {product.stock_quantity === 0 ? (
                            <Badge className="badge-error">Out of Stock</Badge>
                          ) : (
                            <Badge className="badge-warning">Low Stock</Badge>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Add Movement Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent data-testid="movement-dialog">
          <DialogHeader>
            <DialogTitle style={{ fontFamily: 'Outfit, sans-serif' }}>Add Inventory Movement</DialogTitle>
            <DialogDescription>Record stock in, stock out, or adjustment</DialogDescription>
          </DialogHeader>
          <form onSubmit={handleSubmit}>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label>Product *</Label>
                <Select value={formData.product_id} onValueChange={(v) => setFormData({ ...formData, product_id: v })}>
                  <SelectTrigger data-testid="select-movement-product">
                    <SelectValue placeholder="Select product" />
                  </SelectTrigger>
                  <SelectContent>
                    {products.map((p) => (
                      <SelectItem key={p.id} value={p.id}>
                        {p.name} (Stock: {p.stock_quantity})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Movement Type *</Label>
                <Select value={formData.movement_type} onValueChange={(v) => setFormData({ ...formData, movement_type: v })}>
                  <SelectTrigger data-testid="select-movement-type">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="in">Stock In (Add)</SelectItem>
                    <SelectItem value="out">Stock Out (Remove)</SelectItem>
                    <SelectItem value="adjustment">Adjustment (Set)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Quantity *</Label>
                <Input
                  type="number"
                  min="1"
                  value={formData.quantity}
                  onChange={(e) => setFormData({ ...formData, quantity: e.target.value })}
                  required
                  data-testid="movement-quantity"
                />
              </div>
              <div className="space-y-2">
                <Label>Reason *</Label>
                <Input
                  value={formData.reason}
                  onChange={(e) => setFormData({ ...formData, reason: e.target.value })}
                  placeholder="e.g., Manual count adjustment"
                  required
                  data-testid="movement-reason"
                />
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>Cancel</Button>
              <Button type="submit" disabled={submitting || !formData.product_id} className="bg-indigo-600 hover:bg-indigo-700" data-testid="submit-movement-btn">
                {submitting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                Record Movement
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Inventory;
