/**
 * Vendor Compliance Documents
 */

import {
  Shield,
  Upload,
  Loader2,
  CheckCircle,
  AlertCircle,
  Clock,
  FileText,
  Trash2,
  Calendar,
  XCircle,
} from 'lucide-react';
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

import { DateDisplay } from '@/components/common/DateDisplay';
import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { useToast } from '@/hooks/use-toast';
import { vendorComplianceApi } from '@/services/vendorApi';
import type { ComplianceDocument, ComplianceSummary } from '@/types/vendor';

import { logger } from "@/lib/logger";
const DOCUMENT_TYPES = [
  { value: 'PAN_CARD', label: 'PAN Card' },
  { value: 'GST_CERTIFICATE', label: 'GST Certificate' },
  { value: 'MSME_CERTIFICATE', label: 'MSME Certificate' },
  { value: 'ISO_CERTIFICATE', label: 'ISO Certificate' },
  { value: 'TDS_CERTIFICATE', label: 'TDS Certificate' },
  { value: 'FORM_16A', label: 'Form 16A' },
  { value: 'INSURANCE_POLICY', label: 'Insurance Policy' },
  { value: 'FSSAI_LICENSE', label: 'FSSAI License' },
  { value: 'POLLUTION_CERT', label: 'Pollution Certificate' },
  { value: 'FACTORY_LICENSE', label: 'Factory License' },
  { value: 'DRUG_LICENSE', label: 'Drug License' },
  { value: 'CANCELLED_CHEQUE', label: 'Cancelled Cheque' },
  { value: 'OTHER', label: 'Other' },
];

