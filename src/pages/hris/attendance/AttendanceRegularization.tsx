import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Check,
  Clock,
  Eye,
  MoreHorizontal,
  Search,
  X,
} from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { PageHeader } from '@/components/common/PageHeader';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { hrisApi, organizationsApi } from '@/services/api';

interface Regularization {
  id: string;
  employee_id: string;
  employee_name?: string;
  employee_code?: string;
  attendance_date: string;
  request_type: string;
  reason: string;
  original_first_in?: string;
  original_last_out?: string;
  original_status?: string;
  requested_first_in?: string;
  requested_last_out?: string;
  requested_status?: string;
  status: string;
  approved_at?: string;
  approver_remarks?: string;
  rejected_at?: string;
  rejection_reason?: string;
  created_at: string;
}

interface Organization {
  id: string;
  name: string;
}

const STATUS_OPTIONS = [
  { value: '__all__', label: 'All Statuses' },
  { value: 'PENDING', label: 'Pending' },
  { value: 'APPROVED', label: 'Approved' },
  { value: 'REJECTED', label: 'Rejected' },
];

const REQUEST_TYPE_LABELS: { [key: string]: string } = {
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

export function AttendanceRegularization() {
  const navigate = useNavigate();
  const [regularizations, setRegularizations] = useState<Regularization[]>([]);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [loading, setLoading] = useState(true);
  const [pagination, setPagination] = useState({ skip: 0, limit: 20, total: 0 });

  const [selectedOrgId, setSelectedOrgId] = useState<string>('');
  const [selectedStatus, setSelectedStatus] = useState<string>('PENDING');
  const [searchQuery, setSearchQuery] = useState<string>('');

  useEffect(() => {
    const fetchOrganizations = async () => {
      try {
        const response = await organizationsApi.list({ page_size: 100 });
        const orgs = response.data.items || response.data;
        setOrganizations(Array.isArray(orgs) ? orgs : []);
        if (orgs.length > 0 && !selectedOrgId) {
          setSelectedOrgId(orgs[0].id);
        }
      } catch (error) {
        console.error('Failed to fetch organizations:', error);
      }
    };
    fetchOrganizations();
  }, []);

  const fetchRegularizations = async (skip = 0) => {
    if (!selectedOrgId) return;
    try {
      setLoading(true);
      const params: any = {
        organization_id: selectedOrgId,
        skip,
        limit: pagination.limit,
      };
      if (selectedStatus !== '__all__') params.status = selectedStatus;
      if (searchQuery) params.search = searchQuery;

      const response = await hrisApi.listRegularizations(params);
      setRegularizations(response.data.items || []);
      setPagination((prev) => ({ ...prev, skip, total: response.data.total || 0 }));
    } catch (error) {
      console.error('Failed to fetch regularizations:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRegularizations(0);
  }, [selectedOrgId, selectedStatus]);

  const handleSearch = () => {
    fetchRegularizations(0);
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Regularization Requests"
        subtitle="Manage attendance regularization requests"
        breadcrumbs={[
          { label: 'Attendance', to: '/admin/hris/attendance' },
          { label: 'Regularization' },
        ]}
      />

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Clock className="h-5 w-5" />
              Regularization Requests
            </CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          {/* Filters */}
          <div className="grid gap-4 md:grid-cols-4 mb-6">
            <Select value={selectedOrgId} onValueChange={setSelectedOrgId}>
              <SelectTrigger>
                <SelectValue placeholder="Select Organization" />
              </SelectTrigger>
              <SelectContent>
                {organizations.map((org) => (
                  <SelectItem key={org.id} value={org.id}>
                    {org.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select value={selectedStatus} onValueChange={setSelectedStatus}>
              <SelectTrigger>
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                {STATUS_OPTIONS.map((opt) => (
                  <SelectItem key={opt.value} value={opt.value}>
                    {opt.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <div className="flex gap-2 md:col-span-2">
              <Input
                placeholder="Search by employee name or code..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              />
              <Button variant="outline" size="icon" onClick={handleSearch}>
                <Search className="h-4 w-4" />
              </Button>
            </div>
          </div>

          {/* Table */}
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <p className="text-sm text-slate-500">Loading...</p>
            </div>
          ) : regularizations.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8">
              <Clock className="h-12 w-12 text-slate-300 mb-4" />
              <p className="text-sm text-slate-500">No regularization requests found</p>
            </div>
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Employee</TableHead>
                    <TableHead>Date</TableHead>
                    <TableHead>Request Type</TableHead>
                    <TableHead>Original Time</TableHead>
                    <TableHead>Requested Time</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Submitted On</TableHead>
                    <TableHead className="w-[70px]">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {regularizations.map((request) => (
                    <TableRow key={request.id}>
                      <TableCell>
                        <div>
                          <p className="font-medium">{request.employee_name}</p>
                          <p className="text-xs text-slate-500">{request.employee_code}</p>
                        </div>
                      </TableCell>
                      <TableCell>{new Date(request.attendance_date).toLocaleDateString()}</TableCell>
                      <TableCell>
                        <Badge variant="outline">
                          {REQUEST_TYPE_LABELS[request.request_type] || request.request_type}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="text-sm">
                          <p>In: {formatTime(request.original_first_in)}</p>
                          <p>Out: {formatTime(request.original_last_out)}</p>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="text-sm">
                          <p>In: {formatTime(request.requested_first_in)}</p>
                          <p>Out: {formatTime(request.requested_last_out)}</p>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge className={getStatusBadgeColor(request.status)}>
                          {request.status}
                        </Badge>
                      </TableCell>
                      <TableCell>{new Date(request.created_at).toLocaleDateString()}</TableCell>
                      <TableCell>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={() => navigate(`/admin/hris/attendance/regularization/${request.id}`)}>
                              <Eye className="mr-2 h-4 w-4" />
                              View Details
                            </DropdownMenuItem>
                            {request.status === 'PENDING' && (
                              <>
                                <DropdownMenuItem onClick={() => navigate(`/admin/hris/attendance/regularization/${request.id}`)}>
                                  <Check className="mr-2 h-4 w-4" />
                                  Approve / Reject
                                </DropdownMenuItem>
                              </>
                            )}
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

              {/* Pagination */}
              <div className="mt-4 flex items-center justify-between">
                <p className="text-sm text-slate-500">
                  Showing {regularizations.length} of {pagination.total} requests
                </p>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={pagination.skip === 0}
                    onClick={() => fetchRegularizations(pagination.skip - pagination.limit)}
                  >
                    Previous
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={pagination.skip + pagination.limit >= pagination.total}
                    onClick={() => fetchRegularizations(pagination.skip + pagination.limit)}
                  >
                    Next
                  </Button>
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
