import React, { useState, useEffect } from 'react';
import { notificationsAPI } from '../lib/api';
import { useAuth } from '../context/AuthContext';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Switch } from '../components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Separator } from '../components/ui/separator';
import {
  Loader2,
  Bell,
  AlertTriangle,
  Package,
  CreditCard,
  ShoppingCart,
  Users,
  Calendar,
  Settings,
  Trash2,
  Check,
  CheckCheck,
  Mail,
  Send,
  Eye,
  EyeOff
} from 'lucide-react';
import { toast } from 'sonner';

const formatCurrency = (amount) => {
  return new Intl.NumberFormat('en-LK', {
    style: 'currency',
    currency: 'LKR',
    minimumFractionDigits: 0,
  }).format(amount);
};

const notificationIcons = {
  task_assignment: Users,
  task_update: Users,
  payroll: CreditCard,
  payslip: CreditCard,
  leave_approval: Calendar,
  leave_rejection: Calendar,
  inventory: Package,
  order: ShoppingCart,
  system: Settings,
  low_stock: AlertTriangle,
  pending_payment: CreditCard,
  new_order: ShoppingCart,
};

const notificationColors = {
  warning: 'bg-amber-100 text-amber-600',
  error: 'bg-red-100 text-red-600',
  info: 'bg-blue-100 text-blue-600',
  success: 'bg-emerald-100 text-emerald-600',
};

