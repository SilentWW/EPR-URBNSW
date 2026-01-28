import React, { useState, useEffect } from 'react';
import { dashboardAPI, inventoryAPI, accountingAPI } from '../lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import {
  Package,
  Users,
  Truck,
  ShoppingCart,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  DollarSign,
  ArrowUpRight,
  ArrowDownRight,
  Loader2,
  RefreshCw
} from 'lucide-react';
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
    maximumFractionDigits: 0,
  }).format(amount);
};

const StatCard = ({ title, value, icon: Icon, trend, trendValue, color, onClick }) => (
  <Card 
    className={`stat-card ${onClick ? 'cursor-pointer card-interactive' : ''}`}
    onClick={onClick}
    data-testid={`stat-${title.toLowerCase().replace(/\s+/g, '-')}`}
  >
    <div className="flex items-start justify-between">
      <div>
        <p className="text-sm font-medium text-slate-500">{title}</p>
        <p className="text-2xl font-bold text-slate-900 mt-1" style={{ fontFamily: 'Outfit, sans-serif' }}>
          {value}
        </p>
        {trend && (
          <div className={`flex items-center gap-1 mt-2 text-sm ${trend === 'up' ? 'text-emerald-600' : 'text-red-600'}`}>
            {trend === 'up' ? <ArrowUpRight className="w-4 h-4" /> : <ArrowDownRight className="w-4 h-4" />}
            <span>{trendValue}</span>
          </div>
        )}
      </div>
      <div className={`stat-icon ${color}`}>
        <Icon className="w-6 h-6 text-white" />
      </div>
    </div>
  </Card>
);

export const Dashboard = () => {
  const [summary, setSummary] = useState(null);
  const [salesChart, setSalesChart] = useState([]);
  const [topProducts, setTopProducts] = useState([]);
  const [lowStock, setLowStock] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchData = async () => {
    try {
      const [summaryRes, chartRes, topRes, lowStockRes] = await Promise.all([
        dashboardAPI.getSummary(),
        dashboardAPI.getSalesChart('7days'),
        dashboardAPI.getTopProducts(5),
        inventoryAPI.getLowStock(),
      ]);

      setSummary(summaryRes.data);
      setSalesChart(chartRes.data);
      setTopProducts(topRes.data);
      setLowStock(lowStockRes.data);
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchData();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96" data-testid="dashboard-loading">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="dashboard-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900" style={{ fontFamily: 'Outfit, sans-serif' }}>
            Business Overview
          </h2>
          <p className="text-slate-500 mt-1">Welcome back! Here&apos;s what&apos;s happening.</p>
        </div>
        <Button
          variant="outline"
          onClick={handleRefresh}
          disabled={refreshing}
          className="gap-2"
          data-testid="refresh-btn"
        >
          <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Sales"
          value={formatCurrency(summary?.total_sales || 0)}
          icon={TrendingUp}
          color="bg-indigo-600"
        />
        <StatCard
          title="Products"
          value={summary?.products_count || 0}
          icon={Package}
          color="bg-emerald-600"
        />
        <StatCard
          title="Customers"
          value={summary?.customers_count || 0}
          icon={Users}
          color="bg-blue-600"
        />
        <StatCard
          title="Suppliers"
          value={summary?.suppliers_count || 0}
          icon={Truck}
          color="bg-violet-600"
        />
      </div>

      {/* Financial Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Net Profit"
          value={formatCurrency(summary?.net_profit || 0)}
          icon={DollarSign}
          trend={summary?.net_profit >= 0 ? 'up' : 'down'}
          color={summary?.net_profit >= 0 ? 'bg-emerald-600' : 'bg-red-600'}
        />
        <StatCard
          title="Receivables"
          value={formatCurrency(summary?.receivables || 0)}
          icon={TrendingUp}
          color="bg-amber-600"
        />
        <StatCard
          title="Payables"
          value={formatCurrency(summary?.payables || 0)}
          icon={TrendingDown}
          color="bg-orange-600"
        />
        <StatCard
          title="Pending Orders"
          value={summary?.pending_orders || 0}
          icon={ShoppingCart}
          color="bg-cyan-600"
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Sales Chart */}
        <Card className="p-6" data-testid="sales-chart-card">
          <CardHeader className="p-0 pb-6">
            <CardTitle className="text-lg font-semibold" style={{ fontFamily: 'Outfit, sans-serif' }}>
              Sales Trend (7 Days)
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="h-72">
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
                  <Tooltip 
                    formatter={(value) => formatCurrency(value)}
                    labelFormatter={(label) => new Date(label).toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="sales" 
                    stroke="#4f46e5" 
                    strokeWidth={2}
                    dot={{ fill: '#4f46e5', strokeWidth: 2 }}
                    activeDot={{ r: 6, fill: '#4f46e5' }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Top Products */}
        <Card className="p-6" data-testid="top-products-card">
          <CardHeader className="p-0 pb-6">
            <CardTitle className="text-lg font-semibold" style={{ fontFamily: 'Outfit, sans-serif' }}>
              Top Selling Products
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="h-72">
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
                    width={120}
                    tickFormatter={(value) => value.length > 15 ? value.substring(0, 15) + '...' : value}
                  />
                  <Tooltip formatter={(value) => formatCurrency(value)} />
                  <Bar dataKey="total_revenue" fill="#4f46e5" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Low Stock Alert */}
      {lowStock.length > 0 && (
        <Card className="border-amber-200 bg-amber-50/50" data-testid="low-stock-alert">
          <CardHeader className="pb-3">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-amber-600" />
              <CardTitle className="text-lg font-semibold text-amber-800" style={{ fontFamily: 'Outfit, sans-serif' }}>
                Low Stock Alert ({lowStock.length} items)
              </CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {lowStock.slice(0, 6).map((product) => (
                <div
                  key={product.id}
                  className="flex items-center justify-between p-3 bg-white rounded-lg border border-amber-100"
                >
                  <div>
                    <p className="font-medium text-slate-900 text-sm">{product.name}</p>
                    <p className="text-xs text-slate-500">{product.sku}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-lg font-bold text-amber-600">{product.stock_quantity}</p>
                    <p className="text-xs text-slate-500">in stock</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default Dashboard;
