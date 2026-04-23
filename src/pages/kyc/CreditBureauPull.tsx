import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Link, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { PageHeader } from '@/components/common/PageHeader';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
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
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  CreditCard,
  Search,
  RefreshCw,
  CheckCircle,
  XCircle,
  Clock,
  Eye,
  Download,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Building,
} from 'lucide-react';

const pullSchema = z.object({
  searchType: z.enum(['PAN', 'MOBILE', 'CUSTOMER_ID']),
  searchValue: z.string().min(1, 'Search value is required'),
  bureauType: z.string().min(1, 'Bureau type is required'),
  purpose: z.string().min(1, 'Purpose is required'),
  consent: z.boolean().refine(val => val === true, 'Customer consent is required'),
});

type PullFormData = z.infer<typeof pullSchema>;

// Mock recent pulls
const recentPulls = [
  {
    id: '1',
    customerId: 'CUST001',
    customerName: 'Rajesh Kumar',
    pan: 'ABCDE1234F',
    bureau: 'CIBIL',
    pullDate: '2025-01-15 14:30:00',
    score: 782,
    status: 'SUCCESS',
    reportId: 'RPT2025011500001',
  },
  {
    id: '2',
    customerId: 'CUST002',
    customerName: 'Priya Sharma',
    pan: 'FGHIJ5678K',
    bureau: 'EXPERIAN',
    pullDate: '2025-01-15 10:15:00',
    score: 695,
    status: 'SUCCESS',
    reportId: 'RPT2025011500002',
  },
  {
    id: '3',
    customerId: 'CUST003',
    customerName: 'Amit Patel',
    pan: 'KLMNO9012L',
    bureau: 'CIBIL',
    pullDate: '2025-01-14 16:45:00',
    score: null,
    status: 'NO_HIT',
    reportId: null,
  },
  {
    id: '4',
    customerId: 'CUST004',
    customerName: 'Sunita Devi',
    pan: 'PQRST3456M',
    bureau: 'EQUIFAX',
    pullDate: '2025-01-14 11:30:00',
    score: 720,
    status: 'SUCCESS',
    reportId: 'RPT2025011400003',
  },
  {
    id: '5',
    customerId: 'CUST005',
    customerName: 'Vikram Singh',
    pan: 'UVWXY7890N',
    bureau: 'CIBIL',
    pullDate: '2025-01-13 09:00:00',
    score: null,
    status: 'FAILED',
    reportId: null,
    error: 'Bureau service unavailable',
  },
];

// Mock bulk upload history
const bulkUploads = [
  {
    id: '1',
    batchName: 'BATCH_20250115_001',
    bureau: 'CIBIL',
    totalRecords: 50,
    success: 45,
    noHit: 3,
    failed: 2,
    status: 'COMPLETED',
    uploadedAt: '2025-01-15 08:00:00',
  },
  {
    id: '2',
    batchName: 'BATCH_20250114_001',
    bureau: 'EXPERIAN',
    totalRecords: 30,
    success: 28,
    noHit: 2,
    failed: 0,
    status: 'COMPLETED',
    uploadedAt: '2025-01-14 09:30:00',
  },
  {
    id: '3',
    batchName: 'BATCH_20250113_001',
    bureau: 'CIBIL',
    totalRecords: 75,
    success: 0,
    noHit: 0,
    failed: 0,
    status: 'PROCESSING',
    uploadedAt: '2025-01-13 14:00:00',
  },
];

