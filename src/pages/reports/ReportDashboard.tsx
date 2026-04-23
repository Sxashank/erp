import { Link } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { PageHeader } from '@/components/common/PageHeader';
import {
  BarChart3,
  FileText,
  TrendingUp,
  AlertTriangle,
  Building,
  PieChart,
  Calendar,
  Download,
  Clock,
  Shield,
  Landmark,
  Users,
  DollarSign,
} from 'lucide-react';

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    notation: 'compact',
    maximumFractionDigits: 1,
  }).format(value);
};

// Report categories
const reportCategories = [
  {
    title: 'Financial Reports',
    description: 'Core financial statements and analysis',
    icon: DollarSign,
    color: 'bg-blue-100 text-blue-600',
    reports: [
      { name: 'Trial Balance', path: '/admin/reports/trial-balance', badge: null },
      { name: 'Profit & Loss', path: '/admin/reports/profit-loss', badge: null },
      { name: 'Balance Sheet', path: '/admin/reports/balance-sheet', badge: null },
      { name: 'Cash Flow Statement', path: '/admin/reports/cash-flow-statement', badge: null },
      { name: 'Day Book', path: '/admin/reports/day-book', badge: null },
      { name: 'Account Ledger', path: '/admin/reports/account-ledger', badge: null },
    ],
  },
  {
    title: 'Regulatory Reports',
    description: 'RBI and statutory compliance reports',
    icon: Shield,
    color: 'bg-red-100 text-red-600',
    reports: [
      { name: 'ALM Report', path: '/admin/reports/regulatory/alm', badge: 'RBI' },
      { name: 'NPA Classification', path: '/admin/reports/regulatory/npa', badge: 'RBI' },
      { name: 'CRAR Report', path: '/admin/reports/regulatory/crar', badge: 'RBI' },
      { name: 'Liquidity Coverage', path: '/admin/reports/regulatory/liquidity', badge: 'RBI' },
      { name: 'Large Exposure', path: '/admin/reports/regulatory/large-exposure', badge: null },
      { name: 'Sector Exposure', path: '/admin/reports/regulatory/sector-exposure', badge: null },
    ],
  },
  {
    title: 'MIS Reports',
    description: 'Management information and analytics',
    icon: BarChart3,
    color: 'bg-green-100 text-green-600',
    reports: [
      { name: 'Portfolio Summary', path: '/admin/reports/mis/portfolio', badge: null },
      { name: 'Disbursement Report', path: '/admin/reports/mis/disbursement', badge: null },
      { name: 'Collection Report', path: '/admin/reports/mis/collection', badge: null },
      { name: 'Delinquency Report', path: '/admin/reports/mis/delinquency', badge: null },
      { name: 'Profitability Report', path: '/admin/reports/mis/profitability', badge: null },
      { name: 'Branch Performance', path: '/admin/reports/mis/branch-performance', badge: null },
    ],
  },
  {
    title: 'Tax Reports',
    description: 'GST and TDS compliance reports',
    icon: Landmark,
    color: 'bg-purple-100 text-purple-600',
    reports: [
      { name: 'GSTR-1', path: '/admin/gst/gstn/gstr1', badge: 'GST' },
      { name: 'GSTR-3B', path: '/admin/gst/gstn/gstr3b', badge: 'GST' },
      { name: 'TDS Returns', path: '/admin/tds/returns', badge: 'TDS' },
      { name: 'TDS Certificates', path: '/admin/tds/certificates', badge: 'TDS' },
    ],
  },
];

// Key metrics
const keyMetrics = [
  { label: 'AUM', value: 2235000000, change: 3.5, icon: TrendingUp },
  { label: 'GNPA', value: 3.8, unit: '%', change: -0.2, icon: AlertTriangle },
  { label: 'CRAR', value: 18.2, unit: '%', change: 0.5, icon: Shield },
  { label: 'Collection Efficiency', value: 88.4, unit: '%', change: 1.2, icon: BarChart3 },
];

// Recent reports
const recentReports = [
  { name: 'NPA Report - Dec 2024', date: '2025-01-15', type: 'Regulatory' },
  { name: 'Monthly MIS - Dec 2024', date: '2025-01-10', type: 'MIS' },
  { name: 'GSTR-3B - Dec 2024', date: '2025-01-08', type: 'Tax' },
  { name: 'Trial Balance - Dec 2024', date: '2025-01-05', type: 'Financial' },
];

// Scheduled reports
const scheduledReports = [
  { name: 'Daily Collection Report', frequency: 'Daily', nextRun: 'Tomorrow 6:00 AM' },
  { name: 'Weekly MIS', frequency: 'Weekly', nextRun: 'Monday 9:00 AM' },
  { name: 'Monthly ALM Report', frequency: 'Monthly', nextRun: '1st Feb 2025' },
];

export default function ReportDashboard() {
  return (
    <div className="container mx-auto py-6 space-y-6">
      <PageHeader
        title="Reports & Analytics"
        subtitle="Access financial, regulatory, and management reports"
        actions={
          <Button variant="outline">
            <Calendar className="h-4 w-4 mr-2" />
            Report Scheduler
          </Button>
        }
      />

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {keyMetrics.map((metric) => (
          <Card key={metric.label}>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-muted-foreground">{metric.label}</div>
                  <div className="text-2xl font-bold">
                    {metric.unit === '%'
                      ? `${metric.value}%`
                      : formatCurrency(metric.value)}
                  </div>
                </div>
                <div className={`flex items-center text-sm ${metric.change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {metric.change >= 0 ? '+' : ''}{metric.change}{metric.unit === '%' ? 'pp' : '%'}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Report Categories */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {reportCategories.map((category) => (
          <Card key={category.title}>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <div className={`p-2 rounded-lg ${category.color}`}>
                  <category.icon className="h-5 w-5" />
                </div>
                {category.title}
              </CardTitle>
              <CardDescription>{category.description}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-2">
                {category.reports.map((report) => (
                  <Link
                    key={report.name}
                    to={report.path}
                    className="flex items-center justify-between p-2 rounded-lg hover:bg-muted transition-colors"
                  >
                    <span className="text-sm">{report.name}</span>
                    {report.badge && (
                      <Badge variant="outline" className="text-xs">
                        {report.badge}
                      </Badge>
                    )}
                  </Link>
                ))}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Recent & Scheduled */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Reports */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              Recent Reports
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {recentReports.map((report, index) => (
                <div key={index} className="flex items-center justify-between p-2 border rounded-lg">
                  <div>
                    <div className="font-medium text-sm">{report.name}</div>
                    <div className="text-xs text-muted-foreground">{report.date}</div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant="outline">{report.type}</Badge>
                    <Button variant="ghost" size="sm">
                      <Download className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Scheduled Reports */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock className="h-5 w-5" />
              Scheduled Reports
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {scheduledReports.map((report, index) => (
                <div key={index} className="flex items-center justify-between p-2 border rounded-lg">
                  <div>
                    <div className="font-medium text-sm">{report.name}</div>
                    <div className="text-xs text-muted-foreground">Next: {report.nextRun}</div>
                  </div>
                  <Badge variant="secondary">{report.frequency}</Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
