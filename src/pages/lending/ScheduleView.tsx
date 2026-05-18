import {
  ArrowLeft,
  Calendar,
  Download,
  RefreshCw,
  CheckCircle,
  Clock,
  AlertTriangle,
  Edit,
  Printer,
} from 'lucide-react';
import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { formatCurrency, formatDate } from '@/lib/utils';

// Schedule preview shell. Wires to GET /lending/schedules/{loan_account_id}
// once that endpoint + hook land; for now renders the empty state.
const loanDetails = {
  loan_account: '',
  entity: '',
  product: '',
  sanctioned_amount: 0,
  disbursed_amount: 0,
  interest_rate: 0,
  tenure_months: 0,
  emi_amount: 0,
  first_emi_date: '',
  last_emi_date: '',
  calculation_method: 'REDUCING',
  moratorium_months: 0,
};

interface ScheduleRow {
  installment: number;
  due_date: string;
  opening_balance: number;
  principal: number;
  interest: number;
  emi: number;
  closing_balance: number;
  status: string;
  paid_date: string | null;
  paid_amount: number;
  overdue_days?: number;
}

const scheduleData: ScheduleRow[] = [];

const scheduleSummary = {
  total_emi: 0,
  paid_emi: 0,
  overdue_emi: 0,
  upcoming_emi: 0,
  total_principal: 0,
  paid_principal: 0,
  total_interest: 0,
  paid_interest: 0,
  progress_percentage: 0,
};

const getStatusBadge = (status: string, overdueDays?: number) => {
  switch (status) {
    case 'PAID':
      return (
        <Badge variant="default" className="bg-green-600">
          <CheckCircle className="mr-1 h-3 w-3" />
          Paid
        </Badge>
      );
    case 'OVERDUE':
      return (
        <Badge variant="destructive">
          <AlertTriangle className="mr-1 h-3 w-3" />
          Overdue {overdueDays ? `(${overdueDays}d)` : ''}
        </Badge>
      );
    case 'UPCOMING':
      return (
        <Badge variant="secondary">
          <Clock className="mr-1 h-3 w-3" />
          Upcoming
        </Badge>
      );
    default:
      return <Badge variant="outline">Future</Badge>;
  }
};

