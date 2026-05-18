/**
 * Notification Detail Page
 */

import {
  ArrowLeft,
  Bell,
  Mail,
  MessageSquare,
  Smartphone,
  Clock,
  User,
  FileText,
  ExternalLink,
  Trash2,
  Check,
} from 'lucide-react';
import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { useToast } from '@/hooks/use-toast';
import { notificationApi } from '@/services/notificationApi';
import type { Notification } from '@/types/notification';

const CHANNEL_ICONS: Record<string, React.ReactNode> = {
  email: <Mail className="h-4 w-4" />,
  sms: <MessageSquare className="h-4 w-4" />,
  push: <Smartphone className="h-4 w-4" />,
  in_app: <Bell className="h-4 w-4" />,
  whatsapp: <MessageSquare className="h-4 w-4" />,
};

const PRIORITY_COLORS: Record<string, string> = {
  low: 'bg-gray-100 text-gray-700',
  medium: 'bg-blue-100 text-blue-700',
  high: 'bg-orange-100 text-orange-700',
  urgent: 'bg-red-100 text-red-700',
};

const STATUS_COLORS: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
  pending: 'outline',
  queued: 'secondary',
  sent: 'default',
  delivered: 'default',
  read: 'default',
  failed: 'destructive',
  cancelled: 'outline',
};

export default function NotificationDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();

  const [notification, setNotification] = useState<Notification | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (id) {
      loadNotification();
    }
  }, [id]);

  const loadNotification = async () => {
    try {
      setLoading(true);
      const data = await notificationApi.getNotification(id!);
      setNotification(data);

      // Mark as read if not already
      if (!data.read_at) {
        await notificationApi.markSingleAsRead(id!);
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load notification',
        variant: 'destructive',
      });
      navigate('/admin/notifications');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!notification) return;

    try {
      await notificationApi.deleteNotification(notification.id);
      toast({ title: 'Notification deleted' });
      navigate('/admin/notifications');
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to delete notification',
        variant: 'destructive',
      });
    }
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleString();
  };

  if (loading) {
    return (
      <div className="container mx-auto py-6">
        <div className="text-center py-8">Loading...</div>
      </div>
    );
  }

  if (!notification) {
    return (
      <div className="container mx-auto py-6">
        <div className="text-center py-8">Notification not found</div>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" onClick={() => navigate('/admin/notifications')}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back
        </Button>
        <div className="flex-1" />
        <Button variant="destructive" onClick={handleDelete}>
          <Trash2 className="h-4 w-4 mr-2" />
          Delete
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <div className="flex items-start justify-between">
                <div>
                  <CardTitle className="text-xl">{notification.title}</CardTitle>
                  <CardDescription className="mt-2 flex items-center gap-2">
                    <Clock className="h-4 w-4" />
                    {formatDate(notification.created_at)}
                  </CardDescription>
                </div>
                <div className="flex gap-2">
                  <Badge variant={STATUS_COLORS[notification.status]}>
                    {notification.status}
                  </Badge>
                  <Badge className={PRIORITY_COLORS[notification.priority]}>
                    {notification.priority}
                  </Badge>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <h4 className="font-medium mb-2">Message</h4>
                <p className="text-muted-foreground whitespace-pre-wrap">
                  {notification.message}
                </p>
              </div>

              {notification.html_content && (
                <div>
                  <h4 className="font-medium mb-2">HTML Content</h4>
                  <div
                    className="p-4 border rounded-lg bg-white"
                    dangerouslySetInnerHTML={{ __html: notification.html_content }}
                  />
                </div>
              )}

              {notification.action_url && (
                <div className="pt-4">
                  <Button asChild>
                    <a href={notification.action_url} target="_blank" rel="noopener noreferrer">
                      <ExternalLink className="h-4 w-4 mr-2" />
                      {notification.action_label || 'Open Link'}
                    </a>
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>

          {notification.metadata && Object.keys(notification.metadata).length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Additional Data</CardTitle>
              </CardHeader>
              <CardContent>
                <pre className="text-sm bg-muted p-4 rounded-lg overflow-auto">
                  {JSON.stringify(notification.metadata, null, 2)}
                </pre>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-sm text-muted-foreground">Category</label>
                <p className="font-medium capitalize">{notification.category}</p>
              </div>

              <Separator />

              <div>
                <label className="text-sm text-muted-foreground">Channels</label>
                <div className="flex gap-2 mt-1">
                  {notification.channels.map((channel) => (
                    <Badge key={channel} variant="outline" className="flex items-center gap-1">
                      {CHANNEL_ICONS[channel]}
                      {channel}
                    </Badge>
                  ))}
                </div>
              </div>

              <Separator />

              <div>
                <label className="text-sm text-muted-foreground">Delivery Status</label>
                <div className="space-y-2 mt-2">
                  <div className="flex items-center justify-between text-sm">
                    <span>Sent</span>
                    <span>{notification.sent_at ? formatDate(notification.sent_at) : 'Pending'}</span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span>Delivered</span>
                    <span>{notification.delivered_at ? formatDate(notification.delivered_at) : '-'}</span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span>Read</span>
                    <span>{notification.read_at ? formatDate(notification.read_at) : '-'}</span>
                  </div>
                </div>
              </div>

              {notification.entity_type && (
                <>
                  <Separator />
                  <div>
                    <label className="text-sm text-muted-foreground">Related Entity</label>
                    <div className="flex items-center gap-2 mt-1">
                      <FileText className="h-4 w-4" />
                      <span>{notification.entity_type}</span>
                      {notification.entity_reference && (
                        <Badge variant="outline">{notification.entity_reference}</Badge>
                      )}
                    </div>
                  </div>
                </>
              )}

              {notification.scheduled_at && (
                <>
                  <Separator />
                  <div>
                    <label className="text-sm text-muted-foreground">Scheduled</label>
                    <p>{formatDate(notification.scheduled_at)}</p>
                  </div>
                </>
              )}

              {notification.expires_at && (
                <>
                  <Separator />
                  <div>
                    <label className="text-sm text-muted-foreground">Expires</label>
                    <p>{formatDate(notification.expires_at)}</p>
                  </div>
                </>
              )}

              <Separator />

              <div>
                <label className="text-sm text-muted-foreground">Retry Info</label>
                <p className="text-sm">
                  Attempts: {notification.retry_count} / {notification.max_retries}
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
