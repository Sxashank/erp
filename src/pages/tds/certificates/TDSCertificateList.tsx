import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  FileText,
  Search,
  Download,
  CheckCircle,
  Clock,
  AlertTriangle,
  Eye,
  Calendar,
  Mail,
  Printer,
  Users,
  Filter,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import { PageHeader } from '@/components/common/PageHeader';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from '@/components/ui/dropdown-menu';
import { formatCurrency, formatDate } from '@/lib/utils';

// Types
type CertificateStatus = 'PENDING' | 'GENERATED' | 'DOWNLOADED' | 'EMAILED' | 'ERROR';
type CertificateType = 'FORM_16A' | 'FORM_16B' | 'FORM_16C';

interface TDSCertificate {
  id: string;
  certificate_type: CertificateType;
  certificate_number: string;
  deductee_name: string;
  deductee_pan: string;
  deductee_email?: string;
  financial_year: string;
  quarter: string;
  amount_paid: number;
  tds_deducted: number;
  tds_deposited: number;
  section_code: string;
  challan_numbers: string[];
  status: CertificateStatus;
  generated_at?: string;
  downloaded_at?: string;
  emailed_at?: string;
  file_path?: string;
}

// Mock data
const certificateSummary = {
  total_certificates: 156,
  pending_generation: 12,
  generated_this_quarter: 45,
  emailed: 120,
};

const certificates: TDSCertificate[] = [
  {
    id: '1',
    certificate_type: 'FORM_16A',
    certificate_number: 'F16A/2024-25/Q3/001',
    deductee_name: 'John Doe Consultants',
    deductee_pan: 'ABCPD1234F',
    deductee_email: 'john.doe@example.com',
    financial_year: '2024-25',
    quarter: 'Q3',
    amount_paid: 500000,
    tds_deducted: 50000,
    tds_deposited: 50000,
    section_code: '194J',
    challan_numbers: ['23456', '23457'],
    status: 'EMAILED',
    generated_at: '2024-12-20',
    emailed_at: '2024-12-20',
    file_path: '/certificates/f16a_2024-25_q3_001.pdf',
  },
  {
    id: '2',
    certificate_type: 'FORM_16A',
    certificate_number: 'F16A/2024-25/Q3/002',
    deductee_name: 'ABC Technologies Pvt Ltd',
    deductee_pan: 'AABCA1234B',
    deductee_email: 'finance@abctech.com',
    financial_year: '2024-25',
    quarter: 'Q3',
    amount_paid: 1500000,
    tds_deducted: 150000,
    tds_deposited: 150000,
    section_code: '194C',
    challan_numbers: ['23456'],
    status: 'GENERATED',
    generated_at: '2024-12-20',
    file_path: '/certificates/f16a_2024-25_q3_002.pdf',
  },
  {
    id: '3',
    certificate_type: 'FORM_16A',
    certificate_number: '',
    deductee_name: 'XYZ Services',
    deductee_pan: 'AABCX5678G',
    financial_year: '2024-25',
    quarter: 'Q3',
    amount_paid: 250000,
    tds_deducted: 25000,
    tds_deposited: 25000,
    section_code: '194A',
    challan_numbers: ['23458'],
    status: 'PENDING',
  },
  {
    id: '4',
    certificate_type: 'FORM_16A',
    certificate_number: 'F16A/2024-25/Q3/003',
    deductee_name: 'Professional Associates',
    deductee_pan: 'AABCP9012H',
    deductee_email: 'info@professionalassoc.com',
    financial_year: '2024-25',
    quarter: 'Q3',
    amount_paid: 800000,
    tds_deducted: 80000,
    tds_deposited: 80000,
    section_code: '194J',
    challan_numbers: ['23457'],
    status: 'DOWNLOADED',
    generated_at: '2024-12-18',
    downloaded_at: '2024-12-19',
    file_path: '/certificates/f16a_2024-25_q3_003.pdf',
  },
];

