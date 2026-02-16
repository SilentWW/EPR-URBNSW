import React, { useState, useEffect } from 'react';
import api from '../lib/api';
import { toast } from 'sonner';
import {
  Plus,
  Users,
  Pencil,
  Trash2,
  Building2,
  User,
  Briefcase,
  Loader2,
  TrendingUp,
  TrendingDown,
  Wallet
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Badge } from '../components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
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
    minimumFractionDigits: 0
  }).format(amount);
};

export default function Investors() {
  const [investors, setInvestors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isInvestmentModalOpen, setIsInvestmentModalOpen] = useState(false);
  const [isWithdrawalModalOpen, setIsWithdrawalModalOpen] = useState(false);
  const [selectedInvestor, setSelectedInvestor] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const [formData, setFormData] = useState({
    name: '',
    investor_type: 'director',
    email: '',
    phone: '',
    id_number: '',
    address: '',
    notes: ''
  });

  const [investmentData, setInvestmentData] = useState({
    investor_id: '',
    amount: '',
    payment_method: 'bank',
    reference: '',
    notes: ''
  });

  const [withdrawalData, setWithdrawalData] = useState({
    investor_id: '',
    amount: '',
    reason: '',
    payment_method: 'bank',
    reference: '',
    notes: ''
  });

  useEffect(() => {
    fetchInvestors();
  }, []);

  const fetchInvestors = async () => {
    try {
      setLoading(true);
      const response = await api.get('/simple-finance/investors');
      setInvestors(response.data);
    } catch (error) {
      toast.error('Failed to fetch investors');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);

    try {
      const data = {
        ...formData,
        share_percentage: formData.share_percentage ? parseFloat(formData.share_percentage) : null
      };

      if (selectedInvestor) {
        await api.put(`/simple-finance/investors/${selectedInvestor.id}`, data);
        toast.success('Investor updated successfully');
      } else {
        await api.post('/simple-finance/investors', data);
        toast.success('Investor created with capital account');
      }

      setIsModalOpen(false);
      resetForm();
      fetchInvestors();
    } catch (error) {
      const detail = error.response?.data?.detail;
      toast.error(typeof detail === 'string' ? detail : 'Operation failed');
    } finally {
      setSubmitting(false);
    }
  };

  const handleInvestment = async (e) => {
    e.preventDefault();
    setSubmitting(true);

    try {
      const response = await api.post('/simple-finance/capital-investment', {
        ...investmentData,
        amount: parseFloat(investmentData.amount)
      });
      toast.success(response.data.message);
      setIsInvestmentModalOpen(false);
      setInvestmentData({ investor_id: '', amount: '', payment_method: 'bank', reference: '', notes: '' });
      fetchInvestors();
    } catch (error) {
      const detail = error.response?.data?.detail;
      toast.error(typeof detail === 'string' ? detail : 'Failed to record investment');
    } finally {
      setSubmitting(false);
    }
  };

  const handleWithdrawal = async (e) => {
    e.preventDefault();
    setSubmitting(true);

    try {
      const response = await api.post('/simple-finance/capital-withdrawal', {
        ...withdrawalData,
        amount: parseFloat(withdrawalData.amount)
      });
      toast.success(response.data.message);
      setIsWithdrawalModalOpen(false);
      setWithdrawalData({ investor_id: '', amount: '', reason: '', payment_method: 'bank', reference: '', notes: '' });
      fetchInvestors();
    } catch (error) {
      const detail = error.response?.data?.detail;
      toast.error(typeof detail === 'string' ? detail : 'Failed to record withdrawal');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (investor) => {
    if (!window.confirm(`Are you sure you want to delete ${investor.name}?`)) return;

    try {
      await api.delete(`/simple-finance/investors/${investor.id}`);
      toast.success('Investor deleted successfully');
      fetchInvestors();
    } catch (error) {
      const detail = error.response?.data?.detail;
      toast.error(typeof detail === 'string' ? detail : 'Failed to delete investor');
    }
  };

  const openEditModal = (investor) => {
    setSelectedInvestor(investor);
    setFormData({
      name: investor.name,
      investor_type: investor.investor_type,
      email: investor.email || '',
      phone: investor.phone || '',
      id_number: investor.id_number || '',
      address: investor.address || '',
      share_percentage: investor.share_percentage?.toString() || '',
      notes: investor.notes || ''
    });
    setIsModalOpen(true);
  };

  const resetForm = () => {
    setSelectedInvestor(null);
    setFormData({
      name: '',
      investor_type: 'director',
      email: '',
      phone: '',
      id_number: '',
      address: '',
      share_percentage: '',
      notes: ''
    });
  };

  const totalCapital = investors.reduce((sum, inv) => sum + (inv.capital_balance || 0), 0);
  const directorCapital = investors.filter(i => i.investor_type === 'director').reduce((sum, inv) => sum + (inv.capital_balance || 0), 0);
  const shareholderCapital = investors.filter(i => i.investor_type === 'shareholder').reduce((sum, inv) => sum + (inv.capital_balance || 0), 0);

  const getTypeIcon = (type) => {
    switch (type) {
      case 'director': return <Briefcase className="w-4 h-4" />;
      case 'shareholder': return <User className="w-4 h-4" />;
      case 'partner': return <Users className="w-4 h-4" />;
      default: return <Building2 className="w-4 h-4" />;
    }
  };

  const getTypeBadgeColor = (type) => {
    switch (type) {
      case 'director': return 'bg-purple-100 text-purple-700';
      case 'shareholder': return 'bg-blue-100 text-blue-700';
      case 'partner': return 'bg-green-100 text-green-700';
      default: return 'bg-gray-100 text-gray-700';
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
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Investors Management</h1>
          <p className="text-slate-500 mt-1">Manage directors, shareholders and their capital accounts</p>
        </div>
        <div className="flex gap-2">
          <Button 
            variant="outline" 
            onClick={() => setIsWithdrawalModalOpen(true)}
            disabled={investors.length === 0}
          >
            <TrendingDown className="w-4 h-4 mr-2" />
            Withdrawal
          </Button>
          <Button 
            variant="outline" 
            onClick={() => setIsInvestmentModalOpen(true)}
            disabled={investors.length === 0}
            className="bg-green-50 border-green-200 text-green-700 hover:bg-green-100"
          >
            <TrendingUp className="w-4 h-4 mr-2" />
            Add Investment
          </Button>
          <Button onClick={() => { resetForm(); setIsModalOpen(true); }} className="bg-indigo-600 hover:bg-indigo-700">
            <Plus className="w-4 h-4 mr-2" />
            Add Investor
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Total Capital</p>
                <p className="text-2xl font-bold text-slate-900">{formatCurrency(totalCapital)}</p>
              </div>
              <div className="w-12 h-12 bg-indigo-100 rounded-full flex items-center justify-center">
                <Wallet className="w-6 h-6 text-indigo-600" />
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Directors&apos; Capital</p>
                <p className="text-2xl font-bold text-purple-600">{formatCurrency(directorCapital)}</p>
              </div>
              <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center">
                <Briefcase className="w-6 h-6 text-purple-600" />
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Shareholders&apos; Capital</p>
                <p className="text-2xl font-bold text-blue-600">{formatCurrency(shareholderCapital)}</p>
              </div>
              <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                <User className="w-6 h-6 text-blue-600" />
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Total Investors</p>
                <p className="text-2xl font-bold text-slate-900">{investors.length}</p>
              </div>
              <div className="w-12 h-12 bg-slate-100 rounded-full flex items-center justify-center">
                <Users className="w-6 h-6 text-slate-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Investors Table */}
      <Card>
        <CardHeader>
          <CardTitle>All Investors</CardTitle>
        </CardHeader>
        <CardContent>
          {investors.length === 0 ? (
            <div className="text-center py-12">
              <Users className="w-12 h-12 mx-auto text-slate-300 mb-4" />
              <p className="text-slate-500">No investors added yet</p>
              <p className="text-sm text-slate-400">Add directors and shareholders to track their capital</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Account Code</TableHead>
                  <TableHead>Contact</TableHead>
                  <TableHead>Share %</TableHead>
                  <TableHead className="text-right">Capital Balance</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {investors.map((investor) => (
                  <TableRow key={investor.id}>
                    <TableCell className="font-medium">{investor.name}</TableCell>
                    <TableCell>
                      <Badge className={getTypeBadgeColor(investor.investor_type)}>
                        <span className="flex items-center gap-1">
                          {getTypeIcon(investor.investor_type)}
                          {investor.investor_type.charAt(0).toUpperCase() + investor.investor_type.slice(1)}
                        </span>
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <code className="bg-slate-100 px-2 py-1 rounded text-sm">
                        {investor.account_code}
                      </code>
                    </TableCell>
                    <TableCell>
                      <div className="text-sm">
                        {investor.email && <div>{investor.email}</div>}
                        {investor.phone && <div className="text-slate-500">{investor.phone}</div>}
                      </div>
                    </TableCell>
                    <TableCell>
                      {investor.share_percentage ? `${investor.share_percentage}%` : '-'}
                    </TableCell>
                    <TableCell className="text-right font-semibold">
                      {formatCurrency(investor.capital_balance || 0)}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-1">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            setInvestmentData({ ...investmentData, investor_id: investor.id });
                            setIsInvestmentModalOpen(true);
                          }}
                          title="Add Investment"
                        >
                          <TrendingUp className="w-4 h-4 text-green-600" />
                        </Button>
                        <Button variant="ghost" size="sm" onClick={() => openEditModal(investor)}>
                          <Pencil className="w-4 h-4" />
                        </Button>
                        <Button variant="ghost" size="sm" onClick={() => handleDelete(investor)}>
                          <Trash2 className="w-4 h-4 text-red-500" />
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

      {/* Add/Edit Investor Modal */}
      <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>{selectedInvestor ? 'Edit Investor' : 'Add New Investor'}</DialogTitle>
            <DialogDescription>
              {selectedInvestor ? 'Update investor details' : 'Add a director, shareholder, or partner with auto-created capital account'}
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleSubmit}>
            <div className="grid gap-4 py-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Name *</Label>
                  <Input
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="Full name"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label>Type *</Label>
                  <Select
                    value={formData.investor_type}
                    onValueChange={(value) => setFormData({ ...formData, investor_type: value })}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="director">Director</SelectItem>
                      <SelectItem value="shareholder">Shareholder</SelectItem>
                      <SelectItem value="partner">Partner</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Email</Label>
                  <Input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    placeholder="email@example.com"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Phone</Label>
                  <Input
                    value={formData.phone}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                    placeholder="+94 77 123 4567"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>ID Number (NIC/Passport)</Label>
                  <Input
                    value={formData.id_number}
                    onChange={(e) => setFormData({ ...formData, id_number: e.target.value })}
                    placeholder="National ID or Passport"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Share %</Label>
                  <div className="relative">
                    <Input
                      type="text"
                      value={selectedInvestor ? `${selectedInvestor.share_percentage || 0}%` : 'Auto-calculated'}
                      disabled
                      className="bg-slate-50 text-slate-500"
                    />
                  </div>
                  <p className="text-xs text-slate-400">Automatically calculated based on capital investment</p>
                </div>
              </div>
              <div className="space-y-2">
                <Label>Address</Label>
                <Textarea
                  value={formData.address}
                  onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                  placeholder="Full address"
                  rows={2}
                />
              </div>
              <div className="space-y-2">
                <Label>Notes</Label>
                <Textarea
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  placeholder="Additional notes"
                  rows={2}
                />
              </div>
              {!selectedInvestor && (
                <div className="bg-blue-50 p-3 rounded-lg text-sm text-blue-800">
                  <strong>Note:</strong> Share percentage will be automatically calculated based on capital investments.
                  After creating the investor, add capital investment to set their share.
                </div>
              )}
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setIsModalOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={submitting} className="bg-indigo-600 hover:bg-indigo-700">
                {submitting && <Loader2 className="w-4 h-4 animate-spin mr-2" />}
                {selectedInvestor ? 'Update' : 'Create Investor'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Capital Investment Modal */}
      <Dialog open={isInvestmentModalOpen} onOpenChange={setIsInvestmentModalOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-green-700">
              <TrendingUp className="w-5 h-5" />
              Record Capital Investment
            </DialogTitle>
            <DialogDescription>
              Record when an investor puts money into the business
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleInvestment}>
            <div className="grid gap-4 py-4">
              <div className="space-y-2">
                <Label>Select Investor *</Label>
                <Select
                  value={investmentData.investor_id}
                  onValueChange={(value) => setInvestmentData({ ...investmentData, investor_id: value })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Choose investor" />
                  </SelectTrigger>
                  <SelectContent>
                    {investors.map((inv) => (
                      <SelectItem key={inv.id} value={inv.id}>
                        {inv.name} ({inv.investor_type})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Investment Amount (LKR) *</Label>
                <Input
                  type="number"
                  min="0"
                  step="0.01"
                  value={investmentData.amount}
                  onChange={(e) => setInvestmentData({ ...investmentData, amount: e.target.value })}
                  placeholder="Enter amount"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label>Payment Method</Label>
                <Select
                  value={investmentData.payment_method}
                  onValueChange={(value) => setInvestmentData({ ...investmentData, payment_method: value })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="bank">Bank Transfer</SelectItem>
                    <SelectItem value="cash">Cash</SelectItem>
                    <SelectItem value="cheque">Cheque</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Reference Number</Label>
                <Input
                  value={investmentData.reference}
                  onChange={(e) => setInvestmentData({ ...investmentData, reference: e.target.value })}
                  placeholder="Transaction reference"
                />
              </div>
              <div className="space-y-2">
                <Label>Notes</Label>
                <Textarea
                  value={investmentData.notes}
                  onChange={(e) => setInvestmentData({ ...investmentData, notes: e.target.value })}
                  placeholder="Additional notes"
                  rows={2}
                />
              </div>
              <div className="bg-green-50 p-3 rounded-lg text-sm text-green-800">
                <strong>Auto Journal Entry:</strong><br />
                • Debit: Cash/Bank<br />
                • Credit: Investor&apos;s Capital Account
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setIsInvestmentModalOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={submitting} className="bg-green-600 hover:bg-green-700">
                {submitting && <Loader2 className="w-4 h-4 animate-spin mr-2" />}
                Record Investment
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Capital Withdrawal Modal */}
      <Dialog open={isWithdrawalModalOpen} onOpenChange={setIsWithdrawalModalOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-amber-700">
              <TrendingDown className="w-5 h-5" />
              Record Capital Withdrawal
            </DialogTitle>
            <DialogDescription>
              Record when an investor takes money out of the business
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleWithdrawal}>
            <div className="grid gap-4 py-4">
              <div className="space-y-2">
                <Label>Select Investor *</Label>
                <Select
                  value={withdrawalData.investor_id}
                  onValueChange={(value) => setWithdrawalData({ ...withdrawalData, investor_id: value })}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Choose investor" />
                  </SelectTrigger>
                  <SelectContent>
                    {investors.map((inv) => (
                      <SelectItem key={inv.id} value={inv.id}>
                        {inv.name} - Balance: {formatCurrency(inv.capital_balance || 0)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Withdrawal Amount (LKR) *</Label>
                <Input
                  type="number"
                  min="0"
                  step="0.01"
                  value={withdrawalData.amount}
                  onChange={(e) => setWithdrawalData({ ...withdrawalData, amount: e.target.value })}
                  placeholder="Enter amount"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label>Reason *</Label>
                <Input
                  value={withdrawalData.reason}
                  onChange={(e) => setWithdrawalData({ ...withdrawalData, reason: e.target.value })}
                  placeholder="e.g., Personal drawings, Dividend"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label>Payment Method</Label>
                <Select
                  value={withdrawalData.payment_method}
                  onValueChange={(value) => setWithdrawalData({ ...withdrawalData, payment_method: value })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="bank">Bank Transfer</SelectItem>
                    <SelectItem value="cash">Cash</SelectItem>
                    <SelectItem value="cheque">Cheque</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="bg-amber-50 p-3 rounded-lg text-sm text-amber-800">
                <strong>Auto Journal Entry:</strong><br />
                • Debit: Investor&apos;s Capital Account<br />
                • Credit: Cash/Bank
              </div>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setIsWithdrawalModalOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={submitting} className="bg-amber-600 hover:bg-amber-700">
                {submitting && <Loader2 className="w-4 h-4 animate-spin mr-2" />}
                Record Withdrawal
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
