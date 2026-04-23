import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  TrendingUp,
  TrendingDown,
  Minus,
  Search,
  Filter,
  Eye,
  Download,
  History,
  CreditCard,
  Calendar,
  ArrowUpRight,
  ArrowDownRight,
} from 'lucide-react';

// Mock customer score history data
const customerScoreHistory = [
  {
    customerId: 'CUST001',
    customerName: 'Rajesh Kumar',
    pan: 'ABCDE1234F',
    currentScore: 782,
    previousScore: 765,
    scoreChange: 17,
    trend: 'UP',
    bureau: 'CIBIL',
    lastPullDate: '2025-01-15',
    history: [
      { date: '2025-01-15', score: 782, bureau: 'CIBIL', reportId: 'RPT001' },
      { date: '2024-10-20', score: 765, bureau: 'CIBIL', reportId: 'RPT002' },
      { date: '2024-07-15', score: 748, bureau: 'CIBIL', reportId: 'RPT003' },
      { date: '2024-04-10', score: 720, bureau: 'CIBIL', reportId: 'RPT004' },
      { date: '2024-01-05', score: 695, bureau: 'CIBIL', reportId: 'RPT005' },
    ],
  },
  {
    customerId: 'CUST002',
    customerName: 'Priya Sharma',
    pan: 'FGHIJ5678K',
    currentScore: 695,
    previousScore: 710,
    scoreChange: -15,
    trend: 'DOWN',
    bureau: 'EXPERIAN',
    lastPullDate: '2025-01-14',
    history: [
      { date: '2025-01-14', score: 695, bureau: 'EXPERIAN', reportId: 'RPT006' },
      { date: '2024-09-18', score: 710, bureau: 'EXPERIAN', reportId: 'RPT007' },
      { date: '2024-06-22', score: 705, bureau: 'EXPERIAN', reportId: 'RPT008' },
    ],
  },
  {
    customerId: 'CUST003',
    customerName: 'Amit Patel',
    pan: 'KLMNO9012L',
    currentScore: 820,
    previousScore: 820,
    scoreChange: 0,
    trend: 'STABLE',
    bureau: 'CIBIL',
    lastPullDate: '2025-01-10',
    history: [
      { date: '2025-01-10', score: 820, bureau: 'CIBIL', reportId: 'RPT009' },
      { date: '2024-08-12', score: 820, bureau: 'CIBIL', reportId: 'RPT010' },
      { date: '2024-05-08', score: 815, bureau: 'CIBIL', reportId: 'RPT011' },
      { date: '2024-02-14', score: 800, bureau: 'CIBIL', reportId: 'RPT012' },
    ],
  },
  {
    customerId: 'CUST004',
    customerName: 'Sunita Devi',
    pan: 'PQRST3456M',
    currentScore: 580,
    previousScore: 620,
    scoreChange: -40,
    trend: 'DOWN',
    bureau: 'EQUIFAX',
    lastPullDate: '2025-01-08',
    history: [
      { date: '2025-01-08', score: 580, bureau: 'EQUIFAX', reportId: 'RPT013' },
      { date: '2024-11-05', score: 620, bureau: 'EQUIFAX', reportId: 'RPT014' },
      { date: '2024-08-20', score: 650, bureau: 'EQUIFAX', reportId: 'RPT015' },
    ],
  },
  {
    customerId: 'CUST005',
    customerName: 'Vikram Singh',
    pan: 'UVWXY7890N',
    currentScore: 745,
    previousScore: 730,
    scoreChange: 15,
    trend: 'UP',
    bureau: 'CIBIL',
    lastPullDate: '2025-01-05',
    history: [
      { date: '2025-01-05', score: 745, bureau: 'CIBIL', reportId: 'RPT016' },
      { date: '2024-10-01', score: 730, bureau: 'CIBIL', reportId: 'RPT017' },
      { date: '2024-07-12', score: 715, bureau: 'CIBIL', reportId: 'RPT018' },
      { date: '2024-04-25', score: 700, bureau: 'CIBIL', reportId: 'RPT019' },
    ],
  },
];

