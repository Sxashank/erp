/**
 * Notification Log Page - View delivery logs for notifications
 */

import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  ArrowLeft,
  Search,
  RefreshCw,
  Mail,
  MessageSquare,
  Smartphone,
  Bell,
  CheckCircle,
  XCircle,
  Clock,
  AlertCircle,
} from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
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
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useToast } from '@/hooks/use-toast';
import api from '@/services/api';
import { NotificationLog, NotificationChannel, NotificationStatus } from '@/types/notification';

const CHANNEL_ICONS: Record<string, React.ReactNode> = {
  email: <Mail className="h-4 w-4" />,
  sms: <MessageSquare className="h-4 w-4" />,
  push: <Smartphone className="h-4 w-4" />,
  in_app: <Bell className="h-4 w-4" />,
  whatsapp: <MessageSquare className="h-4 w-4 text-green-500" />,
};

const STATUS_ICONS: Record<string, React.ReactNode> = {
  pending: <Clock className="h-4 w-4 text-yellow-500" />,
  queued: <Clock className="h-4 w-4 text-blue-500" />,
  sent: <CheckCircle className="h-4 w-4 text-blue-500" />,
  delivered: <CheckCircle className="h-4 w-4 text-green-500" />,
  read: <CheckCircle className="h-4 w-4 text-green-600" />,
  failed: <XCircle className="h-4 w-4 text-red-500" />,
  cancelled: <XCircle className="h-4 w-4 text-gray-500" />,
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

interface LogEntry extends NotificationLog {
  notification_title?: string;
}

export default function NotificationLogPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { toast } = useToast();

  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(50);

  const [channel, setChannel] = useState<NotificationChannel | 'all'>('all');
  const [status, setStatus] = useState<NotificationStatus | 'all'>('all');

  const notificationId = searchParams.get('notification_id');

  useEffect(() => {
    loadLogs();
  }, [page, channel, status, notificationId]);

  const loadLogs = async () => {
    try {
      setLoading(true);
      // This would be a dedicated endpoint in production
      // For now, simulating with placeholder data
      const mockLogs: LogEntry[] = [
        {
          id: '1',
          notification_id: 'notif-1',
          notification_title: 'Loan Approved',
          channel: 'email',
          status: 'delivered',
          attempt_number: 1,
          attempted_at: new Date().toISOString(),
          provider: 'SMTP',
          response_code: '250',
          response_message: 'Message accepted',
        },
        {
          id: '2',
          notification_id: 'notif-2',
          notification_title: 'Payment Due Reminder',
          channel: 'sms',
          status: 'sent',
          attempt_number: 1,
          attempted_at: new Date(Date.now() - 3600000).toISOString(),
          provider: 'MSG91',
          provider_message_id: 'msg_12345',
        },
        {
          id: '3',
          notification_id: 'notif-3',
          notification_title: 'System Maintenance',
          channel: 'push',
          status: 'failed',
          attempt_number: 2,
          attempted_at: new Date(Date.now() - 7200000).toISOString(),
          provider: 'FCM',
          response_message: 'Invalid device token',
        },
      ];

      setLogs(mockLogs);
      setTotal(mockLogs.length);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load notification logs',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      <PageHeader
        title="Notification Logs"
        subtitle="View delivery history and troubleshoot notification issues"
        breadcrumbs={[
          { label: 'Notifications', to: '/admin/notifications' },
          { label: 'Logs' },
        ]}
        actions={
          <Button variant="outline" onClick={loadLogs}>
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        }
      />

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Attempts
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{total}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-green-600">
              Delivered
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {logs.filter((l) => l.status === 'delivered').length}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-blue-600">
              Sent
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">
              {logs.filter((l) => l.status === 'sent').length}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-yellow-600">
              Pending
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600">
              {logs.filter((l) => l.status === 'pending' || l.status === 'queued').length}
            </div>
          </CardContent>
        </Card>
        <Card className="border-red-200">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-destructive">
              Failed
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-destructive">
              {logs.filter((l) => l.status === 'failed').length}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-4">
            <Select value={channel} onValueChange={(v) => setChannel(v as NotificationChannel | 'all')}>
              <SelectTrigger className="w-[150px]">
                <SelectValue placeholder="Channel" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Channels</SelectItem>
                <SelectItem value="email">Email</SelectItem>
                <SelectItem value="sms">SMS</SelectItem>
                <SelectItem value="push">Push</SelectItem>
                <SelectItem value="in_app">In-App</SelectItem>
                <SelectItem value="whatsapp">WhatsApp</SelectItem>
              </SelectContent>
            </Select>

            <Select value={status} onValueChange={(v) => setStatus(v as NotificationStatus | 'all')}>
              <SelectTrigger className="w-[150px]">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="pending">Pending</SelectItem>
                <SelectItem value="queued">Queued</SelectItem>
                <SelectItem value="sent">Sent</SelectItem>
                <SelectItem value="delivered">Delivered</SelectItem>
                <SelectItem value="failed">Failed</SelectItem>
                <SelectItem value="cancelled">Cancelled</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8">Loading...</div>
          ) : logs.length === 0 ? (
            <div className="text-center py-12">
              <AlertCircle className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
              <p className="text-muted-foreground">No logs found</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Time</TableHead>
                  <TableHead>Notification</TableHead>
                  <TableHead>Channel</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Attempt</TableHead>
                  <TableHead>Provider</TableHead>
                  <TableHead>Response</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {logs.map((log) => (
                  <TableRow key={log.id}>
                    <TableCell className="text-sm">
                      {formatDate(log.attempted_at)}
                    </TableCell>
                    <TableCell>
                      <button
                        className="text-left hover:underline"
                        onClick={() => navigate(`/admin/notifications/${log.notification_id}`)}
                      >
                        {log.notification_title || log.notification_id.substring(0, 8)}
                      </button>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        {CHANNEL_ICONS[log.channel]}
                        <span className="capitalize">{log.channel.replace('_', ' ')}</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        {STATUS_ICONS[log.status]}
                        <Badge variant={STATUS_COLORS[log.status]}>
                          {log.status}
                        </Badge>
                      </div>
                    </TableCell>
                    <TableCell>{log.attempt_number}</TableCell>
                    <TableCell>
                      <span className="text-sm text-muted-foreground">
                        {log.provider || '-'}
                      </span>
                    </TableCell>
                    <TableCell>
                      <div className="max-w-xs">
                        {log.response_code && (
                          <Badge variant="outline" className="mr-2">
                            {log.response_code}
                          </Badge>
                        )}
                        <span className="text-sm text-muted-foreground truncate">
                          {log.response_message || log.provider_message_id || '-'}
                        </span>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
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
