import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, Edit, FileText, CheckCircle, Clock, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { StatusBadge } from '@/components/lending/common/StatusBadge';
import { AmountDisplay } from '@/components/lending/common/AmountDisplay';
import { PercentageDisplay } from '@/components/lending/common/PercentageDisplay';
import { DateDisplay } from '@/components/lending/common/DateDisplay';
import { WorkflowStatus } from '@/components/lending/workflow/WorkflowStatus';
import { ApprovalActions } from '@/components/lending/workflow/ApprovalActions';
import { InlineRemarks } from '@/components/lending/workflow/InlineRemarks';
import { AuditTimeline } from '@/components/lending/common/AuditTimeline';

import { logger } from '@/lib/logger';
// Mock application data
const mockApplication = {
  id: '1',
  applicationNumber: 'SMFC/TL/DEL/2025/A00001',
  stage: 'APPRAISAL',
  status: 'UNDER_REVIEW',
  entity: {
    id: '1',
    entityCode: 'ENT/2025/00001',
    legalName: 'ABC Industries Private Limited',
    pan: 'AABCA1234A',
    entityType: 'CORPORATE',
    internalRating: 'A',
  },
  product: {
    id: '1',
    productCode: 'TL-CORP-001',
    productName: 'Corporate Term Loan',
    category: 'TERM_LOAN',
  },
  requestedAmount: 250000000,
  requestedTenureMonths: 60,
  purpose: 'Expansion of manufacturing facility and acquisition of new plant & machinery',
  projectCost: 350000000,
  promoterContribution: 100000000,
  bankFinance: 250000000,
  interestType: 'FLOATING',
  repaymentFrequency: 'MONTHLY',
  moratoriumMonths: 6,
  securities: [
    {
      securityType: 'PRIMARY',
      nature: 'PROPERTY',
      description: 'Industrial land and building at Plot 45, Industrial Area, Phase II, Gurgaon',
      value: 400000000,
      margin: 25,
    },
    {
      securityType: 'COLLATERAL',
      nature: 'FIXED_DEPOSIT',
      description: 'FD with SBI, Gurgaon branch',
      value: 50000000,
      margin: 10,
    },
  ],
  documents: [
    { name: 'PAN Card', type: 'KYC', status: 'VERIFIED', uploadedAt: '2025-01-05' },
    { name: 'Certificate of Incorporation', type: 'KYC', status: 'VERIFIED', uploadedAt: '2025-01-05' },
    { name: 'MOA & AOA', type: 'KYC', status: 'VERIFIED', uploadedAt: '2025-01-05' },
    { name: 'Audited Financials (3 years)', type: 'FINANCIAL', status: 'VERIFIED', uploadedAt: '2025-01-06' },
    { name: 'ITR (3 years)', type: 'FINANCIAL', status: 'VERIFIED', uploadedAt: '2025-01-06' },
    { name: 'Bank Statements (12 months)', type: 'FINANCIAL', status: 'PENDING_REVIEW', uploadedAt: '2025-01-07' },
    { name: 'Project Report', type: 'PROJECT', status: 'PENDING_REVIEW', uploadedAt: '2025-01-07' },
  ],
  projectMilestones: [
    { milestone: 'Land acquisition', amount: 50000000, targetDate: '2025-02-28', status: 'COMPLETED' },
    { milestone: 'Civil construction - Phase 1', amount: 75000000, targetDate: '2025-06-30', status: 'PENDING' },
    { milestone: 'Plant & machinery procurement', amount: 100000000, targetDate: '2025-09-30', status: 'PENDING' },
    { milestone: 'Civil construction - Phase 2', amount: 25000000, targetDate: '2025-11-30', status: 'PENDING' },
  ],
  workflowStatus: {
    currentStep: 'Credit Analysis',
    currentApprover: 'Rajesh Kumar (Credit Analyst)',
    pendingSince: '2025-01-08',
    slaHours: 48,
    elapsedHours: 36,
  },
  auditTrail: [
    { id: 'a1', action: 'Application Created', user_name: 'Amit Sharma', timestamp: '2025-01-05T10:30:00', description: 'New application submitted' },
    { id: 'a2', action: 'Documents Uploaded', user_name: 'Amit Sharma', timestamp: '2025-01-05T14:15:00', description: 'KYC documents uploaded' },
    { id: 'a3', action: 'Documents Uploaded', user_name: 'Amit Sharma', timestamp: '2025-01-06T11:00:00', description: 'Financial documents uploaded' },
    { id: 'a4', action: 'Application Submitted', user_name: 'Amit Sharma', timestamp: '2025-01-07T09:45:00', description: 'Submitted for credit review' },
    { id: 'a5', action: 'Credit Review Completed', user_name: 'Priya Singh', timestamp: '2025-01-08T16:30:00', description: 'Initial credit assessment complete. Recommended for detailed analysis.' },
  ],
  createdAt: '2025-01-05',
  submittedAt: '2025-01-07',
  relationshipManager: 'Amit Sharma',
  branch: 'Delhi - Connaught Place',
};

