import React, { useState, useEffect } from 'react';
import { payrollAPI } from '../../lib/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../../components/ui/table';
import { Loader2, FileText, Building2, Calculator, Download } from 'lucide-react';
import { toast } from 'sonner';

const formatCurrency = (amount) => {
  return new Intl.NumberFormat('en-LK', {
    style: 'currency',
    currency: 'LKR',
    minimumFractionDigits: 0,
  }).format(amount || 0);
};

export const PayrollReports = () => {
  const [activeTab, setActiveTab] = useState('summary');
  const [loading, setLoading] = useState(false);
  const [summaryData, setSummaryData] = useState(null);
  const [epfEtfData, setEpfEtfData] = useState(null);
  const [departmentData, setDepartmentData] = useState(null);

  // Get current month dates as default
  const now = new Date();
  const year = now.getFullYear();
  const month = now.getMonth();
  const [periodStart, setPeriodStart] = useState(new Date(year, month, 1).toISOString().split('T')[0]);
  const [periodEnd, setPeriodEnd] = useState(new Date(year, month + 1, 0).toISOString().split('T')[0]);

  const fetchSummaryReport = async () => {
    setLoading(true);
    try {
      const response = await payrollAPI.getPayrollSummary({ period_start: periodStart, period_end: periodEnd });
      setSummaryData(response.data);
    } catch (error) {
      toast.error('Failed to fetch summary report');
    } finally {
      setLoading(false);
    }
  };

  const fetchEpfEtfReport = async () => {
    setLoading(true);
    try {
      const response = await payrollAPI.getEpfEtfReport({ period_start: periodStart, period_end: periodEnd });
      setEpfEtfData(response.data);
    } catch (error) {
      toast.error('Failed to fetch EPF/ETF report');
    } finally {
      setLoading(false);
    }
  };

  const fetchDepartmentReport = async () => {
    setLoading(true);
    try {
      const response = await payrollAPI.getDepartmentReport({ period_start: periodStart, period_end: periodEnd });
      setDepartmentData(response.data);
    } catch (error) {
      toast.error('Failed to fetch department report');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'summary') fetchSummaryReport();
    else if (activeTab === 'epf-etf') fetchEpfEtfReport();
    else if (activeTab === 'department') fetchDepartmentReport();
  }, [activeTab, periodStart, periodEnd]);

  return (
    <div className="space-y-6" data-testid="payroll-reports-page">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-slate-900" style={{ fontFamily: 'Outfit, sans-serif' }}>
          Payroll Reports
        </h2>
        <p className="text-slate-500 mt-1">Generate and view payroll reports</p>
      </div>

      {/* Period Filter */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-wrap items-end gap-4">
            <div className="space-y-2">
              <Label>Period Start</Label>
              <Input
                type="date"
                value={periodStart}
                onChange={(e) => setPeriodStart(e.target.value)}
                className="w-44"
              />
            </div>
            <div className="space-y-2">
              <Label>Period End</Label>
              <Input
                type="date"
                value={periodEnd}
                onChange={(e) => setPeriodEnd(e.target.value)}
                className="w-44"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="summary" className="gap-2">
            <FileText className="w-4 h-4" />
            Summary
          </TabsTrigger>
          <TabsTrigger value="epf-etf" className="gap-2">
            <Calculator className="w-4 h-4" />
            EPF/ETF
          </TabsTrigger>
          <TabsTrigger value="department" className="gap-2">
            <Building2 className="w-4 h-4" />
            Department
          </TabsTrigger>
        </TabsList>

        {/* Summary Report */}
        <TabsContent value="summary" className="mt-4">
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
            </div>
          ) : summaryData ? (
            <div className="space-y-4">
              {/* Summary Cards */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <Card>
                  <CardContent className="pt-4">
                    <p className="text-sm text-slate-500">Total Payrolls</p>
                    <p className="text-2xl font-bold">{summaryData.total_payrolls}</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-4">
                    <p className="text-sm text-slate-500">Gross Salary</p>
                    <p className="text-2xl font-bold">{formatCurrency(summaryData.total_gross)}</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-4">
                    <p className="text-sm text-slate-500">Deductions</p>
                    <p className="text-2xl font-bold text-amber-600">{formatCurrency(summaryData.total_deductions)}</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="pt-4">
                    <p className="text-sm text-slate-500">Net Paid</p>
                    <p className="text-2xl font-bold text-green-600">{formatCurrency(summaryData.total_net)}</p>
                  </CardContent>
                </Card>
              </div>

              {/* Payroll List */}
              <Card>
                <CardHeader>
                  <CardTitle>Paid Payrolls</CardTitle>
                </CardHeader>
                <CardContent className="p-0">
                  {summaryData.payrolls?.length === 0 ? (
                    <div className="text-center py-8 text-slate-500">
                      No paid payrolls in this period
                    </div>
                  ) : (
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Payroll #</TableHead>
                          <TableHead>Period</TableHead>
                          <TableHead className="text-center">Employees</TableHead>
                          <TableHead className="text-right">Gross</TableHead>
                          <TableHead className="text-right">Deductions</TableHead>
                          <TableHead className="text-right">Net</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {summaryData.payrolls?.map((payroll) => (
                          <TableRow key={payroll.id}>
                            <TableCell className="font-medium">{payroll.payroll_number}</TableCell>
                            <TableCell className="text-slate-500">{payroll.period_start} - {payroll.period_end}</TableCell>
                            <TableCell className="text-center">{payroll.employee_count}</TableCell>
                            <TableCell className="text-right">{formatCurrency(payroll.total_gross)}</TableCell>
                            <TableCell className="text-right text-amber-600">{formatCurrency(payroll.total_deductions)}</TableCell>
                            <TableCell className="text-right font-medium text-green-600">{formatCurrency(payroll.total_net)}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  )}
                </CardContent>
              </Card>
            </div>
          ) : null}
        </TabsContent>

        {/* EPF/ETF Report */}
        <TabsContent value="epf-etf" className="mt-4">
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
            </div>
          ) : epfEtfData ? (
            <div className="space-y-4">
              {/* Totals */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <Card>
                  <CardContent className="pt-4">
                    <p className="text-sm text-slate-500">Total Gross</p>
                    <p className="text-2xl font-bold">{formatCurrency(epfEtfData.totals?.total_gross)}</p>
                  </CardContent>
                </Card>
                <Card className="bg-blue-50">
                  <CardContent className="pt-4">
                    <p className="text-sm text-blue-600">EPF Employee (8%)</p>
                    <p className="text-2xl font-bold text-blue-700">{formatCurrency(epfEtfData.totals?.total_epf_employee)}</p>
                  </CardContent>
                </Card>
                <Card className="bg-indigo-50">
                  <CardContent className="pt-4">
                    <p className="text-sm text-indigo-600">EPF Employer (12%)</p>
                    <p className="text-2xl font-bold text-indigo-700">{formatCurrency(epfEtfData.totals?.total_epf_employer)}</p>
                  </CardContent>
                </Card>
                <Card className="bg-emerald-50">
                  <CardContent className="pt-4">
                    <p className="text-sm text-emerald-600">ETF (3%)</p>
                    <p className="text-2xl font-bold text-emerald-700">{formatCurrency(epfEtfData.totals?.total_etf)}</p>
                  </CardContent>
                </Card>
              </div>

              {/* Contribution Details */}
              <Card>
                <CardHeader>
                  <CardTitle>Employee Contributions</CardTitle>
                  <CardDescription>Period: {epfEtfData.period_start} to {epfEtfData.period_end}</CardDescription>
                </CardHeader>
                <CardContent className="p-0">
                  {epfEtfData.contributions?.length === 0 ? (
                    <div className="text-center py-8 text-slate-500">
                      No contributions in this period
                    </div>
                  ) : (
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Employee</TableHead>
                          <TableHead>NIC</TableHead>
                          <TableHead className="text-right">Gross Salary</TableHead>
                          <TableHead className="text-right">EPF (Employee)</TableHead>
                          <TableHead className="text-right">EPF (Employer)</TableHead>
                          <TableHead className="text-right">ETF</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {epfEtfData.contributions?.map((emp, index) => (
                          <TableRow key={index}>
                            <TableCell>
                              <div>{emp.employee_name}</div>
                              <span className="text-xs text-slate-400">{emp.employee_code}</span>
                            </TableCell>
                            <TableCell className="text-slate-500">{emp.nic || '-'}</TableCell>
                            <TableCell className="text-right">{formatCurrency(emp.total_gross)}</TableCell>
                            <TableCell className="text-right text-blue-600">{formatCurrency(emp.epf_employee)}</TableCell>
                            <TableCell className="text-right text-indigo-600">{formatCurrency(emp.epf_employer)}</TableCell>
                            <TableCell className="text-right text-emerald-600">{formatCurrency(emp.etf)}</TableCell>
                          </TableRow>
                        ))}
                        {/* Totals Row */}
                        <TableRow className="bg-slate-50 font-medium">
                          <TableCell colSpan={2}>Total</TableCell>
                          <TableCell className="text-right">{formatCurrency(epfEtfData.totals?.total_gross)}</TableCell>
                          <TableCell className="text-right text-blue-600">{formatCurrency(epfEtfData.totals?.total_epf_employee)}</TableCell>
                          <TableCell className="text-right text-indigo-600">{formatCurrency(epfEtfData.totals?.total_epf_employer)}</TableCell>
                          <TableCell className="text-right text-emerald-600">{formatCurrency(epfEtfData.totals?.total_etf)}</TableCell>
                        </TableRow>
                      </TableBody>
                    </Table>
                  )}
                </CardContent>
              </Card>
            </div>
          ) : null}
        </TabsContent>

        {/* Department Report */}
        <TabsContent value="department" className="mt-4">
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
            </div>
          ) : departmentData ? (
            <Card>
              <CardHeader>
                <CardTitle>Department Salary Breakdown</CardTitle>
                <CardDescription>Period: {departmentData.period_start} to {departmentData.period_end}</CardDescription>
              </CardHeader>
              <CardContent className="p-0">
                {departmentData.departments?.length === 0 ? (
                  <div className="text-center py-8 text-slate-500">
                    No data for this period
                  </div>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Department</TableHead>
                        <TableHead className="text-center">Employees</TableHead>
                        <TableHead className="text-right">Gross Salary</TableHead>
                        <TableHead className="text-right">Deductions</TableHead>
                        <TableHead className="text-right">Net Pay</TableHead>
                        <TableHead className="text-right">Employer Cost</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {departmentData.departments?.map((dept) => (
                        <TableRow key={dept.department_id}>
                          <TableCell className="font-medium">{dept.department_name}</TableCell>
                          <TableCell className="text-center">{dept.employee_count}</TableCell>
                          <TableCell className="text-right">{formatCurrency(dept.total_gross)}</TableCell>
                          <TableCell className="text-right text-amber-600">{formatCurrency(dept.total_deductions)}</TableCell>
                          <TableCell className="text-right text-green-600">{formatCurrency(dept.total_net)}</TableCell>
                          <TableCell className="text-right text-indigo-600">{formatCurrency(dept.employer_cost)}</TableCell>
                        </TableRow>
                      ))}
                      {/* Totals Row */}
                      <TableRow className="bg-slate-50 font-medium">
                        <TableCell>Total</TableCell>
                        <TableCell className="text-center">
                          {departmentData.departments?.reduce((sum, d) => sum + d.employee_count, 0)}
                        </TableCell>
                        <TableCell className="text-right">
                          {formatCurrency(departmentData.departments?.reduce((sum, d) => sum + d.total_gross, 0))}
                        </TableCell>
                        <TableCell className="text-right text-amber-600">
                          {formatCurrency(departmentData.departments?.reduce((sum, d) => sum + d.total_deductions, 0))}
                        </TableCell>
                        <TableCell className="text-right text-green-600">
                          {formatCurrency(departmentData.departments?.reduce((sum, d) => sum + d.total_net, 0))}
                        </TableCell>
                        <TableCell className="text-right text-indigo-600">
                          {formatCurrency(departmentData.departments?.reduce((sum, d) => sum + d.employer_cost, 0))}
                        </TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>
          ) : null}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default PayrollReports;