const getStatusBadge = (status: CertificateStatus) => {
  const statusConfig: Record<CertificateStatus, { variant: 'default' | 'secondary' | 'destructive' | 'outline'; icon: React.ReactNode; label: string }> = {
    PENDING: { variant: 'secondary', icon: <Clock className="h-3 w-3 mr-1" />, label: 'Pending' },
    GENERATED: { variant: 'outline', icon: <FileText className="h-3 w-3 mr-1" />, label: 'Generated' },
    DOWNLOADED: { variant: 'default', icon: <Download className="h-3 w-3 mr-1" />, label: 'Downloaded' },
    EMAILED: { variant: 'default', icon: <Mail className="h-3 w-3 mr-1" />, label: 'Emailed' },
    ERROR: { variant: 'destructive', icon: <AlertTriangle className="h-3 w-3 mr-1" />, label: 'Error' },
  };

  const config = statusConfig[status];
  return (
    <Badge variant={config.variant} className="flex items-center w-fit">
      {config.icon}
      {config.label}
    </Badge>
  );
};

const getCertificateTypeLabel = (type: CertificateType) => {
  const labels: Record<CertificateType, string> = {
    FORM_16A: 'Form 16A',
    FORM_16B: 'Form 16B',
    FORM_16C: 'Form 16C',
  };
  return labels[type];
};

