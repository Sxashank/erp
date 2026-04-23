import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Link, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { PageHeader } from '@/components/common/PageHeader';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
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
  ArrowLeft,
  Upload,
  X,
  FileText,
  Image,
  File,
  CheckCircle,
  AlertCircle,
} from 'lucide-react';

const uploadSchema = z.object({
  customerId: z.string().min(1, 'Customer is required'),
  documentType: z.string().min(1, 'Document type is required'),
  documentNumber: z.string().min(1, 'Document number is required'),
  issueDate: z.string().optional(),
  expiryDate: z.string().optional(),
  issuingAuthority: z.string().optional(),
  remarks: z.string().optional(),
});

type UploadFormData = z.infer<typeof uploadSchema>;

// Mock customers
const customers = [
  { id: 'CUST001', name: 'Rajesh Kumar', pan: 'ABCDE1234F' },
  { id: 'CUST002', name: 'Priya Sharma', pan: 'FGHIJ5678K' },
  { id: 'CUST003', name: 'Amit Patel', pan: 'KLMNO9012L' },
  { id: 'CUST004', name: 'Sunita Devi', pan: 'PQRST3456M' },
  { id: 'CUST005', name: 'Vikram Singh', pan: 'UVWXY7890N' },
];

// Document types
const documentTypes = [
  { value: 'PAN_CARD', label: 'PAN Card', requiresExpiry: false },
  { value: 'AADHAAR', label: 'Aadhaar', requiresExpiry: false },
  { value: 'PASSPORT', label: 'Passport', requiresExpiry: true },
  { value: 'VOTER_ID', label: 'Voter ID', requiresExpiry: false },
  { value: 'DRIVING_LICENSE', label: 'Driving License', requiresExpiry: true },
  { value: 'ADDRESS_PROOF', label: 'Address Proof', requiresExpiry: false },
  { value: 'BANK_STATEMENT', label: 'Bank Statement', requiresExpiry: false },
  { value: 'ITR', label: 'Income Tax Return', requiresExpiry: false },
  { value: 'SALARY_SLIP', label: 'Salary Slip', requiresExpiry: false },
  { value: 'PHOTO', label: 'Photograph', requiresExpiry: false },
  { value: 'SIGNATURE', label: 'Signature', requiresExpiry: false },
];

interface UploadedFile {
  id: string;
  file: File;
  preview?: string;
  status: 'uploading' | 'success' | 'error';
  error?: string;
}

