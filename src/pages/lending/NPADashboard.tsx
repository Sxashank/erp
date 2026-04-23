import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  BarChart3,
  RefreshCw,
  Download,
  ArrowRight,
  AlertCircle,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { PageHeader } from '@/components/common/PageHeader';
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
import { Progress } from '@/components/ui/progress';
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
} from 'recharts';
import { formatCurrency, formatPercentage } from '@/lib/utils';

// Mock data
const npaSummary = {
  total_loans: 1250,
  total_outstanding: 5000000000,
  standard: { count: 1180, amount: 4650000000, percentage: 93.0 },
  sma_0: { count: 25, amount: 120000000, percentage: 2.4 },
  sma_1: { count: 15, amount: 80000000, percentage: 1.6 },
  sma_2: { count: 10, amount: 50000000, percentage: 1.0 },
  npa: { count: 20, amount: 100000000, percentage: 2.0 },
  gross_npa_ratio: 2.0,
  net_npa_ratio: 1.2,
  provision_coverage: 65,
};

const classificationBreakdown = [
  { name: 'Standard', value: 93.0, count: 1180, amount: 4650, color: '#22c55e' },
  { name: 'SMA-0', value: 2.4, count: 25, amount: 120, color: '#eab308' },
  { name: 'SMA-1', value: 1.6, count: 15, amount: 80, color: '#f97316' },
  { name: 'SMA-2', value: 1.0, count: 10, amount: 50, color: '#ef4444' },
  { name: 'NPA', value: 2.0, count: 20, amount: 100, color: '#dc2626' },
];

const npaMovement = [
  { month: 'Oct', opening: 85, additions: 12, recovery: 8, closing: 89 },
  { month: 'Nov', opening: 89, additions: 15, recovery: 10, closing: 94 },
  { month: 'Dec', opening: 94, additions: 8, recovery: 12, closing: 90 },
  { month: 'Jan', opening: 90, additions: 18, recovery: 8, closing: 100 },
];

const npaAccounts = [
  {
    id: '1',
    loan_account: 'SMFC/LA/2024/00125',
    entity: 'ABC Trading Co.',
    outstanding: 15000000,
    dpd: 120,
    classification: 'SUBSTANDARD',
    provision: 2250000,
  },
  {
    id: '2',
    loan_account: 'SMFC/LA/2024/00089',
    entity: 'XYZ Industries',
    outstanding: 25000000,
    dpd: 180,
    classification: 'DOUBTFUL_1',
    provision: 6250000,
  },
  {
    id: '3',
    loan_account: 'SMFC/LA/2023/00456',
    entity: 'Metro Logistics',
    outstanding: 18000000,
    dpd: 95,
    classification: 'SUBSTANDARD',
    provision: 2700000,
  },
];

const getClassificationBadge = (classification: string) => {
  const variants: Record<string, { variant: 'default' | 'secondary' | 'destructive' | 'outline'; label: string }> = {
    STANDARD: { variant: 'default', label: 'Standard' },
    SMA_0: { variant: 'secondary', label: 'SMA-0' },
    SMA_1: { variant: 'secondary', label: 'SMA-1' },
    SMA_2: { variant: 'outline', label: 'SMA-2' },
    SUBSTANDARD: { variant: 'destructive', label: 'Substandard' },
    DOUBTFUL_1: { variant: 'destructive', label: 'Doubtful-1' },
    DOUBTFUL_2: { variant: 'destructive', label: 'Doubtful-2' },
    DOUBTFUL_3: { variant: 'destructive', label: 'Doubtful-3' },
    LOSS: { variant: 'destructive', label: 'Loss' },
  };
  const config = variants[classification] || { variant: 'default', label: classification };
  return <Badge variant={config.variant}>{config.label}</Badge>;
};