export default function VendorComplianceList() {
  const { toast } = useToast();

  const [loading, setLoading] = useState(true);
  const [documents, setDocuments] = useState<ComplianceDocument[]>([]);
  const [summary, setSummary] = useState<ComplianceSummary | null>(null);
  const [expiringDocs, setExpiringDocs] = useState<ComplianceDocument[]>([]);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [docsRes, summaryRes, expiringRes] = await Promise.all([
        vendorComplianceApi.list(),
        vendorComplianceApi.getSummary(),
        vendorComplianceApi.getExpiring(30),
      ]);

      setDocuments(docsRes.data.items);
      setSummary(summaryRes.data);
      setExpiringDocs(expiringRes.data);
    } catch (error) {
      logger.error('Failed to fetch compliance data:', error);
      toast({
        variant: 'destructive',
        title: 'Error',
        description: 'Failed to load compliance documents',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this document?')) return;

    try {
      await vendorComplianceApi.delete(id);
      toast({ title: 'Document deleted' });
      fetchData();
    } catch (error) {
      toast({
        variant: 'destructive',
        title: 'Error',
        description: 'Failed to delete document',
      });
    }
  };

  const getVerificationBadge = (doc: ComplianceDocument) => {
    if (doc.verification_status === 'VERIFIED') {
      return <Badge className="bg-green-100 text-green-800"><CheckCircle className="h-3 w-3 mr-1" />Verified</Badge>;
    }
    if (doc.verification_status === 'REJECTED') {
      return <Badge className="bg-red-100 text-red-800"><XCircle className="h-3 w-3 mr-1" />Rejected</Badge>;
    }
    return <Badge className="bg-yellow-100 text-yellow-800"><Clock className="h-3 w-3 mr-1" />Pending</Badge>;
  };

  const completionPercent = summary
    ? Math.round((summary.verified / Math.max(summary.total, 1)) * 100)
    : 0;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Compliance Documents"
        subtitle="Manage your compliance and statutory documents"
        actions={
          <Link to="/vendor/compliance/upload">
            <Button className="bg-purple-600 hover:bg-purple-700">
              <Upload className="h-4 w-4 mr-2" />
              Upload Document
            </Button>
          </Link>
        }
      />

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <Card className="md:col-span-2">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <p className="text-sm text-gray-500">Compliance Status</p>
                <p className="text-2xl font-bold">{completionPercent}%</p>
              </div>
              <Shield className="h-10 w-10 text-purple-600" />
            </div>
            <Progress value={completionPercent} className="h-2" />
            <p className="text-xs text-gray-500 mt-2">
              {summary?.verified || 0} of {summary?.total || 0} documents verified
            </p>
          </CardContent>
        </Card>
        <Card className="bg-green-50 border-green-200">
          <CardContent className="pt-4">
            <div className="flex items-center space-x-2">
              <CheckCircle className="h-5 w-5 text-green-600" />
              <span className="text-sm font-medium text-green-800">Verified</span>
            </div>
            <p className="text-2xl font-bold text-green-900 mt-2">{summary?.verified || 0}</p>
          </CardContent>
        </Card>
        <Card className="bg-yellow-50 border-yellow-200">
          <CardContent className="pt-4">
            <div className="flex items-center space-x-2">
              <Clock className="h-5 w-5 text-yellow-600" />
              <span className="text-sm font-medium text-yellow-800">Pending</span>
            </div>
            <p className="text-2xl font-bold text-yellow-900 mt-2">{summary?.pending || 0}</p>
          </CardContent>
        </Card>
        <Card className="bg-red-50 border-red-200">
          <CardContent className="pt-4">
            <div className="flex items-center space-x-2">
              <AlertCircle className="h-5 w-5 text-red-600" />
              <span className="text-sm font-medium text-red-800">Expired</span>
            </div>
            <p className="text-2xl font-bold text-red-900 mt-2">{summary?.expired || 0}</p>
          </CardContent>
        </Card>
      </div>

      {/* Expiring Soon Alert */}
      {expiringDocs.length > 0 && (
        <Card className="border-orange-200 bg-orange-50">
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center text-orange-800">
              <AlertCircle className="h-5 w-5 mr-2" />
              Documents Expiring Soon
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {expiringDocs.map((doc) => (
                <div key={doc.id} className="flex items-center justify-between p-2 bg-white rounded">
                  <div>
                    <p className="font-medium">{doc.document_name}</p>
                    <p className="text-sm text-gray-500">
                      Expires on <DateDisplay date={doc.expiry_date!} />
                    </p>
                  </div>
                  <Badge variant="outline" className="text-orange-600 border-orange-300">
                    {doc.days_to_expiry} days left
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Documents List */}
      <Card>
        <CardHeader>
          <CardTitle>All Documents</CardTitle>
          <CardDescription>Your uploaded compliance documents</CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <Loader2 className="h-8 w-8 animate-spin text-purple-600" />
            </div>
          ) : documents.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-64 text-gray-500">
              <Shield className="h-12 w-12 text-gray-300 mb-2" />
              <p>No documents uploaded</p>
              <Link to="/vendor/compliance/upload">
                <Button variant="outline" className="mt-4">
                  Upload your first document
                </Button>
              </Link>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {documents.map((doc) => (
                <Card key={doc.id} className="hover:shadow-md transition-shadow">
                  <CardContent className="pt-4">
                    <div className="flex items-start justify-between">
                      <div className="flex items-center space-x-3">
                        <div className="h-10 w-10 rounded bg-purple-100 flex items-center justify-center">
                          <FileText className="h-5 w-5 text-purple-600" />
                        </div>
                        <div>
                          <p className="font-medium text-sm">{doc.document_name}</p>
                          <p className="text-xs text-gray-500">
                            {DOCUMENT_TYPES.find(t => t.value === doc.document_type)?.label || doc.document_type}
                          </p>
                        </div>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDelete(doc.id)}
                        className="text-red-500 hover:text-red-700"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                    <div className="mt-4 space-y-2">
                      {doc.document_number && (
                        <p className="text-xs text-gray-600">
                          Doc #: {doc.document_number}
                        </p>
                      )}
                      {doc.expiry_date && !doc.is_perpetual && (
                        <div className="flex items-center space-x-1 text-xs">
                          <Calendar className="h-3 w-3 text-gray-400" />
                          <span className={doc.is_expired ? 'text-red-600' : 'text-gray-600'}>
                            Expires: <DateDisplay date={doc.expiry_date} />
                          </span>
                        </div>
                      )}
                      {doc.is_perpetual && (
                        <p className="text-xs text-green-600">No Expiry</p>
                      )}
                    </div>
                    <div className="mt-3 flex items-center justify-between">
                      {getVerificationBadge(doc)}
                      {doc.is_expired && (
                        <Badge variant="destructive">Expired</Badge>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