export default function CreditScoreHistory() {
  const [searchTerm, setSearchTerm] = useState('');
  const [trendFilter, setTrendFilter] = useState('all');
  const [selectedCustomer, setSelectedCustomer] = useState<typeof customerScoreHistory[0] | null>(null);

  const filteredCustomers = customerScoreHistory.filter(customer => {
    const matchesSearch =
      customer.customerName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      customer.customerId.toLowerCase().includes(searchTerm.toLowerCase()) ||
      customer.pan.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesTrend = trendFilter === 'all' || customer.trend === trendFilter;
    return matchesSearch && matchesTrend;
  });

  const getScoreColor = (score: number) => {
    if (score >= 750) return 'text-green-600';
    if (score >= 650) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreBg = (score: number) => {
    if (score >= 750) return 'bg-green-100';
    if (score >= 650) return 'bg-yellow-100';
    return 'bg-red-100';
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'UP':
        return <TrendingUp className="h-4 w-4 text-green-500" />;
      case 'DOWN':
        return <TrendingDown className="h-4 w-4 text-red-500" />;
      default:
        return <Minus className="h-4 w-4 text-gray-500" />;
    }
  };

  const getTrendBadge = (trend: string, change: number) => {
    switch (trend) {
      case 'UP':
        return (
          <Badge variant="default" className="bg-green-100 text-green-800">
            <ArrowUpRight className="h-3 w-3 mr-1" />
            +{change}
          </Badge>
        );
      case 'DOWN':
        return (
          <Badge variant="destructive">
            <ArrowDownRight className="h-3 w-3 mr-1" />
            {change}
          </Badge>
        );
      default:
        return (
          <Badge variant="secondary">
            <Minus className="h-3 w-3 mr-1" />
            No Change
          </Badge>
        );
    }
  };

  // Statistics
  const stats = {
    total: customerScoreHistory.length,
    improving: customerScoreHistory.filter(c => c.trend === 'UP').length,
    declining: customerScoreHistory.filter(c => c.trend === 'DOWN').length,
    avgScore: Math.round(customerScoreHistory.reduce((sum, c) => sum + c.currentScore, 0) / customerScoreHistory.length),
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      <PageHeader
        title="Credit Score History"
        subtitle="Track customer credit score trends over time"
        actions={
          <Link to="/admin/kyc/credit-bureau">
            <Button>
              <CreditCard className="h-4 w-4 mr-2" />
              New Pull
            </Button>
          </Link>
        }
      />

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Total Customers</div>
            <div className="text-2xl font-bold mt-1">{stats.total}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <TrendingUp className="h-4 w-4 text-green-500" />
              Improving
            </div>
            <div className="text-2xl font-bold mt-1 text-green-600">{stats.improving}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <TrendingDown className="h-4 w-4 text-red-500" />
              Declining
            </div>
            <div className="text-2xl font-bold mt-1 text-red-600">{stats.declining}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Average Score</div>
            <div className={`text-2xl font-bold mt-1 ${getScoreColor(stats.avgScore)}`}>{stats.avgScore}</div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-2 flex-1 min-w-[200px]">
              <Search className="h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search by name, ID, or PAN..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="max-w-sm"
              />
            </div>
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-muted-foreground" />
              <Select value={trendFilter} onValueChange={setTrendFilter}>
                <SelectTrigger className="w-40">
                  <SelectValue placeholder="Trend" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Trends</SelectItem>
                  <SelectItem value="UP">Improving</SelectItem>
                  <SelectItem value="DOWN">Declining</SelectItem>
                  <SelectItem value="STABLE">Stable</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Customer List */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Customer Score Trends</CardTitle>
            <CardDescription>
              Showing {filteredCustomers.length} customers
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Customer</TableHead>
                  <TableHead>Bureau</TableHead>
                  <TableHead className="text-right">Current Score</TableHead>
                  <TableHead>Change</TableHead>
                  <TableHead>Last Pull</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredCustomers.map((customer) => (
                  <TableRow
                    key={customer.customerId}
                    className={selectedCustomer?.customerId === customer.customerId ? 'bg-muted/50' : 'cursor-pointer hover:bg-muted/30'}
                    onClick={() => setSelectedCustomer(customer)}
                  >
                    <TableCell>
                      <div>
                        <div className="font-medium">{customer.customerName}</div>
                        <div className="text-xs text-muted-foreground">{customer.pan}</div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">{customer.bureau}</Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <span className={`text-lg font-bold ${getScoreColor(customer.currentScore)}`}>
                        {customer.currentScore}
                      </span>
                    </TableCell>
                    <TableCell>
                      {getTrendBadge(customer.trend, customer.scoreChange)}
                    </TableCell>
                    <TableCell className="text-sm">{customer.lastPullDate}</TableCell>
                    <TableCell className="text-right">
                      <Link to={`/admin/kyc/credit-bureau/report/${customer.history[0].reportId}`}>
                        <Button variant="ghost" size="sm">
                          <Eye className="h-4 w-4" />
                        </Button>
                      </Link>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        {/* Score History Detail */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calendar className="h-5 w-5" />
              Score History
            </CardTitle>
            {selectedCustomer && (
              <CardDescription>
                {selectedCustomer.customerName}
              </CardDescription>
            )}
          </CardHeader>
          <CardContent>
            {selectedCustomer ? (
              <div className="space-y-6">
                {/* Current Score Display */}
                <div className={`text-center p-6 rounded-lg ${getScoreBg(selectedCustomer.currentScore)}`}>
                  <div className={`text-5xl font-bold ${getScoreColor(selectedCustomer.currentScore)}`}>
                    {selectedCustomer.currentScore}
                  </div>
                  <p className="text-sm text-muted-foreground mt-1">Current Score</p>
                  <div className="mt-2">
                    {getTrendBadge(selectedCustomer.trend, selectedCustomer.scoreChange)}
                  </div>
                </div>

                {/* Score Timeline */}
                <div className="space-y-3">
                  <h4 className="font-medium text-sm">Score Timeline</h4>
                  {selectedCustomer.history.map((entry, index) => {
                    const prevScore = selectedCustomer.history[index + 1]?.score;
                    const change = prevScore ? entry.score - prevScore : 0;

                    return (
                      <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                        <div className="flex items-center gap-3">
                          <div className={`h-10 w-10 rounded-full flex items-center justify-center ${getScoreBg(entry.score)}`}>
                            <span className={`font-bold text-sm ${getScoreColor(entry.score)}`}>
                              {entry.score}
                            </span>
                          </div>
                          <div>
                            <p className="text-sm font-medium">{entry.date}</p>
                            <p className="text-xs text-muted-foreground">{entry.bureau}</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          {change !== 0 && (
                            <span className={`text-xs ${change > 0 ? 'text-green-600' : 'text-red-600'}`}>
                              {change > 0 ? '+' : ''}{change}
                            </span>
                          )}
                          <Link to={`/admin/kyc/credit-bureau/report/${entry.reportId}`}>
                            <Button variant="ghost" size="sm">
                              <Eye className="h-3 w-3" />
                            </Button>
                          </Link>
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* Actions */}
                <div className="flex gap-2">
                  <Link to="/admin/kyc/credit-bureau" className="flex-1">
                    <Button variant="outline" className="w-full">
                      <CreditCard className="h-4 w-4 mr-2" />
                      New Pull
                    </Button>
                  </Link>
                  <Button variant="outline">
                    <Download className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ) : (
              <div className="text-center py-12 text-muted-foreground">
                <History className="h-16 w-16 mx-auto mb-4 opacity-50" />
                <p>Select a customer to view their score history</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
