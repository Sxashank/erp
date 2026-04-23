/**
 * Compliance Dashboard
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Calendar,
  AlertTriangle,
  Clock,
  CheckCircle,
  FileText,
  Plus,
  Settings,
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
import { useToast } from '@/hooks/use-toast';
import complianceService, {
  ComplianceSummary,
  UpcomingCompliance,
  ComplianceCalendarItem,
} from '@/services/complianceService';
import { useRequiredActiveOrganizationId } from '@/hooks/useOrganization';

const REGULATORY_BODY_COLORS: Record<string, string> = {
  RBI: 'bg-blue-100 text-blue-800',
  SEBI: 'bg-purple-100 text-purple-800',
  MCA: 'bg-green-100 text-green-800',
  GST: 'bg-orange-100 text-orange-800',
  INCOME_TAX: 'bg-red-100 text-red-800',
  EPFO: 'bg-cyan-100 text-cyan-800',
  ESIC: 'bg-teal-100 text-teal-800',
  STATE: 'bg-gray-100 text-gray-800',
  OTHER: 'bg-gray-100 text-gray-800',
};

const STATUS_COLORS: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
  PENDING: 'outline',
  IN_PROGRESS: 'secondary',
  PREPARED: 'default',
  UNDER_REVIEW: 'secondary',
  FILED: 'default',
  ACKNOWLEDGED: 'default',
  DELAYED: 'destructive',
  NOT_APPLICABLE: 'outline',
};

export default function ComplianceDashboard() {
  const navigate = useNavigate();
  const { toast } = useToast();

  const [summary, setSummary] = useState<ComplianceSummary | null>(null);
  const [upcoming, setUpcoming] = useState<UpcomingCompliance | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear().toString());

  const organizationId = useRequiredActiveOrganizationId();

  const currentYear = new Date().getFullYear();
  const years = Array.from({ length: 3 }, (_, i) => currentYear - i + 1);

  useEffect(() => {
    loadData();
  }, [selectedYear]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [summaryData, upcomingData] = await Promise.all([
        complianceService.getSummary({
          organization_id: organizationId,
          year: parseInt(selectedYear),
        }),
        complianceService.getUpcoming(organizationId),
      ]);
      setSummary(summaryData);
      setUpcoming(upcomingData);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load compliance data',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateInstances = async () => {
    const currentMonth = new Date().getMonth() + 1;
    try {
      const result = await complianceService.generateInstances({
        organization_id: organizationId,
        year: parseInt(selectedYear),
        month: currentMonth,
      });
      toast({
        title: 'Success',
        description: result.message,
      });
      loadData();
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to generate instances',
        variant: 'destructive',
      });
    }
  };

  const renderComplianceItem = (item: ComplianceCalendarItem) => (
    <div
      key={item.id}
      className="flex items-center justify-between p-3 border rounded-lg hover:bg-muted/50 cursor-pointer"
      onClick={() => navigate(`/admin/compliance/instances/${item.id}`)}
    >
      <div className="flex items-center gap-3">
        <Badge className={REGULATORY_BODY_COLORS[item.regulatory_body]}>
          {item.regulatory_body}
        </Badge>
        <div>
          <p className="font-medium">{item.item_name}</p>
          <p className="text-sm text-muted-foreground">
            Due: {new Date(item.due_date).toLocaleDateString()}
          </p>
        </div>
      </div>
      <Badge variant={STATUS_COLORS[item.status] || 'outline'}>
        {item.status}
      </Badge>
    </div>
  );

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
        title="Compliance Dashboard"
        subtitle="Track and manage regulatory compliance"
        actions={
          <div className="flex gap-2">
            <Select value={selectedYear} onValueChange={setSelectedYear}>
              <SelectTrigger className="w-[120px]">
                <SelectValue placeholder="Year" />
              </SelectTrigger>
              <SelectContent>
                {years.map((year) => (
                  <SelectItem key={year} value={year.toString()}>
                    {year}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button variant="outline" onClick={handleGenerateInstances}>
              <RefreshCw className="mr-2 h-4 w-4" />
              Generate
            </Button>
            <Button variant="outline" onClick={() => navigate('/admin/compliance/items')}>
              <Settings className="mr-2 h-4 w-4" />
              Manage Items
            </Button>
            <Button onClick={() => navigate('/admin/compliance/instances')}>
              <FileText className="mr-2 h-4 w-4" />
              All Instances
            </Button>
          </div>
        }
      />

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary?.total || 0}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Pending
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-600">
              {summary?.pending || 0}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              In Progress
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">
              {summary?.in_progress || 0}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Prepared
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-purple-600">
              {summary?.prepared || 0}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Filed
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {summary?.filed || 0}
            </div>
          </CardContent>
        </Card>
        <Card className="border-red-200">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-destructive">
              Delayed
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-destructive">
              {summary?.delayed || 0}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Upcoming Compliance */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Overdue */}
        <Card className="border-red-200">
          <CardHeader>
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-destructive" />
              <CardTitle className="text-destructive">Overdue</CardTitle>
            </div>
            <CardDescription>
              {upcoming?.overdue.length || 0} items past due date
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {upcoming?.overdue.length === 0 ? (
              <p className="text-center text-muted-foreground py-4">
                No overdue items
              </p>
            ) : (
              upcoming?.overdue.map(renderComplianceItem)
            )}
          </CardContent>
        </Card>

        {/* Due This Week */}
        <Card className="border-yellow-200">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Clock className="h-5 w-5 text-yellow-600" />
              <CardTitle className="text-yellow-600">Due This Week</CardTitle>
            </div>
            <CardDescription>
              {upcoming?.due_this_week.length || 0} items due soon
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {upcoming?.due_this_week.length === 0 ? (
              <p className="text-center text-muted-foreground py-4">
                No items due this week
              </p>
            ) : (
              upcoming?.due_this_week.map(renderComplianceItem)
            )}
          </CardContent>
        </Card>

        {/* Due This Month */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Calendar className="h-5 w-5 text-blue-600" />
              <CardTitle>Due This Month</CardTitle>
            </div>
            <CardDescription>
              {upcoming?.due_this_month.length || 0} upcoming items
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {upcoming?.due_this_month.length === 0 ? (
              <p className="text-center text-muted-foreground py-4">
                No items due this month
              </p>
            ) : (
              upcoming?.due_this_month.map(renderComplianceItem)
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
