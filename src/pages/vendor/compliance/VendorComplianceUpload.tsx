/**
 * Vendor Compliance Document Upload Page
 */

import { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Upload,
  Loader2,
  FileText,
  Calendar,
  Shield,
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useToast } from '@/hooks/use-toast';
import { vendorComplianceApi } from '@/services/vendorApi';
import type { ComplianceDocumentType } from '@/types/vendor';

const DOCUMENT_TYPES = [
  { value: 'PAN_CARD', label: 'PAN Card', description: 'Permanent Account Number card' },
  { value: 'GST_CERTIFICATE', label: 'GST Certificate', description: 'GST registration certificate' },
  { value: 'MSME_CERTIFICATE', label: 'MSME Certificate', description: 'Micro, Small and Medium Enterprises certificate' },
  { value: 'ISO_CERTIFICATE', label: 'ISO Certificate', description: 'ISO quality certification' },
  { value: 'TDS_CERTIFICATE', label: 'TDS Certificate', description: 'Tax Deducted at Source certificate' },
  { value: 'FORM_16A', label: 'Form 16A', description: 'TDS certificate for non-salary payments' },
  { value: 'INSURANCE_POLICY', label: 'Insurance Policy', description: 'Business insurance policy' },
  { value: 'FSSAI_LICENSE', label: 'FSSAI License', description: 'Food Safety and Standards Authority license' },
  { value: 'POLLUTION_CERT', label: 'Pollution Certificate', description: 'Pollution control certificate' },
  { value: 'FACTORY_LICENSE', label: 'Factory License', description: 'Factory operating license' },
  { value: 'DRUG_LICENSE', label: 'Drug License', description: 'Pharmaceutical drug license' },
  { value: 'CANCELLED_CHEQUE', label: 'Cancelled Cheque', description: 'Bank verification document' },
  { value: 'OTHER', label: 'Other', description: 'Other compliance document' },
];

