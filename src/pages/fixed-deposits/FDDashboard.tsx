/**
 * Fixed Deposits Dashboard
 */

import {
  Wallet,
  TrendingUp,
  Calendar,
  Clock,
  Plus,
  Settings,
  FileText,
  Calculator,
} from 'lucide-react';
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

import { DateDisplay } from '@/components/common/DateDisplay';
import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from '@/components/ui/card';
import { useToast } from '@/hooks/use-toast';
import { useRequiredActiveOrganizationId } from '@/hooks/useOrganization';
import type { FDSummary, FixedDeposit } from '@/services/fixedDepositService';
import fixedDepositService from '@/services/fixedDepositService';

const STATUS_COLORS: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
  DRAFT: 'outline',
  PENDING_APPROVAL: 'secondary',
  ACTIVE: 'default',
  MATURED: 'default',
  PREMATURE_CLOSED: 'secondary',
  RENEWED: 'default',
  CANCELLED: 'destructive',
};

export default function FDDashboard() {
  const navigate = useNavigate();
  const { toast } = useToast();

  const [summary, setSummary] = useState<FDSummary | null>(null);
  const [maturingFDs, setMaturingFDs] = useState<FixedDeposit[]>([]);
  const [loading, setLoading] = useState(true);

  const organizationId = useRequiredActiveOrganizationId();

  useEffect(() => {
    loadData();
  }, [organizationId]);

  const loadData = async () => {
    try {
      setLoading(true);

      // Get summary
      const summaryData = await fixedDepositService.getSummary();
      setSummary(summaryData);

      // Get FDs maturing in next 30 days
      const today = new Date();
      const thirtyDaysLater = new Date();
      thirtyDaysLater.setDate(thirtyDaysLater.getDate() + 30);

      const maturingData = await fixedDepositService.listDeposits({
        status: 'ACTIVE',
        maturing_after: today.toISOString().split('T')[0],
        maturing_before: thirtyDaysLater.toISOString().split('T')[0],
        limit: 10,
      });
      setMaturingFDs(maturingData.items);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load dashboard data',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(amount);
  };

  if (loading) {
    return (
      <div className="container mx-auto py-6">
        <div className="text-center py-8">Loading...</div>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-6 space-y-6">
      <PageHeader
        title="Fixed Deposits"
        subtitle="Manage fixed deposits and interest calculations"
        actions={
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => navigate('/admin/fixed-deposits/products')}>
              <Settings className="mr-2 h-4 w-4" />
              Products
            </Button>
            <Button variant="outline" onClick={() => navigate('/admin/fixed-deposits/interest')}>
              <Calculator className="mr-2 h-4 w-4" />
              Interest Run
            </Button>
            <Button onClick={() => navigate('/admin/fixed-deposits/new')}>
              <Plus className="mr-2 h-4 w-4" />
              New FD
            </Button>
          </div>
        }
      />

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total FDs
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary?.total_fds || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Active FDs
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {summary?.active_fds || 0}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Deposits
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {formatCurrency(summary?.total_deposit_amount || 0)}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Maturity Value
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">
              {formatCurrency(summary?.total_maturity_amount || 0)}
            </div>
          </CardContent>
        </Card>
        <Card className="border-yellow-200">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-yellow-600">
              Maturing This Month
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600">
              {summary?.maturing_this_month || 0}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Maturing Next Month
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {summary?.maturing_next_month || 0}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Status Breakdown */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>By Status</CardTitle>
            <CardDescription>FD distribution by status</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {summary?.by_status &&
                Object.entries(summary.by_status).map(([status, count]) => (
                  <div key={status} className="flex justify-between items-center">
                    <Badge variant={STATUS_COLORS[status] || 'outline'}>
                      {status.replace('_', ' ')}
                    </Badge>
                    <span className="font-medium">{count}</span>
                  </div>
                ))}
              {(!summary?.by_status || Object.keys(summary.by_status).length === 0) && (
                <p className="text-center text-muted-foreground py-4">No data</p>
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>By Customer Category</CardTitle>
            <CardDescription>Active FDs by customer type</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {summary?.by_customer_category &&
                Object.entries(summary.by_customer_category).map(([category, count]) => (
                  <div key={category} className="flex justify-between items-center">
                    <span className="text-sm">{category.replace('_', ' ')}</span>
                    <span className="font-medium">{count}</span>
                  </div>
                ))}
              {(!summary?.by_customer_category ||
                Object.keys(summary.by_customer_category).length === 0) && (
                <p className="text-center text-muted-foreground py-4">No data</p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Upcoming Maturities */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Calendar className="h-5 w-5 text-yellow-600" />
              <div>
                <CardTitle>Upcoming Maturities</CardTitle>
                <CardDescription>FDs maturing in the next 30 days</CardDescription>
              </div>
            </div>
            <Button variant="outline" onClick={() => navigate('/admin/fixed-deposits')}>
              View All
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {maturingFDs.length === 0 ? (
            <p className="text-center text-muted-foreground py-8">
              No FDs maturing in the next 30 days
            </p>
          ) : (
            <div className="space-y-3">
              {maturingFDs.map((fd) => (
                <div
                  key={fd.id}
                  className="flex items-center justify-between p-3 border rounded-lg hover:bg-muted/50 cursor-pointer"
                  onClick={() => navigate(`/admin/fixed-deposits/${fd.id}`)}
                >
                  <div className="flex items-center gap-4">
                    <div>
                      <p className="font-medium">{fd.fd_number}</p>
                      <p className="text-sm text-muted-foreground">
                        {fd.product_name || fd.product_code}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-medium">{formatCurrency(fd.maturity_amount)}</p>
                    <p className="text-sm text-muted-foreground">
                      Due: <DateDisplay date={fd.maturity_date} />
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    {fd.auto_renew && (
                      <Badge variant="outline">Auto-Renew</Badge>
                    )}
                    <Badge variant={STATUS_COLORS[fd.status]}>{fd.status}</Badge>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card
          className="cursor-pointer hover:bg-muted/50"
          onClick={() => navigate('/admin/fixed-deposits')}
        >
          <CardContent className="flex items-center gap-4 p-6">
            <FileText className="h-8 w-8 text-blue-600" />
            <div>
              <p className="font-medium">All Fixed Deposits</p>
              <p className="text-sm text-muted-foreground">View and manage</p>
            </div>
          </CardContent>
        </Card>
        <Card
          className="cursor-pointer hover:bg-muted/50"
          onClick={() => navigate('/admin/fixed-deposits/new')}
        >
          <CardContent className="flex items-center gap-4 p-6">
            <Plus className="h-8 w-8 text-green-600" />
            <div>
              <p className="font-medium">New FD</p>
              <p className="text-sm text-muted-foreground">Create deposit</p>
            </div>
          </CardContent>
        </Card>
        <Card
          className="cursor-pointer hover:bg-muted/50"
          onClick={() => navigate('/admin/fixed-deposits/products')}
        >
          <CardContent className="flex items-center gap-4 p-6">
            <Settings className="h-8 w-8 text-purple-600" />
            <div>
              <p className="font-medium">Products</p>
              <p className="text-sm text-muted-foreground">Configure</p>
            </div>
          </CardContent>
        </Card>
        <Card
          className="cursor-pointer hover:bg-muted/50"
          onClick={() => navigate('/admin/fixed-deposits/interest')}
        >
          <CardContent className="flex items-center gap-4 p-6">
            <Calculator className="h-8 w-8 text-orange-600" />
            <div>
              <p className="font-medium">Interest Run</p>
              <p className="text-sm text-muted-foreground">Accrual & payout</p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
