import { ArrowLeft, Check, Clock, X } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { hrisApi } from '@/services/api';

import { logger } from "@/lib/logger";
interface Regularization {
  id: string;
  employeeId: string;
  employeeName?: string;
  employeeCode?: string;
  departmentName?: string;
  attendanceDate: string;
  requestType: string;
  reason: string;
  originalFirstIn?: string;
  originalLastOut?: string;
  originalStatus?: string;
  requestedFirstIn?: string;
  requestedLastOut?: string;
  requestedStatus?: string;
  status: string;
  approvedAt?: string;
  approverRemarks?: string;
  rejectedAt?: string;
  rejectionReason?: string;
  createdAt: string;
}

const REQUEST_TYPE_LABELS: Record<string, string> = {
  MISSED_PUNCH: 'Missed Punch',
  CORRECTION: 'Time Correction',
  ON_DUTY: 'On Duty',
  WFH: 'Work From Home',
};

const getStatusBadgeColor = (status: string) => {
  switch (status) {
    case 'PENDING':
      return 'bg-amber-50 text-amber-700';
    case 'APPROVED':
      return 'bg-green-50 text-green-700';
    case 'REJECTED':
      return 'bg-red-50 text-red-700';
    default:
      return 'bg-slate-100 text-slate-600';
  }
};

const formatTime = (time: string | null | undefined) => {
  if (!time) return '-';
  const [hours, minutes] = time.split(':');
  const h = parseInt(hours, 10);
  const ampm = h >= 12 ? 'PM' : 'AM';
  const displayHour = h % 12 || 12;
  return `${displayHour}:${minutes} ${ampm}`;
};

