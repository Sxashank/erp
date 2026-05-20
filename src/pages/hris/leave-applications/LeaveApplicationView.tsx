import { ArrowLeft, Calendar, Check, Clock, FileText, Phone, User, X } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

import { DateDisplay } from '@/components/common/DateDisplay';
import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { hrisApi } from '@/services/api';

import { logger } from "@/lib/logger";
interface LeaveApplication {
  id: string;
  applicationNumber: string;
  employeeId: string;
  employeeName?: string;
  employeeCode?: string;
  departmentName?: string;
  designationName?: string;
  leaveTypeId: string;
  leaveTypeName?: string;
  leaveTypeCode?: string;
  fromDate: string;
  toDate: string;
  totalDays: number;
  workingDays: number;
  isHalfDay: boolean;
  halfDayType?: string;
  reason: string;
  contactNumber?: string;
  contactAddress?: string;
  attachments?: string[];
  status: string;
  approvedBy?: string;
  approvedAt?: string;
  approverRemarks?: string;
  rejectedBy?: string;
  rejectedAt?: string;
  rejectionReason?: string;
  cancelledAt?: string;
  cancellationReason?: string;
  createdAt: string;
  updatedAt: string;
}

const getStatusBadgeColor = (status: string) => {
  switch (status) {
    case 'PENDING':
      return 'bg-amber-50 text-amber-700';
    case 'APPROVED':
      return 'bg-green-50 text-green-700';
    case 'REJECTED':
      return 'bg-red-50 text-red-700';
    case 'CANCELLED':
      return 'bg-slate-100 text-slate-600';
    default:
      return 'bg-slate-100 text-slate-600';
  }
};

