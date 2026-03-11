import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { notificationsAPI } from '../lib/api';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import {
  Bell,
  Check,
  CheckCheck,
  X,
  AlertTriangle,
  Package,
  CreditCard,
  ShoppingCart,
  Users,
  Calendar,
  Settings,
  Loader2
} from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from './ui/dropdown-menu';
import { ScrollArea } from './ui/scroll-area';
import { toast } from 'sonner';

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

const severityColors = {
  info: 'bg-blue-100 text-blue-600',
  warning: 'bg-amber-100 text-amber-600',
  error: 'bg-red-100 text-red-600',
  success: 'bg-emerald-100 text-emerald-600',
};

export const NotificationBell = () => {
  const navigate = useNavigate();
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);

  const fetchNotifications = useCallback(async () => {
    try {
      const response = await notificationsAPI.getAll({ limit: 10 });
      setNotifications(response.data.notifications || []);
      setUnreadCount(response.data.unread_count || 0);
    } catch (error) {
      console.error('Failed to fetch notifications:', error);
    }
  }, []);

  const fetchUnreadCount = useCallback(async () => {
    try {
      const response = await notificationsAPI.getUnreadCount();
      setUnreadCount(response.data.unread_count || 0);
    } catch (error) {
      console.error('Failed to fetch unread count:', error);
    }
  }, []);

  // WebSocket connection for real-time updates
  const connectWebSocket = useCallback(() => {
    // Prevent multiple connections
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      console.log('WebSocket already connected, skipping');
      return;
    }
    
    // Close existing connection if in connecting state
    if (wsRef.current && wsRef.current.readyState === WebSocket.CONNECTING) {
      console.log('WebSocket connecting, skipping new connection');
      return;
    }

    const token = localStorage.getItem('erp_token');
    if (!token) return;

    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const backendUrl = process.env.REACT_APP_BACKEND_URL;
    
    // Extract host from backend URL
    let wsHost;
    try {
      const url = new URL(backendUrl);
      wsHost = url.host;
    } catch {
      wsHost = window.location.host;
    }

    const wsUrl = `${wsProtocol}//${wsHost}/api/notifications/ws/${token}`;

    try {
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        console.log('WebSocket connected for notifications');
      };

      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'new_notification') {
            // Add to notifications list (prevent duplicates by checking id)
            setNotifications(prev => {
              const exists = prev.some(n => n.id === data.notification.id);
              if (exists) return prev;
              return [data.notification, ...prev.slice(0, 9)];
            });
            setUnreadCount(prev => prev + 1);
            
            // Show toast notification
            toast(data.notification.title, {
              description: data.notification.message,
              action: {
                label: 'View',
                onClick: () => navigate('/notifications'),
              },
            });
          }
        } catch (e) {
          console.error('Failed to parse WebSocket message:', e);
        }
      };

      wsRef.current.onclose = (event) => {
        console.log('WebSocket closed:', event.code);
        // Only reconnect if not intentionally closed (code 1000)
        if (event.code !== 1000) {
          reconnectTimeoutRef.current = setTimeout(connectWebSocket, 5000);
        }
      };

      wsRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
    }
  }, [navigate]);

  useEffect(() => {
    fetchNotifications();
    
    // Small delay to prevent race conditions with React strict mode
    const connectTimeout = setTimeout(() => {
      connectWebSocket();
    }, 100);

    // Periodic refresh as fallback
    const interval = setInterval(fetchUnreadCount, 30000);

    return () => {
      clearTimeout(connectTimeout);
      clearInterval(interval);
      if (wsRef.current) {
        wsRef.current.close(1000, 'Component unmounting');
        wsRef.current = null;
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, []);

  const handleMarkRead = async (notificationId, e) => {
    e.stopPropagation();
    try {
      await notificationsAPI.markRead(notificationId);
      setNotifications(prev =>
        prev.map(n => n.id === notificationId ? { ...n, is_read: true } : n)
      );
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch (error) {
      toast.error('Failed to mark notification as read');
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await notificationsAPI.markAllRead();
      setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
      setUnreadCount(0);
      toast.success('All notifications marked as read');
    } catch (error) {
      toast.error('Failed to mark all as read');
    }
  };

  const formatTimeAgo = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  return (
    <DropdownMenu open={open} onOpenChange={setOpen}>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className="relative"
          data-testid="notification-bell-btn"
        >
          <Bell className="w-5 h-5 text-slate-600" />
          {unreadCount > 0 && (
            <Badge
              className="absolute -top-1 -right-1 h-5 w-5 flex items-center justify-center p-0 bg-red-500 text-white text-xs animate-pulse"
              data-testid="notification-badge"
            >
              {unreadCount > 9 ? '9+' : unreadCount}
            </Badge>
          )}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-80" data-testid="notification-dropdown">
        <DropdownMenuLabel className="flex items-center justify-between">
          <span>Notifications</span>
          {unreadCount > 0 && (
            <Button
              variant="ghost"
              size="sm"
              className="h-auto p-1 text-xs text-indigo-600 hover:text-indigo-700"
              onClick={handleMarkAllRead}
              data-testid="mark-all-read-btn"
            >
              <CheckCheck className="w-3 h-3 mr-1" />
              Mark all read
            </Button>
          )}
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        
        <ScrollArea className="h-[300px]">
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-6 h-6 animate-spin text-indigo-600" />
            </div>
          ) : notifications.length === 0 ? (
            <div className="text-center py-8 px-4">
              <Bell className="w-10 h-10 text-slate-300 mx-auto mb-2" />
              <p className="text-sm text-slate-500">No notifications</p>
              <p className="text-xs text-slate-400 mt-1">You're all caught up!</p>
            </div>
          ) : (
            notifications.map((notification) => {
              const Icon = notificationIcons[notification.type] || Bell;
              const colorClass = severityColors[notification.severity] || severityColors.info;

              return (
                <div
                  key={notification.id}
                  className={`flex items-start gap-3 p-3 hover:bg-slate-50 cursor-pointer transition-colors border-b border-slate-100 last:border-0 ${
                    !notification.is_read ? 'bg-indigo-50/50' : ''
                  }`}
                  onClick={() => {
                    setOpen(false);
                    navigate('/notifications');
                  }}
                  data-testid={`notification-item-${notification.id}`}
                >
                  <div className={`p-1.5 rounded-lg ${colorClass} flex-shrink-0`}>
                    <Icon className="w-4 h-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-2">
                      <p className={`text-sm ${!notification.is_read ? 'font-medium' : ''} text-slate-900 line-clamp-1`}>
                        {notification.title}
                      </p>
                      {!notification.is_read && (
                        <button
                          onClick={(e) => handleMarkRead(notification.id, e)}
                          className="flex-shrink-0 p-1 hover:bg-slate-200 rounded"
                          title="Mark as read"
                        >
                          <Check className="w-3 h-3 text-slate-500" />
                        </button>
                      )}
                    </div>
                    <p className="text-xs text-slate-500 line-clamp-2 mt-0.5">
                      {notification.message}
                    </p>
                    <p className="text-xs text-slate-400 mt-1">
                      {formatTimeAgo(notification.created_at)}
                    </p>
                  </div>
                </div>
              );
            })
          )}
        </ScrollArea>

        <DropdownMenuSeparator />
        <DropdownMenuItem
          className="text-center justify-center text-indigo-600 cursor-pointer"
          onClick={() => {
            setOpen(false);
            navigate('/notifications');
          }}
          data-testid="view-all-notifications-btn"
        >
          View all notifications
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
};

export default NotificationBell;
