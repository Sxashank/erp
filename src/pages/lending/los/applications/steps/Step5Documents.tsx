import { useState, useEffect } from 'react';
import { Upload, FileText, Check, X, Eye } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useWizard } from '@/components/lending/wizard/WizardContext';

interface DocumentItem {
  id: string;
  name: string;
  category: string;
  mandatory: boolean;
  uploaded: boolean;
  fileName?: string;
  uploadDate?: string;
}

interface Step5Props {
  applicationId?: string;
}

// Mock document checklist
const mockChecklist: DocumentItem[] = [
  { id: '1', name: 'Board Resolution', category: 'CORPORATE', mandatory: true, uploaded: true, fileName: 'board_resolution.pdf', uploadDate: '2025-01-10' },
  { id: '2', name: 'Audited Financials (3 Years)', category: 'FINANCIAL', mandatory: true, uploaded: true, fileName: 'financials_2022_2024.pdf', uploadDate: '2025-01-10' },
  { id: '3', name: 'Bank Statements (12 Months)', category: 'FINANCIAL', mandatory: true, uploaded: false },
  { id: '4', name: 'GST Returns', category: 'TAX', mandatory: true, uploaded: false },
  { id: '5', name: 'ITR (3 Years)', category: 'TAX', mandatory: true, uploaded: true, fileName: 'itr_2022_2024.pdf', uploadDate: '2025-01-08' },
  { id: '6', name: 'Property Documents', category: 'SECURITY', mandatory: false, uploaded: false },
  { id: '7', name: 'Title Search Report', category: 'SECURITY', mandatory: false, uploaded: false },
  { id: '8', name: 'PAN Card', category: 'KYC', mandatory: true, uploaded: true, fileName: 'pan_card.pdf', uploadDate: '2025-01-05' },
  { id: '9', name: 'Address Proof', category: 'KYC', mandatory: true, uploaded: true, fileName: 'address_proof.pdf', uploadDate: '2025-01-05' },
  { id: '10', name: 'Project Report', category: 'PROJECT', mandatory: false, uploaded: false },
];

export default function Step5Documents({ applicationId }: Step5Props) {
  const { setValidation } = useWizard();
  const [documents, setDocuments] = useState<DocumentItem[]>(mockChecklist);

  useEffect(() => {
    // Check if all mandatory documents are uploaded
    const allMandatoryUploaded = documents
      .filter((d) => d.mandatory)
      .every((d) => d.uploaded);
    setValidation('documents', allMandatoryUploaded);
  }, [documents, setValidation]);

  const handleUpload = (docId: string) => {
    // Simulate file upload
    setDocuments(
      documents.map((d) =>
        d.id === docId
          ? {
              ...d,
              uploaded: true,
              fileName: `${d.name.toLowerCase().replace(/\s+/g, '_')}.pdf`,
              uploadDate: new Date().toISOString().split('T')[0],
            }
          : d
      )
    );
  };

  const handleRemove = (docId: string) => {
    setDocuments(
      documents.map((d) =>
        d.id === docId
          ? { ...d, uploaded: false, fileName: undefined, uploadDate: undefined }
          : d
      )
    );
  };

  const uploadedCount = documents.filter((d) => d.uploaded).length;
  const mandatoryCount = documents.filter((d) => d.mandatory).length;
  const mandatoryUploadedCount = documents.filter((d) => d.mandatory && d.uploaded).length;

  const groupedDocs = documents.reduce((acc, doc) => {
    if (!acc[doc.category]) {
      acc[doc.category] = [];
    }
    acc[doc.category].push(doc);
    return acc;
  }, {} as Record<string, DocumentItem[]>);

  const categoryLabels: Record<string, string> = {
    CORPORATE: 'Corporate Documents',
    FINANCIAL: 'Financial Documents',
    TAX: 'Tax Documents',
    SECURITY: 'Security Documents',
    KYC: 'KYC Documents',
    PROJECT: 'Project Documents',
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium">Document Upload</h3>
        <p className="text-sm text-muted-foreground">
          Upload required documents for the loan application
        </p>
      </div>

      {/* Progress Summary */}
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-muted-foreground">Total Documents</p>
            <p className="text-2xl font-bold">
              {uploadedCount} / {documents.length}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-muted-foreground">Mandatory Documents</p>
            <p className={`text-2xl font-bold ${mandatoryUploadedCount === mandatoryCount ? 'text-green-600' : 'text-amber-600'}`}>
              {mandatoryUploadedCount} / {mandatoryCount}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-muted-foreground">Completion Status</p>
            <p className={`text-2xl font-bold ${mandatoryUploadedCount === mandatoryCount ? 'text-green-600' : 'text-amber-600'}`}>
              {mandatoryUploadedCount === mandatoryCount ? 'Complete' : 'Pending'}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Documents by Category */}
      {Object.entries(groupedDocs).map(([category, docs]) => (
        <Card key={category}>
          <CardContent className="pt-6">
            <h4 className="font-medium mb-4">{categoryLabels[category] || category}</h4>
            <div className="space-y-3">
              {docs.map((doc) => (
                <div
                  key={doc.id}
                  className="flex items-center justify-between p-3 rounded-lg border"
                >
                  <div className="flex items-center gap-3">
                    <div
                      className={`p-2 rounded ${
                        doc.uploaded ? 'bg-green-100' : 'bg-gray-100'
                      }`}
                    >
                      <FileText
                        className={`h-4 w-4 ${
                          doc.uploaded ? 'text-green-600' : 'text-gray-400'
                        }`}
                      />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{doc.name}</span>
                        {doc.mandatory && (
                          <Badge variant="outline" className="text-xs">
                            Required
                          </Badge>
                        )}
                      </div>
                      {doc.uploaded && doc.fileName && (
                        <p className="text-sm text-muted-foreground">
                          {doc.fileName} • Uploaded on {doc.uploadDate}
                        </p>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {doc.uploaded ? (
                      <>
                        <Button variant="ghost" size="sm">
                          <Eye className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleRemove(doc.id)}
                        >
                          <X className="h-4 w-4 text-red-500" />
                        </Button>
                        <Check className="h-5 w-5 text-green-500" />
                      </>
                    ) : (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleUpload(doc.id)}
                      >
                        <Upload className="mr-2 h-4 w-4" />
                        Upload
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
