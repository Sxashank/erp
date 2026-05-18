import {
  FileText,
  Search,
  Filter,
  Plus,
  Eye,
  CheckCircle,
  XCircle,
  Clock,
  AlertTriangle,
  Download,
  Upload,
  Image,
  File,
} from 'lucide-react';
import { useState } from 'react';
import { Link } from 'react-router-dom';

import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
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

// Mock documents data
const documents = [
  {
    id: '1',
    customerId: 'CUST001',
    customerName: 'Rajesh Kumar',
    documentType: 'PAN_CARD',
    documentNumber: 'ABCDE1234F',
    fileName: 'pan_card_rajesh.jpg',
    fileSize: '245 KB',
    uploadedAt: '2025-01-15 10:30:00',
    verificationStatus: 'VERIFIED',
    verifiedBy: 'KYC Officer',
    verifiedAt: '2025-01-15 14:00:00',
    expiryDate: null,
  },
  {
    id: '2',
    customerId: 'CUST001',
    customerName: 'Rajesh Kumar',
    documentType: 'AADHAAR',
    documentNumber: '****-****-1234',
    fileName: 'aadhaar_rajesh.jpg',
    fileSize: '312 KB',
    uploadedAt: '2025-01-15 10:32:00',
    verificationStatus: 'VERIFIED',
    verifiedBy: 'KYC Officer',
    verifiedAt: '2025-01-15 14:05:00',
    expiryDate: null,
  },
  {
    id: '3',
    customerId: 'CUST002',
    customerName: 'Priya Sharma',
    documentType: 'PASSPORT',
    documentNumber: 'K1234567',
    fileName: 'passport_priya.pdf',
    fileSize: '1.2 MB',
    uploadedAt: '2025-01-14 16:20:00',
    verificationStatus: 'PENDING',
    verifiedBy: null,
    verifiedAt: null,
    expiryDate: '2030-05-15',
  },
  {
    id: '4',
    customerId: 'CUST002',
    customerName: 'Priya Sharma',
    documentType: 'ADDRESS_PROOF',
    documentNumber: 'ELEC-12345678',
    fileName: 'electricity_bill_priya.pdf',
    fileSize: '890 KB',
    uploadedAt: '2025-01-14 16:25:00',
    verificationStatus: 'REJECTED',
    verifiedBy: 'KYC Officer',
    verifiedAt: '2025-01-14 18:00:00',
    rejectionReason: 'Document older than 3 months',
    expiryDate: null,
  },
  {
    id: '5',
    customerId: 'CUST003',
    customerName: 'Amit Patel',
    documentType: 'PAN_CARD',
    documentNumber: 'FGHIJ5678K',
    fileName: 'pan_amit.jpg',
    fileSize: '198 KB',
    uploadedAt: '2025-01-13 09:15:00',
    verificationStatus: 'VERIFIED',
    verifiedBy: 'KYC Team',
    verifiedAt: '2025-01-13 11:30:00',
    expiryDate: null,
  },
  {
    id: '6',
    customerId: 'CUST004',
    customerName: 'Sunita Devi',
    documentType: 'VOTER_ID',
    documentNumber: 'XYZ1234567',
    fileName: 'voter_id_sunita.jpg',
    fileSize: '267 KB',
    uploadedAt: '2025-01-12 14:45:00',
    verificationStatus: 'PENDING',
    verifiedBy: null,
    verifiedAt: null,
    expiryDate: null,
  },
  {
    id: '7',
    customerId: 'CUST005',
    customerName: 'Vikram Singh',
    documentType: 'DRIVING_LICENSE',
    documentNumber: 'DL-1234567890',
    fileName: 'driving_license_vikram.jpg',
    fileSize: '345 KB',
    uploadedAt: '2025-01-11 11:20:00',
    verificationStatus: 'EXPIRING_SOON',
    verifiedBy: 'KYC Team',
    verifiedAt: '2025-01-11 15:00:00',
    expiryDate: '2025-02-28',
  },
];

// Document type labels
const documentTypeLabels: Record<string, string> = {
  PAN_CARD: 'PAN Card',
  AADHAAR: 'Aadhaar',
  PASSPORT: 'Passport',
  VOTER_ID: 'Voter ID',
  DRIVING_LICENSE: 'Driving License',
  ADDRESS_PROOF: 'Address Proof',
  BANK_STATEMENT: 'Bank Statement',
  PHOTO: 'Photograph',
  SIGNATURE: 'Signature',
};

