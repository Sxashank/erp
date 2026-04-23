import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { PageHeader } from '@/components/common/PageHeader';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Progress } from '@/components/ui/progress';
import {
  ArrowLeft,
  Users,
  Search,
  Building,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Download,
  Filter,
} from 'lucide-react';

const formatCurrency = (value: number) => {
  if (value >= 10000000) {
    return `₹${(value / 10000000).toFixed(2)} Cr`;
  }
  if (value >= 100000) {
    return `₹${(value / 100000).toFixed(2)} L`;
  }
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(value);
};

// Top counterparty exposures
const counterpartyExposures = [
  {
    id: '1',
    name: 'ABC Industries Ltd',
    type: 'Corporate',
    rating: 'A+',
    exposure: 85000000,
    limit: 100000000,
    utilization: 85,
    products: ['Term Loan', 'Working Capital'],
    sector: 'Manufacturing',
    trend: 'stable',
  },
  {
    id: '2',
    name: 'XYZ Real Estate',
    type: 'Corporate',
    rating: 'BBB',
    exposure: 75000000,
    limit: 80000000,
    utilization: 94,
    products: ['Project Finance'],
    sector: 'Real Estate',
    trend: 'up',
  },
  {
    id: '3',
    name: 'HDFC Bank',
    type: 'Bank',
    rating: 'AAA',
    exposure: 65000000,
    limit: 150000000,
    utilization: 43,
    products: ['Interbank Deposit'],
    sector: 'BFSI',
    trend: 'stable',
  },
  {
    id: '4',
    name: 'PQR Textiles',
    type: 'Corporate',
    rating: 'A-',
    exposure: 55000000,
    limit: 70000000,
    utilization: 79,
    products: ['Term Loan', 'LC/BG'],
    sector: 'Textiles',
    trend: 'down',
  },
  {
    id: '5',
    name: 'LMN Pharma',
    type: 'Corporate',
    rating: 'AA-',
    exposure: 48000000,
    limit: 60000000,
    utilization: 80,
    products: ['Working Capital'],
    sector: 'Pharmaceuticals',
    trend: 'stable',
  },
];

// Sector exposures
const sectorExposures = [
  { sector: 'Manufacturing', exposure: 280000000, limit: 350000000, percent: 80, count: 45 },
  { sector: 'Real Estate', exposure: 185000000, limit: 200000000, percent: 93, count: 12 },
  { sector: 'BFSI', exposure: 150000000, limit: 200000000, percent: 75, count: 8 },
  { sector: 'Textiles', exposure: 125000000, limit: 150000000, percent: 83, count: 22 },
  { sector: 'Services', exposure: 110000000, limit: 180000000, percent: 61, count: 35 },
  { sector: 'Infrastructure', exposure: 95000000, limit: 150000000, percent: 63, count: 6 },
];

// Rating-wise distribution
const ratingDistribution = [
  { rating: 'AAA/AA+', exposure: 180000000, percent: 18, count: 5 },
  { rating: 'AA/AA-', exposure: 250000000, percent: 25, count: 12 },
  { rating: 'A+/A', exposure: 320000000, percent: 32, count: 35 },
  { rating: 'A-/BBB+', exposure: 180000000, percent: 18, count: 28 },
  { rating: 'BBB/BBB-', exposure: 70000000, percent: 7, count: 15 },
];

// Limit breaches
const limitBreaches = [
  { counterparty: 'XYZ Real Estate', type: 'Single Counterparty', breach: 5000000, date: '2025-01-15' },
  { counterparty: 'Real Estate Sector', type: 'Sector Limit', breach: 15000000, date: '2025-01-14' },
];

