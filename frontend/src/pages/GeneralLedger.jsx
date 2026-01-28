import React, { useState, useEffect } from 'react';
import api from '../lib/api';
import { toast } from 'sonner';
import {
  Plus,
  FileText,
  Calendar,
  RefreshCw,
  ArrowRightLeft,
  ChevronDown,
  ChevronRight,
  Undo2
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
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

export default function GeneralLedger() {
  const [entries, setEntries] = useState([]);
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [expandedEntry, setExpandedEntry] = useState(null);
  const [startDate, setStartDate] = useState(
    new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString().split('T')[0]
  );
  const [endDate, setEndDate] = useState(
    new Date().toISOString().split('T')[0]
  );
  const [formData, setFormData] = useState({
    entry_date: new Date().toISOString().split('T')[0],
    description: '',
    reference_number: '',
    lines: [
      { account_id: '', debit: 0, credit: 0, description: '' },
      { account_id: '', debit: 0, credit: 0, description: '' }
    ]
  });

  useEffect(() => {
    fetchData();
  }, [startDate, endDate]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [entriesRes, accountsRes] = await Promise.all([
        api.get('/finance/journal-entries', {
          params: { start_date: startDate, end_date: endDate }
        }),
        api.get('/finance/chart-of-accounts')
      ]);
      setEntries(entriesRes.data);
      setAccounts(accountsRes.data);
    } catch (error) {
      toast.error('Failed to fetch data');
    } finally {
      setLoading(false);
    }
  };

  const handleAddLine = () => {
    setFormData({
      ...formData,
      lines: [...formData.lines, { account_id: '', debit: 0, credit: 0, description: '' }]
    });
  };

  const handleRemoveLine = (index) => {
    if (formData.lines.length <= 2) {
      toast.error('Minimum 2 lines required for double-entry');
      return;
    }
    setFormData({
      ...formData,
      lines: formData.lines.filter((_, i) => i !== index)
    });
  };

  const handleLineChange = (index, field, value) => {
    const newLines = [...formData.lines];
    newLines[index] = { ...newLines[index], [field]: value };
    setFormData({ ...formData, lines: newLines });
  };

  const calculateTotals = () => {
    const totalDebit = formData.lines.reduce((sum, line) => sum + (parseFloat(line.debit) || 0), 0);
    const totalCredit = formData.lines.reduce((sum, line) => sum + (parseFloat(line.credit) || 0), 0);
    return { totalDebit, totalCredit, isBalanced: Math.abs(totalDebit - totalCredit) < 0.01 };
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const { isBalanced, totalDebit, totalCredit } = calculateTotals();
    
    if (!isBalanced) {
      toast.error(`Entry not balanced. Debits: ${totalDebit.toFixed(2)}, Credits: ${totalCredit.toFixed(2)}`);
      return;
    }

    // Filter out empty lines
    const validLines = formData.lines.filter(
      line => line.account_id && (line.debit > 0 || line.credit > 0)
    );

    if (validLines.length < 2) {
      toast.error('At least 2 valid lines required');
      return;
    }

    try {
      await api.post('/finance/journal-entries', {
        entry_date: formData.entry_date,
        description: formData.description,
        reference_number: formData.reference_number,
        lines: validLines
      });
      toast.success('Journal entry created');
      setIsModalOpen(false);
      resetForm();
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create entry');
    }
  };

  const handleReverse = async (entryId) => {
    if (!window.confirm('Are you sure you want to reverse this entry?')) return;
    try {
      await api.post(`/finance/journal-entries/${entryId}/reverse`);
      toast.success('Entry reversed');
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to reverse entry');
    }
  };

  const resetForm = () => {
    setFormData({
      entry_date: new Date().toISOString().split('T')[0],
      description: '',
      reference_number: '',
      lines: [
        { account_id: '', debit: 0, credit: 0, description: '' },
        { account_id: '', debit: 0, credit: 0, description: '' }
      ]
    });
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-LK', {
      style: 'currency',
      currency: 'LKR',
      minimumFractionDigits: 2
    }).format(amount || 0);
  };

  const { totalDebit, totalCredit, isBalanced } = calculateTotals();

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-slate-900"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="general-ledger-page">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">General Ledger</h1>
          <p className="text-slate-500 mt-1">Journal entries & transactions</p>
        </div>
        <Button onClick={() => { resetForm(); setIsModalOpen(true); }} data-testid="add-entry-btn">
          <Plus className="w-4 h-4 mr-2" />
          New Journal Entry
        </Button>
      </div>

      {/* Date Filters */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 flex items-center gap-4">
        <Calendar className="w-5 h-5 text-slate-400" />
        <div className="flex items-center gap-2">
          <label className="text-sm text-slate-600">From:</label>
          <Input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            className="w-40"
          />
        </div>
        <div className="flex items-center gap-2">
          <label className="text-sm text-slate-600">To:</label>
          <Input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            className="w-40"
          />
        </div>
        <Button variant="outline" onClick={fetchData}>
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Entries List */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        {entries.length === 0 ? (
          <div className="p-8 text-center text-slate-500">
            <FileText className="w-12 h-12 mx-auto mb-4 text-slate-300" />
            <p>No journal entries found</p>
            <p className="text-sm mt-1">Create your first entry to get started</p>
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {entries.map((entry) => (
              <div key={entry.id} className="hover:bg-slate-50" data-testid={`entry-${entry.entry_number}`}>
                <button
                  onClick={() => setExpandedEntry(expandedEntry === entry.id ? null : entry.id)}
                  className="w-full p-4 flex items-center justify-between text-left"
                >
                  <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2">
                      {expandedEntry === entry.id ? (
                        <ChevronDown className="w-4 h-4 text-slate-400" />
                      ) : (
                        <ChevronRight className="w-4 h-4 text-slate-400" />
                      )}
                      <ArrowRightLeft className="w-5 h-5 text-slate-400" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-sm font-medium">{entry.entry_number}</span>
                        {entry.is_auto_generated && (
                          <span className="px-1.5 py-0.5 text-xs bg-blue-100 text-blue-700 rounded">Auto</span>
                        )}
                        {entry.is_reversed && (
                          <span className="px-1.5 py-0.5 text-xs bg-red-100 text-red-700 rounded">Reversed</span>
                        )}
                      </div>
                      <p className="text-sm text-slate-600 mt-0.5">{entry.description}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-slate-500">{entry.entry_date}</p>
                    <p className="font-semibold">{formatCurrency(entry.total_debit)}</p>
                  </div>
                </button>
                
                {expandedEntry === entry.id && (
                  <div className="px-4 pb-4">
                    <table className="w-full text-sm">
                      <thead className="bg-slate-100">
                        <tr>
                          <th className="text-left p-2">Account</th>
                          <th className="text-left p-2">Description</th>
                          <th className="text-right p-2">Debit</th>
                          <th className="text-right p-2">Credit</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {entry.lines.map((line, idx) => (
                          <tr key={idx}>
                            <td className="p-2">
                              <span className="font-mono text-xs text-slate-500 mr-2">{line.account_code}</span>
                              {line.account_name}
                            </td>
                            <td className="p-2 text-slate-600">{line.description || '-'}</td>
                            <td className="p-2 text-right">{line.debit > 0 ? formatCurrency(line.debit) : '-'}</td>
                            <td className="p-2 text-right">{line.credit > 0 ? formatCurrency(line.credit) : '-'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                    {!entry.is_reversed && !entry.is_auto_generated && (
                      <div className="mt-3 flex justify-end">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleReverse(entry.id)}
                          className="text-red-600 hover:text-red-700"
                        >
                          <Undo2 className="w-4 h-4 mr-1" />
                          Reverse Entry
                        </Button>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* New Journal Entry Modal */}
      <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
        <DialogContent className="sm:max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>New Journal Entry</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="text-sm font-medium text-slate-700">Date</label>
                <Input
                  type="date"
                  value={formData.entry_date}
                  onChange={(e) => setFormData({ ...formData, entry_date: e.target.value })}
                  required
                  data-testid="entry-date-input"
                />
              </div>
              <div className="col-span-2">
                <label className="text-sm font-medium text-slate-700">Reference Number</label>
                <Input
                  value={formData.reference_number}
                  onChange={(e) => setFormData({ ...formData, reference_number: e.target.value })}
                  placeholder="Optional reference"
                  data-testid="entry-reference-input"
                />
              </div>
            </div>
            <div>
              <label className="text-sm font-medium text-slate-700">Description</label>
              <Textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="Entry description"
                required
                rows={2}
                data-testid="entry-description-input"
              />
            </div>

            {/* Entry Lines */}
            <div>
              <div className="flex justify-between items-center mb-2">
                <label className="text-sm font-medium text-slate-700">Entry Lines</label>
                <Button type="button" variant="outline" size="sm" onClick={handleAddLine}>
                  <Plus className="w-4 h-4 mr-1" />
                  Add Line
                </Button>
              </div>
              <div className="border rounded-lg overflow-hidden">
                <table className="w-full text-sm">
                  <thead className="bg-slate-100">
                    <tr>
                      <th className="text-left p-2">Account</th>
                      <th className="text-right p-2 w-32">Debit</th>
                      <th className="text-right p-2 w-32">Credit</th>
                      <th className="w-10"></th>
                    </tr>
                  </thead>
                  <tbody>
                    {formData.lines.map((line, idx) => (
                      <tr key={idx} className="border-t">
                        <td className="p-2">
                          <Select
                            value={line.account_id}
                            onValueChange={(value) => handleLineChange(idx, 'account_id', value)}
                          >
                            <SelectTrigger data-testid={`line-account-${idx}`}>
                              <SelectValue placeholder="Select account" />
                            </SelectTrigger>
                            <SelectContent>
                              {accounts.map(acc => (
                                <SelectItem key={acc.id} value={acc.id}>
                                  {acc.code} - {acc.name}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </td>
                        <td className="p-2">
                          <Input
                            type="number"
                            value={line.debit || ''}
                            onChange={(e) => handleLineChange(idx, 'debit', parseFloat(e.target.value) || 0)}
                            placeholder="0.00"
                            step="0.01"
                            min="0"
                            className="text-right"
                            data-testid={`line-debit-${idx}`}
                          />
                        </td>
                        <td className="p-2">
                          <Input
                            type="number"
                            value={line.credit || ''}
                            onChange={(e) => handleLineChange(idx, 'credit', parseFloat(e.target.value) || 0)}
                            placeholder="0.00"
                            step="0.01"
                            min="0"
                            className="text-right"
                            data-testid={`line-credit-${idx}`}
                          />
                        </td>
                        <td className="p-2">
                          <button
                            type="button"
                            onClick={() => handleRemoveLine(idx)}
                            className="p-1 text-slate-400 hover:text-red-600"
                          >
                            ×
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                  <tfoot className="bg-slate-50 font-semibold">
                    <tr>
                      <td className="p-2">Totals</td>
                      <td className="p-2 text-right">{formatCurrency(totalDebit)}</td>
                      <td className="p-2 text-right">{formatCurrency(totalCredit)}</td>
                      <td></td>
                    </tr>
                  </tfoot>
                </table>
              </div>
              <div className={`mt-2 text-sm ${isBalanced ? 'text-green-600' : 'text-red-600'}`}>
                {isBalanced ? '✓ Entry is balanced' : `✗ Difference: ${formatCurrency(Math.abs(totalDebit - totalCredit))}`}
              </div>
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setIsModalOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={!isBalanced} data-testid="save-entry-btn">
                Create Entry
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
