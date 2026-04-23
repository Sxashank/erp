import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { PageHeader } from '@/components/common/PageHeader';
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
  ArrowLeft,
  Calendar,
  Download,
  AlertTriangle,
  Clock,
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

// Maturity schedule data
const maturitySchedule = [
  {
    month: 'January 2025',
    investments: [
      { id: 'INV2023015', issuer: 'Government of India', description: 'G-Sec 6.84% 2024', maturityDate: '2025-01-15', faceValue: 15000000, coupon: 6.84 },
    ],
    totalMaturing: 15000000,
  },
  {
    month: 'February 2025',
    investments: [
      { id: 'INV2023020', issuer: 'SBI', description: 'SBI CD 7.0% 2025', maturityDate: '2025-02-10', faceValue: 10000000, coupon: 7.0 },
    ],
    totalMaturing: 10000000,
  },
  {
    month: 'March 2025',
    investments: [
      { id: 'INV2024025', issuer: 'HDFC Ltd', description: 'HDFC CP 6.8%', maturityDate: '2025-03-15', faceValue: 8000000, coupon: 6.8 },
      { id: 'INV2024026', issuer: 'LIC Housing', description: 'LIC HF NCD 7.5%', maturityDate: '2025-03-25', faceValue: 12000000, coupon: 7.5 },
    ],
    totalMaturing: 20000000,
  },
  {
    month: 'Q2 2025 (Apr-Jun)',
    investments: [
      { id: 'INV2024030', issuer: 'Government of India', description: 'T-Bill 91-day', maturityDate: '2025-04-20', faceValue: 5000000, coupon: 0 },
      { id: 'INV2024031', issuer: 'ICICI Bank', description: 'ICICI CD 7.25%', maturityDate: '2025-05-15', faceValue: 15000000, coupon: 7.25 },
      { id: 'INV2024032', issuer: 'Bajaj Finance', description: 'Bajaj NCD 8.0%', maturityDate: '2025-06-30', faceValue: 10000000, coupon: 8.0 },
    ],
    totalMaturing: 30000000,
  },
  {
    month: 'Q3 2025 (Jul-Sep)',
    investments: [
      { id: 'INV2024004', issuer: 'RBI', description: '364-day T-Bill', maturityDate: '2025-08-31', faceValue: 20000000, coupon: 0 },
    ],
    totalMaturing: 20000000,
  },
  {
    month: 'Q4 2025 (Oct-Dec)',
    investments: [],
    totalMaturing: 0,
  },
  {
    month: '2026',
    investments: [
      { id: 'INV2024040', issuer: 'Government of India', description: 'G-Sec 7.0% 2026', maturityDate: '2026-03-15', faceValue: 25000000, coupon: 7.0 },
      { id: 'INV2024041', issuer: 'State Bank of India', description: 'SBI Bond 7.5%', maturityDate: '2026-07-20', faceValue: 18000000, coupon: 7.5 },
    ],
    totalMaturing: 43000000,
  },
  {
    month: '2027',
    investments: [
      { id: 'INV2024002', issuer: 'HDFC Ltd', description: 'HDFC NCD 8.25% 2027', maturityDate: '2027-07-20', faceValue: 25000000, coupon: 8.25 },
    ],
    totalMaturing: 25000000,
  },
  {
    month: '>2027',
    investments: [
      { id: 'INV2024003', issuer: 'Government of Maharashtra', description: 'SDL 7.45% 2031', maturityDate: '2031-08-10', faceValue: 30000000, coupon: 7.45 },
      { id: 'INV2024001', issuer: 'Government of India', description: 'G-Sec 7.26% 2033', maturityDate: '2033-01-15', faceValue: 50000000, coupon: 7.26 },
    ],
    totalMaturing: 80000000,
  },
];

// Upcoming maturities (next 30 days)
const upcomingMaturities = [
  { id: 'INV2023015', issuer: 'Government of India', description: 'G-Sec 6.84% 2024', maturityDate: '2025-01-15', faceValue: 15000000, daysToMaturity: 0 },
];

