import { zodResolver } from '@hookform/resolvers/zod';
import {
  ArrowLeft,
  Upload,
  FileText,
  CheckCircle,
  XCircle,
  AlertCircle,
  Clock,
  Download,
  RefreshCw,
  Search,
  Eye,
} from 'lucide-react';
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { Link } from 'react-router-dom';
import { z } from 'zod';

import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
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
import { Textarea } from '@/components/ui/textarea';
import { logger } from '@/lib/logger';

const uploadSchema = z.object({
  uploadType: z.string().min(1, 'Upload type is required'),
  batchName: z.string().min(1, 'Batch name is required'),
  file: z.any(),
  remarks: z.string().optional(),
});

type UploadFormData = z.infer<typeof uploadSchema>;

// Mock upload history
const uploadHistory = [
  {
    id: '1',
    batchName: 'CKYC_BATCH_20250115_001',
    uploadType: 'NEW_REGISTRATION',
    fileName: 'ckyc_new_customers_jan.xml',
    recordCount: 125,
    successCount: 120,
    failedCount: 5,
    status: 'COMPLETED',
    uploadedAt: '2025-01-15 14:30:00',
    uploadedBy: 'KYC Team',
    ckycAckNo: 'ACK2025011500125',
  },
  {
    id: '2',
    batchName: 'CKYC_BATCH_20250114_002',
    uploadType: 'UPDATE',
    fileName: 'ckyc_updates_jan.xml',
    recordCount: 85,
    successCount: 82,
    failedCount: 3,
    status: 'COMPLETED',
    uploadedAt: '2025-01-14 10:15:00',
    uploadedBy: 'KYC Team',
    ckycAckNo: 'ACK2025011400085',
  },
  {
    id: '3',
    batchName: 'CKYC_BATCH_20250113_001',
    uploadType: 'NEW_REGISTRATION',
    fileName: 'ckyc_bulk_jan.xml',
    recordCount: 200,
    successCount: 0,
    failedCount: 0,
    status: 'PROCESSING',
    uploadedAt: '2025-01-13 16:45:00',
    uploadedBy: 'Operations',
    ckycAckNo: '-',
  },
  {
    id: '4',
    batchName: 'CKYC_BATCH_20250112_001',
    uploadType: 'NEW_REGISTRATION',
    fileName: 'ckyc_failed_batch.xml',
    recordCount: 50,
    successCount: 0,
    failedCount: 50,
    status: 'FAILED',
    uploadedAt: '2025-01-12 09:00:00',
    uploadedBy: 'KYC Team',
    ckycAckNo: '-',
    errorMessage: 'Invalid XML format',
  },
];

// Pending records for upload
const pendingRecords = [
  { id: '1', customerId: 'CUST001', name: 'Rajesh Kumar', pan: 'ABCDE1234F', status: 'PENDING', lastAttempt: '-' },
  { id: '2', customerId: 'CUST002', name: 'Priya Sharma', pan: 'FGHIJ5678K', status: 'PENDING', lastAttempt: '-' },
  { id: '3', customerId: 'CUST003', name: 'Amit Patel', pan: 'KLMNO9012L', status: 'RETRY', lastAttempt: '2025-01-14' },
  { id: '4', customerId: 'CUST004', name: 'Sunita Devi', pan: 'PQRST3456M', status: 'PENDING', lastAttempt: '-' },
  { id: '5', customerId: 'CUST005', name: 'Vikram Singh', pan: 'UVWXY7890N', status: 'RETRY', lastAttempt: '2025-01-13' },
];

