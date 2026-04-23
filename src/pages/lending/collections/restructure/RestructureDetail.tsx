import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, Edit, CheckCircle, XCircle, Clock, Play, FileText, ArrowRight, Calendar } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { AmountDisplay } from '@/components/lending/common/AmountDisplay';
import { DateDisplay } from '@/components/lending/common/DateDisplay';

interface LoanRestructureDetail {
  id: string;
  restructureReference: string;
  loanAccountId: string;
  loanAccountNumber: string;
  entityName: string;
  restructureType: string;
  status: string;
  proposalDate: string;
  // Pre-restructure
  preOutstandingPrincipal: number;
  preOutstandingInterest: number;
  preInterestRate: number;
  preTenureMonths: number;
  preEmiAmount: number;
  preMaturityDate: string;
  // Post-restructure
  postOutstandingPrincipal: number;
  postInterestRate: number;
  postTenureMonths: number;
  postEmiAmount: number;
  postMaturityDate: string;
  // Moratorium
  moratoriumMonths: number;
  moratoriumStartDate: string | null;
  moratoriumEndDate: string | null;
  moratoriumInterestTreatment: string | null;
  // Waivers
  interestWaived: number;
  penalWaived: number;
  principalConvertedToFitl: number;
  // Classification
  isStandardRestructure: boolean;
  downgradeRequired: boolean;
  // Conditions
  preConditions: string | null;
  postConditions: string | null;
  // Approval
  approvedById: string | null;
  approvedByName: string | null;
  approvalDate: string | null;
  approvalAuthority: string | null;
  // Implementation
  implementationDate: string | null;
  newScheduleGenerated: boolean;
  // Other
  justification: string;
  remarks: string | null;
  createdAt: string;
  updatedAt: string;
}

// Mock data
const mockRestructureDetail: LoanRestructureDetail = {
  id: '1',
  restructureReference: 'RESTR/2025/00001',
  loanAccountId: '1',
  loanAccountNumber: 'SMFC/TL/CHN/2023/L00034',
  entityName: 'Southern Motors Corp',
  restructureType: 'COMPREHENSIVE',
  status: 'PENDING_APPROVAL',
  proposalDate: '2025-01-15',
  preOutstandingPrincipal: 130250000,
  preOutstandingInterest: 5250000,
  preInterestRate: 12.5,
  preTenureMonths: 60,
  preEmiAmount: 2950000,
  preMaturityDate: '2028-06-15',
  postOutstandingPrincipal: 130250000,
  postInterestRate: 11.0,
  postTenureMonths: 84,
  postEmiAmount: 2100000,
  postMaturityDate: '2032-01-15',
  moratoriumMonths: 6,
  moratoriumStartDate: '2025-02-01',
  moratoriumEndDate: '2025-07-31',
  moratoriumInterestTreatment: 'CAPITALIZE',
  interestWaived: 2500000,
  penalWaived: 750000,
  principalConvertedToFitl: 0,
  isStandardRestructure: true,
  downgradeRequired: false,
  preConditions: '1. Submission of all pending financials\n2. Personal guarantee from promoters\n3. Additional collateral coverage of 1.5x',
  postConditions: '1. Quarterly stock audit\n2. No dividend distribution for 2 years\n3. Monthly cash flow statements',
  approvedById: null,
  approvedByName: null,
  approvalDate: null,
  approvalAuthority: null,
  implementationDate: null,
  newScheduleGenerated: false,
  justification: 'Borrower facing temporary cash flow issues due to delayed receivables from major customers. The company has secured new orders worth Rs. 50 Cr which will be executed over the next 18 months. The restructure will provide breathing room while maintaining asset quality.',
  remarks: 'Recommended by RM after detailed analysis of borrower situation.',
  createdAt: '2025-01-15T10:30:00Z',
  updatedAt: '2025-01-15T10:30:00Z',
};

const statusConfig: Record<string, { label: string; color: string; icon: React.ElementType }> = {
  DRAFT: { label: 'Draft', color: 'bg-gray-100 text-gray-700', icon: FileText },
  PROPOSED: { label: 'Proposed', color: 'bg-blue-100 text-blue-700', icon: FileText },
  PENDING_APPROVAL: { label: 'Pending Approval', color: 'bg-yellow-100 text-yellow-700', icon: Clock },
  APPROVED: { label: 'Approved', color: 'bg-green-100 text-green-700', icon: CheckCircle },
  REJECTED: { label: 'Rejected', color: 'bg-red-100 text-red-700', icon: XCircle },
  IMPLEMENTED: { label: 'Implemented', color: 'bg-green-200 text-green-800', icon: CheckCircle },
  CANCELLED: { label: 'Cancelled', color: 'bg-gray-200 text-gray-700', icon: XCircle },
};

const restructureTypeLabels: Record<string, string> = {
  TENURE_EXTENSION: 'Tenure Extension',
  EMI_REDUCTION: 'EMI Reduction',
  MORATORIUM: 'Moratorium',
  RATE_REDUCTION: 'Rate Reduction',
  PRINCIPAL_HAIRCUT: 'Principal Haircut',
  INTEREST_WAIVER: 'Interest Waiver',
  COMPREHENSIVE: 'Comprehensive',
  COVID_RESTRUCTURE: 'COVID Restructure',
};