export default function VendorComplianceUpload() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [uploading, setUploading] = useState(false);
  const [uploadForm, setUploadForm] = useState({
    document_type: '' as ComplianceDocumentType | '',
    document_name: '',
    document_number: '',
    issue_date: '',
    expiry_date: '',
    is_perpetual: false,
  });
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      // Validate file size (max 10MB)
      if (file.size > 10 * 1024 * 1024) {
        toast({ variant: 'destructive', title: 'File size must be less than 10MB' });
        return;
      }
      setSelectedFile(file);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!selectedFile || !uploadForm.document_type || !uploadForm.document_name) {
      toast({ variant: 'destructive', title: 'Please fill in all required fields' });
      return;
    }

    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('document_type', uploadForm.document_type);
      formData.append('document_name', uploadForm.document_name);
      if (uploadForm.document_number) formData.append('document_number', uploadForm.document_number);
      if (uploadForm.issue_date) formData.append('issue_date', uploadForm.issue_date);
      if (uploadForm.expiry_date) formData.append('expiry_date', uploadForm.expiry_date);
      formData.append('is_perpetual', String(uploadForm.is_perpetual));

      await vendorComplianceApi.upload(formData);

      toast({ title: 'Document uploaded successfully' });
      navigate('/vendor/compliance');
    } catch (error) {
      console.error('Failed to upload document:', error);
      toast({
        variant: 'destructive',
        title: 'Error',
        description: 'Failed to upload document',
      });
    } finally {
      setUploading(false);
    }
  };

  const selectedDocType = DOCUMENT_TYPES.find(t => t.value === uploadForm.document_type);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center space-x-4">
        <Button variant="ghost" onClick={() => navigate('/vendor/compliance')}>
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back to Compliance
        </Button>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Upload Compliance Document</h1>
          <p className="text-gray-600">Upload a new compliance or statutory document</p>
        </div>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Form */}
          <div className="lg:col-span-2 space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <FileText className="h-5 w-5 mr-2 text-purple-600" />
                  Document Information
                </CardTitle>
                <CardDescription>
                  Enter the details of the document you are uploading
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-2">
                  <Label htmlFor="document_type">Document Type *</Label>
                  <Select
                    value={uploadForm.document_type}
                    onValueChange={(v) => setUploadForm({ ...uploadForm, document_type: v as ComplianceDocumentType })}
                  >
                    <SelectTrigger id="document_type">
                      <SelectValue placeholder="Select document type" />
                    </SelectTrigger>
                    <SelectContent>
                      {DOCUMENT_TYPES.map((type) => (
                        <SelectItem key={type.value} value={type.value}>
                          {type.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  {selectedDocType && (
                    <p className="text-xs text-gray-500">{selectedDocType.description}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="document_name">Document Name *</Label>
                  <Input
                    id="document_name"
                    value={uploadForm.document_name}
                    onChange={(e) => setUploadForm({ ...uploadForm, document_name: e.target.value })}
                    placeholder="e.g., GST Certificate - FY 2024-25"
                  />
                  <p className="text-xs text-gray-500">
                    A descriptive name for easy identification
                  </p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="document_number">Document Number</Label>
                  <Input
                    id="document_number"
                    value={uploadForm.document_number}
                    onChange={(e) => setUploadForm({ ...uploadForm, document_number: e.target.value })}
                    placeholder="e.g., 29ABCDE1234F1ZK"
                  />
                  <p className="text-xs text-gray-500">
                    The official document number or registration number
                  </p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Calendar className="h-5 w-5 mr-2 text-purple-600" />
                  Validity Period
                </CardTitle>
                <CardDescription>
                  Specify the validity period of this document
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="issue_date">Issue Date</Label>
                    <Input
                      id="issue_date"
                      type="date"
                      value={uploadForm.issue_date}
                      onChange={(e) => setUploadForm({ ...uploadForm, issue_date: e.target.value })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="expiry_date">Expiry Date</Label>
                    <Input
                      id="expiry_date"
                      type="date"
                      value={uploadForm.expiry_date}
                      onChange={(e) => setUploadForm({ ...uploadForm, expiry_date: e.target.value })}
                      disabled={uploadForm.is_perpetual}
                    />
                  </div>
                </div>

                <div className="flex items-center space-x-2 p-4 bg-gray-50 rounded-lg">
                  <input
                    type="checkbox"
                    id="perpetual"
                    checked={uploadForm.is_perpetual}
                    onChange={(e) => setUploadForm({
                      ...uploadForm,
                      is_perpetual: e.target.checked,
                      expiry_date: e.target.checked ? '' : uploadForm.expiry_date
                    })}
                    className="h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded"
                  />
                  <Label htmlFor="perpetual" className="font-normal">
                    This document does not expire (perpetual validity)
                  </Label>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* File Upload Card */}
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Upload className="h-5 w-5 mr-2 text-purple-600" />
                  Upload File
                </CardTitle>
                <CardDescription>
                  Select the document file to upload
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div
                  className="border-2 border-dashed border-gray-200 rounded-lg p-6 text-center cursor-pointer hover:border-purple-400 transition-colors"
                  onClick={() => fileInputRef.current?.click()}
                >
                  <Input
                    type="file"
                    ref={fileInputRef}
                    onChange={handleFileSelect}
                    accept=".pdf,.jpg,.jpeg,.png"
                    className="hidden"
                  />
                  {selectedFile ? (
                    <div className="space-y-2">
                      <FileText className="h-10 w-10 text-purple-600 mx-auto" />
                      <p className="font-medium text-gray-900">{selectedFile.name}</p>
                      <p className="text-sm text-gray-500">
                        {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                      </p>
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedFile(null);
                          if (fileInputRef.current) fileInputRef.current.value = '';
                        }}
                      >
                        Remove
                      </Button>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      <Upload className="h-10 w-10 text-gray-400 mx-auto" />
                      <p className="text-gray-600">Click to select a file</p>
                      <p className="text-xs text-gray-400">
                        PDF, JPG, or PNG (max 10MB)
                      </p>
                    </div>
                  )}
                </div>

                <div className="text-xs text-gray-500 space-y-1">
                  <p>Accepted formats: PDF, JPG, JPEG, PNG</p>
                  <p>Maximum file size: 10MB</p>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-purple-50 border-purple-200">
              <CardContent className="pt-6">
                <div className="flex items-start space-x-3">
                  <Shield className="h-5 w-5 text-purple-600 mt-0.5" />
                  <div>
                    <h4 className="font-medium text-purple-900">Document Verification</h4>
                    <p className="text-sm text-purple-700 mt-1">
                      Uploaded documents will be reviewed and verified by the procurement team.
                      You will be notified once the verification is complete.
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Action Buttons */}
            <div className="flex flex-col space-y-3">
              <Button
                type="submit"
                disabled={uploading || !selectedFile || !uploadForm.document_type || !uploadForm.document_name}
                className="w-full bg-purple-600 hover:bg-purple-700"
              >
                {uploading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                <Upload className="h-4 w-4 mr-2" />
                Upload Document
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => navigate('/vendor/compliance')}
                className="w-full"
              >
                Cancel
              </Button>
            </div>
          </div>
        </div>
      </form>
    </div>
  );
}