export default function CKYCUpload() {
  const [selectedRecords, setSelectedRecords] = useState<string[]>([]);
  const [isUploading, setIsUploading] = useState(false);

  const form = useForm<UploadFormData>({
    resolver: zodResolver(uploadSchema),
    defaultValues: {
      uploadType: '',
      batchName: `CKYC_BATCH_${new Date().toISOString().split('T')[0].replace(/-/g, '')}_001`,
      remarks: '',
    },
  });

  const onSubmit = async (data: UploadFormData) => {
    setIsUploading(true);
    // Simulate upload
    await new Promise(resolve => setTimeout(resolve, 2000));
    setIsUploading(false);
    logger.debug('Upload data:', data);
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'COMPLETED':
        return <Badge variant="default" className="bg-green-100 text-green-800"><CheckCircle className="h-3 w-3 mr-1" />Completed</Badge>;
      case 'FAILED':
        return <Badge variant="destructive"><XCircle className="h-3 w-3 mr-1" />Failed</Badge>;
      case 'PROCESSING':
        return <Badge variant="secondary"><RefreshCw className="h-3 w-3 mr-1 animate-spin" />Processing</Badge>;
      case 'PENDING':
        return <Badge variant="outline"><Clock className="h-3 w-3 mr-1" />Pending</Badge>;
      case 'RETRY':
        return <Badge variant="secondary"><AlertCircle className="h-3 w-3 mr-1" />Retry</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const toggleRecord = (id: string) => {
    setSelectedRecords(prev =>
      prev.includes(id) ? prev.filter(r => r !== id) : [...prev, id]
    );
  };

  const toggleAll = () => {
    if (selectedRecords.length === pendingRecords.length) {
      setSelectedRecords([]);
    } else {
      setSelectedRecords(pendingRecords.map(r => r.id));
    }
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      <PageHeader
        title="CKYC Upload"
        subtitle="Upload customer KYC data to CERSAI CKYC registry"
        breadcrumbs={[
          { label: 'CKYC', to: '/admin/kyc/ckyc-status' },
          { label: 'Upload' },
        ]}
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Upload Form */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle>Upload CKYC Data</CardTitle>
            <CardDescription>Upload XML file or generate from pending records</CardDescription>
          </CardHeader>
          <CardContent>
            <Form {...form}>
              <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
                <FormField
                  control={form.control}
                  name="uploadType"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Upload Type</FormLabel>
                      <Select onValueChange={field.onChange} value={field.value}>
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder="Select type" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          <SelectItem value="NEW_REGISTRATION">New Registration</SelectItem>
                          <SelectItem value="UPDATE">Update Existing</SelectItem>
                          <SelectItem value="IMAGE_UPLOAD">Image Upload</SelectItem>
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="batchName"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Batch Name</FormLabel>
                      <FormControl>
                        <Input {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="file"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Upload XML File</FormLabel>
                      <FormControl>
                        <div className="border-2 border-dashed rounded-lg p-6 text-center cursor-pointer hover:border-primary transition-colors">
                          <Upload className="h-8 w-8 mx-auto text-muted-foreground mb-2" />
                          <p className="text-sm text-muted-foreground">
                            Drag & drop XML file or click to browse
                          </p>
                          <Input
                            type="file"
                            accept=".xml"
                            className="hidden"
                            onChange={(e) => field.onChange(e.target.files?.[0])}
                          />
                        </div>
                      </FormControl>
                      <FormDescription>
                        Max file size: 10MB. Format: CKYC XML v2.0
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="remarks"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Remarks</FormLabel>
                      <FormControl>
                        <Textarea {...field} rows={2} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <div className="flex gap-2">
                  <Button type="submit" className="flex-1" disabled={isUploading}>
                    {isUploading ? (
                      <>
                        <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                        Uploading...
                      </>
                    ) : (
                      <>
                        <Upload className="h-4 w-4 mr-2" />
                        Upload
                      </>
                    )}
                  </Button>
                </div>

                <div className="relative">
                  <div className="absolute inset-0 flex items-center">
                    <span className="w-full border-t" />
                  </div>
                  <div className="relative flex justify-center text-xs uppercase">
                    <span className="bg-background px-2 text-muted-foreground">Or</span>
                  </div>
                </div>

                <Button
                  type="button"
                  variant="outline"
                  className="w-full"
                  disabled={selectedRecords.length === 0}
                >
                  <FileText className="h-4 w-4 mr-2" />
                  Generate from Selected ({selectedRecords.length})
                </Button>
              </form>
            </Form>
          </CardContent>
        </Card>

        {/* Pending Records */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>Pending CKYC Records</span>
              <Badge variant="secondary">{pendingRecords.length} records</Badge>
            </CardTitle>
            <CardDescription>Select records to generate CKYC upload file</CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-12">
                    <input
                      type="checkbox"
                      checked={selectedRecords.length === pendingRecords.length}
                      onChange={toggleAll}
                      className="rounded border-gray-300"
                    />
                  </TableHead>
                  <TableHead>Customer ID</TableHead>
                  <TableHead>Name</TableHead>
                  <TableHead>PAN</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Last Attempt</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {pendingRecords.map((record) => (
                  <TableRow key={record.id}>
                    <TableCell>
                      <input
                        type="checkbox"
                        checked={selectedRecords.includes(record.id)}
                        onChange={() => toggleRecord(record.id)}
                        className="rounded border-gray-300"
                      />
                    </TableCell>
                    <TableCell className="font-mono text-sm">{record.customerId}</TableCell>
                    <TableCell>{record.name}</TableCell>
                    <TableCell className="font-mono">{record.pan}</TableCell>
                    <TableCell>{getStatusBadge(record.status)}</TableCell>
                    <TableCell className="text-sm text-muted-foreground">{record.lastAttempt}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>

      {/* Upload History */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-5 w-5" />
            Upload History
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Batch Name</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>File Name</TableHead>
                <TableHead className="text-right">Records</TableHead>
                <TableHead className="text-right">Success</TableHead>
                <TableHead className="text-right">Failed</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>CKYC Ack No</TableHead>
                <TableHead>Uploaded At</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {uploadHistory.map((upload) => (
                <TableRow key={upload.id}>
                  <TableCell className="font-medium">{upload.batchName}</TableCell>
                  <TableCell>
                    <Badge variant="outline">
                      {upload.uploadType === 'NEW_REGISTRATION' ? 'New' : 'Update'}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-sm">{upload.fileName}</TableCell>
                  <TableCell className="text-right">{upload.recordCount}</TableCell>
                  <TableCell className="text-right text-green-600">{upload.successCount}</TableCell>
                  <TableCell className="text-right text-red-600">{upload.failedCount}</TableCell>
                  <TableCell>{getStatusBadge(upload.status)}</TableCell>
                  <TableCell className="font-mono text-sm">{upload.ckycAckNo}</TableCell>
                  <TableCell className="text-sm">{upload.uploadedAt}</TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-1">
                      <Button variant="ghost" size="sm">
                        <Eye className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="sm">
                        <Download className="h-4 w-4" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
