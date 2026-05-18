import { Edit, Printer, FileText, CheckCircle, XCircle, Clock } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { useToast } from '@/hooks/use-toast';
import { essReimbursementApi } from '@/services/essApi';

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(value);
};

interface ExpenseLineItem {
  id: string;
  expense_date: string;
  description: string;
  amount: number;
  approved_amount?: number | null;
  bill_number?: string | null;
  vendor_name?: string | null;
  attachment_url?: string | null;
}

interface ExpenseDetail {
  id: string;
  claim_number: string;
  claim_date: string;
  claim_type: string;
  category?: string | null;
  description: string;
  purpose?: string | null;
  claimed_amount: number;
  approved_amount?: number | null;
  status: string;
  created_at: string;
  approved_by?: string | null;
  approved_date?: string | null;
  rejection_reason?: string | null;
  payment_date?: string | null;
  payment_reference?: string | null;
  line_items: ExpenseLineItem[];
}

export default function ESSExpenseDetail() {
  const navigate = useNavigate();
  const { id } = useParams();
  const { toast } = useToast();
  const [expense, setExpense] = useState<ExpenseDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    const loadExpense = async () => {
      if (!id) return;
      setIsLoading(true);
      try {
        const response = await essReimbursementApi.getClaim(id);
        if (mounted) setExpense(response.data);
      } catch (error) {
        if (mounted) {
          toast({
            title: 'Unable to load expense claim',
            description: 'Check your ESS session and reimbursement access.',
            variant: 'destructive',
          });
        }
      } finally {
        if (mounted) setIsLoading(false);
      }
    };
    loadExpense();
    return () => {
      mounted = false;
    };
  }, [id, toast]);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'DRAFT':
        return <Badge variant="outline">Draft</Badge>;
      case 'PENDING':
      case 'SUBMITTED':
      case 'PENDING_APPROVAL':
        return (
          <Badge variant="secondary" className="bg-yellow-100 text-yellow-800">
            Pending Approval
          </Badge>
        );
      case 'APPROVED':
        return (
          <Badge variant="default" className="bg-blue-500">
            Approved
          </Badge>
        );
      case 'REJECTED':
        return <Badge variant="destructive">Rejected</Badge>;
      case 'PAID':
        return (
          <Badge variant="default" className="bg-green-500">
            Paid
          </Badge>
        );
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Expense claim"
          subtitle="Loading expense claim"
          breadcrumbs={[{ label: 'Expenses', to: '/ess/expenses' }, { label: 'Loading' }]}
        />
        <Card>
          <CardContent className="py-10 text-center text-sm text-muted-foreground">
            Loading expense claim...
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!expense) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Expense claim not found"
          subtitle="The claim may have been removed or is not available to your ESS account"
          breadcrumbs={[{ label: 'Expenses', to: '/ess/expenses' }, { label: 'Not found' }]}
        />
        <Card>
          <CardContent className="py-10 text-center">
            <Button variant="outline" onClick={() => navigate('/ess/expenses')}>
              Back to expenses
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

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
      <PageHeader
        title={expense.claim_number}
        subtitle={expense.purpose || expense.description}
        breadcrumbs={[{ label: 'Expenses', to: '/ess/expenses' }, { label: expense.claim_number }]}
        actions={
          <div className="flex gap-2">
            <Button variant="outline">
              <Printer className="mr-2 h-4 w-4" />
              Print
            </Button>
            {expense.status === 'DRAFT' && (
              <Button asChild>
                <a href={`/ess/expenses/${id}/edit`}>
                  <Edit className="mr-2 h-4 w-4" />
                  Edit
                </a>
              </Button>
            )}
          </div>
        }
      />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Main Content */}
        <div className="space-y-6 lg:col-span-2">
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
                  <div className="font-medium">{expense.claim_number}</div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">Submitted Date</div>
                  <div className="font-medium">{expense.claim_date}</div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">Project</div>
                  <div className="font-medium">{expense.category || '-'}</div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">Approved By</div>
                  <div className="font-medium">{expense.approved_by || '-'}</div>
                </div>
                <div className="col-span-2">
                  <div className="text-sm text-muted-foreground">Purpose</div>
                  <div className="font-medium">{expense.purpose || expense.description}</div>
                </div>
                {expense.rejection_reason && (
                  <div className="col-span-2">
                    <div className="text-sm text-muted-foreground">Rejection Reason</div>
                    <div className="font-medium">{expense.rejection_reason}</div>
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
                  {expense.line_items.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={5} className="py-8 text-center text-sm text-muted-foreground">
                        No expense line items found.
                      </TableCell>
                    </TableRow>
                  ) : expense.line_items.map((line) => (
                    <TableRow key={line.id}>
                      <TableCell>{line.expense_date}</TableCell>
                      <TableCell>
                        <Badge variant="outline">{expense.category || expense.claim_type}</Badge>
                      </TableCell>
                      <TableCell>{line.description}</TableCell>
                      <TableCell className="text-center">
                        {line.attachment_url ? (
                          <Button variant="ghost" size="sm">
                            <FileText className="h-4 w-4 text-blue-500" />
                          </Button>
                        ) : (
                          <span className="text-sm text-muted-foreground">No receipt</span>
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
                      {formatCurrency(expense.claimed_amount)}
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
                  {formatCurrency(expense.approved_amount ?? expense.claimed_amount)}
                </div>
                <div className="mt-1 text-sm text-muted-foreground">
                  {expense.line_items.length} expense items
                </div>
              </div>
              <Separator className="my-4" />
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Status</span>
                  {getStatusBadge(expense.status)}
                </div>
                {expense.approved_date && (
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Approved On</span>
                    <span>{expense.approved_date}</span>
                  </div>
                )}
                {expense.payment_date && (
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Paid On</span>
                    <span>{expense.payment_date}</span>
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
                {[
                  { date: expense.created_at, action: 'Created', user: 'You', remarks: 'Expense claim created' },
                  expense.approved_date
                    ? { date: expense.approved_date, action: expense.status, user: expense.approved_by || 'Approver', remarks: expense.rejection_reason || '' }
                    : null,
                  expense.payment_date
                    ? { date: expense.payment_date, action: 'Paid', user: 'Payroll', remarks: expense.payment_reference || '' }
                    : null,
                ].filter((item): item is { date: string; action: string; user: string; remarks: string } => Boolean(item)).map((item, index: number) => (
                  <div key={index} className="flex gap-3">
                    <div className="mt-1">{getTimelineIcon(item.action)}</div>
                    <div className="flex-1">
                      <div className="text-sm font-medium">{item.action}</div>
                      <div className="text-xs text-muted-foreground">
                        {item.user} - {item.date}
                      </div>
                      {item.remarks && (
                        <div className="mt-1 text-sm text-muted-foreground">{item.remarks}</div>
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
