import {
  Calendar,
  Edit,
  MoreHorizontal,
  Plus,
  Trash2,
} from 'lucide-react';
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { PageHeader } from '@/components/common/PageHeader';
import { HrisConfirmDialog } from '@/components/hris/HrisConfirmDialog';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
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

import { logger } from "@/lib/logger";
interface LeaveType {
  id: string;
  leave_code: string;
  leave_name: string;
  category: string;
  annual_quota: number;
  carry_forward_allowed: boolean;
  encashment_allowed: boolean;
  is_paid: boolean;
  is_active: boolean;
}

interface Organization {
  id: string;
  name: string;
}

const getCategoryBadgeColor = (category: string) => {
  switch (category) {
    case 'CASUAL':
      return 'bg-blue-50 text-blue-700';
    case 'SICK':
      return 'bg-red-50 text-red-700';
    case 'EARNED':
      return 'bg-green-50 text-green-700';
    case 'MATERNITY':
      return 'bg-pink-50 text-pink-700';
    case 'PATERNITY':
      return 'bg-purple-50 text-purple-700';
    case 'COMP_OFF':
      return 'bg-amber-50 text-amber-700';
    case 'LOP':
      return 'bg-slate-100 text-slate-600';
    default:
      return 'bg-slate-100 text-slate-600';
  }
};

export function LeaveTypeList() {
  const navigate = useNavigate();
  const [leaveTypes, setLeaveTypes] = useState<LeaveType[]>([]);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedOrgId, setSelectedOrgId] = useState<string>('');
  const [deleteLeaveTypeId, setDeleteLeaveTypeId] = useState<string | null>(null);
  const [deleteBusy, setDeleteBusy] = useState(false);

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
        logger.error('Failed to fetch organizations:', error);
      }
    };
    fetchOrganizations();
  }, []);

  useEffect(() => {
    const fetchLeaveTypes = async () => {
      if (!selectedOrgId) return;
      try {
        setLoading(true);
        const response = await hrisApi.listLeaveTypes({ organization_id: selectedOrgId });
        setLeaveTypes(response.data.items || response.data || []);
      } catch (error) {
        logger.error('Failed to fetch leave types:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchLeaveTypes();
  }, [selectedOrgId]);

  const executeDelete = async () => {
    if (!deleteLeaveTypeId) return;
    try {
      setDeleteBusy(true);
      await hrisApi.deleteLeaveType(deleteLeaveTypeId);
      setLeaveTypes(leaveTypes.filter((lt) => lt.id !== deleteLeaveTypeId));
      setDeleteLeaveTypeId(null);
    } catch (error) {
      logger.error('Failed to delete leave type:', error);
    } finally {
      setDeleteBusy(false);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Leave Types"
        subtitle="Configure leave types and policies"
        actions={
          <Button onClick={() => navigate('/admin/hris/leave-types/new')}>
            <Plus className="mr-2 h-4 w-4" />
            Add Leave Type
          </Button>
        }
      />

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Calendar className="h-5 w-5" />
              Leave Type List
            </CardTitle>
            <Select value={selectedOrgId} onValueChange={setSelectedOrgId}>
              <SelectTrigger className="w-[200px]">
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
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <p className="text-sm text-slate-500">Loading...</p>
            </div>
          ) : leaveTypes.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8">
              <Calendar className="h-12 w-12 text-slate-300 mb-4" />
              <p className="text-sm text-slate-500">No leave types found</p>
              <Button variant="link" onClick={() => navigate('/admin/hris/leave-types/new')}>
                Add your first leave type
              </Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Code</TableHead>
                  <TableHead>Name</TableHead>
                  <TableHead>Category</TableHead>
                  <TableHead>Annual Quota</TableHead>
                  <TableHead>Carry Forward</TableHead>
                  <TableHead>Encashment</TableHead>
                  <TableHead>Paid</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="w-[70px]">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {leaveTypes.map((leaveType) => (
                  <TableRow key={leaveType.id}>
                    <TableCell className="font-medium">{leaveType.leave_code}</TableCell>
                    <TableCell>{leaveType.leave_name}</TableCell>
                    <TableCell>
                      <Badge className={getCategoryBadgeColor(leaveType.category)}>
                        {leaveType.category}
                      </Badge>
                    </TableCell>
                    <TableCell>{leaveType.annual_quota} days</TableCell>
                    <TableCell>
                      <Badge variant={leaveType.carry_forward_allowed ? 'default' : 'secondary'}>
                        {leaveType.carry_forward_allowed ? 'Yes' : 'No'}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant={leaveType.encashment_allowed ? 'default' : 'secondary'}>
                        {leaveType.encashment_allowed ? 'Yes' : 'No'}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant={leaveType.is_paid ? 'default' : 'secondary'}>
                        {leaveType.is_paid ? 'Paid' : 'Unpaid'}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant={leaveType.is_active ? 'default' : 'secondary'}>
                        {leaveType.is_active ? 'Active' : 'Inactive'}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon">
                            <MoreHorizontal className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => navigate(`/admin/hris/leave-types/${leaveType.id}/edit`)}>
                            <Edit className="mr-2 h-4 w-4" />
                            Edit
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            onClick={() => setDeleteLeaveTypeId(leaveType.id)}
                            className="text-red-600"
                          >
                            <Trash2 className="mr-2 h-4 w-4" />
                            Delete
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
      <HrisConfirmDialog
        open={Boolean(deleteLeaveTypeId)}
        title="Delete leave type"
        description="This removes the leave type from future HRIS leave setup. Existing balances and applications should be reviewed before deletion."
        confirmLabel="Delete leave type"
        destructive
        busy={deleteBusy}
        onOpenChange={(open) => {
          if (!open && !deleteBusy) setDeleteLeaveTypeId(null);
        }}
        onConfirm={executeDelete}
      />
    </div>
  );
}
