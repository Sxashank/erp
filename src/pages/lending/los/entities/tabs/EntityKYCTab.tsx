/**
 * Entity KYC Tab
 * Inline management of entity KYC documents (NO MODALS)
 */

import {
  Plus,
  Trash2,
  X,
  Check,
  Loader2,
  Upload,
  FileText,
  Eye,
  ShieldCheck,
  XCircle,
} from 'lucide-react';
import { useState, useEffect, useRef } from 'react';

import { DateDisplay } from '@/components/lending/common/DateDisplay';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { entityApi } from '@/services/lending';
import type { EntityKYCDocument } from '@/types/lending';

const KYC_DOCUMENT_TYPES = [
  { value: 'PAN_CARD', label: 'PAN Card' },
  { value: 'AADHAAR', label: 'Aadhaar Card' },
  { value: 'PASSPORT', label: 'Passport' },
  { value: 'VOTER_ID', label: 'Voter ID' },
  { value: 'DRIVING_LICENSE', label: 'Driving License' },
  { value: 'COI', label: 'Certificate of Incorporation' },
  { value: 'MOA', label: 'Memorandum of Association' },
  { value: 'AOA', label: 'Articles of Association' },
  { value: 'PARTNERSHIP_DEED', label: 'Partnership Deed' },
  { value: 'LLP_AGREEMENT', label: 'LLP Agreement' },
  { value: 'BOARD_RESOLUTION', label: 'Board Resolution' },
  { value: 'GSTIN_CERTIFICATE', label: 'GSTIN Certificate' },
  { value: 'ITR', label: 'Income Tax Return' },
  { value: 'AUDITED_FINANCIALS', label: 'Audited Financial Statements' },
  { value: 'BANK_STATEMENT', label: 'Bank Statement' },
  { value: 'OTHER', label: 'Other' },
];

interface EntityKYCTabProps {
  entityId: string;
}

