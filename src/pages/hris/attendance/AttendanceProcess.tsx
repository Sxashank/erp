import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Calendar,
  Clock,
  Play,
  RefreshCw,
} from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { PageHeader } from '@/components/common/PageHeader';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { hrisApi, organizationsApi } from '@/services/api';

interface Organization {
  id: string;
  name: string;
}

interface ProcessingResult {
  processed_count: number;
  present_count: number;
  absent_count: number;
  half_day_count: number;
  leave_count: number;
  holiday_count: number;
  week_off_count: number;
  errors?: string[];
}

export function AttendanceProcess() {
  const navigate = useNavigate();
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [selectedOrgId, setSelectedOrgId] = useState<string>('');
  const [processDate, setProcessDate] = useState<string>(new Date().toISOString().split('T')[0]);
  const [dateRangeStart, setDateRangeStart] = useState<string>('');
  const [dateRangeEnd, setDateRangeEnd] = useState<string>('');
  const [processMode, setProcessMode] = useState<'single' | 'range'>('single');
  const [processing, setProcessing] = useState(false);
  const [result, setResult] = useState<ProcessingResult | null>(null);

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

  const handleProcess = async () => {
    if (!selectedOrgId) return;

    try {
      setProcessing(true);
      setResult(null);

      const params: any = {
        organization_id: selectedOrgId,
      };

      if (processMode === 'single') {
        const response = await hrisApi.processDailyAttendance({
          organization_id: selectedOrgId,
          attendance_date: processDate,
        });
        setResult(response.data);
      } else {
        // Process each day in range
        const from = new Date(dateRangeStart);
        const to = new Date(dateRangeEnd);
        let totalResult = {
          processed_count: 0,
          present_count: 0,
          absent_count: 0,
          half_day_count: 0,
          leave_count: 0,
          holiday_count: 0,
          week_off_count: 0,
          errors: [] as string[],
        };

        for (let d = new Date(from); d <= to; d.setDate(d.getDate() + 1)) {
          try {
            const response = await hrisApi.processDailyAttendance({
              organization_id: selectedOrgId,
              attendance_date: d.toISOString().split('T')[0],
            });
            totalResult.processed_count += response.data.processed_count || 0;
            totalResult.present_count += response.data.present_count || 0;
            totalResult.absent_count += response.data.absent_count || 0;
            totalResult.half_day_count += response.data.half_day_count || 0;
            totalResult.leave_count += response.data.leave_count || 0;
            totalResult.holiday_count += response.data.holiday_count || 0;
            totalResult.week_off_count += response.data.week_off_count || 0;
          } catch (err) {
            totalResult.errors?.push(`Failed for ${d.toISOString().split('T')[0]}`);
          }
        }
        setResult(totalResult);
      }
    } catch (error) {
      console.error('Failed to process attendance:', error);
      setResult({
        processed_count: 0,
        present_count: 0,
        absent_count: 0,
        half_day_count: 0,
        leave_count: 0,
        holiday_count: 0,
        week_off_count: 0,
        errors: ['Failed to process attendance. Please try again.'],
      });
    } finally {
      setProcessing(false);
    }
  };

  const handleReprocess = async () => {
    if (!selectedOrgId || !processDate) return;

    try {
      setProcessing(true);
      setResult(null);

      const response = await hrisApi.processDailyAttendance({
        organization_id: selectedOrgId,
        attendance_date: processDate,
      });
      setResult(response.data);
    } catch (error) {
      console.error('Failed to reprocess attendance:', error);
    } finally {
      setProcessing(false);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Process Attendance"
        subtitle="Process raw punch data into attendance records"
        breadcrumbs={[
          { label: 'Attendance', to: '/admin/hris/attendance' },
          { label: 'Process' },
        ]}
      />

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Processing Form */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock className="h-5 w-5" />
              Processing Options
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-2">
              <Label>Organization *</Label>
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
            </div>

            <div className="space-y-2">
              <Label>Processing Mode</Label>
              <Select value={processMode} onValueChange={(v) => setProcessMode(v as 'single' | 'range')}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="single">Single Date</SelectItem>
                  <SelectItem value="range">Date Range</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {processMode === 'single' ? (
              <div className="space-y-2">
                <Label htmlFor="processDate">Date *</Label>
                <Input
                  id="processDate"
                  type="date"
                  value={processDate}
                  onChange={(e) => setProcessDate(e.target.value)}
                />
              </div>
            ) : (
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="dateRangeStart">From Date *</Label>
                  <Input
                    id="dateRangeStart"
                    type="date"
                    value={dateRangeStart}
                    onChange={(e) => setDateRangeStart(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="dateRangeEnd">To Date *</Label>
                  <Input
                    id="dateRangeEnd"
                    type="date"
                    value={dateRangeEnd}
                    onChange={(e) => setDateRangeEnd(e.target.value)}
                  />
                </div>
              </div>
            )}

            <div className="flex gap-2 pt-4">
              <Button onClick={handleProcess} disabled={processing}>
                <Play className="mr-2 h-4 w-4" />
                {processing ? 'Processing...' : 'Process Attendance'}
              </Button>
              {processMode === 'single' && (
                <Button variant="outline" onClick={handleReprocess} disabled={processing}>
                  <RefreshCw className="mr-2 h-4 w-4" />
                  Reprocess
                </Button>
              )}
            </div>

            <div className="pt-4 text-sm text-slate-500">
              <h4 className="font-medium text-slate-700 mb-2">Processing Notes:</h4>
              <ul className="list-disc list-inside space-y-1">
                <li>Processes raw punch records into daily attendance</li>
                <li>Calculates work hours, late arrivals, early leaves</li>
                <li>Applies shift rules and grace periods</li>
                <li>Identifies holidays and week-offs</li>
                <li>Reprocess will recalculate existing records</li>
              </ul>
            </div>
          </CardContent>
        </Card>

        {/* Results */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calendar className="h-5 w-5" />
              Processing Results
            </CardTitle>
          </CardHeader>
          <CardContent>
            {!result ? (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <Clock className="h-12 w-12 text-slate-300 mb-4" />
                <p className="text-sm text-slate-500">
                  Select options and click Process to see results
                </p>
              </div>
            ) : (
              <div className="space-y-6">
                {/* Summary Cards */}
                <div className="grid gap-4 grid-cols-2">
                  <div className="p-4 bg-slate-50 rounded-lg">
                    <p className="text-sm text-slate-500">Total Processed</p>
                    <p className="text-2xl font-bold">{result.processed_count}</p>
                  </div>
                  <div className="p-4 bg-green-50 rounded-lg">
                    <p className="text-sm text-green-700">Present</p>
                    <p className="text-2xl font-bold text-green-700">{result.present_count}</p>
                  </div>
                  <div className="p-4 bg-red-50 rounded-lg">
                    <p className="text-sm text-red-700">Absent</p>
                    <p className="text-2xl font-bold text-red-700">{result.absent_count}</p>
                  </div>
                  <div className="p-4 bg-amber-50 rounded-lg">
                    <p className="text-sm text-amber-700">Half Day</p>
                    <p className="text-2xl font-bold text-amber-700">{result.half_day_count}</p>
                  </div>
                </div>

                {/* Breakdown */}
                <div className="space-y-3">
                  <h4 className="font-medium text-sm text-slate-700">Breakdown</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-slate-500">On Leave</span>
                      <Badge variant="outline">{result.leave_count}</Badge>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-slate-500">Holidays</span>
                      <Badge variant="outline">{result.holiday_count}</Badge>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-slate-500">Week Offs</span>
                      <Badge variant="outline">{result.week_off_count}</Badge>
                    </div>
                  </div>
                </div>

                {/* Errors */}
                {result.errors && result.errors.length > 0 && (
                  <div className="space-y-2">
                    <h4 className="font-medium text-sm text-red-700">Errors</h4>
                    <div className="p-3 bg-red-50 rounded-lg">
                      <ul className="list-disc list-inside space-y-1 text-sm text-red-700">
                        {result.errors.map((error, index) => (
                          <li key={index}>{error}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                )}

                {/* Actions */}
                <div className="pt-4">
                  <Button variant="outline" className="w-full" onClick={() => navigate('/admin/hris/attendance')}>
                    View Attendance Records
                  </Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
