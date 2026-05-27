import { formatDistanceToNow } from 'date-fns';
import { Activity, Receipt, FileText, CreditCard, Banknote, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';

import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';

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
          <CardTitle className="flex items-center gap-2 text-lg font-semibold">
            <Activity className="h-5 w-5 text-indigo-500" />
            Recent Activity
          </CardTitle>
        </div>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-[400px] pr-4">
          {activities.length === 0 ? (
            <div className="py-8 text-center text-muted-foreground">No recent activity</div>
          ) : (
            <div className="space-y-4">
              {activities.map((activity) => (
                <Link
                  key={activity.id}
                  to={getActivityLink(activity.type, activity.id)}
                  className="block"
                >
                  <div className="flex items-start gap-3 rounded-lg border p-3 transition-colors hover:bg-muted/50">
                    <div className="mt-1">{getActivityIcon(activity.type)}</div>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center justify-between gap-2">
                        <span className="truncate text-sm font-medium">{activity.number}</span>
                        {getStatusBadge(activity.status)}
                      </div>
                      <p className="truncate text-sm text-muted-foreground">
                        {activity.partyName || activity.description}
                      </p>
                      <div className="mt-1 flex items-center justify-between">
                        <span className="text-sm font-medium">
                          {formatIndianCompactCurrency(activity.amount)}
                        </span>
                        <span className="text-xs text-muted-foreground">
                          {formatDistanceToNow(new Date(activity.createdAt), {
                            addSuffix: true,
                          })}
                        </span>
                      </div>
                    </div>
                    <ArrowRight className="mt-1 h-4 w-4 text-muted-foreground" />
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
