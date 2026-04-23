import { useNavigate, useParams } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Separator } from '@/components/ui/separator';
import { ArrowLeft, Edit, Printer, Receipt, FileText, CheckCircle, XCircle, Clock } from 'lucide-react';

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(value);
};

// Mock data
const expense = {
  id: '1',
  expenseNumber: 'EXP-2025-001',
  date: '2025-01-15',
  purpose: 'Client visit to Mumbai - ABC Corp meeting',
  projectName: 'Project Alpha',
  status: 'APPROVED',
  totalAmount: 12500,
  remarks: 'Meeting with client for project requirements discussion',
  submittedDate: '2025-01-15',
  approvedBy: 'Rahul Sharma',
  approvedDate: '2025-01-16',
  paidDate: null,
  lines: [
    { id: '1', date: '2025-01-14', category: 'Travel', description: 'Flight ticket - DEL to BOM', amount: 5500, hasReceipt: true },
    { id: '2', date: '2025-01-14', category: 'Travel', description: 'Cab from airport to hotel', amount: 800, hasReceipt: true },
    { id: '3', date: '2025-01-14', category: 'Accommodation', description: 'Hotel stay - 1 night', amount: 4500, hasReceipt: true },
    { id: '4', date: '2025-01-15', category: 'Food & Entertainment', description: 'Client lunch meeting', amount: 1200, hasReceipt: true },
    { id: '5', date: '2025-01-15', category: 'Travel', description: 'Cab to airport', amount: 500, hasReceipt: false },
  ],
  timeline: [
    { date: '2025-01-15 10:30', action: 'Created', user: 'You', remarks: 'Expense claim created' },
    { date: '2025-01-15 10:35', action: 'Submitted', user: 'You', remarks: 'Submitted for approval' },
    { date: '2025-01-16 14:20', action: 'Approved', user: 'Rahul Sharma', remarks: 'Approved. Please attach missing receipt for cab.' },
  ],
};

export default function ESSExpenseDetail() {
  const navigate = useNavigate();
  const { id } = useParams();

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'DRAFT':
        return <Badge variant="outline">Draft</Badge>;
      case 'PENDING':
        return <Badge variant="secondary" className="bg-yellow-100 text-yellow-800">Pending Approval</Badge>;
      case 'APPROVED':
        return <Badge variant="default" className="bg-blue-500">Approved</Badge>;
      case 'REJECTED':
        return <Badge variant="destructive">Rejected</Badge>;
      case 'PAID':
        return <Badge variant="default" className="bg-green-500">Paid</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const getTimelineIcon = (action: string) => {
    switch (action) {
      case 'Created':
      case 'Submitted':
        return <Clock className="h-4 w-4 text-blue-500" />;
      case 'Approved':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'Rejected':
        return <XCircle className="h-4 w-4 text-red-500" />;
      default:
        return <Clock className="h-4 w-4 text-gray-500" />;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => navigate(-1)}>
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <Receipt className="h-6 w-6" />
              {expense.expenseNumber}
            </h1>
            <p className="text-muted-foreground">{expense.purpose}</p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="outline">
            <Printer className="h-4 w-4 mr-2" />
            Print
          </Button>
          {expense.status === 'DRAFT' && (
            <Button asChild>
              <a href={`/ess/expenses/${id}/edit`}>
                <Edit className="h-4 w-4 mr-2" />
                Edit
              </a>
            </Button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Expense Details */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>Expense Details</span>
                {getStatusBadge(expense.status)}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-sm text-muted-foreground">Expense Number</div>
                  <div className="font-medium">{expense.expenseNumber}</div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">Submitted Date</div>
                  <div className="font-medium">{expense.submittedDate}</div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">Project</div>
                  <div className="font-medium">{expense.projectName || '-'}</div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">Approved By</div>
                  <div className="font-medium">{expense.approvedBy || '-'}</div>
                </div>
                <div className="col-span-2">
                  <div className="text-sm text-muted-foreground">Purpose</div>
                  <div className="font-medium">{expense.purpose}</div>
                </div>
                {expense.remarks && (
                  <div className="col-span-2">
                    <div className="text-sm text-muted-foreground">Remarks</div>
                    <div className="font-medium">{expense.remarks}</div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Expense Lines */}
          <Card>
            <CardHeader>
              <CardTitle>Expense Items</CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Date</TableHead>
                    <TableHead>Category</TableHead>
                    <TableHead>Description</TableHead>
                    <TableHead className="text-center">Receipt</TableHead>
                    <TableHead className="text-right">Amount</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {expense.lines.map((line) => (
                    <TableRow key={line.id}>
                      <TableCell>{line.date}</TableCell>
                      <TableCell>
                        <Badge variant="outline">{line.category}</Badge>
                      </TableCell>
                      <TableCell>{line.description}</TableCell>
                      <TableCell className="text-center">
                        {line.hasReceipt ? (
                          <Button variant="ghost" size="sm">
                            <FileText className="h-4 w-4 text-blue-500" />
                          </Button>
                        ) : (
                          <span className="text-muted-foreground text-sm">No receipt</span>
                        )}
                      </TableCell>
                      <TableCell className="text-right font-medium">
                        {formatCurrency(line.amount)}
                      </TableCell>
                    </TableRow>
                  ))}
                  <TableRow className="bg-muted/50">
                    <TableCell colSpan={4} className="font-medium">
                      Total
                    </TableCell>
                    <TableCell className="text-right font-bold">
                      {formatCurrency(expense.totalAmount)}
                    </TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Summary Card */}
          <Card>
            <CardHeader>
              <CardTitle>Summary</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-center">
                <div className="text-3xl font-bold text-primary">
                  {formatCurrency(expense.totalAmount)}
                </div>
                <div className="text-sm text-muted-foreground mt-1">
                  {expense.lines.length} expense items
                </div>
              </div>
              <Separator className="my-4" />
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Status</span>
                  {getStatusBadge(expense.status)}
                </div>
                {expense.approvedDate && (
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Approved On</span>
                    <span>{expense.approvedDate}</span>
                  </div>
                )}
                {expense.paidDate && (
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Paid On</span>
                    <span>{expense.paidDate}</span>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Timeline */}
          <Card>
            <CardHeader>
              <CardTitle>Timeline</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {expense.timeline.map((item, index) => (
                  <div key={index} className="flex gap-3">
                    <div className="mt-1">{getTimelineIcon(item.action)}</div>
                    <div className="flex-1">
                      <div className="font-medium text-sm">{item.action}</div>
                      <div className="text-xs text-muted-foreground">
                        {item.user} - {item.date}
                      </div>
                      {item.remarks && (
                        <div className="text-sm text-muted-foreground mt-1">
                          {item.remarks}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
