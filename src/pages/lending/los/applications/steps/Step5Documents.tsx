import { Check, FileText } from 'lucide-react';
import { useEffect } from 'react';

import { EmptyState, ErrorState, SkeletonTable } from '@/components/common';
import { useWizard } from '@/components/lending/wizard/WizardContext';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';
import { useProductDocumentRequirements } from '@/hooks/lending/useProductDocuments';

interface Step5Props {
  applicationId?: string;
}

export default function Step5Documents({ applicationId }: Step5Props) {
  const { data, setValidation } = useWizard();
  const entityProduct = (data['entity-product'] || {}) as { productId?: string };
  const requirementsQuery = useProductDocumentRequirements(entityProduct.productId);
  const requirements = requirementsQuery.data ?? [];
  const mandatoryCount = requirements.filter((requirement) => requirement.isMandatory).length;
  const needsDraftBeforeSubmit = mandatoryCount > 0 && !applicationId;
  const documentsStepReady =
    Boolean(entityProduct.productId) &&
    !requirementsQuery.isLoading &&
    !requirementsQuery.isError &&
    !needsDraftBeforeSubmit;

  useEffect(() => {
    setValidation('documents', documentsStepReady);
  }, [documentsStepReady, setValidation]);

  if (requirementsQuery.isLoading) {
    return <SkeletonTable rows={5} columns={3} />;
  }

  if (requirementsQuery.isError) {
    return (
      <ErrorState
        title="Could not load product document requirements"
        error={requirementsQuery.error}
        onRetry={() => requirementsQuery.refetch()}
      />
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium">Document Requirements</h3>
        <p className="text-sm text-muted-foreground">
          Review the product-specific borrower documents required for this application.
        </p>
      </div>

      {needsDraftBeforeSubmit ? (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
          Save this application as a draft before submission. Mandatory product documents must be
          uploaded against the application record before SFC review can start.
        </div>
      ) : null}

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-muted-foreground">Configured Requirements</p>
            <p className="text-2xl font-bold">{requirements.length}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-muted-foreground">Mandatory Requirements</p>
            <p className="text-2xl font-bold">{mandatoryCount}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-muted-foreground">Capture Point</p>
            <p className="text-2xl font-bold">{applicationId ? 'Application' : 'Post Draft'}</p>
          </CardContent>
        </Card>
      </div>

      {requirements.length === 0 ? (
        <EmptyState
          title="No document requirements configured"
          subtitle="Configure product document requirements in the product setup checklist."
        />
      ) : (
        <Card>
          <CardContent className="space-y-3 pt-6">
            {requirements.map((requirement) => (
              <div
                key={requirement.id}
                className="flex items-center justify-between rounded-lg border p-3"
              >
                <div className="flex items-center gap-3">
                  <div className="rounded bg-gray-100 p-2">
                    <FileText className="h-4 w-4 text-gray-500" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{requirement.name}</span>
                      {requirement.isMandatory ? (
                        <Badge variant="outline" className="text-xs">
                          Required
                        </Badge>
                      ) : null}
                      {requirement.isMandatoryForDisbursement ? (
                        <Badge variant="secondary" className="text-xs">
                          Disbursement gate
                        </Badge>
                      ) : null}
                    </div>
                    <p className="text-sm text-muted-foreground">
                      {requirement.category} • {requirement.requiredAtStage} •{' '}
                      {requirement.minFileCount}-{requirement.maxFileCount} file(s)
                    </p>
                  </div>
                </div>
                <Check className="h-5 w-5 text-green-500" />
              </div>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