export default function TDSCertificateList() {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [quarterFilter, setQuarterFilter] = useState('all');
  const [selectedIds, setSelectedIds] = useState<string[]>([]);

  const filteredCertificates = certificates.filter((c) => {
    const matchesSearch =
      c.deductee_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.deductee_pan.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.certificate_number.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || c.status === statusFilter;
    const matchesQuarter = quarterFilter === 'all' || c.quarter === quarterFilter;
    return matchesSearch && matchesStatus && matchesQuarter;
  });

  const toggleSelect = (id: string) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]
    );
  };

  const toggleSelectAll = () => {
    if (selectedIds.length === filteredCertificates.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(filteredCertificates.map((c) => c.id));
    }
  };

  const pendingCerts = filteredCertificates.filter((c) => c.status === 'PENDING');
  const generatedCerts = filteredCertificates.filter(
    (c) => c.status !== 'PENDING' && c.status !== 'ERROR'
  );

  return (
    <div className="space-y-6">
      <PageHeader
        title="TDS Certificates"
        subtitle="Generate and manage Form 16A/16B certificates"
        actions={
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => navigate('/tds/certificates/generate')}>
              <FileText className="h-4 w-4 mr-2" />
              Generate Certificates
            </Button>
            {selectedIds.length > 0 && (
              <>
                <Button variant="outline">
                  <Download className="h-4 w-4 mr-2" />
                  Download ({selectedIds.length})
                </Button>
                <Button variant="outline">
                  <Mail className="h-4 w-4 mr-2" />
                  Email ({selectedIds.length})
                </Button>
              </>
            )}
          </div>
        }
      />

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total Certificates
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{certificateSummary.total_certificates}</div>
            <p className="text-xs text-muted-foreground">This financial year</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Pending Generation
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-yellow-600">
              {certificateSummary.pending_generation}
            </div>
            <p className="text-xs text-muted-foreground">Awaiting generation</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Generated This Quarter
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-600">
              {certificateSummary.generated_this_quarter}
            </div>
            <p className="text-xs text-muted-foreground">Q3 2024-25</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Emailed</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{certificateSummary.emailed}</div>
            <p className="text-xs text-muted-foreground">Sent to deductees</p>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex gap-4 flex-wrap">
            <div className="relative flex-1 min-w-[200px]">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search by name, PAN, certificate number..."
                className="pl-10"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            <Select value={quarterFilter} onValueChange={setQuarterFilter}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Quarter" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Quarters</SelectItem>
                <SelectItem value="Q1">Q1 (Apr-Jun)</SelectItem>
                <SelectItem value="Q2">Q2 (Jul-Sep)</SelectItem>
                <SelectItem value="Q3">Q3 (Oct-Dec)</SelectItem>
                <SelectItem value="Q4">Q4 (Jan-Mar)</SelectItem>
              </SelectContent>
            </Select>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="PENDING">Pending</SelectItem>
                <SelectItem value="GENERATED">Generated</SelectItem>
                <SelectItem value="DOWNLOADED">Downloaded</SelectItem>
                <SelectItem value="EMAILED">Emailed</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Quick Actions for Pending */}
      {pendingCerts.length > 0 && (
        <Card className="border-yellow-200 bg-yellow-50">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <AlertTriangle className="h-5 w-5 text-yellow-600" />
                <div>
                  <div className="font-medium">
                    {pendingCerts.length} certificates pending generation
                  </div>
                  <div className="text-sm text-muted-foreground">
                    Generate certificates for all pending deductees
                  </div>
                </div>
              </div>
              <Button>
                <FileText className="h-4 w-4 mr-2" />
                Generate All Pending
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Certificates Table */}
      <Card>
        <CardHeader>
          <CardTitle>TDS Certificates</CardTitle>
          <CardDescription>{filteredCertificates.length} certificates found</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-12">
                  <Checkbox
                    checked={selectedIds.length === filteredCertificates.length}
                    onCheckedChange={toggleSelectAll}
                  />
                </TableHead>
                <TableHead>Deductee</TableHead>
                <TableHead>Certificate</TableHead>
                <TableHead>Period</TableHead>
                <TableHead className="text-right">Amount Paid</TableHead>
                <TableHead className="text-right">TDS</TableHead>
                <TableHead>Status</TableHead>
                <TableHead></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredCertificates.map((cert) => (
                <TableRow key={cert.id}>
                  <TableCell>
                    <Checkbox
                      checked={selectedIds.includes(cert.id)}
                      onCheckedChange={() => toggleSelect(cert.id)}
                    />
                  </TableCell>
                  <TableCell>
                    <div className="font-medium">{cert.deductee_name}</div>
                    <div className="text-sm text-muted-foreground">PAN: {cert.deductee_pan}</div>
                    {cert.deductee_email && (
                      <div className="text-xs text-muted-foreground">{cert.deductee_email}</div>
                    )}
                  </TableCell>
                  <TableCell>
                    <div className="font-medium">
                      {getCertificateTypeLabel(cert.certificate_type)}
                    </div>
                    {cert.certificate_number ? (
                      <div className="text-sm text-muted-foreground">{cert.certificate_number}</div>
                    ) : (
                      <div className="text-sm text-yellow-600">Not generated</div>
                    )}
                    <Badge variant="outline" className="mt-1">
                      {cert.section_code}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div className="font-medium">{cert.financial_year}</div>
                    <div className="text-sm text-muted-foreground">{cert.quarter}</div>
                  </TableCell>
                  <TableCell className="text-right font-medium">
                    {formatCurrency(cert.amount_paid)}
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="font-medium text-green-600">
                      {formatCurrency(cert.tds_deducted)}
                    </div>
                    {cert.tds_deposited !== cert.tds_deducted && (
                      <div className="text-xs text-yellow-600">
                        Deposited: {formatCurrency(cert.tds_deposited)}
                      </div>
                    )}
                  </TableCell>
                  <TableCell>{getStatusBadge(cert.status)}</TableCell>
                  <TableCell>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="sm">
                          ...
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={() => navigate(`/tds/certificates/${cert.id}`)}>
                          <Eye className="h-4 w-4 mr-2" />
                          View Details
                        </DropdownMenuItem>
                        {cert.status === 'PENDING' && (
                          <DropdownMenuItem>
                            <FileText className="h-4 w-4 mr-2" />
                            Generate Certificate
                          </DropdownMenuItem>
                        )}
                        {cert.file_path && (
                          <>
                            <DropdownMenuItem>
                              <Download className="h-4 w-4 mr-2" />
                              Download PDF
                            </DropdownMenuItem>
                            <DropdownMenuItem>
                              <Printer className="h-4 w-4 mr-2" />
                              Print
                            </DropdownMenuItem>
                          </>
                        )}
                        {cert.deductee_email && cert.file_path && (
                          <DropdownMenuItem>
                            <Mail className="h-4 w-4 mr-2" />
                            Email to Deductee
                          </DropdownMenuItem>
                        )}
                      </DropdownMenuContent>
                    </DropdownMenu>
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
