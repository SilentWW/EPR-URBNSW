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
  Plus, Search, MoreHorizontal, Loader2, Factory, AlertTriangle, Play, 
  PackageCheck, ClipboardCheck, XCircle, Eye, Boxes, CheckCircle2
} from 'lucide-react';
import { toast } from 'sonner';

const formatCurrency = (amount) => {
  return new Intl.NumberFormat('en-LK', {
    style: 'currency',
    currency: 'LKR',
    minimumFractionDigits: 0,
  }).format(amount);
};

const STATUS_CONFIG = {
  draft: { label: 'Draft', color: 'bg-slate-100 text-slate-700', icon: Factory },
  materials_issued: { label: 'Materials Issued', color: 'bg-blue-100 text-blue-700', icon: Boxes },
  in_progress: { label: 'In Progress', color: 'bg-amber-100 text-amber-700', icon: Play },
  qc_pending: { label: 'QC Pending', color: 'bg-purple-100 text-purple-700', icon: ClipboardCheck },
  completed: { label: 'Completed', color: 'bg-green-100 text-green-700', icon: CheckCircle2 },
  cancelled: { label: 'Cancelled', color: 'bg-red-100 text-red-700', icon: XCircle }
};

export const WorkOrders = () => {
  const [workOrders, setWorkOrders] = useState([]);
  const [products, setProducts] = useState([]);
  const [variations, setVariations] = useState({});
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('all');
  const [search, setSearch] = useState('');
  
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [issueMaterialsDialogOpen, setIssueMaterialsDialogOpen] = useState(false);
  const [recordProductionDialogOpen, setRecordProductionDialogOpen] = useState(false);
  const [qcDialogOpen, setQcDialogOpen] = useState(false);
  const [cancelDialogOpen, setCancelDialogOpen] = useState(false);
  
  const [selectedWO, setSelectedWO] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const [formData, setFormData] = useState({
    product_id: '',
    variation_id: '',
    quantity: '',
    order_type: 'make_to_stock',
    planned_start_date: '',
    planned_end_date: '',
    notes: ''
  });

  const [productionData, setProductionData] = useState({ quantity_completed: '' });
  const [qcData, setQcData] = useState({
    quantity_passed: '',
    quantity_failed: '0',
    failure_reason: '',
    notes: ''
  });
  const [cancelReason, setCancelReason] = useState('');

  const fetchData = async () => {
    try {
      const [woRes, productsRes] = await Promise.all([
        api.get('/manufacturing/work-orders', {
          params: statusFilter !== 'all' ? { status: statusFilter } : {}
        }),
        api.get('/products')
      ]);
      setWorkOrders(woRes.data);
      setProducts(productsRes.data);
    } catch (error) {
      toast.error('Failed to fetch work orders');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [statusFilter]);

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

  const fetchWorkOrderDetails = async (woId) => {
    try {
      const response = await api.get(`/manufacturing/work-orders/${woId}`);
      setSelectedWO(response.data);
      return response.data;
    } catch (error) {
      toast.error('Failed to fetch work order details');
      return null;
    }
  };

  const handleProductSelect = (productId) => {
    const product = products.find(p => p.id === productId);
    setFormData({ ...formData, product_id: productId, variation_id: '' });
    
    if (product?.product_type === 'variable') {
      fetchVariations(productId);
    }
  };

  const handleCreateSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);

    try {
      const data = {
        product_id: formData.product_id,
        variation_id: formData.variation_id || null,
        quantity: parseInt(formData.quantity),
        order_type: formData.order_type,
        planned_start_date: formData.planned_start_date || null,
        planned_end_date: formData.planned_end_date || null,
        notes: formData.notes || null
      };

      const response = await api.post('/manufacturing/work-orders', data);
      toast.success(`Work Order ${response.data.wo_number} created!`);
      setCreateDialogOpen(false);
      setFormData({
        product_id: '',
        variation_id: '',
        quantity: '',
        order_type: 'make_to_stock',
        planned_start_date: '',
        planned_end_date: '',
        notes: ''
      });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create work order');
    } finally {
      setSubmitting(false);
    }
  };

  const handleIssueMaterials = async () => {
    setSubmitting(true);
    try {
      const response = await api.post(`/manufacturing/work-orders/${selectedWO.id}/issue-materials`);
      toast.success(`Materials issued! Cost: ${formatCurrency(response.data.total_material_cost)}`);
      setIssueMaterialsDialogOpen(false);
      fetchData();
    } catch (error) {
      const detail = error.response?.data?.detail;
      if (detail?.materials) {
        toast.error(
          <div>
            <p className="font-medium">Insufficient materials:</p>
            {detail.materials.map((m, i) => (
              <p key={i} className="text-sm">• {m.material}: Need {m.required}, Have {m.available}</p>
            ))}
          </div>,
          { duration: 8000 }
        );
      } else {
        toast.error(detail?.message || 'Failed to issue materials');
      }
    } finally {
      setSubmitting(false);
    }
  };

  const handleStartProduction = async (wo) => {
    try {
      await api.post(`/manufacturing/work-orders/${wo.id}/start-production`);
      toast.success('Production started!');
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to start production');
    }
  };

  const handleRecordProduction = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await api.post(
        `/manufacturing/work-orders/${selectedWO.id}/record-production`,
        null,
        { params: { quantity_completed: parseInt(productionData.quantity_completed) } }
      );
      toast.success('Production recorded!');
      setRecordProductionDialogOpen(false);
      setProductionData({ quantity_completed: '' });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to record production');
    } finally {
      setSubmitting(false);
    }
  };

  const handleSubmitQC = async (wo) => {
    try {
      await api.post(`/manufacturing/work-orders/${wo.id}/submit-qc`);
      toast.success('Submitted for QC inspection!');
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to submit for QC');
    }
  };

  const handleQCInspection = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const response = await api.post(`/manufacturing/work-orders/${selectedWO.id}/qc-inspection`, {
        work_order_id: selectedWO.id,
        quantity_passed: parseInt(qcData.quantity_passed),
        quantity_failed: parseInt(qcData.quantity_failed) || 0,
        failure_reason: qcData.failure_reason || null,
        notes: qcData.notes || null
      });
      toast.success(
        `QC Complete! ${response.data.quantity_passed} passed, ${response.data.quantity_failed} failed. ` +
        `Production cost: ${formatCurrency(response.data.production_cost_per_unit)}/unit`
      );
      setQcDialogOpen(false);
      setQcData({ quantity_passed: '', quantity_failed: '0', failure_reason: '', notes: '' });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to complete QC');
    } finally {
      setSubmitting(false);
    }
  };

  const handleCancel = async () => {
    setSubmitting(true);
    try {
      await api.post(
        `/manufacturing/work-orders/${selectedWO.id}/cancel`,
        null,
        { params: { reason: cancelReason || null } }
      );
      toast.success('Work order cancelled. Materials returned to stock.');
      setCancelDialogOpen(false);
      setCancelReason('');
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to cancel');
    } finally {
      setSubmitting(false);
    }
  };

  const getStatusBadge = (status) => {
    const config = STATUS_CONFIG[status] || STATUS_CONFIG.draft;
    const Icon = config.icon;
    return (
      <Badge className={`${config.color} gap-1`}>
        <Icon className="w-3 h-3" />
        {config.label}
      </Badge>
    );
  };

  const filteredOrders = workOrders.filter(wo => {
    if (!search) return true;
    const searchLower = search.toLowerCase();
    return (
      wo.wo_number?.toLowerCase().includes(searchLower) ||
      wo.product_name?.toLowerCase().includes(searchLower)
    );
  });

  return (
    <div className="space-y-6" data-testid="work-orders-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900" style={{ fontFamily: 'Outfit, sans-serif' }}>
            Work Orders
          </h2>
          <p className="text-slate-500 mt-1">{workOrders.length} production orders</p>
        </div>
        <Button 
          onClick={() => setCreateDialogOpen(true)} 
          className="gap-2 bg-indigo-600 hover:bg-indigo-700" 
          data-testid="create-wo-btn"
        >
          <Plus className="w-4 h-4" />
          Create Work Order
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <Input
                placeholder="Search work orders..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9"
              />
            </div>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-full sm:w-48">
                <SelectValue placeholder="All Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                {Object.entries(STATUS_CONFIG).map(([key, config]) => (
                  <SelectItem key={key} value={key}>{config.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Work Orders Table */}
      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
            </div>
          ) : filteredOrders.length === 0 ? (
            <div className="text-center py-16">
              <Factory className="w-12 h-12 text-slate-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-slate-900">No work orders found</h3>
              <p className="text-slate-500 mt-1">Create a work order to start production.</p>
              <Button onClick={() => setCreateDialogOpen(true)} className="mt-4 bg-indigo-600 hover:bg-indigo-700">
                Create Work Order
              </Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="bg-slate-50">
                  <TableHead>WO Number</TableHead>
                  <TableHead>Product</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead className="text-right">Qty</TableHead>
                  <TableHead className="text-right">Completed</TableHead>
                  <TableHead className="text-right">Est. Cost</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="w-12"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredOrders.map((wo) => (
                  <TableRow key={wo.id} data-testid={`wo-row-${wo.id}`}>
                    <TableCell className="font-medium">{wo.wo_number}</TableCell>
                    <TableCell>
                      <div>
                        {wo.product_name}
                        {wo.variation_name && (
                          <Badge variant="secondary" className="ml-2 text-xs">
                            {wo.variation_name}
                          </Badge>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className="text-xs">
                        {wo.order_type === 'make_to_stock' ? 'Stock' : 'Order'}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">{wo.quantity}</TableCell>
                    <TableCell className="text-right">
                      {wo.quantity_completed || 0}
                      {wo.quantity_passed_qc > 0 && (
                        <span className="text-green-600 text-xs ml-1">({wo.quantity_passed_qc} QC✓)</span>
                      )}
                    </TableCell>
                    <TableCell className="text-right">{formatCurrency(wo.estimated_total_cost)}</TableCell>
                    <TableCell>{getStatusBadge(wo.status)}</TableCell>
                    <TableCell>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon">
                            <MoreHorizontal className="w-4 h-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={async () => {
                            await fetchWorkOrderDetails(wo.id);
                            setViewDialogOpen(true);
                          }}>
                            <Eye className="w-4 h-4 mr-2" />
                            View Details
                          </DropdownMenuItem>

                          {wo.status === 'draft' && (
                            <>
                              <DropdownMenuSeparator />
                              <DropdownMenuItem onClick={() => {
                                setSelectedWO(wo);
                                setIssueMaterialsDialogOpen(true);
                              }}>
                                <Boxes className="w-4 h-4 mr-2" />
                                Issue Materials
                              </DropdownMenuItem>
                            </>
                          )}

                          {wo.status === 'materials_issued' && (
                            <DropdownMenuItem onClick={() => handleStartProduction(wo)}>
                              <Play className="w-4 h-4 mr-2" />
                              Start Production
                            </DropdownMenuItem>
                          )}

                          {(wo.status === 'materials_issued' || wo.status === 'in_progress') && (
                            <DropdownMenuItem onClick={() => {
                              setSelectedWO(wo);
                              setRecordProductionDialogOpen(true);
                            }}>
                              <PackageCheck className="w-4 h-4 mr-2" />
                              Record Production
                            </DropdownMenuItem>
                          )}

                          {wo.status === 'in_progress' && wo.quantity_completed > 0 && (
                            <DropdownMenuItem onClick={() => handleSubmitQC(wo)}>
                              <ClipboardCheck className="w-4 h-4 mr-2" />
                              Submit to QC
                            </DropdownMenuItem>
                          )}

                          {wo.status === 'qc_pending' && (
                            <DropdownMenuItem onClick={() => {
                              setSelectedWO(wo);
                              setQcData({ ...qcData, quantity_passed: wo.quantity_completed.toString() });
                              setQcDialogOpen(true);
                            }}>
                              <ClipboardCheck className="w-4 h-4 mr-2" />
                              Perform QC Inspection
                            </DropdownMenuItem>
                          )}

                          {wo.status !== 'completed' && wo.status !== 'cancelled' && (
                            <>
                              <DropdownMenuSeparator />
                              <DropdownMenuItem 
                                className="text-red-600"
                                onClick={() => {
                                  setSelectedWO(wo);
                                  setCancelDialogOpen(true);
                                }}
                              >
                                <XCircle className="w-4 h-4 mr-2" />
                                Cancel Order
                              </DropdownMenuItem>
                            </>
                          )}
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

      {/* Create Work Order Dialog */}
      <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
        <DialogContent className="max-w-lg" data-testid="create-wo-dialog">
          <DialogHeader>
            <DialogTitle>Create Work Order</DialogTitle>
            <DialogDescription>
              Create a production order to manufacture products
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleCreateSubmit}>
            <div className="grid gap-4 py-4">
              <div className="space-y-2">
                <Label>Product *</Label>
                <Select value={formData.product_id} onValueChange={handleProductSelect}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select product to manufacture" />
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

              {formData.product_id && products.find(p => p.id === formData.product_id)?.product_type === 'variable' && (
                <div className="space-y-2">
                  <Label>Variation *</Label>
                  <Select
                    value={formData.variation_id}
                    onValueChange={(v) => setFormData({ ...formData, variation_id: v })}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select variation" />
                    </SelectTrigger>
                    <SelectContent>
                      {(variations[formData.product_id] || []).map((v) => (
                        <SelectItem key={v.id} value={v.id}>
                          {v.variation_name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Quantity *</Label>
                  <Input
                    type="number"
                    min="1"
                    value={formData.quantity}
                    onChange={(e) => setFormData({ ...formData, quantity: e.target.value })}
                    required
                    placeholder="100"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Order Type</Label>
                  <Select
                    value={formData.order_type}
                    onValueChange={(v) => setFormData({ ...formData, order_type: v })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="make_to_stock">Make to Stock</SelectItem>
                      <SelectItem value="make_to_order">Make to Order</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Planned Start</Label>
                  <Input
                    type="date"
                    value={formData.planned_start_date}
                    onChange={(e) => setFormData({ ...formData, planned_start_date: e.target.value })}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Planned End</Label>
                  <Input
                    type="date"
                    value={formData.planned_end_date}
                    onChange={(e) => setFormData({ ...formData, planned_end_date: e.target.value })}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label>Notes</Label>
                <Input
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  placeholder="Optional notes"
                />
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setCreateDialogOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={submitting} className="bg-indigo-600 hover:bg-indigo-700">
                {submitting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                Create Work Order
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* View Details Dialog */}
      <Dialog open={viewDialogOpen} onOpenChange={setViewDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{selectedWO?.wo_number} - Details</DialogTitle>
          </DialogHeader>
          {selectedWO && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-slate-500">Product</Label>
                  <p className="font-medium">{selectedWO.product_name}</p>
                  {selectedWO.variation_name && <Badge variant="secondary">{selectedWO.variation_name}</Badge>}
                </div>
                <div>
                  <Label className="text-slate-500">Status</Label>
                  <div>{getStatusBadge(selectedWO.status)}</div>
                </div>
                <div>
                  <Label className="text-slate-500">Quantity</Label>
                  <p className="font-medium">{selectedWO.quantity} units</p>
                </div>
                <div>
                  <Label className="text-slate-500">Completed</Label>
                  <p className="font-medium">{selectedWO.quantity_completed || 0} units</p>
                </div>
              </div>

              <div className="border-t pt-4">
                <Label className="text-slate-500">Cost Breakdown (per unit)</Label>
                <div className="grid grid-cols-4 gap-4 mt-2">
                  <div className="text-center p-3 bg-slate-50 rounded">
                    <p className="text-xs text-slate-500">Material</p>
                    <p className="font-semibold">{formatCurrency(selectedWO.material_cost_per_unit)}</p>
                  </div>
                  <div className="text-center p-3 bg-slate-50 rounded">
                    <p className="text-xs text-slate-500">Labor</p>
                    <p className="font-semibold">{formatCurrency(selectedWO.labor_cost_per_unit)}</p>
                  </div>
                  <div className="text-center p-3 bg-slate-50 rounded">
                    <p className="text-xs text-slate-500">Overhead</p>
                    <p className="font-semibold">{formatCurrency(selectedWO.overhead_cost_per_unit)}</p>
                  </div>
                  <div className="text-center p-3 bg-indigo-50 rounded">
                    <p className="text-xs text-indigo-600">Total</p>
                    <p className="font-bold text-indigo-600">{formatCurrency(selectedWO.total_cost_per_unit)}</p>
                  </div>
                </div>
              </div>

              {selectedWO.material_issuances?.length > 0 && (
                <div className="border-t pt-4">
                  <Label className="text-slate-500">Materials Issued</Label>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Material</TableHead>
                        <TableHead className="text-right">Qty</TableHead>
                        <TableHead className="text-right">Cost</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {selectedWO.material_issuances.map((m, i) => (
                        <TableRow key={i}>
                          <TableCell>{m.material_name}</TableCell>
                          <TableCell className="text-right">{m.quantity} {m.unit}</TableCell>
                          <TableCell className="text-right">{formatCurrency(m.line_cost)}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              )}

              {selectedWO.qc_inspections?.length > 0 && (
                <div className="border-t pt-4">
                  <Label className="text-slate-500">QC Inspections</Label>
                  {selectedWO.qc_inspections.map((qc, i) => (
                    <div key={i} className="flex gap-4 mt-2 p-3 bg-slate-50 rounded">
                      <div>
                        <span className="text-green-600 font-medium">{qc.quantity_passed} passed</span>
                      </div>
                      <div>
                        <span className="text-red-600">{qc.quantity_failed} failed</span>
                      </div>
                      {qc.failure_reason && (
                        <div className="text-slate-500 text-sm">Reason: {qc.failure_reason}</div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Issue Materials Dialog */}
      <Dialog open={issueMaterialsDialogOpen} onOpenChange={setIssueMaterialsDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Boxes className="w-5 h-5 text-blue-600" />
              Issue Materials
            </DialogTitle>
            <DialogDescription>
              Issue raw materials for {selectedWO?.wo_number}. This will deduct materials from stock.
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <p className="text-sm">
              Product: <strong>{selectedWO?.product_name}</strong>
            </p>
            <p className="text-sm">
              Quantity to produce: <strong>{selectedWO?.quantity} units</strong>
            </p>
            <p className="text-sm mt-2 text-amber-600">
              Materials will be deducted from raw material inventory and charged to WIP.
            </p>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIssueMaterialsDialogOpen(false)}>
              Cancel
            </Button>
            <Button 
              onClick={handleIssueMaterials} 
              disabled={submitting}
              className="bg-blue-600 hover:bg-blue-700"
            >
              {submitting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Boxes className="w-4 h-4 mr-2" />}
              Issue Materials
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Record Production Dialog */}
      <Dialog open={recordProductionDialogOpen} onOpenChange={setRecordProductionDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <PackageCheck className="w-5 h-5 text-amber-600" />
              Record Production
            </DialogTitle>
            <DialogDescription>
              Record completed production for {selectedWO?.wo_number}
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleRecordProduction}>
            <div className="py-4 space-y-4">
              <div className="flex justify-between text-sm">
                <span>Planned: {selectedWO?.quantity} units</span>
                <span>Already completed: {selectedWO?.quantity_completed || 0} units</span>
              </div>
              <div className="space-y-2">
                <Label>Quantity Completed Now *</Label>
                <Input
                  type="number"
                  min="1"
                  max={selectedWO ? selectedWO.quantity - (selectedWO.quantity_completed || 0) : 1}
                  value={productionData.quantity_completed}
                  onChange={(e) => setProductionData({ quantity_completed: e.target.value })}
                  required
                  placeholder="Enter quantity produced"
                />
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setRecordProductionDialogOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={submitting} className="bg-amber-600 hover:bg-amber-700">
                {submitting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                Record Production
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* QC Inspection Dialog */}
      <Dialog open={qcDialogOpen} onOpenChange={setQcDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <ClipboardCheck className="w-5 h-5 text-purple-600" />
              QC Inspection
            </DialogTitle>
            <DialogDescription>
              Perform quality control inspection for {selectedWO?.wo_number}
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleQCInspection}>
            <div className="py-4 space-y-4">
              <div className="text-sm bg-slate-50 p-3 rounded">
                <p>Total produced: <strong>{selectedWO?.quantity_completed} units</strong></p>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Quantity Passed *</Label>
                  <Input
                    type="number"
                    min="0"
                    value={qcData.quantity_passed}
                    onChange={(e) => setQcData({ ...qcData, quantity_passed: e.target.value })}
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label>Quantity Failed</Label>
                  <Input
                    type="number"
                    min="0"
                    value={qcData.quantity_failed}
                    onChange={(e) => setQcData({ ...qcData, quantity_failed: e.target.value })}
                  />
                </div>
              </div>
              {parseInt(qcData.quantity_failed) > 0 && (
                <div className="space-y-2">
                  <Label>Failure Reason</Label>
                  <Input
                    value={qcData.failure_reason}
                    onChange={(e) => setQcData({ ...qcData, failure_reason: e.target.value })}
                    placeholder="Describe the quality issue"
                  />
                </div>
              )}
              <div className="space-y-2">
                <Label>Notes</Label>
                <Input
                  value={qcData.notes}
                  onChange={(e) => setQcData({ ...qcData, notes: e.target.value })}
                  placeholder="Optional inspection notes"
                />
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setQcDialogOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={submitting} className="bg-purple-600 hover:bg-purple-700">
                {submitting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                Complete QC
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Cancel Dialog */}
      <Dialog open={cancelDialogOpen} onOpenChange={setCancelDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-red-600">
              <AlertTriangle className="w-5 h-5" />
              Cancel Work Order
            </DialogTitle>
            <DialogDescription>
              Cancel {selectedWO?.wo_number}? Materials will be returned to stock.
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <Label>Cancellation Reason (optional)</Label>
            <Input
              value={cancelReason}
              onChange={(e) => setCancelReason(e.target.value)}
              placeholder="Enter reason for cancellation"
              className="mt-2"
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCancelDialogOpen(false)}>
              Keep Order
            </Button>
            <Button variant="destructive" onClick={handleCancel} disabled={submitting}>
              {submitting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
              Cancel Order
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default WorkOrders;