export default function ScheduleView() {
  const navigate = useNavigate();
  const { id } = useParams();
  const [activeTab, setActiveTab] = useState('schedule');

  const paidAmount = scheduleData
    .filter((s) => s.status === 'PAID')
    .reduce((sum, s) => sum + s.paid_amount, 0);
  const overdueAmount = scheduleData
    .filter((s) => s.status === 'OVERDUE')
    .reduce((sum, s) => sum + s.emi, 0);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Loan Schedule"
        subtitle={`${loanDetails.loan_account} - ${loanDetails.entity}`}
        breadcrumbs={[
          { label: 'Loan Accounts', to: '/admin/lending/loan-accounts' },
          { label: loanDetails.loan_account },
          { label: 'Schedule' },
        ]}
        actions={
          <div className="flex gap-2">
            <Button variant="outline">
              <Printer className="mr-2 h-4 w-4" />
              Print
            </Button>
            <Button variant="outline">
              <Download className="mr-2 h-4 w-4" />
              Export
            </Button>
            <Button onClick={() => navigate(`/admin/lending/schedules/${id}/modify`)}>
              <Edit className="mr-2 h-4 w-4" />
              Modify Schedule
            </Button>
          </div>
        }
      />

      {/* Loan Summary */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-5">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Sanctioned</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-xl font-bold">{formatCurrency(loanDetails.sanctioned_amount)}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Interest Rate
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-xl font-bold">{loanDetails.interest_rate}% p.a.</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Tenure</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-xl font-bold">{loanDetails.tenure_months} months</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">EMI Amount</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-xl font-bold">{formatCurrency(loanDetails.emi_amount)}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Method</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-xl font-bold">
              {loanDetails.calculation_method === 'REDUCING' ? 'Reducing' : 'Flat'}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Progress Overview */}
      <Card>
        <CardContent className="pt-6">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Repayment Progress</p>
              <p className="text-2xl font-bold">{scheduleSummary.progress_percentage}%</p>
            </div>
            <div className="text-right">
              <p className="text-sm text-muted-foreground">EMIs Completed</p>
              <p className="text-xl font-bold">
                {scheduleSummary.paid_emi} / {scheduleSummary.total_emi}
              </p>
            </div>
          </div>
          <Progress value={scheduleSummary.progress_percentage} className="h-3" />
          <div className="mt-6 grid grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{scheduleSummary.paid_emi}</div>
              <div className="text-xs text-muted-foreground">Paid</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-red-600">{scheduleSummary.overdue_emi}</div>
              <div className="text-xs text-muted-foreground">Overdue</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">1</div>
              <div className="text-xs text-muted-foreground">Upcoming</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-600">
                {scheduleSummary.upcoming_emi - 1}
              </div>
              <div className="text-xs text-muted-foreground">Future</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Schedule Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <Card>
          <CardHeader>
            <TabsList>
              <TabsTrigger value="schedule">Full Schedule</TabsTrigger>
              <TabsTrigger value="summary">Summary</TabsTrigger>
              <TabsTrigger value="history">Payment History</TabsTrigger>
            </TabsList>
          </CardHeader>
          <CardContent>
            <TabsContent value="schedule" className="mt-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="text-center">Inst.</TableHead>
                    <TableHead>Due Date</TableHead>
                    <TableHead className="text-right">Opening Bal.</TableHead>
                    <TableHead className="text-right">Principal</TableHead>
                    <TableHead className="text-right">Interest</TableHead>
                    <TableHead className="text-right">EMI</TableHead>
                    <TableHead className="text-right">Closing Bal.</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {scheduleData.map((row) => (
                    <TableRow
                      key={row.installment}
                      className={
                        row.status === 'OVERDUE'
                          ? 'bg-red-50'
                          : row.status === 'UPCOMING'
                            ? 'bg-blue-50'
                            : ''
                      }
                    >
                      <TableCell className="text-center font-medium">{row.installment}</TableCell>
                      <TableCell>{formatDate(row.due_date)}</TableCell>
                      <TableCell className="text-right">
                        {formatCurrency(row.opening_balance)}
                      </TableCell>
                      <TableCell className="text-right text-green-600">
                        {formatCurrency(row.principal)}
                      </TableCell>
                      <TableCell className="text-right text-orange-600">
                        {formatCurrency(row.interest)}
                      </TableCell>
                      <TableCell className="text-right font-medium">
                        {formatCurrency(row.emi)}
                      </TableCell>
                      <TableCell className="text-right">
                        {formatCurrency(row.closing_balance)}
                      </TableCell>
                      <TableCell>{getStatusBadge(row.status, row.overdue_days)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TabsContent>

            <TabsContent value="summary" className="mt-0">
              <div className="grid grid-cols-2 gap-6">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">Principal Summary</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Total Principal</span>
                      <span className="font-medium">
                        {formatCurrency(scheduleSummary.total_principal)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Principal Paid</span>
                      <span className="font-medium text-green-600">
                        {formatCurrency(scheduleSummary.paid_principal)}
                      </span>
                    </div>
                    <div className="flex justify-between border-t pt-4">
                      <span className="font-medium">Principal Outstanding</span>
                      <span className="font-bold">
                        {formatCurrency(
                          scheduleSummary.total_principal - scheduleSummary.paid_principal,
                        )}
                      </span>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">Interest Summary</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Total Interest</span>
                      <span className="font-medium">
                        {formatCurrency(scheduleSummary.total_interest)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Interest Paid</span>
                      <span className="font-medium text-green-600">
                        {formatCurrency(scheduleSummary.paid_interest)}
                      </span>
                    </div>
                    <div className="flex justify-between border-t pt-4">
                      <span className="font-medium">Interest Remaining</span>
                      <span className="font-bold">
                        {formatCurrency(
                          scheduleSummary.total_interest - scheduleSummary.paid_interest,
                        )}
                      </span>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            <TabsContent value="history" className="mt-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Installment</TableHead>
                    <TableHead>Due Date</TableHead>
                    <TableHead>Payment Date</TableHead>
                    <TableHead className="text-right">EMI Amount</TableHead>
                    <TableHead className="text-right">Paid Amount</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {scheduleData
                    .filter((s) => s.status === 'PAID' || s.status === 'OVERDUE')
                    .map((row) => (
                      <TableRow key={row.installment}>
                        <TableCell className="font-medium">EMI {row.installment}</TableCell>
                        <TableCell>{formatDate(row.due_date)}</TableCell>
                        <TableCell>{row.paid_date ? formatDate(row.paid_date) : '-'}</TableCell>
                        <TableCell className="text-right">{formatCurrency(row.emi)}</TableCell>
                        <TableCell className="text-right">
                          {row.paid_amount > 0 ? (
                            <span className="text-green-600">
                              {formatCurrency(row.paid_amount)}
                            </span>
                          ) : (
                            <span className="text-red-600">-</span>
                          )}
                        </TableCell>
                        <TableCell>{getStatusBadge(row.status, row.overdue_days)}</TableCell>
                      </TableRow>
                    ))}
                </TableBody>
              </Table>
            </TabsContent>
          </CardContent>
        </Card>
      </Tabs>
    </div>
  );
}