export function RegularizationView() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [request, setRequest] = useState<Regularization | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [showApprovalForm, setShowApprovalForm] = useState(false);
  const [showRejectionForm, setShowRejectionForm] = useState(false);
  const [remarks, setRemarks] = useState('');

  useEffect(() => {
    if (!id) return;
    const fetchRequest = async () => {
      try {
        setLoading(true);
        const response = await hrisApi.getRegularization(id);
        setRequest(response.data);
      } catch (error) {
        logger.error('Failed to fetch regularization:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchRequest();
  }, [id]);

  const handleApprove = async () => {
    if (!id) return;
    try {
      setActionLoading(true);
      await hrisApi.approveRegularization(id, remarks);
      const response = await hrisApi.getRegularization(id);
      setRequest(response.data);
      setShowApprovalForm(false);
      setRemarks('');
    } catch (error) {
      logger.error('Failed to approve regularization:', error);
    } finally {
      setActionLoading(false);
    }
  };

  const handleReject = async () => {
    if (!id || !remarks) return;
    try {
      setActionLoading(true);
      await hrisApi.rejectRegularization(id, remarks);
      const response = await hrisApi.getRegularization(id);
      setRequest(response.data);
      setShowRejectionForm(false);
      setRemarks('');
    } catch (error) {
      logger.error('Failed to reject regularization:', error);
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

  if (!request) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <p className="text-sm text-slate-500">Regularization request not found</p>
        <Button variant="link" onClick={() => navigate('/admin/hris/attendance/regularization')}>
          Back to Regularization Requests
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Regularization Request"
        subtitle={`${request.employeeName} - ${new Date(request.attendanceDate).toLocaleDateString()}`}
        breadcrumbs={[
          { label: 'Regularization', to: '/admin/hris/attendance/regularization' },
          { label: 'Request' },
        ]}
        actions={<Badge className={getStatusBadgeColor(request.status)}>{request.status}</Badge>}
      />

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Main Content */}
        <div className="space-y-6 lg:col-span-2">
          {/* Employee Info */}
          <Card>
            <CardHeader>
              <CardTitle>Employee Information</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <p className="text-sm text-slate-500">Employee Name</p>
                  <p className="font-medium">{request.employeeName}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-500">Employee Code</p>
                  <p className="font-medium">{request.employeeCode}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-500">Department</p>
                  <p className="font-medium">{request.departmentName || '-'}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-500">Request Type</p>
                  <Badge variant="outline">
                    {REQUEST_TYPE_LABELS[request.requestType] || request.requestType}
                  </Badge>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Timing Details */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Clock className="h-5 w-5" />
                Timing Details
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-6 md:grid-cols-2">
                <div className="space-y-4">
                  <h4 className="text-sm font-medium text-slate-700">Original Timings</h4>
                  <div className="space-y-2 rounded-lg bg-slate-50 p-4">
                    <div className="flex justify-between">
                      <span className="text-sm text-slate-500">First In</span>
                      <span className="font-medium">{formatTime(request.originalFirstIn)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-slate-500">Last Out</span>
                      <span className="font-medium">{formatTime(request.originalLastOut)}</span>
                    </div>
                    {request.originalStatus && (
                      <div className="flex justify-between">
                        <span className="text-sm text-slate-500">Status</span>
                        <Badge variant="outline">{request.originalStatus}</Badge>
                      </div>
                    )}
                  </div>
                </div>

                <div className="space-y-4">
                  <h4 className="text-sm font-medium text-slate-700">Requested Timings</h4>
                  <div className="space-y-2 rounded-lg bg-blue-50 p-4">
                    <div className="flex justify-between">
                      <span className="text-sm text-blue-700">First In</span>
                      <span className="font-medium text-blue-900">
                        {formatTime(request.requestedFirstIn)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-blue-700">Last Out</span>
                      <span className="font-medium text-blue-900">
                        {formatTime(request.requestedLastOut)}
                      </span>
                    </div>
                    {request.requestedStatus && (
                      <div className="flex justify-between">
                        <span className="text-sm text-blue-700">Status</span>
                        <Badge variant="outline">{request.requestedStatus}</Badge>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              <div className="mt-6">
                <p className="text-sm text-slate-500">Reason for Request</p>
                <p className="mt-1 font-medium">{request.reason}</p>
              </div>
            </CardContent>
          </Card>

          {/* Action Forms */}
          {request.status === 'PENDING' && (
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

          {/* Status Info */}
          {(request.status === 'APPROVED' || request.status === 'REJECTED') && (
            <Card>
              <CardHeader>
                <CardTitle>
                  {request.status === 'APPROVED' ? 'Approval Details' : 'Rejection Details'}
                </CardTitle>
              </CardHeader>
              <CardContent>
                {request.status === 'APPROVED' && (
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm text-slate-500">Approved On</span>
                      <span className="font-medium">
                        {request.approvedAt ? new Date(request.approvedAt).toLocaleString() : '-'}
                      </span>
                    </div>
                    {request.approverRemarks && (
                      <div>
                        <p className="text-sm text-slate-500">Remarks</p>
                        <p className="mt-1 font-medium">{request.approverRemarks}</p>
                      </div>
                    )}
                  </div>
                )}

                {request.status === 'REJECTED' && (
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm text-slate-500">Rejected On</span>
                      <span className="font-medium">
                        {request.rejectedAt ? new Date(request.rejectedAt).toLocaleString() : '-'}
                      </span>
                    </div>
                    {request.rejectionReason && (
                      <div>
                        <p className="text-sm text-slate-500">Reason</p>
                        <p className="mt-1 font-medium">{request.rejectionReason}</p>
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
                    <p className="text-sm font-medium">Request Submitted</p>
                    <p className="text-xs text-slate-500">
                      {new Date(request.createdAt).toLocaleString()}
                    </p>
                  </div>
                </div>

                {request.status !== 'PENDING' && (
                  <div className="flex gap-3">
                    <div className="flex flex-col items-center">
                      <div
                        className={`h-2 w-2 rounded-full ${
                          request.status === 'APPROVED' ? 'bg-green-500' : 'bg-red-500'
                        }`}
                      />
                    </div>
                    <div>
                      <p className="text-sm font-medium">{request.status}</p>
                      <p className="text-xs text-slate-500">
                        {request.approvedAt && new Date(request.approvedAt).toLocaleString()}
                        {request.rejectedAt && new Date(request.rejectedAt).toLocaleString()}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