export function LeaveApplicationView() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [application, setApplication] = useState<LeaveApplication | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [showApprovalForm, setShowApprovalForm] = useState(false);
  const [showRejectionForm, setShowRejectionForm] = useState(false);
  const [remarks, setRemarks] = useState('');

  useEffect(() => {
    if (!id) return;
    const fetchApplication = async () => {
      try {
        setLoading(true);
        const response = await hrisApi.getLeaveApplication(id);
        setApplication(response.data);
      } catch (error) {
        logger.error('Failed to fetch leave application:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchApplication();
  }, [id]);

  const handleApprove = async () => {
    if (!id) return;
    try {
      setActionLoading(true);
      await hrisApi.approveLeaveApplication(id, remarks);
      const response = await hrisApi.getLeaveApplication(id);
      setApplication(response.data);
      setShowApprovalForm(false);
      setRemarks('');
    } catch (error) {
      logger.error('Failed to approve application:', error);
    } finally {
      setActionLoading(false);
    }
  };

  const handleReject = async () => {
    if (!id || !remarks) return;
    try {
      setActionLoading(true);
      await hrisApi.rejectLeaveApplication(id, remarks);
      const response = await hrisApi.getLeaveApplication(id);
      setApplication(response.data);
      setShowRejectionForm(false);
      setRemarks('');
    } catch (error) {
      logger.error('Failed to reject application:', error);
    } finally {
      setActionLoading(false);
    }
  };

  const handleCancel = async () => {
    if (!id) return;
    const reason = prompt('Please provide a reason for cancellation:');
    if (!reason) return;

    try {
      setActionLoading(true);
      await hrisApi.cancelLeaveApplication(id, reason);
      const response = await hrisApi.getLeaveApplication(id);
      setApplication(response.data);
    } catch (error) {
      logger.error('Failed to cancel application:', error);
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <p className="text-sm text-slate-500">Loading...</p>
      </div>
    );
  }

  if (!application) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <p className="text-sm text-slate-500">Leave application not found</p>
        <Button variant="link" onClick={() => navigate('/admin/hris/leave-applications')}>
          Back to Leave Applications
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Leave Application"
        subtitle={application.applicationNumber}
        breadcrumbs={[
          { label: 'Leave Applications', to: '/admin/hris/leave-applications' },
          { label: application.applicationNumber },
        ]}
        actions={
          <Badge className={getStatusBadgeColor(application.status)}>{application.status}</Badge>
        }
      />

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Main Content */}
        <div className="space-y-6 lg:col-span-2">
          {/* Employee Info */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <User className="h-5 w-5" />
                Employee Information
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <p className="text-sm text-slate-500">Employee Name</p>
                  <p className="font-medium">{application.employeeName}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-500">Employee Code</p>
                  <p className="font-medium">{application.employeeCode}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-500">Department</p>
                  <p className="font-medium">{application.departmentName || '-'}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-500">Designation</p>
                  <p className="font-medium">{application.designationName || '-'}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Leave Details */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Calendar className="h-5 w-5" />
                Leave Details
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <p className="text-sm text-slate-500">Leave Type</p>
                  <p className="font-medium">
                    {application.leaveTypeCode} - {application.leaveTypeName}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-slate-500">Duration</p>
                  <p className="font-medium">
                    {application.workingDays} day(s)
                    {application.isHalfDay && (
                      <span className="ml-1 text-slate-500">({application.halfDayType})</span>
                    )}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-slate-500">From Date</p>
                  <p className="font-medium">
                    <DateDisplay date={application.fromDate} />
                  </p>
                </div>
                <div>
                  <p className="text-sm text-slate-500">To Date</p>
                  <p className="font-medium">
                    <DateDisplay date={application.toDate} />
                  </p>
                </div>
              </div>

              <div>
                <p className="text-sm text-slate-500">Reason</p>
                <p className="mt-1 font-medium">{application.reason}</p>
              </div>

              {(application.contactNumber || application.contactAddress) && (
                <div className="grid gap-4 md:grid-cols-2">
                  {application.contactNumber && (
                    <div className="flex items-center gap-2">
                      <Phone className="h-4 w-4 text-slate-400" />
                      <div>
                        <p className="text-sm text-slate-500">Contact During Leave</p>
                        <p className="font-medium">{application.contactNumber}</p>
                      </div>
                    </div>
                  )}
                  {application.contactAddress && (
                    <div>
                      <p className="text-sm text-slate-500">Contact Address</p>
                      <p className="font-medium">{application.contactAddress}</p>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Approval/Rejection Forms */}
          {application.status === 'PENDING' && (
            <Card>
              <CardHeader>
                <CardTitle>Take Action</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {!showApprovalForm && !showRejectionForm && (
                  <div className="flex gap-2">
                    <Button onClick={() => setShowApprovalForm(true)}>
                      <Check className="mr-2 h-4 w-4" />
                      Approve
                    </Button>
                    <Button variant="destructive" onClick={() => setShowRejectionForm(true)}>
                      <X className="mr-2 h-4 w-4" />
                      Reject
                    </Button>
                  </div>
                )}

                {showApprovalForm && (
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="approval_remarks">Approval Remarks (Optional)</Label>
                      <Textarea
                        id="approval_remarks"
                        value={remarks}
                        onChange={(e) => setRemarks(e.target.value)}
                        placeholder="Add any remarks..."
                        rows={3}
                      />
                    </div>
                    <div className="flex gap-2">
                      <Button onClick={handleApprove} disabled={actionLoading}>
                        {actionLoading ? 'Processing...' : 'Confirm Approval'}
                      </Button>
                      <Button
                        variant="outline"
                        onClick={() => {
                          setShowApprovalForm(false);
                          setRemarks('');
                        }}
                      >
                        Cancel
                      </Button>
                    </div>
                  </div>
                )}

                {showRejectionForm && (
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="rejection_reason">Rejection Reason *</Label>
                      <Textarea
                        id="rejection_reason"
                        value={remarks}
                        onChange={(e) => setRemarks(e.target.value)}
                        placeholder="Please provide the reason for rejection..."
                        rows={3}
                      />
                    </div>
                    <div className="flex gap-2">
                      <Button
                        variant="destructive"
                        onClick={handleReject}
                        disabled={actionLoading || !remarks}
                      >
                        {actionLoading ? 'Processing...' : 'Confirm Rejection'}
                      </Button>
                      <Button
                        variant="outline"
                        onClick={() => {
                          setShowRejectionForm(false);
                          setRemarks('');
                        }}
                      >
                        Cancel
                      </Button>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Status/Approval Info */}
          {(application.status === 'APPROVED' ||
            application.status === 'REJECTED' ||
            application.status === 'CANCELLED') && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="h-5 w-5" />
                  {application.status === 'APPROVED' && 'Approval Details'}
                  {application.status === 'REJECTED' && 'Rejection Details'}
                  {application.status === 'CANCELLED' && 'Cancellation Details'}
                </CardTitle>
              </CardHeader>
              <CardContent>
                {application.status === 'APPROVED' && (
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm text-slate-500">Approved On</span>
                      <DateDisplay date={application.approvedAt} className="font-medium" />
                    </div>
                    {application.approverRemarks && (
                      <div>
                        <p className="text-sm text-slate-500">Remarks</p>
                        <p className="mt-1 font-medium">{application.approverRemarks}</p>
                      </div>
                    )}
                  </div>
                )}

                {application.status === 'REJECTED' && (
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm text-slate-500">Rejected On</span>
                      <DateDisplay date={application.rejectedAt} className="font-medium" />
                    </div>
                    {application.rejectionReason && (
                      <div>
                        <p className="text-sm text-slate-500">Reason</p>
                        <p className="mt-1 font-medium">{application.rejectionReason}</p>
                      </div>
                    )}
                  </div>
                )}

                {application.status === 'CANCELLED' && (
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm text-slate-500">Cancelled On</span>
                      <DateDisplay date={application.cancelledAt} className="font-medium" />
                    </div>
                    {application.cancellationReason && (
                      <div>
                        <p className="text-sm text-slate-500">Reason</p>
                        <p className="mt-1 font-medium">{application.cancellationReason}</p>
                      </div>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Timeline */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Clock className="h-5 w-5" />
                Timeline
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex gap-3">
                  <div className="flex flex-col items-center">
                    <div className="h-2 w-2 rounded-full bg-green-500" />
                    <div className="h-full w-px bg-slate-200" />
                  </div>
                  <div>
                    <p className="text-sm font-medium">Applied</p>
                    <p className="text-xs text-slate-500">
                      {new Date(application.createdAt).toLocaleString()}
                    </p>
                  </div>
                </div>

                {application.status !== 'PENDING' && (
                  <div className="flex gap-3">
                    <div className="flex flex-col items-center">
                      <div
                        className={`h-2 w-2 rounded-full ${
                          application.status === 'APPROVED'
                            ? 'bg-green-500'
                            : application.status === 'REJECTED'
                              ? 'bg-red-500'
                              : 'bg-slate-400'
                        }`}
                      />
                    </div>
                    <div>
                      <p className="text-sm font-medium">{application.status}</p>
                      <p className="text-xs text-slate-500">
                        {application.approvedAt &&
                          new Date(application.approvedAt).toLocaleString()}
                        {application.rejectedAt &&
                          new Date(application.rejectedAt).toLocaleString()}
                        {application.cancelledAt &&
                          new Date(application.cancelledAt).toLocaleString()}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Actions */}
          {application.status === 'APPROVED' && (
            <Card>
              <CardHeader>
                <CardTitle>Actions</CardTitle>
              </CardHeader>
              <CardContent>
                <Button
                  variant="outline"
                  className="w-full"
                  onClick={handleCancel}
                  disabled={actionLoading}
                >
                  Cancel Leave
                </Button>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
