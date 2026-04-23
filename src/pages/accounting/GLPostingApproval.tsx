import { useState } from 'react';
import { Link, useParams, useNavigate } from 'react-router-dom';
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
  CheckCircle,
  XCircle,
  Clock,
  User,
  Calendar,
  AlertTriangle,
  History,
  FileText,
} from 'lucide-react';

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(value);
};

// Mock pending postings for approval
const pendingPostings = [
  {
    id: '1',
    postingId: 'GLP2025010010',
    description: 'Provision for NPA - Q4',
    postingDate: '2025-01-14',
    period: 'Jan 2025',
    entries: [
      { id: '1', accountCode: '4012', accountName: 'Provision for NPA', debit: 850000, credit: 0 },
      { id: '2', accountCode: '2010', accountName: 'NPA Provision Reserve', debit: 0, credit: 850000 },
    ],
    totalDebit: 850000,
    totalCredit: 850000,
    createdBy: 'Risk Team',
    createdAt: '2025-01-14 16:45:00',
    priority: 'HIGH',
    remarks: 'Quarterly NPA provisioning as per RBI guidelines',
    attachments: ['npa_calculation.xlsx', 'provisioning_schedule.pdf'],
  },
  {
    id: '2',
    postingId: 'GLP2025010011',
    description: 'Interest Accrual - Gold Loans',
    postingDate: '2025-01-15',
    period: 'Jan 2025',
    entries: [
      { id: '1', accountCode: '1009', accountName: 'Interest Receivable - Gold Loans', debit: 320000, credit: 0 },
      { id: '2', accountCode: '3003', accountName: 'Interest Income - Gold Loans', debit: 0, credit: 320000 },
    ],
    totalDebit: 320000,
    totalCredit: 320000,
    createdBy: 'Finance Team',
    createdAt: '2025-01-15 09:30:00',
    priority: 'NORMAL',
    remarks: 'Monthly interest accrual for gold loan portfolio',
    attachments: [],
  },
  {
    id: '3',
    postingId: 'GLP2025010012',
    description: 'Salary Accrual - January 2025',
    postingDate: '2025-01-16',
    period: 'Jan 2025',
    entries: [
      { id: '1', accountCode: '4002', accountName: 'Salary Expense', debit: 1500000, credit: 0 },
      { id: '2', accountCode: '4005', accountName: 'Employer PF Contribution', debit: 180000, credit: 0 },
      { id: '3', accountCode: '2005', accountName: 'Salary Payable', debit: 0, credit: 1350000 },
      { id: '4', accountCode: '2006', accountName: 'TDS Payable', debit: 0, credit: 150000 },
      { id: '5', accountCode: '2007', accountName: 'PF Payable', debit: 0, credit: 180000 },
    ],
    totalDebit: 1680000,
    totalCredit: 1680000,
    createdBy: 'HR Finance',
    createdAt: '2025-01-16 11:00:00',
    priority: 'NORMAL',
    remarks: 'Monthly salary accrual with statutory deductions',
    attachments: ['payroll_summary.xlsx'],
  },
];