export default function KYCDocumentUpload() {
  const navigate = useNavigate();
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const form = useForm<UploadFormData>({
    resolver: zodResolver(uploadSchema),
    defaultValues: {
      customerId: '',
      documentType: '',
      documentNumber: '',
      issueDate: '',
      expiryDate: '',
      issuingAuthority: '',
      remarks: '',
    },
  });

  const documentType = form.watch('documentType');
  const selectedDocType = documentTypes.find(d => d.value === documentType);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = e.target.files;
    if (!selectedFiles) return;

    const newFiles: UploadedFile[] = Array.from(selectedFiles).map(file => ({
      id: Math.random().toString(36).substr(2, 9),
      file,
      preview: file.type.startsWith('image/') ? URL.createObjectURL(file) : undefined,
      status: 'success',
    }));

    setFiles(prev => [...prev, ...newFiles]);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const droppedFiles = e.dataTransfer.files;
    if (!droppedFiles) return;

    const newFiles: UploadedFile[] = Array.from(droppedFiles).map(file => ({
      id: Math.random().toString(36).substr(2, 9),
      file,
      preview: file.type.startsWith('image/') ? URL.createObjectURL(file) : undefined,
      status: 'success',
    }));

    setFiles(prev => [...prev, ...newFiles]);
  };

  const removeFile = (id: string) => {
    setFiles(prev => {
      const file = prev.find(f => f.id === id);
      if (file?.preview) {
        URL.revokeObjectURL(file.preview);
      }
      return prev.filter(f => f.id !== id);
    });
  };

  const onSubmit = async (data: UploadFormData) => {
    if (files.length === 0) {
      return;
    }

    setIsSubmitting(true);
    // Simulate upload
    await new Promise(resolve => setTimeout(resolve, 2000));
    setIsSubmitting(false);
    navigate('/admin/kyc/documents');
  };

  const getFileIcon = (file: File) => {
    if (file.type.startsWith('image/')) {
      return <Image className="h-8 w-8 text-blue-500" />;
    }
    if (file.type === 'application/pdf') {
      return <FileText className="h-8 w-8 text-red-500" />;
    }
    return <File className="h-8 w-8 text-gray-500" />;
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      <PageHeader
        title="Upload KYC Document"
        subtitle="Upload and attach KYC documents to customer profile"
        breadcrumbs={[
          { label: 'KYC Documents', to: '/admin/kyc/documents' },
          { label: 'Upload' },
        ]}
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Document Details Form */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Document Details</CardTitle>
            <CardDescription>Enter document information</CardDescription>
          </CardHeader>
          <CardContent>
            <Form {...form}>
              <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <FormField
                    control={form.control}
                    name="customerId"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Customer</FormLabel>
                        <Select onValueChange={field.onChange} value={field.value}>
                          <FormControl>
                            <SelectTrigger>
                              <SelectValue placeholder="Select customer" />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            {customers.map(customer => (
                              <SelectItem key={customer.id} value={customer.id}>
                                {customer.name} ({customer.id})
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
                    name="documentType"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Document Type</FormLabel>
                        <Select onValueChange={field.onChange} value={field.value}>
                          <FormControl>
                            <SelectTrigger>
                              <SelectValue placeholder="Select type" />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            {documentTypes.map(type => (
                              <SelectItem key={type.value} value={type.value}>
                                {type.label}
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
                    name="documentNumber"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Document Number</FormLabel>
                        <FormControl>
                          <Input placeholder="Enter document number" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="issuingAuthority"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Issuing Authority</FormLabel>
                        <FormControl>
                          <Input placeholder="e.g., Income Tax Dept" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="issueDate"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Issue Date</FormLabel>
                        <FormControl>
                          <Input type="date" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  {selectedDocType?.requiresExpiry && (
                    <FormField
                      control={form.control}
                      name="expiryDate"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Expiry Date</FormLabel>
                          <FormControl>
                            <Input type="date" {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  )}
                </div>

                <FormField
                  control={form.control}
                  name="remarks"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Remarks</FormLabel>
                      <FormControl>
                        <Textarea placeholder="Any additional notes..." rows={2} {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                {/* File Upload Area */}
                <div className="space-y-4">
                  <Label>Upload Files</Label>
                  <div
                    className="border-2 border-dashed rounded-lg p-8 text-center cursor-pointer hover:border-primary transition-colors"
                    onDrop={handleDrop}
                    onDragOver={(e) => e.preventDefault()}
                    onClick={() => document.getElementById('file-input')?.click()}
                  >
                    <Upload className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                    <p className="text-lg font-medium">Drag & drop files here</p>
                    <p className="text-sm text-muted-foreground mt-1">
                      or click to browse
                    </p>
                    <p className="text-xs text-muted-foreground mt-2">
                      Supported: JPG, PNG, PDF (Max 10MB per file)
                    </p>
                    <input
                      id="file-input"
                      type="file"
                      multiple
                      accept=".jpg,.jpeg,.png,.pdf"
                      className="hidden"
                      onChange={handleFileSelect}
                    />
                  </div>

                  {/* Uploaded Files List */}
                  {files.length > 0 && (
                    <div className="space-y-2">
                      {files.map((uploadedFile) => (
                        <div
                          key={uploadedFile.id}
                          className="flex items-center gap-4 p-3 border rounded-lg"
                        >
                          {uploadedFile.preview ? (
                            <img
                              src={uploadedFile.preview}
                              alt="Preview"
                              className="h-12 w-12 object-cover rounded"
                            />
                          ) : (
                            getFileIcon(uploadedFile.file)
                          )}
                          <div className="flex-1 min-w-0">
                            <p className="font-medium truncate">{uploadedFile.file.name}</p>
                            <p className="text-sm text-muted-foreground">
                              {formatFileSize(uploadedFile.file.size)}
                            </p>
                          </div>
                          {uploadedFile.status === 'success' && (
                            <CheckCircle className="h-5 w-5 text-green-500" />
                          )}
                          {uploadedFile.status === 'error' && (
                            <AlertCircle className="h-5 w-5 text-red-500" />
                          )}
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            onClick={() => removeFile(uploadedFile.id)}
                          >
                            <X className="h-4 w-4" />
                          </Button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                <div className="flex gap-2">
                  <Button type="submit" disabled={isSubmitting || files.length === 0}>
                    {isSubmitting ? 'Uploading...' : 'Upload Document'}
                  </Button>
                  <Button type="button" variant="outline" onClick={() => navigate(-1)}>
                    Cancel
                  </Button>
                </div>
              </form>
            </Form>
          </CardContent>
        </Card>

        {/* Guidelines */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle>Upload Guidelines</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <h4 className="font-medium">Accepted Formats</h4>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>- JPEG, PNG for images</li>
                <li>- PDF for documents</li>
                <li>- Maximum file size: 10MB</li>
              </ul>
            </div>

            <div className="space-y-2">
              <h4 className="font-medium">Image Quality</h4>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>- Clear and readable</li>
                <li>- All corners visible</li>
                <li>- No blur or glare</li>
                <li>- Color scan preferred</li>
              </ul>
            </div>

            <div className="space-y-2">
              <h4 className="font-medium">Document Requirements</h4>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>- Self-attested copy</li>
                <li>- Current and valid</li>
                <li>- Address proof &lt; 3 months old</li>
                <li>- Bank statements latest 6 months</li>
              </ul>
            </div>

            <div className="p-3 bg-yellow-50 rounded-lg">
              <p className="text-sm text-yellow-800">
                <AlertCircle className="h-4 w-4 inline mr-1" />
                Ensure all personal information is clearly visible and matches the customer records.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
