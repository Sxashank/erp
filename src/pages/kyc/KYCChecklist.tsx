import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
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
import {
  ClipboardCheck,
  Search,
  Filter,
  CheckCircle,
  XCircle,
  Clock,
  AlertTriangle,
  Eye,
  Upload,
  User,
  FileText,
} from 'lucide-react';

// Mock customer KYC status data
const customerKYCData = [
  {
    id: '1',
    customerId: 'CUST001',
    customerName: 'Rajesh Kumar',
    customerType: 'INDIVIDUAL',
    kycStatus: 'COMPLETE',
    completionPercent: 100,
    documents: {
      pan: { status: 'VERIFIED', doc: 'ABCDE1234F' },
      aadhaar: { status: 'VERIFIED', doc: '****-****-1234' },
      photo: { status: 'VERIFIED', doc: 'Uploaded' },
      signature: { status: 'VERIFIED', doc: 'Uploaded' },
      addressProof: { status: 'VERIFIED', doc: 'Electricity Bill' },
      bankStatement: { status: 'VERIFIED', doc: '6 months' },
    },
    ckycStatus: 'REGISTERED',
    ckycNumber: '12345678901234',
    lastUpdated: '2025-01-15',
  },
  {
    id: '2',
    customerId: 'CUST002',
    customerName: 'Priya Sharma',
    customerType: 'INDIVIDUAL',
    kycStatus: 'INCOMPLETE',
    completionPercent: 67,
    documents: {
      pan: { status: 'VERIFIED', doc: 'FGHIJ5678K' },
      aadhaar: { status: 'VERIFIED', doc: '****-****-5678' },
      photo: { status: 'VERIFIED', doc: 'Uploaded' },
      signature: { status: 'PENDING', doc: null },
      addressProof: { status: 'REJECTED', doc: 'Old document' },
      bankStatement: { status: 'PENDING', doc: null },
    },
    ckycStatus: 'PENDING',
    ckycNumber: null,
    lastUpdated: '2025-01-14',
  },
  {
    id: '3',
    customerId: 'CUST003',
    customerName: 'Amit Patel Enterprises',
    customerType: 'BUSINESS',
    kycStatus: 'IN_PROGRESS',
    completionPercent: 50,
    documents: {
      pan: { status: 'VERIFIED', doc: 'AABCA1234B' },
      gst: { status: 'VERIFIED', doc: '27AABCA1234B1ZA' },
      coi: { status: 'PENDING', doc: null },
      moa: { status: 'PENDING', doc: null },
      boardResolution: { status: 'PENDING', doc: null },
      authorizedSignatory: { status: 'VERIFIED', doc: 'Amit Patel' },
    },
    ckycStatus: 'NOT_REQUIRED',
    ckycNumber: null,
    lastUpdated: '2025-01-13',
  },
  {
    id: '4',
    customerId: 'CUST004',
    customerName: 'Sunita Devi',
    customerType: 'INDIVIDUAL',
    kycStatus: 'EXPIRED',
    completionPercent: 100,
    documents: {
      pan: { status: 'VERIFIED', doc: 'PQRST3456M' },
      aadhaar: { status: 'VERIFIED', doc: '****-****-9012' },
      photo: { status: 'EXPIRED', doc: 'Re-upload needed' },
      signature: { status: 'VERIFIED', doc: 'Uploaded' },
      addressProof: { status: 'EXPIRED', doc: 'Older than 1 year' },
      bankStatement: { status: 'VERIFIED', doc: '6 months' },
    },
    ckycStatus: 'REGISTERED',
    ckycNumber: '98765432109876',
    lastUpdated: '2024-01-10',
  },
  {
    id: '5',
    customerId: 'CUST005',
    customerName: 'Vikram Singh',
    customerType: 'INDIVIDUAL',
    kycStatus: 'PENDING_VERIFICATION',
    completionPercent: 85,
    documents: {
      pan: { status: 'VERIFIED', doc: 'UVWXY7890N' },
      aadhaar: { status: 'VERIFIED', doc: '****-****-3456' },
      photo: { status: 'PENDING', doc: 'Awaiting verification' },
      signature: { status: 'VERIFIED', doc: 'Uploaded' },
      addressProof: { status: 'PENDING', doc: 'Awaiting verification' },
      bankStatement: { status: 'VERIFIED', doc: '6 months' },
    },
    ckycStatus: 'IN_PROGRESS',
    ckycNumber: null,
    lastUpdated: '2025-01-15',
  },
];

