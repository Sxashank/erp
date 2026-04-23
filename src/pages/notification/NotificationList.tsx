/**
 * Notification List Page
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Bell,
  BellOff,
  Check,
  CheckCheck,
  Filter,
  Trash2,
  Settings,
  FileText,
  AlertCircle,
  Clock,
  RefreshCw,
} from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { PageHeader } from '@/components/common/PageHeader';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from '@/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { useToast } from '@/hooks/use-toast';
import { notificationApi } from '@/services/notificationApi';
import { Notification, NotificationCategory } from '@/types/notification';

const CATEGORY_OPTIONS: { value: NotificationCategory | 'all'; label: string }[] = [
  { value: 'all', label: 'All Categories' },
  { value: 'system', label: 'System' },
  { value: 'workflow', label: 'Workflow' },
  { value: 'loan', label: 'Loan' },
  { value: 'payment', label: 'Payment' },
  { value: 'collection', label: 'Collection' },
  { value: 'reminder', label: 'Reminder' },
  { value: 'alert', label: 'Alert' },
  { value: 'announcement', label: 'Announcement' },
];

const PRIORITY_COLORS: Record<string, string> = {
  low: 'bg-gray-100 text-gray-700',
  medium: 'bg-blue-100 text-blue-700',
  high: 'bg-orange-100 text-orange-700',
  urgent: 'bg-red-100 text-red-700',
};

const CATEGORY_COLORS: Record<string, string> = {
  system: 'bg-slate-100 text-slate-700',
  workflow: 'bg-purple-100 text-purple-700',
  loan: 'bg-green-100 text-green-700',
  payment: 'bg-emerald-100 text-emerald-700',
  collection: 'bg-orange-100 text-orange-700',
  reminder: 'bg-yellow-100 text-yellow-700',
  alert: 'bg-red-100 text-red-700',
  announcement: 'bg-blue-100 text-blue-700',
  marketing: 'bg-pink-100 text-pink-700',
};

export default function NotificationList() {
  const navigate = useNavigate();
  const { toast } = useToast();

  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [unreadCount, setUnreadCount] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);

  const [category, setCategory] = useState<NotificationCategory | 'all'>('all');
  const [unreadOnly, setUnreadOnly] = useState(false);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);

  useEffect(() => {
    loadNotifications();
  }, [page, category, unreadOnly]);

  const loadNotifications = async () => {
    try {
      setLoading(true);
      const response = await notificationApi.getNotifications({
        category: category === 'all' ? undefined : category,
        unread_only: unreadOnly,
        page,
        page_size: pageSize,
      });
      setNotifications(response.items);
      setTotal(response.total);
      setUnreadCount(response.unread_count);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load notifications',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleMarkAsRead = async (ids?: string[]) => {
    try {
      const toMark = ids || selectedIds;
      if (toMark.length === 0) return;

      await notificationApi.markAsRead({ notification_ids: toMark });
      toast({ title: 'Notifications marked as read' });
      loadNotifications();
      setSelectedIds([]);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to mark notifications as read',
        variant: 'destructive',
      });
    }
  };

  const handleMarkAllAsRead = async () => {
    try {
      const result = await notificationApi.markAsRead({ mark_all: true });
      toast({ title: `${result.marked_read} notifications marked as read` });
      loadNotifications();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to mark all as read',
        variant: 'destructive',
      });
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await notificationApi.deleteNotification(id);
      toast({ title: 'Notification deleted' });
      loadNotifications();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to delete notification',
        variant: 'destructive',
      });
    }
  };

  const toggleSelection = (id: string) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]
    );
  };

  const selectAll = () => {
    if (selectedIds.length === notifications.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(notifications.map((n) => n.id));
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const days = Math.floor(hours / 24);

    if (hours < 1) return 'Just now';
    if (hours < 24) return `${hours}h ago`;
    if (days < 7) return `${days}d ago`;
    return date.toLocaleDateString();
  };

  const renderNotification = (notification: Notification) => {
    const isRead = !!notification.read_at;
    return (
      <div
        key={notification.id}
        className={`flex items-start gap-4 p-4 border-b hover:bg-muted/50 cursor-pointer ${
          !isRead ? 'bg-blue-50/50' : ''
        }`}
      >
        <Checkbox
          checked={selectedIds.includes(notification.id)}
          onCheckedChange={() => toggleSelection(notification.id)}
          onClick={(e) => e.stopPropagation()}
        />
        <div
          className="flex-1 min-w-0"
          onClick={() => navigate(`/admin/notifications/${notification.id}`)}
        >
          <div className="flex items-center gap-2 mb-1">
            {!isRead && <div className="w-2 h-2 bg-blue-500 rounded-full" />}
            <span className={`font-medium ${!isRead ? 'text-foreground' : 'text-muted-foreground'}`}>
              {notification.title}
            </span>
            <Badge className={CATEGORY_COLORS[notification.category]} variant="secondary">
              {notification.category}
            </Badge>
            <Badge className={PRIORITY_COLORS[notification.priority]} variant="secondary">
              {notification.priority}
            </Badge>
          </div>
          <p className="text-sm text-muted-foreground line-clamp-2">
            {notification.message}
          </p>
          <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
            <span className="flex items-center gap-1">
              <Clock className="h-3 w-3" />
              {formatDate(notification.created_at)}
            </span>
            {notification.entity_type && (
              <span className="flex items-center gap-1">
                <FileText className="h-3 w-3" />
                {notification.entity_type}: {notification.entity_reference}
              </span>
            )}
          </div>
        </div>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="sm">
              <AlertCircle className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            {!isRead && (
              <DropdownMenuItem onClick={() => handleMarkAsRead([notification.id])}>
                <Check className="mr-2 h-4 w-4" />
                Mark as read
              </DropdownMenuItem>
            )}
            <DropdownMenuItem onClick={() => navigate(`/admin/notifications/${notification.id}`)}>
              <FileText className="mr-2 h-4 w-4" />
              View details
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              className="text-destructive"
              onClick={() => handleDelete(notification.id)}
            >
              <Trash2 className="mr-2 h-4 w-4" />
              Delete
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    );
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      <PageHeader
        title="Notifications"
        subtitle={
          unreadCount > 0 ? `${unreadCount} unread notifications` : 'All caught up!'
        }
        actions={
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => navigate('/admin/notifications/settings')}>
              <Settings className="mr-2 h-4 w-4" />
              Preferences
            </Button>
            <Button variant="outline" onClick={() => navigate('/admin/notifications/templates')}>
              <FileText className="mr-2 h-4 w-4" />
              Templates
            </Button>
          </div>
        }
      />

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Select
                value={category}
                onValueChange={(v) => setCategory(v as NotificationCategory | 'all')}
              >
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="Category" />
                </SelectTrigger>
                <SelectContent>
                  {CATEGORY_OPTIONS.map((opt) => (
                    <SelectItem key={opt.value} value={opt.value}>
                      {opt.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <label className="flex items-center gap-2 cursor-pointer">
                <Checkbox
                  checked={unreadOnly}
                  onCheckedChange={(checked) => setUnreadOnly(checked === true)}
                />
                <span className="text-sm">Unread only</span>
              </label>
            </div>
            <div className="flex items-center gap-2">
              {selectedIds.length > 0 && (
                <Button variant="outline" size="sm" onClick={() => handleMarkAsRead()}>
                  <Check className="mr-2 h-4 w-4" />
                  Mark selected as read
                </Button>
              )}
              <Button variant="outline" size="sm" onClick={handleMarkAllAsRead}>
                <CheckCheck className="mr-2 h-4 w-4" />
                Mark all as read
              </Button>
              <Button variant="ghost" size="sm" onClick={loadNotifications}>
                <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {loading ? (
            <div className="text-center py-8">Loading...</div>
          ) : notifications.length === 0 ? (
            <div className="text-center py-12">
              <BellOff className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
              <p className="text-muted-foreground">No notifications</p>
            </div>
          ) : (
            <div>
              <div className="flex items-center gap-2 px-4 py-2 border-b bg-muted/50">
                <Checkbox
                  checked={selectedIds.length === notifications.length}
                  onCheckedChange={selectAll}
                />
                <span className="text-sm text-muted-foreground">
                  {selectedIds.length > 0
                    ? `${selectedIds.length} selected`
                    : 'Select all'}
                </span>
              </div>
              {notifications.map(renderNotification)}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Pagination */}
      {total > pageSize && (
        <div className="flex justify-center gap-2">
          <Button
            variant="outline"
            disabled={page === 1}
            onClick={() => setPage((p) => p - 1)}
          >
            Previous
          </Button>
          <span className="flex items-center px-4">
            Page {page} of {Math.ceil(total / pageSize)}
          </span>
          <Button
            variant="outline"
            disabled={page >= Math.ceil(total / pageSize)}
            onClick={() => setPage((p) => p + 1)}
          >
            Next
          </Button>
        </div>
      )}
    </div>
  );
}
