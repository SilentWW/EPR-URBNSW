import React, { useState, useEffect } from 'react';
import { reportsAPI, dashboardAPI } from '../lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../components/ui/table';
import { Loader2, Download, PieChart, BarChart3 } from 'lucide-react';
import { toast } from 'sonner';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar
} from 'recharts';

const formatCurrency = (amount) => {
  return new Intl.NumberFormat('en-LK', {
    style: 'currency',
    currency: 'LKR',
    minimumFractionDigits: 0,
  }).format(amount);
};

export const Reports = () => {
  const [loading, setLoading] = useState(true);
  const [salesReport, setSalesReport] = useState(null);
  const [salesChart, setSalesChart] = useState([]);
  const [topProducts, setTopProducts] = useState([]);
  const [dateRange, setDateRange] = useState({
    start_date: '',
    end_date: '',
  });

  const fetchReports = async () => {
    try {
      const [salesRes, chartRes, topRes] = await Promise.all([
        reportsAPI.getSales(dateRange.start_date && dateRange.end_date ? dateRange : {}),
        dashboardAPI.getSalesChart('30days'),
        dashboardAPI.getTopProducts(10),
      ]);
      setSalesReport(salesRes.data);
      setSalesChart(chartRes.data);
      setTopProducts(topRes.data);
    } catch (error) {
      toast.error('Failed to fetch reports');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, []);

  const handleApplyFilter = () => {
    setLoading(true);
    fetchReports();
  };

  const exportToCSV = (data, filename) => {
    if (!data || data.length === 0) return;
    
    const headers = Object.keys(data[0]).join(',');
    const rows = data.map(row => Object.values(row).join(','));
    const csv = [headers, ...rows].join('\n');
    
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${filename}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="reports-page">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-slate-900" style={{ fontFamily: 'Outfit, sans-serif' }}>
          Reports
        </h2>
        <p className="text-slate-500 mt-1">Business analytics and insights</p>
      </div>

      {/* Date Filter */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-wrap items-end gap-4">
            <div className="space-y-2">
              <Label>Start Date</Label>
              <Input
                type="date"
                value={dateRange.start_date}
                onChange={(e) => setDateRange({ ...dateRange, start_date: e.target.value })}
                data-testid="start-date"
              />
            </div>
            <div className="space-y-2">
              <Label>End Date</Label>
              <Input
                type="date"
                value={dateRange.end_date}
                onChange={(e) => setDateRange({ ...dateRange, end_date: e.target.value })}
                data-testid="end-date"
              />
            </div>
            <Button onClick={handleApplyFilter} className="bg-indigo-600 hover:bg-indigo-700" data-testid="apply-filter-btn">
              Apply Filter
            </Button>
          </div>
        </CardContent>
      </Card>

      <Tabs defaultValue="sales" className="space-y-4">
        <TabsList>
          <TabsTrigger value="sales">Sales Report</TabsTrigger>
          <TabsTrigger value="products">Product Performance</TabsTrigger>
        </TabsList>

        <TabsContent value="sales" className="space-y-6">
          {/* Sales Summary */}
          {salesReport && (
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <Card className="stat-card">
                <p className="text-sm font-medium text-slate-500">Total Orders</p>
                <p className="text-2xl font-bold text-slate-900 mt-1">{salesReport.total_orders}</p>
              </Card>
              <Card className="stat-card">
                <p className="text-sm font-medium text-slate-500">Total Revenue</p>
                <p className="text-2xl font-bold text-emerald-600 mt-1">{formatCurrency(salesReport.total_revenue)}</p>
              </Card>
              <Card className="stat-card">
                <p className="text-sm font-medium text-slate-500">Total Discount</p>
                <p className="text-2xl font-bold text-amber-600 mt-1">{formatCurrency(salesReport.total_discount)}</p>
              </Card>
              <Card className="stat-card">
                <p className="text-sm font-medium text-slate-500">Avg Order Value</p>
                <p className="text-2xl font-bold text-indigo-600 mt-1">
                  {formatCurrency(salesReport.total_orders > 0 ? salesReport.total_revenue / salesReport.total_orders : 0)}
                </p>
              </Card>
            </div>
          )}

          {/* Sales Chart */}
          <Card className="p-6">
            <CardHeader className="p-0 pb-6 flex flex-row items-center justify-between">
              <CardTitle className="text-lg font-semibold" style={{ fontFamily: 'Outfit, sans-serif' }}>
                Sales Trend (30 Days)
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={salesChart}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis
                      dataKey="date"
                      stroke="#64748b"
                      fontSize={12}
                      tickFormatter={(value) => new Date(value).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                    />
                    <YAxis
                      stroke="#64748b"
                      fontSize={12}
                      tickFormatter={(value) => `${(value / 1000).toFixed(0)}K`}
                    />
                    <Tooltip formatter={(value) => formatCurrency(value)} />
                    <Line
                      type="monotone"
                      dataKey="sales"
                      stroke="#4f46e5"
                      strokeWidth={2}
                      dot={{ fill: '#4f46e5', strokeWidth: 2 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          {/* Orders by Status */}
          {salesReport && (
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-lg font-semibold" style={{ fontFamily: 'Outfit, sans-serif' }}>
                    Orders List
                  </CardTitle>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => exportToCSV(salesReport.orders, 'sales-report')}
                    className="gap-2"
                    data-testid="export-sales-btn"
                  >
                    <Download className="w-4 h-4" />
                    Export CSV
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="p-0">
                <Table>
                  <TableHeader>
                    <TableRow className="table-header">
                      <TableHead className="table-header-cell">Order #</TableHead>
                      <TableHead className="table-header-cell">Customer</TableHead>
                      <TableHead className="table-header-cell">Date</TableHead>
                      <TableHead className="table-header-cell text-right">Total</TableHead>
                      <TableHead className="table-header-cell">Status</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {salesReport.orders.slice(0, 20).map((order) => (
                      <TableRow key={order.id} className="table-row">
                        <TableCell className="table-cell font-medium">{order.order_number}</TableCell>
                        <TableCell className="table-cell">{order.customer_name}</TableCell>
                        <TableCell className="table-cell text-slate-500">
                          {new Date(order.created_at).toLocaleDateString()}
                        </TableCell>
                        <TableCell className="table-cell text-right font-medium">{formatCurrency(order.total)}</TableCell>
                        <TableCell className="table-cell capitalize">{order.status}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="products" className="space-y-6">
          {/* Top Products Chart */}
          <Card className="p-6">
            <CardHeader className="p-0 pb-6 flex flex-row items-center justify-between">
              <CardTitle className="text-lg font-semibold" style={{ fontFamily: 'Outfit, sans-serif' }}>
                Top Selling Products
              </CardTitle>
              <Button
                variant="outline"
                size="sm"
                onClick={() => exportToCSV(topProducts, 'top-products')}
                className="gap-2"
                data-testid="export-products-btn"
              >
                <Download className="w-4 h-4" />
                Export CSV
              </Button>
            </CardHeader>
            <CardContent className="p-0">
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={topProducts} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" horizontal={false} />
                    <XAxis
                      type="number"
                      stroke="#64748b"
                      fontSize={12}
                      tickFormatter={(value) => `${(value / 1000).toFixed(0)}K`}
                    />
                    <YAxis
                      type="category"
                      dataKey="product_name"
                      stroke="#64748b"
                      fontSize={12}
                      width={150}
                      tickFormatter={(value) => value.length > 20 ? value.substring(0, 20) + '...' : value}
                    />
                    <Tooltip formatter={(value) => formatCurrency(value)} />
                    <Bar dataKey="total_revenue" fill="#4f46e5" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          {/* Products Table */}
          <Card>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow className="table-header">
                    <TableHead className="table-header-cell">Product</TableHead>
                    <TableHead className="table-header-cell text-right">Qty Sold</TableHead>
                    <TableHead className="table-header-cell text-right">Total Revenue</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {topProducts.map((product, index) => (
                    <TableRow key={product.product_id} className="table-row">
                      <TableCell className="table-cell font-medium">
                        <div className="flex items-center gap-2">
                          <span className="text-slate-400 text-sm">#{index + 1}</span>
                          {product.product_name}
                        </div>
                      </TableCell>
                      <TableCell className="table-cell text-right">{product.quantity_sold}</TableCell>
                      <TableCell className="table-cell text-right font-medium text-emerald-600">
                        {formatCurrency(product.total_revenue)}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default Reports;
