import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { PageHeader } from '@/components/common/PageHeader';
import { Input } from '@/components/ui/input';
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
  Briefcase,
  Plus,
  Search,
  Filter,
  Eye,
  Download,
  TrendingUp,
  Calendar,
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

// Investment portfolio data
const investments = [
  {
    id: '1',
    investmentId: 'INV2024001',
    type: 'Government Securities',
    issuer: 'Government of India',
    description: 'G-Sec 7.26% 2033',
    faceValue: 50000000,
    bookValue: 49500000,
    marketValue: 51200000,
    coupon: 7.26,
    ytm: 7.1,
    purchaseDate: '2024-06-15',
    maturityDate: '2033-01-15',
    status: 'ACTIVE',
    category: 'HTM',
  },
  {
    id: '2',
    investmentId: 'INV2024002',
    type: 'Corporate Bonds',
    issuer: 'HDFC Ltd',
    description: 'HDFC NCD 8.25% 2027',
    faceValue: 25000000,
    bookValue: 25200000,
    marketValue: 25800000,
    coupon: 8.25,
    ytm: 8.0,
    purchaseDate: '2024-07-20',
    maturityDate: '2027-07-20',
    status: 'ACTIVE',
    category: 'AFS',
  },
  {
    id: '3',
    investmentId: 'INV2024003',
    type: 'State Development Loans',
    issuer: 'Government of Maharashtra',
    description: 'SDL 7.45% 2031',
    faceValue: 30000000,
    bookValue: 29800000,
    marketValue: 30500000,
    coupon: 7.45,
    ytm: 7.3,
    purchaseDate: '2024-08-10',
    maturityDate: '2031-08-10',
    status: 'ACTIVE',
    category: 'HTM',
  },
  {
    id: '4',
    investmentId: 'INV2024004',
    type: 'Treasury Bills',
    issuer: 'RBI',
    description: '364-day T-Bill',
    faceValue: 20000000,
    bookValue: 19250000,
    marketValue: 19450000,
    coupon: 0,
    ytm: 6.8,
    purchaseDate: '2024-09-01',
    maturityDate: '2025-08-31',
    status: 'ACTIVE',
    category: 'HFT',
  },
  {
    id: '5',
    investmentId: 'INV2023015',
    type: 'Government Securities',
    issuer: 'Government of India',
    description: 'G-Sec 6.84% 2024',
    faceValue: 15000000,
    bookValue: 15000000,
    marketValue: 15000000,
    coupon: 6.84,
    ytm: 6.84,
    purchaseDate: '2023-12-15',
    maturityDate: '2024-12-15',
    status: 'MATURED',
    category: 'HTM',
  },
];

// Portfolio summary
const portfolioSummary = {
  totalFaceValue: 140000000,
  totalBookValue: 138750000,
  totalMarketValue: 141950000,
  unrealizedGain: 3200000,
  avgYTM: 7.2,
  avgDuration: 4.8,
};