export default function CounterpartyRisk() {
  const [searchTerm, setSearchTerm] = useState('');

  const getUtilizationColor = (percent: number) => {
    if (percent >= 90) return 'text-red-600';
    if (percent >= 75) return 'text-yellow-600';
    return 'text-green-600';
  };

  const getRatingBadge = (rating: string) => {
    if (rating.startsWith('AAA') || rating.startsWith('AA')) {
      return <Badge variant="default" className="bg-green-100 text-green-800">{rating}</Badge>;
    }
    if (rating.startsWith('A')) {
      return <Badge variant="secondary">{rating}</Badge>;
    }
    return <Badge variant="outline">{rating}</Badge>;
  };

  const filteredExposures = counterpartyExposures.filter(
    (c) => c.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
           c.sector.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="container mx-auto py-6 space-y-6">
      <PageHeader
        title="Counterparty Risk Management"
        subtitle="Credit concentration and exposure monitoring"
        breadcrumbs={[
          { label: 'Risk Dashboard', to: '/admin/treasury/risk-dashboard' },
          { label: 'Counterparty Risk' },
        ]}
        actions={
          <Button variant="outline">
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
        }
      />

      {/* Breach Alerts */}
      {limitBreaches.length > 0 && (
        <Card className="border-red-200 bg-red-50">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-red-800">
              <AlertTriangle className="h-5 w-5" />
              Limit Breaches
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {limitBreaches.map((breach, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-white rounded-lg">
                  <div>
                    <p className="font-medium">{breach.counterparty}</p>
                    <p className="text-sm text-muted-foreground">{breach.type}</p>
                  </div>
                  <div className="text-right">
                    <p className="font-bold text-red-600">{formatCurrency(breach.breach)}</p>
                    <p className="text-xs text-muted-foreground">{breach.date}</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Total Exposure</div>
            <div className="text-2xl font-bold mt-1">
              {formatCurrency(counterpartyExposures.reduce((sum, c) => sum + c.exposure, 0))}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Top 10 Concentration</div>
            <div className="text-2xl font-bold mt-1">45%</div>
            <p className="text-xs text-muted-foreground">of total portfolio</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">High Utilization ({'>'} 80%)</div>
            <div className="text-2xl font-bold mt-1 text-yellow-600">
              {counterpartyExposures.filter(c => c.utilization > 80).length}
            </div>
            <p className="text-xs text-muted-foreground">counterparties</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Limit Breaches</div>
            <div className="text-2xl font-bold mt-1 text-red-600">{limitBreaches.length}</div>
            <p className="text-xs text-muted-foreground">active breaches</p>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="counterparty" className="space-y-4">
        <TabsList>
          <TabsTrigger value="counterparty">Top Counterparties</TabsTrigger>
          <TabsTrigger value="sector">Sector Exposure</TabsTrigger>
          <TabsTrigger value="rating">Rating Distribution</TabsTrigger>
        </TabsList>

        <TabsContent value="counterparty">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Top Counterparty Exposures</CardTitle>
                  <CardDescription>Largest single counterparty exposures</CardDescription>
                </div>
                <div className="flex items-center gap-2">
                  <Search className="h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Search counterparties..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-64"
                  />
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Counterparty</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Rating</TableHead>
                    <TableHead>Sector</TableHead>
                    <TableHead className="text-right">Exposure</TableHead>
                    <TableHead className="text-right">Limit</TableHead>
                    <TableHead className="text-right">Utilization</TableHead>
                    <TableHead>Trend</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredExposures.map((counterparty) => (
                    <TableRow key={counterparty.id}>
                      <TableCell>
                        <div className="font-medium">{counterparty.name}</div>
                        <div className="text-xs text-muted-foreground">
                          {counterparty.products.join(', ')}
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline">{counterparty.type}</Badge>
                      </TableCell>
                      <TableCell>{getRatingBadge(counterparty.rating)}</TableCell>
                      <TableCell>{counterparty.sector}</TableCell>
                      <TableCell className="text-right font-medium">
                        {formatCurrency(counterparty.exposure)}
                      </TableCell>
                      <TableCell className="text-right">
                        {formatCurrency(counterparty.limit)}
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-2">
                          <Progress value={counterparty.utilization} className="w-16 h-2" />
                          <span className={`font-bold ${getUtilizationColor(counterparty.utilization)}`}>
                            {counterparty.utilization}%
                          </span>
                        </div>
                      </TableCell>
                      <TableCell>
                        {counterparty.trend === 'up' && <TrendingUp className="h-4 w-4 text-red-500" />}
                        {counterparty.trend === 'down' && <TrendingDown className="h-4 w-4 text-green-500" />}
                        {counterparty.trend === 'stable' && <span className="text-muted-foreground">-</span>}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="sector">
          <Card>
            <CardHeader>
              <CardTitle>Sector-wise Exposure</CardTitle>
              <CardDescription>Credit concentration by industry sector</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {sectorExposures.map((sector) => (
                  <div key={sector.sector} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div>
                        <span className="font-medium">{sector.sector}</span>
                        <span className="text-sm text-muted-foreground ml-2">({sector.count} counterparties)</span>
                      </div>
                      <div className="text-right">
                        <span className={`font-bold ${getUtilizationColor(sector.percent)}`}>{sector.percent}%</span>
                        <span className="text-sm text-muted-foreground ml-2">({formatCurrency(sector.exposure)})</span>
                      </div>
                    </div>
                    <Progress value={sector.percent} className="h-3" />
                    <div className="flex justify-between text-xs text-muted-foreground">
                      <span>Limit: {formatCurrency(sector.limit)}</span>
                      <span>Available: {formatCurrency(sector.limit - sector.exposure)}</span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="rating">
          <Card>
            <CardHeader>
              <CardTitle>Rating-wise Distribution</CardTitle>
              <CardDescription>Portfolio distribution by credit rating</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Rating Band</TableHead>
                    <TableHead className="text-right">Exposure</TableHead>
                    <TableHead className="text-right">% of Portfolio</TableHead>
                    <TableHead className="text-right">No. of Counterparties</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {ratingDistribution.map((item) => (
                    <TableRow key={item.rating}>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          {getRatingBadge(item.rating.split('/')[0])}
                          <span className="font-medium">{item.rating}</span>
                        </div>
                      </TableCell>
                      <TableCell className="text-right font-medium">{formatCurrency(item.exposure)}</TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-2">
                          <Progress value={item.percent} className="w-20 h-2" />
                          <span>{item.percent}%</span>
                        </div>
                      </TableCell>
                      <TableCell className="text-right">{item.count}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

              <div className="mt-6 p-4 bg-blue-50 rounded-lg">
                <p className="text-sm text-blue-800">
                  <strong>Portfolio Quality:</strong> 75% of the portfolio is rated A- or above,
                  indicating strong credit quality. The BBB rated exposure is within acceptable limits.
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
