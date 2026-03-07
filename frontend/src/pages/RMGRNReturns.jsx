import React, { useState, useEffect } from 'react';
import { rmProcurementAPI } from '../lib/api';
import api from '../lib/api';
import { useSearchParams } from 'react-router-dom';
import { Card, CardContent } from '../components/ui/card';
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
  Plus, MoreHorizontal, Eye, Loader2, RotateCcw, AlertTriangle
} from 'lucide-react';
import { toast } from 'sonner';

const formatCurrency = (amount) => {
  return new Intl.NumberFormat('en-LK', {
    style: 'currency',
    currency: 'LKR',
    minimumFractionDigits: 0,
  }).format(amount);
};

const settlementColors = {
  refund: 'bg-green-100 text-green-700',
  credit: 'bg-blue-100 text-blue-700',
};

export const RMGRNReturns = () => {
  const [searchParams] = useSearchParams();
  const preSelectedGRNId = searchParams.get('grn_id');

  const [returns, setReturns] = useState([]);
  const [grns, setGRNs] = useState([]);
  const [bankAccounts, setBankAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [selectedReturn, setSelectedReturn] = useState(null);
  const [selectedGRN, setSelectedGRN] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const [formData, setFormData] = useState({
    rm_grn_id: '',
    settlement_type: 'refund',
    refund_account_id: '',
    notes: '',
    items: [],
  });

  const fetchData = async () => {
    try {
      const [returnsRes, grnsRes, bankRes] = await Promise.all([
        rmProcurementAPI.getGRNReturns(),
        rmProcurementAPI.getGRNs(),
        api.get('/bank-accounts'),
      ]);
      
      setReturns(returnsRes.data);
      // Filter GRNs that can have returns (received or partial_return)
      setGRNs(grnsRes.data.filter(g => g.status !== 'returned'));
      setBankAccounts(bankRes.data || []);

      // Open dialog if GRN pre-selected
      if (preSelectedGRNId) {
        const grn = grnsRes.data.find(g => g.id === preSelectedGRNId);
        if (grn && grn.status !== 'returned') {
          handleSelectGRN(grn.id, grnsRes.data);
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

  const handleSelectGRN = async (grnId, grnList = grns) => {
    try {
      const response = await rmProcurementAPI.getGRN(grnId);
      const grn = response.data;
      setSelectedGRN(grn);
      
      // Calculate returnable quantities (received - already returned)
      const returnedMap = {};
      (grn.returns || []).forEach(ret => {
        (ret.items || []).forEach(item => {
          returnedMap[item.raw_material_id] = (returnedMap[item.raw_material_id] || 0) + item.return_quantity;
        });
      });

      const items = grn.items
        .map(item => {
          const alreadyReturned = returnedMap[item.raw_material_id] || 0;
          const returnable = item.received_quantity - alreadyReturned;
          return {
            raw_material_id: item.raw_material_id,
            raw_material_name: item.raw_material_name,
            raw_material_sku: item.raw_material_sku,
            unit: item.unit,
            received: item.received_quantity,
            already_returned: alreadyReturned,
            returnable,
            return_quantity: 0,
            unit_price: item.unit_price,
            reason: '',
          };
        })
        .filter(item => item.returnable > 0);

      setFormData({
        rm_grn_id: grnId,
        settlement_type: 'refund',
        refund_account_id: '',
        notes: '',
        items,
      });
    } catch (error) {
      toast.error('Failed to load GRN details');
    }
  };

  const updateItemReturnQty = (index, qty) => {
    const items = [...formData.items];
    const parsed = parseFloat(qty) || 0;
    items[index].return_quantity = Math.min(parsed, items[index].returnable);
    setFormData({ ...formData, items });
  };

  const updateItemReason = (index, reason) => {
    const items = [...formData.items];
    items[index].reason = reason;
    setFormData({ ...formData, items });
  };

  const calculateTotalReturn = () => {
    return formData.items.reduce((sum, item) => sum + (item.return_quantity * item.unit_price), 0);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    const itemsToReturn = formData.items.filter(i => i.return_quantity > 0);
    if (itemsToReturn.length === 0) {
      toast.error('Please enter return quantity for at least one item');
      return;
    }

    // Validate reasons
    const missingReason = itemsToReturn.find(i => !i.reason.trim());
    if (missingReason) {
      toast.error('Please provide a reason for each returned item');
      return;
    }

    // Validate refund account if settlement is refund
    if (formData.settlement_type === 'refund' && !formData.refund_account_id) {
      toast.error('Please select a refund account');
      return;
    }

    setSubmitting(true);
    try {
      const payload = {
        rm_grn_id: formData.rm_grn_id,
        items: itemsToReturn.map(item => ({
          raw_material_id: item.raw_material_id,
          return_quantity: item.return_quantity,
          reason: item.reason,
        })),
        settlement_type: formData.settlement_type,
        refund_account_id: formData.settlement_type === 'refund' ? formData.refund_account_id : null,
        notes: formData.notes || null,
      };

      const response = await rmProcurementAPI.createGRNReturn(payload);
      toast.success(`Return ${response.data.return_number} created successfully`);
      setDialogOpen(false);
      setSelectedGRN(null);
      setFormData({
        rm_grn_id: '',
        settlement_type: 'refund',
        refund_account_id: '',
        notes: '',
        items: [],
      });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create return');
    } finally {
      setSubmitting(false);
    }
  };

  const handleViewReturn = (ret) => {
    setSelectedReturn(ret);
    setViewDialogOpen(true);
  };

  return (
    <div className="space-y-6" data-testid="rm-grn-returns-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900" style={{ fontFamily: 'Outfit, sans-serif' }}>
            RM GRN Returns
          </h2>
          <p className="text-slate-500 mt-1">{returns.length} returns processed</p>
        </div>
        <Button 
          onClick={() => {
            setSelectedGRN(null);
            setFormData({
              rm_grn_id: '',
              settlement_type: 'refund',
              refund_account_id: '',
              notes: '',
              items: [],
            });
            setDialogOpen(true);
          }} 
          className="gap-2 bg-indigo-600 hover:bg-indigo-700" 
          data-testid="create-rm-return-btn"
          disabled={grns.length === 0}
        >
          <Plus className="w-4 h-4" />
          Create Return
        </Button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="pt-4">
            <div className="text-sm text-slate-500">Total Returns</div>
            <div className="text-2xl font-bold mt-1">{returns.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="text-sm text-slate-500">Refunds</div>
            <div className="text-2xl font-bold mt-1 text-green-600">
              {formatCurrency(returns.filter(r => r.settlement_type === 'refund').reduce((sum, r) => sum + r.total_cost, 0))}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="text-sm text-slate-500">Credits</div>
            <div className="text-2xl font-bold mt-1 text-blue-600">
              {formatCurrency(returns.filter(r => r.settlement_type === 'credit').reduce((sum, r) => sum + r.total_cost, 0))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Returns Table */}
      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
            </div>
          ) : returns.length === 0 ? (
            <div className="text-center py-16">
              <RotateCcw className="w-12 h-12 text-slate-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-slate-900">No returns yet</h3>
              <p className="text-slate-500 mt-1">Return defective materials from received goods.</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="table-header">
                  <TableHead className="table-header-cell">Return #</TableHead>
                  <TableHead className="table-header-cell">GRN #</TableHead>
                  <TableHead className="table-header-cell">Supplier</TableHead>
                  <TableHead className="table-header-cell">Date</TableHead>
                  <TableHead className="table-header-cell text-right">Total</TableHead>
                  <TableHead className="table-header-cell">Settlement</TableHead>
                  <TableHead className="table-header-cell w-12"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {returns.map((ret) => (
                  <TableRow key={ret.id} className="table-row" data-testid={`rm-return-row-${ret.id}`}>
                    <TableCell className="table-cell font-medium">{ret.return_number}</TableCell>
                    <TableCell className="table-cell">{ret.grn_number}</TableCell>
                    <TableCell className="table-cell">{ret.supplier_name}</TableCell>
                    <TableCell className="table-cell text-slate-500">
                      {new Date(ret.created_at).toLocaleDateString()}
                    </TableCell>
                    <TableCell className="table-cell text-right font-medium text-red-600">
                      -{formatCurrency(ret.total_cost)}
                    </TableCell>
                    <TableCell className="table-cell">
                      <Badge className={settlementColors[ret.settlement_type]}>{ret.settlement_type}</Badge>
                    </TableCell>
                    <TableCell className="table-cell">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon">
                            <MoreHorizontal className="w-4 h-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => handleViewReturn(ret)}>
                            <Eye className="w-4 h-4 mr-2" />
                            View Details
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

      {/* Create Return Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-3xl" data-testid="create-rm-return-dialog">
          <DialogHeader>
            <DialogTitle style={{ fontFamily: 'Outfit, sans-serif' }}>Create RM Return</DialogTitle>
            <DialogDescription>Return defective raw materials to supplier</DialogDescription>
          </DialogHeader>
          <form onSubmit={handleSubmit}>
            <div className="space-y-4 py-4 max-h-[60vh] overflow-y-auto">
              {/* GRN Selection */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Select GRN *</Label>
                  <Select 
                    value={formData.rm_grn_id} 
                    onValueChange={(v) => handleSelectGRN(v)}
                  >
                    <SelectTrigger data-testid="select-rm-grn-return">
                      <SelectValue placeholder="Select GRN" />
                    </SelectTrigger>
                    <SelectContent>
                      {grns.map((grn) => (
                        <SelectItem key={grn.id} value={grn.id}>
                          {grn.grn_number} - {grn.supplier_name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Settlement Type *</Label>
                  <Select 
                    value={formData.settlement_type} 
                    onValueChange={(v) => setFormData({ ...formData, settlement_type: v })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="refund">Refund (Credit to Bank/Cash)</SelectItem>
                      <SelectItem value="credit">Supplier Credit Note</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {/* Refund Account */}
              {formData.settlement_type === 'refund' && (
                <div className="p-3 bg-green-50 rounded-lg border border-green-200">
                  <div className="flex items-center gap-2 text-green-700 mb-2">
                    <AlertTriangle className="w-4 h-4" />
                    <span className="font-medium">Refund Account</span>
                  </div>
                  <div className="space-y-2">
                    <Label>Credit Refund To *</Label>
                    <Select 
                      value={formData.refund_account_id} 
                      onValueChange={(v) => setFormData({ ...formData, refund_account_id: v })}
                    >
                      <SelectTrigger data-testid="select-refund-account">
                        <SelectValue placeholder="Select account to receive refund" />
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

              {formData.settlement_type === 'credit' && (
                <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
                  <div className="text-blue-700 text-sm">
                    A supplier credit note will be created. You can apply this credit to future purchases.
                  </div>
                </div>
              )}

              {/* Items to Return */}
              {formData.items.length > 0 && (
                <div className="border rounded-lg overflow-hidden">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Material</TableHead>
                        <TableHead className="text-right">Received</TableHead>
                        <TableHead className="text-right">Returned</TableHead>
                        <TableHead className="text-right">Available</TableHead>
                        <TableHead className="text-center">Return Qty</TableHead>
                        <TableHead>Reason</TableHead>
                        <TableHead className="text-right">Value</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {formData.items.map((item, index) => (
                        <TableRow key={index}>
                          <TableCell>
                            <div>{item.raw_material_name}</div>
                            <span className="text-xs text-slate-400">{item.raw_material_sku}</span>
                          </TableCell>
                          <TableCell className="text-right">{item.received} {item.unit}</TableCell>
                          <TableCell className="text-right">{item.already_returned}</TableCell>
                          <TableCell className="text-right text-amber-600">{item.returnable}</TableCell>
                          <TableCell className="text-center">
                            <Input
                              type="number"
                              min="0"
                              max={item.returnable}
                              step="0.01"
                              value={item.return_quantity}
                              onChange={(e) => updateItemReturnQty(index, e.target.value)}
                              className="w-20 text-center"
                              data-testid={`return-qty-${index}`}
                            />
                          </TableCell>
                          <TableCell>
                            <Input
                              value={item.reason}
                              onChange={(e) => updateItemReason(index, e.target.value)}
                              placeholder="Reason..."
                              className="w-32"
                              data-testid={`return-reason-${index}`}
                            />
                          </TableCell>
                          <TableCell className="text-right font-medium text-red-600">
                            -{formatCurrency(item.return_quantity * item.unit_price)}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              )}

              {formData.items.length === 0 && formData.rm_grn_id && (
                <div className="text-center py-8 text-slate-500">
                  All items in this GRN have been fully returned
                </div>
              )}

              <div className="space-y-2">
                <Label>Notes</Label>
                <Textarea
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  placeholder="Additional notes about the return..."
                  rows={2}
                />
              </div>

              {/* Total */}
              <div className="flex justify-end pt-4 border-t">
                <div className="text-right">
                  <p className="text-sm text-slate-500">Total Return Value</p>
                  <p className="text-2xl font-bold text-red-600">-{formatCurrency(calculateTotalReturn())}</p>
                </div>
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>Cancel</Button>
              <Button 
                type="submit" 
                disabled={submitting || formData.items.length === 0} 
                className="bg-indigo-600 hover:bg-indigo-700"
                data-testid="submit-rm-return"
              >
                {submitting ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                Process Return
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* View Return Dialog */}
      <Dialog open={viewDialogOpen} onOpenChange={setViewDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle style={{ fontFamily: 'Outfit, sans-serif' }}>
              Return {selectedReturn?.return_number}
            </DialogTitle>
          </DialogHeader>
          {selectedReturn && (
            <div className="space-y-4 max-h-[60vh] overflow-y-auto">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-slate-500">GRN Number</p>
                  <p className="font-medium">{selectedReturn.grn_number}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-500">Supplier</p>
                  <p className="font-medium">{selectedReturn.supplier_name}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-500">Date</p>
                  <p className="font-medium">{new Date(selectedReturn.created_at).toLocaleString()}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-500">Settlement</p>
                  <Badge className={settlementColors[selectedReturn.settlement_type]}>
                    {selectedReturn.settlement_type}
                  </Badge>
                </div>
              </div>

              <div className="border rounded-lg overflow-hidden">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Material</TableHead>
                      <TableHead className="text-right">Qty Returned</TableHead>
                      <TableHead className="text-right">Unit Price</TableHead>
                      <TableHead className="text-right">Value</TableHead>
                      <TableHead>Reason</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {selectedReturn.items.map((item, index) => (
                      <TableRow key={index}>
                        <TableCell>
                          <div>{item.raw_material_name}</div>
                        </TableCell>
                        <TableCell className="text-right">{item.return_quantity}</TableCell>
                        <TableCell className="text-right">{formatCurrency(item.unit_price)}</TableCell>
                        <TableCell className="text-right font-medium text-red-600">
                          -{formatCurrency(item.line_cost)}
                        </TableCell>
                        <TableCell className="text-slate-500">{item.reason}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>

              <div className="flex justify-end">
                <div className="text-right">
                  <p className="text-lg font-bold text-red-600">Total: -{formatCurrency(selectedReturn.total_cost)}</p>
                </div>
              </div>

              {selectedReturn.notes && (
                <div className="p-3 bg-slate-50 rounded-lg">
                  <p className="text-sm text-slate-500">Notes</p>
                  <p className="text-sm">{selectedReturn.notes}</p>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default RMGRNReturns;
