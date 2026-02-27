import React, { useState, useEffect } from 'react';
import { rmProcurementAPI } from '../lib/api';
import api from '../lib/api';
import { useSearchParams } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Textarea } from '../components/ui/textarea';
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
  Plus, MoreHorizontal, Eye, Loader2, Package, FileInput, RotateCcw, AlertTriangle
} from 'lucide-react';
import { toast } from 'sonner';

const formatCurrency = (amount) => {
  return new Intl.NumberFormat('en-LK', {
    style: 'currency',
    currency: 'LKR',
    minimumFractionDigits: 0,
  }).format(amount);
};

const grnStatusColors = {
  received: 'bg-green-100 text-green-700',
  partial_return: 'bg-amber-100 text-amber-700',
  returned: 'bg-red-100 text-red-700',
};

export const RMGRN = () => {
  const [searchParams] = useSearchParams();
  const preSelectedPOId = searchParams.get('po_id');

  const [grns, setGRNs] = useState([]);
  const [purchaseOrders, setPurchaseOrders] = useState([]);
  const [bankAccounts, setBankAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [selectedGRN, setSelectedGRN] = useState(null);
  const [selectedPO, setSelectedPO] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const [formData, setFormData] = useState({
    rm_po_id: '',
    received_date: new Date().toISOString().split('T')[0],
    reference_number: '',
    bank_account_id: '',
    notes: '',
    items: [],
  });

  const fetchData = async () => {
    try {
      const [grnsRes, posRes, bankRes] = await Promise.all([
        rmProcurementAPI.getGRNs(),
        rmProcurementAPI.getPurchaseOrders({ status: 'approved' }),
        api.get('/bank-accounts'),
      ]);
      
      setGRNs(grnsRes.data);
      // Also fetch partially received POs
      const partialRes = await rmProcurementAPI.getPurchaseOrders({ status: 'partially_received' });
      setPurchaseOrders([...posRes.data, ...partialRes.data]);
      setBankAccounts(bankRes.data || []);

      // Open dialog if PO pre-selected
      if (preSelectedPOId && posRes.data.length > 0) {
        const po = posRes.data.find(p => p.id === preSelectedPOId) || partialRes.data.find(p => p.id === preSelectedPOId);
        if (po) {
          handleSelectPO(po.id, [...posRes.data, ...partialRes.data]);
          setDialogOpen(true);
        }
      }
    } catch (error) {
      toast.error('Failed to fetch data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleSelectPO = async (poId, poList = purchaseOrders) => {
    const po = poList.find(p => p.id === poId);
    if (!po) return;
    
    // Get full PO details
    try {
      const response = await rmProcurementAPI.getPurchaseOrder(poId);
      setSelectedPO(response.data);
      
      // Pre-fill receivable items
      const items = response.data.items
        .filter(item => item.received_quantity < item.quantity)
        .map((item, idx) => ({
          raw_material_id: item.raw_material_id,
          raw_material_name: item.raw_material_name,
          raw_material_sku: item.raw_material_sku,
          unit: item.unit,
          po_item_index: response.data.items.indexOf(item),
          ordered: item.quantity,
          already_received: item.received_quantity,
          remaining: item.quantity - item.received_quantity,
          received_quantity: item.quantity - item.received_quantity, // Default to full receive
          unit_price: item.unit_price,
        }));

      setFormData({
        ...formData,
        rm_po_id: poId,
        items,
        bank_account_id: response.data.payment_terms === 'immediate' ? '' : '',
      });
    } catch (error) {
      toast.error('Failed to load PO details');
    }
  };

  const updateItemQuantity = (index, qty) => {
    const items = [...formData.items];
    const parsed = parseFloat(qty) || 0;
    items[index].received_quantity = Math.min(parsed, items[index].remaining);
    setFormData({ ...formData, items });
  };

  const updateItemPrice = (index, price) => {
    const items = [...formData.items];
    items[index].unit_price = parseFloat(price) || 0;
    setFormData({ ...formData, items });
  };

  const calculateTotalCost = () => {
    return formData.items.reduce((sum, item) => sum + (item.received_quantity * item.unit_price), 0);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    const itemsToReceive = formData.items.filter(i => i.received_quantity > 0);
    if (itemsToReceive.length === 0) {
      toast.error('Please enter quantity for at least one item');
      return;
    }

    // Validate bank account for immediate payment
    if (selectedPO?.payment_terms === 'immediate' && !formData.bank_account_id) {
      toast.error('Please select a payment account for immediate payment');
      return;
    }

    setSubmitting(true);
    try {
      const payload = {
        rm_po_id: formData.rm_po_id,
        items: itemsToReceive.map(item => ({
          raw_material_id: item.raw_material_id,
          po_item_index: item.po_item_index,
          received_quantity: item.received_quantity,
          unit_price: item.unit_price,
        })),
        received_date: formData.received_date,
        reference_number: formData.reference_number || null,
        bank_account_id: formData.bank_account_id || null,
        notes: formData.notes || null,
      };

      const response = await rmProcurementAPI.createGRN(payload);
      toast.success(`GRN ${response.data.grn_number} created successfully`);
      setDialogOpen(false);
      setSelectedPO(null);
      setFormData({
        rm_po_id: '',
        received_date: new Date().toISOString().split('T')[0],
        reference_number: '',
        bank_account_id: '',
        notes: '',
        items: [],
      });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create GRN');
    } finally {
      setSubmitting(false);
    }
  };

  const handleViewGRN = async (grn) => {
    try {
      const response = await rmProcurementAPI.getGRN(grn.id);
      setSelectedGRN(response.data);
      setViewDialogOpen(true);
    } catch (error) {
      toast.error('Failed to load GRN details');
    }
  };

  return (
    <div className="space-y-6" data-testid="rm-grn-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900" style={{ fontFamily: 'Outfit, sans-serif' }}>
            RM Goods Received
          </h2>
          <p className="text-slate-500 mt-1">{grns.length} goods receipts</p>
        </div>
        <Button 
          onClick={() => {
            setSelectedPO(null);
            setFormData({
              rm_po_id: '',
              received_date: new Date().toISOString().split('T')[0],
              reference_number: '',
              bank_account_id: '',
              notes: '',
              items: [],
            });
            setDialogOpen(true);
          }} 
          className="gap-2 bg-indigo-600 hover:bg-indigo-700" 
          data-testid="create-rm-grn-btn"
          disabled={purchaseOrders.length === 0}
        >
          <Plus className="w-4 h-4" />
          Receive Goods
        </Button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="pt-4">
            <div className="text-sm text-slate-500">Total Receipts</div>
            <div className="text-2xl font-bold mt-1">{grns.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="text-sm text-slate-500">Pending POs</div>
            <div className="text-2xl font-bold mt-1">{purchaseOrders.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="text-sm text-slate-500">Total Value Received</div>
            <div className="text-2xl font-bold mt-1">
              {formatCurrency(grns.reduce((sum, g) => sum + g.total_cost, 0))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* GRN Table */}
      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
            </div>
          ) : grns.length === 0 ? (
            <div className="text-center py-16">
              <Package className="w-12 h-12 text-slate-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-slate-900">No goods receipts yet</h3>
              <p className="text-slate-500 mt-1">Receive goods from approved purchase orders.</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="table-header">
                  <TableHead className="table-header-cell">GRN #</TableHead>
                  <TableHead className="table-header-cell">PO #</TableHead>
                  <TableHead className="table-header-cell">Supplier</TableHead>
                  <TableHead className="table-header-cell">Received Date</TableHead>
                  <TableHead className="table-header-cell text-right">Total Cost</TableHead>
                  <TableHead className="table-header-cell">Status</TableHead>
                  <TableHead className="table-header-cell w-12"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {grns.map((grn) => (
                  <TableRow key={grn.id} className="table-row" data-testid={`rm-grn-row-${grn.id}`}>
                    <TableCell className="table-cell font-medium">{grn.grn_number}</TableCell>
                    <TableCell className="table-cell">{grn.po_number}</TableCell>
                    <TableCell className="table-cell">{grn.supplier_name}</TableCell>
                    <TableCell className="table-cell text-slate-500">{grn.received_date}</TableCell>
                    <TableCell className="table-cell text-right font-medium">
                      {formatCurrency(grn.total_cost)}
                    </TableCell>
                    <TableCell className="table-cell">
                      <Badge className={grnStatusColors[grn.status]}>{grn.status.replace('_', ' ')}</Badge>
                    </TableCell>
                    <TableCell className="table-cell">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon">
                            <MoreHorizontal className="w-4 h-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => handleViewGRN(grn)}>
                            <Eye className="w-4 h-4 mr-2" />
                            View Details
                          </DropdownMenuItem>
                          {grn.status !== 'returned' && (
                            <DropdownMenuItem onClick={() => window.location.href = `/rm-grn-returns?grn_id=${grn.id}`}>
                              <RotateCcw className="w-4 h-4 mr-2" />
                              Create Return
                            </DropdownMenuItem>
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

      {/* Create GRN Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-3xl" data-testid="create-rm-grn-dialog">
          <DialogHeader>
            <DialogTitle style={{ fontFamily: 'Outfit, sans-serif' }}>Receive Raw Materials</DialogTitle>
            <DialogDescription>Select a purchase order and enter received quantities</DialogDescription>
          </DialogHeader>
          <form onSubmit={handleSubmit}>
            <div className="space-y-4 py-4 max-h-[60vh] overflow-y-auto">
              {/* PO Selection */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Purchase Order *</Label>
                  <Select 
                    value={formData.rm_po_id} 
                    onValueChange={(v) => handleSelectPO(v)}
                  >
                    <SelectTrigger data-testid="select-rm-po">
                      <SelectValue placeholder="Select PO" />
                    </SelectTrigger>
                    <SelectContent>
                      {purchaseOrders.map((po) => (
                        <SelectItem key={po.id} value={po.id}>
                          {po.po_number} - {po.supplier_name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Received Date</Label>
                  <Input
                    type="date"
                    value={formData.received_date}
                    onChange={(e) => setFormData({ ...formData, received_date: e.target.value })}
                  />
                </div>
              </div>

              {/* Payment Account for Immediate Payment */}
              {selectedPO?.payment_terms === 'immediate' && (
                <div className="p-3 bg-amber-50 rounded-lg border border-amber-200">
                  <div className="flex items-center gap-2 text-amber-700 mb-2">
                    <AlertTriangle className="w-4 h-4" />
                    <span className="font-medium">Immediate Payment Required</span>
                  </div>
                  <div className="space-y-2">
                    <Label>Pay From Account *</Label>
                    <Select 
                      value={formData.bank_account_id} 
                      onValueChange={(v) => setFormData({ ...formData, bank_account_id: v })}
                    >
                      <SelectTrigger data-testid="select-grn-payment-account">
                        <SelectValue placeholder="Select payment account" />
                      </SelectTrigger>
                      <SelectContent>
                        {bankAccounts.map((acc) => (
                          <SelectItem key={acc.id} value={acc.id}>
                            {acc.account_name} - {formatCurrency(acc.current_balance)}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              )}

              {/* Items to Receive */}
              {formData.items.length > 0 && (
                <div className="border rounded-lg overflow-hidden">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Material</TableHead>
                        <TableHead className="text-right">Ordered</TableHead>
                        <TableHead className="text-right">Received</TableHead>
                        <TableHead className="text-right">Remaining</TableHead>
                        <TableHead className="text-center">Receive Qty</TableHead>
                        <TableHead className="text-center">Unit Price</TableHead>
                        <TableHead className="text-right">Line Total</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {formData.items.map((item, index) => (
                        <TableRow key={index}>
                          <TableCell>
                            <div>{item.raw_material_name}</div>
                            <span className="text-xs text-slate-400">{item.raw_material_sku}</span>
                          </TableCell>
                          <TableCell className="text-right">{item.ordered} {item.unit}</TableCell>
                          <TableCell className="text-right">{item.already_received}</TableCell>
                          <TableCell className="text-right text-amber-600">{item.remaining}</TableCell>
                          <TableCell className="text-center">
                            <Input
                              type="number"
                              min="0"
                              max={item.remaining}
                              step="0.01"
                              value={item.received_quantity}
                              onChange={(e) => updateItemQuantity(index, e.target.value)}
                              className="w-20 text-center"
                              data-testid={`grn-qty-${index}`}
                            />
                          </TableCell>
                          <TableCell className="text-center">
                            <Input
                              type="number"
                              min="0"
                              step="0.01"
                              value={item.unit_price}
                              onChange={(e) => updateItemPrice(index, e.target.value)}
                              className="w-24 text-center"
                            />
                          </TableCell>
                          <TableCell className="text-right font-medium">
                            {formatCurrency(item.received_quantity * item.unit_price)}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              )}

              {formData.items.length === 0 && formData.rm_po_id && (
                <div className="text-center py-8 text-slate-500">
                  All items in this PO have been fully received
                </div>
              )}

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Reference Number</Label>
                  <Input
                    value={formData.reference_number}
                    onChange={(e) => setFormData({ ...formData, reference_number: e.target.value })}
                    placeholder="Supplier delivery note #"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label>Notes</Label>
                <Textarea
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  placeholder="Additional notes..."
                  rows={2}
                />
              </div>

              {/* Total */}
              <div className="flex justify-end pt-4 border-t">
                <div className="text-right">
                  <p className="text-sm text-slate-500">Total Cost</p>
                  <p className="text-2xl font-bold">{formatCurrency(calculateTotalCost())}</p>
                </div>
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>Cancel</Button>
              <Button 
                type="submit" 
                disabled={submitting || formData.items.length === 0} 
                className="bg-indigo-600 hover:bg-indigo-700"
                data-testid="submit-rm-grn"
              >
                {submitting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                Receive Goods
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* View GRN Dialog */}
      <Dialog open={viewDialogOpen} onOpenChange={setViewDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle style={{ fontFamily: 'Outfit, sans-serif' }}>
              GRN {selectedGRN?.grn_number}
            </DialogTitle>
          </DialogHeader>
          {selectedGRN && (
            <div className="space-y-4 max-h-[60vh] overflow-y-auto">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-slate-500">PO Number</p>
                  <p className="font-medium">{selectedGRN.po_number}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-500">Supplier</p>
                  <p className="font-medium">{selectedGRN.supplier_name}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-500">Received Date</p>
                  <p className="font-medium">{selectedGRN.received_date}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-500">Status</p>
                  <Badge className={grnStatusColors[selectedGRN.status]}>{selectedGRN.status.replace('_', ' ')}</Badge>
                </div>
              </div>

              <div className="border rounded-lg overflow-hidden">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Material</TableHead>
                      <TableHead className="text-right">Received</TableHead>
                      <TableHead className="text-right">Unit Price</TableHead>
                      <TableHead className="text-right">Line Total</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {selectedGRN.items.map((item, index) => (
                      <TableRow key={index}>
                        <TableCell>
                          <div>{item.raw_material_name}</div>
                          <span className="text-xs text-slate-400">{item.raw_material_sku}</span>
                        </TableCell>
                        <TableCell className="text-right">{item.received_quantity} {item.unit}</TableCell>
                        <TableCell className="text-right">{formatCurrency(item.unit_price)}</TableCell>
                        <TableCell className="text-right font-medium">{formatCurrency(item.line_total)}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>

              <div className="flex justify-end">
                <div className="text-right">
                  <p className="text-lg font-bold">Total: {formatCurrency(selectedGRN.total_cost)}</p>
                </div>
              </div>

              {selectedGRN.reference_number && (
                <div className="p-3 bg-slate-50 rounded-lg">
                  <p className="text-sm text-slate-500">Reference</p>
                  <p className="text-sm">{selectedGRN.reference_number}</p>
                </div>
              )}

              {selectedGRN.notes && (
                <div className="p-3 bg-slate-50 rounded-lg">
                  <p className="text-sm text-slate-500">Notes</p>
                  <p className="text-sm">{selectedGRN.notes}</p>
                </div>
              )}

              {/* Returns */}
              {selectedGRN.returns && selectedGRN.returns.length > 0 && (
                <div className="space-y-2">
                  <p className="font-medium">Returns</p>
                  {selectedGRN.returns.map((ret, idx) => (
                    <div key={idx} className="p-3 bg-red-50 rounded-lg text-sm">
                      <p className="font-medium">{ret.return_number}</p>
                      <p className="text-slate-500">{ret.items?.length || 0} items returned - {formatCurrency(ret.total_cost)}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default RMGRN;