export default function CreditBureauPull() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('single');
  const [isPulling, setIsPulling] = useState(false);
  const [pullResult, setPullResult] = useState<any>(null);

  const form = useForm<PullFormData>({
    resolver: zodResolver(pullSchema),
    defaultValues: {
      searchType: 'PAN',
      searchValue: '',
      bureauType: 'CIBIL',
      purpose: '',
      consent: false,
    },
  });

  const onSubmit = async (data: PullFormData) => {
    setIsPulling(true);
    setPullResult(null);

    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 3000));

    // Mock result
    setPullResult({
      status: 'SUCCESS',
      customerId: 'CUST001',
      customerName: 'Rajesh Kumar',
      bureau: data.bureauType,
      score: 782,
      scoreRange: '300-900',
      reportId: 'RPT' + Date.now(),
      pullDate: new Date().toISOString(),
      accounts: 5,
      activeAccounts: 3,
      overdueAccounts: 0,
      enquiries30Days: 2,
    });

    setIsPulling(false);
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'SUCCESS':
        return <Badge variant="default" className="bg-green-100 text-green-800"><CheckCircle className="h-3 w-3 mr-1" />Success</Badge>;
      case 'FAILED':
        return <Badge variant="destructive"><XCircle className="h-3 w-3 mr-1" />Failed</Badge>;
      case 'NO_HIT':
        return <Badge variant="secondary"><AlertTriangle className="h-3 w-3 mr-1" />No Hit</Badge>;
      case 'PROCESSING':
        return <Badge variant="outline"><RefreshCw className="h-3 w-3 mr-1 animate-spin" />Processing</Badge>;
      case 'COMPLETED':
        return <Badge variant="default" className="bg-green-100 text-green-800"><CheckCircle className="h-3 w-3 mr-1" />Completed</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const getScoreColor = (score: number | null) => {
    if (!score) return 'text-gray-500';
    if (score >= 750) return 'text-green-600';
    if (score >= 650) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      <PageHeader
        title="Credit Bureau Pull"
        subtitle="Fetch credit reports from CIBIL, Experian, Equifax"
        actions={
          <Link to="/admin/kyc/credit-bureau/history">
            <Button variant="outline">
              <Clock className="h-4 w-4 mr-2" />
              View History
            </Button>
          </Link>
        }
      />

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="single">Single Pull</TabsTrigger>
          <TabsTrigger value="bulk">Bulk Pull</TabsTrigger>
          <TabsTrigger value="recent">Recent Pulls</TabsTrigger>
        </TabsList>

        <TabsContent value="single" className="mt-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Pull Form */}
            <Card>
              <CardHeader>
                <CardTitle>Credit Bureau Enquiry</CardTitle>
                <CardDescription>Enter customer details to pull credit report</CardDescription>
              </CardHeader>
              <CardContent>
                <Form {...form}>
                  <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
                    <FormField
                      control={form.control}
                      name="searchType"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Search By</FormLabel>
                          <Select onValueChange={field.onChange} value={field.value}>
                            <FormControl>
                              <SelectTrigger>
                                <SelectValue />
                              </SelectTrigger>
                            </FormControl>
                            <SelectContent>
                              <SelectItem value="PAN">PAN Number</SelectItem>
                              <SelectItem value="MOBILE">Mobile Number</SelectItem>
                              <SelectItem value="CUSTOMER_ID">Customer ID</SelectItem>
                            </SelectContent>
                          </Select>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="searchValue"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>
                            {form.watch('searchType') === 'PAN' ? 'PAN Number' :
                             form.watch('searchType') === 'MOBILE' ? 'Mobile Number' : 'Customer ID'}
                          </FormLabel>
                          <FormControl>
                            <Input
                              placeholder={
                                form.watch('searchType') === 'PAN' ? 'ABCDE1234F' :
                                form.watch('searchType') === 'MOBILE' ? '9876543210' : 'CUST001'
                              }
                              {...field}
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="bureauType"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Credit Bureau</FormLabel>
                          <Select onValueChange={field.onChange} value={field.value}>
                            <FormControl>
                              <SelectTrigger>
                                <SelectValue />
                              </SelectTrigger>
                            </FormControl>
                            <SelectContent>
                              <SelectItem value="CIBIL">CIBIL (TransUnion)</SelectItem>
                              <SelectItem value="EXPERIAN">Experian</SelectItem>
                              <SelectItem value="EQUIFAX">Equifax</SelectItem>
                              <SelectItem value="CRIF">CRIF High Mark</SelectItem>
                            </SelectContent>
                          </Select>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="purpose"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Purpose</FormLabel>
                          <Select onValueChange={field.onChange} value={field.value}>
                            <FormControl>
                              <SelectTrigger>
                                <SelectValue placeholder="Select purpose" />
                              </SelectTrigger>
                            </FormControl>
                            <SelectContent>
                              <SelectItem value="NEW_LOAN">New Loan Application</SelectItem>
                              <SelectItem value="TOP_UP">Top-up / Enhancement</SelectItem>
                              <SelectItem value="REVIEW">Periodic Review</SelectItem>
                              <SelectItem value="COLLECTION">Collection</SelectItem>
                            </SelectContent>
                          </Select>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="consent"
                      render={({ field }) => (
                        <FormItem className="flex items-start space-x-3 space-y-0 rounded-md border p-4">
                          <FormControl>
                            <input
                              type="checkbox"
                              checked={field.value}
                              onChange={field.onChange}
                              className="mt-1"
                            />
                          </FormControl>
                          <div className="space-y-1 leading-none">
                            <FormLabel>Customer Consent</FormLabel>
                            <FormDescription>
                              I confirm that customer consent has been obtained for this credit bureau enquiry
                            </FormDescription>
                          </div>
                        </FormItem>
                      )}
                    />

                    <Button type="submit" className="w-full" disabled={isPulling}>
                      {isPulling ? (
                        <>
                          <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                          Fetching Report...
                        </>
                      ) : (
                        <>
                          <Search className="h-4 w-4 mr-2" />
                          Pull Credit Report
                        </>
                      )}
                    </Button>
                  </form>
                </Form>
              </CardContent>
            </Card>

            {/* Pull Result */}
            <Card>
              <CardHeader>
                <CardTitle>Pull Result</CardTitle>
              </CardHeader>
              <CardContent>
                {pullResult ? (
                  <div className="space-y-6">
                    <div className="text-center py-4">
                      <div className={`text-5xl font-bold ${getScoreColor(pullResult.score)}`}>
                        {pullResult.score}
                      </div>
                      <p className="text-sm text-muted-foreground mt-1">
                        Credit Score ({pullResult.scoreRange})
                      </p>
                      <Badge className="mt-2" variant="outline">{pullResult.bureau}</Badge>
                    </div>

                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div className="p-3 bg-muted rounded-lg">
                        <p className="text-muted-foreground">Customer</p>
                        <p className="font-medium">{pullResult.customerName}</p>
                      </div>
                      <div className="p-3 bg-muted rounded-lg">
                        <p className="text-muted-foreground">Report ID</p>
                        <p className="font-mono text-xs">{pullResult.reportId}</p>
                      </div>
                      <div className="p-3 bg-muted rounded-lg">
                        <p className="text-muted-foreground">Total Accounts</p>
                        <p className="font-medium">{pullResult.accounts}</p>
                      </div>
                      <div className="p-3 bg-muted rounded-lg">
                        <p className="text-muted-foreground">Active Accounts</p>
                        <p className="font-medium">{pullResult.activeAccounts}</p>
                      </div>
                      <div className="p-3 bg-muted rounded-lg">
                        <p className="text-muted-foreground">Overdue Accounts</p>
                        <p className={`font-medium ${pullResult.overdueAccounts > 0 ? 'text-red-600' : 'text-green-600'}`}>
                          {pullResult.overdueAccounts}
                        </p>
                      </div>
                      <div className="p-3 bg-muted rounded-lg">
                        <p className="text-muted-foreground">Enquiries (30 days)</p>
                        <p className="font-medium">{pullResult.enquiries30Days}</p>
                      </div>
                    </div>

                    <div className="flex gap-2">
                      <Link to={`/admin/kyc/credit-bureau/report/${pullResult.reportId}`} className="flex-1">
                        <Button variant="outline" className="w-full">
                          <Eye className="h-4 w-4 mr-2" />
                          View Full Report
                        </Button>
                      </Link>
                      <Button variant="outline">
                        <Download className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-12 text-muted-foreground">
                    <CreditCard className="h-16 w-16 mx-auto mb-4 opacity-50" />
                    <p>Enter customer details and click "Pull Credit Report"</p>
                    <p className="text-sm mt-2">Results will appear here</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="bulk" className="mt-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Bulk Credit Pull</CardTitle>
                <CardDescription>Upload CSV file for bulk credit bureau enquiry</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="border-2 border-dashed rounded-lg p-8 text-center">
                  <Building className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                  <p className="text-lg font-medium">Upload CSV File</p>
                  <p className="text-sm text-muted-foreground mt-1">
                    Format: Customer ID, Name, PAN, Mobile
                  </p>
                  <Button variant="outline" className="mt-4">
                    Select File
                  </Button>
                </div>

                <div className="flex gap-2">
                  <Select defaultValue="CIBIL">
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="CIBIL">CIBIL</SelectItem>
                      <SelectItem value="EXPERIAN">Experian</SelectItem>
                      <SelectItem value="EQUIFAX">Equifax</SelectItem>
                    </SelectContent>
                  </Select>
                  <Button className="flex-1">
                    Start Bulk Pull
                  </Button>
                </div>

                <Button variant="link" className="w-full">
                  Download Sample Template
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Bulk Upload History</CardTitle>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Batch</TableHead>
                      <TableHead>Bureau</TableHead>
                      <TableHead className="text-right">Records</TableHead>
                      <TableHead>Status</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {bulkUploads.map((upload) => (
                      <TableRow key={upload.id}>
                        <TableCell>
                          <div>
                            <div className="font-mono text-xs">{upload.batchName}</div>
                            <div className="text-xs text-muted-foreground">{upload.uploadedAt}</div>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline">{upload.bureau}</Badge>
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="text-sm">
                            <span className="text-green-600">{upload.success}</span>/
                            <span className="text-yellow-600">{upload.noHit}</span>/
                            <span className="text-red-600">{upload.failed}</span>
                          </div>
                          <div className="text-xs text-muted-foreground">
                            of {upload.totalRecords}
                          </div>
                        </TableCell>
                        <TableCell>{getStatusBadge(upload.status)}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="recent" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Recent Credit Pulls</CardTitle>
              <CardDescription>Last 50 credit bureau enquiries</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Customer</TableHead>
                    <TableHead>PAN</TableHead>
                    <TableHead>Bureau</TableHead>
                    <TableHead>Pull Date</TableHead>
                    <TableHead className="text-right">Score</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {recentPulls.map((pull) => (
                    <TableRow key={pull.id}>
                      <TableCell>
                        <div>
                          <div className="font-medium">{pull.customerName}</div>
                          <div className="text-xs text-muted-foreground">{pull.customerId}</div>
                        </div>
                      </TableCell>
                      <TableCell className="font-mono">{pull.pan}</TableCell>
                      <TableCell>
                        <Badge variant="outline">{pull.bureau}</Badge>
                      </TableCell>
                      <TableCell className="text-sm">{pull.pullDate}</TableCell>
                      <TableCell className={`text-right font-bold ${getScoreColor(pull.score)}`}>
                        {pull.score || '-'}
                      </TableCell>
                      <TableCell>{getStatusBadge(pull.status)}</TableCell>
                      <TableCell className="text-right">
                        {pull.reportId && (
                          <div className="flex items-center justify-end gap-1">
                            <Link to={`/admin/kyc/credit-bureau/report/${pull.reportId}`}>
                              <Button variant="ghost" size="sm">
                                <Eye className="h-4 w-4" />
                              </Button>
                            </Link>
                            <Button variant="ghost" size="sm">
                              <Download className="h-4 w-4" />
                            </Button>
                          </div>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