export default function NPADashboard() {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [period, setPeriod] = useState('current');

  const runClassification = async () => {
    setIsLoading(true);
    // API call would go here
    setTimeout(() => setIsLoading(false), 2000);
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="NPA Dashboard"
        subtitle="Non-Performing Asset monitoring and classification"
        actions={
          <div className="flex gap-2">
            <Select value={period} onValueChange={setPeriod}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Select period" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="current">Current</SelectItem>
                <SelectItem value="previous">Previous Month</SelectItem>
                <SelectItem value="quarter">Quarter End</SelectItem>
              </SelectContent>
            </Select>
            <Button variant="outline" onClick={runClassification} disabled={isLoading}>
              <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
              Run Classification
            </Button>
            <Button variant="outline">
              <Download className="h-4 w-4 mr-2" />
              Export Report
            </Button>
          </div>
        }
      />

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Gross NPA Ratio
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <span className="text-3xl font-bold">{npaSummary.gross_npa_ratio}%</span>
              <Badge variant="destructive" className="flex items-center gap-1">
                <TrendingUp className="h-3 w-3" />
                +0.2%
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Previous: 1.8%
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Net NPA Ratio
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <span className="text-3xl font-bold">{npaSummary.net_npa_ratio}%</span>
              <Badge variant="secondary" className="flex items-center gap-1">
                <TrendingDown className="h-3 w-3" />
                -0.1%
              </Badge>
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Previous: 1.3%
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Provision Coverage
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <span className="text-3xl font-bold">{npaSummary.provision_coverage}%</span>
            </div>
            <Progress value={npaSummary.provision_coverage} className="mt-2" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              NPA Count
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <span className="text-3xl font-bold">{npaSummary.npa.count}</span>
              <span className="text-sm text-muted-foreground">
                / {npaSummary.total_loans} loans
              </span>
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Amount: {formatCurrency(npaSummary.npa.amount)}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Asset Classification</CardTitle>
            <CardDescription>Portfolio distribution by classification</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={classificationBreakdown}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={2}
                    dataKey="value"
                    label={({ name, value }) => `${name}: ${value}%`}
                  >
                    {classificationBreakdown.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(value: number | undefined, name, props: any) => [
                      `${value ?? 0}% (${formatCurrency(props.payload.amount * 10000000)})`,
                      name,
                    ]}
                  />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>NPA Movement</CardTitle>
            <CardDescription>Monthly NPA trend (in Cr)</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={npaMovement}>
                  <XAxis dataKey="month" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="opening" name="Opening" fill="#94a3b8" />
                  <Bar dataKey="additions" name="Additions" fill="#ef4444" />
                  <Bar dataKey="recovery" name="Recovery" fill="#22c55e" />
                  <Bar dataKey="closing" name="Closing" fill="#3b82f6" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Classification Breakdown */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>Classification Breakdown</CardTitle>
            <CardDescription>Detailed view of asset classification</CardDescription>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {classificationBreakdown.map((item) => (
              <div key={item.name} className="flex items-center gap-4">
                <div className="w-24 font-medium">{item.name}</div>
                <div className="flex-1">
                  <Progress
                    value={item.value}
                    className="h-4"
                    style={{
                      // @ts-ignore
                      '--progress-background': item.color,
                    }}
                  />
                </div>
                <div className="w-20 text-right font-medium">{item.value}%</div>
                <div className="w-20 text-right text-muted-foreground">{item.count} loans</div>
                <div className="w-32 text-right text-muted-foreground">
                  {formatCurrency(item.amount * 10000000)}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* NPA Accounts */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle>NPA Accounts</CardTitle>
            <CardDescription>Accounts currently classified as NPA</CardDescription>
          </div>
          <Button variant="outline" onClick={() => navigate('/lending/npa/classification')}>
            View All
            <ArrowRight className="h-4 w-4 ml-2" />
          </Button>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Loan Account</TableHead>
                <TableHead>Entity</TableHead>
                <TableHead className="text-right">Outstanding</TableHead>
                <TableHead className="text-center">DPD</TableHead>
                <TableHead>Classification</TableHead>
                <TableHead className="text-right">Provision</TableHead>
                <TableHead></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {npaAccounts.map((account) => (
                <TableRow key={account.id}>
                  <TableCell className="font-medium">{account.loan_account}</TableCell>
                  <TableCell>{account.entity}</TableCell>
                  <TableCell className="text-right">
                    {formatCurrency(account.outstanding)}
                  </TableCell>
                  <TableCell className="text-center">
                    <Badge variant={account.dpd > 90 ? 'destructive' : 'secondary'}>
                      {account.dpd} days
                    </Badge>
                  </TableCell>
                  <TableCell>{getClassificationBadge(account.classification)}</TableCell>
                  <TableCell className="text-right">
                    {formatCurrency(account.provision)}
                  </TableCell>
                  <TableCell>
                    <Button variant="ghost" size="sm">
                      <AlertCircle className="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Button
          variant="outline"
          className="h-auto py-4 flex flex-col items-center gap-2"
          onClick={() => navigate('/lending/npa/classification')}
        >
          <BarChart3 className="h-6 w-6" />
          <span>View Classification</span>
        </Button>
        <Button
          variant="outline"
          className="h-auto py-4 flex flex-col items-center gap-2"
          onClick={() => navigate('/lending/npa/provision')}
        >
          <AlertTriangle className="h-6 w-6" />
          <span>Calculate Provision</span>
        </Button>
        <Button
          variant="outline"
          className="h-auto py-4 flex flex-col items-center gap-2"
          onClick={() => navigate('/lending/npa/upgrade')}
        >
          <TrendingUp className="h-6 w-6" />
          <span>NPA Upgrade</span>
        </Button>
        <Button
          variant="outline"
          className="h-auto py-4 flex flex-col items-center gap-2"
          onClick={() => navigate('/lending/npa/write-off')}
        >
          <AlertTriangle className="h-6 w-6" />
          <span>Write-Off</span>
        </Button>
      </div>
    </div>
  );
}
