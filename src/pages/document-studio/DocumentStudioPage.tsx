import {
  ArrowLeft,
  Eye,
  FileText,
  FolderTree,
  Package,
  Plus,
  Send,
  Stamp,
  Upload,
} from 'lucide-react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { useMemo, useState } from 'react';

import { DataTable, ErrorState, PageHeader } from '@/components/common';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
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
import {
  useCreateDocumentPackage,
  useCreateDocumentTemplate,
  useCreateDocumentTemplateVersion,
  useDmsFilingRules,
  useDocumentPackages,
  useDocumentTemplate,
  useDocumentTemplates,
  useDocumentVariables,
  usePreviewDocument,
  useTransitionDocumentTemplateVersion,
} from '@/hooks/useDocumentStudio';
import { useToast } from '@/hooks/use-toast';
import { showErrorToast } from '@/lib/errorToast';
import type {
  DocumentModule,
  DocumentPackage,
  DocumentTemplate,
  DocumentTemplateVersion,
  FilingRule,
} from '@/services/documentStudioApi';

const MODULES: DocumentModule[] = [
  'LENDING',
  'TREASURY',
  'HRIS',
  'PAYROLL',
  'LEGAL',
  'FINANCE',
  'AP_AR',
  'VENDOR_PORTAL',
  'BORROWER_PORTAL',
  'ESS',
];

const DEFAULT_BODY =
  '<h2>Sanction Letter</h2><p>Dear {{ entity.legalName }},</p><p>This document is generated for {{ sanction.sanctionNumber }}.</p><p>Regards,<br/>Authorised Signatory</p>';

function statusClass(status: string): string {
  if (status === 'PUBLISHED') return 'border-emerald-200 bg-emerald-50 text-emerald-700';
  if (status === 'APPROVED') return 'border-blue-200 bg-blue-50 text-blue-700';
  if (status === 'IN_REVIEW') return 'border-amber-200 bg-amber-50 text-amber-700';
  if (status === 'FINALIZED') return 'border-emerald-200 bg-emerald-50 text-emerald-700';
  if (status === 'RETIRED') return 'border-slate-200 bg-slate-50 text-slate-600';
  return 'border-slate-200 bg-white text-slate-700';
}

function latestVersion(template?: DocumentTemplate): DocumentTemplateVersion | undefined {
  return [...(template?.versions ?? [])].sort((a, b) => b.versionNumber - a.versionNumber)[0];
}

function templateSrcDoc(renderedHtml?: string): string {
  return `<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <style>
      body {
        margin: 0;
        padding: 32px;
        color: #111827;
        font: 14px/1.65 Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      }
      h1, h2, h3 { margin: 0 0 16px; color: #0f172a; line-height: 1.25; }
      p { margin: 0 0 14px; }
      table { width: 100%; border-collapse: collapse; margin: 16px 0; }
      td, th { border: 1px solid #d1d5db; padding: 8px; text-align: left; }
      .muted { color: #64748b; }
    </style>
  </head>
  <body>${renderedHtml || '<p class="muted">Render a sample to preview the document.</p>'}</body>
</html>`;
}

function DocumentStudioActions(): JSX.Element {
  return (
    <div className="flex flex-wrap gap-2">
      <Button asChild variant="outline">
        <Link to="/admin/dms/document-studio/filing-rules">
          <FolderTree className="mr-2 h-4 w-4" />
          Filing Rules
        </Link>
      </Button>
      <Button asChild variant="outline">
        <Link to="/admin/dms/document-studio/packages">
          <Package className="mr-2 h-4 w-4" />
          Packages
        </Link>
      </Button>
      <Button asChild>
        <Link to="/admin/dms/document-studio/templates/new">
          <Plus className="mr-2 h-4 w-4" />
          New Template
        </Link>
      </Button>
    </div>
  );
}