export const Notifications = () => {
  const { user } = useAuth();
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('all');
  
  // Preferences state
  const [preferences, setPreferences] = useState({
    task_assignments: true,
    task_updates: true,
    payroll_processed: true,
    payslip_ready: true,
    leave_approvals: true,
    leave_rejections: true,
    low_inventory: true,
    new_orders: true,
    email_enabled: true,
    in_app_enabled: true,
  });
  const [savingPrefs, setSavingPrefs] = useState(false);

  // SMTP Settings state
  const [smtpSettings, setSmtpSettings] = useState({
    smtp_host: '',
    smtp_port: 587,
    smtp_username: '',
    smtp_password: '',
    from_email: '',
    from_name: 'ERP System',
    use_tls: true,
    enabled: true,
  });
  const [smtpConfigured, setSmtpConfigured] = useState(false);
  const [savingSmtp, setSavingSmtp] = useState(false);
  const [testingSmtp, setTestingSmtp] = useState(false);
  const [testEmail, setTestEmail] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  const isAdmin = user?.role === 'admin' || user?.role === 'manager';

  const fetchNotifications = async () => {
    try {
      const response = await notificationsAPI.getAll({ limit: 100 });
      setNotifications(response.data.notifications || []);
    } catch (error) {
      toast.error('Failed to fetch notifications');
    } finally {
      setLoading(false);
    }
  };

  const fetchPreferences = async () => {
    try {
      const response = await notificationsAPI.getPreferences();
      setPreferences(prev => ({ ...prev, ...response.data }));
    } catch (error) {
      console.error('Failed to fetch preferences:', error);
    }
  };

  const fetchSmtpSettings = async () => {
    if (!isAdmin) return;
    try {
      const response = await notificationsAPI.getSmtpSettings();
      if (response.data.configured) {
        setSmtpConfigured(true);
        setSmtpSettings(prev => ({
          ...prev,
          ...response.data,
          smtp_password: '' // Don't show password
        }));
      }
    } catch (error) {
      console.error('Failed to fetch SMTP settings:', error);
    }
  };

  useEffect(() => {
    fetchNotifications();
    fetchPreferences();
    fetchSmtpSettings();
  }, []);

  const handleMarkRead = async (notificationId) => {
    try {
      await notificationsAPI.markRead(notificationId);
      setNotifications(prev =>
        prev.map(n => n.id === notificationId ? { ...n, is_read: true } : n)
      );
      toast.success('Notification marked as read');
    } catch (error) {
      toast.error('Failed to mark notification as read');
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await notificationsAPI.markAllRead();
      setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
      toast.success('All notifications marked as read');
    } catch (error) {
      toast.error('Failed to mark all as read');
    }
  };

  const handleDelete = async (notificationId) => {
    try {
      await notificationsAPI.delete(notificationId);
      setNotifications(prev => prev.filter(n => n.id !== notificationId));
      toast.success('Notification deleted');
    } catch (error) {
      toast.error('Failed to delete notification');
    }
  };

  const handleClearAll = async () => {
    if (!window.confirm('Are you sure you want to clear all notifications?')) return;
    try {
      await notificationsAPI.clearAll();
      setNotifications([]);
      toast.success('All notifications cleared');
    } catch (error) {
      toast.error('Failed to clear notifications');
    }
  };

  const handleSavePreferences = async () => {
    setSavingPrefs(true);
    try {
      await notificationsAPI.updatePreferences(preferences);
      toast.success('Preferences saved successfully');
    } catch (error) {
      toast.error('Failed to save preferences');
    } finally {
      setSavingPrefs(false);
    }
  };

  const handleSaveSmtp = async () => {
    setSavingSmtp(true);
    try {
      await notificationsAPI.updateSmtpSettings(smtpSettings);
      setSmtpConfigured(true);
      toast.success('SMTP settings saved successfully');
    } catch (error) {
      toast.error('Failed to save SMTP settings');
    } finally {
      setSavingSmtp(false);
    }
  };

  const handleTestSmtp = async () => {
    if (!testEmail) {
      toast.error('Please enter a test email address');
      return;
    }
    setTestingSmtp(true);
    try {
      await notificationsAPI.testSmtp(testEmail);
      toast.success('Test email sent! Please check your inbox.');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to send test email');
    } finally {
      setTestingSmtp(false);
    }
  };

  const unreadCount = notifications.filter(n => !n.is_read).length;

  const filteredNotifications = activeTab === 'unread'
    ? notifications.filter(n => !n.is_read)
    : notifications;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="notifications-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-slate-900" style={{ fontFamily: 'Outfit, sans-serif' }}>
            Notifications
          </h2>
          <p className="text-slate-500 mt-1">Alerts, updates, and notification settings</p>
        </div>
        {unreadCount > 0 && (
          <Badge className="bg-red-100 text-red-600">
            {unreadCount} unread
          </Badge>
        )}
      </div>

      <Tabs defaultValue="all" className="space-y-4">
        <TabsList>
          <TabsTrigger value="all" data-testid="tab-all-notifications">
            All Notifications
          </TabsTrigger>
          <TabsTrigger value="unread" data-testid="tab-unread-notifications">
            Unread ({unreadCount})
          </TabsTrigger>
          <TabsTrigger value="preferences" data-testid="tab-notification-preferences">
            Preferences
          </TabsTrigger>
          {isAdmin && (
            <TabsTrigger value="smtp" data-testid="tab-smtp-settings">
              Email Settings
            </TabsTrigger>
          )}
        </TabsList>

        {/* All Notifications Tab */}
        <TabsContent value="all" className="space-y-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between py-4">
              <CardTitle className="text-lg">All Notifications</CardTitle>
              <div className="flex gap-2">
                {unreadCount > 0 && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleMarkAllRead}
                    data-testid="mark-all-read-btn"
                  >
                    <CheckCheck className="w-4 h-4 mr-2" />
                    Mark All Read
                  </Button>
                )}
                {notifications.length > 0 && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleClearAll}
                    className="text-red-600 hover:text-red-700"
                    data-testid="clear-all-btn"
                  >
                    <Trash2 className="w-4 h-4 mr-2" />
                    Clear All
                  </Button>
                )}
              </div>
            </CardHeader>
            <CardContent className="p-0">
              {filteredNotifications.length === 0 ? (
                <div className="text-center py-16">
                  <Bell className="w-12 h-12 text-slate-300 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-slate-900">No notifications</h3>
                  <p className="text-slate-500 mt-1">You're all caught up!</p>
                </div>
              ) : (
                <div className="divide-y divide-slate-100">
                  {filteredNotifications.map((notification) => {
                    const Icon = notificationIcons[notification.type] || Bell;
                    const colorClass = notificationColors[notification.severity] || notificationColors.info;

                    return (
                      <div
                        key={notification.id}
                        className={`flex items-start gap-4 p-4 hover:bg-slate-50 transition-colors ${
                          !notification.is_read ? 'bg-indigo-50/50' : ''
                        }`}
                        data-testid={`notification-${notification.id}`}
                      >
                        <div className={`p-2 rounded-lg ${colorClass}`}>
                          <Icon className="w-5 h-5" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between gap-4">
                            <p className={`font-medium text-slate-900 ${!notification.is_read ? 'font-semibold' : ''}`}>
                              {notification.title}
                            </p>
                            <div className="flex items-center gap-2">
                              <Badge className={
                                notification.severity === 'warning' ? 'badge-warning' :
                                notification.severity === 'error' ? 'badge-error' :
                                notification.severity === 'success' ? 'badge-success' :
                                'badge-neutral'
                              }>
                                {notification.severity}
                              </Badge>
                              {!notification.is_read && (
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => handleMarkRead(notification.id)}
                                  title="Mark as read"
                                >
                                  <Check className="w-4 h-4" />
                                </Button>
                              )}
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleDelete(notification.id)}
                                className="text-red-500 hover:text-red-600"
                                title="Delete"
                              >
                                <Trash2 className="w-4 h-4" />
                              </Button>
                            </div>
                          </div>
                          <p className="text-sm text-slate-600 mt-1">{notification.message}</p>
                          <p className="text-xs text-slate-400 mt-2">
                            {new Date(notification.created_at).toLocaleString()}
                          </p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Unread Tab */}
        <TabsContent value="unread" className="space-y-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between py-4">
              <CardTitle className="text-lg">Unread Notifications</CardTitle>
              {unreadCount > 0 && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleMarkAllRead}
                >
                  <CheckCheck className="w-4 h-4 mr-2" />
                  Mark All Read
                </Button>
              )}
            </CardHeader>
            <CardContent className="p-0">
              {notifications.filter(n => !n.is_read).length === 0 ? (
                <div className="text-center py-16">
                  <CheckCheck className="w-12 h-12 text-emerald-300 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-slate-900">All caught up!</h3>
                  <p className="text-slate-500 mt-1">No unread notifications</p>
                </div>
              ) : (
                <div className="divide-y divide-slate-100">
                  {notifications.filter(n => !n.is_read).map((notification) => {
                    const Icon = notificationIcons[notification.type] || Bell;
                    const colorClass = notificationColors[notification.severity] || notificationColors.info;

                    return (
                      <div
                        key={notification.id}
                        className="flex items-start gap-4 p-4 hover:bg-slate-50 transition-colors bg-indigo-50/50"
                        data-testid={`unread-notification-${notification.id}`}
                      >
                        <div className={`p-2 rounded-lg ${colorClass}`}>
                          <Icon className="w-5 h-5" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between gap-4">
                            <p className="font-semibold text-slate-900">{notification.title}</p>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleMarkRead(notification.id)}
                            >
                              <Check className="w-4 h-4 mr-1" />
                              Mark Read
                            </Button>
                          </div>
                          <p className="text-sm text-slate-600 mt-1">{notification.message}</p>
                          <p className="text-xs text-slate-400 mt-2">
                            {new Date(notification.created_at).toLocaleString()}
                          </p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Preferences Tab */}
        <TabsContent value="preferences" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Notification Preferences</CardTitle>
              <CardDescription>
                Choose which notifications you want to receive
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Delivery Methods */}
              <div className="space-y-4">
                <h4 className="font-medium text-slate-900">Delivery Methods</h4>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <Label>In-App Notifications</Label>
                      <p className="text-sm text-slate-500">Show notifications in the app</p>
                    </div>
                    <Switch
                      checked={preferences.in_app_enabled}
                      onCheckedChange={(checked) => setPreferences(prev => ({ ...prev, in_app_enabled: checked }))}
                      data-testid="pref-in-app"
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <Label>Email Notifications</Label>
                      <p className="text-sm text-slate-500">Receive notifications via email</p>
                    </div>
                    <Switch
                      checked={preferences.email_enabled}
                      onCheckedChange={(checked) => setPreferences(prev => ({ ...prev, email_enabled: checked }))}
                      data-testid="pref-email"
                    />
                  </div>
                </div>
              </div>

              <Separator />

              {/* Notification Types */}
              <div className="space-y-4">
                <h4 className="font-medium text-slate-900">Notification Types</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                    <div className="flex items-center gap-3">
                      <Users className="w-5 h-5 text-indigo-600" />
                      <div>
                        <Label>Task Assignments</Label>
                        <p className="text-xs text-slate-500">New tasks assigned to you</p>
                      </div>
                    </div>
                    <Switch
                      checked={preferences.task_assignments}
                      onCheckedChange={(checked) => setPreferences(prev => ({ ...prev, task_assignments: checked }))}
                      data-testid="pref-task-assignments"
                    />
                  </div>
                  <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                    <div className="flex items-center gap-3">
                      <Users className="w-5 h-5 text-indigo-600" />
                      <div>
                        <Label>Task Updates</Label>
                        <p className="text-xs text-slate-500">Updates on your tasks</p>
                      </div>
                    </div>
                    <Switch
                      checked={preferences.task_updates}
                      onCheckedChange={(checked) => setPreferences(prev => ({ ...prev, task_updates: checked }))}
                      data-testid="pref-task-updates"
                    />
                  </div>
                  <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                    <div className="flex items-center gap-3">
                      <CreditCard className="w-5 h-5 text-emerald-600" />
                      <div>
                        <Label>Payroll Processed</Label>
                        <p className="text-xs text-slate-500">When payroll is processed</p>
                      </div>
                    </div>
                    <Switch
                      checked={preferences.payroll_processed}
                      onCheckedChange={(checked) => setPreferences(prev => ({ ...prev, payroll_processed: checked }))}
                      data-testid="pref-payroll"
                    />
                  </div>
                  <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                    <div className="flex items-center gap-3">
                      <CreditCard className="w-5 h-5 text-emerald-600" />
                      <div>
                        <Label>Payslip Ready</Label>
                        <p className="text-xs text-slate-500">When your payslip is ready</p>
                      </div>
                    </div>
                    <Switch
                      checked={preferences.payslip_ready}
                      onCheckedChange={(checked) => setPreferences(prev => ({ ...prev, payslip_ready: checked }))}
                      data-testid="pref-payslip"
                    />
                  </div>
                  <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                    <div className="flex items-center gap-3">
                      <Calendar className="w-5 h-5 text-blue-600" />
                      <div>
                        <Label>Leave Approvals</Label>
                        <p className="text-xs text-slate-500">Leave request approved</p>
                      </div>
                    </div>
                    <Switch
                      checked={preferences.leave_approvals}
                      onCheckedChange={(checked) => setPreferences(prev => ({ ...prev, leave_approvals: checked }))}
                      data-testid="pref-leave-approvals"
                    />
                  </div>
                  <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                    <div className="flex items-center gap-3">
                      <Calendar className="w-5 h-5 text-red-600" />
                      <div>
                        <Label>Leave Rejections</Label>
                        <p className="text-xs text-slate-500">Leave request rejected</p>
                      </div>
                    </div>
                    <Switch
                      checked={preferences.leave_rejections}
                      onCheckedChange={(checked) => setPreferences(prev => ({ ...prev, leave_rejections: checked }))}
                      data-testid="pref-leave-rejections"
                    />
                  </div>
                  <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                    <div className="flex items-center gap-3">
                      <Package className="w-5 h-5 text-amber-600" />
                      <div>
                        <Label>Low Inventory</Label>
                        <p className="text-xs text-slate-500">Stock below threshold</p>
                      </div>
                    </div>
                    <Switch
                      checked={preferences.low_inventory}
                      onCheckedChange={(checked) => setPreferences(prev => ({ ...prev, low_inventory: checked }))}
                      data-testid="pref-low-inventory"
                    />
                  </div>
                  <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                    <div className="flex items-center gap-3">
                      <ShoppingCart className="w-5 h-5 text-purple-600" />
                      <div>
                        <Label>New Orders</Label>
                        <p className="text-xs text-slate-500">New orders received</p>
                      </div>
                    </div>
                    <Switch
                      checked={preferences.new_orders}
                      onCheckedChange={(checked) => setPreferences(prev => ({ ...prev, new_orders: checked }))}
                      data-testid="pref-new-orders"
                    />
                  </div>
                </div>
              </div>

              <div className="flex justify-end pt-4">
                <Button onClick={handleSavePreferences} disabled={savingPrefs} data-testid="save-preferences-btn">
                  {savingPrefs ? (
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  ) : (
                    <Check className="w-4 h-4 mr-2" />
                  )}
                  Save Preferences
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* SMTP Settings Tab (Admin Only) */}
        {isAdmin && (
          <TabsContent value="smtp" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Mail className="w-5 h-5" />
                  Email (SMTP) Settings
                </CardTitle>
                <CardDescription>
                  Configure SMTP settings to enable email notifications
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="flex items-center justify-between p-4 bg-slate-50 rounded-lg">
                  <div className="space-y-0.5">
                    <Label>Enable Email Notifications</Label>
                    <p className="text-sm text-slate-500">Turn on email sending for the entire system</p>
                  </div>
                  <Switch
                    checked={smtpSettings.enabled}
                    onCheckedChange={(checked) => setSmtpSettings(prev => ({ ...prev, enabled: checked }))}
                    data-testid="smtp-enabled"
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="smtp_host">SMTP Host *</Label>
                    <Input
                      id="smtp_host"
                      placeholder="smtp.gmail.com"
                      value={smtpSettings.smtp_host}
                      onChange={(e) => setSmtpSettings(prev => ({ ...prev, smtp_host: e.target.value }))}
                      data-testid="smtp-host-input"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="smtp_port">SMTP Port *</Label>
                    <Input
                      id="smtp_port"
                      type="number"
                      placeholder="587"
                      value={smtpSettings.smtp_port}
                      onChange={(e) => setSmtpSettings(prev => ({ ...prev, smtp_port: parseInt(e.target.value) || 587 }))}
                      data-testid="smtp-port-input"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="smtp_username">SMTP Username *</Label>
                    <Input
                      id="smtp_username"
                      placeholder="your-email@gmail.com"
                      value={smtpSettings.smtp_username}
                      onChange={(e) => setSmtpSettings(prev => ({ ...prev, smtp_username: e.target.value }))}
                      data-testid="smtp-username-input"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="smtp_password">SMTP Password *</Label>
                    <div className="relative">
                      <Input
                        id="smtp_password"
                        type={showPassword ? 'text' : 'password'}
                        placeholder={smtpConfigured ? '••••••••' : 'App password or SMTP password'}
                        value={smtpSettings.smtp_password}
                        onChange={(e) => setSmtpSettings(prev => ({ ...prev, smtp_password: e.target.value }))}
                        data-testid="smtp-password-input"
                      />
                      <button
                        type="button"
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-700"
                        onClick={() => setShowPassword(!showPassword)}
                      >
                        {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="from_email">From Email *</Label>
                    <Input
                      id="from_email"
                      type="email"
                      placeholder="noreply@yourcompany.com"
                      value={smtpSettings.from_email}
                      onChange={(e) => setSmtpSettings(prev => ({ ...prev, from_email: e.target.value }))}
                      data-testid="smtp-from-email-input"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="from_name">From Name</Label>
                    <Input
                      id="from_name"
                      placeholder="ERP System"
                      value={smtpSettings.from_name}
                      onChange={(e) => setSmtpSettings(prev => ({ ...prev, from_name: e.target.value }))}
                      data-testid="smtp-from-name-input"
                    />
                  </div>
                </div>

                <div className="flex items-center justify-between p-4 bg-slate-50 rounded-lg">
                  <div className="space-y-0.5">
                    <Label>Use TLS</Label>
                    <p className="text-sm text-slate-500">Use STARTTLS for secure connection (recommended)</p>
                  </div>
                  <Switch
                    checked={smtpSettings.use_tls}
                    onCheckedChange={(checked) => setSmtpSettings(prev => ({ ...prev, use_tls: checked }))}
                    data-testid="smtp-tls"
                  />
                </div>

                <Separator />

                {/* Test Email */}
                <div className="space-y-4">
                  <h4 className="font-medium text-slate-900">Test Configuration</h4>
                  <div className="flex gap-4">
                    <div className="flex-1">
                      <Input
                        placeholder="Enter email to send test"
                        value={testEmail}
                        onChange={(e) => setTestEmail(e.target.value)}
                        data-testid="test-email-input"
                      />
                    </div>
                    <Button
                      variant="outline"
                      onClick={handleTestSmtp}
                      disabled={testingSmtp || !smtpConfigured}
                      data-testid="test-smtp-btn"
                    >
                      {testingSmtp ? (
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      ) : (
                        <Send className="w-4 h-4 mr-2" />
                      )}
                      Send Test Email
                    </Button>
                  </div>
                  {!smtpConfigured && (
                    <p className="text-sm text-amber-600">
                      Save SMTP settings first before testing
                    </p>
                  )}
                </div>

                <div className="flex justify-end pt-4">
                  <Button onClick={handleSaveSmtp} disabled={savingSmtp} data-testid="save-smtp-btn">
                    {savingSmtp ? (
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    ) : (
                      <Check className="w-4 h-4 mr-2" />
                    )}
                    Save SMTP Settings
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* SMTP Help Card */}
            <Card>
              <CardHeader>
                <CardTitle className="text-sm">Common SMTP Settings</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                  <div className="p-3 bg-slate-50 rounded-lg">
                    <p className="font-medium">Gmail</p>
                    <p className="text-slate-500">Host: smtp.gmail.com</p>
                    <p className="text-slate-500">Port: 587 (TLS)</p>
                    <p className="text-xs text-amber-600 mt-1">Use App Password</p>
                  </div>
                  <div className="p-3 bg-slate-50 rounded-lg">
                    <p className="font-medium">Outlook/Office 365</p>
                    <p className="text-slate-500">Host: smtp.office365.com</p>
                    <p className="text-slate-500">Port: 587 (TLS)</p>
                  </div>
                  <div className="p-3 bg-slate-50 rounded-lg">
                    <p className="font-medium">SendGrid</p>
                    <p className="text-slate-500">Host: smtp.sendgrid.net</p>
                    <p className="text-slate-500">Port: 587 (TLS)</p>
                    <p className="text-xs text-slate-500 mt-1">Username: apikey</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        )}
      </Tabs>
    </div>
  );
};

export default Notifications;
