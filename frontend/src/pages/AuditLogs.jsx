import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Badge } from '../components/ui/badge';
import { toast } from 'sonner';
import { auditLogsAPI } from '../lib/api';
import { 
  FileText, Search, RefreshCw, User, Clock, 
  Filter, Download, Shield
} from 'lucide-react';

export default function AuditLogs() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterAction, setFilterAction] = useState('all');
  const [limit, setLimit] = useState(100);

  useEffect(() => {
    fetchLogs();
  }, [limit]);

  const fetchLogs = async () => {
    try {
      setLoading(true);
      const response = await auditLogsAPI.getAll(limit);
      setLogs(response.data);
    } catch (error) {
      if (error.response?.status === 403) {
        toast.error('Admin access required to view audit logs');
      } else {
        toast.error('Failed to load audit logs');
      }
    } finally {
      setLoading(false);
    }
  };

  const getActionColor = (action) => {
    if (action.includes('create') || action.includes('add')) return 'bg-green-100 text-green-700';
    if (action.includes('delete') || action.includes('remove')) return 'bg-red-100 text-red-700';
    if (action.includes('update') || action.includes('edit')) return 'bg-blue-100 text-blue-700';
    if (action.includes('login') || action.includes('auth')) return 'bg-purple-100 text-purple-700';
    if (action.includes('reset') || action.includes('restore')) return 'bg-orange-100 text-orange-700';
    return 'bg-slate-100 text-slate-700';
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  const formatDetails = (details) => {
    if (!details) return '-';
    if (typeof details === 'string') return details;
    if (typeof details === 'object') {
      return JSON.stringify(details, null, 0).slice(0, 100) + (JSON.stringify(details).length > 100 ? '...' : '');
    }
    return String(details);
  };

  const filteredLogs = logs.filter(log => {
    const detailsStr = typeof log.details === 'object' ? JSON.stringify(log.details) : (log.details || '');
    const matchesSearch = 
      log.action?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      log.user_email?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      detailsStr.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesFilter = filterAction === 'all' || log.action?.includes(filterAction);
    
    return matchesSearch && matchesFilter;
  });

  const uniqueActions = [...new Set(logs.map(log => log.action?.split('_')[0]))].filter(Boolean);

  const exportLogs = () => {
    const csvContent = [
      ['Timestamp', 'Action', 'User', 'Details'].join(','),
      ...filteredLogs.map(log => [
        log.timestamp,
        log.action,
        log.user_email || 'System',
        `"${formatDetails(log.details).replace(/"/g, '""')}"`
      ].join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `audit-logs-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    toast.success('Audit logs exported');
  };

  return (
    <div className="space-y-6" data-testid="audit-logs-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
            <Shield className="w-6 h-6 text-purple-600" />
            Audit Logs
          </h1>
          <p className="text-slate-500 text-sm mt-1">
            Track all system activities and changes (Admin Only)
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={exportLogs} data-testid="export-logs-btn">
            <Download className="w-4 h-4 mr-2" />
            Export CSV
          </Button>
          <Button onClick={fetchLogs} disabled={loading} data-testid="refresh-logs-btn">
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-4">
          <div className="flex flex-wrap gap-4">
            <div className="flex-1 min-w-[200px]">
              <div className="relative">
                <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                <Input
                  placeholder="Search by action, user, or details..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-9"
                  data-testid="search-logs-input"
                />
              </div>
            </div>
            <div className="w-[150px]">
              <Select value={filterAction} onValueChange={setFilterAction}>
                <SelectTrigger data-testid="filter-action-select">
                  <Filter className="w-4 h-4 mr-2" />
                  <SelectValue placeholder="Filter" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Actions</SelectItem>
                  {uniqueActions.map(action => (
                    <SelectItem key={action} value={action}>
                      {action.charAt(0).toUpperCase() + action.slice(1)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="w-[120px]">
              <Select value={limit.toString()} onValueChange={(v) => setLimit(parseInt(v))}>
                <SelectTrigger data-testid="limit-select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="50">50 logs</SelectItem>
                  <SelectItem value="100">100 logs</SelectItem>
                  <SelectItem value="250">250 logs</SelectItem>
                  <SelectItem value="500">500 logs</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Logs Table */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-lg flex items-center gap-2">
            <FileText className="w-5 h-5" />
            Activity Log
            <Badge variant="secondary" className="ml-2">
              {filteredLogs.length} records
            </Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8 text-slate-500">
              <RefreshCw className="w-6 h-6 animate-spin mx-auto mb-2" />
              Loading audit logs...
            </div>
          ) : filteredLogs.length === 0 ? (
            <div className="text-center py-8 text-slate-500">
              <FileText className="w-10 h-10 mx-auto mb-2 text-slate-300" />
              No audit logs found
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-slate-50">
                    <th className="text-left p-3 font-medium text-slate-600">Timestamp</th>
                    <th className="text-left p-3 font-medium text-slate-600">Action</th>
                    <th className="text-left p-3 font-medium text-slate-600">User</th>
                    <th className="text-left p-3 font-medium text-slate-600">Details</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredLogs.map((log, index) => (
                    <tr 
                      key={log.id || index} 
                      className="border-b hover:bg-slate-50 transition-colors"
                    >
                      <td className="p-3">
                        <div className="flex items-center gap-2 text-slate-600">
                          <Clock className="w-3 h-3" />
                          {formatDate(log.timestamp)}
                        </div>
                      </td>
                      <td className="p-3">
                        <Badge className={getActionColor(log.action || '')}>
                          {log.action?.replace(/_/g, ' ') || 'N/A'}
                        </Badge>
                      </td>
                      <td className="p-3">
                        <div className="flex items-center gap-2">
                          <User className="w-3 h-3 text-slate-400" />
                          <span className="text-slate-700">{log.user_email || 'System'}</span>
                        </div>
                      </td>
                      <td className="p-3">
                        <span className="text-slate-600 text-xs">
                          {formatDetails(log.details)}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
