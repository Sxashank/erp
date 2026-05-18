/**
 * ESS Profile Page
 * View and request updates to employee profile
 */

import {
  User,
  Mail,
  Phone,
  MapPin,
  Building,
  Calendar,
  CreditCard,
  Shield,
  Edit,
  Loader2,
  Clock,
  CheckCircle,
  XCircle,
} from 'lucide-react';
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

import { DateDisplay } from '@/components/common/DateDisplay';
import { PageHeader } from '@/components/common/PageHeader';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Textarea } from '@/components/ui/textarea';
import { essProfileApi } from '@/services/essApi';
import { useEssAuthStore } from '@/stores/essAuthStore';
import type { ESSProfile, ESSProfileUpdateRequest, ProfileUpdateType } from '@/types/ess';

import { logger } from "@/lib/logger";
export default function ESSProfilePage() {
  const navigate = useNavigate();
  const accessToken = useEssAuthStore((state) => state.accessToken);
  const [loading, setLoading] = useState(true);
  const [profile, setProfile] = useState<ESSProfile | null>(null);
  const [updateRequests, setUpdateRequests] = useState<ESSProfileUpdateRequest[]>([]);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editType, setEditType] = useState<ProfileUpdateType>('PERSONAL');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!accessToken) {
      navigate('/ess/login');
      return;
    }
    fetchData();
  }, [accessToken, navigate]);

  const fetchData = async () => {
    try {
      const [profileRes, requestsRes] = await Promise.all([
        essProfileApi.getProfile(),
        essProfileApi.getUpdateRequests(),
      ]);
      setProfile(profileRes.data);
      setUpdateRequests(Array.isArray(requestsRes.data) ? requestsRes.data : requestsRes.data?.items || []);
    } catch (error) {
      logger.error('Failed to fetch profile:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitRequest = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);

    setSubmitting(true);
    try {
      const requestedValues: Record<string, any> = {};
      formData.forEach((value, key) => {
        if (key !== 'change_reason' && value) {
          requestedValues[key] = value;
        }
      });

      await essProfileApi.requestUpdate({
        update_type: editType,
        requested_values: requestedValues,
        change_reason: formData.get('change_reason') as string,
      });

      setEditDialogOpen(false);
      fetchData();
    } catch (error) {
      logger.error('Failed to submit request:', error);
    } finally {
      setSubmitting(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'PENDING':
        return <Badge variant="secondary" className="bg-yellow-100 text-yellow-700"><Clock className="h-3 w-3 mr-1" />Pending</Badge>;
      case 'APPROVED':
        return <Badge variant="secondary" className="bg-green-100 text-green-700"><CheckCircle className="h-3 w-3 mr-1" />Approved</Badge>;
      case 'REJECTED':
        return <Badge variant="secondary" className="bg-red-100 text-red-700"><XCircle className="h-3 w-3 mr-1" />Rejected</Badge>;
      default:
        return <Badge variant="secondary">{status}</Badge>;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  const requestUpdateDialog = (
    <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
      <DialogTrigger asChild>
        <Button>
          <Edit className="h-4 w-4 mr-2" />
          Request Update
        </Button>
      </DialogTrigger>
          <DialogContent className="max-w-lg">
            <DialogHeader>
              <DialogTitle>Request Profile Update</DialogTitle>
              <DialogDescription>
                Submit a request to update your profile information. HR will review and approve the changes.
              </DialogDescription>
            </DialogHeader>
            <form onSubmit={handleSubmitRequest} className="space-y-4">
              <div>
                <Label>Update Type</Label>
                <Select value={editType} onValueChange={(v) => setEditType(v as ProfileUpdateType)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="PERSONAL">Personal Details</SelectItem>
                    <SelectItem value="CONTACT">Contact Information</SelectItem>
                    <SelectItem value="ADDRESS">Address</SelectItem>
                    <SelectItem value="BANK">Bank Details</SelectItem>
                    <SelectItem value="EMERGENCY_CONTACT">Emergency Contact</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {editType === 'CONTACT' && (
                <>
                  <div>
                    <Label htmlFor="personal_email">Personal Email</Label>
                    <Input id="personal_email" name="personal_email" type="email" placeholder="Enter new email" />
                  </div>
                  <div>
                    <Label htmlFor="mobile">Mobile Number</Label>
                    <Input id="mobile" name="mobile" placeholder="Enter new mobile" />
                  </div>
                </>
              )}

              {editType === 'ADDRESS' && (
                <>
                  <div>
                    <Label htmlFor="current_address">Current Address</Label>
                    <Textarea id="current_address" name="current_address" placeholder="Enter new address" />
                  </div>
                  <div>
                    <Label htmlFor="permanent_address">Permanent Address</Label>
                    <Textarea id="permanent_address" name="permanent_address" placeholder="Enter permanent address" />
                  </div>
                </>
              )}

              {editType === 'BANK' && (
                <>
                  <div>
                    <Label htmlFor="bank_name">Bank Name</Label>
                    <Input id="bank_name" name="bank_name" placeholder="Enter bank name" />
                  </div>
                  <div>
                    <Label htmlFor="bank_account_number">Account Number</Label>
                    <Input id="bank_account_number" name="bank_account_number" placeholder="Enter account number" />
                  </div>
                  <div>
                    <Label htmlFor="ifsc_code">IFSC Code</Label>
                    <Input id="ifsc_code" name="ifsc_code" placeholder="Enter IFSC code" />
                  </div>
                </>
              )}

              {editType === 'EMERGENCY_CONTACT' && (
                <>
                  <div>
                    <Label htmlFor="emergency_contact_name">Contact Name</Label>
                    <Input id="emergency_contact_name" name="emergency_contact_name" placeholder="Enter name" />
                  </div>
                  <div>
                    <Label htmlFor="emergency_contact_phone">Contact Phone</Label>
                    <Input id="emergency_contact_phone" name="emergency_contact_phone" placeholder="Enter phone" />
                  </div>
                </>
              )}

              <div>
                <Label htmlFor="change_reason">Reason for Change</Label>
                <Textarea id="change_reason" name="change_reason" placeholder="Explain why you need this update" required />
              </div>

              <div className="flex gap-3 justify-end">
                <Button type="button" variant="outline" onClick={() => setEditDialogOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit" disabled={submitting}>
                  {submitting && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                  Submit Request
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
  );

  return (
    <div className="space-y-6">
      <PageHeader
        title="My Profile"
        subtitle="View and manage your personal information"
        actions={requestUpdateDialog}
      />

      <Tabs defaultValue="profile" className="space-y-6">
        <TabsList>
          <TabsTrigger value="profile">Profile Details</TabsTrigger>
          <TabsTrigger value="requests">Update Requests</TabsTrigger>
        </TabsList>

        <TabsContent value="profile" className="space-y-6">
          {/* Profile Header Card */}
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center gap-6">
                <Avatar className="h-24 w-24">
                  <AvatarImage src={profile?.profile_photo_url} />
                  <AvatarFallback className="bg-blue-600 text-white text-2xl">
                    {profile?.first_name?.charAt(0)}{profile?.last_name?.charAt(0)}
                  </AvatarFallback>
                </Avatar>
                <div>
                  <h2 className="text-2xl font-bold">{profile?.full_name}</h2>
                  <p className="text-gray-500">{profile?.designation}</p>
                  <p className="text-sm text-gray-400">{profile?.department}</p>
                  <p className="text-sm text-gray-400 mt-1">Employee ID: {profile?.employee_code}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Personal Information */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <User className="h-4 w-4" />
                  Personal Information
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between">
                  <span className="text-gray-500">Date of Birth</span>
                  <span>{profile?.date_of_birth || '-'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Gender</span>
                  <span>{profile?.gender || '-'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Marital Status</span>
                  <span>{profile?.marital_status || '-'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Blood Group</span>
                  <span>{profile?.blood_group || '-'}</span>
                </div>
              </CardContent>
            </Card>

            {/* Contact Information */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Phone className="h-4 w-4" />
                  Contact Information
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between">
                  <span className="text-gray-500">Official Email</span>
                  <span className="text-sm">{profile?.email || '-'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Personal Email</span>
                  <span className="text-sm">{profile?.personal_email || '-'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Mobile</span>
                  <span>{profile?.mobile || '-'}</span>
                </div>
              </CardContent>
            </Card>

            {/* Employment Information */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Building className="h-4 w-4" />
                  Employment Information
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between">
                  <span className="text-gray-500">Date of Joining</span>
                  <span>{profile?.date_of_joining || '-'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Employment Type</span>
                  <span>{profile?.employment_type || '-'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Work Location</span>
                  <span>{profile?.work_location || '-'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Reporting Manager</span>
                  <span>{profile?.reporting_manager || '-'}</span>
                </div>
              </CardContent>
            </Card>

            {/* Bank Details */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <CreditCard className="h-4 w-4" />
                  Bank Details
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between">
                  <span className="text-gray-500">Bank Name</span>
                  <span>{profile?.bank_name || '-'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Account Number</span>
                  <span>{profile?.bank_account_number ? `****${profile.bank_account_number.slice(-4)}` : '-'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">IFSC Code</span>
                  <span>{profile?.ifsc_code || '-'}</span>
                </div>
              </CardContent>
            </Card>

            {/* Identity Documents */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Shield className="h-4 w-4" />
                  Identity Documents
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between">
                  <span className="text-gray-500">PAN Number</span>
                  <span>{profile?.pan_number ? `${profile.pan_number.slice(0, 4)}****${profile.pan_number.slice(-1)}` : '-'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Aadhaar Number</span>
                  <span>{profile?.aadhaar_number ? `****${profile.aadhaar_number.slice(-4)}` : '-'}</span>
                </div>
              </CardContent>
            </Card>

            {/* Emergency Contact */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Phone className="h-4 w-4" />
                  Emergency Contact
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between">
                  <span className="text-gray-500">Contact Name</span>
                  <span>{profile?.emergency_contact_name || '-'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Contact Phone</span>
                  <span>{profile?.emergency_contact_phone || '-'}</span>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Address */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <MapPin className="h-4 w-4" />
                Address
              </CardTitle>
            </CardHeader>
            <CardContent className="grid md:grid-cols-2 gap-6">
              <div>
                <p className="text-sm text-gray-500 mb-2">Current Address</p>
                <p className="text-sm">{profile?.current_address || 'Not provided'}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500 mb-2">Permanent Address</p>
                <p className="text-sm">{profile?.permanent_address || 'Not provided'}</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="requests">
          <Card>
            <CardHeader>
              <CardTitle>Update Requests</CardTitle>
              <CardDescription>Track your profile update requests</CardDescription>
            </CardHeader>
            <CardContent>
              {updateRequests.length > 0 ? (
                <div className="space-y-4">
                  {updateRequests.map((request) => (
                    <div key={request.id} className="p-4 border rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-medium">{request.update_type.replace('_', ' ')}</span>
                        {getStatusBadge(request.status)}
                      </div>
                      <p className="text-sm text-gray-500">Request #: {request.request_number}</p>
                      <p className="text-sm text-gray-500">
                        Submitted: <DateDisplay date={request.created_at} />
                      </p>
                      {request.reviewer_remarks && (
                        <p className="text-sm text-gray-600 mt-2">
                          Remarks: {request.reviewer_remarks}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <Edit className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  <p>No update requests</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
