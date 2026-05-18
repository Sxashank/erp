import {
  CheckCircle,
  XCircle,
  ZoomIn,
  ZoomOut,
  RotateCw,
  Download,
  Clock,
  User,
  FileText,
} from 'lucide-react';
import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';

// Mock document data
const documentData = {
  id: '1',
  customerId: 'CUST001',
  customerName: 'Rajesh Kumar',
  customerPan: 'ABCDE1234F',
  documentType: 'PAN_CARD',
  documentNumber: 'ABCDE1234F',
  fileName: 'pan_card_rajesh.jpg',
  fileSize: '245 KB',
  fileUrl: '/api/documents/pan_card_rajesh.jpg',
  uploadedAt: '2025-01-15 10:30:00',
  uploadedBy: 'Branch Staff',
  issueDate: '2015-03-20',
  expiryDate: null,
  issuingAuthority: 'Income Tax Department',
  verificationStatus: 'PENDING',
  verifiedBy: null,
  verifiedAt: null,
  remarks: '',
  previousVerifications: [
    {
      action: 'UPLOADED',
      by: 'Branch Staff',
      at: '2025-01-15 10:30:00',
      remarks: 'Initial upload',
    },
  ],
};

// Rejection reasons
const rejectionReasons = [
  { value: 'BLURRY', label: 'Document is blurry or unclear' },
  { value: 'INCOMPLETE', label: 'Document is incomplete or cropped' },
  { value: 'EXPIRED', label: 'Document has expired' },
  { value: 'MISMATCH', label: 'Details do not match customer records' },
  { value: 'TAMPERED', label: 'Document appears to be tampered' },
  { value: 'WRONG_TYPE', label: 'Wrong document type uploaded' },
  { value: 'OLD_ADDRESS', label: 'Address proof is older than 3 months' },
  { value: 'OTHER', label: 'Other reason' },
];

const documentTypeLabels: Record<string, string> = {
  PAN_CARD: 'PAN Card',
  AADHAAR: 'Aadhaar',
  PASSPORT: 'Passport',
  VOTER_ID: 'Voter ID',
  DRIVING_LICENSE: 'Driving License',
  ADDRESS_PROOF: 'Address Proof',
};

