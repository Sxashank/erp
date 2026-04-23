import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  ArrowLeft,
  Calendar,
  Check,
  Clock,
  FileText,
  Phone,
  User,
  X,
} from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { hrisApi } from '@/services/api';

interface LeaveApplication {
  id: string;
  application_number: string;
  employee_id: string;
  employee_name?: string;
  employee_code?: string;
  department_name?: string;
  designation_name?: string;
  leave_type_id: string;
  leave_type_name?: string;
  leave_type_code?: string;
  from_date: string;
  to_date: string;
  total_days: number;
  working_days: number;
  is_half_day: boolean;
  half_day_type?: string;
  reason: string;
  contact_number?: string;
  contact_address?: string;
  attachments?: string[];
  status: string;
  approved_by?: string;
  approved_at?: string;
  approver_remarks?: string;
  rejected_by?: string;
  rejected_at?: string;
  rejection_reason?: string;
  cancelled_at?: string;
  cancellation_reason?: string;
  created_at: string;
  updated_at: string;
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
        console.error('Failed to fetch leave application:', error);
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
      console.error('Failed to approve application:', error);
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
      console.error('Failed to reject application:', error);
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
      console.error('Failed to cancel application:', error);
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
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => navigate('/admin/hris/leave-applications')}>
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Leave Application</h1>
            <p className="text-sm text-slate-500">{application.application_number}</p>
          </div>
        </div>
        <Badge className={getStatusBadgeColor(application.status)}>
          {application.status}
        </Badge>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
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
                  <p className="font-medium">{application.employee_name}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-500">Employee Code</p>
                  <p className="font-medium">{application.employee_code}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-500">Department</p>
                  <p className="font-medium">{application.department_name || '-'}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-500">Designation</p>
                  <p className="font-medium">{application.designation_name || '-'}</p>
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
                    {application.leave_type_code} - {application.leave_type_name}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-slate-500">Duration</p>
                  <p className="font-medium">
                    {application.working_days} day(s)
                    {application.is_half_day && (
                      <span className="text-slate-500 ml-1">({application.half_day_type})</span>
                    )}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-slate-500">From Date</p>
                  <p className="font-medium">{new Date(application.from_date).toLocaleDateString()}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-500">To Date</p>
                  <p className="font-medium">{new Date(application.to_date).toLocaleDateString()}</p>
                </div>
              </div>

              <div>
                <p className="text-sm text-slate-500">Reason</p>
                <p className="font-medium mt-1">{application.reason}</p>
              </div>

              {(application.contact_number || application.contact_address) && (
                <div className="grid gap-4 md:grid-cols-2">
                  {application.contact_number && (
                    <div className="flex items-center gap-2">
                      <Phone className="h-4 w-4 text-slate-400" />
                      <div>
                        <p className="text-sm text-slate-500">Contact During Leave</p>
                        <p className="font-medium">{application.contact_number}</p>
                      </div>
                    </div>
                  )}
                  {application.contact_address && (
                    <div>
                      <p className="text-sm text-slate-500">Contact Address</p>
                      <p className="font-medium">{application.contact_address}</p>
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
                      <Button variant="outline" onClick={() => {
                        setShowApprovalForm(false);
                        setRemarks('');
                      }}>
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
                      <Button variant="destructive" onClick={handleReject} disabled={actionLoading || !remarks}>
                        {actionLoading ? 'Processing...' : 'Confirm Rejection'}
                      </Button>
                      <Button variant="outline" onClick={() => {
                        setShowRejectionForm(false);
                        setRemarks('');
                      }}>
                        Cancel
                      </Button>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Status/Approval Info */}
          {(application.status === 'APPROVED' || application.status === 'REJECTED' || application.status === 'CANCELLED') && (
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
                      <span className="font-medium">
                        {application.approved_at ? new Date(application.approved_at).toLocaleDateString() : '-'}
                      </span>
                    </div>
                    {application.approver_remarks && (
                      <div>
                        <p className="text-sm text-slate-500">Remarks</p>
                        <p className="font-medium mt-1">{application.approver_remarks}</p>
                      </div>
                    )}
                  </div>
                )}

                {application.status === 'REJECTED' && (
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm text-slate-500">Rejected On</span>
                      <span className="font-medium">
                        {application.rejected_at ? new Date(application.rejected_at).toLocaleDateString() : '-'}
                      </span>
                    </div>
                    {application.rejection_reason && (
                      <div>
                        <p className="text-sm text-slate-500">Reason</p>
                        <p className="font-medium mt-1">{application.rejection_reason}</p>
                      </div>
                    )}
                  </div>
                )}

                {application.status === 'CANCELLED' && (
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm text-slate-500">Cancelled On</span>
                      <span className="font-medium">
                        {application.cancelled_at ? new Date(application.cancelled_at).toLocaleDateString() : '-'}
                      </span>
                    </div>
                    {application.cancellation_reason && (
                      <div>
                        <p className="text-sm text-slate-500">Reason</p>
                        <p className="font-medium mt-1">{application.cancellation_reason}</p>
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
                    <div className="w-px h-full bg-slate-200" />
                  </div>
                  <div>
                    <p className="text-sm font-medium">Applied</p>
                    <p className="text-xs text-slate-500">
                      {new Date(application.created_at).toLocaleString()}
                    </p>
                  </div>
                </div>

                {application.status !== 'PENDING' && (
                  <div className="flex gap-3">
                    <div className="flex flex-col items-center">
                      <div className={`h-2 w-2 rounded-full ${
                        application.status === 'APPROVED' ? 'bg-green-500' :
                        application.status === 'REJECTED' ? 'bg-red-500' :
                        'bg-slate-400'
                      }`} />
                    </div>
                    <div>
                      <p className="text-sm font-medium">{application.status}</p>
                      <p className="text-xs text-slate-500">
                        {application.approved_at && new Date(application.approved_at).toLocaleString()}
                        {application.rejected_at && new Date(application.rejected_at).toLocaleString()}
                        {application.cancelled_at && new Date(application.cancelled_at).toLocaleString()}
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