export default function EntityKYCTab({ entityId }: EntityKYCTabProps) {
  const [documents, setDocuments] = useState<EntityKYCDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [verifyingId, setVerifyingId] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Upload form state
  const [uploadForm, setUploadForm] = useState({
    documentType: '',
    documentNumber: '',
    expiryDate: '',
    file: null as File | null,
  });

  // Verify form state
  const [verifyForm, setVerifyForm] = useState({
    status: '' as 'VERIFIED' | 'REJECTED' | '',
    remarks: '',
  });

  useEffect(() => {
    loadDocuments();
  }, [entityId]);

  const loadDocuments = async () => {
    setLoading(true);
    try {
      const data = await entityApi.getEntityKYCDocuments(entityId);
      setDocuments(data);
    } catch {
    } finally {
      setLoading(false);
    }
  };

  const handleStartUpload = () => {
    setUploadForm({
      documentType: '',
      documentNumber: '',
      expiryDate: '',
      file: null,
    });
    setIsUploading(true);
  };

  const handleCancelUpload = () => {
    setUploadForm({
      documentType: '',
      documentNumber: '',
      expiryDate: '',
      file: null,
    });
    setIsUploading(false);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] || null;
    setUploadForm((prev) => ({ ...prev, file }));
  };

  const handleUpload = async () => {
    if (!uploadForm.documentType || !uploadForm.file) {
      alert('Please select document type and file');
      return;
    }

    setSaving(true);
    try {
      const formData = new FormData();
      formData.append('file', uploadForm.file);
      formData.append('document_type', uploadForm.documentType);
      if (uploadForm.documentNumber) {
        formData.append('document_number', uploadForm.documentNumber);
      }
      if (uploadForm.expiryDate) {
        formData.append('expiry_date', uploadForm.expiryDate);
      }

      await entityApi.uploadKYCDocument(entityId, formData);
      await loadDocuments();
      handleCancelUpload();
    } catch {
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (documentId: string) => {
    if (!confirm('Are you sure you want to delete this document?')) return;
    try {
      await entityApi.deleteKYCDocument(entityId, documentId);
      await loadDocuments();
    } catch {}
  };

  const handleStartVerify = (documentId: string) => {
    setVerifyingId(documentId);
    setVerifyForm({ status: '', remarks: '' });
  };

  const handleCancelVerify = () => {
    setVerifyingId(null);
    setVerifyForm({ status: '', remarks: '' });
  };

  const handleVerify = async () => {
    if (!verifyingId || !verifyForm.status) return;

    setSaving(true);
    try {
      await entityApi.verifyKYCDocument(entityId, verifyingId, {
        status: verifyForm.status,
        remarks: verifyForm.remarks || undefined,
      });
      await loadDocuments();
      handleCancelVerify();
    } catch {
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex h-48 items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
      </div>
    );
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle>KYC Documents</CardTitle>
          <CardDescription>Identity and verification documents</CardDescription>
        </div>
        {!isUploading && (
          <Button onClick={handleStartUpload}>
            <Plus className="mr-2 h-4 w-4" />
            Upload Document
          </Button>
        )}
      </CardHeader>
      <CardContent>
        {/* Upload Form */}
        {isUploading && (
          <div className="mb-6 rounded-lg border bg-gray-50 p-4">
            <h4 className="mb-4 font-medium">Upload KYC Document</h4>
            <div className="space-y-4">
              <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                <div className="space-y-2">
                  <Label>Document Type *</Label>
                  <Select
                    value={uploadForm.documentType}
                    onValueChange={(value) =>
                      setUploadForm((prev) => ({ ...prev, documentType: value }))
                    }
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select type" />
                    </SelectTrigger>
                    <SelectContent>
                      {KYC_DOCUMENT_TYPES.map((type) => (
                        <SelectItem key={type.value} value={type.value}>
                          {type.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label>Document Number</Label>
                  <Input
                    placeholder="e.g., XXXXX0000X"
                    value={uploadForm.documentNumber}
                    onChange={(e) =>
                      setUploadForm((prev) => ({ ...prev, documentNumber: e.target.value }))
                    }
                  />
                </div>

                <div className="space-y-2">
                  <Label>Expiry Date</Label>
                  <Input
                    type="date"
                    value={uploadForm.expiryDate}
                    onChange={(e) =>
                      setUploadForm((prev) => ({ ...prev, expiryDate: e.target.value }))
                    }
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label>File *</Label>
                <div className="rounded-lg border-2 border-dashed p-4">
                  <input
                    ref={fileInputRef}
                    type="file"
                    onChange={handleFileChange}
                    accept=".pdf,.jpg,.jpeg,.png"
                    className="hidden"
                    id="kyc-file-input"
                  />
                  <label
                    htmlFor="kyc-file-input"
                    className="flex cursor-pointer flex-col items-center justify-center"
                  >
                    {uploadForm.file ? (
                      <div className="flex items-center gap-2">
                        <FileText className="h-8 w-8 text-blue-500" />
                        <div>
                          <p className="font-medium">{uploadForm.file.name}</p>
                          <p className="text-sm text-gray-500">
                            {(uploadForm.file.size / 1024 / 1024).toFixed(2)} MB
                          </p>
                        </div>
                      </div>
                    ) : (
                      <>
                        <Upload className="mb-2 h-8 w-8 text-gray-400" />
                        <p className="text-sm text-gray-500">Click to upload or drag and drop</p>
                        <p className="text-xs text-gray-400">PDF, JPG, PNG up to 10MB</p>
                      </>
                    )}
                  </label>
                </div>
              </div>

              <div className="flex gap-2">
                <Button onClick={handleUpload} disabled={saving || !uploadForm.file}>
                  {saving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  <Upload className="mr-2 h-4 w-4" />
                  Upload
                </Button>
                <Button variant="outline" onClick={handleCancelUpload}>
                  <X className="mr-2 h-4 w-4" />
                  Cancel
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* Documents List */}
        {documents.length === 0 && !isUploading ? (
          <p className="py-8 text-center text-gray-500">
            No KYC documents uploaded yet. Click "Upload Document" to add one.
          </p>
        ) : (
          <div className="space-y-4">
            {documents.map((doc) => (
              <div key={doc.id} className="rounded-lg border p-4">
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3">
                    <div className="rounded-lg bg-gray-100 p-2">
                      <FileText className="h-5 w-5 text-gray-600" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <p className="font-medium">{doc.documentName || doc.documentTypeId}</p>
                        <Badge
                          variant={
                            doc.verificationStatus === 'VERIFIED'
                              ? 'default'
                              : doc.verificationStatus === 'REJECTED'
                                ? 'destructive'
                                : 'secondary'
                          }
                        >
                          {doc.verificationStatus === 'VERIFIED' && (
                            <ShieldCheck className="mr-1 h-3 w-3" />
                          )}
                          {doc.verificationStatus === 'REJECTED' && (
                            <XCircle className="mr-1 h-3 w-3" />
                          )}
                          {doc.verificationStatus}
                        </Badge>
                      </div>
                      {doc.documentNumber && (
                        <p className="text-sm text-gray-600">Document No: {doc.documentNumber}</p>
                      )}
                      {doc.expiryDate && (
                        <p className="text-sm text-gray-500">
                          Expiry: <DateDisplay date={doc.expiryDate} />
                        </p>
                      )}
                      <p className="mt-1 text-xs text-gray-400">
                        Uploaded: <DateDisplay date={doc.createdAt} showTime />
                      </p>
                      {doc.verifiedAt && (
                        <p className="text-xs text-gray-400">
                          Verified: <DateDisplay date={doc.verifiedAt} showTime />
                        </p>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <Button variant="ghost" size="sm">
                      <Eye className="h-4 w-4" />
                    </Button>
                    {doc.verificationStatus === 'PENDING' && (
                      <Button variant="outline" size="sm" onClick={() => handleStartVerify(doc.id)}>
                        Verify
                      </Button>
                    )}
                    <Button variant="ghost" size="sm" onClick={() => handleDelete(doc.id)}>
                      <Trash2 className="h-4 w-4 text-red-500" />
                    </Button>
                  </div>
                </div>

                {/* Inline Verify Form */}
                {verifyingId === doc.id && (
                  <div className="mt-4 border-t pt-4">
                    <h5 className="mb-3 font-medium">Verify Document</h5>
                    <div className="space-y-4">
                      <div className="flex gap-2">
                        <Button
                          variant={verifyForm.status === 'VERIFIED' ? 'default' : 'outline'}
                          onClick={() => setVerifyForm((prev) => ({ ...prev, status: 'VERIFIED' }))}
                        >
                          <Check className="mr-2 h-4 w-4" />
                          Verify
                        </Button>
                        <Button
                          variant={verifyForm.status === 'REJECTED' ? 'destructive' : 'outline'}
                          onClick={() => setVerifyForm((prev) => ({ ...prev, status: 'REJECTED' }))}
                        >
                          <X className="mr-2 h-4 w-4" />
                          Reject
                        </Button>
                      </div>

                      {verifyForm.status && (
                        <>
                          <div className="space-y-2">
                            <Label>Remarks {verifyForm.status === 'REJECTED' && '*'}</Label>
                            <Textarea
                              placeholder={
                                verifyForm.status === 'REJECTED'
                                  ? 'Reason for rejection (required)'
                                  : 'Optional remarks'
                              }
                              value={verifyForm.remarks}
                              onChange={(e) =>
                                setVerifyForm((prev) => ({ ...prev, remarks: e.target.value }))
                              }
                            />
                          </div>

                          <div className="flex gap-2">
                            <Button
                              onClick={handleVerify}
                              disabled={
                                saving || (verifyForm.status === 'REJECTED' && !verifyForm.remarks)
                              }
                            >
                              {saving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                              Confirm
                            </Button>
                            <Button variant="outline" onClick={handleCancelVerify}>
                              Cancel
                            </Button>
                          </div>
                        </>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