export default function KYCDocumentVerify() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [zoom, setZoom] = useState(100);
  const [rotation, setRotation] = useState(0);
  const [verificationAction, setVerificationAction] = useState<'approve' | 'reject' | null>(null);
  const [rejectionReason, setRejectionReason] = useState('');
  const [remarks, setRemarks] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleZoomIn = () => setZoom((prev) => Math.min(prev + 25, 200));
  const handleZoomOut = () => setZoom((prev) => Math.max(prev - 25, 50));
  const handleRotate = () => setRotation((prev) => (prev + 90) % 360);

  const handleVerify = async () => {
    setIsSubmitting(true);
    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 1500));
    setIsSubmitting(false);
    navigate('/admin/kyc/documents');
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'VERIFIED':
        return (
          <Badge variant="default" className="bg-green-100 text-green-800">
            <CheckCircle className="mr-1 h-3 w-3" />
            Verified
          </Badge>
        );
      case 'REJECTED':
        return (
          <Badge variant="destructive">
            <XCircle className="mr-1 h-3 w-3" />
            Rejected
          </Badge>
        );
      case 'PENDING':
        return (
          <Badge variant="secondary">
            <Clock className="mr-1 h-3 w-3" />
            Pending Verification
          </Badge>
        );
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  return (
    <div className="container mx-auto space-y-6 py-6">
      <PageHeader
        title="Verify Document"
        subtitle="Review and verify KYC document"
        breadcrumbs={[{ label: 'KYC Documents', to: '/admin/kyc/documents' }, { label: 'Verify' }]}
        actions={getStatusBadge(documentData.verificationStatus)}
      />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Document Preview */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>Document Preview</span>
              <div className="flex items-center gap-2">
                <Button variant="outline" size="sm" onClick={handleZoomOut}>
                  <ZoomOut className="h-4 w-4" />
                </Button>
                <span className="w-12 text-center text-sm">{zoom}%</span>
                <Button variant="outline" size="sm" onClick={handleZoomIn}>
                  <ZoomIn className="h-4 w-4" />
                </Button>
                <Button variant="outline" size="sm" onClick={handleRotate}>
                  <RotateCw className="h-4 w-4" />
                </Button>
                <Button variant="outline" size="sm">
                  <Download className="h-4 w-4" />
                </Button>
              </div>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex min-h-[500px] items-center justify-center overflow-auto rounded-lg bg-gray-100 p-4">
              <div
                style={{
                  transform: `scale(${zoom / 100}) rotate(${rotation}deg)`,
                  transition: 'transform 0.3s ease',
                }}
              >
                {/* Placeholder for actual document image */}
                <div className="flex h-[250px] w-[400px] flex-col items-center justify-center rounded-lg bg-white p-8 shadow-lg">
                  <FileText className="mb-4 h-16 w-16 text-gray-400" />
                  <p className="text-lg font-medium">
                    {documentTypeLabels[documentData.documentType]}
                  </p>
                  <p className="text-sm text-muted-foreground">{documentData.fileName}</p>
                  <p className="mt-2 text-xs text-muted-foreground">{documentData.fileSize}</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Document Details & Verification */}
        <div className="space-y-6">
          {/* Document Info */}
          <Card>
            <CardHeader>
              <CardTitle>Document Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-muted-foreground">Customer</p>
                  <p className="font-medium">{documentData.customerName}</p>
                  <p className="text-xs text-muted-foreground">{documentData.customerId}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Customer PAN</p>
                  <p className="font-mono">{documentData.customerPan}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Document Type</p>
                  <p className="font-medium">{documentTypeLabels[documentData.documentType]}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Document Number</p>
                  <p className="font-mono">{documentData.documentNumber}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Issue Date</p>
                  <p>{documentData.issueDate || 'N/A'}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Expiry Date</p>
                  <p>{documentData.expiryDate || 'N/A'}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Uploaded By</p>
                  <p>{documentData.uploadedBy}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Uploaded At</p>
                  <p>{documentData.uploadedAt}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Verification Checklist */}
          <Card>
            <CardHeader>
              <CardTitle>Verification Checklist</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {[
                  'Document is clear and readable',
                  'All corners are visible',
                  'No signs of tampering',
                  'Details match customer records',
                  'Document is not expired',
                  'Self-attestation visible (if required)',
                ].map((item, index) => (
                  <label key={index} className="flex items-center gap-2 text-sm">
                    <input type="checkbox" className="rounded border-gray-300" />
                    {item}
                  </label>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Verification Action */}
          {documentData.verificationStatus === 'PENDING' && (
            <Card>
              <CardHeader>
                <CardTitle>Verification Decision</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex gap-2">
                  <Button
                    variant={verificationAction === 'approve' ? 'default' : 'outline'}
                    className={
                      verificationAction === 'approve' ? 'bg-green-600 hover:bg-green-700' : ''
                    }
                    onClick={() => setVerificationAction('approve')}
                  >
                    <CheckCircle className="mr-2 h-4 w-4" />
                    Approve
                  </Button>
                  <Button
                    variant={verificationAction === 'reject' ? 'destructive' : 'outline'}
                    onClick={() => setVerificationAction('reject')}
                  >
                    <XCircle className="mr-2 h-4 w-4" />
                    Reject
                  </Button>
                </div>

                {verificationAction === 'reject' && (
                  <div className="space-y-2">
                    <Label>Rejection Reason</Label>
                    <Select value={rejectionReason} onValueChange={setRejectionReason}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select reason" />
                      </SelectTrigger>
                      <SelectContent>
                        {rejectionReasons.map((reason) => (
                          <SelectItem key={reason.value} value={reason.value}>
                            {reason.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                )}

                <div className="space-y-2">
                  <Label>Remarks</Label>
                  <Textarea
                    placeholder="Add verification remarks..."
                    value={remarks}
                    onChange={(e) => setRemarks(e.target.value)}
                    rows={3}
                  />
                </div>

                <Button
                  className="w-full"
                  disabled={
                    !verificationAction ||
                    (verificationAction === 'reject' && !rejectionReason) ||
                    isSubmitting
                  }
                  onClick={handleVerify}
                >
                  {isSubmitting ? 'Submitting...' : 'Submit Verification'}
                </Button>
              </CardContent>
            </Card>
          )}

          {/* Verification History */}
          <Card>
            <CardHeader>
              <CardTitle>History</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {documentData.previousVerifications.map((entry, index) => (
                  <div key={index} className="flex items-start gap-3 text-sm">
                    <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-gray-100">
                      <User className="h-4 w-4 text-gray-600" />
                    </div>
                    <div>
                      <p className="font-medium">{entry.action}</p>
                      <p className="text-muted-foreground">
                        by {entry.by} on {entry.at}
                      </p>
                      {entry.remarks && (
                        <p className="mt-1 text-muted-foreground">{entry.remarks}</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
