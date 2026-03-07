import React, { useState, useEffect } from 'react';
import { payrollAPI } from '../../lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Switch } from '../../components/ui/switch';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../../components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../../components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../../components/ui/table';
import { Plus, Loader2, Settings, Percent, Trash2, AlertTriangle, Save } from 'lucide-react';
import { toast } from 'sonner';

export const SalaryStructure = () => {
  const [settings, setSettings] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [addAllowanceOpen, setAddAllowanceOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedAllowance, setSelectedAllowance] = useState(null);

  const [rateForm, setRateForm] = useState({
    epf_employee_rate: 8,
    epf_employer_rate: 12,
    etf_employer_rate: 3,
    overtime_weekday_rate: 1.25,
    overtime_weekend_rate: 1.5,
  });

  const [newAllowance, setNewAllowance] = useState({
    name: '',
    type: 'fixed',
    value: '',
    is_taxable: true,
  });

  const fetchSettings = async () => {
    try {
      const response = await payrollAPI.getSalaryStructure();
      setSettings(response.data);
      setRateForm({
        epf_employee_rate: response.data.epf_employee_rate || 8,
        epf_employer_rate: response.data.epf_employer_rate || 12,
        etf_employer_rate: response.data.etf_employer_rate || 3,
        overtime_weekday_rate: response.data.overtime_weekday_rate || 1.25,
        overtime_weekend_rate: response.data.overtime_weekend_rate || 1.5,
      });
    } catch (error) {
      toast.error('Failed to fetch salary structure');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSettings();
  }, []);

  const handleSaveRates = async () => {
    setSaving(true);
    try {
      await payrollAPI.updateSalaryStructure(rateForm);
      toast.success('Rates updated successfully');
      fetchSettings();
    } catch (error) {
      toast.error('Failed to update rates');
    } finally {
      setSaving(false);
    }
  };

  const handleAddAllowance = async () => {
    if (!newAllowance.name || !newAllowance.value) {
      toast.error('Please fill all fields');
      return;
    }

    setSaving(true);
    try {
      await payrollAPI.addAllowance({
        name: newAllowance.name,
        type: newAllowance.type,
        value: parseFloat(newAllowance.value),
        is_taxable: newAllowance.is_taxable,
        applies_to: [],
      });
      toast.success('Allowance added successfully');
      setAddAllowanceOpen(false);
      setNewAllowance({ name: '', type: 'fixed', value: '', is_taxable: true });
      fetchSettings();
    } catch (error) {
      toast.error('Failed to add allowance');
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteAllowance = async () => {
    try {
      await payrollAPI.deleteAllowance(selectedAllowance.id);
      toast.success('Allowance deleted');
      setDeleteDialogOpen(false);
      fetchSettings();
    } catch (error) {
      toast.error('Failed to delete allowance');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="salary-structure-page">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-slate-900" style={{ fontFamily: 'Outfit, sans-serif' }}>
          Salary Structure
        </h2>
        <p className="text-slate-500 mt-1">Configure statutory rates, allowances, and deductions</p>
      </div>

      {/* Statutory Rates */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Percent className="w-5 h-5" />
            Statutory Rates
          </CardTitle>
          <CardDescription>EPF, ETF and overtime calculation rates</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* EPF Rates */}
            <div className="space-y-4 p-4 bg-blue-50 rounded-lg">
              <h4 className="font-medium text-blue-900">EPF (Employees' Provident Fund)</h4>
              <div className="space-y-3">
                <div>
                  <Label className="text-sm text-blue-700">Employee Contribution (%)</Label>
                  <Input
                    type="number"
                    step="0.1"
                    value={rateForm.epf_employee_rate}
                    onChange={(e) => setRateForm({ ...rateForm, epf_employee_rate: parseFloat(e.target.value) })}
                    className="mt-1"
                    data-testid="epf-employee-rate"
                  />
                </div>
                <div>
                  <Label className="text-sm text-blue-700">Employer Contribution (%)</Label>
                  <Input
                    type="number"
                    step="0.1"
                    value={rateForm.epf_employer_rate}
                    onChange={(e) => setRateForm({ ...rateForm, epf_employer_rate: parseFloat(e.target.value) })}
                    className="mt-1"
                    data-testid="epf-employer-rate"
                  />
                </div>
              </div>
            </div>

            {/* ETF Rate */}
            <div className="space-y-4 p-4 bg-emerald-50 rounded-lg">
              <h4 className="font-medium text-emerald-900">ETF (Employees' Trust Fund)</h4>
              <div>
                <Label className="text-sm text-emerald-700">Employer Contribution (%)</Label>
                <Input
                  type="number"
                  step="0.1"
                  value={rateForm.etf_employer_rate}
                  onChange={(e) => setRateForm({ ...rateForm, etf_employer_rate: parseFloat(e.target.value) })}
                  className="mt-1"
                  data-testid="etf-rate"
                />
              </div>
              <p className="text-xs text-emerald-600">
                Standard rate: 3% of basic salary
              </p>
            </div>

            {/* Overtime Rates */}
            <div className="space-y-4 p-4 bg-amber-50 rounded-lg">
              <h4 className="font-medium text-amber-900">Overtime Multipliers</h4>
              <div className="space-y-3">
                <div>
                  <Label className="text-sm text-amber-700">Weekday Rate (x)</Label>
                  <Input
                    type="number"
                    step="0.05"
                    value={rateForm.overtime_weekday_rate}
                    onChange={(e) => setRateForm({ ...rateForm, overtime_weekday_rate: parseFloat(e.target.value) })}
                    className="mt-1"
                    data-testid="ot-weekday-rate"
                  />
                </div>
                <div>
                  <Label className="text-sm text-amber-700">Weekend/Holiday Rate (x)</Label>
                  <Input
                    type="number"
                    step="0.05"
                    value={rateForm.overtime_weekend_rate}
                    onChange={(e) => setRateForm({ ...rateForm, overtime_weekend_rate: parseFloat(e.target.value) })}
                    className="mt-1"
                    data-testid="ot-weekend-rate"
                  />
                </div>
              </div>
            </div>
          </div>

          <div className="flex justify-end">
            <Button onClick={handleSaveRates} disabled={saving} className="bg-indigo-600 hover:bg-indigo-700" data-testid="save-rates-btn">
              {saving ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Save className="w-4 h-4 mr-2" />}
              Save Rates
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Allowances */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>Allowances</CardTitle>
            <CardDescription>Configure default allowances for employees</CardDescription>
          </div>
          <Button onClick={() => setAddAllowanceOpen(true)} className="bg-indigo-600 hover:bg-indigo-700" data-testid="add-allowance-btn">
            <Plus className="w-4 h-4 mr-2" />
            Add Allowance
          </Button>
        </CardHeader>
        <CardContent>
          {settings?.allowances?.length === 0 ? (
            <div className="text-center py-8 text-slate-500">
              No allowances configured yet. Add your first allowance.
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Allowance Name</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead className="text-right">Value</TableHead>
                  <TableHead className="text-center">Taxable</TableHead>
                  <TableHead className="w-12"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {settings?.allowances?.map((allowance) => (
                  <TableRow key={allowance.id}>
                    <TableCell className="font-medium">{allowance.name}</TableCell>
                    <TableCell className="capitalize">{allowance.type}</TableCell>
                    <TableCell className="text-right">
                      {allowance.type === 'percentage' ? `${allowance.value}%` : `LKR ${allowance.value.toLocaleString()}`}
                    </TableCell>
                    <TableCell className="text-center">
                      {allowance.is_taxable ? (
                        <span className="text-green-600">Yes</span>
                      ) : (
                        <span className="text-slate-400">No</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => {
                          setSelectedAllowance(allowance);
                          setDeleteDialogOpen(true);
                        }}
                      >
                        <Trash2 className="w-4 h-4 text-red-500" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Tax Slabs Info */}
      <Card>
        <CardHeader>
          <CardTitle>PAYE Tax Slabs (Sri Lanka)</CardTitle>
          <CardDescription>Automatic tax calculation based on monthly income</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Income Range (LKR)</TableHead>
                <TableHead className="text-right">Tax Rate</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {settings?.tax_slabs?.map((slab, index) => (
                <TableRow key={index}>
                  <TableCell>
                    {slab.min.toLocaleString()} - {slab.max ? slab.max.toLocaleString() : 'Above'}
                  </TableCell>
                  <TableCell className="text-right font-medium">{slab.rate}%</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
          <p className="text-sm text-slate-500 mt-4">
            * Tax slabs are based on current Sri Lanka PAYE regulations. Contact admin to update.
          </p>
        </CardContent>
      </Card>

      {/* Add Allowance Dialog */}
      <Dialog open={addAllowanceOpen} onOpenChange={setAddAllowanceOpen}>
        <DialogContent data-testid="add-allowance-dialog">
          <DialogHeader>
            <DialogTitle>Add Allowance</DialogTitle>
            <DialogDescription>Create a new allowance type</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Allowance Name *</Label>
              <Input
                value={newAllowance.name}
                onChange={(e) => setNewAllowance({ ...newAllowance, name: e.target.value })}
                placeholder="e.g., Performance Bonus"
                data-testid="allowance-name"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Type</Label>
                <Select 
                  value={newAllowance.type} 
                  onValueChange={(v) => setNewAllowance({ ...newAllowance, type: v })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="fixed">Fixed Amount</SelectItem>
                    <SelectItem value="percentage">% of Basic</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Value *</Label>
                <Input
                  type="number"
                  value={newAllowance.value}
                  onChange={(e) => setNewAllowance({ ...newAllowance, value: e.target.value })}
                  placeholder={newAllowance.type === 'percentage' ? '10' : '5000'}
                  data-testid="allowance-value"
                />
              </div>
            </div>
            <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
              <div>
                <Label>Taxable</Label>
                <p className="text-sm text-slate-500">Include in taxable income</p>
              </div>
              <Switch
                checked={newAllowance.is_taxable}
                onCheckedChange={(v) => setNewAllowance({ ...newAllowance, is_taxable: v })}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setAddAllowanceOpen(false)}>Cancel</Button>
            <Button onClick={handleAddAllowance} disabled={saving} className="bg-indigo-600 hover:bg-indigo-700" data-testid="submit-allowance-btn">
              {saving ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
              Add Allowance
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-red-600">
              <AlertTriangle className="w-5 h-5" />
              Delete Allowance
            </DialogTitle>
            <DialogDescription>
              Are you sure you want to delete "{selectedAllowance?.name}"? This won't affect existing payroll records.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
            <Button variant="destructive" onClick={handleDeleteAllowance}>Delete</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default SalaryStructure;
