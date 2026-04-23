import { useState } from 'react';
import { Link } from 'react-router-dom';
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
  Calendar,
  Lock,
  Unlock,
  CheckCircle,
  XCircle,
  Clock,
  AlertTriangle,
  Settings,
  Play,
  ChevronRight,
} from 'lucide-react';

// Mock periods data
const periods = [
  {
    id: 'FY2024-25-Q4-M3',
    name: 'March 2025',
    fiscalYear: 'FY 2024-25',
    quarter: 'Q4',
    startDate: '2025-03-01',
    endDate: '2025-03-31',
    status: 'FUTURE',
    glPostings: 0,
    pendingPostings: 0,
    isYearEnd: true,
  },
  {
    id: 'FY2024-25-Q4-M2',
    name: 'February 2025',
    fiscalYear: 'FY 2024-25',
    quarter: 'Q4',
    startDate: '2025-02-01',
    endDate: '2025-02-28',
    status: 'FUTURE',
    glPostings: 0,
    pendingPostings: 0,
    isYearEnd: false,
  },
  {
    id: 'FY2024-25-Q4-M1',
    name: 'January 2025',
    fiscalYear: 'FY 2024-25',
    quarter: 'Q4',
    startDate: '2025-01-01',
    endDate: '2025-01-31',
    status: 'OPEN',
    glPostings: 45,
    pendingPostings: 3,
    isYearEnd: false,
  },
  {
    id: 'FY2024-25-Q3-M3',
    name: 'December 2024',
    fiscalYear: 'FY 2024-25',
    quarter: 'Q3',
    startDate: '2024-12-01',
    endDate: '2024-12-31',
    status: 'SOFT_CLOSED',
    glPostings: 120,
    pendingPostings: 0,
    isYearEnd: false,
  },
  {
    id: 'FY2024-25-Q3-M2',
    name: 'November 2024',
    fiscalYear: 'FY 2024-25',
    quarter: 'Q3',
    startDate: '2024-11-01',
    endDate: '2024-11-30',
    status: 'CLOSED',
    glPostings: 98,
    pendingPostings: 0,
    isYearEnd: false,
  },
  {
    id: 'FY2024-25-Q3-M1',
    name: 'October 2024',
    fiscalYear: 'FY 2024-25',
    quarter: 'Q3',
    startDate: '2024-10-01',
    endDate: '2024-10-31',
    status: 'CLOSED',
    glPostings: 105,
    pendingPostings: 0,
    isYearEnd: false,
  },
  {
    id: 'FY2024-25-Q2-M3',
    name: 'September 2024',
    fiscalYear: 'FY 2024-25',
    quarter: 'Q2',
    startDate: '2024-09-01',
    endDate: '2024-09-30',
    status: 'CLOSED',
    glPostings: 112,
    pendingPostings: 0,
    isYearEnd: false,
  },
];