export default function RestructureDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const restructure = mockRestructureDetail;

  const status = statusConfig[restructure.status];
  const StatusIcon = status.icon;

  const rateChange = restructure.postInterestRate - restructure.preInterestRate;
  const tenureChange = restructure.postTenureMonths - restructure.preTenureMonths;
  const totalWaiver = restructure.interestWaived + restructure.penalWaived;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => navigate(-1)}>
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-semibold">{restructure.restructureReference}</h1>
              <Badge variant="outline" className={status.color}>
                <StatusIcon className="h-3 w-3 mr-1" />
                {status.label}
              </Badge>
            </div>
            <p className="text-muted-foreground">
              {restructure.loanAccountNumber} - {restructure.entityName}
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          {restructure.status === 'DRAFT' && (
            <Button variant="outline" onClick={() => navigate(`/admin/lending/collections/restructure/${id}/edit`)}>
              <Edit className="mr-2 h-4 w-4" />
              Edit
            </Button>
          )}
          {restructure.status === 'PENDING_APPROVAL' && (
            <Button onClick={() => navigate(`/admin/lending/collections/restructure/${id}/approve`)}>
              <CheckCircle className="mr-2 h-4 w-4" />
              Review & Approve
            </Button>
          )}
          {restructure.status === 'APPROVED' && (
            <Button>
              <Play className="mr-2 h-4 w-4" />
              Implement Restructure
            </Button>
          )}
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Restructure Type</CardTitle>
          </CardHeader>
          <CardContent>
            <Badge variant="secondary" className="text-sm">
              {restructureTypeLabels[restructure.restructureType]}
            </Badge>
            <p className="text-xs text-muted-foreground mt-1">
              Proposed on <DateDisplay date={restructure.proposalDate} />
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Rate Impact</CardTitle>
          </CardHeader>
          <CardContent>
            <p className={`text-2xl font-bold ${rateChange < 0 ? 'text-green-600' : rateChange > 0 ? 'text-red-600' : ''}`}>
              {rateChange > 0 ? '+' : ''}{rateChange.toFixed(2)}%
            </p>
            <p className="text-xs text-muted-foreground">
              {restructure.preInterestRate}% → {restructure.postInterestRate}%
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Tenure Extension</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{tenureChange > 0 ? '+' : ''}{tenureChange} months</p>
            <p className="text-xs text-muted-foreground">
              {restructure.preTenureMonths} → {restructure.postTenureMonths} months
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Waiver</CardTitle>
          </CardHeader>
          <CardContent>
            <AmountDisplay amount={totalWaiver} className="text-2xl font-bold text-red-600" />
            <p className="text-xs text-muted-foreground">Interest + Penal waived</p>
          </CardContent>
        </Card>
      </div>

      {/* Terms Comparison */}
      <Card>
        <CardHeader>
          <CardTitle>Terms Comparison</CardTitle>
          <CardDescription>Pre and post restructure terms side by side</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-8">
            {/* Pre Column */}
            <div className="space-y-4">
              <h3 className="font-semibold text-lg border-b pb-2">Pre-Restructure</h3>
              <div>
                <p className="text-xs text-muted-foreground">Principal Outstanding</p>
                <AmountDisplay amount={restructure.preOutstandingPrincipal} className="font-semibold" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Interest Outstanding</p>
                <AmountDisplay amount={restructure.preOutstandingInterest} className="font-semibold" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Interest Rate</p>
                <p className="font-semibold">{restructure.preInterestRate}% p.a.</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Tenure</p>
                <p className="font-semibold">{restructure.preTenureMonths} months</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">EMI Amount</p>
                <AmountDisplay amount={restructure.preEmiAmount} className="font-semibold" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Maturity Date</p>
                <DateDisplay date={restructure.preMaturityDate} className="font-semibold" />
              </div>
            </div>

            {/* Arrow */}
            <div className="flex items-center justify-center">
              <ArrowRight className="h-8 w-8 text-muted-foreground" />
            </div>

            {/* Post Column */}
            <div className="space-y-4">
              <h3 className="font-semibold text-lg border-b pb-2">Post-Restructure</h3>
              <div>
                <p className="text-xs text-muted-foreground">Principal Outstanding</p>
                <AmountDisplay amount={restructure.postOutstandingPrincipal} className="font-semibold" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Interest Outstanding</p>
                <p className="font-semibold text-green-600">Waived: <AmountDisplay amount={restructure.interestWaived} /></p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Interest Rate</p>
                <p className={`font-semibold ${rateChange < 0 ? 'text-green-600' : ''}`}>
                  {restructure.postInterestRate}% p.a.
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Tenure</p>
                <p className="font-semibold">{restructure.postTenureMonths} months</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">EMI Amount</p>
                <AmountDisplay amount={restructure.postEmiAmount} className="font-semibold text-green-600" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Maturity Date</p>
                <DateDisplay date={restructure.postMaturityDate} className="font-semibold" />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Moratorium Details */}
      {restructure.moratoriumMonths > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calendar className="h-5 w-5" />
              Moratorium Details
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-4 gap-4">
              <div>
                <p className="text-xs text-muted-foreground">Duration</p>
                <p className="font-semibold">{restructure.moratoriumMonths} months</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Start Date</p>
                {restructure.moratoriumStartDate ? (
                  <DateDisplay date={restructure.moratoriumStartDate} className="font-semibold" />
                ) : (
                  <p className="text-muted-foreground">-</p>
                )}
              </div>
              <div>
                <p className="text-xs text-muted-foreground">End Date</p>
                {restructure.moratoriumEndDate ? (
                  <DateDisplay date={restructure.moratoriumEndDate} className="font-semibold" />
                ) : (
                  <p className="text-muted-foreground">-</p>
                )}
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Interest Treatment</p>
                <Badge variant="outline">
                  {restructure.moratoriumInterestTreatment === 'CAPITALIZE' && 'Capitalize'}
                  {restructure.moratoriumInterestTreatment === 'DEFER' && 'Defer'}
                  {restructure.moratoriumInterestTreatment === 'WAIVE' && 'Waive'}
                </Badge>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Waivers */}
      <Card>
        <CardHeader>
          <CardTitle>Waivers & Relief</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4">
            <div className="p-4 bg-muted rounded-lg">
              <p className="text-xs text-muted-foreground">Interest Waived</p>
              <AmountDisplay amount={restructure.interestWaived} className="text-xl font-semibold text-red-600" />
            </div>
            <div className="p-4 bg-muted rounded-lg">
              <p className="text-xs text-muted-foreground">Penal Interest Waived</p>
              <AmountDisplay amount={restructure.penalWaived} className="text-xl font-semibold text-red-600" />
            </div>
            <div className="p-4 bg-muted rounded-lg">
              <p className="text-xs text-muted-foreground">Principal to FITL</p>
              <AmountDisplay amount={restructure.principalConvertedToFitl} className="text-xl font-semibold" />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Classification */}
      <Card>
        <CardHeader>
          <CardTitle>Classification & Compliance</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-6">
            <div className="flex items-center gap-2">
              {restructure.isStandardRestructure ? (
                <CheckCircle className="h-5 w-5 text-green-600" />
              ) : (
                <XCircle className="h-5 w-5 text-red-600" />
              )}
              <span>Standard Restructure (RBI Compliant)</span>
            </div>
            <Separator orientation="vertical" className="h-6" />
            <div className="flex items-center gap-2">
              {restructure.downgradeRequired ? (
                <XCircle className="h-5 w-5 text-red-600" />
              ) : (
                <CheckCircle className="h-5 w-5 text-green-600" />
              )}
              <span>Downgrade {restructure.downgradeRequired ? 'Required' : 'Not Required'}</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Conditions */}
      <div className="grid grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Pre-Conditions</CardTitle>
            <CardDescription>Conditions to be fulfilled before restructure</CardDescription>
          </CardHeader>
          <CardContent>
            {restructure.preConditions ? (
              <pre className="text-sm whitespace-pre-wrap">{restructure.preConditions}</pre>
            ) : (
              <p className="text-muted-foreground">No pre-conditions specified</p>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Post-Conditions</CardTitle>
            <CardDescription>Conditions to be monitored after restructure</CardDescription>
          </CardHeader>
          <CardContent>
            {restructure.postConditions ? (
              <pre className="text-sm whitespace-pre-wrap">{restructure.postConditions}</pre>
            ) : (
              <p className="text-muted-foreground">No post-conditions specified</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Justification */}
      <Card>
        <CardHeader>
          <CardTitle>Justification</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm">{restructure.justification}</p>
          {restructure.remarks && (
            <>
              <Separator className="my-4" />
              <div>
                <p className="text-xs text-muted-foreground mb-1">Additional Remarks</p>
                <p className="text-sm">{restructure.remarks}</p>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {/* Approval Details (if approved) */}
      {restructure.approvedByName && (
        <Card>
          <CardHeader>
            <CardTitle>Approval Details</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-4 gap-4">
              <div>
                <p className="text-xs text-muted-foreground">Approved By</p>
                <p className="font-semibold">{restructure.approvedByName}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Authority</p>
                <p className="font-semibold">{restructure.approvalAuthority}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Approval Date</p>
                {restructure.approvalDate ? (
                  <DateDisplay date={restructure.approvalDate} className="font-semibold" />
                ) : (
                  <p className="text-muted-foreground">-</p>
                )}
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Implementation</p>
                {restructure.implementationDate ? (
                  <DateDisplay date={restructure.implementationDate} className="font-semibold" />
                ) : (
                  <Badge variant="outline">Pending</Badge>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Timeline */}
      <Card>
        <CardHeader>
          <CardTitle>Timeline</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2 text-sm text-muted-foreground">
            <span>Created: {new Date(restructure.createdAt).toLocaleString()}</span>
            <span>|</span>
            <span>Last Updated: {new Date(restructure.updatedAt).toLocaleString()}</span>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