export default function DocumentStudioPage(): JSX.Element {
  const [selectedModule, setSelectedModule] = useState<DocumentModule | 'ALL'>('ALL');
  const templatesQuery = useDocumentTemplates(
    selectedModule === 'ALL' ? undefined : { module: selectedModule },
  );
  const rows = templatesQuery.data?.items ?? [];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Document Studio"
        breadcrumbs={[{ label: 'DMS', to: '/admin/dms' }, { label: 'Document Studio' }]}
        actions={<DocumentStudioActions />}
      />

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <FileText className="h-4 w-4" />
            Template Catalog
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="max-w-xs">
            <Select
              value={selectedModule}
              onValueChange={(value) => setSelectedModule(value as DocumentModule | 'ALL')}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="ALL">All modules</SelectItem>
                {MODULES.map((module) => (
                  <SelectItem key={module} value={module}>
                    {module}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <DataTable
            data={rows}
            isLoading={templatesQuery.isLoading}
            error={templatesQuery.error}
            onRetry={() => templatesQuery.refetch()}
            getRowId={(row) => row.id}
            dense
            emptyTitle="No templates"
            emptySubtitle="Create a template shell to start authoring."
            columns={[
              {
                key: 'name',
                header: 'Template',
                render: (row) => (
                  <div>
                    <Link
                      to={`/admin/dms/document-studio/templates/${row.id}`}
                      className="font-medium text-primary hover:underline"
                    >
                      {row.name}
                    </Link>
                    <div className="text-xs text-muted-foreground">{row.code}</div>
                  </div>
                ),
              },
              { key: 'module', header: 'Module' },
              { key: 'documentType', header: 'Type' },
              {
                key: 'versions',
                header: 'Latest',
                render: (row) => {
                  const latest = latestVersion(row);
                  return latest ? (
                    <Badge className={statusClass(latest.status)}>
                      v{latest.versionNumber} · {latest.status}
                    </Badge>
                  ) : (
                    'No version'
                  );
                },
              },
            ]}
          />
        </CardContent>
      </Card>
    </div>
  );
}

export function DocumentTemplateCreatePage(): JSX.Element {
  const { toast } = useToast();
  const navigate = useNavigate();
  const createTemplate = useCreateDocumentTemplate();
  const [module, setModule] = useState<DocumentModule>('LENDING');
  const [documentType, setDocumentType] = useState('SANCTION_LETTER');
  const [code, setCode] = useState(() => `SANCTION_LETTER_CUSTOM_${Date.now()}`);
  const [name, setName] = useState('Custom Sanction Letter');

  return (
    <div className="space-y-6">
      <PageHeader
        title="New Template"
        breadcrumbs={[
          { label: 'Document Studio', to: '/admin/dms/document-studio' },
          { label: 'New Template' },
        ]}
      />
      <Card className="max-w-3xl">
        <CardContent className="grid gap-4 pt-6">
          <div className="grid gap-2">
            <Label>Module</Label>
            <Select value={module} onValueChange={(value) => setModule(value as DocumentModule)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {MODULES.map((item) => (
                  <SelectItem key={item} value={item}>
                    {item}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="grid gap-2">
            <Label>Document type</Label>
            <Input value={documentType} onChange={(event) => setDocumentType(event.target.value)} />
          </div>
          <div className="grid gap-2">
            <Label>Code</Label>
            <Input value={code} onChange={(event) => setCode(event.target.value)} />
          </div>
          <div className="grid gap-2">
            <Label>Name</Label>
            <Input value={name} onChange={(event) => setName(event.target.value)} />
          </div>
          <div className="flex justify-end gap-2">
            <Button asChild variant="outline">
              <Link to="/admin/dms/document-studio">Cancel</Link>
            </Button>
            <Button
              disabled={createTemplate.isPending}
              onClick={() =>
                createTemplate.mutate(
                  {
                    module,
                    documentType,
                    code,
                    name,
                    locale: 'en',
                    channel: 'PDF',
                    priority: 100,
                    selectionRules: {},
                  },
                  {
                    onSuccess: (template) => {
                      toast({ title: 'Template created' });
                      navigate(`/admin/dms/document-studio/templates/${template.id}/versions/new`);
                    },
                    onError: (error) => showErrorToast(error, toast),
                  },
                )
              }
            >
              Create
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export function DocumentTemplateDetailPage(): JSX.Element {
  const { templateId } = useParams();
  const { toast } = useToast();
  const templateQuery = useDocumentTemplate(templateId);
  const transition = useTransitionDocumentTemplateVersion(templateId);
  const preview = usePreviewDocument();
  const template = templateQuery.data;
  const selectedVersion = latestVersion(template);
  const variables = useDocumentVariables(template?.module ?? 'LENDING', template?.documentType);

  if (templateQuery.error) {
    return <ErrorState error={templateQuery.error} onRetry={() => templateQuery.refetch()} />;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={template?.name ?? 'Template'}
        breadcrumbs={[
          { label: 'Document Studio', to: '/admin/dms/document-studio' },
          { label: template?.name ?? 'Template' },
        ]}
        actions={
          <Button asChild>
            <Link to={`/admin/dms/document-studio/templates/${templateId}/versions/new`}>
              <Upload className="mr-2 h-4 w-4" />
              Add Version
            </Link>
          </Button>
        }
      />

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_420px]">
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Versions</CardTitle>
            </CardHeader>
            <CardContent>
              <DataTable
                data={template?.versions ?? []}
                isLoading={templateQuery.isLoading}
                getRowId={(row) => row.id}
                dense
                emptyTitle="No versions"
                emptySubtitle="Add a version before review and publish."
                columns={[
                  {
                    key: 'versionNumber',
                    header: 'Version',
                    render: (row) => `v${row.versionNumber}`,
                  },
                  {
                    key: 'status',
                    header: 'Status',
                    render: (row) => (
                      <Badge className={statusClass(row.status)}>{row.status}</Badge>
                    ),
                  },
                  { key: 'format', header: 'Format' },
                  {
                    key: 'actions',
                    header: 'Actions',
                    render: (row) => (
                      <div className="flex flex-wrap gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          disabled={transition.isPending || row.status !== 'DRAFT'}
                          onClick={() =>
                            transition.mutate(
                              { versionId: row.id, action: 'submit-review' },
                              {
                                onSuccess: () => toast({ title: 'Submitted for review' }),
                                onError: (error) => showErrorToast(error, toast),
                              },
                            )
                          }
                        >
                          <Send className="mr-2 h-3.5 w-3.5" />
                          Review
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          disabled={transition.isPending || row.status === 'PUBLISHED'}
                          onClick={() =>
                            transition.mutate(
                              { versionId: row.id, action: 'approve' },
                              {
                                onSuccess: () => toast({ title: 'Version approved' }),
                                onError: (error) => showErrorToast(error, toast),
                              },
                            )
                          }
                        >
                          <Stamp className="mr-2 h-3.5 w-3.5" />
                          Approve
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          disabled={transition.isPending || row.status !== 'APPROVED'}
                          onClick={() =>
                            transition.mutate(
                              { versionId: row.id, action: 'publish' },
                              {
                                onSuccess: () => toast({ title: 'Version published' }),
                                onError: (error) => showErrorToast(error, toast),
                              },
                            )
                          }
                        >
                          Publish
                        </Button>
                      </div>
                    ),
                  },
                ]}
              />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <Eye className="h-4 w-4" />
                Preview
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <Button
                variant="outline"
                disabled={!selectedVersion || preview.isPending}
                onClick={() =>
                  preview.mutate(
                    {
                      templateVersionId: selectedVersion?.id,
                      context: {
                        organization: { name: 'SMFC Ltd', registeredAddress: 'Mumbai' },
                        entity: { entityCode: 'ENT-001', legalName: 'Example Borrower Pvt Ltd' },
                        sanction: {
                          sanctionNumber: 'SAN/2026/0001',
                          sanctionedAmount: 12500000,
                          validityDate: '2026-06-30',
                        },
                        loanAccount: { accountNumber: 'LN000123', interestRate: 12.5 },
                      },
                    },
                    { onError: (error) => showErrorToast(error, toast) },
                  )
                }
              >
                Render sample
              </Button>
              <div className="overflow-hidden rounded-md border bg-slate-100 p-4">
                <iframe
                  title="Document preview"
                  sandbox="allow-same-origin"
                  srcDoc={templateSrcDoc(preview.data?.renderedHtml)}
                  className="h-[560px] w-full rounded-sm border bg-white shadow-sm"
                />
              </div>
              {preview.data?.missingVariables?.length ? (
                <p className="text-xs text-amber-700">
                  Missing: {preview.data.missingVariables.join(', ')}
                </p>
              ) : null}
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Variables</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {(variables.data?.items ?? []).map((item) => (
              <div key={item.key} className="rounded-md border p-2">
                <div className="font-mono text-xs">{`{{ ${item.key}${
                  item.formatter ? ` | ${item.formatter}` : ''
                } }}`}</div>
                <div className="text-xs text-muted-foreground">{item.description}</div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export function DocumentTemplateVersionCreatePage(): JSX.Element {
  const { templateId } = useParams();
  const navigate = useNavigate();
  const { toast } = useToast();
  const templateQuery = useDocumentTemplate(templateId);
  const createVersion = useCreateDocumentTemplateVersion(templateId ?? '');
  const [body, setBody] = useState(DEFAULT_BODY);
  const [header, setHeader] = useState('<b>{{ organization.name }}</b>');
  const [footer, setFooter] = useState('Authorised Signatory');
  const [requiredVariables, setRequiredVariables] = useState('organization.name,entity.legalName');

  return (
    <div className="space-y-6">
      <PageHeader
        title="Author Version"
        breadcrumbs={[
          { label: 'Document Studio', to: '/admin/dms/document-studio' },
          {
            label: templateQuery.data?.name ?? 'Template',
            to: `/admin/dms/document-studio/templates/${templateId}`,
          },
          { label: 'New Version' },
        ]}
      />
      <Card>
        <CardContent className="grid gap-4 pt-6">
          <div className="grid gap-2">
            <Label>Header</Label>
            <Input value={header} onChange={(event) => setHeader(event.target.value)} />
          </div>
          <div className="grid gap-2">
            <Label>Body</Label>
            <Textarea
              value={body}
              onChange={(event) => setBody(event.target.value)}
              className="min-h-[420px] font-mono text-sm"
            />
          </div>
          <div className="grid gap-2">
            <Label>Footer</Label>
            <Input value={footer} onChange={(event) => setFooter(event.target.value)} />
          </div>
          <div className="grid gap-2">
            <Label>Required variables</Label>
            <Input
              value={requiredVariables}
              onChange={(event) => setRequiredVariables(event.target.value)}
            />
          </div>
          <div className="flex justify-end gap-2">
            <Button asChild variant="outline">
              <Link to={`/admin/dms/document-studio/templates/${templateId}`}>Cancel</Link>
            </Button>
            <Button
              disabled={createVersion.isPending || !templateId}
              onClick={() =>
                createVersion.mutate(
                  {
                    format: 'HTML',
                    body,
                    header,
                    footer,
                    requiredVariables: requiredVariables
                      .split(',')
                      .map((item) => item.trim())
                      .filter(Boolean),
                    variableSchema: {},
                    styleConfig: {},
                    lockedBlocks: [],
                  },
                  {
                    onSuccess: () => {
                      toast({ title: 'Version created' });
                      navigate(`/admin/dms/document-studio/templates/${templateId}`);
                    },
                    onError: (error) => showErrorToast(error, toast),
                  },
                )
              }
            >
              Save Version
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export function DocumentFilingRulesPage(): JSX.Element {
  const rules = useDmsFilingRules();
  return (
    <div className="space-y-6">
      <PageHeader
        title="Filing Rules"
        breadcrumbs={[
          { label: 'Document Studio', to: '/admin/dms/document-studio' },
          { label: 'Filing Rules' },
        ]}
        actions={
          <Button asChild variant="outline">
            <Link to="/admin/dms/document-studio">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Templates
            </Link>
          </Button>
        }
      />
      <DataTable
        data={rules.data ?? []}
        isLoading={rules.isLoading}
        error={rules.error}
        onRetry={() => rules.refetch()}
        getRowId={(row: FilingRule) => row.id}
        dense
        emptyTitle="No filing rules"
        emptySubtitle="Default filing rules are created when this page loads."
        columns={[
          { key: 'module', header: 'Module' },
          { key: 'documentType', header: 'Document Type' },
          { key: 'entityType', header: 'Entity' },
          { key: 'pathTemplate', header: 'DMS Path' },
          {
            key: 'portalVisible',
            header: 'Portal',
            render: (row) => (row.portalVisible ? 'Visible' : 'Internal'),
          },
        ]}
      />
    </div>
  );
}

export function DocumentPackagesPage(): JSX.Element {
  const packages = useDocumentPackages();
  return (
    <div className="space-y-6">
      <PageHeader
        title="Document Packages"
        breadcrumbs={[
          { label: 'Document Studio', to: '/admin/dms/document-studio' },
          { label: 'Packages' },
        ]}
        actions={
          <Button asChild>
            <Link to="/admin/dms/document-studio/packages/new">
              <Plus className="mr-2 h-4 w-4" />
              New Package
            </Link>
          </Button>
        }
      />
      <DataTable
        data={packages.data?.items ?? []}
        isLoading={packages.isLoading}
        error={packages.error}
        onRetry={() => packages.refetch()}
        getRowId={(row: DocumentPackage) => row.id}
        dense
        emptyTitle="No packages"
        emptySubtitle="Create a process package to group generated and uploaded documents."
        columns={[
          {
            key: 'packageNumber',
            header: 'Package',
            render: (row) => (
              <div>
                <div className="font-medium">{row.name}</div>
                <div className="text-xs text-muted-foreground">{row.packageNumber}</div>
              </div>
            ),
          },
          { key: 'packageType', header: 'Type' },
          {
            key: 'entity',
            header: 'Entity',
            render: (row) => `${row.entityType} · ${row.entityId.slice(0, 8)}`,
          },
          {
            key: 'status',
            header: 'Status',
            render: (row) => <Badge className={statusClass(row.status)}>{row.status}</Badge>,
          },
        ]}
      />
    </div>
  );
}

export function DocumentPackageCreatePage(): JSX.Element {
  const navigate = useNavigate();
  const { toast } = useToast();
  const createPackage = useCreateDocumentPackage();
  const [packageType, setPackageType] = useState('SANCTION_PACKAGE');
  const [name, setName] = useState('Sanction Package');
  const [entityType, setEntityType] = useState('sanction');
  const [entityId, setEntityId] = useState<string>(() => crypto.randomUUID());

  return (
    <div className="space-y-6">
      <PageHeader
        title="New Package"
        breadcrumbs={[
          { label: 'Document Studio', to: '/admin/dms/document-studio' },
          { label: 'Packages', to: '/admin/dms/document-studio/packages' },
          { label: 'New Package' },
        ]}
      />
      <Card className="max-w-3xl">
        <CardContent className="grid gap-4 pt-6">
          <div className="grid gap-2">
            <Label>Package type</Label>
            <Input value={packageType} onChange={(event) => setPackageType(event.target.value)} />
          </div>
          <div className="grid gap-2">
            <Label>Name</Label>
            <Input value={name} onChange={(event) => setName(event.target.value)} />
          </div>
          <div className="grid gap-2">
            <Label>Entity type</Label>
            <Input value={entityType} onChange={(event) => setEntityType(event.target.value)} />
          </div>
          <div className="grid gap-2">
            <Label>Entity ID</Label>
            <Input value={entityId} onChange={(event) => setEntityId(event.target.value)} />
          </div>
          <div className="flex justify-end gap-2">
            <Button asChild variant="outline">
              <Link to="/admin/dms/document-studio/packages">Cancel</Link>
            </Button>
            <Button
              disabled={createPackage.isPending}
              onClick={() =>
                createPackage.mutate(
                  {
                    packageType,
                    name,
                    entityType,
                    entityId,
                    manifest: { source: 'DOCUMENT_STUDIO' },
                  },
                  {
                    onSuccess: () => {
                      toast({ title: 'Package created' });
                      navigate('/admin/dms/document-studio/packages');
                    },
                    onError: (error) => showErrorToast(error, toast),
                  },
                )
              }
            >
              Create Package
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
