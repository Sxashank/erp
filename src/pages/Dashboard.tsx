import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Building2,
  Users,
  FileText,
  Receipt,
  CreditCard,
  Banknote,
  Clock,
  AlertCircle,
  Loader2,
  RefreshCw,
  TrendingUp,
  TrendingDown,
  LayoutDashboard,
} from 'lucide-react';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { PageHeader } from '@/components/common/PageHeader';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  KPICard,
  APSummaryWidget,
  ARSummaryWidget,
  CashFlowWidget,
  TrendChart,
  RecentActivityList,
} from '@/components/dashboard';
import { ResponsiveDashboardGrid } from '@/components/bi';
import {
  organizationsApi,
  dashboardApi,
} from '@/services/api';
import { biDashboardApi } from '@/services/biApi';
import { useToast } from '@/hooks/use-toast';
import { DashboardListItem } from '@/types/bi';

interface Organization {
  id: string;
  name: string;
  code: string;
}

export function Dashboard() {
  const { toast } = useToast();
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [selectedOrg, setSelectedOrg] = useState<string>('');

  // Dashboard data states
  const [summary, setSummary] = useState<any>(null);
  const [apSummary, setApSummary] = useState<any>(null);
  const [arSummary, setArSummary] = useState<any>(null);
  const [cashflow, setCashflow] = useState<any>(null);
  const [trends, setTrends] = useState<any>(null);
  const [recentActivity, setRecentActivity] = useState<any[]>([]);

  // Custom BI dashboards
  const [customDashboards, setCustomDashboards] = useState<DashboardListItem[]>([]);
  const [activeDashboard, setActiveDashboard] = useState<string>('overview');
  const [selectedDashboardData, setSelectedDashboardData] = useState<any>(null);
  const [loadingCustomDashboard, setLoadingCustomDashboard] = useState(false);

  useEffect(() => {
    loadOrganizations();
    loadLandingDashboards();
  }, []);

  useEffect(() => {
    if (selectedOrg) {
      loadDashboardData();
    }
  }, [selectedOrg]);

  // Load custom dashboard when tab changes
  useEffect(() => {
    if (activeDashboard !== 'overview' && activeDashboard) {
      loadCustomDashboard(activeDashboard);
    }
  }, [activeDashboard]);

  const loadLandingDashboards = async () => {
    try {
      const response = await biDashboardApi.getLanding();
      setCustomDashboards((response.data || []) as any);
    } catch (error) {
      console.error('Failed to load landing dashboards:', error);
      // Silently fail - custom dashboards are optional
    }
  };

  const loadCustomDashboard = async (dashboardId: string) => {
    try {
      setLoadingCustomDashboard(true);
      const response = await biDashboardApi.get(dashboardId);
      setSelectedDashboardData(response.data);
    } catch (error) {
      console.error('Failed to load custom dashboard:', error);
      toast({
        title: 'Error',
        description: 'Failed to load dashboard',
        variant: 'destructive',
      });
    } finally {
      setLoadingCustomDashboard(false);
    }
  };

  const loadOrganizations = async () => {
    try {
      const response = await organizationsApi.list({ include_inactive: false });
      const orgs = response.data.items || [];
      setOrganizations(orgs);
      if (orgs.length > 0) {
        setSelectedOrg(orgs[0].id);
      }
    } catch (error) {
      console.error('Failed to load organizations:', error);
      toast({
        title: 'Error',
        description: 'Failed to load organizations',
        variant: 'destructive',
      });
    }
  };

  const loadDashboardData = async () => {
    if (!selectedOrg) return;

    setLoading(true);
    try {
      const [summaryRes, apRes, arRes, cashflowRes, trendsRes, activityRes] =
        await Promise.all([
          dashboardApi.getSummary({ organization_id: selectedOrg }).catch(() => ({ data: null })),
          dashboardApi.getAPSummary({ organization_id: selectedOrg }).catch(() => ({ data: null })),
          dashboardApi.getARSummary({ organization_id: selectedOrg }).catch(() => ({ data: null })),
          dashboardApi.getCashflow({ organization_id: selectedOrg }).catch(() => ({ data: null })),
          dashboardApi.getTrends({ organization_id: selectedOrg, months: 6 }).catch(() => ({ data: null })),
          dashboardApi.getRecentActivity({ organization_id: selectedOrg, limit: 10 }).catch(() => ({ data: [] })),
        ]);

      setSummary(summaryRes.data);
      setApSummary(apRes.data);
      setArSummary(arRes.data);
      setCashflow(cashflowRes.data);
      setTrends(trendsRes.data);
      setRecentActivity(activityRes.data || []);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
      toast({
        title: 'Error',
        description: 'Failed to load dashboard data',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadDashboardData();
    setRefreshing(false);
    toast({
      title: 'Refreshed',
      description: 'Dashboard data has been updated',
    });
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount || 0);
  };

  const formatCompact = (amount: number | undefined | null) => {
    const num = Number(amount) || 0;
    if (num === 0) return '0';
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

  // Render the main overview dashboard content
  const renderOverviewContent = () => (
    <>
      {/* Top KPI Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <KPICard
          title="Total Revenue (MTD)"
          value={formatCurrency(summary?.total_revenue_mtd || 0)}
          change={summary?.revenue_change}
          changeLabel="vs last month"
          trend={summary?.revenue_change > 0 ? 'up' : summary?.revenue_change < 0 ? 'down' : 'neutral'}
          icon={<TrendingUp className="h-5 w-5 text-green-500" />}
        />
        <KPICard
          title="Total Expenses (MTD)"
          value={formatCurrency(summary?.total_expenses_mtd || 0)}
          change={summary?.expenses_change}
          changeLabel="vs last month"
          trend={summary?.expenses_change > 0 ? 'down' : summary?.expenses_change < 0 ? 'up' : 'neutral'}
          icon={<TrendingDown className="h-5 w-5 text-red-500" />}
        />
        <KPICard
          title="Net Profit (MTD)"
          value={formatCurrency(summary?.net_profit_mtd || 0)}
          subtitle={`${((summary?.net_profit_mtd || 0) / (summary?.total_revenue_mtd || 1) * 100).toFixed(1)}% margin`}
          icon={<Receipt className="h-5 w-5 text-purple-500" />}
          valueClassName={summary?.net_profit_mtd >= 0 ? 'text-green-600' : 'text-red-600'}
        />
        <KPICard
          title="Pending Approvals"
          value={summary?.total_pending_approvals || 0}
          subtitle={`${summary?.total_vendors || 0} vendors, ${summary?.total_customers || 0} customers`}
          icon={<Clock className="h-5 w-5 text-orange-500" />}
        />
      </div>

      {/* Quick Stats Row */}
      <div className="grid gap-4 md:grid-cols-4">
        <Link to="/admin/ap-ar/vendors">
          <Card className="hover:shadow-md transition-shadow cursor-pointer">
            <CardContent className="flex items-center gap-4 p-4">
              <div className="rounded-lg bg-orange-100 p-3">
                <Building2 className="h-5 w-5 text-orange-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{summary?.total_vendors || 0}</p>
                <p className="text-sm text-muted-foreground">Active Vendors</p>
              </div>
            </CardContent>
          </Card>
        </Link>
        <Link to="/admin/ap-ar/customers">
          <Card className="hover:shadow-md transition-shadow cursor-pointer">
            <CardContent className="flex items-center gap-4 p-4">
              <div className="rounded-lg bg-blue-100 p-3">
                <Users className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{summary?.total_customers || 0}</p>
                <p className="text-sm text-muted-foreground">Active Customers</p>
              </div>
            </CardContent>
          </Card>
        </Link>
        <Link to="/admin/ap-ar/purchase-bills">
          <Card className="hover:shadow-md transition-shadow cursor-pointer">
            <CardContent className="flex items-center gap-4 p-4">
              <div className="rounded-lg bg-red-100 p-3">
                <FileText className="h-5 w-5 text-red-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{formatCompact(apSummary?.total_outstanding || 0)}</p>
                <p className="text-sm text-muted-foreground">AP Outstanding</p>
              </div>
            </CardContent>
          </Card>
        </Link>
        <Link to="/admin/ap-ar/sales-invoices">
          <Card className="hover:shadow-md transition-shadow cursor-pointer">
            <CardContent className="flex items-center gap-4 p-4">
              <div className="rounded-lg bg-green-100 p-3">
                <Receipt className="h-5 w-5 text-green-600" />
              </div>
              <div>
                <p className="text-2xl font-bold">{formatCompact(arSummary?.total_outstanding || 0)}</p>
                <p className="text-sm text-muted-foreground">AR Outstanding</p>
              </div>
            </CardContent>
          </Card>
        </Link>
      </div>

      {/* Main Content Grid */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left Column - AP & AR */}
        <div className="space-y-6">
          {apSummary && (
            <APSummaryWidget
              totalOutstanding={apSummary.total_outstanding || 0}
              totalOverdue={apSummary.total_overdue || 0}
              overdueCount={apSummary.overdue_count || 0}
              dueThisWeek={apSummary.due_this_week || 0}
              dueThisWeekCount={apSummary.due_this_week_count || 0}
              agingBuckets={apSummary.aging_buckets || []}
              topVendors={apSummary.top_vendors || []}
            />
          )}
          {arSummary && (
            <ARSummaryWidget
              totalOutstanding={arSummary.total_outstanding || 0}
              totalOverdue={arSummary.total_overdue || 0}
              overdueCount={arSummary.overdue_count || 0}
              dueThisWeek={arSummary.due_this_week || 0}
              dueThisWeekCount={arSummary.due_this_week_count || 0}
              agingBuckets={arSummary.aging_buckets || []}
              topCustomers={arSummary.top_customers || []}
              collectionRate={arSummary.collection_rate}
            />
          )}
        </div>

        {/* Middle Column - Cash Flow & Trends */}
        <div className="space-y-6">
          {cashflow && (
            <CashFlowWidget
              totalBankBalance={cashflow.total_bank_balance || 0}
              receiptsToday={cashflow.receipts_today || 0}
              paymentsToday={cashflow.payments_today || 0}
              netToday={cashflow.net_today || 0}
              receiptsWeek={cashflow.receipts_week || 0}
              paymentsWeek={cashflow.payments_week || 0}
              netWeek={cashflow.net_week || 0}
              receiptsMonth={cashflow.receipts_month || 0}
              paymentsMonth={cashflow.payments_month || 0}
              netMonth={cashflow.net_month || 0}
              pendingChequeReceipts={cashflow.pending_cheque_receipts}
              pendingChequePayments={cashflow.pending_cheque_payments}
            />
          )}
          {trends && (
            <TrendChart
              revenue={trends.revenue || []}
              expenses={trends.expenses || []}
              collections={trends.collections || []}
              payments={trends.payments || []}
              netProfit={trends.net_profit || []}
            />
          )}
        </div>

        {/* Right Column - Activity & Quick Actions */}
        <div className="space-y-6">
          <RecentActivityList
            activities={recentActivity.map((a: any) => ({
              id: a.id,
              type: a.type,
              number: a.number,
              description: a.description,
              amount: a.amount,
              partyName: a.party_name,
              status: a.status,
              createdAt: a.created_at,
              createdByName: a.created_by_name,
            }))}
          />

          {/* Quick Actions */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-lg font-semibold">Quick Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Link to="/admin/ap-ar/payments/new?type=VENDOR_PAYMENT">
                <Button variant="outline" className="w-full justify-start">
                  <CreditCard className="mr-2 h-4 w-4 text-red-500" />
                  New Vendor Payment
                </Button>
              </Link>
              <Link to="/admin/ap-ar/payments/new?type=CUSTOMER_RECEIPT">
                <Button variant="outline" className="w-full justify-start">
                  <Banknote className="mr-2 h-4 w-4 text-green-500" />
                  New Customer Receipt
                </Button>
              </Link>
              <Link to="/admin/ap-ar/purchase-bills/new">
                <Button variant="outline" className="w-full justify-start">
                  <FileText className="mr-2 h-4 w-4 text-orange-500" />
                  New Purchase Bill
                </Button>
              </Link>
              <Link to="/admin/ap-ar/sales-invoices/new">
                <Button variant="outline" className="w-full justify-start">
                  <Receipt className="mr-2 h-4 w-4 text-blue-500" />
                  New Sales Invoice
                </Button>
              </Link>
            </CardContent>
          </Card>
        </div>
      </div>
    </>
  );

  return (
    <div className="space-y-6">
      <PageHeader
        title="Dashboard"
        subtitle={
          summary?.current_financial_year
            ? `Financial Year: ${summary.current_financial_year}`
            : 'Welcome to SMFC ERP'
        }
        actions={
          <div className="flex items-center gap-3">
            <Select value={selectedOrg} onValueChange={setSelectedOrg}>
              <SelectTrigger className="w-[200px]">
                <SelectValue placeholder="Select Organization" />
              </SelectTrigger>
              <SelectContent>
                {organizations.map((org) => (
                  <SelectItem key={org.id} value={org.id}>
                    {org.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button
              variant="outline"
              size="icon"
              onClick={handleRefresh}
              disabled={refreshing}
            >
              <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
            </Button>
          </div>
        }
      />

      {/* Dashboard Tabs (if custom dashboards exist) */}
      {customDashboards.length > 0 ? (
        <Tabs value={activeDashboard} onValueChange={setActiveDashboard}>
          <TabsList>
            <TabsTrigger value="overview" className="flex items-center gap-2">
              <LayoutDashboard className="h-4 w-4" />
              Overview
            </TabsTrigger>
            {customDashboards.map((d) => (
              <TabsTrigger key={d.id} value={d.id}>
                {d.name}
              </TabsTrigger>
            ))}
          </TabsList>

          <TabsContent value="overview" className="space-y-6 mt-6">
            {loading ? (
              <div className="flex items-center justify-center py-24">
                <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
              </div>
            ) : (
              renderOverviewContent()
            )}
          </TabsContent>

          {customDashboards.map((d) => (
            <TabsContent key={d.id} value={d.id} className="mt-6">
              {loadingCustomDashboard ? (
                <div className="flex items-center justify-center py-24">
                  <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
                </div>
              ) : selectedDashboardData ? (
                <ResponsiveDashboardGrid
                  widgets={selectedDashboardData.widgets || []}
                  autoRefresh={selectedDashboardData.auto_refresh}
                  refreshInterval={selectedDashboardData.refresh_interval_seconds * 1000}
                />
              ) : (
                <div className="text-center py-12 text-muted-foreground">
                  No widgets configured for this dashboard
                </div>
              )}
            </TabsContent>
          ))}
        </Tabs>
      ) : (
        // No custom dashboards - show standard layout
        loading ? (
          <div className="flex items-center justify-center py-24">
            <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
          </div>
        ) : (
          renderOverviewContent()
        )
      )}
    </div>
  );
}
