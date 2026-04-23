import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Link } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { PageHeader } from '@/components/common/PageHeader';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Textarea } from '@/components/ui/textarea';
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
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import {
  ArrowLeft,
  Calendar,
  Clock,
  Play,
  Pause,
  Trash2,
  Edit,
  Mail,
  Plus,
  RefreshCw,
  FileText,
  CheckCircle,
  XCircle,
  AlertCircle,
} from 'lucide-react';

const scheduleSchema = z.object({
  reportType: z.string().min(1, 'Report type is required'),
  reportName: z.string().min(1, 'Report name is required'),
  frequency: z.string().min(1, 'Frequency is required'),
  dayOfWeek: z.string().optional(),
  dayOfMonth: z.string().optional(),
  time: z.string().min(1, 'Time is required'),
  format: z.string().min(1, 'Format is required'),
  recipients: z.string().min(1, 'At least one recipient is required'),
  isActive: z.boolean(),
  description: z.string().optional(),
});

type ScheduleFormData = z.infer<typeof scheduleSchema>;

// Report types
const reportTypes = [
  { value: 'portfolio_summary', label: 'Portfolio Summary', category: 'MIS' },
  { value: 'disbursement', label: 'Disbursement Report', category: 'MIS' },
  { value: 'collection', label: 'Collection Report', category: 'MIS' },
  { value: 'delinquency', label: 'Delinquency Report', category: 'MIS' },
  { value: 'npa', label: 'NPA Classification', category: 'Regulatory' },
  { value: 'alm', label: 'ALM Report', category: 'Regulatory' },
  { value: 'crar', label: 'CRAR Report', category: 'Regulatory' },
  { value: 'trial_balance', label: 'Trial Balance', category: 'Financial' },
  { value: 'profit_loss', label: 'Profit & Loss', category: 'Financial' },
  { value: 'branch_performance', label: 'Branch Performance', category: 'MIS' },
];

// Mock scheduled reports
interface ScheduleItem {
  id: string;
  reportType: string;
  reportName: string;
  frequency: string;
  dayOfWeek?: string;
  dayOfMonth?: string;
  time: string;
  format: string;
  recipients: string;
  isActive: boolean;
  lastRun: string;
  lastStatus: string;
  nextRun: string;
  description?: string;
}

const initialSchedules: ScheduleItem[] = [
  {
    id: '1',
    reportType: 'collection',
    reportName: 'Daily Collection Report',
    frequency: 'DAILY',
    time: '06:00',
    format: 'xlsx',
    recipients: 'ops@company.com, management@company.com',
    isActive: true,
    lastRun: '2025-01-15 06:00',
    lastStatus: 'SUCCESS',
    nextRun: '2025-01-16 06:00',
  },
  {
    id: '2',
    reportType: 'portfolio_summary',
    reportName: 'Weekly MIS Report',
    frequency: 'WEEKLY',
    dayOfWeek: '1',
    time: '09:00',
    format: 'pdf',
    recipients: 'ceo@company.com, cfo@company.com',
    isActive: true,
    lastRun: '2025-01-13 09:00',
    lastStatus: 'SUCCESS',
    nextRun: '2025-01-20 09:00',
  },
  {
    id: '3',
    reportType: 'alm',
    reportName: 'Monthly ALM Report',
    frequency: 'MONTHLY',
    dayOfMonth: '1',
    time: '08:00',
    format: 'pdf',
    recipients: 'compliance@company.com, treasury@company.com',
    isActive: true,
    lastRun: '2025-01-01 08:00',
    lastStatus: 'SUCCESS',
    nextRun: '2025-02-01 08:00',
  },
  {
    id: '4',
    reportType: 'npa',
    reportName: 'NPA Classification Report',
    frequency: 'MONTHLY',
    dayOfMonth: '5',
    time: '10:00',
    format: 'xlsx',
    recipients: 'risk@company.com, compliance@company.com',
    isActive: false,
    lastRun: '2025-01-05 10:00',
    lastStatus: 'FAILED',
    nextRun: '-',
  },
  {
    id: '5',
    reportType: 'delinquency',
    reportName: 'Delinquency Alert Report',
    frequency: 'DAILY',
    time: '07:00',
    format: 'xlsx',
    recipients: 'collections@company.com',
    isActive: true,
    lastRun: '2025-01-15 07:00',
    lastStatus: 'SUCCESS',
    nextRun: '2025-01-16 07:00',
  },
];

