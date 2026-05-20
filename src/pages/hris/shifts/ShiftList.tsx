import {
  Clock,
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
interface Shift {
  id: string;
  shiftCode: string;
  shiftName: string;
  shiftType: string;
  startTime: string;
  endTime: string;
  breakDurationMinutes: number;
  workingHours: number;
  gracePeriodMinutes: number;
  isNightShift: boolean;
  isActive: boolean;
}

interface Organization {
  id: string;
  name: string;
}

const formatTime = (time: string) => {
  if (!time) return '-';
  const [hours, minutes] = time.split(':');
  const h = parseInt(hours, 10);
  const ampm = h >= 12 ? 'PM' : 'AM';
  const displayHour = h % 12 || 12;
  return `${displayHour}:${minutes} ${ampm}`;
};

export function ShiftList() {
  const navigate = useNavigate();
  const [shifts, setShifts] = useState<Shift[]>([]);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedOrgId, setSelectedOrgId] = useState<string>('');
  const [deleteShiftId, setDeleteShiftId] = useState<string | null>(null);
  const [deleteBusy, setDeleteBusy] = useState(false);

  useEffect(() => {
    const fetchOrganizations = async () => {
      try {
        const response = await organizationsApi.list({ pageSize: 100 });
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
    const fetchShifts = async () => {
      if (!selectedOrgId) return;
      try {
        setLoading(true);
        const response = await hrisApi.listShifts({});
        setShifts(response.data.items || response.data || []);
      } catch (error) {
        logger.error('Failed to fetch shifts:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchShifts();
  }, [selectedOrgId]);

  const executeDelete = async () => {
    if (!deleteShiftId) return;
    try {
      setDeleteBusy(true);
      await hrisApi.deleteShift(deleteShiftId);
      setShifts(shifts.filter((s) => s.id !== deleteShiftId));
      setDeleteShiftId(null);
    } catch (error) {
      logger.error('Failed to delete shift:', error);
    } finally {
      setDeleteBusy(false);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Shifts"
        subtitle="Manage work shifts and timings"
        actions={
          <Button onClick={() => navigate('/admin/hris/shifts/new')}>
            <Plus className="mr-2 h-4 w-4" />
            Add Shift
          </Button>
        }
      />

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Clock className="h-5 w-5" />
              Shift List
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
          ) : shifts.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8">
              <Clock className="h-12 w-12 text-slate-300 mb-4" />
              <p className="text-sm text-slate-500">No shifts found</p>
              <Button variant="link" onClick={() => navigate('/admin/hris/shifts/new')}>
                Add your first shift
              </Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Code</TableHead>
                  <TableHead>Name</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Start Time</TableHead>
                  <TableHead>End Time</TableHead>
                  <TableHead>Working Hours</TableHead>
                  <TableHead>Break (mins)</TableHead>
                  <TableHead>Night Shift</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="w-[70px]">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {shifts.map((shift) => (
                  <TableRow key={shift.id}>
                    <TableCell className="font-medium">{shift.shiftCode}</TableCell>
                    <TableCell>{shift.shiftName}</TableCell>
                    <TableCell>
                      <Badge variant="outline">{shift.shiftType}</Badge>
                    </TableCell>
                    <TableCell>{formatTime(shift.startTime)}</TableCell>
                    <TableCell>{formatTime(shift.endTime)}</TableCell>
                    <TableCell>{shift.workingHours} hrs</TableCell>
                    <TableCell>{shift.breakDurationMinutes}</TableCell>
                    <TableCell>
                      <Badge variant={shift.isNightShift ? 'default' : 'secondary'}>
                        {shift.isNightShift ? 'Yes' : 'No'}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant={shift.isActive ? 'default' : 'secondary'}>
                        {shift.isActive ? 'Active' : 'Inactive'}
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
                          <DropdownMenuItem onClick={() => navigate(`/admin/hris/shifts/${shift.id}/edit`)}>
                            <Edit className="mr-2 h-4 w-4" />
                            Edit
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            onClick={() => setDeleteShiftId(shift.id)}
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
        open={Boolean(deleteShiftId)}
        title="Delete shift"
        description="This removes the shift from future roster and attendance setup. Existing processed attendance should be reviewed before deletion."
        confirmLabel="Delete shift"
        destructive
        busy={deleteBusy}
        onOpenChange={(open) => {
          if (!open && !deleteBusy) setDeleteShiftId(null);
        }}
        onConfirm={executeDelete}
      />
    </div>
  );
}
