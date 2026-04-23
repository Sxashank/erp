import { useNavigate } from 'react-router-dom';
import {
  BarChart3,
  PieChart,
  TrendingUp,
  AlertTriangle,
  FileText,
  Building2,
  Receipt,
  Scale,
  Landmark,
  Calendar,
  ArrowRight,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { PageHeader } from '@/components/common/PageHeader';

interface ReportCategory {
  title: string;
  description: string;
  icon: React.ReactNode;
  path: string;
  reports: { name: string; path: string }[];
  color: string;
}

const reportCategories: ReportCategory[] = [
  {
    title: 'Portfolio Reports',
    description: 'AUM analysis, product-wise, branch-wise breakdowns',
    icon: <PieChart className="h-6 w-6" />,
    path: '/admin/lending/reports/portfolio',
    color: 'bg-blue-100 text-blue-700',
    reports: [
      { name: 'AUM Summary', path: '/admin/lending/reports/portfolio/aum' },
      { name: 'Product-wise AUM', path: '/admin/lending/reports/portfolio/product-wise' },
      { name: 'Branch-wise AUM', path: '/admin/lending/reports/portfolio/branch-wise' },
      { name: 'Industry Exposure', path: '/admin/lending/reports/portfolio/industry' },
    ],
  },
  {
    title: 'Origination Reports',
    description: 'Application pipeline, conversion funnel, TAT analysis',
    icon: <TrendingUp className="h-6 w-6" />,
    path: '/admin/lending/reports/origination',
    color: 'bg-green-100 text-green-700',
    reports: [
      { name: 'Application Pipeline', path: '/admin/lending/reports/origination/pipeline' },
      { name: 'Conversion Analysis', path: '/admin/lending/reports/origination/conversion' },
      { name: 'TAT Report', path: '/admin/lending/reports/origination/tat' },
      { name: 'Sanction Trend', path: '/admin/lending/reports/origination/sanctions' },
    ],
  },
  {
    title: 'Collection Reports',
    description: 'Collection efficiency, receipt analysis, overdue ageing',
    icon: <Receipt className="h-6 w-6" />,
    path: '/admin/lending/reports/collections',
    color: 'bg-emerald-100 text-emerald-700',
    reports: [
      { name: 'Collection Efficiency', path: '/admin/lending/reports/collections/efficiency' },
      { name: 'Receipt Analysis', path: '/admin/lending/reports/collections/receipts' },
      { name: 'Overdue Ageing', path: '/admin/lending/reports/collections/ageing' },
      { name: 'Demand vs Collection', path: '/admin/lending/reports/collections/demand' },
    ],
  },
  {
    title: 'NPA Reports',
    description: 'NPA movement, classification ageing, provisioning',
    icon: <AlertTriangle className="h-6 w-6" />,
    path: '/admin/lending/reports/npa',
    color: 'bg-red-100 text-red-700',
    reports: [
      { name: 'NPA Movement', path: '/admin/lending/reports/npa/movement' },
      { name: 'Classification Ageing', path: '/admin/lending/reports/npa/classification' },
      { name: 'Provisioning Report', path: '/admin/lending/reports/npa/provisioning' },
      { name: 'Recovery Trend', path: '/admin/lending/reports/npa/recovery' },
    ],
  },
  {
    title: 'Compliance Reports',
    description: 'RBI returns, CRILC, ALM statutory reports',
    icon: <FileText className="h-6 w-6" />,
    path: '/admin/lending/reports/compliance',
    color: 'bg-purple-100 text-purple-700',
    reports: [
      { name: 'NBS-7 Report', path: '/admin/lending/reports/compliance/nbs7' },
      { name: 'CRILC Report', path: '/admin/lending/reports/compliance/crilc' },
      { name: 'ALM Returns', path: '/admin/lending/reports/compliance/alm' },
      { name: 'Compliance Calendar', path: '/admin/lending/reports/compliance/calendar' },
    ],
  },
  {
    title: 'Treasury Reports',
    description: 'Borrowing position, ALM gap, interest rate sensitivity',
    icon: <Landmark className="h-6 w-6" />,
    path: '/admin/lending/reports/treasury',
    color: 'bg-indigo-100 text-indigo-700',
    reports: [
      { name: 'Borrowing Position', path: '/admin/lending/reports/treasury/borrowings' },
      { name: 'ALM Gap Analysis', path: '/admin/lending/reports/treasury/alm-gap' },
      { name: 'IRS Report', path: '/admin/lending/reports/treasury/irs' },
      { name: 'Maturity Profile', path: '/admin/lending/reports/treasury/maturity' },
    ],
  },
];

export default function ReportsDashboard() {
  const navigate = useNavigate();

  return (
    <div className="space-y-6">
      <PageHeader
        title="Reports & Analytics"
        subtitle="Comprehensive reporting for portfolio analysis and regulatory compliance"
      />

      {/* Report Categories Grid */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {reportCategories.map((category) => (
          <Card key={category.title} className="hover:shadow-md transition-shadow">
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className={`p-2 rounded-lg ${category.color}`}>
                  {category.icon}
                </div>
              </div>
              <CardTitle className="mt-4">{category.title}</CardTitle>
              <CardDescription>{category.description}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {category.reports.map((report) => (
                  <Button
                    key={report.path}
                    variant="ghost"
                    className="w-full justify-between h-auto py-2"
                    onClick={() => navigate(report.path)}
                  >
                    <span>{report.name}</span>
                    <ArrowRight className="h-4 w-4" />
                  </Button>
                ))}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Scheduled Reports */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Scheduled Reports</CardTitle>
              <CardDescription>
                Auto-generated reports delivered to your inbox
              </CardDescription>
            </div>
            <Button variant="outline">
              <Calendar className="mr-2 h-4 w-4" />
              Manage Schedules
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-3">
            <div className="p-4 rounded-lg border">
              <div className="flex items-center gap-2 mb-2">
                <div className="h-2 w-2 rounded-full bg-green-500" />
                <span className="font-medium">Daily Portfolio Summary</span>
              </div>
              <p className="text-sm text-muted-foreground">
                Sent daily at 8:00 AM to management@company.com
              </p>
            </div>
            <div className="p-4 rounded-lg border">
              <div className="flex items-center gap-2 mb-2">
                <div className="h-2 w-2 rounded-full bg-green-500" />
                <span className="font-medium">Weekly Collection Report</span>
              </div>
              <p className="text-sm text-muted-foreground">
                Sent every Monday at 9:00 AM to collections@company.com
              </p>
            </div>
            <div className="p-4 rounded-lg border">
              <div className="flex items-center gap-2 mb-2">
                <div className="h-2 w-2 rounded-full bg-green-500" />
                <span className="font-medium">Monthly NPA Report</span>
              </div>
              <p className="text-sm text-muted-foreground">
                Sent 1st of every month to board@company.com
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