export default function KYCDocumentList() {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [typeFilter, setTypeFilter] = useState('all');

  const filteredDocuments = documents.filter(doc => {
    const matchesSearch =
      doc.customerName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      doc.customerId.toLowerCase().includes(searchTerm.toLowerCase()) ||
      doc.documentNumber.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || doc.verificationStatus === statusFilter;
    const matchesType = typeFilter === 'all' || doc.documentType === typeFilter;
    return matchesSearch && matchesStatus && matchesType;
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'VERIFIED':
        return <Badge variant="default" className="bg-green-100 text-green-800"><CheckCircle className="h-3 w-3 mr-1" />Verified</Badge>;
      case 'REJECTED':
        return <Badge variant="destructive"><XCircle className="h-3 w-3 mr-1" />Rejected</Badge>;
      case 'PENDING':
        return <Badge variant="secondary"><Clock className="h-3 w-3 mr-1" />Pending</Badge>;
      case 'EXPIRING_SOON':
        return <Badge variant="outline" className="bg-orange-100 text-orange-800"><AlertTriangle className="h-3 w-3 mr-1" />Expiring Soon</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const getFileIcon = (fileName: string) => {
    if (fileName.endsWith('.pdf')) {
      return <File className="h-4 w-4 text-red-500" />;
    }
    return <Image className="h-4 w-4 text-blue-500" />;
  };

  // Statistics
  const stats = {
    total: documents.length,
    verified: documents.filter(d => d.verificationStatus === 'VERIFIED').length,
    pending: documents.filter(d => d.verificationStatus === 'PENDING').length,
    rejected: documents.filter(d => d.verificationStatus === 'REJECTED').length,
    expiring: documents.filter(d => d.verificationStatus === 'EXPIRING_SOON').length,
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      <PageHeader
        title="KYC Documents"
        subtitle="Manage and verify customer KYC documents"
        actions={
          <Link to="/admin/kyc/documents/upload">
            <Button>
              <Upload className="h-4 w-4 mr-2" />
              Upload Document
            </Button>
          </Link>
        }
      />

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Total Documents</div>
            <div className="text-2xl font-bold mt-1">{stats.total}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Verified</div>
            <div className="text-2xl font-bold mt-1 text-green-600">{stats.verified}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Pending</div>
            <div className="text-2xl font-bold mt-1 text-yellow-600">{stats.pending}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Rejected</div>
            <div className="text-2xl font-bold mt-1 text-red-600">{stats.rejected}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Expiring Soon</div>
            <div className="text-2xl font-bold mt-1 text-orange-600">{stats.expiring}</div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-2 flex-1 min-w-[200px]">
              <Search className="h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search by customer, document number..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="max-w-sm"
              />
            </div>
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-muted-foreground" />
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-40">
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="VERIFIED">Verified</SelectItem>
                  <SelectItem value="PENDING">Pending</SelectItem>
                  <SelectItem value="REJECTED">Rejected</SelectItem>
                  <SelectItem value="EXPIRING_SOON">Expiring Soon</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Select value={typeFilter} onValueChange={setTypeFilter}>
              <SelectTrigger className="w-44">
                <SelectValue placeholder="Document Type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                <SelectItem value="PAN_CARD">PAN Card</SelectItem>
                <SelectItem value="AADHAAR">Aadhaar</SelectItem>
                <SelectItem value="PASSPORT">Passport</SelectItem>
                <SelectItem value="VOTER_ID">Voter ID</SelectItem>
                <SelectItem value="DRIVING_LICENSE">Driving License</SelectItem>
                <SelectItem value="ADDRESS_PROOF">Address Proof</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Documents Table */}
      <Card>
        <CardHeader>
          <CardTitle>Documents</CardTitle>
          <CardDescription>
            Showing {filteredDocuments.length} of {documents.length} documents
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Customer</TableHead>
                <TableHead>Document Type</TableHead>
                <TableHead>Document Number</TableHead>
                <TableHead>File</TableHead>
                <TableHead>Uploaded</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Expiry</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredDocuments.map((doc) => (
                <TableRow key={doc.id}>
                  <TableCell>
                    <div>
                      <div className="font-medium">{doc.customerName}</div>
                      <div className="text-xs text-muted-foreground">{doc.customerId}</div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline">
                      {documentTypeLabels[doc.documentType] || doc.documentType}
                    </Badge>
                  </TableCell>
                  <TableCell className="font-mono text-sm">{doc.documentNumber}</TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      {getFileIcon(doc.fileName)}
                      <div>
                        <div className="text-sm">{doc.fileName}</div>
                        <div className="text-xs text-muted-foreground">{doc.fileSize}</div>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell className="text-sm">{doc.uploadedAt.split(' ')[0]}</TableCell>
                  <TableCell>{getStatusBadge(doc.verificationStatus)}</TableCell>
                  <TableCell className="text-sm">
                    {doc.expiryDate ? (
                      <span className={doc.verificationStatus === 'EXPIRING_SOON' ? 'text-orange-600' : ''}>
                        {doc.expiryDate}
                      </span>
                    ) : (
                      <span className="text-muted-foreground">N/A</span>
                    )}
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-1">
                      <Link to={`/admin/kyc/documents/${doc.id}/verify`}>
                        <Button variant="ghost" size="sm">
                          <Eye className="h-4 w-4" />
                        </Button>
                      </Link>
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
