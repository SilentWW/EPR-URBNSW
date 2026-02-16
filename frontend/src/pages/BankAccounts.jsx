import React, { useState, useEffect } from 'react';
import { Building2, Plus, Wallet, ArrowRightLeft, TrendingUp, TrendingDown, MoreVertical, Eye, Pencil, Trash2, RefreshCw } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '../components/ui/dropdown-menu';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { toast } from 'sonner';
import api from '../lib/api';

export default function BankAccounts() {
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isTransferModalOpen, setIsTransferModalOpen] = useState(false);
  const [isTransactionModalOpen, setIsTransactionModalOpen] = useState(false);
  const [isViewModalOpen, setIsViewModalOpen] = useState(false);
  const [selectedAccount, setSelectedAccount] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [editingAccount, setEditingAccount] = useState(null);

  const [formData, setFormData] = useState({
    account_name: '',
    account_type: 'bank',
    bank_name: '',
    account_number: '',
    branch: '',
    opening_balance: 0,
    description: ''
  });

  const [transferData, setTransferData] = useState({
    from_account_id: '',
    to_account_id: '',
    amount: 0,
    description: '',
    transaction_date: new Date().toISOString().split('T')[0]
  });

  const [transactionData, setTransactionData] = useState({
    bank_account_id: '',
    transaction_type: 'deposit',
    amount: 0,
    description: '',
    transaction_date: new Date().toISOString().split('T')[0]
  });

  useEffect(() => {
    fetchAccounts();
  }, []);

  const fetchAccounts = async () => {
    try {
      setLoading(true);
      const response = await api.get('/bank-accounts');
      setAccounts(response.data);
    } catch (error) {
      toast.error('Failed to fetch bank accounts');
    } finally {
      setLoading(false);
    }
  };

  const fetchTransactions = async (accountId) => {
    try {
      const response = await api.get(`/bank-accounts/${accountId}/transactions`);
      setTransactions(response.data);
    } catch (error) {
      toast.error('Failed to fetch transactions');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingAccount) {
        await api.put(`/bank-accounts/${editingAccount.id}`, formData);
        toast.success('Account updated successfully');
      } else {
        await api.post('/bank-accounts', formData);
        toast.success('Account created successfully');
      }
      setIsModalOpen(false);
      resetForm();
      fetchAccounts();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save account');
    }
  };

  const handleTransfer = async (e) => {
    e.preventDefault();
    try {
      await api.post('/bank-accounts/transfer', transferData);
      toast.success('Transfer completed successfully');
      setIsTransferModalOpen(false);
      resetTransferForm();
      fetchAccounts();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Transfer failed');
    }
  };

  const handleTransaction = async (e) => {
    e.preventDefault();
    try {
      await api.post(`/bank-accounts/${transactionData.bank_account_id}/transactions`, transactionData);
      toast.success('Transaction recorded successfully');
      setIsTransactionModalOpen(false);
      resetTransactionForm();
      fetchAccounts();
      if (selectedAccount) {
        fetchTransactions(selectedAccount.id);
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to record transaction');
    }
  };

  const handleDelete = async (accountId) => {
    if (!confirm('Are you sure you want to delete this account?')) return;
    try {
      await api.delete(`/bank-accounts/${accountId}`);
      toast.success('Account deleted');
      fetchAccounts();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete account');
    }
  };

  const handleView = async (account) => {
    setSelectedAccount(account);
    await fetchTransactions(account.id);
    setIsViewModalOpen(true);
  };

  const handleEdit = (account) => {
    setEditingAccount(account);
    setFormData({
      account_name: account.account_name,
      account_type: account.account_type,
      bank_name: account.bank_name || '',
      account_number: account.account_number || '',
      branch: account.branch || '',
      opening_balance: account.opening_balance,
      description: account.description || ''
    });
    setIsModalOpen(true);
  };

  const resetForm = () => {
    setFormData({
      account_name: '',
      account_type: 'bank',
      bank_name: '',
      account_number: '',
      branch: '',
      opening_balance: 0,
      description: ''
    });
    setEditingAccount(null);
  };

  const resetTransferForm = () => {
    setTransferData({
      from_account_id: '',
      to_account_id: '',
      amount: 0,
      description: '',
      transaction_date: new Date().toISOString().split('T')[0]
    });
  };

  const resetTransactionForm = () => {
    setTransactionData({
      bank_account_id: '',
      transaction_type: 'deposit',
      amount: 0,
      description: '',
      transaction_date: new Date().toISOString().split('T')[0]
    });
  };

  const openNewAccountModal = () => {
    resetForm();
    setIsModalOpen(true);
  };

  const openTransactionModal = (account) => {
    setTransactionData({
      ...transactionData,
      bank_account_id: account.id
    });
    setSelectedAccount(account);
    setIsTransactionModalOpen(true);
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-LK', { style: 'currency', currency: 'LKR' }).format(amount || 0);
  };

  const getTotalBalance = () => {
    return accounts.reduce((sum, acc) => sum + (acc.current_balance || 0), 0);
  };

  const getCashTotal = () => {
    return accounts.filter(a => a.account_type === 'cash').reduce((sum, acc) => sum + (acc.current_balance || 0), 0);
  };

  const getBankTotal = () => {
    return accounts.filter(a => a.account_type === 'bank').reduce((sum, acc) => sum + (acc.current_balance || 0), 0);
  };

  return (
    <div className="space-y-6" data-testid="bank-accounts-page">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Bank & Cash Accounts</h1>
          <p className="text-slate-500">Manage your business bank accounts and cash</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => setIsTransferModalOpen(true)} data-testid="transfer-btn">
            <ArrowRightLeft className="w-4 h-4 mr-2" />
            Transfer
          </Button>
          <Button onClick={openNewAccountModal} data-testid="add-account-btn">
            <Plus className="w-4 h-4 mr-2" />
            Add Account
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-green-100 rounded-lg">
                <Wallet className="w-6 h-6 text-green-600" />
              </div>
              <div>
                <p className="text-sm text-slate-500">Total Balance</p>
                <p className="text-2xl font-bold text-slate-900">{formatCurrency(getTotalBalance())}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-blue-100 rounded-lg">
                <Building2 className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-slate-500">Bank Accounts</p>
                <p className="text-2xl font-bold text-slate-900">{formatCurrency(getBankTotal())}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-amber-100 rounded-lg">
                <Wallet className="w-6 h-6 text-amber-600" />
              </div>
              <div>
                <p className="text-sm text-slate-500">Cash on Hand</p>
                <p className="text-2xl font-bold text-slate-900">{formatCurrency(getCashTotal())}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Accounts List */}
      <Tabs defaultValue="all">
        <TabsList>
          <TabsTrigger value="all">All Accounts ({accounts.length})</TabsTrigger>
          <TabsTrigger value="bank">Bank ({accounts.filter(a => a.account_type === 'bank').length})</TabsTrigger>
          <TabsTrigger value="cash">Cash ({accounts.filter(a => a.account_type === 'cash').length})</TabsTrigger>
        </TabsList>

        <TabsContent value="all" className="mt-4">
          <AccountsList 
            accounts={accounts} 
            onView={handleView} 
            onEdit={handleEdit} 
            onDelete={handleDelete}
            onTransaction={openTransactionModal}
            formatCurrency={formatCurrency}
          />
        </TabsContent>
        <TabsContent value="bank" className="mt-4">
          <AccountsList 
            accounts={accounts.filter(a => a.account_type === 'bank')} 
            onView={handleView} 
            onEdit={handleEdit} 
            onDelete={handleDelete}
            onTransaction={openTransactionModal}
            formatCurrency={formatCurrency}
          />
        </TabsContent>
        <TabsContent value="cash" className="mt-4">
          <AccountsList 
            accounts={accounts.filter(a => a.account_type === 'cash')} 
            onView={handleView} 
            onEdit={handleEdit} 
            onDelete={handleDelete}
            onTransaction={openTransactionModal}
            formatCurrency={formatCurrency}
          />
        </TabsContent>
      </Tabs>

      {/* Add/Edit Account Modal */}
      <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>{editingAccount ? 'Edit Account' : 'Add New Account'}</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-sm font-medium text-slate-700">Account Name *</label>
              <Input
                value={formData.account_name}
                onChange={(e) => setFormData({ ...formData, account_name: e.target.value })}
                placeholder="e.g., Main Business Account"
                required
                data-testid="account-name-input"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-slate-700">Account Type *</label>
              <Select
                value={formData.account_type}
                onValueChange={(value) => setFormData({ ...formData, account_type: value })}
                disabled={!!editingAccount}
              >
                <SelectTrigger data-testid="account-type-select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="bank">Bank Account</SelectItem>
                  <SelectItem value="cash">Cash Account</SelectItem>
                </SelectContent>
              </Select>
            </div>
            {formData.account_type === 'bank' && (
              <>
                <div>
                  <label className="text-sm font-medium text-slate-700">Bank Name</label>
                  <Input
                    value={formData.bank_name}
                    onChange={(e) => setFormData({ ...formData, bank_name: e.target.value })}
                    placeholder="e.g., Bank of Ceylon"
                    data-testid="bank-name-input"
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium text-slate-700">Account Number</label>
                    <Input
                      value={formData.account_number}
                      onChange={(e) => setFormData({ ...formData, account_number: e.target.value })}
                      placeholder="Account number"
                      data-testid="account-number-input"
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium text-slate-700">Branch</label>
                    <Input
                      value={formData.branch}
                      onChange={(e) => setFormData({ ...formData, branch: e.target.value })}
                      placeholder="Branch name"
                    />
                  </div>
                </div>
              </>
            )}
            {!editingAccount && (
              <div>
                <label className="text-sm font-medium text-slate-700">Opening Balance</label>
                <Input
                  type="number"
                  step="0.01"
                  value={formData.opening_balance}
                  onChange={(e) => setFormData({ ...formData, opening_balance: parseFloat(e.target.value) || 0 })}
                  data-testid="opening-balance-input"
                />
              </div>
            )}
            <div>
              <label className="text-sm font-medium text-slate-700">Description</label>
              <Input
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="Optional description"
              />
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setIsModalOpen(false)}>Cancel</Button>
              <Button type="submit" data-testid="save-account-btn">{editingAccount ? 'Update' : 'Create'} Account</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Transfer Modal */}
      <Dialog open={isTransferModalOpen} onOpenChange={setIsTransferModalOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Transfer Between Accounts</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleTransfer} className="space-y-4">
            <div>
              <label className="text-sm font-medium text-slate-700">From Account *</label>
              <Select
                value={transferData.from_account_id}
                onValueChange={(value) => setTransferData({ ...transferData, from_account_id: value })}
              >
                <SelectTrigger data-testid="from-account-select">
                  <SelectValue placeholder="Select source account" />
                </SelectTrigger>
                <SelectContent>
                  {accounts.filter(a => a.is_active !== false).map(acc => (
                    <SelectItem key={acc.id} value={acc.id}>
                      {acc.account_name} ({formatCurrency(acc.current_balance)})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-sm font-medium text-slate-700">To Account *</label>
              <Select
                value={transferData.to_account_id}
                onValueChange={(value) => setTransferData({ ...transferData, to_account_id: value })}
              >
                <SelectTrigger data-testid="to-account-select">
                  <SelectValue placeholder="Select destination account" />
                </SelectTrigger>
                <SelectContent>
                  {accounts.filter(a => a.is_active !== false && a.id !== transferData.from_account_id).map(acc => (
                    <SelectItem key={acc.id} value={acc.id}>
                      {acc.account_name} ({formatCurrency(acc.current_balance)})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-sm font-medium text-slate-700">Amount *</label>
              <Input
                type="number"
                step="0.01"
                min="0.01"
                value={transferData.amount}
                onChange={(e) => setTransferData({ ...transferData, amount: parseFloat(e.target.value) || 0 })}
                required
                data-testid="transfer-amount-input"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-slate-700">Date</label>
              <Input
                type="date"
                value={transferData.transaction_date}
                onChange={(e) => setTransferData({ ...transferData, transaction_date: e.target.value })}
              />
            </div>
            <div>
              <label className="text-sm font-medium text-slate-700">Description</label>
              <Input
                value={transferData.description}
                onChange={(e) => setTransferData({ ...transferData, description: e.target.value })}
                placeholder="Optional description"
              />
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setIsTransferModalOpen(false)}>Cancel</Button>
              <Button type="submit" data-testid="confirm-transfer-btn">Transfer</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Transaction Modal */}
      <Dialog open={isTransactionModalOpen} onOpenChange={setIsTransactionModalOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Record Transaction - {selectedAccount?.account_name}</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleTransaction} className="space-y-4">
            <div>
              <label className="text-sm font-medium text-slate-700">Transaction Type *</label>
              <Select
                value={transactionData.transaction_type}
                onValueChange={(value) => setTransactionData({ ...transactionData, transaction_type: value })}
              >
                <SelectTrigger data-testid="transaction-type-select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="deposit">Deposit (Money In)</SelectItem>
                  <SelectItem value="withdrawal">Withdrawal (Money Out)</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-sm font-medium text-slate-700">Amount *</label>
              <Input
                type="number"
                step="0.01"
                min="0.01"
                value={transactionData.amount}
                onChange={(e) => setTransactionData({ ...transactionData, amount: parseFloat(e.target.value) || 0 })}
                required
                data-testid="transaction-amount-input"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-slate-700">Date</label>
              <Input
                type="date"
                value={transactionData.transaction_date}
                onChange={(e) => setTransactionData({ ...transactionData, transaction_date: e.target.value })}
              />
            </div>
            <div>
              <label className="text-sm font-medium text-slate-700">Description *</label>
              <Input
                value={transactionData.description}
                onChange={(e) => setTransactionData({ ...transactionData, description: e.target.value })}
                placeholder="e.g., Customer payment, Office supplies"
                required
                data-testid="transaction-description-input"
              />
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setIsTransactionModalOpen(false)}>Cancel</Button>
              <Button type="submit" data-testid="record-transaction-btn">Record Transaction</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* View Account Modal */}
      <Dialog open={isViewModalOpen} onOpenChange={setIsViewModalOpen}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{selectedAccount?.account_name}</DialogTitle>
          </DialogHeader>
          {selectedAccount && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-slate-500">Account Type</p>
                  <p className="font-medium capitalize">{selectedAccount.account_type}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-500">Current Balance</p>
                  <p className="font-medium text-lg">{formatCurrency(selectedAccount.current_balance)}</p>
                </div>
                {selectedAccount.bank_name && (
                  <div>
                    <p className="text-sm text-slate-500">Bank</p>
                    <p className="font-medium">{selectedAccount.bank_name}</p>
                  </div>
                )}
                {selectedAccount.account_number && (
                  <div>
                    <p className="text-sm text-slate-500">Account Number</p>
                    <p className="font-medium">{selectedAccount.account_number}</p>
                  </div>
                )}
              </div>

              <div className="border-t pt-4">
                <div className="flex justify-between items-center mb-3">
                  <h3 className="font-semibold">Recent Transactions</h3>
                  <Button size="sm" variant="outline" onClick={() => fetchTransactions(selectedAccount.id)}>
                    <RefreshCw className="w-4 h-4 mr-1" /> Refresh
                  </Button>
                </div>
                {transactions.length === 0 ? (
                  <p className="text-slate-500 text-center py-4">No transactions yet</p>
                ) : (
                  <div className="space-y-2 max-h-60 overflow-y-auto">
                    {transactions.map(tx => (
                      <div key={tx.id} className="flex justify-between items-center p-3 bg-slate-50 rounded-lg">
                        <div className="flex items-center gap-3">
                          {tx.transaction_type === 'deposit' || tx.transaction_type === 'transfer_in' ? (
                            <TrendingUp className="w-5 h-5 text-green-600" />
                          ) : (
                            <TrendingDown className="w-5 h-5 text-red-600" />
                          )}
                          <div>
                            <p className="font-medium text-sm">{tx.description}</p>
                            <p className="text-xs text-slate-500">{tx.transaction_date}</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className={`font-medium ${tx.transaction_type === 'deposit' || tx.transaction_type === 'transfer_in' ? 'text-green-600' : 'text-red-600'}`}>
                            {tx.transaction_type === 'deposit' || tx.transaction_type === 'transfer_in' ? '+' : '-'}{formatCurrency(tx.amount)}
                          </p>
                          <p className="text-xs text-slate-500">Bal: {formatCurrency(tx.balance_after)}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

// Accounts List Component
function AccountsList({ accounts, onView, onEdit, onDelete, onTransaction, formatCurrency }) {
  if (accounts.length === 0) {
    return (
      <div className="text-center py-12 bg-slate-50 rounded-lg">
        <Wallet className="w-12 h-12 mx-auto text-slate-300 mb-3" />
        <p className="text-slate-500">No accounts found</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {accounts.map(account => (
        <Card key={account.id} className={`${account.is_active === false ? 'opacity-60' : ''}`}>
          <CardHeader className="pb-2">
            <div className="flex justify-between items-start">
              <div className="flex items-center gap-2">
                {account.account_type === 'bank' ? (
                  <Building2 className="w-5 h-5 text-blue-600" />
                ) : (
                  <Wallet className="w-5 h-5 text-amber-600" />
                )}
                <CardTitle className="text-base">{account.account_name}</CardTitle>
              </div>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="sm" data-testid={`account-menu-${account.id}`}>
                    <MoreVertical className="w-4 h-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem onClick={() => onView(account)}>
                    <Eye className="w-4 h-4 mr-2" /> View Details
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => onTransaction(account)}>
                    <Plus className="w-4 h-4 mr-2" /> Record Transaction
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => onEdit(account)}>
                    <Pencil className="w-4 h-4 mr-2" /> Edit
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => onDelete(account.id)} className="text-red-600">
                    <Trash2 className="w-4 h-4 mr-2" /> Delete
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </CardHeader>
          <CardContent>
            {account.bank_name && (
              <p className="text-sm text-slate-500 mb-1">{account.bank_name}</p>
            )}
            {account.account_number && (
              <p className="text-xs text-slate-400 mb-2">A/C: {account.account_number}</p>
            )}
            <p className="text-2xl font-bold text-slate-900">{formatCurrency(account.current_balance)}</p>
            <p className="text-xs text-slate-400 mt-1">Code: {account.chart_account_code}</p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
