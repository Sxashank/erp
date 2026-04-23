import { useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
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
  ArrowLeft,
  BookOpen,
  Edit,
  CheckCircle,
  XCircle,
  Clock,
  Download,
  Printer,
  User,
  Calendar,
  FileText,
  Send,
} from 'lucide-react';

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(value);
};

// Mock posting detail
const postingDetail = {
  id: '1',
  postingId: 'GLP2025010001',
  description: 'Interest Accrual - January 2025',
  postingDate: '2025-01-15',
  period: 'Jan 2025',
  reference: 'REF/INT/2025/001',
  narration: 'Monthly interest accrual for all active loan accounts as per system calculation. This includes accrued interest on business loans, vehicle loans, and gold loans.',
  status: 'POSTED',
  createdBy: 'Finance Team',
  createdAt: '2025-01-15 10:30:00',
  approvedBy: 'CFO',
  approvedAt: '2025-01-15 14:00:00',
  postedAt: '2025-01-15 14:05:00',

  entries: [
    {
      id: '1',
      accountCode: '1007',
      accountName: 'Interest Receivable - Business Loans',
      description: 'Interest accrual for business loans',
      costCenter: 'Head Office',
      debit: 580000,
      credit: 0,
    },
    {
      id: '2',
      accountCode: '1008',
      accountName: 'Interest Receivable - Vehicle Loans',
      description: 'Interest accrual for vehicle loans',
      costCenter: 'Head Office',
      debit: 420000,
      credit: 0,
    },
    {
      id: '3',
      accountCode: '1009',
      accountName: 'Interest Receivable - Gold Loans',
      description: 'Interest accrual for gold loans',
      costCenter: 'Head Office',
      debit: 250000,
      credit: 0,
    },
    {
      id: '4',
      accountCode: '3001',
      accountName: 'Interest Income - Business Loans',
      description: 'Interest income recognition',
      costCenter: 'Head Office',
      debit: 0,
      credit: 580000,
    },
    {
      id: '5',
      accountCode: '3002',
      accountName: 'Interest Income - Vehicle Loans',
      description: 'Interest income recognition',
      costCenter: 'Head Office',
      debit: 0,
      credit: 420000,
    },
    {
      id: '6',
      accountCode: '3003',
      accountName: 'Interest Income - Gold Loans',
      description: 'Interest income recognition',
      costCenter: 'Head Office',
      debit: 0,
      credit: 250000,
    },
  ],

  history: [
    { action: 'POSTED', by: 'System', at: '2025-01-15 14:05:00', remarks: 'Auto-posted after approval' },
    { action: 'APPROVED', by: 'CFO', at: '2025-01-15 14:00:00', remarks: 'Verified and approved' },
    { action: 'SUBMITTED', by: 'Finance Team', at: '2025-01-15 10:35:00', remarks: 'Submitted for approval' },
    { action: 'CREATED', by: 'Finance Team', at: '2025-01-15 10:30:00', remarks: 'Initial creation' },
  ],
};