export default function PeriodManagement() {
  const [selectedPeriod, setSelectedPeriod] = useState<typeof periods[0] | null>(null);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'OPEN':
        return <Badge variant="default" className="bg-green-100 text-green-800"><Unlock className="h-3 w-3 mr-1" />Open</Badge>;
      case 'SOFT_CLOSED':
        return <Badge variant="secondary"><Clock className="h-3 w-3 mr-1" />Soft Closed</Badge>;
      case 'CLOSED':
        return <Badge variant="outline" className="bg-gray-100"><Lock className="h-3 w-3 mr-1" />Closed</Badge>;
      case 'FUTURE':
        return <Badge variant="outline"><Calendar className="h-3 w-3 mr-1" />Future</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  // Statistics
  const stats = {
    totalPeriods: periods.length,
    openPeriods: periods.filter(p => p.status === 'OPEN').length,
    softClosed: periods.filter(p => p.status === 'SOFT_CLOSED').length,
    closed: periods.filter(p => p.status === 'CLOSED').length,
    pendingPostings: periods.reduce((sum, p) => sum + p.pendingPostings, 0),
  };

  const currentPeriod = periods.find(p => p.status === 'OPEN');

  return (
    <div className="container mx-auto py-6 space-y-6">
      <PageHeader
        title="Period Management"
        subtitle="Manage accounting periods and period closures"
        actions={
          <Link to="/admin/accounting/period-close">
            <Button>
              <Lock className="h-4 w-4 mr-2" />
              Period Close Wizard
            </Button>
          </Link>
        }
      />

      {/* Current Period Banner */}
      {currentPeriod && (
        <Card className="bg-blue-50 border-blue-200">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="h-12 w-12 rounded-full bg-blue-100 flex items-center justify-center">
                  <Calendar className="h-6 w-6 text-blue-600" />
                </div>
                <div>
                  <h3 className="font-bold text-lg text-blue-900">Current Open Period</h3>
                  <p className="text-blue-700">{currentPeriod.name} ({currentPeriod.fiscalYear})</p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-sm text-blue-600">{currentPeriod.startDate} to {currentPeriod.endDate}</p>
                <p className="text-sm text-blue-700">{currentPeriod.glPostings} postings | {currentPeriod.pendingPostings} pending</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Total Periods</div>
            <div className="text-2xl font-bold mt-1">{stats.totalPeriods}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Open</div>
            <div className="text-2xl font-bold mt-1 text-green-600">{stats.openPeriods}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Soft Closed</div>
            <div className="text-2xl font-bold mt-1 text-yellow-600">{stats.softClosed}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Closed</div>
            <div className="text-2xl font-bold mt-1 text-gray-600">{stats.closed}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Pending Postings</div>
            <div className="text-2xl font-bold mt-1 text-orange-600">{stats.pendingPostings}</div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Periods List */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Accounting Periods</CardTitle>
            <CardDescription>FY 2024-25</CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Period</TableHead>
                  <TableHead>Quarter</TableHead>
                  <TableHead>Date Range</TableHead>
                  <TableHead className="text-right">Postings</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {periods.map((period) => (
                  <TableRow
                    key={period.id}
                    className={`cursor-pointer ${selectedPeriod?.id === period.id ? 'bg-muted/50' : 'hover:bg-muted/30'}`}
                    onClick={() => setSelectedPeriod(period)}
                  >
                    <TableCell>
                      <div className="flex items-center gap-2">
                        {period.isYearEnd && (
                          <Badge variant="outline" className="text-xs bg-purple-100 text-purple-800">
                            Year End
                          </Badge>
                        )}
                        <span className="font-medium">{period.name}</span>
                      </div>
                    </TableCell>
                    <TableCell>{period.quarter}</TableCell>
                    <TableCell className="text-sm">
                      {period.startDate} - {period.endDate}
                    </TableCell>
                    <TableCell className="text-right">
                      <span className="font-medium">{period.glPostings}</span>
                      {period.pendingPostings > 0 && (
                        <span className="text-orange-600 ml-1">({period.pendingPostings} pending)</span>
                      )}
                    </TableCell>
                    <TableCell>{getStatusBadge(period.status)}</TableCell>
                    <TableCell className="text-right">
                      <Button variant="ghost" size="sm">
                        <ChevronRight className="h-4 w-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        {/* Period Detail / Actions */}
        <Card>
          <CardHeader>
            <CardTitle>Period Actions</CardTitle>
          </CardHeader>
          <CardContent>
            {selectedPeriod ? (
              <div className="space-y-6">
                <div>
                  <h3 className="font-bold text-lg">{selectedPeriod.name}</h3>
                  <p className="text-sm text-muted-foreground">
                    {selectedPeriod.fiscalYear} - {selectedPeriod.quarter}
                  </p>
                  <div className="mt-2">
                    {getStatusBadge(selectedPeriod.status)}
                  </div>
                </div>

                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Start Date</span>
                    <span>{selectedPeriod.startDate}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">End Date</span>
                    <span>{selectedPeriod.endDate}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">GL Postings</span>
                    <span>{selectedPeriod.glPostings}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Pending Postings</span>
                    <span className={selectedPeriod.pendingPostings > 0 ? 'text-orange-600' : ''}>
                      {selectedPeriod.pendingPostings}
                    </span>
                  </div>
                </div>

                <div className="space-y-2">
                  {selectedPeriod.status === 'OPEN' && (
                    <>
                      <Link to={`/admin/accounting/period-close?period=${selectedPeriod.id}`} className="block">
                        <Button className="w-full" variant="outline">
                          <Lock className="h-4 w-4 mr-2" />
                          Soft Close Period
                        </Button>
                      </Link>
                      {selectedPeriod.pendingPostings > 0 && (
                        <div className="p-3 bg-yellow-50 rounded-lg text-sm text-yellow-800">
                          <AlertTriangle className="h-4 w-4 inline mr-1" />
                          {selectedPeriod.pendingPostings} pending postings must be processed before closing
                        </div>
                      )}
                    </>
                  )}

                  {selectedPeriod.status === 'SOFT_CLOSED' && (
                    <>
                      <Button className="w-full" variant="outline">
                        <Unlock className="h-4 w-4 mr-2" />
                        Reopen Period
                      </Button>
                      <Link to={`/admin/accounting/period-close?period=${selectedPeriod.id}&final=true`} className="block">
                        <Button className="w-full">
                          <Lock className="h-4 w-4 mr-2" />
                          Final Close
                        </Button>
                      </Link>
                    </>
                  )}

                  {selectedPeriod.status === 'CLOSED' && (
                    <div className="p-3 bg-gray-100 rounded-lg text-sm text-gray-700">
                      <Lock className="h-4 w-4 inline mr-1" />
                      This period is permanently closed and cannot be modified.
                    </div>
                  )}

                  {selectedPeriod.status === 'FUTURE' && (
                    <div className="p-3 bg-blue-50 rounded-lg text-sm text-blue-700">
                      <Calendar className="h-4 w-4 inline mr-1" />
                      This is a future period. It will become available when the current period is closed.
                    </div>
                  )}
                </div>

                <Link to={`/admin/accounting/gl-postings?period=${selectedPeriod.id}`}>
                  <Button variant="link" className="w-full">
                    View GL Postings
                    <ChevronRight className="h-4 w-4 ml-1" />
                  </Button>
                </Link>
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <Calendar className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>Select a period to view details and actions</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
