import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import {
  ArrowLeft,
  Search,
  UserMinus,
  Calendar,
  FileText,
  AlertTriangle,
  User,
  Building,
  Briefcase,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { formatDate } from '@/lib/utils';

import { logger } from '@/lib/logger';
const separationSchema = z.object({
  employee_id: z.string().min(1, 'Employee is required'),
  separation_type: z.enum(['RESIGNATION', 'TERMINATION', 'RETIREMENT', 'ABSCONDING', 'DEATH']),
  notice_date: z.string().min(1, 'Notice date is required'),
  last_working_date: z.string().min(1, 'Last working date is required'),
  reason: z.string().min(10, 'Reason must be at least 10 characters'),
  remarks: z.string().optional(),
  waive_notice_period: z.boolean().default(false),
  buyout_notice_days: z.number().optional(),
});

type SeparationFormData = z.infer<typeof separationSchema>;

interface EmployeeInfo {
  id: string;
  employee_code: string;
  full_name: string;
  department: string;
  designation: string;
  date_of_joining: string;
  employment_type: string;
  notice_period_days: number;
  pending_leaves: number;
  pending_loans: number;
}

// Mock employee search result
const mockEmployee: EmployeeInfo = {
  id: 'emp-001',
  employee_code: 'EMP001',
  full_name: 'Rahul Sharma',
  department: 'Engineering',
  designation: 'Senior Developer',
  date_of_joining: '2020-03-15',
  employment_type: 'PERMANENT',
  notice_period_days: 60,
  pending_leaves: 12,
  pending_loans: 50000,
};

export default function SeparationInitiate() {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedEmployee, setSelectedEmployee] = useState<EmployeeInfo | null>(null);
  const [isSearching, setIsSearching] = useState(false);
  const [showBuyout, setShowBuyout] = useState(false);

  const form = useForm<SeparationFormData>({
    resolver: zodResolver(separationSchema) as any,
    defaultValues: {
      employee_id: '',
      separation_type: 'RESIGNATION',
      notice_date: new Date().toISOString().split('T')[0],
      last_working_date: '',
      reason: '',
      remarks: '',
      waive_notice_period: false,
      buyout_notice_days: 0,
    },
  });

  const handleSearchEmployee = () => {
    if (!searchQuery.trim()) return;
    setIsSearching(true);
    // Simulate API call
    setTimeout(() => {
      setSelectedEmployee(mockEmployee);
      form.setValue('employee_id', mockEmployee.id);
      // Calculate default last working date based on notice period
      const noticeDate = new Date();
      const lwd = new Date(noticeDate);
      lwd.setDate(lwd.getDate() + mockEmployee.notice_period_days);
      form.setValue('last_working_date', lwd.toISOString().split('T')[0]);
      setIsSearching(false);
    }, 500);
  };

  const calculateYearsOfService = (joiningDate: string) => {
    const start = new Date(joiningDate);
    const end = new Date();
    const years = (end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24 * 365);
    return years.toFixed(1);
  };

  const onSubmit = (data: SeparationFormData) => {
    logger.debug('Separation data:', data);
    // API call would go here
    navigate('/admin/hris/separation');
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => navigate('/admin/hris/separation')}>
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div>
          <h1 className="text-3xl font-bold">Initiate Employee Separation</h1>
          <p className="text-muted-foreground">
            Start the separation process for an employee
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Form */}
        <div className="lg:col-span-2 space-y-6">
          {/* Employee Search */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Search className="h-5 w-5" />
                Select Employee
              </CardTitle>
              <CardDescription>
                Search for the employee to initiate separation
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex gap-2">
                <Input
                  placeholder="Search by employee code or name..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSearchEmployee()}
                />
                <Button onClick={handleSearchEmployee} disabled={isSearching}>
                  {isSearching ? 'Searching...' : 'Search'}
                </Button>
              </div>

              {selectedEmployee && (
                <div className="mt-4 p-4 border rounded-lg bg-muted/50">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-4">
                      <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center">
                        <User className="h-6 w-6 text-primary" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-lg">{selectedEmployee.full_name}</h3>
                        <p className="text-sm text-muted-foreground">
                          {selectedEmployee.employee_code}
                        </p>
                      </div>
                    </div>
                    <Badge variant="outline">{selectedEmployee.employment_type}</Badge>
                  </div>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4 pt-4 border-t">
                    <div className="flex items-center gap-2">
                      <Building className="h-4 w-4 text-muted-foreground" />
                      <div>
                        <p className="text-xs text-muted-foreground">Department</p>
                        <p className="text-sm font-medium">{selectedEmployee.department}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Briefcase className="h-4 w-4 text-muted-foreground" />
                      <div>
                        <p className="text-xs text-muted-foreground">Designation</p>
                        <p className="text-sm font-medium">{selectedEmployee.designation}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Calendar className="h-4 w-4 text-muted-foreground" />
                      <div>
                        <p className="text-xs text-muted-foreground">Date of Joining</p>
                        <p className="text-sm font-medium">{formatDate(selectedEmployee.date_of_joining)}</p>
                      </div>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Years of Service</p>
                      <p className="text-sm font-medium">
                        {calculateYearsOfService(selectedEmployee.date_of_joining)} years
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Separation Details Form */}
          {selectedEmployee && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <UserMinus className="h-5 w-5" />
                  Separation Details
                </CardTitle>
              </CardHeader>
              <CardContent>
                <Form {...form}>
                  <form onSubmit={form.handleSubmit(onSubmit as any)} className="space-y-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <FormField
                        control={form.control}
                        name="separation_type"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Separation Type</FormLabel>
                            <Select
                              onValueChange={field.onChange}
                              defaultValue={field.value}
                            >
                              <FormControl>
                                <SelectTrigger>
                                  <SelectValue placeholder="Select type" />
                                </SelectTrigger>
                              </FormControl>
                              <SelectContent>
                                <SelectItem value="RESIGNATION">Resignation</SelectItem>
                                <SelectItem value="TERMINATION">Termination</SelectItem>
                                <SelectItem value="RETIREMENT">Retirement</SelectItem>
                                <SelectItem value="ABSCONDING">Absconding</SelectItem>
                                <SelectItem value="DEATH">Death</SelectItem>
                              </SelectContent>
                            </Select>
                            <FormMessage />
                          </FormItem>
                        )}
                      />

                      <FormField
                        control={form.control}
                        name="notice_date"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Notice Date</FormLabel>
                            <FormControl>
                              <Input type="date" {...field} />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />

                      <FormField
                        control={form.control}
                        name="last_working_date"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Last Working Date</FormLabel>
                            <FormControl>
                              <Input type="date" {...field} />
                            </FormControl>
                            <FormDescription>
                              Notice period: {selectedEmployee.notice_period_days} days
                            </FormDescription>
                            <FormMessage />
                          </FormItem>
                        )}
                      />

                      <div className="space-y-2">
                        <Label>Notice Period Options</Label>
                        <div className="flex items-center space-x-2">
                          <input
                            type="checkbox"
                            id="waive_notice"
                            className="rounded"
                            onChange={(e) => {
                              form.setValue('waive_notice_period', e.target.checked);
                              setShowBuyout(e.target.checked);
                            }}
                          />
                          <label htmlFor="waive_notice" className="text-sm">
                            Waive/Buyout notice period
                          </label>
                        </div>
                        {showBuyout && (
                          <FormField
                            control={form.control}
                            name="buyout_notice_days"
                            render={({ field }) => (
                              <FormItem>
                                <FormControl>
                                  <Input
                                    type="number"
                                    placeholder="Days to buyout"
                                    {...field}
                                    onChange={(e) => field.onChange(parseInt(e.target.value))}
                                  />
                                </FormControl>
                                <FormDescription>
                                  Days of notice period to be bought out
                                </FormDescription>
                              </FormItem>
                            )}
                          />
                        )}
                      </div>
                    </div>

                    <FormField
                      control={form.control}
                      name="reason"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Reason for Separation</FormLabel>
                          <FormControl>
                            <Textarea
                              placeholder="Enter the reason for separation..."
                              className="min-h-[100px]"
                              {...field}
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="remarks"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Additional Remarks (Optional)</FormLabel>
                          <FormControl>
                            <Textarea
                              placeholder="Any additional remarks or notes..."
                              {...field}
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <div className="flex justify-end gap-2">
                      <Button
                        type="button"
                        variant="outline"
                        onClick={() => navigate('/admin/hris/separation')}
                      >
                        Cancel
                      </Button>
                      <Button type="submit">
                        <UserMinus className="h-4 w-4 mr-2" />
                        Initiate Separation
                      </Button>
                    </div>
                  </form>
                </Form>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Sidebar - Employee Summary & Warnings */}
        <div className="space-y-6">
          {selectedEmployee && (
            <>
              {/* Pending Items Alert */}
              {(selectedEmployee.pending_leaves > 0 || selectedEmployee.pending_loans > 0) && (
                <Alert variant="destructive">
                  <AlertTriangle className="h-4 w-4" />
                  <AlertTitle>Pending Items</AlertTitle>
                  <AlertDescription>
                    <ul className="list-disc list-inside mt-2 space-y-1">
                      {selectedEmployee.pending_leaves > 0 && (
                        <li>{selectedEmployee.pending_leaves} pending leave days</li>
                      )}
                      {selectedEmployee.pending_loans > 0 && (
                        <li>Loan balance: ₹{selectedEmployee.pending_loans.toLocaleString()}</li>
                      )}
                    </ul>
                  </AlertDescription>
                </Alert>
              )}

              {/* Clearance Checklist Preview */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-base">
                    <FileText className="h-4 w-4" />
                    Clearance Checklist
                  </CardTitle>
                  <CardDescription>
                    Required clearances will be initiated
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2 text-sm">
                    <li className="flex items-center gap-2">
                      <div className="h-2 w-2 rounded-full bg-blue-500" />
                      IT Department - Asset return
                    </li>
                    <li className="flex items-center gap-2">
                      <div className="h-2 w-2 rounded-full bg-blue-500" />
                      Admin - ID card, access card
                    </li>
                    <li className="flex items-center gap-2">
                      <div className="h-2 w-2 rounded-full bg-blue-500" />
                      Finance - Loan settlement
                    </li>
                    <li className="flex items-center gap-2">
                      <div className="h-2 w-2 rounded-full bg-blue-500" />
                      HR - Policy documents
                    </li>
                    <li className="flex items-center gap-2">
                      <div className="h-2 w-2 rounded-full bg-blue-500" />
                      Reporting Manager - Knowledge transfer
                    </li>
                  </ul>
                </CardContent>
              </Card>

              {/* F&F Components Preview */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">F&F Settlement Components</CardTitle>
                  <CardDescription>
                    Will be calculated on clearance completion
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2 text-sm">
                    <li className="flex justify-between">
                      <span className="text-muted-foreground">Basic + DA (pro-rata)</span>
                      <span>Calculated</span>
                    </li>
                    <li className="flex justify-between">
                      <span className="text-muted-foreground">Leave encashment</span>
                      <span>{selectedEmployee.pending_leaves} days</span>
                    </li>
                    <li className="flex justify-between">
                      <span className="text-muted-foreground">Gratuity</span>
                      <span>
                        {parseFloat(calculateYearsOfService(selectedEmployee.date_of_joining)) >= 5
                          ? 'Eligible'
                          : 'Not eligible'}
                      </span>
                    </li>
                    <li className="flex justify-between">
                      <span className="text-muted-foreground">Bonus (pro-rata)</span>
                      <span>Calculated</span>
                    </li>
                    <li className="flex justify-between text-red-600">
                      <span>Loan recovery</span>
                      <span>-₹{selectedEmployee.pending_loans.toLocaleString()}</span>
                    </li>
                  </ul>
                </CardContent>
              </Card>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
