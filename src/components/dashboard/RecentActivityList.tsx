import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Activity,
  Receipt,
  FileText,
  CreditCard,
  Banknote,
  ArrowRight,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { formatDistanceToNow } from 'date-fns';

interface ActivityItem {
  id: string;
  type: string;
  number: string;
  description: string;
  amount: number;
  partyName?: string;
  status: string;
  createdAt: string;
  createdByName?: string;
}

interface RecentActivityProps {
  activities: ActivityItem[];
}

const formatCurrency = (amount: number) => {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount);
};

const getActivityIcon = (type: string) => {
  switch (type) {
    case 'PAYMENT':
      return <CreditCard className="h-4 w-4 text-red-500" />;
    case 'RECEIPT':
      return <Banknote className="h-4 w-4 text-green-500" />;
    case 'INVOICE':
      return <Receipt className="h-4 w-4 text-blue-500" />;
    case 'BILL':
      return <FileText className="h-4 w-4 text-orange-500" />;
    default:
      return <Activity className="h-4 w-4 text-gray-500" />;
  }
};

const getStatusBadge = (status: string) => {
  const statusStyles: Record<string, string> = {
    DRAFT: 'bg-gray-100 text-gray-700',
    SUBMITTED: 'bg-blue-100 text-blue-700',
    APPROVED: 'bg-green-100 text-green-700',
    POSTED: 'bg-green-100 text-green-700',
    CANCELLED: 'bg-red-100 text-red-700',
  };

  return (
    <Badge className={statusStyles[status] || 'bg-gray-100 text-gray-700'} variant="secondary">
      {status}
    </Badge>
  );
};

const getActivityLink = (type: string, id: string) => {
  switch (type) {
    case 'PAYMENT':
    case 'RECEIPT':
      return `/admin/ap-ar/payments/${id}`;
    case 'INVOICE':
      return `/admin/ap-ar/sales-invoices/${id}`;
    case 'BILL':
      return `/admin/ap-ar/purchase-bills/${id}`;
    default:
      return '#';
  }
};

export function RecentActivityList({ activities }: RecentActivityProps) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-semibold flex items-center gap-2">
            <Activity className="h-5 w-5 text-indigo-500" />
            Recent Activity
          </CardTitle>
        </div>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-[400px] pr-4">
          {activities.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No recent activity
            </div>
          ) : (
            <div className="space-y-4">
              {activities.map((activity) => (
                <Link
                  key={activity.id}
                  to={getActivityLink(activity.type, activity.id)}
                  className="block"
                >
                  <div className="flex items-start gap-3 p-3 rounded-lg border hover:bg-muted/50 transition-colors">
                    <div className="mt-1">
                      {getActivityIcon(activity.type)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-2">
                        <span className="font-medium text-sm truncate">
                          {activity.number}
                        </span>
                        {getStatusBadge(activity.status)}
                      </div>
                      <p className="text-sm text-muted-foreground truncate">
                        {activity.partyName || activity.description}
                      </p>
                      <div className="flex items-center justify-between mt-1">
                        <span className="text-sm font-medium">
                          {formatCurrency(activity.amount)}
                        </span>
                        <span className="text-xs text-muted-foreground">
                          {formatDistanceToNow(new Date(activity.createdAt), {
                            addSuffix: true,
                          })}
                        </span>
                      </div>
                    </div>
                    <ArrowRight className="h-4 w-4 text-muted-foreground mt-1" />
                  </div>
                </Link>
              ))}
            </div>
          )}
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