export default function InvestmentMaturity() {
  const [periodFilter, setPeriodFilter] = useState('all');

  const totalMaturing = maturitySchedule.reduce((sum, m) => sum + m.totalMaturing, 0);
  const maturingIn30Days = upcomingMaturities.reduce((sum, m) => sum + m.faceValue, 0);
  const maturingIn90Days = maturitySchedule.slice(0, 3).reduce((sum, m) => sum + m.totalMaturing, 0);

  return (
    <div className="container mx-auto py-6 space-y-6">
      <PageHeader
        title="Maturity Schedule"
        subtitle="Investment maturity profile and upcoming redemptions"
        breadcrumbs={[
          { label: 'Investments', to: '/admin/treasury/investments' },
          { label: 'Maturity' },
        ]}
        actions={
          <Button variant="outline">
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
        }
      />

      {/* Upcoming Maturities Alert */}
      {upcomingMaturities.length > 0 && (
        <Card className="border-yellow-200 bg-yellow-50">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-yellow-800">
              <AlertTriangle className="h-5 w-5" />
              Upcoming Maturities (Next 30 Days)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {upcomingMaturities.map((investment) => (
                <div key={investment.id} className="flex items-center justify-between p-3 bg-white rounded-lg">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-sm">{investment.id}</span>
                      <Badge variant="outline">
                        <Clock className="h-3 w-3 mr-1" />
                        {investment.daysToMaturity === 0 ? 'Today' : `${investment.daysToMaturity} days`}
                      </Badge>
                    </div>
                    <p className="font-medium">{investment.issuer}</p>
                    <p className="text-sm text-muted-foreground">{investment.description}</p>
                  </div>
                  <div className="text-right">
                    <p className="font-bold">{formatCurrency(investment.faceValue)}</p>
                    <p className="text-sm text-muted-foreground">Maturity: {investment.maturityDate}</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Summary Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Maturing in 30 Days</div>
            <div className="text-2xl font-bold mt-1 text-yellow-600">{formatCurrency(maturingIn30Days)}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Maturing in 90 Days</div>
            <div className="text-2xl font-bold mt-1">{formatCurrency(maturingIn90Days)}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Maturing in 2025</div>
            <div className="text-2xl font-bold mt-1">
              {formatCurrency(maturitySchedule.slice(0, 5).reduce((sum, m) => sum + m.totalMaturing, 0))}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Total Portfolio</div>
            <div className="text-2xl font-bold mt-1">{formatCurrency(totalMaturing)}</div>
          </CardContent>
        </Card>
      </div>

      {/* Maturity Ladder */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Maturity Ladder</CardTitle>
              <CardDescription>Investment redemption schedule by time bucket</CardDescription>
            </div>
            <Select value={periodFilter} onValueChange={setPeriodFilter}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Period" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Periods</SelectItem>
                <SelectItem value="3m">Next 3 Months</SelectItem>
                <SelectItem value="6m">Next 6 Months</SelectItem>
                <SelectItem value="1y">Next 1 Year</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            {maturitySchedule.map((period, index) => (
              <div key={index} className="border rounded-lg p-4">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-bold text-lg">{period.month}</h3>
                  <Badge variant={period.totalMaturing > 0 ? 'default' : 'outline'}>
                    {formatCurrency(period.totalMaturing)}
                  </Badge>
                </div>
                {period.investments.length > 0 ? (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Investment ID</TableHead>
                        <TableHead>Issuer</TableHead>
                        <TableHead>Description</TableHead>
                        <TableHead>Maturity Date</TableHead>
                        <TableHead className="text-right">Coupon</TableHead>
                        <TableHead className="text-right">Face Value</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {period.investments.map((investment) => (
                        <TableRow key={investment.id}>
                          <TableCell className="font-mono text-sm">{investment.id}</TableCell>
                          <TableCell className="font-medium">{investment.issuer}</TableCell>
                          <TableCell>{investment.description}</TableCell>
                          <TableCell>{investment.maturityDate}</TableCell>
                          <TableCell className="text-right">{investment.coupon > 0 ? `${investment.coupon}%` : '-'}</TableCell>
                          <TableCell className="text-right font-medium">{formatCurrency(investment.faceValue)}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                ) : (
                  <p className="text-muted-foreground text-center py-4">No maturities scheduled</p>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
