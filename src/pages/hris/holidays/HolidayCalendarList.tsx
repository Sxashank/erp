import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Calendar,
  CalendarDays,
  Edit,
  Eye,
  MoreHorizontal,
  Plus,
  Trash2,
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

interface HolidayCalendar {
  id: string;
  calendar_name: string;
  year: number;
  is_default: boolean;
  is_active: boolean;
  holiday_count?: number;
}

interface Organization {
  id: string;
  name: string;
}

export function HolidayCalendarList() {
  const navigate = useNavigate();
  const [calendars, setCalendars] = useState<HolidayCalendar[]>([]);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedOrgId, setSelectedOrgId] = useState<string>('');
  const [selectedYear, setSelectedYear] = useState<string>(new Date().getFullYear().toString());

  const years = Array.from({ length: 5 }, (_, i) => (new Date().getFullYear() - 1 + i).toString());

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

  useEffect(() => {
    const fetchCalendars = async () => {
      if (!selectedOrgId) return;
      try {
        setLoading(true);
        const response = await hrisApi.listHolidayCalendars({
          organization_id: selectedOrgId,
          year: parseInt(selectedYear, 10),
        });
        setCalendars(response.data.items || response.data || []);
      } catch (error) {
        console.error('Failed to fetch holiday calendars:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchCalendars();
  }, [selectedOrgId, selectedYear]);

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this holiday calendar?')) return;
    try {
      await hrisApi.deleteHolidayCalendar(id);
      setCalendars(calendars.filter((c) => c.id !== id));
    } catch (error) {
      console.error('Failed to delete holiday calendar:', error);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Holiday Calendars"
        subtitle="Manage organizational holiday calendars"
        actions={
          <Button onClick={() => navigate('/admin/hris/holidays/new')}>
            <Plus className="mr-2 h-4 w-4" />
            Add Calendar
          </Button>
        }
      />

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <CalendarDays className="h-5 w-5" />
              Holiday Calendar List
            </CardTitle>
            <div className="flex gap-2">
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
              <Select value={selectedYear} onValueChange={setSelectedYear}>
                <SelectTrigger className="w-[120px]">
                  <SelectValue placeholder="Year" />
                </SelectTrigger>
                <SelectContent>
                  {years.map((year) => (
                    <SelectItem key={year} value={year}>
                      {year}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <p className="text-sm text-slate-500">Loading...</p>
            </div>
          ) : calendars.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8">
              <Calendar className="h-12 w-12 text-slate-300 mb-4" />
              <p className="text-sm text-slate-500">No holiday calendars found for {selectedYear}</p>
              <Button variant="link" onClick={() => navigate('/admin/hris/holidays/new')}>
                Create a holiday calendar
              </Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Calendar Name</TableHead>
                  <TableHead>Year</TableHead>
                  <TableHead>Holidays</TableHead>
                  <TableHead>Default</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="w-[70px]">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {calendars.map((calendar) => (
                  <TableRow key={calendar.id}>
                    <TableCell className="font-medium">{calendar.calendar_name}</TableCell>
                    <TableCell>{calendar.year}</TableCell>
                    <TableCell>{calendar.holiday_count || 0} holidays</TableCell>
                    <TableCell>
                      <Badge variant={calendar.is_default ? 'default' : 'secondary'}>
                        {calendar.is_default ? 'Yes' : 'No'}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant={calendar.is_active ? 'default' : 'secondary'}>
                        {calendar.is_active ? 'Active' : 'Inactive'}
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
                          <DropdownMenuItem onClick={() => navigate(`/admin/hris/holidays/${calendar.id}`)}>
                            <Eye className="mr-2 h-4 w-4" />
                            View Holidays
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => navigate(`/admin/hris/holidays/${calendar.id}/edit`)}>
                            <Edit className="mr-2 h-4 w-4" />
                            Edit
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            onClick={() => handleDelete(calendar.id)}
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
    </div>
  );
}
