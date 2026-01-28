import React, { useState, useEffect } from 'react';
import api from '../lib/api';
import { toast } from 'sonner';
import {
  FileText,
  DollarSign,
  TrendingUp,
  TrendingDown,
  Calendar,
  Download,
  RefreshCw,
  ChevronDown,
  ChevronRight
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger
} from '../components/ui/tabs';

export default function FinancialReports() {
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('trial-balance');
  const [startDate, setStartDate] = useState(
    new Date(new Date().getFullYear(), 3, 1).toISOString().split('T')[0] // April 1
  );
  const [endDate, setEndDate] = useState(
    new Date().toISOString().split('T')[0]
  );
  const [trialBalance, setTrialBalance] = useState(null);
  const [profitLoss, setProfitLoss] = useState(null);
  const [balanceSheet, setBalanceSheet] = useState(null);
  const [cashFlow, setCashFlow] = useState(null);
  const [expandedSections, setExpandedSections] = useState({});

  useEffect(() => {
    fetchReport(activeTab);
  }, [activeTab, startDate, endDate]);

  const fetchReport = async (reportType) => {
    try {
      setLoading(true);
      switch (reportType) {
        case 'trial-balance':
          const tbResponse = await api.get('/api/finance/reports/trial-balance', {
            params: { as_of_date: endDate }
          });
          setTrialBalance(tbResponse.data);
          break;
        case 'profit-loss':
          const plResponse = await api.get('/api/finance/reports/profit-loss', {
            params: { start_date: startDate, end_date: endDate }
          });
          setProfitLoss(plResponse.data);
          break;
        case 'balance-sheet':
          const bsResponse = await api.get('/api/finance/reports/balance-sheet', {
            params: { as_of_date: endDate }
          });
          setBalanceSheet(bsResponse.data);
          break;
        case 'cash-flow':
          const cfResponse = await api.get('/api/finance/reports/cash-flow', {
            params: { start_date: startDate, end_date: endDate }
          });
          setCashFlow(cfResponse.data);
          break;
      }
    } catch (error) {
      toast.error('Failed to fetch report');
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-LK', {
      style: 'currency',
      currency: 'LKR',
      minimumFractionDigits: 2
    }).format(amount || 0);
  };

  const toggleSection = (section) => {
    setExpandedSections(prev => ({ ...prev, [section]: !prev[section] }));
  };

  const exportToCSV = (data, filename) => {
    // Simple CSV export
    let csv = '';
    if (Array.isArray(data)) {
      const headers = Object.keys(data[0] || {});
      csv = headers.join(',') + '\n';
      data.forEach(row => {
        csv += headers.map(h => row[h]).join(',') + '\n';
      });
    }
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${filename}.csv`;
    a.click();
  };

  return (
    <div className="space-y-6" data-testid="financial-reports-page">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Financial Reports</h1>
          <p className="text-slate-500 mt-1">Financial Year: April 1 - March 31</p>
        </div>
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
            data-testid="start-date-input"
          />
        </div>
        <div className="flex items-center gap-2">
          <label className="text-sm text-slate-600">To:</label>
          <Input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            className="w-40"
            data-testid="end-date-input"
          />
        </div>
        <Button variant="outline" onClick={() => fetchReport(activeTab)} data-testid="refresh-report-btn">
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="trial-balance" data-testid="tab-trial-balance">Trial Balance</TabsTrigger>
          <TabsTrigger value="profit-loss" data-testid="tab-profit-loss">Profit & Loss</TabsTrigger>
          <TabsTrigger value="balance-sheet" data-testid="tab-balance-sheet">Balance Sheet</TabsTrigger>
          <TabsTrigger value="cash-flow" data-testid="tab-cash-flow">Cash Flow</TabsTrigger>
        </TabsList>

        {/* Trial Balance */}
        <TabsContent value="trial-balance" className="mt-4">
          <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
            <div className="p-4 border-b border-slate-200 flex justify-between items-center">
              <div>
                <h2 className="font-semibold text-lg">Trial Balance</h2>
                <p className="text-sm text-slate-500">As of {endDate}</p>
              </div>
              {trialBalance && (
                <div className={`px-3 py-1 rounded-full text-sm font-medium ${trialBalance.is_balanced ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                  {trialBalance.is_balanced ? 'Balanced' : 'Not Balanced'}
                </div>
              )}
            </div>
            {loading ? (
              <div className="p-8 text-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-slate-900 mx-auto"></div>
              </div>
            ) : trialBalance?.accounts?.length > 0 ? (
              <table className="w-full">
                <thead className="bg-slate-50">
                  <tr>
                    <th className="text-left p-3 font-medium text-slate-600">Account Code</th>
                    <th className="text-left p-3 font-medium text-slate-600">Account Name</th>
                    <th className="text-right p-3 font-medium text-slate-600">Debit</th>
                    <th className="text-right p-3 font-medium text-slate-600">Credit</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {trialBalance.accounts.map((account, idx) => (
                    <tr key={idx} className="hover:bg-slate-50">
                      <td className="p-3 font-mono text-sm">{account.account_code}</td>
                      <td className="p-3">{account.account_name}</td>
                      <td className="p-3 text-right">{account.debit > 0 ? formatCurrency(account.debit) : '-'}</td>
                      <td className="p-3 text-right">{account.credit > 0 ? formatCurrency(account.credit) : '-'}</td>
                    </tr>
                  ))}
                </tbody>
                <tfoot className="bg-slate-100 font-semibold">
                  <tr>
                    <td colSpan="2" className="p-3">Total</td>
                    <td className="p-3 text-right">{formatCurrency(trialBalance.total_debit)}</td>
                    <td className="p-3 text-right">{formatCurrency(trialBalance.total_credit)}</td>
                  </tr>
                </tfoot>
              </table>
            ) : (
              <div className="p-8 text-center text-slate-500">
                No transactions found for this period
              </div>
            )}
          </div>
        </TabsContent>

        {/* Profit & Loss */}
        <TabsContent value="profit-loss" className="mt-4">
          <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
            <div className="p-4 border-b border-slate-200">
              <h2 className="font-semibold text-lg">Profit & Loss Statement</h2>
              <p className="text-sm text-slate-500">{startDate} to {endDate}</p>
            </div>
            {loading ? (
              <div className="p-8 text-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-slate-900 mx-auto"></div>
              </div>
            ) : profitLoss ? (
              <div className="divide-y divide-slate-200">
                {/* Income Section */}
                <div className="p-4">
                  <button
                    onClick={() => toggleSection('income')}
                    className="flex items-center justify-between w-full text-left"
                  >
                    <div className="flex items-center gap-2">
                      {expandedSections.income ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                      <TrendingUp className="w-5 h-5 text-green-600" />
                      <span className="font-semibold text-green-700">Income</span>
                    </div>
                    <span className="font-bold text-green-700">{formatCurrency(profitLoss.income?.total)}</span>
                  </button>
                  {expandedSections.income && profitLoss.income?.items?.length > 0 && (
                    <div className="mt-2 ml-8 space-y-1">
                      {profitLoss.income.items.map((item, idx) => (
                        <div key={idx} className="flex justify-between text-sm py-1">
                          <span className="text-slate-600">{item.name}</span>
                          <span>{formatCurrency(item.amount)}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Expenses Section */}
                <div className="p-4">
                  <button
                    onClick={() => toggleSection('expenses')}
                    className="flex items-center justify-between w-full text-left"
                  >
                    <div className="flex items-center gap-2">
                      {expandedSections.expenses ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                      <TrendingDown className="w-5 h-5 text-red-600" />
                      <span className="font-semibold text-red-700">Expenses</span>
                    </div>
                    <span className="font-bold text-red-700">{formatCurrency(profitLoss.expenses?.total)}</span>
                  </button>
                  {expandedSections.expenses && profitLoss.expenses?.items?.length > 0 && (
                    <div className="mt-2 ml-8 space-y-1">
                      {profitLoss.expenses.items.map((item, idx) => (
                        <div key={idx} className="flex justify-between text-sm py-1">
                          <span className="text-slate-600">{item.name}</span>
                          <span>{formatCurrency(item.amount)}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Net Profit */}
                <div className="p-4 bg-slate-50">
                  <div className="flex justify-between items-center">
                    <span className="font-bold text-lg">Net Profit</span>
                    <span className={`font-bold text-xl ${profitLoss.net_profit >= 0 ? 'text-green-700' : 'text-red-700'}`}>
                      {formatCurrency(profitLoss.net_profit)}
                    </span>
                  </div>
                  {profitLoss.gross_margin_percent && (
                    <p className="text-sm text-slate-500 mt-1">
                      Gross Margin: {profitLoss.gross_margin_percent}%
                    </p>
                  )}
                </div>
              </div>
            ) : (
              <div className="p-8 text-center text-slate-500">
                No data available for this period
              </div>
            )}
          </div>
        </TabsContent>

        {/* Balance Sheet */}
        <TabsContent value="balance-sheet" className="mt-4">
          <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
            <div className="p-4 border-b border-slate-200 flex justify-between items-center">
              <div>
                <h2 className="font-semibold text-lg">Balance Sheet</h2>
                <p className="text-sm text-slate-500">As of {endDate}</p>
              </div>
              {balanceSheet && (
                <div className={`px-3 py-1 rounded-full text-sm font-medium ${balanceSheet.is_balanced ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                  {balanceSheet.is_balanced ? 'Balanced' : 'Not Balanced'}
                </div>
              )}
            </div>
            {loading ? (
              <div className="p-8 text-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-slate-900 mx-auto"></div>
              </div>
            ) : balanceSheet ? (
              <div className="grid grid-cols-2 divide-x divide-slate-200">
                {/* Assets */}
                <div className="p-4">
                  <h3 className="font-semibold text-lg text-blue-700 mb-4 flex items-center gap-2">
                    <TrendingUp className="w-5 h-5" />
                    Assets
                  </h3>
                  {balanceSheet.assets?.items?.length > 0 ? (
                    <div className="space-y-2">
                      {balanceSheet.assets.items.map((item, idx) => (
                        <div key={idx} className="flex justify-between py-1 border-b border-slate-100">
                          <span className="text-slate-600">{item.name}</span>
                          <span className="font-medium">{formatCurrency(item.amount)}</span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-slate-400">No assets recorded</p>
                  )}
                  <div className="mt-4 pt-4 border-t-2 border-blue-200 flex justify-between">
                    <span className="font-bold">Total Assets</span>
                    <span className="font-bold text-blue-700">{formatCurrency(balanceSheet.total_assets)}</span>
                  </div>
                </div>

                {/* Liabilities & Equity */}
                <div className="p-4">
                  <h3 className="font-semibold text-lg text-red-700 mb-4 flex items-center gap-2">
                    <TrendingDown className="w-5 h-5" />
                    Liabilities
                  </h3>
                  {balanceSheet.liabilities?.items?.length > 0 ? (
                    <div className="space-y-2 mb-6">
                      {balanceSheet.liabilities.items.map((item, idx) => (
                        <div key={idx} className="flex justify-between py-1 border-b border-slate-100">
                          <span className="text-slate-600">{item.name}</span>
                          <span className="font-medium">{formatCurrency(item.amount)}</span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-slate-400 mb-6">No liabilities recorded</p>
                  )}

                  <h3 className="font-semibold text-lg text-purple-700 mb-4 flex items-center gap-2">
                    <DollarSign className="w-5 h-5" />
                    Equity
                  </h3>
                  {balanceSheet.equity?.items?.length > 0 ? (
                    <div className="space-y-2">
                      {balanceSheet.equity.items.map((item, idx) => (
                        <div key={idx} className="flex justify-between py-1 border-b border-slate-100">
                          <span className="text-slate-600">{item.name}</span>
                          <span className="font-medium">{formatCurrency(item.amount)}</span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-slate-400">No equity recorded</p>
                  )}
                  
                  <div className="mt-4 pt-4 border-t-2 border-purple-200 flex justify-between">
                    <span className="font-bold">Total Liabilities & Equity</span>
                    <span className="font-bold text-purple-700">{formatCurrency(balanceSheet.total_liabilities_equity)}</span>
                  </div>
                </div>
              </div>
            ) : (
              <div className="p-8 text-center text-slate-500">
                No data available
              </div>
            )}
          </div>
        </TabsContent>

        {/* Cash Flow */}
        <TabsContent value="cash-flow" className="mt-4">
          <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
            <div className="p-4 border-b border-slate-200">
              <h2 className="font-semibold text-lg">Cash Flow Statement</h2>
              <p className="text-sm text-slate-500">{startDate} to {endDate}</p>
            </div>
            {loading ? (
              <div className="p-8 text-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-slate-900 mx-auto"></div>
              </div>
            ) : cashFlow ? (
              <div className="divide-y divide-slate-200">
                {/* Operating Activities */}
                <div className="p-4">
                  <h3 className="font-semibold mb-3">Operating Activities</h3>
                  <div className="space-y-2 ml-4">
                    <div className="flex justify-between">
                      <span className="text-slate-600">Cash from Customers</span>
                      <span className="text-green-600 font-medium">
                        {formatCurrency(cashFlow.operating_activities?.cash_from_customers)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-600">Cash to Suppliers</span>
                      <span className="text-red-600 font-medium">
                        ({formatCurrency(cashFlow.operating_activities?.cash_to_suppliers)})
                      </span>
                    </div>
                    <div className="flex justify-between font-semibold pt-2 border-t">
                      <span>Net Operating Cash</span>
                      <span className={cashFlow.operating_activities?.net_operating_cash >= 0 ? 'text-green-600' : 'text-red-600'}>
                        {formatCurrency(cashFlow.operating_activities?.net_operating_cash)}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Summary */}
                <div className="p-4 bg-slate-50">
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span>Opening Cash Balance</span>
                      <span className="font-medium">{formatCurrency(cashFlow.opening_cash_balance)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Net Change in Cash</span>
                      <span className={`font-medium ${cashFlow.net_change_in_cash >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {formatCurrency(cashFlow.net_change_in_cash)}
                      </span>
                    </div>
                    <div className="flex justify-between font-bold text-lg pt-2 border-t">
                      <span>Closing Cash Balance</span>
                      <span className="text-blue-700">{formatCurrency(cashFlow.closing_cash_balance)}</span>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="p-8 text-center text-slate-500">
                No data available for this period
              </div>
            )}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