export default function ReportScheduler() {
  const [schedules, setSchedules] = useState<ScheduleItem[]>(initialSchedules);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);

  const form = useForm<ScheduleFormData>({
    resolver: zodResolver(scheduleSchema),
    defaultValues: {
      reportType: '',
      reportName: '',
      frequency: 'DAILY',
      dayOfWeek: '1',
      dayOfMonth: '1',
      time: '06:00',
      format: 'xlsx',
      recipients: '',
      isActive: true,
      description: '',
    },
  });

  const frequency = form.watch('frequency');

  const onSubmit = (data: ScheduleFormData) => {
    if (editingId) {
      setSchedules(schedules.map(s =>
        s.id === editingId
          ? { ...s, ...data, lastRun: s.lastRun, lastStatus: s.lastStatus, nextRun: 'Calculating...' }
          : s
      ));
    } else {
      const newSchedule = {
        id: Date.now().toString(),
        ...data,
        lastRun: '-',
        lastStatus: 'PENDING',
        nextRun: 'Calculating...',
      };
      setSchedules([...schedules, newSchedule]);
    }
    setShowForm(false);
    setEditingId(null);
    form.reset();
  };

  const handleEdit = (schedule: typeof schedules[0]) => {
    setEditingId(schedule.id);
    form.reset({
      reportType: schedule.reportType,
      reportName: schedule.reportName,
      frequency: schedule.frequency,
      dayOfWeek: schedule.dayOfWeek || '1',
      dayOfMonth: schedule.dayOfMonth || '1',
      time: schedule.time,
      format: schedule.format,
      recipients: schedule.recipients,
      isActive: schedule.isActive,
    });
    setShowForm(true);
  };

  const handleDelete = (id: string) => {
    setSchedules(schedules.filter(s => s.id !== id));
  };

  const handleToggle = (id: string) => {
    setSchedules(schedules.map(s =>
      s.id === id ? { ...s, isActive: !s.isActive } : s
    ));
  };

  const handleRunNow = (id: string) => {
    // Simulate running the report
    setSchedules(schedules.map(s =>
      s.id === id
        ? { ...s, lastRun: new Date().toISOString().replace('T', ' ').substring(0, 16), lastStatus: 'RUNNING' }
        : s
    ));
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'SUCCESS':
        return <Badge variant="default" className="bg-green-100 text-green-800"><CheckCircle className="h-3 w-3 mr-1" />Success</Badge>;
      case 'FAILED':
        return <Badge variant="destructive"><XCircle className="h-3 w-3 mr-1" />Failed</Badge>;
      case 'RUNNING':
        return <Badge variant="secondary"><RefreshCw className="h-3 w-3 mr-1 animate-spin" />Running</Badge>;
      case 'PENDING':
        return <Badge variant="outline"><AlertCircle className="h-3 w-3 mr-1" />Pending</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      <PageHeader
        title="Report Scheduler"
        subtitle="Schedule automated report generation and delivery"
        breadcrumbs={[
          { label: 'Reports', to: '/admin/reports' },
          { label: 'Scheduler' },
        ]}
        actions={
          <Button onClick={() => { setShowForm(true); setEditingId(null); form.reset(); }}>
            <Plus className="h-4 w-4 mr-2" />
            New Schedule
          </Button>
        }
      />

      {/* Schedule Form */}
      {showForm && (
        <Card>
          <CardHeader>
            <CardTitle>{editingId ? 'Edit Schedule' : 'Create New Schedule'}</CardTitle>
            <CardDescription>Configure automated report generation</CardDescription>
          </CardHeader>
          <CardContent>
            <Form {...form}>
              <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <FormField
                    control={form.control}
                    name="reportType"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Report Type</FormLabel>
                        <Select onValueChange={field.onChange} value={field.value}>
                          <FormControl>
                            <SelectTrigger>
                              <SelectValue placeholder="Select report type" />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            {reportTypes.map(report => (
                              <SelectItem key={report.value} value={report.value}>
                                <span className="flex items-center gap-2">
                                  {report.label}
                                  <Badge variant="outline" className="text-xs">{report.category}</Badge>
                                </span>
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="reportName"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Schedule Name</FormLabel>
                        <FormControl>
                          <Input placeholder="e.g., Daily Collection Report" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="frequency"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Frequency</FormLabel>
                        <Select onValueChange={field.onChange} value={field.value}>
                          <FormControl>
                            <SelectTrigger>
                              <SelectValue />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            <SelectItem value="DAILY">Daily</SelectItem>
                            <SelectItem value="WEEKLY">Weekly</SelectItem>
                            <SelectItem value="MONTHLY">Monthly</SelectItem>
                            <SelectItem value="QUARTERLY">Quarterly</SelectItem>
                          </SelectContent>
                        </Select>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  {frequency === 'WEEKLY' && (
                    <FormField
                      control={form.control}
                      name="dayOfWeek"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Day of Week</FormLabel>
                          <Select onValueChange={field.onChange} value={field.value}>
                            <FormControl>
                              <SelectTrigger>
                                <SelectValue />
                              </SelectTrigger>
                            </FormControl>
                            <SelectContent>
                              <SelectItem value="1">Monday</SelectItem>
                              <SelectItem value="2">Tuesday</SelectItem>
                              <SelectItem value="3">Wednesday</SelectItem>
                              <SelectItem value="4">Thursday</SelectItem>
                              <SelectItem value="5">Friday</SelectItem>
                              <SelectItem value="6">Saturday</SelectItem>
                              <SelectItem value="0">Sunday</SelectItem>
                            </SelectContent>
                          </Select>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  )}

                  {(frequency === 'MONTHLY' || frequency === 'QUARTERLY') && (
                    <FormField
                      control={form.control}
                      name="dayOfMonth"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Day of Month</FormLabel>
                          <Select onValueChange={field.onChange} value={field.value}>
                            <FormControl>
                              <SelectTrigger>
                                <SelectValue />
                              </SelectTrigger>
                            </FormControl>
                            <SelectContent>
                              {Array.from({ length: 28 }, (_, i) => (
                                <SelectItem key={i + 1} value={(i + 1).toString()}>
                                  {i + 1}
                                </SelectItem>
                              ))}
                              <SelectItem value="L">Last Day</SelectItem>
                            </SelectContent>
                          </Select>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  )}

                  <FormField
                    control={form.control}
                    name="time"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Time</FormLabel>
                        <FormControl>
                          <Input type="time" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="format"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Output Format</FormLabel>
                        <Select onValueChange={field.onChange} value={field.value}>
                          <FormControl>
                            <SelectTrigger>
                              <SelectValue />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            <SelectItem value="xlsx">Excel (.xlsx)</SelectItem>
                            <SelectItem value="pdf">PDF</SelectItem>
                            <SelectItem value="csv">CSV</SelectItem>
                          </SelectContent>
                        </Select>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="recipients"
                    render={({ field }) => (
                      <FormItem className="md:col-span-2">
                        <FormLabel>Email Recipients</FormLabel>
                        <FormControl>
                          <Input placeholder="email1@company.com, email2@company.com" {...field} />
                        </FormControl>
                        <FormDescription>Comma-separated email addresses</FormDescription>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="isActive"
                    render={({ field }) => (
                      <FormItem className="flex items-center justify-between rounded-lg border p-4">
                        <div className="space-y-0.5">
                          <FormLabel>Active</FormLabel>
                          <FormDescription>Enable this schedule</FormDescription>
                        </div>
                        <FormControl>
                          <Switch checked={field.value} onCheckedChange={field.onChange} />
                        </FormControl>
                      </FormItem>
                    )}
                  />
                </div>

                <div className="flex gap-2">
                  <Button type="submit">{editingId ? 'Update' : 'Create'} Schedule</Button>
                  <Button type="button" variant="outline" onClick={() => { setShowForm(false); setEditingId(null); }}>
                    Cancel
                  </Button>
                </div>
              </form>
            </Form>
          </CardContent>
        </Card>
      )}

      {/* Scheduled Reports List */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-5 w-5" />
            Scheduled Reports
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Report Name</TableHead>
                <TableHead>Frequency</TableHead>
                <TableHead>Time</TableHead>
                <TableHead>Format</TableHead>
                <TableHead>Last Run</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Next Run</TableHead>
                <TableHead>Active</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {schedules.map((schedule) => (
                <TableRow key={schedule.id}>
                  <TableCell>
                    <div>
                      <div className="font-medium">{schedule.reportName}</div>
                      <div className="text-xs text-muted-foreground">
                        {reportTypes.find(r => r.value === schedule.reportType)?.category}
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline">
                      {schedule.frequency}
                      {schedule.frequency === 'WEEKLY' && schedule.dayOfWeek &&
                        ` (${['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'][parseInt(schedule.dayOfWeek)]})`}
                      {schedule.frequency === 'MONTHLY' && schedule.dayOfMonth &&
                        ` (Day ${schedule.dayOfMonth})`}
                    </Badge>
                  </TableCell>
                  <TableCell>{schedule.time}</TableCell>
                  <TableCell>
                    <Badge variant="secondary">{schedule.format.toUpperCase()}</Badge>
                  </TableCell>
                  <TableCell className="text-sm">{schedule.lastRun}</TableCell>
                  <TableCell>{getStatusBadge(schedule.lastStatus)}</TableCell>
                  <TableCell className="text-sm">{schedule.nextRun}</TableCell>
                  <TableCell>
                    <Switch
                      checked={schedule.isActive}
                      onCheckedChange={() => handleToggle(schedule.id)}
                    />
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleRunNow(schedule.id)}
                        disabled={schedule.lastStatus === 'RUNNING'}
                      >
                        <Play className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="sm" onClick={() => handleEdit(schedule)}>
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="sm" onClick={() => handleDelete(schedule.id)}>
                        <Trash2 className="h-4 w-4 text-red-500" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Email Delivery Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Mail className="h-5 w-5" />
            Email Delivery Settings
          </CardTitle>
          <CardDescription>Configure email delivery options for scheduled reports</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <Label>Sender Email</Label>
              <Input value="reports@company.com" disabled />
            </div>
            <div className="space-y-2">
              <Label>Reply-To Email</Label>
              <Input value="support@company.com" disabled />
            </div>
            <div className="space-y-2">
              <Label>CC Recipients (Global)</Label>
              <Input placeholder="cc@company.com" />
            </div>
            <div className="space-y-2">
              <Label>BCC Recipients (Global)</Label>
              <Input placeholder="audit@company.com" />
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
