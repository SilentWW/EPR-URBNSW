import React, { useState, useEffect } from 'react';
import api from '../lib/api';
import { toast } from 'sonner';
import {
  Plus,
  Edit2,
  Trash2,
  ChevronDown,
  ChevronRight,
  FileText,
  DollarSign,
  TrendingUp,
  TrendingDown,
  Building,
  RefreshCw
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter
} from '../components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from '../components/ui/select';

const accountTypeIcons = {
  asset: TrendingUp,
  liability: TrendingDown,
  equity: Building,
  income: DollarSign,
  expense: FileText
};

const accountTypeColors = {
  asset: 'text-blue-600 bg-blue-50',
  liability: 'text-red-600 bg-red-50',
  equity: 'text-purple-600 bg-purple-50',
  income: 'text-green-600 bg-green-50',
  expense: 'text-orange-600 bg-orange-50'
};

export default function ChartOfAccounts() {
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expandedTypes, setExpandedTypes] = useState({
    asset: true,
    liability: true,
    equity: true,
    income: true,
    expense: true
  });
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingAccount, setEditingAccount] = useState(null);
  const [formData, setFormData] = useState({
    code: '',
    name: '',
    account_type: 'asset',
    category: 'current_asset',
    description: '',
    opening_balance: 0
  });
  const [nextCode, setNextCode] = useState('');

  const categories = {
    asset: [
      { value: 'current_asset', label: 'Current Asset' },
      { value: 'fixed_asset', label: 'Fixed Asset' },
      { value: 'bank', label: 'Bank' },
      { value: 'cash', label: 'Cash' },
      { value: 'accounts_receivable', label: 'Accounts Receivable' },
      { value: 'inventory', label: 'Inventory' }
    ],
    liability: [
      { value: 'current_liability', label: 'Current Liability' },
      { value: 'long_term_liability', label: 'Long Term Liability' },
      { value: 'accounts_payable', label: 'Accounts Payable' }
    ],
    equity: [
      { value: 'capital', label: 'Capital' },
      { value: 'retained_earnings', label: 'Retained Earnings' }
    ],
    income: [
      { value: 'revenue', label: 'Revenue' },
      { value: 'other_income', label: 'Other Income' }
    ],
    expense: [
      { value: 'cost_of_goods_sold', label: 'Cost of Goods Sold' },
      { value: 'operating_expense', label: 'Operating Expense' },
      { value: 'tax_expense', label: 'Tax Expense' }
    ]
  };

  useEffect(() => {
    fetchAccounts();
  }, []);

  // Fetch next account code when account type changes (for new accounts only)
  useEffect(() => {
    if (!editingAccount && isModalOpen) {
      fetchNextCode(formData.account_type);
    }
  }, [formData.account_type, editingAccount, isModalOpen]);

  const fetchNextCode = async (accountType) => {
    try {
      const response = await api.get(`/finance/chart-of-accounts/next-code/${accountType}`);
      setNextCode(response.data.next_code);
      setFormData(prev => ({ ...prev, code: response.data.next_code }));
    } catch (error) {
      console.error('Failed to fetch next code', error);
    }
  };

  const fetchAccounts = async () => {
    try {
      setLoading(true);
      const response = await api.get('/finance/chart-of-accounts');
      setAccounts(response.data);
    } catch (error) {
      if (error.response?.status === 404 || (Array.isArray(error.response?.data) && error.response?.data.length === 0)) {
        setAccounts([]);
      } else {
        toast.error('Failed to fetch accounts');
      }
    } finally {
      setLoading(false);
    }
  };

  const initializeAccounts = async () => {
    try {
      await api.post('/finance/chart-of-accounts/initialize');
      toast.success('Chart of accounts initialized');
      fetchAccounts();
    } catch (error) {
      toast.error('Failed to initialize accounts');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingAccount) {
        await api.put(`/finance/chart-of-accounts/${editingAccount.id}`, {
          name: formData.name,
          description: formData.description
        });
        toast.success('Account updated');
      } else {
        await api.post('/finance/chart-of-accounts', formData);
        toast.success('Account created');
      }
      setIsModalOpen(false);
      resetForm();
      fetchAccounts();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save account');
    }
  };

  const handleDelete = async (account) => {
    if (account.is_system) {
      toast.error('Cannot delete system account');
      return;
    }
    if (!window.confirm('Are you sure you want to delete this account?')) return;
    try {
      await api.delete(`/finance/chart-of-accounts/${account.id}`);
      toast.success('Account deleted');
      fetchAccounts();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete account');
    }
  };

  const resetForm = () => {
    setFormData({
      code: '',
      name: '',
      account_type: 'asset',
      category: 'current_asset',
      description: '',
      opening_balance: 0
    });
    setEditingAccount(null);
    setNextCode('');
  };

  const openAddModal = async () => {
    resetForm();
    setIsModalOpen(true);
    // Fetch next code after modal opens (useEffect will handle it)
  };

  const openEditModal = (account) => {
    setEditingAccount(account);
    setFormData({
      code: account.code,
      name: account.name,
      account_type: account.account_type,
      category: account.category,
      description: account.description || '',
      opening_balance: account.current_balance || 0
    });
    setIsModalOpen(true);
  };

  const groupedAccounts = accounts.reduce((acc, account) => {
    const type = account.account_type;
    if (!acc[type]) acc[type] = [];
    acc[type].push(account);
    return acc;
  }, {});

  const toggleType = (type) => {
    setExpandedTypes(prev => ({ ...prev, [type]: !prev[type] }));
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-LK', {
      style: 'currency',
      currency: 'LKR',
      minimumFractionDigits: 2
    }).format(amount);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-slate-900"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="chart-of-accounts-page">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Chart of Accounts</h1>
          <p className="text-slate-500 mt-1">Manage your accounting structure</p>
        </div>
        <div className="flex gap-2">
          {accounts.length === 0 && (
            <Button onClick={initializeAccounts} variant="outline" data-testid="init-accounts-btn">
              <RefreshCw className="w-4 h-4 mr-2" />
              Initialize Default Accounts
            </Button>
          )}
          <Button onClick={openAddModal} data-testid="add-account-btn">
            <Plus className="w-4 h-4 mr-2" />
            Add Account
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-5 gap-4">
        {['asset', 'liability', 'equity', 'income', 'expense'].map(type => {
          const Icon = accountTypeIcons[type];
          const typeAccounts = groupedAccounts[type] || [];
          const total = typeAccounts.reduce((sum, a) => sum + (a.current_balance || 0), 0);
          return (
            <div key={type} className={`p-4 rounded-lg ${accountTypeColors[type]}`}>
              <div className="flex items-center gap-2">
                <Icon className="w-5 h-5" />
                <span className="font-medium capitalize">{type}</span>
              </div>
              <p className="text-2xl font-bold mt-2">{formatCurrency(Math.abs(total))}</p>
              <p className="text-sm opacity-70">{typeAccounts.length} accounts</p>
            </div>
          );
        })}
      </div>

      {/* Accounts List */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        {['asset', 'liability', 'equity', 'income', 'expense'].map(type => {
          const Icon = accountTypeIcons[type];
          const typeAccounts = (groupedAccounts[type] || []).sort((a, b) => a.code.localeCompare(b.code));
          
          return (
            <div key={type} className="border-b border-slate-200 last:border-b-0">
              <button
                onClick={() => toggleType(type)}
                className={`w-full flex items-center justify-between p-4 hover:bg-slate-50 ${accountTypeColors[type]}`}
              >
                <div className="flex items-center gap-3">
                  <Icon className="w-5 h-5" />
                  <span className="font-semibold capitalize">{type === 'liability' ? 'Liabilities' : `${type}s`}</span>
                  <span className="text-sm opacity-70">({typeAccounts.length})</span>
                </div>
                {expandedTypes[type] ? <ChevronDown className="w-5 h-5" /> : <ChevronRight className="w-5 h-5" />}
              </button>
              
              {expandedTypes[type] && typeAccounts.length > 0 && (
                <div className="bg-white">
                  <table className="w-full">
                    <thead className="bg-slate-50 text-sm text-slate-600">
                      <tr>
                        <th className="text-left p-3 font-medium">Code</th>
                        <th className="text-left p-3 font-medium">Account Name</th>
                        <th className="text-left p-3 font-medium">Category</th>
                        <th className="text-right p-3 font-medium">Balance</th>
                        <th className="text-center p-3 font-medium">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {typeAccounts.map(account => (
                        <tr key={account.id} className="hover:bg-slate-50" data-testid={`account-row-${account.code}`}>
                          <td className="p-3 font-mono text-sm">{account.code}</td>
                          <td className="p-3">
                            <div className="flex items-center gap-2">
                              {account.name}
                              {account.is_system && (
                                <span className="px-1.5 py-0.5 text-xs bg-slate-200 text-slate-600 rounded">System</span>
                              )}
                            </div>
                          </td>
                          <td className="p-3 text-sm text-slate-600 capitalize">
                            {account.category.replace(/_/g, ' ')}
                          </td>
                          <td className="p-3 text-right font-medium">
                            {formatCurrency(account.current_balance || 0)}
                          </td>
                          <td className="p-3">
                            <div className="flex items-center justify-center gap-2">
                              <button
                                onClick={() => openEditModal(account)}
                                className="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded"
                                data-testid={`edit-account-${account.code}`}
                              >
                                <Edit2 className="w-4 h-4" />
                              </button>
                              {!account.is_system && (
                                <button
                                  onClick={() => handleDelete(account)}
                                  className="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded"
                                  data-testid={`delete-account-${account.code}`}
                                >
                                  <Trash2 className="w-4 h-4" />
                                </button>
                              )}
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Add/Edit Account Modal */}
      <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>{editingAccount ? 'Edit Account' : 'Add New Account'}</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium text-slate-700">Account Code</label>
                <Input
                  value={formData.code}
                  onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                  placeholder="e.g., 1101"
                  required
                  disabled={!!editingAccount}
                  data-testid="account-code-input"
                />
              </div>
              <div>
                <label className="text-sm font-medium text-slate-700">Account Type</label>
                <Select
                  value={formData.account_type}
                  onValueChange={(value) => setFormData({ 
                    ...formData, 
                    account_type: value,
                    category: categories[value][0].value
                  })}
                  disabled={!!editingAccount}
                >
                  <SelectTrigger data-testid="account-type-select">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="asset">Asset</SelectItem>
                    <SelectItem value="liability">Liability</SelectItem>
                    <SelectItem value="equity">Equity</SelectItem>
                    <SelectItem value="income">Income</SelectItem>
                    <SelectItem value="expense">Expense</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div>
              <label className="text-sm font-medium text-slate-700">Account Name</label>
              <Input
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="Account name"
                required
                data-testid="account-name-input"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-slate-700">Category</label>
              <Select
                value={formData.category}
                onValueChange={(value) => setFormData({ ...formData, category: value })}
                disabled={!!editingAccount}
              >
                <SelectTrigger data-testid="account-category-select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {categories[formData.account_type]?.map(cat => (
                    <SelectItem key={cat.value} value={cat.value}>{cat.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-sm font-medium text-slate-700">Description</label>
              <Input
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="Optional description"
                data-testid="account-description-input"
              />
            </div>
            {!editingAccount && (
              <div>
                <label className="text-sm font-medium text-slate-700">Opening Balance</label>
                <Input
                  type="number"
                  value={formData.opening_balance}
                  onChange={(e) => setFormData({ ...formData, opening_balance: parseFloat(e.target.value) || 0 })}
                  placeholder="0.00"
                  step="0.01"
                  data-testid="account-balance-input"
                />
              </div>
            )}
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setIsModalOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" data-testid="save-account-btn">
                {editingAccount ? 'Update' : 'Create'} Account
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
