import { useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  ArrowLeft,
  CheckCircle,
  XCircle,
  ZoomIn,
  ZoomOut,
  RotateCw,
  Download,
  Clock,
  User,
  Calendar,
  FileText,
  AlertTriangle,
  Shield,
} from 'lucide-react';

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

  const handleZoomIn = () => setZoom(prev => Math.min(prev + 25, 200));
  const handleZoomOut = () => setZoom(prev => Math.max(prev - 25, 50));
  const handleRotate = () => setRotation(prev => (prev + 90) % 360);

  const handleVerify = async () => {
    setIsSubmitting(true);
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1500));
    setIsSubmitting(false);
    navigate('/admin/kyc/documents');
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'VERIFIED':
        return <Badge variant="default" className="bg-green-100 text-green-800"><CheckCircle className="h-3 w-3 mr-1" />Verified</Badge>;
      case 'REJECTED':
        return <Badge variant="destructive"><XCircle className="h-3 w-3 mr-1" />Rejected</Badge>;
      case 'PENDING':
        return <Badge variant="secondary"><Clock className="h-3 w-3 mr-1" />Pending Verification</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link to="/admin/kyc/documents">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back
            </Button>
          </Link>
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <Shield className="h-6 w-6" />
              Verify Document
            </h1>
            <p className="text-muted-foreground">Review and verify KYC document</p>
          </div>
        </div>
        {getStatusBadge(documentData.verificationStatus)}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Document Preview */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>Document Preview</span>
              <div className="flex items-center gap-2">
                <Button variant="outline" size="sm" onClick={handleZoomOut}>
                  <ZoomOut className="h-4 w-4" />
                </Button>
                <span className="text-sm w-12 text-center">{zoom}%</span>
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
            <div className="bg-gray-100 rounded-lg p-4 min-h-[500px] flex items-center justify-center overflow-auto">
              <div
                style={{
                  transform: `scale(${zoom / 100}) rotate(${rotation}deg)`,
                  transition: 'transform 0.3s ease',
                }}
              >
                {/* Placeholder for actual document image */}
                <div className="bg-white rounded-lg shadow-lg p-8 w-[400px] h-[250px] flex flex-col items-center justify-center">
                  <FileText className="h-16 w-16 text-gray-400 mb-4" />
                  <p className="text-lg font-medium">{documentTypeLabels[documentData.documentType]}</p>
                  <p className="text-sm text-muted-foreground">{documentData.fileName}</p>
                  <p className="text-xs text-muted-foreground mt-2">{documentData.fileSize}</p>
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
                    className={verificationAction === 'approve' ? 'bg-green-600 hover:bg-green-700' : ''}
                    onClick={() => setVerificationAction('approve')}
                  >
                    <CheckCircle className="h-4 w-4 mr-2" />
                    Approve
                  </Button>
                  <Button
                    variant={verificationAction === 'reject' ? 'destructive' : 'outline'}
                    onClick={() => setVerificationAction('reject')}
                  >
                    <XCircle className="h-4 w-4 mr-2" />
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
                        {rejectionReasons.map(reason => (
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
                    <div className="h-8 w-8 rounded-full bg-gray-100 flex items-center justify-center flex-shrink-0">
                      <User className="h-4 w-4 text-gray-600" />
                    </div>
                    <div>
                      <p className="font-medium">{entry.action}</p>
                      <p className="text-muted-foreground">
                        by {entry.by} on {entry.at}
                      </p>
                      {entry.remarks && (
                        <p className="text-muted-foreground mt-1">{entry.remarks}</p>
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