export default function GLPostingApproval() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [selectedPosting, setSelectedPosting] = useState<typeof pendingPostings[0] | null>(
    id ? pendingPostings.find(p => p.id === id) || null : null
  );
  const [approvalRemarks, setApprovalRemarks] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);

  const handleApprove = async () => {
    if (!selectedPosting) return;
    setIsProcessing(true);
    await new Promise(resolve => setTimeout(resolve, 1000));
    setIsProcessing(false);
    setSelectedPosting(null);
    setApprovalRemarks('');
  };

  const handleReject = async () => {
    if (!selectedPosting) return;
    setIsProcessing(true);
    await new Promise(resolve => setTimeout(resolve, 1000));
    setIsProcessing(false);
    setSelectedPosting(null);
    setApprovalRemarks('');
  };

  const getPriorityBadge = (priority: string) => {
    switch (priority) {
      case 'HIGH':
        return <Badge variant="destructive">High Priority</Badge>;
      case 'URGENT':
        return <Badge variant="destructive" className="bg-red-600">Urgent</Badge>;
      default:
        return <Badge variant="secondary">Normal</Badge>;
    }
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      <PageHeader
        title="GL Posting Approval"
        subtitle="Review and approve pending GL postings"
        breadcrumbs={[
          { label: 'GL Postings', to: '/admin/accounting/gl-postings' },
          { label: 'Approval' },
        ]}
      />

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Clock className="h-4 w-4" />
              Pending Approval
            </div>
            <div className="text-2xl font-bold mt-1 text-yellow-600">{pendingPostings.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <AlertTriangle className="h-4 w-4 text-red-500" />
              High Priority
            </div>
            <div className="text-2xl font-bold mt-1 text-red-600">
              {pendingPostings.filter(p => p.priority === 'HIGH' || p.priority === 'URGENT').length}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Total Debit Value</div>
            <div className="text-2xl font-bold mt-1">
              {formatCurrency(pendingPostings.reduce((sum, p) => sum + p.totalDebit, 0))}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Oldest Pending</div>
            <div className="text-2xl font-bold mt-1">2 days</div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Pending List */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle>Pending Postings</CardTitle>
            <CardDescription>{pendingPostings.length} awaiting approval</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {pendingPostings.map((posting) => (
                <div
                  key={posting.id}
                  className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                    selectedPosting?.id === posting.id ? 'border-primary bg-muted/50' : 'hover:bg-muted/30'
                  }`}
                  onClick={() => setSelectedPosting(posting)}
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="font-mono text-sm">{posting.postingId}</div>
                      <div className="font-medium text-sm mt-1">{posting.description}</div>
                      <div className="text-xs text-muted-foreground mt-1">
                        by {posting.createdBy} • {posting.postingDate}
                      </div>
                    </div>
                    {getPriorityBadge(posting.priority)}
                  </div>
                  <div className="mt-2 text-sm font-medium">
                    {formatCurrency(posting.totalDebit)}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Detail View */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Posting Details</CardTitle>
          </CardHeader>
          <CardContent>
            {selectedPosting ? (
              <div className="space-y-6">
                {/* Header Info */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <p className="text-muted-foreground">Posting ID</p>
                    <p className="font-mono font-medium">{selectedPosting.postingId}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Posting Date</p>
                    <p className="font-medium">{selectedPosting.postingDate}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Period</p>
                    <p className="font-medium">{selectedPosting.period}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Priority</p>
                    {getPriorityBadge(selectedPosting.priority)}
                  </div>
                </div>

                <div>
                  <p className="text-sm text-muted-foreground mb-1">Description</p>
                  <p className="font-medium">{selectedPosting.description}</p>
                </div>

                {selectedPosting.remarks && (
                  <div className="p-3 bg-muted rounded-lg">
                    <p className="text-sm text-muted-foreground mb-1">Remarks</p>
                    <p className="text-sm">{selectedPosting.remarks}</p>
                  </div>
                )}

                {/* Journal Entries */}
                <div>
                  <h4 className="font-medium mb-3">Journal Entries</h4>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Account</TableHead>
                        <TableHead className="text-right">Debit</TableHead>
                        <TableHead className="text-right">Credit</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {selectedPosting.entries.map((entry) => (
                        <TableRow key={entry.id}>
                          <TableCell>
                            <div className="font-mono text-sm">{entry.accountCode}</div>
                            <div className="text-sm text-muted-foreground">{entry.accountName}</div>
                          </TableCell>
                          <TableCell className="text-right font-medium">
                            {entry.debit > 0 ? formatCurrency(entry.debit) : '-'}
                          </TableCell>
                          <TableCell className="text-right font-medium">
                            {entry.credit > 0 ? formatCurrency(entry.credit) : '-'}
                          </TableCell>
                        </TableRow>
                      ))}
                      <TableRow className="bg-muted/50 font-bold">
                        <TableCell>Total</TableCell>
                        <TableCell className="text-right">{formatCurrency(selectedPosting.totalDebit)}</TableCell>
                        <TableCell className="text-right">{formatCurrency(selectedPosting.totalCredit)}</TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>

                  <div className="mt-3 p-3 bg-green-50 rounded-lg flex items-center gap-2">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                    <span className="text-sm text-green-800">Entries are balanced</span>
                  </div>
                </div>

                {/* Attachments */}
                {selectedPosting.attachments.length > 0 && (
                  <div>
                    <h4 className="font-medium mb-2">Attachments</h4>
                    <div className="flex flex-wrap gap-2">
                      {selectedPosting.attachments.map((file, index) => (
                        <Badge key={index} variant="outline" className="flex items-center gap-1">
                          <FileText className="h-3 w-3" />
                          {file}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}

                {/* Audit Info */}
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div className="flex items-center gap-2">
                    <User className="h-4 w-4 text-muted-foreground" />
                    <div>
                      <p className="text-muted-foreground">Created By</p>
                      <p className="font-medium">{selectedPosting.createdBy}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Calendar className="h-4 w-4 text-muted-foreground" />
                    <div>
                      <p className="text-muted-foreground">Created At</p>
                      <p className="font-medium">{selectedPosting.createdAt}</p>
                    </div>
                  </div>
                </div>

                {/* Approval Form */}
                <div className="border-t pt-6 space-y-4">
                  <div>
                    <Label>Approval Remarks</Label>
                    <Textarea
                      placeholder="Add remarks for this approval..."
                      value={approvalRemarks}
                      onChange={(e) => setApprovalRemarks(e.target.value)}
                      rows={3}
                      className="mt-2"
                    />
                  </div>

                  <div className="flex gap-2">
                    <Button
                      onClick={handleApprove}
                      disabled={isProcessing}
                      className="bg-green-600 hover:bg-green-700"
                    >
                      <CheckCircle className="h-4 w-4 mr-2" />
                      Approve & Post
                    </Button>
                    <Button
                      variant="destructive"
                      onClick={handleReject}
                      disabled={isProcessing}
                    >
                      <XCircle className="h-4 w-4 mr-2" />
                      Reject
                    </Button>
                    <Link to={`/admin/accounting/gl-postings/${selectedPosting.id}`}>
                      <Button variant="outline">
                        <History className="h-4 w-4 mr-2" />
                        View Full Details
                      </Button>
                    </Link>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center py-12 text-muted-foreground">
                <BookOpen className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>Select a posting from the list to review</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