// Individual KYC requirements
const individualRequirements = [
  { key: 'pan', label: 'PAN Card', mandatory: true },
  { key: 'aadhaar', label: 'Aadhaar', mandatory: true },
  { key: 'photo', label: 'Photograph', mandatory: true },
  { key: 'signature', label: 'Signature', mandatory: true },
  { key: 'addressProof', label: 'Address Proof', mandatory: true },
  { key: 'bankStatement', label: 'Bank Statement', mandatory: false },
];

// Business KYC requirements
const businessRequirements = [
  { key: 'pan', label: 'Business PAN', mandatory: true },
  { key: 'gst', label: 'GST Certificate', mandatory: true },
  { key: 'coi', label: 'Certificate of Incorporation', mandatory: true },
  { key: 'moa', label: 'MOA/AOA', mandatory: true },
  { key: 'boardResolution', label: 'Board Resolution', mandatory: true },
  { key: 'authorizedSignatory', label: 'Authorized Signatory KYC', mandatory: true },
];

export default function KYCChecklist() {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [typeFilter, setTypeFilter] = useState('all');
  const [selectedCustomer, setSelectedCustomer] = useState<typeof customerKYCData[0] | null>(null);

  const filteredCustomers = customerKYCData.filter(customer => {
    const matchesSearch =
      customer.customerName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      customer.customerId.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || customer.kycStatus === statusFilter;
    const matchesType = typeFilter === 'all' || customer.customerType === typeFilter;
    return matchesSearch && matchesStatus && matchesType;
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'COMPLETE':
        return <Badge variant="default" className="bg-green-100 text-green-800"><CheckCircle className="h-3 w-3 mr-1" />Complete</Badge>;
      case 'INCOMPLETE':
        return <Badge variant="destructive"><XCircle className="h-3 w-3 mr-1" />Incomplete</Badge>;
      case 'IN_PROGRESS':
        return <Badge variant="secondary"><Clock className="h-3 w-3 mr-1" />In Progress</Badge>;
      case 'PENDING_VERIFICATION':
        return <Badge variant="outline" className="bg-yellow-100 text-yellow-800"><Clock className="h-3 w-3 mr-1" />Pending Verification</Badge>;
      case 'EXPIRED':
        return <Badge variant="outline" className="bg-orange-100 text-orange-800"><AlertTriangle className="h-3 w-3 mr-1" />Expired</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const getDocStatusIcon = (status: string) => {
    switch (status) {
      case 'VERIFIED':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'PENDING':
        return <Clock className="h-4 w-4 text-yellow-500" />;
      case 'REJECTED':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'EXPIRED':
        return <AlertTriangle className="h-4 w-4 text-orange-500" />;
      default:
        return <Clock className="h-4 w-4 text-gray-400" />;
    }
  };

  const getCKYCBadge = (status: string) => {
    switch (status) {
      case 'REGISTERED':
        return <Badge variant="default" className="bg-green-100 text-green-800">CKYC Registered</Badge>;
      case 'PENDING':
        return <Badge variant="secondary">CKYC Pending</Badge>;
      case 'IN_PROGRESS':
        return <Badge variant="outline">CKYC In Progress</Badge>;
      case 'NOT_REQUIRED':
        return <Badge variant="outline" className="text-muted-foreground">N/A</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  // Statistics
  const stats = {
    total: customerKYCData.length,
    complete: customerKYCData.filter(c => c.kycStatus === 'COMPLETE').length,
    incomplete: customerKYCData.filter(c => c.kycStatus === 'INCOMPLETE').length,
    pendingVerification: customerKYCData.filter(c => c.kycStatus === 'PENDING_VERIFICATION').length,
    expired: customerKYCData.filter(c => c.kycStatus === 'EXPIRED').length,
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      <PageHeader
        title="KYC Checklist"
        subtitle="Track customer KYC document completion status"
      />

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Total Customers</div>
            <div className="text-2xl font-bold mt-1">{stats.total}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">KYC Complete</div>
            <div className="text-2xl font-bold mt-1 text-green-600">{stats.complete}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Incomplete</div>
            <div className="text-2xl font-bold mt-1 text-red-600">{stats.incomplete}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Pending Verification</div>
            <div className="text-2xl font-bold mt-1 text-yellow-600">{stats.pendingVerification}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Expired</div>
            <div className="text-2xl font-bold mt-1 text-orange-600">{stats.expired}</div>
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
                placeholder="Search by customer name or ID..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="max-w-sm"
              />
            </div>
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-muted-foreground" />
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-44">
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="COMPLETE">Complete</SelectItem>
                  <SelectItem value="INCOMPLETE">Incomplete</SelectItem>
                  <SelectItem value="IN_PROGRESS">In Progress</SelectItem>
                  <SelectItem value="PENDING_VERIFICATION">Pending Verification</SelectItem>
                  <SelectItem value="EXPIRED">Expired</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Select value={typeFilter} onValueChange={setTypeFilter}>
              <SelectTrigger className="w-36">
                <SelectValue placeholder="Type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                <SelectItem value="INDIVIDUAL">Individual</SelectItem>
                <SelectItem value="BUSINESS">Business</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Customer List */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Customer KYC Status</CardTitle>
            <CardDescription>
              Showing {filteredCustomers.length} customers
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Customer</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Completion</TableHead>
                  <TableHead>KYC Status</TableHead>
                  <TableHead>CKYC Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredCustomers.map((customer) => (
                  <TableRow
                    key={customer.id}
                    className={selectedCustomer?.id === customer.id ? 'bg-muted/50' : 'cursor-pointer hover:bg-muted/30'}
                    onClick={() => setSelectedCustomer(customer)}
                  >
                    <TableCell>
                      <div>
                        <div className="font-medium">{customer.customerName}</div>
                        <div className="text-xs text-muted-foreground">{customer.customerId}</div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">
                        {customer.customerType === 'INDIVIDUAL' ? 'Individual' : 'Business'}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="w-24">
                        <Progress value={customer.completionPercent} className="h-2" />
                        <p className="text-xs text-muted-foreground mt-1">{customer.completionPercent}%</p>
                      </div>
                    </TableCell>
                    <TableCell>{getStatusBadge(customer.kycStatus)}</TableCell>
                    <TableCell>{getCKYCBadge(customer.ckycStatus)}</TableCell>
                    <TableCell className="text-right">
                      <Button variant="ghost" size="sm" onClick={(e) => { e.stopPropagation(); setSelectedCustomer(customer); }}>
                        <Eye className="h-4 w-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        {/* Document Checklist Detail */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              Document Checklist
            </CardTitle>
            {selectedCustomer && (
              <CardDescription>
                {selectedCustomer.customerName} ({selectedCustomer.customerId})
              </CardDescription>
            )}
          </CardHeader>
          <CardContent>
            {selectedCustomer ? (
              <div className="space-y-4">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Completion</span>
                  <span className="font-medium">{selectedCustomer.completionPercent}%</span>
                </div>
                <Progress value={selectedCustomer.completionPercent} />

                <div className="space-y-3 mt-4">
                  {(selectedCustomer.customerType === 'INDIVIDUAL' ? individualRequirements : businessRequirements).map((req) => {
                    const doc = selectedCustomer.documents[req.key as keyof typeof selectedCustomer.documents];
                    return (
                      <div key={req.key} className="flex items-center justify-between p-2 border rounded-lg">
                        <div className="flex items-center gap-2">
                          {doc ? getDocStatusIcon(doc.status) : <Clock className="h-4 w-4 text-gray-400" />}
                          <div>
                            <p className="text-sm font-medium">{req.label}</p>
                            {doc?.doc && (
                              <p className="text-xs text-muted-foreground">{doc.doc}</p>
                            )}
                          </div>
                        </div>
                        {req.mandatory && (
                          <Badge variant="outline" className="text-xs">Required</Badge>
                        )}
                      </div>
                    );
                  })}
                </div>

                {selectedCustomer.ckycNumber && (
                  <div className="p-3 bg-green-50 rounded-lg mt-4">
                    <p className="text-sm font-medium text-green-800">CKYC Number</p>
                    <p className="font-mono text-green-700">{selectedCustomer.ckycNumber}</p>
                  </div>
                )}

                <div className="flex gap-2 mt-4">
                  <Link to={`/admin/kyc/documents?customer=${selectedCustomer.customerId}`} className="flex-1">
                    <Button variant="outline" className="w-full">
                      <Eye className="h-4 w-4 mr-2" />
                      View Documents
                    </Button>
                  </Link>
                  <Link to="/admin/kyc/documents/upload" className="flex-1">
                    <Button className="w-full">
                      <Upload className="h-4 w-4 mr-2" />
                      Upload
                    </Button>
                  </Link>
                </div>
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <User className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>Select a customer to view their KYC checklist</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
