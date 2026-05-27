import { FileText, AlertTriangle, Clock, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';

import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';

interface AgingBucket {
  label: string;
  amount: number;
  percentage: number;
}

interface TopParty {
  id: string;
  name: string;
  code: string;
  outstanding: number;
  overdue: number;
}

interface APSummaryProps {
  totalOutstanding: number;
  totalOverdue: number;
  overdueCount: number;
  dueThisWeek: number;
  dueThisWeekCount: number;
  agingBuckets: AgingBucket[];
  topVendors: TopParty[];
}
const formatCompact = (amount: number | undefined | null) => {
  const num = Number(amount) || 0;
  if (num >= 10000000) {
    return `${(num / 10000000).toFixed(2)} Cr`;
  }
  if (num >= 100000) {
    return `${(num / 100000).toFixed(2)} L`;
  }
  if (num >= 1000) {
    return `${(num / 1000).toFixed(1)} K`;
  }
  return num.toFixed(0);
};

export function APSummaryWidget({
  totalOutstanding,
  totalOverdue,
  overdueCount,
  dueThisWeek,
  dueThisWeekCount,
  agingBuckets,
  topVendors,
}: APSummaryProps) {
  const overduePercentage = totalOutstanding > 0 ? (totalOverdue / totalOutstanding) * 100 : 0;

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-lg font-semibold">
            <FileText className="h-5 w-5 text-orange-500" />
            Accounts Payable
          </CardTitle>
          <Link
            to="/admin/ap-ar/purchase-bills"
            className="flex items-center text-sm text-blue-600 hover:underline"
          >
            View All <ArrowRight className="ml-1 h-4 w-4" />
          </Link>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Main KPIs */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-muted-foreground">Total Outstanding</p>
            <p className="text-2xl font-bold">{formatIndianCompactCurrency(totalOutstanding)}</p>
          </div>
          <div>
            <p className="flex items-center gap-1 text-sm text-muted-foreground">
              <AlertTriangle className="h-4 w-4 text-red-500" />
              Overdue
            </p>
            <p className="text-2xl font-bold text-red-600">
              {formatIndianCompactCurrency(totalOverdue)}
            </p>
            <p className="text-xs text-muted-foreground">{overdueCount} bills</p>
          </div>
        </div>

        {/* Overdue Progress */}
        <div>
          <div className="mb-1 flex justify-between text-sm">
            <span>Overdue Ratio</span>
            <span className="font-medium">{overduePercentage.toFixed(1)}%</span>
          </div>
          <Progress value={overduePercentage} className="h-2" />
        </div>

        {/* Due This Week */}
        <div className="rounded-lg bg-yellow-50 p-3">
          <div className="flex items-center gap-2">
            <Clock className="h-4 w-4 text-yellow-600" />
            <span className="text-sm font-medium">Due This Week</span>
          </div>
          <p className="mt-1 text-lg font-bold text-yellow-700">
            {formatIndianCompactCurrency(dueThisWeek)}
          </p>
          <p className="text-xs text-yellow-600">{dueThisWeekCount} bills</p>
        </div>

        {/* Aging Buckets */}
        {agingBuckets.length > 0 && (
          <div>
            <p className="mb-2 text-sm font-medium">Overdue Aging</p>
            <div className="space-y-2">
              {agingBuckets.map((bucket, idx) => (
                <div key={idx} className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">{bucket.label}</span>
                  <div className="flex items-center gap-2">
                    <span className="font-medium">{formatCompact(bucket.amount)}</span>
                    <Badge variant="outline" className="text-xs">
                      {bucket.percentage.toFixed(0)}%
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Top Vendors */}
        {topVendors.length > 0 && (
          <div>
            <p className="mb-2 text-sm font-medium">Top Vendors by Outstanding</p>
            <div className="space-y-2">
              {topVendors.slice(0, 3).map((vendor) => (
                <div key={vendor.id} className="flex items-center justify-between text-sm">
                  <div className="max-w-[150px] truncate">
                    <span className="font-medium">{vendor.name}</span>
                  </div>
                  <span className="font-medium">{formatCompact(vendor.outstanding)}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
