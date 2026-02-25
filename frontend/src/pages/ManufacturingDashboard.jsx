import React, { useState, useEffect } from 'react';
import api from '../lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../components/ui/table';
import { 
  Factory, Boxes, Package, TrendingUp, AlertTriangle, CheckCircle2,
  Clock, Play, ClipboardCheck, XCircle, RefreshCw, Loader2,
  ArrowUpRight, ArrowDownRight, Hammer
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const formatCurrency = (amount) => {
  return new Intl.NumberFormat('en-LK', {
    style: 'currency',
    currency: 'LKR',
    minimumFractionDigits: 0,
  }).format(amount || 0);
};

const STATUS_CONFIG = {
  draft: { label: 'Draft', color: 'bg-slate-100 text-slate-700', icon: Factory },
  materials_issued: { label: 'Materials Issued', color: 'bg-blue-100 text-blue-700', icon: Boxes },
  in_progress: { label: 'In Progress', color: 'bg-amber-100 text-amber-700', icon: Play },
  qc_pending: { label: 'QC Pending', color: 'bg-purple-100 text-purple-700', icon: ClipboardCheck },
  completed: { label: 'Completed', color: 'bg-green-100 text-green-700', icon: CheckCircle2 },
  cancelled: { label: 'Cancelled', color: 'bg-red-100 text-red-700', icon: XCircle }
};

export const ManufacturingDashboard = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const navigate = useNavigate();

  const fetchDashboard = async (showRefresh = false) => {
    if (showRefresh) setRefreshing(true);
    try {
      const response = await api.get('/manufacturing/dashboard/summary');
      setDashboardData(response.data);
    } catch (error) {
      console.error('Failed to fetch dashboard:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
  }, []);

  const getStatusBadge = (status) => {
    const config = STATUS_CONFIG[status] || STATUS_CONFIG.draft;
    const Icon = config.icon;
    return (
      <Badge className={`${config.color} gap-1`}>
        <Icon className="w-3 h-3" />
        {config.label}
      </Badge>
    );
  };

  // Calculate totals from status summary
  const statusSummary = dashboardData?.status_summary || {};
  const totalOrders = Object.values(statusSummary).reduce((sum, count) => sum + count, 0);
  const activeOrders = (statusSummary.draft || 0) + (statusSummary.materials_issued || 0) + 
                       (statusSummary.in_progress || 0) + (statusSummary.qc_pending || 0);
  const completedOrders = statusSummary.completed || 0;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="manufacturing-dashboard">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-slate-900" style={{ fontFamily: 'Outfit, sans-serif' }}>
            Manufacturing Dashboard
          </h2>
          <p className="text-slate-500 mt-1">Production overview and KPIs</p>
        </div>
        <div className="flex gap-2">
          <Button 
            variant="outline" 
            onClick={() => fetchDashboard(true)}
            disabled={refreshing}
            className="gap-2"
          >
            {refreshing ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
            Refresh
          </Button>
          <Button 
            onClick={() => navigate('/work-orders')} 
            className="gap-2 bg-indigo-600 hover:bg-indigo-700"
          >
            <Factory className="w-4 h-4" />
            View Work Orders
          </Button>
        </div>
      </div>

      {/* KPI Cards - Top Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* This Month Production Value */}
        <Card className="border-l-4 border-l-green-500">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">This Month Production</p>
                <p className="text-2xl font-bold text-slate-900">
                  {formatCurrency(dashboardData?.this_month?.production_value)}
                </p>
                <p className="text-xs text-slate-400 mt-1">
                  {dashboardData?.this_month?.units_produced || 0} units produced
                </p>
              </div>
              <div className="p-3 bg-green-100 rounded-full">
                <TrendingUp className="w-6 h-6 text-green-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Orders Completed */}
        <Card className="border-l-4 border-l-blue-500">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Orders Completed</p>
                <p className="text-2xl font-bold text-slate-900">
                  {dashboardData?.this_month?.orders_completed || 0}
                </p>
                <p className="text-xs text-slate-400 mt-1">
                  This month
                </p>
              </div>
              <div className="p-3 bg-blue-100 rounded-full">
                <CheckCircle2 className="w-6 h-6 text-blue-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Active Work Orders */}
        <Card className="border-l-4 border-l-amber-500">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Active Orders</p>
                <p className="text-2xl font-bold text-slate-900">{activeOrders}</p>
                <p className="text-xs text-slate-400 mt-1">
                  {statusSummary.in_progress || 0} in progress
                </p>
              </div>
              <div className="p-3 bg-amber-100 rounded-full">
                <Play className="w-6 h-6 text-amber-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Low Stock Materials */}
        <Card className={`border-l-4 ${(dashboardData?.low_stock_materials?.length || 0) > 0 ? 'border-l-red-500' : 'border-l-slate-300'}`}>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Low Stock Alerts</p>
                <p className={`text-2xl font-bold ${(dashboardData?.low_stock_materials?.length || 0) > 0 ? 'text-red-600' : 'text-slate-900'}`}>
                  {dashboardData?.low_stock_materials?.length || 0}
                </p>
                <p className="text-xs text-slate-400 mt-1">
                  Raw materials
                </p>
              </div>
              <div className={`p-3 rounded-full ${(dashboardData?.low_stock_materials?.length || 0) > 0 ? 'bg-red-100' : 'bg-slate-100'}`}>
                <AlertTriangle className={`w-6 h-6 ${(dashboardData?.low_stock_materials?.length || 0) > 0 ? 'text-red-600' : 'text-slate-400'}`} />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Second Row - Status Breakdown & Low Stock */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Work Order Status Breakdown */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-lg flex items-center gap-2">
              <Factory className="w-5 h-5 text-indigo-600" />
              Work Order Status
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Object.entries(STATUS_CONFIG).map(([status, config]) => {
                const count = statusSummary[status] || 0;
                const percentage = totalOrders > 0 ? Math.round((count / totalOrders) * 100) : 0;
                const Icon = config.icon;
                
                return (
                  <div key={status} className="flex items-center gap-3">
                    <div className={`p-2 rounded ${config.color}`}>
                      <Icon className="w-4 h-4" />
                    </div>
                    <div className="flex-1">
                      <div className="flex justify-between items-center mb-1">
                        <span className="text-sm font-medium">{config.label}</span>
                        <span className="text-sm text-slate-500">{count}</span>
                      </div>
                      <div className="w-full bg-slate-100 rounded-full h-2">
                        <div 
                          className={`h-2 rounded-full ${config.color.replace('text-', 'bg-').split(' ')[0]}`}
                          style={{ width: `${percentage}%` }}
                        />
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
            <div className="mt-4 pt-4 border-t flex justify-between items-center">
              <span className="text-sm text-slate-500">Total Work Orders</span>
              <span className="text-lg font-bold">{totalOrders}</span>
            </div>
          </CardContent>
        </Card>

        {/* Low Stock Materials Alert */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-lg flex items-center gap-2">
              <Boxes className="w-5 h-5 text-orange-600" />
              Raw Material Stock Alerts
            </CardTitle>
          </CardHeader>
          <CardContent>
            {dashboardData?.low_stock_materials?.length > 0 ? (
              <div className="space-y-3">
                {dashboardData.low_stock_materials.map((material, idx) => (
                  <div key={idx} className="flex items-center justify-between p-3 bg-red-50 border border-red-100 rounded-lg">
                    <div className="flex items-center gap-3">
                      <AlertTriangle className="w-5 h-5 text-red-500" />
                      <div>
                        <p className="font-medium text-slate-900">{material.name}</p>
                        <p className="text-xs text-slate-500">
                          Threshold: {material.low_stock_threshold} {material.unit}
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className={`font-bold ${material.stock_quantity <= 0 ? 'text-red-600' : 'text-amber-600'}`}>
                        {material.stock_quantity} {material.unit}
                      </p>
                      <Badge variant="outline" className={material.stock_quantity <= 0 ? 'text-red-600 border-red-300' : 'text-amber-600 border-amber-300'}>
                        {material.stock_quantity <= 0 ? 'Out of Stock' : 'Low Stock'}
                      </Badge>
                    </div>
                  </div>
                ))}
                <Button 
                  variant="outline" 
                  className="w-full mt-2"
                  onClick={() => navigate('/raw-materials')}
                >
                  <Hammer className="w-4 h-4 mr-2" />
                  Manage Raw Materials
                </Button>
              </div>
            ) : (
              <div className="text-center py-8">
                <CheckCircle2 className="w-12 h-12 text-green-500 mx-auto mb-3" />
                <p className="text-slate-600 font-medium">All materials in stock</p>
                <p className="text-sm text-slate-400 mt-1">No low stock alerts</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Recent Work Orders */}
      <Card>
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg flex items-center gap-2">
              <Clock className="w-5 h-5 text-slate-600" />
              Recent Work Orders
            </CardTitle>
            <Button variant="ghost" size="sm" onClick={() => navigate('/work-orders')}>
              View All
              <ArrowUpRight className="w-4 h-4 ml-1" />
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {dashboardData?.recent_work_orders?.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>WO Number</TableHead>
                  <TableHead>Product</TableHead>
                  <TableHead className="text-right">Quantity</TableHead>
                  <TableHead className="text-right">Completed</TableHead>
                  <TableHead className="text-right">Est. Cost</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {dashboardData.recent_work_orders.map((wo) => (
                  <TableRow key={wo.id} className="cursor-pointer hover:bg-slate-50" onClick={() => navigate('/work-orders')}>
                    <TableCell className="font-medium">{wo.wo_number}</TableCell>
                    <TableCell>
                      <div>
                        {wo.product_name}
                        {wo.variation_name && (
                          <Badge variant="secondary" className="ml-2 text-xs">
                            {wo.variation_name}
                          </Badge>
                        )}
                      </div>
                    </TableCell>
                    <TableCell className="text-right">{wo.quantity}</TableCell>
                    <TableCell className="text-right">
                      {wo.quantity_completed || 0}
                      {wo.quantity_passed_qc > 0 && (
                        <span className="text-green-600 text-xs ml-1">({wo.quantity_passed_qc} QC✓)</span>
                      )}
                    </TableCell>
                    <TableCell className="text-right">{formatCurrency(wo.estimated_total_cost)}</TableCell>
                    <TableCell>{getStatusBadge(wo.status)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <div className="text-center py-8">
              <Factory className="w-12 h-12 text-slate-300 mx-auto mb-3" />
              <p className="text-slate-600">No work orders yet</p>
              <Button 
                className="mt-3 bg-indigo-600 hover:bg-indigo-700"
                onClick={() => navigate('/work-orders')}
              >
                Create First Work Order
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="hover:shadow-md transition-shadow cursor-pointer" onClick={() => navigate('/raw-materials')}>
          <CardContent className="p-6 flex items-center gap-4">
            <div className="p-3 bg-orange-100 rounded-lg">
              <Hammer className="w-6 h-6 text-orange-600" />
            </div>
            <div>
              <h3 className="font-semibold text-slate-900">Raw Materials</h3>
              <p className="text-sm text-slate-500">Manage inventory</p>
            </div>
            <ArrowUpRight className="w-5 h-5 text-slate-400 ml-auto" />
          </CardContent>
        </Card>

        <Card className="hover:shadow-md transition-shadow cursor-pointer" onClick={() => navigate('/bom')}>
          <CardContent className="p-6 flex items-center gap-4">
            <div className="p-3 bg-teal-100 rounded-lg">
              <Package className="w-6 h-6 text-teal-600" />
            </div>
            <div>
              <h3 className="font-semibold text-slate-900">Bill of Materials</h3>
              <p className="text-sm text-slate-500">Product recipes</p>
            </div>
            <ArrowUpRight className="w-5 h-5 text-slate-400 ml-auto" />
          </CardContent>
        </Card>

        <Card className="hover:shadow-md transition-shadow cursor-pointer" onClick={() => navigate('/work-orders')}>
          <CardContent className="p-6 flex items-center gap-4">
            <div className="p-3 bg-indigo-100 rounded-lg">
              <Factory className="w-6 h-6 text-indigo-600" />
            </div>
            <div>
              <h3 className="font-semibold text-slate-900">Work Orders</h3>
              <p className="text-sm text-slate-500">Production orders</p>
            </div>
            <ArrowUpRight className="w-5 h-5 text-slate-400 ml-auto" />
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default ManufacturingDashboard;