export default function GLPostingDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [showApprovalForm, setShowApprovalForm] = useState(false);
  const [approvalRemarks, setApprovalRemarks] = useState('');

  const totalDebit = postingDetail.entries.reduce((sum, e) => sum + e.debit, 0);
  const totalCredit = postingDetail.entries.reduce((sum, e) => sum + e.credit, 0);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'POSTED':
        return <Badge variant="default" className="bg-green-100 text-green-800"><CheckCircle className="h-3 w-3 mr-1" />Posted</Badge>;
      case 'PENDING_APPROVAL':
        return <Badge variant="secondary"><Clock className="h-3 w-3 mr-1" />Pending Approval</Badge>;
      case 'DRAFT':
        return <Badge variant="outline"><Edit className="h-3 w-3 mr-1" />Draft</Badge>;
      case 'REJECTED':
        return <Badge variant="destructive"><XCircle className="h-3 w-3 mr-1" />Rejected</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const handleApprove = () => {
    // Handle approval
    navigate('/admin/accounting/gl-postings');
  };

  const handleReject = () => {
    // Handle rejection
    navigate('/admin/accounting/gl-postings');
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      <PageHeader
        title={postingDetail.postingId}
        subtitle={postingDetail.description}
        breadcrumbs={[
          { label: 'GL Postings', to: '/admin/accounting/gl-postings' },
          { label: postingDetail.postingId },
        ]}
        actions={
          <div className="flex items-center gap-2">
            {getStatusBadge(postingDetail.status)}
            <Button variant="outline" size="sm">
              <Printer className="h-4 w-4 mr-2" />
              Print
            </Button>
            <Button variant="outline" size="sm">
              <Download className="h-4 w-4 mr-2" />
              Export
            </Button>
          </div>
        }
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Posting Details */}
          <Card>
            <CardHeader>
              <CardTitle>Posting Details</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <p className="text-muted-foreground">Posting ID</p>
                  <p className="font-mono font-medium">{postingDetail.postingId}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Posting Date</p>
                  <p className="font-medium">{postingDetail.postingDate}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Accounting Period</p>
                  <p className="font-medium">{postingDetail.period}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Reference</p>
                  <p className="font-medium">{postingDetail.reference || 'N/A'}</p>
                </div>
              </div>
              {postingDetail.narration && (
                <div className="mt-4 p-3 bg-muted rounded-lg">
                  <p className="text-sm text-muted-foreground mb-1">Narration</p>
                  <p className="text-sm">{postingDetail.narration}</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Journal Entries */}
          <Card>
            <CardHeader>
              <CardTitle>Journal Entries</CardTitle>
              <CardDescription>{postingDetail.entries.length} line items</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Account</TableHead>
                    <TableHead>Description</TableHead>
                    <TableHead>Cost Center</TableHead>
                    <TableHead className="text-right">Debit</TableHead>
                    <TableHead className="text-right">Credit</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {postingDetail.entries.map((entry) => (
                    <TableRow key={entry.id}>
                      <TableCell>
                        <div>
                          <div className="font-mono text-sm">{entry.accountCode}</div>
                          <div className="text-sm text-muted-foreground">{entry.accountName}</div>
                        </div>
                      </TableCell>
                      <TableCell className="text-sm">{entry.description}</TableCell>
                      <TableCell className="text-sm">{entry.costCenter}</TableCell>
                      <TableCell className="text-right font-medium">
                        {entry.debit > 0 ? formatCurrency(entry.debit) : '-'}
                      </TableCell>
                      <TableCell className="text-right font-medium">
                        {entry.credit > 0 ? formatCurrency(entry.credit) : '-'}
                      </TableCell>
                    </TableRow>
                  ))}
                  <TableRow className="bg-muted/50 font-bold">
                    <TableCell colSpan={3} className="text-right">Total</TableCell>
                    <TableCell className="text-right">{formatCurrency(totalDebit)}</TableCell>
                    <TableCell className="text-right">{formatCurrency(totalCredit)}</TableCell>
                  </TableRow>
                </TableBody>
              </Table>

              <div className="mt-4 p-4 bg-green-50 rounded-lg flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <CheckCircle className="h-5 w-5 text-green-600" />
                  <span className="text-green-800 font-medium">Entries are balanced</span>
                </div>
                <span className="text-green-700">
                  {formatCurrency(totalDebit)}
                </span>
              </div>
            </CardContent>
          </Card>

          {/* Approval Actions (if pending) */}
          {postingDetail.status === 'PENDING_APPROVAL' && (
            <Card>
              <CardHeader>
                <CardTitle>Approval Action</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>Remarks</Label>
                  <Textarea
                    placeholder="Add approval remarks..."
                    value={approvalRemarks}
                    onChange={(e) => setApprovalRemarks(e.target.value)}
                    rows={3}
                  />
                </div>
                <div className="flex gap-2">
                  <Button onClick={handleApprove} className="bg-green-600 hover:bg-green-700">
                    <CheckCircle className="h-4 w-4 mr-2" />
                    Approve & Post
                  </Button>
                  <Button variant="destructive" onClick={handleReject}>
                    <XCircle className="h-4 w-4 mr-2" />
                    Reject
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Summary */}
          <Card>
            <CardHeader>
              <CardTitle>Summary</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-muted-foreground">Total Debit</span>
                <span className="font-bold text-lg">{formatCurrency(totalDebit)}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-muted-foreground">Total Credit</span>
                <span className="font-bold text-lg">{formatCurrency(totalCredit)}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-muted-foreground">Line Items</span>
                <span className="font-bold">{postingDetail.entries.length}</span>
              </div>
            </CardContent>
          </Card>

          {/* Audit Information */}
          <Card>
            <CardHeader>
              <CardTitle>Audit Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 text-sm">
              <div className="flex items-center gap-2">
                <User className="h-4 w-4 text-muted-foreground" />
                <div>
                  <p className="text-muted-foreground">Created By</p>
                  <p className="font-medium">{postingDetail.createdBy}</p>
                  <p className="text-xs text-muted-foreground">{postingDetail.createdAt}</p>
                </div>
              </div>
              {postingDetail.approvedBy && (
                <div className="flex items-center gap-2">
                  <CheckCircle className="h-4 w-4 text-green-500" />
                  <div>
                    <p className="text-muted-foreground">Approved By</p>
                    <p className="font-medium">{postingDetail.approvedBy}</p>
                    <p className="text-xs text-muted-foreground">{postingDetail.approvedAt}</p>
                  </div>
                </div>
              )}
              {postingDetail.postedAt && (
                <div className="flex items-center gap-2">
                  <FileText className="h-4 w-4 text-blue-500" />
                  <div>
                    <p className="text-muted-foreground">Posted At</p>
                    <p className="text-xs text-muted-foreground">{postingDetail.postedAt}</p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* History */}
          <Card>
            <CardHeader>
              <CardTitle>Activity History</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {postingDetail.history.map((entry, index) => (
                  <div key={index} className="flex gap-3 text-sm">
                    <div className="flex flex-col items-center">
                      <div className={`h-2 w-2 rounded-full ${index === 0 ? 'bg-green-500' : 'bg-gray-300'}`} />
                      {index < postingDetail.history.length - 1 && (
                        <div className="w-px h-full bg-gray-200" />
                      )}
                    </div>
                    <div className="flex-1 pb-4">
                      <p className="font-medium">{entry.action}</p>
                      <p className="text-muted-foreground">by {entry.by}</p>
                      <p className="text-xs text-muted-foreground">{entry.at}</p>
                      {entry.remarks && (
                        <p className="text-xs mt-1 p-2 bg-muted rounded">{entry.remarks}</p>
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
