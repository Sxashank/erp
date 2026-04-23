import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { PageHeader } from '@/components/common/PageHeader';
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
import { Calendar, Clock, Save, Send, ChevronLeft, ChevronRight } from 'lucide-react';

// Mock data
const projects = [
  { id: '1', name: 'Project Alpha', code: 'ALPHA' },
  { id: '2', name: 'Project Beta', code: 'BETA' },
  { id: '3', name: 'Internal - Admin', code: 'ADMIN' },
  { id: '4', name: 'Internal - Training', code: 'TRAIN' },
  { id: '5', name: 'Leave', code: 'LEAVE' },
];

const tasks = [
  { id: '1', name: 'Development', projectId: '1' },
  { id: '2', name: 'Testing', projectId: '1' },
  { id: '3', name: 'Documentation', projectId: '1' },
  { id: '4', name: 'Code Review', projectId: '2' },
  { id: '5', name: 'Meetings', projectId: '3' },
  { id: '6', name: 'Training Session', projectId: '4' },
];

interface TimesheetEntry {
  id: string;
  projectId: string;
  taskId: string;
  hours: { [key: string]: number };
}

export default function ESSTimesheet() {
  const [currentWeekStart, setCurrentWeekStart] = useState(new Date('2025-01-13'));
  const [entries, setEntries] = useState<TimesheetEntry[]>([
    {
      id: '1',
      projectId: '1',
      taskId: '1',
      hours: { '2025-01-13': 8, '2025-01-14': 7, '2025-01-15': 8, '2025-01-16': 6, '2025-01-17': 8 },
    },
    {
      id: '2',
      projectId: '1',
      taskId: '2',
      hours: { '2025-01-14': 1, '2025-01-16': 2 },
    },
    {
      id: '3',
      projectId: '3',
      taskId: '5',
      hours: { '2025-01-13': 1, '2025-01-15': 1 },
    },
  ]);
  const [status, setStatus] = useState<'DRAFT' | 'SUBMITTED' | 'APPROVED'>('DRAFT');

  const getWeekDays = () => {
    const days = [];
    for (let i = 0; i < 7; i++) {
      const date = new Date(currentWeekStart);
      date.setDate(date.getDate() + i);
      days.push(date);
    }
    return days;
  };

  const weekDays = getWeekDays();

  const formatDate = (date: Date) => {
    return date.toISOString().split('T')[0];
  };

  const formatDayHeader = (date: Date) => {
    const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    return {
      day: dayNames[date.getDay()],
      date: date.getDate(),
    };
  };

  const navigateWeek = (direction: 'prev' | 'next') => {
    const newDate = new Date(currentWeekStart);
    newDate.setDate(newDate.getDate() + (direction === 'next' ? 7 : -7));
    setCurrentWeekStart(newDate);
  };

  const updateHours = (entryId: string, dateStr: string, hours: number) => {
    setEntries(entries.map((entry) => {
      if (entry.id === entryId) {
        return {
          ...entry,
          hours: { ...entry.hours, [dateStr]: hours },
        };
      }
      return entry;
    }));
  };

  const addNewRow = () => {
    const newEntry: TimesheetEntry = {
      id: `new-${Date.now()}`,
      projectId: '',
      taskId: '',
      hours: {},
    };
    setEntries([...entries, newEntry]);
  };

  const removeRow = (id: string) => {
    setEntries(entries.filter((e) => e.id !== id));
  };

  const calculateDayTotal = (dateStr: string) => {
    return entries.reduce((sum, entry) => sum + (entry.hours[dateStr] || 0), 0);
  };

  const calculateRowTotal = (entry: TimesheetEntry) => {
    return Object.values(entry.hours).reduce((sum, h) => sum + h, 0);
  };

  const calculateGrandTotal = () => {
    return entries.reduce((sum, entry) => sum + calculateRowTotal(entry), 0);
  };

  const getStatusBadge = () => {
    switch (status) {
      case 'DRAFT':
        return <Badge variant="outline">Draft</Badge>;
      case 'SUBMITTED':
        return <Badge variant="secondary" className="bg-yellow-100 text-yellow-800">Submitted</Badge>;
      case 'APPROVED':
        return <Badge variant="default" className="bg-green-500">Approved</Badge>;
    }
  };

  const isWeekend = (date: Date) => {
    const day = date.getDay();
    return day === 0 || day === 6;
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Timesheet"
        subtitle="Log your working hours"
        actions={getStatusBadge()}
      />

      {/* Week Navigation */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            <Button variant="outline" size="icon" onClick={() => navigateWeek('prev')}>
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <div className="flex items-center gap-2">
              <Calendar className="h-5 w-5 text-muted-foreground" />
              <span className="font-medium">
                {weekDays[0].toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })} -{' '}
                {weekDays[6].toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}
              </span>
            </div>
            <Button variant="outline" size="icon" onClick={() => navigateWeek('next')}>
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Timesheet Grid */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Time Entries</CardTitle>
          <Button variant="outline" size="sm" onClick={addNewRow} disabled={status !== 'DRAFT'}>
            Add Row
          </Button>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-40">Project</TableHead>
                  <TableHead className="w-40">Task</TableHead>
                  {weekDays.map((date) => {
                    const { day, date: dateNum } = formatDayHeader(date);
                    const weekend = isWeekend(date);
                    return (
                      <TableHead
                        key={formatDate(date)}
                        className={`text-center w-20 ${weekend ? 'bg-muted/50' : ''}`}
                      >
                        <div className="text-xs text-muted-foreground">{day}</div>
                        <div>{dateNum}</div>
                      </TableHead>
                    );
                  })}
                  <TableHead className="text-center w-20">Total</TableHead>
                  <TableHead className="w-12"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {entries.map((entry) => (
                  <TableRow key={entry.id}>
                    <TableCell>
                      <Select
                        value={entry.projectId}
                        onValueChange={(value) => {
                          setEntries(entries.map((e) =>
                            e.id === entry.id ? { ...e, projectId: value, taskId: '' } : e
                          ));
                        }}
                        disabled={status !== 'DRAFT'}
                      >
                        <SelectTrigger className="w-40">
                          <SelectValue placeholder="Project" />
                        </SelectTrigger>
                        <SelectContent>
                          {projects.map((p) => (
                            <SelectItem key={p.id} value={p.id}>
                              {p.name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </TableCell>
                    <TableCell>
                      <Select
                        value={entry.taskId}
                        onValueChange={(value) => {
                          setEntries(entries.map((e) =>
                            e.id === entry.id ? { ...e, taskId: value } : e
                          ));
                        }}
                        disabled={status !== 'DRAFT' || !entry.projectId}
                      >
                        <SelectTrigger className="w-40">
                          <SelectValue placeholder="Task" />
                        </SelectTrigger>
                        <SelectContent>
                          {tasks
                            .filter((t) => t.projectId === entry.projectId)
                            .map((t) => (
                              <SelectItem key={t.id} value={t.id}>
                                {t.name}
                              </SelectItem>
                            ))}
                        </SelectContent>
                      </Select>
                    </TableCell>
                    {weekDays.map((date) => {
                      const dateStr = formatDate(date);
                      const weekend = isWeekend(date);
                      return (
                        <TableCell key={dateStr} className={`text-center ${weekend ? 'bg-muted/50' : ''}`}>
                          <Input
                            type="number"
                            min="0"
                            max="24"
                            step="0.5"
                            className="w-16 text-center mx-auto"
                            value={entry.hours[dateStr] || ''}
                            onChange={(e) => updateHours(entry.id, dateStr, parseFloat(e.target.value) || 0)}
                            disabled={status !== 'DRAFT'}
                          />
                        </TableCell>
                      );
                    })}
                    <TableCell className="text-center font-medium">
                      {calculateRowTotal(entry)}
                    </TableCell>
                    <TableCell>
                      {status === 'DRAFT' && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => removeRow(entry.id)}
                          className="text-destructive"
                        >
                          x
                        </Button>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
                {/* Totals Row */}
                <TableRow className="bg-muted/50 font-medium">
                  <TableCell colSpan={2}>Daily Total</TableCell>
                  {weekDays.map((date) => {
                    const dateStr = formatDate(date);
                    const dayTotal = calculateDayTotal(dateStr);
                    return (
                      <TableCell
                        key={dateStr}
                        className={`text-center ${dayTotal > 8 ? 'text-orange-600' : ''}`}
                      >
                        {dayTotal || '-'}
                      </TableCell>
                    );
                  })}
                  <TableCell className="text-center font-bold">
                    {calculateGrandTotal()}
                  </TableCell>
                  <TableCell></TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      {/* Summary & Actions */}
      <div className="flex justify-between items-center">
        <Card className="w-64">
          <CardContent className="pt-6">
            <div className="text-center">
              <div className="text-3xl font-bold text-primary">{calculateGrandTotal()}</div>
              <div className="text-sm text-muted-foreground">Total Hours This Week</div>
            </div>
          </CardContent>
        </Card>

        <div className="flex gap-4">
          {status === 'DRAFT' && (
            <>
              <Button variant="outline">
                <Save className="h-4 w-4 mr-2" />
                Save Draft
              </Button>
              <Button onClick={() => setStatus('SUBMITTED')}>
                <Send className="h-4 w-4 mr-2" />
                Submit for Approval
              </Button>
            </>
          )}
          {status === 'SUBMITTED' && (
            <Button variant="outline" onClick={() => setStatus('DRAFT')}>
              Recall
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