export default function InvestmentList() {
  const [searchTerm, setSearchTerm] = useState('');
  const [typeFilter, setTypeFilter] = useState('all');
  const [categoryFilter, setCategoryFilter] = useState('all');

  const filteredInvestments = investments.filter((inv) => {
    const matchesSearch = inv.investmentId.toLowerCase().includes(searchTerm.toLowerCase()) ||
      inv.issuer.toLowerCase().includes(searchTerm.toLowerCase()) ||
      inv.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesType = typeFilter === 'all' || inv.type === typeFilter;
    const matchesCategory = categoryFilter === 'all' || inv.category === categoryFilter;
    return matchesSearch && matchesType && matchesCategory;
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'ACTIVE':
        return <Badge variant="default" className="bg-green-100 text-green-800">Active</Badge>;
      case 'MATURED':
        return <Badge variant="secondary">Matured</Badge>;
      case 'SOLD':
        return <Badge variant="outline">Sold</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const getCategoryBadge = (category: string) => {
    switch (category) {
      case 'HTM':
        return <Badge variant="outline">HTM</Badge>;
      case 'AFS':
        return <Badge variant="secondary">AFS</Badge>;
      case 'HFT':
        return <Badge variant="default">HFT</Badge>;
      default:
        return <Badge variant="outline">{category}</Badge>;
    }
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      <PageHeader
        title="Investment Portfolio"
        subtitle="Manage treasury investments and securities"
        actions={
          <Link to="/admin/treasury/investments/new">
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              New Investment
            </Button>
          </Link>
        }
      />

      {/* Portfolio Summary */}
      <div className="grid grid-cols-1 md:grid-cols-6 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Face Value</div>
            <div className="text-2xl font-bold mt-1">{formatCurrency(portfolioSummary.totalFaceValue)}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Book Value</div>
            <div className="text-2xl font-bold mt-1">{formatCurrency(portfolioSummary.totalBookValue)}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Market Value</div>
            <div className="text-2xl font-bold mt-1">{formatCurrency(portfolioSummary.totalMarketValue)}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Unrealized Gain</div>
            <div className="text-2xl font-bold mt-1 text-green-600">
              +{formatCurrency(portfolioSummary.unrealizedGain)}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Avg. YTM</div>
            <div className="text-2xl font-bold mt-1">{portfolioSummary.avgYTM}%</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Avg. Duration</div>
            <div className="text-2xl font-bold mt-1">{portfolioSummary.avgDuration} yrs</div>
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
                placeholder="Search by ID, issuer, or description..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="max-w-sm"
              />
            </div>
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-muted-foreground" />
              <Select value={typeFilter} onValueChange={setTypeFilter}>
                <SelectTrigger className="w-48">
                  <SelectValue placeholder="Type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Types</SelectItem>
                  <SelectItem value="Government Securities">Government Securities</SelectItem>
                  <SelectItem value="Corporate Bonds">Corporate Bonds</SelectItem>
                  <SelectItem value="State Development Loans">State Development Loans</SelectItem>
                  <SelectItem value="Treasury Bills">Treasury Bills</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Select value={categoryFilter} onValueChange={setCategoryFilter}>
              <SelectTrigger className="w-32">
                <SelectValue placeholder="Category" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All</SelectItem>
                <SelectItem value="HTM">HTM</SelectItem>
                <SelectItem value="AFS">AFS</SelectItem>
                <SelectItem value="HFT">HFT</SelectItem>
              </SelectContent>
            </Select>
            <Button variant="outline">
              <Download className="h-4 w-4 mr-2" />
              Export
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Investments Table */}
      <Card>
        <CardHeader>
          <CardTitle>Investment Holdings</CardTitle>
          <CardDescription>
            Showing {filteredInvestments.length} of {investments.length} investments
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Investment</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Category</TableHead>
                <TableHead className="text-right">Face Value</TableHead>
                <TableHead className="text-right">Market Value</TableHead>
                <TableHead className="text-right">Coupon</TableHead>
                <TableHead className="text-right">YTM</TableHead>
                <TableHead>Maturity</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredInvestments.map((investment) => (
                <TableRow key={investment.id}>
                  <TableCell>
                    <div>
                      <div className="font-mono text-sm">{investment.investmentId}</div>
                      <div className="font-medium">{investment.issuer}</div>
                      <div className="text-xs text-muted-foreground">{investment.description}</div>
                    </div>
                  </TableCell>
                  <TableCell>{investment.type}</TableCell>
                  <TableCell>{getCategoryBadge(investment.category)}</TableCell>
                  <TableCell className="text-right font-medium">{formatCurrency(investment.faceValue)}</TableCell>
                  <TableCell className="text-right">
                    <div>{formatCurrency(investment.marketValue)}</div>
                    {investment.marketValue > investment.bookValue && (
                      <div className="text-xs text-green-600">
                        +{formatCurrency(investment.marketValue - investment.bookValue)}
                      </div>
                    )}
                    {investment.marketValue < investment.bookValue && (
                      <div className="text-xs text-red-600">
                        -{formatCurrency(investment.bookValue - investment.marketValue)}
                      </div>
                    )}
                  </TableCell>
                  <TableCell className="text-right">{investment.coupon > 0 ? `${investment.coupon}%` : '-'}</TableCell>
                  <TableCell className="text-right">{investment.ytm}%</TableCell>
                  <TableCell>{investment.maturityDate}</TableCell>
                  <TableCell>{getStatusBadge(investment.status)}</TableCell>
                  <TableCell className="text-right">
                    <Link to={`/admin/treasury/investments/${investment.id}`}>
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

      {/* Quick Links */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Link to="/admin/treasury/investments/maturity">
          <Card className="hover:bg-muted/50 cursor-pointer transition-colors">
            <CardContent className="pt-6">
              <Calendar className="h-8 w-8 text-primary mb-2" />
              <h3 className="font-medium">Maturity Schedule</h3>
              <p className="text-sm text-muted-foreground">View upcoming maturities</p>
            </CardContent>
          </Card>
        </Link>
        <Link to="/admin/treasury/investments/valuation">
          <Card className="hover:bg-muted/50 cursor-pointer transition-colors">
            <CardContent className="pt-6">
              <TrendingUp className="h-8 w-8 text-primary mb-2" />
              <h3 className="font-medium">Portfolio Valuation</h3>
              <p className="text-sm text-muted-foreground">Mark-to-market analysis</p>
            </CardContent>
          </Card>
        </Link>
        <Link to="/admin/treasury/risk-dashboard">
          <Card className="hover:bg-muted/50 cursor-pointer transition-colors">
            <CardContent className="pt-6">
              <Briefcase className="h-8 w-8 text-primary mb-2" />
              <h3 className="font-medium">Risk Analysis</h3>
              <p className="text-sm text-muted-foreground">Investment risk metrics</p>
            </CardContent>
          </Card>
        </Link>
      </div>
    </div>
  );
}
