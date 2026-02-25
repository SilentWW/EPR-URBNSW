import React, { useState, useEffect } from 'react';
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
  DropdownMenuTrigger,
} from '../components/ui/dropdown-menu';
import { 
  Plus, Search, MoreHorizontal, Pencil, Trash2, Loader2, FileText, AlertTriangle,
  ChevronDown, ChevronRight
} from 'lucide-react';
import { toast } from 'sonner';

const formatCurrency = (amount) => {
  return new Intl.NumberFormat('en-LK', {
    style: 'currency',
    currency: 'LKR',
    minimumFractionDigits: 0,
  }).format(amount);
};

export const BillOfMaterials = () => {
  const [boms, setBoms] = useState([]);
  const [products, setProducts] = useState([]);
  const [variations, setVariations] = useState({});
  const [rawMaterials, setRawMaterials] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedBOM, setSelectedBOM] = useState(null);
  const [expandedBOMs, setExpandedBOMs] = useState({});
  const [submitting, setSubmitting] = useState(false);

  const [formData, setFormData] = useState({
    product_id: '',
    variation_id: '',
    components: [],
    labor_cost_per_unit: '',
    overhead_percent: '',
    notes: ''
  });

  const [newComponent, setNewComponent] = useState({
    raw_material_id: '',
    quantity: '',
    wastage_percent: '0',
    notes: ''
  });

  const fetchData = async () => {
    try {
      const [bomsRes, productsRes, materialsRes] = await Promise.all([
        api.get('/manufacturing/bom'),
        api.get('/products'),
        api.get('/manufacturing/raw-materials')
      ]);
      setBoms(bomsRes.data);
      setProducts(productsRes.data);
      setRawMaterials(materialsRes.data);
    } catch (error) {
      toast.error('Failed to fetch data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const fetchVariations = async (productId) => {
    try {
      const response = await api.get(`/variations/product/${productId}`);
      setVariations(prev => ({
        ...prev,
        [productId]: response.data.variations || []
      }));
    } catch (error) {
      console.error('Failed to fetch variations:', error);
    }
  };

  const handleProductSelect = (productId) => {
    const product = products.find(p => p.id === productId);
    setFormData({ ...formData, product_id: productId, variation_id: '' });
    
    if (product?.product_type === 'variable') {
      fetchVariations(productId);
    }
  };

  const toggleExpanded = (bomId) => {
    setExpandedBOMs(prev => ({
      ...prev,
      [bomId]: !prev[bomId]
    }));
  };

  const handleOpenDialog = (bom = null) => {
    if (bom) {
      setSelectedBOM(bom);
      setFormData({
        product_id: bom.product_id,
        variation_id: bom.variation_id || '',
        components: bom.components || [],
        labor_cost_per_unit: bom.labor_cost_per_unit?.toString() || '',
        overhead_percent: bom.overhead_percent?.toString() || '',
        notes: bom.notes || ''
      });
      if (bom.variation_id) {
        fetchVariations(bom.product_id);
      }
    } else {
      setSelectedBOM(null);
      setFormData({
        product_id: '',
        variation_id: '',
        components: [],
        labor_cost_per_unit: '',
        overhead_percent: '',
        notes: ''
      });
    }
    setDialogOpen(true);
  };

  const handleAddComponent = () => {
    if (!newComponent.raw_material_id || !newComponent.quantity) {
      toast.error('Please select a material and enter quantity');
      return;
    }

    const material = rawMaterials.find(m => m.id === newComponent.raw_material_id);
    if (!material) return;

    setFormData({
      ...formData,
      components: [...formData.components, {
        raw_material_id: newComponent.raw_material_id,
        material_name: material.name,
        quantity: parseFloat(newComponent.quantity),
        unit: material.unit,
        wastage_percent: parseFloat(newComponent.wastage_percent) || 0,
        notes: newComponent.notes,
        material_cost: material.cost_price
      }]
    });

    setNewComponent({
      raw_material_id: '',
      quantity: '',
      wastage_percent: '0',
      notes: ''
    });
  };

  const handleRemoveComponent = (index) => {
    setFormData({
      ...formData,
      components: formData.components.filter((_, i) => i !== index)
    });
  };

  const calculateTotalCost = () => {
    let materialCost = 0;
    formData.components.forEach(comp => {
      const material = rawMaterials.find(m => m.id === comp.raw_material_id);
      if (material) {
        const effectiveQty = comp.quantity * (1 + (comp.wastage_percent || 0) / 100);
        materialCost += effectiveQty * material.cost_price;
      }
    });

    const laborCost = parseFloat(formData.labor_cost_per_unit) || 0;
    const overheadPercent = parseFloat(formData.overhead_percent) || 0;
    const overheadCost = (materialCost + laborCost) * overheadPercent / 100;

    return {
      materialCost: Math.round(materialCost * 100) / 100,
      laborCost,
      overheadCost: Math.round(overheadCost * 100) / 100,
      totalCost: Math.round((materialCost + laborCost + overheadCost) * 100) / 100
    };
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);

    try {
      if (formData.components.length === 0) {
        toast.error('Please add at least one component');
        setSubmitting(false);
        return;
      }

      const data = {
        product_id: formData.product_id,
        variation_id: formData.variation_id || null,
        components: formData.components.map(c => ({
          raw_material_id: c.raw_material_id,
          quantity: c.quantity,
          unit: c.unit,
          wastage_percent: c.wastage_percent || 0,
          notes: c.notes || null
        })),
        labor_cost_per_unit: parseFloat(formData.labor_cost_per_unit) || 0,
        overhead_percent: parseFloat(formData.overhead_percent) || 0,
        notes: formData.notes || null
      };

      if (selectedBOM) {
        await api.put(`/manufacturing/bom/${selectedBOM.id}`, data);
        toast.success('Bill of Materials updated successfully');
      } else {
        await api.post('/manufacturing/bom', data);
        toast.success('Bill of Materials created successfully');
      }

      setDialogOpen(false);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Operation failed');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async () => {
    try {
      await api.delete(`/manufacturing/bom/${selectedBOM.id}`);
      toast.success('Bill of Materials deleted successfully');
      setDeleteDialogOpen(false);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete BOM');
    }
  };

  const filteredBoms = boms.filter(bom => {
    if (!search) return true;
    const searchLower = search.toLowerCase();
    return (
      bom.product_name?.toLowerCase().includes(searchLower) ||
      bom.product_sku?.toLowerCase().includes(searchLower) ||
      bom.variation_name?.toLowerCase().includes(searchLower)
    );
  });

  const costs = calculateTotalCost();

  return (
    <div className="space-y-6" data-testid="bom-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900" style={{ fontFamily: 'Outfit, sans-serif' }}>
            Bill of Materials
          </h2>
          <p className="text-slate-500 mt-1">{boms.length} recipes defined</p>
        </div>
        <Button 
          onClick={() => handleOpenDialog()} 
          className="gap-2 bg-teal-600 hover:bg-teal-700" 
          data-testid="add-bom-btn"
        >
          <Plus className="w-4 h-4" />
          Create BOM
        </Button>
      </div>

      {/* Search */}
      <Card>
        <CardContent className="p-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <Input
              placeholder="Search by product name or SKU..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9"
              data-testid="search-bom"
            />
          </div>
        </CardContent>
      </Card>

      {/* BOMs Table */}
      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <Loader2 className="w-8 h-8 animate-spin text-teal-600" />
            </div>
          ) : filteredBoms.length === 0 ? (
            <div className="text-center py-16">
              <FileText className="w-12 h-12 text-slate-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-slate-900">No Bill of Materials found</h3>
              <p className="text-slate-500 mt-1">Create a BOM to define product recipes.</p>
              <Button onClick={() => handleOpenDialog()} className="mt-4 bg-teal-600 hover:bg-teal-700">
                Create BOM
              </Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="bg-slate-50">
                  <TableHead className="w-8"></TableHead>
                  <TableHead>Product</TableHead>
                  <TableHead>SKU</TableHead>
                  <TableHead className="text-right">Material Cost</TableHead>
                  <TableHead className="text-right">Labor</TableHead>
                  <TableHead className="text-right">Overhead</TableHead>
                  <TableHead className="text-right">Total Cost/Unit</TableHead>
                  <TableHead className="w-12"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredBoms.map((bom) => (
                  <React.Fragment key={bom.id}>
                    <TableRow data-testid={`bom-row-${bom.id}`}>
                      <TableCell>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="p-0 h-6 w-6"
                          onClick={() => toggleExpanded(bom.id)}
                        >
                          {expandedBOMs[bom.id] ? (
                            <ChevronDown className="w-4 h-4" />
                          ) : (
                            <ChevronRight className="w-4 h-4" />
                          )}
                        </Button>
                      </TableCell>
                      <TableCell className="font-medium">
                        <div>
                          {bom.product_name}
                          {bom.variation_name && (
                            <Badge variant="secondary" className="ml-2 text-xs">
                              {bom.variation_name}
                            </Badge>
                          )}
                        </div>
                      </TableCell>
                      <TableCell className="text-slate-500">
                        {bom.variation_sku || bom.product_sku}
                      </TableCell>
                      <TableCell className="text-right">{formatCurrency(bom.total_material_cost)}</TableCell>
                      <TableCell className="text-right">{formatCurrency(bom.total_labor_cost)}</TableCell>
                      <TableCell className="text-right">{formatCurrency(bom.overhead_cost)}</TableCell>
                      <TableCell className="text-right font-semibold text-teal-600">
                        {formatCurrency(bom.total_cost_per_unit)}
                      </TableCell>
                      <TableCell>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon">
                              <MoreHorizontal className="w-4 h-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={() => handleOpenDialog(bom)}>
                              <Pencil className="w-4 h-4 mr-2" />
                              Edit
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              className="text-red-600"
                              onClick={() => {
                                setSelectedBOM(bom);
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

                    {/* Expanded Components */}
                    {expandedBOMs[bom.id] && (
                      <TableRow className="bg-slate-50">
                        <TableCell colSpan={8} className="p-4">
                          <div className="text-sm font-medium text-slate-600 mb-2">Components:</div>
                          <Table>
                            <TableHeader>
                              <TableRow>
                                <TableHead>Material</TableHead>
                                <TableHead className="text-right">Quantity</TableHead>
                                <TableHead className="text-right">Wastage %</TableHead>
                                <TableHead className="text-right">Effective Qty</TableHead>
                                <TableHead className="text-right">Unit Cost</TableHead>
                                <TableHead className="text-right">Line Cost</TableHead>
                              </TableRow>
                            </TableHeader>
                            <TableBody>
                              {bom.components?.map((comp, idx) => (
                                <TableRow key={idx}>
                                  <TableCell>{comp.material_name}</TableCell>
                                  <TableCell className="text-right">{comp.quantity} {comp.unit}</TableCell>
                                  <TableCell className="text-right">{comp.wastage_percent || 0}%</TableCell>
                                  <TableCell className="text-right">
                                    {(comp.quantity * (1 + (comp.wastage_percent || 0) / 100)).toFixed(2)} {comp.unit}
                                  </TableCell>
                                  <TableCell className="text-right">{formatCurrency(comp.material_cost)}</TableCell>
                                  <TableCell className="text-right font-medium">{formatCurrency(comp.line_cost)}</TableCell>
                                </TableRow>
                              ))}
                            </TableBody>
                          </Table>
                          {bom.notes && (
                            <div className="mt-3 text-sm text-slate-500">
                              <strong>Notes:</strong> {bom.notes}
                            </div>
                          )}
                        </TableCell>
                      </TableRow>
                    )}
                  </React.Fragment>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Create/Edit BOM Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto" data-testid="bom-dialog">
          <DialogHeader>
            <DialogTitle style={{ fontFamily: 'Outfit, sans-serif' }}>
              {selectedBOM ? 'Edit Bill of Materials' : 'Create Bill of Materials'}
            </DialogTitle>
            <DialogDescription>
              Define the raw materials needed to produce this product
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleSubmit}>
            <div className="grid gap-4 py-4">
              {/* Product Selection */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Finished Product *</Label>
                  <Select
                    value={formData.product_id}
                    onValueChange={handleProductSelect}
                    disabled={!!selectedBOM}
                  >
                    <SelectTrigger data-testid="bom-product">
                      <SelectValue placeholder="Select product" />
                    </SelectTrigger>
                    <SelectContent>
                      {products.map((p) => (
                        <SelectItem key={p.id} value={p.id}>
                          {p.name} {p.product_type === 'variable' && '(Variable)'}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Variation Selection (for variable products) */}
                {formData.product_id && products.find(p => p.id === formData.product_id)?.product_type === 'variable' && (
                  <div className="space-y-2">
                    <Label>Variation</Label>
                    <Select
                      value={formData.variation_id || "all"}
                      onValueChange={(v) => setFormData({ ...formData, variation_id: v === "all" ? "" : v })}
                      disabled={!!selectedBOM}
                    >
                      <SelectTrigger data-testid="bom-variation">
                        <SelectValue placeholder="Select variation (optional)" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">All Variations (Generic BOM)</SelectItem>
                        {(variations[formData.product_id] || []).map((v) => (
                          <SelectItem key={v.id} value={v.id}>
                            {v.variation_name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                )}
              </div>

              {/* Components Section */}
              <div className="space-y-3">
                <Label className="text-base font-medium">Components / Raw Materials</Label>
                
                {/* Add Component */}
                <div className="flex gap-2 p-3 bg-slate-50 rounded-lg">
                  <Select
                    value={newComponent.raw_material_id}
                    onValueChange={(v) => setNewComponent({ ...newComponent, raw_material_id: v })}
                  >
                    <SelectTrigger className="flex-[2]">
                      <SelectValue placeholder="Select raw material" />
                    </SelectTrigger>
                    <SelectContent>
                      {rawMaterials.map((m) => (
                        <SelectItem key={m.id} value={m.id}>
                          {m.name} ({m.unit}) - {formatCurrency(m.cost_price)}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Input
                    type="number"
                    step="0.01"
                    placeholder="Qty"
                    value={newComponent.quantity}
                    onChange={(e) => setNewComponent({ ...newComponent, quantity: e.target.value })}
                    className="w-24"
                  />
                  <Input
                    type="number"
                    step="0.1"
                    placeholder="Waste %"
                    value={newComponent.wastage_percent}
                    onChange={(e) => setNewComponent({ ...newComponent, wastage_percent: e.target.value })}
                    className="w-24"
                  />
                  <Button type="button" onClick={handleAddComponent} variant="outline">
                    <Plus className="w-4 h-4" />
                  </Button>
                </div>

                {/* Components List */}
                {formData.components.length > 0 && (
                  <div className="border rounded-lg overflow-hidden">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Material</TableHead>
                          <TableHead className="text-right">Qty</TableHead>
                          <TableHead className="text-right">Waste %</TableHead>
                          <TableHead className="text-right">Cost</TableHead>
                          <TableHead className="w-10"></TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {formData.components.map((comp, idx) => {
                          const material = rawMaterials.find(m => m.id === comp.raw_material_id);
                          const effectiveQty = comp.quantity * (1 + (comp.wastage_percent || 0) / 100);
                          const lineCost = effectiveQty * (material?.cost_price || 0);
                          
                          return (
                            <TableRow key={idx}>
                              <TableCell>{comp.material_name || material?.name}</TableCell>
                              <TableCell className="text-right">{comp.quantity} {comp.unit || material?.unit}</TableCell>
                              <TableCell className="text-right">{comp.wastage_percent || 0}%</TableCell>
                              <TableCell className="text-right">{formatCurrency(lineCost)}</TableCell>
                              <TableCell>
                                <Button
                                  type="button"
                                  variant="ghost"
                                  size="icon"
                                  onClick={() => handleRemoveComponent(idx)}
                                >
                                  <Trash2 className="w-4 h-4 text-red-500" />
                                </Button>
                              </TableCell>
                            </TableRow>
                          );
                        })}
                      </TableBody>
                    </Table>
                  </div>
                )}
              </div>

              {/* Labor & Overhead */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Labor Cost per Unit</Label>
                  <Input
                    type="number"
                    step="0.01"
                    value={formData.labor_cost_per_unit}
                    onChange={(e) => setFormData({ ...formData, labor_cost_per_unit: e.target.value })}
                    placeholder="0.00"
                    data-testid="bom-labor"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Overhead %</Label>
                  <Input
                    type="number"
                    step="0.1"
                    value={formData.overhead_percent}
                    onChange={(e) => setFormData({ ...formData, overhead_percent: e.target.value })}
                    placeholder="0"
                    data-testid="bom-overhead"
                  />
                </div>
              </div>

              {/* Cost Summary */}
              {formData.components.length > 0 && (
                <div className="bg-teal-50 border border-teal-200 rounded-lg p-4">
                  <h4 className="font-medium text-teal-800 mb-2">Cost Summary (per unit)</h4>
                  <div className="grid grid-cols-4 gap-4 text-sm">
                    <div>
                      <span className="text-teal-600">Material Cost</span>
                      <p className="font-semibold">{formatCurrency(costs.materialCost)}</p>
                    </div>
                    <div>
                      <span className="text-teal-600">Labor Cost</span>
                      <p className="font-semibold">{formatCurrency(costs.laborCost)}</p>
                    </div>
                    <div>
                      <span className="text-teal-600">Overhead</span>
                      <p className="font-semibold">{formatCurrency(costs.overheadCost)}</p>
                    </div>
                    <div>
                      <span className="text-teal-600">Total Cost</span>
                      <p className="font-bold text-lg text-teal-700">{formatCurrency(costs.totalCost)}</p>
                    </div>
                  </div>
                </div>
              )}

              {/* Notes */}
              <div className="space-y-2">
                <Label>Notes</Label>
                <Input
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  placeholder="Optional notes about this BOM"
                />
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={submitting} className="bg-teal-600 hover:bg-teal-700" data-testid="bom-submit">
                {submitting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                {selectedBOM ? 'Update' : 'Create'} BOM
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-red-600">
              <AlertTriangle className="w-5 h-5" />
              Delete Bill of Materials
            </DialogTitle>
            <DialogDescription>
              Are you sure you want to delete the BOM for &quot;{selectedBOM?.product_name}&quot;? This cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteDialogOpen(false)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={handleDelete}>
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default BillOfMaterials;
