import React, { useState, useEffect } from 'react';
import { companyAPI, usersAPI } from '../lib/api';
import api from '../lib/api';
import { useAuth } from '../context/AuthContext';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Switch } from '../components/ui/switch';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { 
  Plus, 
  Loader2, 
  Building2, 
  Users, 
  ShoppingBag, 
  Trash2,
  RefreshCw,
  CheckCircle,
  XCircle,
  Clock,
  Package,
  ShoppingCart,
  UserCheck,
  Zap,
  AlertCircle
} from 'lucide-react';
import { toast } from 'sonner';

export const Settings = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [company, setCompany] = useState(null);
  const [wooSettings, setWooSettings] = useState({
    store_url: '',
    consumer_key: '',
    consumer_secret: '',
    enabled: false,
    auto_sync_enabled: false,
    auto_sync_interval: 60,
  });
  const [users, setUsers] = useState([]);
  const [userDialogOpen, setUserDialogOpen] = useState(false);
  const [newUser, setNewUser] = useState({
    full_name: '',
    email: '',
    password: '',
  });
  
  // WooCommerce sync states
  const [syncStatus, setSyncStatus] = useState(null);
  const [syncLogs, setSyncLogs] = useState([]);
  const [syncing, setSyncing] = useState(false);
  const [testingConnection, setTestingConnection] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState(null);

  const fetchData = async () => {
    try {
      const [companyRes, wooRes, usersRes] = await Promise.all([
        companyAPI.get(),
        companyAPI.getWooSettings(),
        user?.role === 'admin' ? usersAPI.getAll() : Promise.resolve({ data: [] }),
      ]);
      setCompany(companyRes.data);
      if (wooRes.data) {
        setWooSettings({
          store_url: wooRes.data.store_url || '',
          consumer_key: wooRes.data.consumer_key || '',
          consumer_secret: wooRes.data.consumer_secret || '',
          enabled: wooRes.data.enabled || false,
          auto_sync_enabled: wooRes.data.auto_sync_enabled || false,
          auto_sync_interval: wooRes.data.auto_sync_interval || 60,
        });
      }
      setUsers(usersRes.data);
      
      // Fetch sync logs if WooCommerce is enabled
      if (wooRes.data?.enabled) {
        fetchSyncLogs();
        fetchSyncStatus();
      }
    } catch (error) {
      toast.error('Failed to load settings');
    } finally {
      setLoading(false);
    }
  };

  const fetchSyncLogs = async () => {
    try {
      const response = await api.get('/woocommerce/sync-logs', { params: { limit: 10 } });
      setSyncLogs(response.data);
    } catch (error) {
      console.error('Failed to fetch sync logs');
    }
  };

  const fetchSyncStatus = async () => {
    try {
      const response = await api.get('/woocommerce/sync-status');
      setSyncStatus(response.data);
    } catch (error) {
      console.error('Failed to fetch sync status');
    }
  };

  useEffect(() => {
    fetchData();
  }, [user]);

  const handleSaveCompany = async () => {
    setSaving(true);
    try {
      await companyAPI.update(company);
      toast.success('Company settings saved');
    } catch (error) {
      toast.error('Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  const handleSaveWoo = async () => {
    setSaving(true);
    try {
      await companyAPI.updateWooSettings(wooSettings);
      toast.success('WooCommerce settings saved');
      if (wooSettings.enabled) {
        fetchSyncLogs();
        fetchSyncStatus();
      }
    } catch (error) {
      toast.error('Failed to save WooCommerce settings');
    } finally {
      setSaving(false);
    }
  };

  const handleTestConnection = async () => {
    setTestingConnection(true);
    setConnectionStatus(null);
    try {
      const response = await api.get('/woocommerce/test-connection');
      setConnectionStatus(response.data);
      if (response.data.success) {
        toast.success('Connection successful!');
      } else {
        toast.error(response.data.message || 'Connection failed');
      }
    } catch (error) {
      setConnectionStatus({ success: false, message: error.response?.data?.detail || 'Connection failed' });
      toast.error('Connection test failed');
    } finally {
      setTestingConnection(false);
    }
  };

  const handleManualSync = async (syncType) => {
    setSyncing(true);
    try {
      let endpoint = '/woocommerce/full-sync';
      let message = 'Full sync started';
      
      if (syncType === 'products') {
        endpoint = '/woocommerce/products/sync';
        message = 'Product sync started';
      } else if (syncType === 'orders') {
        endpoint = '/woocommerce/orders/sync';
        message = 'Order sync started';
      } else if (syncType === 'customers') {
        endpoint = '/woocommerce/customers/sync';
        message = 'Customer sync started';
      }
      
      const response = await api.post(endpoint);
      toast.success(message);
      
      // Poll for completion
      setTimeout(() => {
        fetchSyncLogs();
        fetchSyncStatus();
        setSyncing(false);
      }, 3000);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Sync failed');
      setSyncing(false);
    }
  };

  const handleAddUser = async () => {
    setSaving(true);
    try {
      await usersAPI.create(newUser);
      toast.success('User created successfully');
      setUserDialogOpen(false);
      setNewUser({ full_name: '', email: '', password: '' });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create user');
    } finally {
      setSaving(false);
    }
  };

  const handleUpdateRole = async (userId, role) => {
    try {
      await usersAPI.updateRole(userId, role);
      toast.success('Role updated');
      fetchData();
    } catch (error) {
      toast.error('Failed to update role');
    }
  };

  const handleDeleteUser = async (userId) => {
    if (!window.confirm('Are you sure you want to delete this user?')) return;
    try {
      await usersAPI.delete(userId);
      toast.success('User deleted');
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete user');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="settings-page">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-slate-900" style={{ fontFamily: 'Outfit, sans-serif' }}>
          Settings
        </h2>
        <p className="text-slate-500 mt-1">Manage your company and system settings</p>
      </div>

      <Tabs defaultValue="company" className="space-y-4">
        <TabsList>
          <TabsTrigger value="company">Company</TabsTrigger>
          <TabsTrigger value="woocommerce">WooCommerce</TabsTrigger>
          {user?.role === 'admin' && <TabsTrigger value="users">Users</TabsTrigger>}
        </TabsList>

        {/* Company Settings */}
        <TabsContent value="company">
          <Card>
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-indigo-100">
                  <Building2 className="w-5 h-5 text-indigo-600" />
                </div>
                <div>
                  <CardTitle>Company Information</CardTitle>
                  <CardDescription>Basic company details and preferences</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                  <Label>Company Name</Label>
                  <Input
                    value={company?.name || ''}
                    onChange={(e) => setCompany({ ...company, name: e.target.value })}
                    data-testid="company-name"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Email</Label>
                  <Input
                    type="email"
                    value={company?.email || ''}
                    onChange={(e) => setCompany({ ...company, email: e.target.value })}
                    data-testid="company-email"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Phone</Label>
                  <Input
                    value={company?.phone || ''}
                    onChange={(e) => setCompany({ ...company, phone: e.target.value })}
                    data-testid="company-phone"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Currency</Label>
                  <Select
                    value={company?.currency || 'LKR'}
                    onValueChange={(v) => setCompany({ ...company, currency: v })}
                  >
                    <SelectTrigger data-testid="company-currency">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="LKR">LKR - Sri Lankan Rupee</SelectItem>
                      <SelectItem value="USD">USD - US Dollar</SelectItem>
                      <SelectItem value="EUR">EUR - Euro</SelectItem>
                      <SelectItem value="GBP">GBP - British Pound</SelectItem>
                      <SelectItem value="INR">INR - Indian Rupee</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Timezone</Label>
                  <Select
                    value={company?.timezone || 'Asia/Colombo'}
                    onValueChange={(v) => setCompany({ ...company, timezone: v })}
                  >
                    <SelectTrigger data-testid="company-timezone">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Asia/Colombo">Asia/Colombo (Sri Lanka)</SelectItem>
                      <SelectItem value="UTC">UTC</SelectItem>
                      <SelectItem value="America/New_York">America/New York</SelectItem>
                      <SelectItem value="Europe/London">Europe/London</SelectItem>
                      <SelectItem value="Asia/Dubai">Asia/Dubai</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Tax Rate (%)</Label>
                  <Input
                    type="number"
                    value={company?.tax_rate || 0}
                    onChange={(e) => setCompany({ ...company, tax_rate: parseFloat(e.target.value) || 0 })}
                    data-testid="company-tax"
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label>Address</Label>
                <Input
                  value={company?.address || ''}
                  onChange={(e) => setCompany({ ...company, address: e.target.value })}
                  data-testid="company-address"
                />
              </div>
              <div className="flex justify-end">
                <Button
                  onClick={handleSaveCompany}
                  disabled={saving}
                  className="bg-indigo-600 hover:bg-indigo-700"
                  data-testid="save-company-btn"
                >
                  {saving ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                  Save Changes
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* WooCommerce Settings */}
        <TabsContent value="woocommerce">
          <Card>
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-violet-100">
                  <ShoppingBag className="w-5 h-5 text-violet-600" />
                </div>
                <div>
                  <CardTitle>WooCommerce Integration</CardTitle>
                  <CardDescription>Connect your WooCommerce store for two-way sync</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center justify-between p-4 bg-slate-50 rounded-lg">
                <div>
                  <p className="font-medium">Enable Integration</p>
                  <p className="text-sm text-slate-500">Turn on/off WooCommerce sync</p>
                </div>
                <Switch
                  checked={wooSettings.enabled}
                  onCheckedChange={(checked) => setWooSettings({ ...wooSettings, enabled: checked })}
                  data-testid="woo-enabled"
                />
              </div>

              <div className="space-y-4">
                <div className="space-y-2">
                  <Label>Store URL</Label>
                  <Input
                    value={wooSettings.store_url}
                    onChange={(e) => setWooSettings({ ...wooSettings, store_url: e.target.value })}
                    placeholder="https://yourstore.com"
                    data-testid="woo-url"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Consumer Key</Label>
                  <Input
                    value={wooSettings.consumer_key}
                    onChange={(e) => setWooSettings({ ...wooSettings, consumer_key: e.target.value })}
                    placeholder="ck_xxxxxxxxxxxxxxxx"
                    data-testid="woo-key"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Consumer Secret</Label>
                  <Input
                    type="password"
                    value={wooSettings.consumer_secret}
                    onChange={(e) => setWooSettings({ ...wooSettings, consumer_secret: e.target.value })}
                    placeholder="cs_xxxxxxxxxxxxxxxx"
                    data-testid="woo-secret"
                  />
                </div>
              </div>

              <div className="p-4 bg-amber-50 rounded-lg border border-amber-200">
                <p className="text-sm text-amber-800">
                  <strong>Note:</strong> To get your API credentials, go to your WooCommerce store → 
                  Settings → Advanced → REST API → Add Key. Select Read/Write permissions.
                </p>
              </div>

              <div className="flex justify-end">
                <Button
                  onClick={handleSaveWoo}
                  disabled={saving}
                  className="bg-indigo-600 hover:bg-indigo-700"
                  data-testid="save-woo-btn"
                >
                  {saving ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                  Save WooCommerce Settings
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* User Management */}
        {user?.role === 'admin' && (
          <TabsContent value="users">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-emerald-100">
                      <Users className="w-5 h-5 text-emerald-600" />
                    </div>
                    <div>
                      <CardTitle>User Management</CardTitle>
                      <CardDescription>Manage team members and their roles</CardDescription>
                    </div>
                  </div>
                  <Button onClick={() => setUserDialogOpen(true)} className="gap-2 bg-indigo-600 hover:bg-indigo-700" data-testid="add-user-btn">
                    <Plus className="w-4 h-4" />
                    Add User
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="p-0">
                <Table>
                  <TableHeader>
                    <TableRow className="table-header">
                      <TableHead className="table-header-cell">Name</TableHead>
                      <TableHead className="table-header-cell">Email</TableHead>
                      <TableHead className="table-header-cell">Role</TableHead>
                      <TableHead className="table-header-cell">Joined</TableHead>
                      <TableHead className="table-header-cell w-12"></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {users.map((u) => (
                      <TableRow key={u.id} className="table-row">
                        <TableCell className="table-cell font-medium">{u.full_name}</TableCell>
                        <TableCell className="table-cell text-slate-500">{u.email}</TableCell>
                        <TableCell className="table-cell">
                          <Select
                            value={u.role}
                            onValueChange={(v) => handleUpdateRole(u.id, v)}
                            disabled={u.id === user.id}
                          >
                            <SelectTrigger className="w-32">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="admin">Admin</SelectItem>
                              <SelectItem value="manager">Manager</SelectItem>
                              <SelectItem value="accounts">Accounts</SelectItem>
                              <SelectItem value="store">Store</SelectItem>
                              <SelectItem value="staff">Staff</SelectItem>
                            </SelectContent>
                          </Select>
                        </TableCell>
                        <TableCell className="table-cell text-slate-500">
                          {new Date(u.created_at).toLocaleDateString()}
                        </TableCell>
                        <TableCell className="table-cell">
                          {u.id !== user.id && (
                            <Button
                              variant="ghost"
                              size="icon"
                              onClick={() => handleDeleteUser(u.id)}
                              className="text-red-600 hover:text-red-700 hover:bg-red-50"
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>
        )}
      </Tabs>

      {/* Add User Dialog */}
      <Dialog open={userDialogOpen} onOpenChange={setUserDialogOpen}>
        <DialogContent data-testid="add-user-dialog">
          <DialogHeader>
            <DialogTitle style={{ fontFamily: 'Outfit, sans-serif' }}>Add New User</DialogTitle>
            <DialogDescription>Create a new team member account</DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Full Name *</Label>
              <Input
                value={newUser.full_name}
                onChange={(e) => setNewUser({ ...newUser, full_name: e.target.value })}
                data-testid="new-user-name"
              />
            </div>
            <div className="space-y-2">
              <Label>Email *</Label>
              <Input
                type="email"
                value={newUser.email}
                onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
                data-testid="new-user-email"
              />
            </div>
            <div className="space-y-2">
              <Label>Password *</Label>
              <Input
                type="password"
                value={newUser.password}
                onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                data-testid="new-user-password"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setUserDialogOpen(false)}>Cancel</Button>
            <Button onClick={handleAddUser} disabled={saving} className="bg-indigo-600 hover:bg-indigo-700" data-testid="submit-user-btn">
              {saving ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
              Create User
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Settings;