const stageSteps = ['APPLICATION', 'APPRAISAL', 'SANCTION', 'POST_SANCTION', 'DISBURSED'];

export default function ApplicationView() {
  const navigate = useNavigate();
  const { id } = useParams();
  const application = mockApplication;

  const currentStageIndex = stageSteps.indexOf(application.stage);

  const handleApprove = (remarks: string) => {
    logger.debug('Approved with remarks:', remarks);
  };

  const handleReject = (remarks: string) => {
    logger.debug('Rejected with remarks:', remarks);
  };

  const handleReturn = (remarks: string) => {
    logger.debug('Returned with remarks:', remarks);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => navigate('/admin/lending/applications')}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-semibold">Loan Application</h1>
            <StatusBadge status={application.status} type="application" />
          </div>
          <p className="text-muted-foreground font-mono">{application.applicationNumber}</p>
        </div>
        {application.status === 'DRAFT' && (
          <Button onClick={() => navigate(`/admin/lending/applications/${id}/edit`)}>
            <Edit className="mr-2 h-4 w-4" />
            Continue Application
          </Button>
        )}
      </div>

      {/* Stage Progress */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            {stageSteps.map((stage, index) => {
              const isCompleted = index < currentStageIndex;
              const isCurrent = index === currentStageIndex;
              return (
                <div key={stage} className="flex items-center flex-1">
                  <div className="flex flex-col items-center">
                    <div
                      className={`w-10 h-10 rounded-full flex items-center justify-center ${
                        isCompleted
                          ? 'bg-green-500 text-white'
                          : isCurrent
                          ? 'bg-blue-500 text-white'
                          : 'bg-gray-200 text-gray-500'
                      }`}
                    >
                      {isCompleted ? (
                        <CheckCircle className="h-5 w-5" />
                      ) : (
                        <span className="text-sm font-medium">{index + 1}</span>
                      )}
                    </div>
                    <span
                      className={`mt-2 text-xs font-medium ${
                        isCurrent ? 'text-blue-600' : 'text-muted-foreground'
                      }`}
                    >
                      {stage.replace('_', ' ')}
                    </span>
                  </div>
                  {index < stageSteps.length - 1 && (
                    <div
                      className={`flex-1 h-1 mx-2 ${
                        index < currentStageIndex ? 'bg-green-500' : 'bg-gray-200'
                      }`}
                    />
                  )}
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Requested Amount
            </CardTitle>
          </CardHeader>
          <CardContent>
            <AmountDisplay amount={application.requestedAmount} abbreviated className="text-2xl font-bold" />
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Tenure</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{application.requestedTenureMonths} Months</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Product</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-lg font-semibold">{application.product.productName}</div>
            <p className="text-xs text-muted-foreground">{application.product.productCode}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Entity Rating</CardTitle>
          </CardHeader>
          <CardContent>
            <Badge
              variant="outline"
              className="text-lg px-3 py-1 bg-green-50 text-green-700 border-green-200"
            >
              {application.entity.internalRating}
            </Badge>
          </CardContent>
        </Card>
      </div>

      {/* Main Content */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left Column - Application Details */}
        <div className="lg:col-span-2 space-y-6">
          <Tabs defaultValue="details">
            <TabsList>
              <TabsTrigger value="details">Application Details</TabsTrigger>
              <TabsTrigger value="security">Security/Collateral</TabsTrigger>
              <TabsTrigger value="documents">Documents</TabsTrigger>
              <TabsTrigger value="milestones">Project Milestones</TabsTrigger>
            </TabsList>

            {/* Details Tab */}
            <TabsContent value="details" className="space-y-6 mt-6">
              <Card>
                <CardHeader>
                  <CardTitle>Entity Information</CardTitle>
                </CardHeader>
                <CardContent>
                  <dl className="grid gap-4 md:grid-cols-2">
                    <div>
                      <dt className="text-sm font-medium text-muted-foreground">Entity Name</dt>
                      <dd className="font-medium">{application.entity.legalName}</dd>
                    </div>
                    <div>
                      <dt className="text-sm font-medium text-muted-foreground">Entity Code</dt>
                      <dd className="font-mono">{application.entity.entityCode}</dd>
                    </div>
                    <div>
                      <dt className="text-sm font-medium text-muted-foreground">Entity Type</dt>
                      <dd>{application.entity.entityType}</dd>
                    </div>
                    <div>
                      <dt className="text-sm font-medium text-muted-foreground">PAN</dt>
                      <dd className="font-mono">{application.entity.pan}</dd>
                    </div>
                  </dl>
                  <Button
                    variant="link"
                    className="p-0 mt-4"
                    onClick={() => navigate(`/admin/lending/entities/${application.entity.id}`)}
                  >
                    View Full Entity Profile →
                  </Button>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Loan Details</CardTitle>
                </CardHeader>
                <CardContent>
                  <dl className="grid gap-4 md:grid-cols-2">
                    <div>
                      <dt className="text-sm font-medium text-muted-foreground">Requested Amount</dt>
                      <dd>
                        <AmountDisplay amount={application.requestedAmount} showFull />
                      </dd>
                    </div>
                    <div>
                      <dt className="text-sm font-medium text-muted-foreground">Tenure</dt>
                      <dd>{application.requestedTenureMonths} Months</dd>
                    </div>
                    <div>
                      <dt className="text-sm font-medium text-muted-foreground">Interest Type</dt>
                      <dd>
                        <Badge variant="outline">{application.interestType}</Badge>
                      </dd>
                    </div>
                    <div>
                      <dt className="text-sm font-medium text-muted-foreground">
                        Repayment Frequency
                      </dt>
                      <dd>{application.repaymentFrequency}</dd>
                    </div>
                    <div>
                      <dt className="text-sm font-medium text-muted-foreground">Moratorium</dt>
                      <dd>{application.moratoriumMonths} Months</dd>
                    </div>
                    <div className="md:col-span-2">
                      <dt className="text-sm font-medium text-muted-foreground">Purpose</dt>
                      <dd className="text-sm">{application.purpose}</dd>
                    </div>
                  </dl>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Project Cost Structure</CardTitle>
                </CardHeader>
                <CardContent>
                  <dl className="grid gap-4 md:grid-cols-3">
                    <div>
                      <dt className="text-sm font-medium text-muted-foreground">Total Project Cost</dt>
                      <dd>
                        <AmountDisplay amount={application.projectCost} showFull />
                      </dd>
                    </div>
                    <div>
                      <dt className="text-sm font-medium text-muted-foreground">
                        Promoter Contribution
                      </dt>
                      <dd>
                        <AmountDisplay amount={application.promoterContribution} showFull />
                        <span className="text-xs text-muted-foreground ml-1">
                          (
                          <PercentageDisplay
                            value={(application.promoterContribution / application.projectCost) * 100}
                          />
                          )
                        </span>
                      </dd>
                    </div>
                    <div>
                      <dt className="text-sm font-medium text-muted-foreground">Bank Finance</dt>
                      <dd>
                        <AmountDisplay amount={application.bankFinance} showFull />
                        <span className="text-xs text-muted-foreground ml-1">
                          (
                          <PercentageDisplay
                            value={(application.bankFinance / application.projectCost) * 100}
                          />
                          )
                        </span>
                      </dd>
                    </div>
                  </dl>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Security Tab */}
            <TabsContent value="security" className="mt-6">
              <Card>
                <CardHeader>
                  <CardTitle>Security/Collateral Details</CardTitle>
                  <CardDescription>
                    Securities proposed against the loan facility
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Type</TableHead>
                        <TableHead>Nature</TableHead>
                        <TableHead>Description</TableHead>
                        <TableHead className="text-right">Value</TableHead>
                        <TableHead className="text-right">Margin</TableHead>
                        <TableHead className="text-right">Net Value</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {application.securities.map((security, index) => (
                        <TableRow key={index}>
                          <TableCell>
                            <Badge
                              variant={security.securityType === 'PRIMARY' ? 'default' : 'secondary'}
                            >
                              {security.securityType}
                            </Badge>
                          </TableCell>
                          <TableCell>{security.nature}</TableCell>
                          <TableCell className="max-w-[300px]">{security.description}</TableCell>
                          <TableCell className="text-right">
                            <AmountDisplay amount={security.value} abbreviated />
                          </TableCell>
                          <TableCell className="text-right">
                            <PercentageDisplay value={security.margin} />
                          </TableCell>
                          <TableCell className="text-right">
                            <AmountDisplay
                              amount={security.value * (1 - security.margin / 100)}
                              abbreviated
                            />
                          </TableCell>
                        </TableRow>
                      ))}
                      <TableRow className="font-medium bg-muted/50">
                        <TableCell colSpan={3}>Total Security Coverage</TableCell>
                        <TableCell className="text-right">
                          <AmountDisplay
                            amount={application.securities.reduce((sum, s) => sum + s.value, 0)}
                            abbreviated
                          />
                        </TableCell>
                        <TableCell></TableCell>
                        <TableCell className="text-right">
                          <AmountDisplay
                            amount={application.securities.reduce(
                              (sum, s) => sum + s.value * (1 - s.margin / 100),
                              0
                            )}
                            abbreviated
                          />
                        </TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Documents Tab */}
            <TabsContent value="documents" className="mt-6">
              <Card>
                <CardHeader>
                  <CardTitle>Uploaded Documents</CardTitle>
                  <CardDescription>
                    Documents submitted with the application
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Document Name</TableHead>
                        <TableHead>Type</TableHead>
                        <TableHead>Uploaded On</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead className="w-[100px]"></TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {application.documents.map((doc, index) => (
                        <TableRow key={index}>
                          <TableCell className="font-medium">{doc.name}</TableCell>
                          <TableCell>
                            <Badge variant="outline">{doc.type}</Badge>
                          </TableCell>
                          <TableCell>
                            <DateDisplay date={doc.uploadedAt} />
                          </TableCell>
                          <TableCell>
                            <Badge
                              variant={doc.status === 'VERIFIED' ? 'default' : 'secondary'}
                              className={
                                doc.status === 'VERIFIED'
                                  ? 'bg-green-100 text-green-700'
                                  : 'bg-yellow-100 text-yellow-700'
                              }
                            >
                              {doc.status === 'VERIFIED' ? (
                                <CheckCircle className="h-3 w-3 mr-1" />
                              ) : (
                                <Clock className="h-3 w-3 mr-1" />
                              )}
                              {doc.status.replace('_', ' ')}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <Button variant="ghost" size="sm">
                              <FileText className="h-4 w-4 mr-1" />
                              View
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
            </TabsContent>

            {/* Milestones Tab */}
            <TabsContent value="milestones" className="mt-6">
              <Card>
                <CardHeader>
                  <CardTitle>Project Milestones</CardTitle>
                  <CardDescription>
                    Milestone-linked disbursement schedule
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>#</TableHead>
                        <TableHead>Milestone</TableHead>
                        <TableHead className="text-right">Amount</TableHead>
                        <TableHead>Target Date</TableHead>
                        <TableHead>Status</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {application.projectMilestones.map((milestone, index) => (
                        <TableRow key={index}>
                          <TableCell>{index + 1}</TableCell>
                          <TableCell className="font-medium">{milestone.milestone}</TableCell>
                          <TableCell className="text-right">
                            <AmountDisplay amount={milestone.amount} abbreviated />
                          </TableCell>
                          <TableCell>
                            <DateDisplay date={milestone.targetDate} />
                          </TableCell>
                          <TableCell>
                            <Badge
                              variant={milestone.status === 'COMPLETED' ? 'default' : 'secondary'}
                              className={
                                milestone.status === 'COMPLETED'
                                  ? 'bg-green-100 text-green-700'
                                  : ''
                              }
                            >
                              {milestone.status}
                            </Badge>
                          </TableCell>
                        </TableRow>
                      ))}
                      <TableRow className="font-medium bg-muted/50">
                        <TableCell colSpan={2}>Total</TableCell>
                        <TableCell className="text-right">
                          <AmountDisplay
                            amount={application.projectMilestones.reduce((sum, m) => sum + m.amount, 0)}
                            abbreviated
                          />
                        </TableCell>
                        <TableCell colSpan={2}></TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>

        {/* Right Column - Workflow & Actions */}
        <div className="space-y-6">
          {/* Workflow Status */}
          <WorkflowStatus
            workflow={{
              instance_id: 'wf-1',
              workflow_name: 'Loan Application Approval',
              entity_type: 'application',
              entity_id: application.id,
              status: 'IN_PROGRESS',
              initiated_at: application.createdAt,
              current_step: 2,
              steps: [
                { step_id: 's1', step_number: 1, step_name: 'Initial Review', status: 'COMPLETED', completed_by_name: 'Amit Sharma', action: 'APPROVE' },
                { step_id: 's2', step_number: 2, step_name: application.workflowStatus.currentStep, status: 'IN_PROGRESS', assigned_to_name: application.workflowStatus.currentApprover, sla_hours: application.workflowStatus.slaHours },
                { step_id: 's3', step_number: 3, step_name: 'Final Approval', status: 'PENDING' },
              ],
            }}
          />

          {/* Approval Actions */}
          {application.status === 'UNDER_REVIEW' && (
            <ApprovalActions
              onApprove={handleApprove}
              onReject={handleReject}
              onReturn={handleReturn}
            />
          )}

          {/* Application Info */}
          <Card>
            <CardHeader>
              <CardTitle>Application Info</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <dt className="text-sm font-medium text-muted-foreground">Relationship Manager</dt>
                <dd>{application.relationshipManager}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-muted-foreground">Branch</dt>
                <dd>{application.branch}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-muted-foreground">Created On</dt>
                <dd>
                  <DateDisplay date={application.createdAt} />
                </dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-muted-foreground">Submitted On</dt>
                <dd>
                  <DateDisplay date={application.submittedAt} />
                </dd>
              </div>
            </CardContent>
          </Card>

          {/* Audit Trail */}
          <Card>
            <CardHeader>
              <CardTitle>Activity Timeline</CardTitle>
            </CardHeader>
            <CardContent>
              <AuditTimeline entries={application.auditTrail} />
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
