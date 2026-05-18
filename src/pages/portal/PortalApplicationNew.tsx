/**
 * Scheme Portal — New Loan Application wizard.
 *
 * Steps:
 *   1. Entity & Product  — pick entity (if borrower has >1) + loan product
 *   2. Loan details      — amount + tenure + purpose
 *   3. Fund utilisation  — split the requested amount across categories
 *   4. Documents         — stage supporting docs for draft upload + submit
 *   5. Review & submit   — confirmation
 *
 * Uses RHF + zod (CLAUDE.md §5.3) with a single `submitApplicationSchema`
 * that validates the whole payload at the final step.  Idempotency-Key is
 * carried at the service layer (CLAUDE.md §6.3).
 *
 * Reuse note: the admin lending pipeline's `StepFundUtilization` is tied
 * to the admin wizard context + admin-side IIF hooks (subvention schemes,
 * category catalogue) that the borrower user does not have access to.
 * The portal therefore renders an equivalent zod-driven step inline; the
 * resulting payload matches `SubmitApplicationRequest.fundUtilization`.
 */

import { zodResolver } from '@hookform/resolvers/zod';
import { ChevronLeft, ChevronRight, CloudUpload, Loader2, Send, Trash2 } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate } from 'react-router-dom';

import {
  AmountDisplay,
  AmountInput,
  EmptyState,
  ErrorState,
  FormShell,
  PageHeader,
  SkeletonTable,
} from '@/components/common';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
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
import { Textarea } from '@/components/ui/textarea';
import { useActiveEntity } from '@/hooks/portal/useActiveEntity';
import {
  useCreatePortalApplicationDraft,
  usePortalProducts,
  usePortalUtilizationCategories,
  useSubmitPortalApplication,
  useUploadApplicationDocument,
} from '@/hooks/portal/useApplications';
import { useToast } from '@/hooks/use-toast';
import { showErrorToast } from '@/lib/errorToast';
import { logger } from '@/lib/logger';
import {
  submitApplicationSchema,
  type SubmitApplicationInput,
} from '@/schemas/portal/applicationSchema';

type Step = 'entity' | 'loan' | 'utilization' | 'documents' | 'review';

const STEPS: { key: Step; label: string }[] = [
  { key: 'entity', label: 'Entity & product' },
  { key: 'loan', label: 'Loan details' },
  { key: 'utilization', label: 'Fund utilisation' },
  { key: 'documents', label: 'Documents' },
  { key: 'review', label: 'Review & submit' },
];

const PRODUCT_FALLBACK: { id: string; name: string }[] = [];

interface StagedDocument {
  id: string;
  file: File;
  documentType: string;
  status: 'staged' | 'uploading' | 'uploaded' | 'error';
  errorMessage?: string;
}

export default function PortalApplicationNew(): JSX.Element {
  const navigate = useNavigate();
  const { toast } = useToast();
  const { entities, activeEntityId } = useActiveEntity();

  const [step, setStep] = useState<Step>('entity');
  const [stagedDocuments, setStagedDocuments] = useState<StagedDocument[]>([]);
  const [submittedAppId, setSubmittedAppId] = useState<string | null>(null);

  const form = useForm<SubmitApplicationInput>({
    resolver: zodResolver(submitApplicationSchema),
    defaultValues: {
      entityId: entities.length === 1 ? entities[0]!.id : (activeEntityId ?? ''),
      productId: '',
      requestedAmount: '',
      tenureMonths: 12,
      purposeDescription: '',
      projectName: '',
      projectLocation: '',
      projectCost: '',
      shipyardName: '',
      maritimeSegment: '',
      lenderName: '',
      lenderBranch: '',
      sanctionReference: '',
      declarationAccepted: false,
      lines: [],
    },
    mode: 'onBlur',
  });

  const selectedEntityId = form.watch('entityId');
  const productsQuery = usePortalProducts(selectedEntityId || undefined);
  const utilizationCategoriesQuery = usePortalUtilizationCategories();
  const createDraft = useCreatePortalApplicationDraft();
  const submitApplication = useSubmitPortalApplication();
  const uploadDocument = useUploadApplicationDocument();

  const lines = form.watch('lines');
  const requestedAmount = form.watch('requestedAmount');

  const totalAllocated = lines.reduce((acc, l) => acc + Number(l.amount || 0), 0);
  const requestedNumeric = Number(requestedAmount || 0);
  const remainder = requestedNumeric - totalAllocated;

  useEffect(() => {
    if ((form.getValues('lines') ?? []).length > 0) {
      return;
    }
    const categories = utilizationCategoriesQuery.data ?? [];
    if (categories.length === 0) {
      return;
    }
    form.setValue(
      'lines',
      categories.map((category) => ({
        categoryId: category.id,
        categoryLabel: category.label,
        amount: '',
        remarks: null,
      })),
      { shouldDirty: false },
    );
  }, [form, utilizationCategoriesQuery.data]);

  const goNext = async () => {
    let valid = true;
    switch (step) {
      case 'entity':
        valid = await form.trigger(['entityId', 'productId']);
        if (valid) setStep('loan');
        break;
      case 'loan':
        valid = await form.trigger([
          'requestedAmount',
          'tenureMonths',
          'purposeDescription',
          'projectName',
          'projectLocation',
          'projectCost',
          'shipyardName',
          'maritimeSegment',
          'lenderName',
          'lenderBranch',
          'sanctionReference',
          'declarationAccepted',
        ]);
        if (valid) setStep('utilization');
        break;
      case 'utilization':
        valid = await form.trigger(['lines']);
        if (valid) setStep('documents');
        break;
      case 'documents':
        setStep('review');
        break;
      case 'review':
        // submit
        break;
    }
  };

  const goBack = () => {
    const idx = STEPS.findIndex((s) => s.key === step);
    if (idx > 0) setStep(STEPS[idx - 1]!.key);
  };

  const stageDocument = (file: File, documentType: string) => {
    setStagedDocuments((prev) => [
      ...prev,
      {
        id: crypto.randomUUID(),
        file,
        documentType,
        status: 'staged',
      },
    ]);
  };

  const removeStagedDocument = (id: string) => {
    setStagedDocuments((prev) => prev.filter((d) => d.id !== id));
  };

  const buildDraftPayload = (values: SubmitApplicationInput) => ({
    entityId: values.entityId,
    productId: values.productId,
    requestedAmount: values.requestedAmount,
    tenureMonths: values.tenureMonths,
    purposeDescription: values.purposeDescription,
    projectName: values.projectName || null,
    projectLocation: values.projectLocation || null,
    projectCost: values.projectCost || null,
    shipyardName: values.shipyardName || null,
    maritimeSegment: values.maritimeSegment || null,
    lenderName: values.lenderName || null,
    lenderBranch: values.lenderBranch || null,
    sanctionReference: values.sanctionReference || null,
    declarationAccepted: values.declarationAccepted,
    fundUtilization: values.lines.map((l) => ({
      categoryId: l.categoryId,
      amount: l.amount,
      remarks: l.remarks ?? null,
    })),
  });

  const onSubmit = form.handleSubmit(async (values) => {
    try {
      const draft = await createDraft.mutateAsync(buildDraftPayload(values));
      setSubmittedAppId(draft.id);

      const failedUploads: string[] = [];
      for (const doc of stagedDocuments) {
        try {
          await uploadDocument.mutateAsync({
            applicationId: draft.id,
            file: doc.file,
            documentType: doc.documentType,
            documentName: doc.file.name,
          });
        } catch (uploadErr) {
          failedUploads.push(doc.file.name);
          logger.warn('Document upload failed', {
            file: doc.file.name,
            error: uploadErr,
          });
        }
      }

      if (failedUploads.length > 0) {
        toast({
          title: 'Draft saved',
          description:
            'Some documents could not be uploaded. Complete the remaining uploads from the application detail page before submitting.',
          variant: 'destructive',
        });
        navigate(`/portal/applications/${draft.id}`);
        return;
      }

      const created = await submitApplication.mutateAsync(draft.id);
      setSubmittedAppId(created.id);

      toast({
        title: 'Application submitted',
        description: `Application ${created.applicationNumber} is now in the scheme review queue.`,
      });
      navigate(`/portal/applications/${created.id}`);
    } catch (err) {
      showErrorToast(err, toast);
    }
  });

  const saveDraft = form.handleSubmit(async (values) => {
    try {
      const draft = await createDraft.mutateAsync(buildDraftPayload(values));
      toast({
        title: 'Draft saved',
        description: `Application ${draft.applicationNumber} was saved as a draft.`,
      });
      navigate(`/portal/applications/${draft.id}`);
    } catch (err) {
      showErrorToast(err, toast);
    }
  });

  const productOptions = productsQuery.data ?? PRODUCT_FALLBACK;
  const submitting =
    createDraft.isPending || submitApplication.isPending || uploadDocument.isPending;

  return (
    <div className="space-y-6">
      <PageHeader
        title="New scheme application"
        subtitle="Provide institutional borrower, project, lender, and utilisation details for scheme review."
        breadcrumbs={[
          { label: 'Scheme Portal', to: '/portal/workbench' },
          { label: 'Applications', to: '/portal/applications' },
          { label: 'New' },
        ]}
      />

      <div className="flex flex-wrap gap-2 text-sm">
        {STEPS.map((s, idx) => {
          const isActive = s.key === step;
          const isPast = STEPS.findIndex((x) => x.key === step) > idx;
          return (
            <div
              key={s.key}
              className={`rounded-full border px-3 py-1 ${
                isActive
                  ? 'border-emerald-600 bg-emerald-50 text-emerald-700'
                  : isPast
                    ? 'border-emerald-200 bg-emerald-100 text-emerald-700'
                    : 'border-muted text-muted-foreground'
              }`}
            >
              {idx + 1}. {s.label}
            </div>
          );
        })}
      </div>

      <Form {...form}>
        <form onSubmit={onSubmit}>
          <FormShell
            footer={
              <>
                <Button
                  type="button"
                  variant="ghost"
                  onClick={goBack}
                  disabled={step === 'entity' || submitting}
                >
                  <ChevronLeft className="mr-1 h-4 w-4" /> Back
                </Button>
                {step !== 'review' ? (
                  <Button
                    type="button"
                    className="bg-emerald-600 hover:bg-emerald-700"
                    onClick={goNext}
                  >
                    Next <ChevronRight className="ml-1 h-4 w-4" />
                  </Button>
                ) : (
                  <div className="flex items-center gap-2">
                    <Button
                      type="button"
                      variant="outline"
                      onClick={saveDraft}
                      disabled={submitting || submittedAppId !== null}
                    >
                      Save draft
                    </Button>
                    <Button
                      type="submit"
                      className="bg-emerald-600 hover:bg-emerald-700"
                      disabled={submitting || submittedAppId !== null}
                    >
                      {submitting ? (
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      ) : (
                        <Send className="mr-2 h-4 w-4" />
                      )}
                      Submit application
                    </Button>
                  </div>
                )}
              </>
            }
          >
            {step === 'entity' && (
              <div className="space-y-6">
                <FormField
                  control={form.control}
                  name="entityId"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Organisation</FormLabel>
                      <FormControl>
                        <Select
                          value={field.value}
                          onValueChange={field.onChange}
                          disabled={entities.length <= 1}
                        >
                          <SelectTrigger>
                            <SelectValue placeholder="Pick an entity" />
                          </SelectTrigger>
                          <SelectContent>
                            {entities.map((e) => (
                              <SelectItem key={e.id} value={e.id}>
                                {e.legalName}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="productId"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Loan product</FormLabel>
                      <FormControl>
                        {productOptions.length > 0 ? (
                          <Select value={field.value} onValueChange={field.onChange}>
                            <SelectTrigger>
                              <SelectValue placeholder="Pick a product" />
                            </SelectTrigger>
                            <SelectContent>
                              {productOptions.map((p) => (
                                <SelectItem key={p.id} value={p.id}>
                                  {p.name}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        ) : (
                          <Input
                            {...field}
                            placeholder="Paste the scheme product ID provided by SMFCL"
                          />
                        )}
                      </FormControl>
                      {productsQuery.isLoading ? (
                        <p className="text-xs text-muted-foreground">Loading eligible products…</p>
                      ) : null}
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>
            )}

            {step === 'loan' && (
              <div className="space-y-6">
                <FormField
                  control={form.control}
                  name="requestedAmount"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Requested amount (INR)</FormLabel>
                      <FormControl>
                        <AmountInput
                          value={field.value === '' ? undefined : Number(field.value)}
                          onChange={(n) => field.onChange(n === undefined ? '' : String(n))}
                          placeholder="Loan amount"
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="tenureMonths"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Tenure (months)</FormLabel>
                      <FormControl>
                        <Input
                          type="number"
                          min={1}
                          max={360}
                          {...field}
                          onChange={(e) => field.onChange(Number(e.target.value))}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="purposeDescription"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Purpose</FormLabel>
                      <FormControl>
                        <Textarea
                          rows={4}
                          placeholder="Describe how the loan will be used."
                          {...field}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                  <FormField
                    control={form.control}
                    name="projectName"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Project name</FormLabel>
                        <FormControl>
                          <Input {...field} placeholder="Dry dock modernisation" />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={form.control}
                    name="projectLocation"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Project location</FormLabel>
                        <FormControl>
                          <Input {...field} placeholder="Visakhapatnam, Andhra Pradesh" />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>
                <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                  <FormField
                    control={form.control}
                    name="projectCost"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Project cost (optional)</FormLabel>
                        <FormControl>
                          <AmountInput
                            value={field.value ? Number(field.value) : undefined}
                            onChange={(n) => field.onChange(n === undefined ? '' : String(n))}
                            placeholder="Total project cost"
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={form.control}
                    name="shipyardName"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Shipyard / facility</FormLabel>
                        <FormControl>
                          <Input {...field} placeholder="Facility or yard name" />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>
                <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                  <FormField
                    control={form.control}
                    name="maritimeSegment"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Maritime segment</FormLabel>
                        <FormControl>
                          <Input {...field} placeholder="Shipbuilding / repair / ancillary" />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={form.control}
                    name="lenderName"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Primary lender</FormLabel>
                        <FormControl>
                          <Input {...field} placeholder="Scheduled lender / bank name" />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>
                <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                  <FormField
                    control={form.control}
                    name="lenderBranch"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Lender branch / office</FormLabel>
                        <FormControl>
                          <Input {...field} placeholder="Branch or credit office" />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={form.control}
                    name="sanctionReference"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Sanction reference</FormLabel>
                        <FormControl>
                          <Input {...field} placeholder="Reference / sanction memo number" />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>
                <FormField
                  control={form.control}
                  name="declarationAccepted"
                  render={({ field }) => (
                    <FormItem>
                      <div className="flex items-start gap-3 rounded-lg border p-3">
                        <input
                          id="portal-borrower-declaration"
                          type="checkbox"
                          checked={field.value}
                          onChange={(e) => field.onChange(e.target.checked)}
                          className="mt-1"
                        />
                        <div>
                          <FormLabel htmlFor="portal-borrower-declaration">
                            Borrower declaration
                          </FormLabel>
                          <p className="text-sm text-muted-foreground">
                            We confirm that the organisation is an eligible institutional borrower
                            and that the submitted project, lender, and utilisation details are
                            complete and accurate.
                          </p>
                        </div>
                      </div>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>
            )}

            {step === 'utilization' && (
              <div className="space-y-4">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="text-sm">
                    <span className="text-muted-foreground">Requested: </span>
                    <span className="font-medium">
                      <AmountDisplay amount={requestedNumeric} />
                    </span>
                    <span className="ml-4 text-muted-foreground">Allocated: </span>
                    <span className="font-medium">
                      <AmountDisplay amount={totalAllocated} />
                    </span>
                    <span className="ml-4 text-muted-foreground">Remaining: </span>
                    <span
                      className={`font-medium ${
                        Math.abs(remainder) > 0.01 ? 'text-amber-600' : 'text-emerald-700'
                      }`}
                    >
                      <AmountDisplay amount={remainder} />
                    </span>
                  </div>
                </div>
                {utilizationCategoriesQuery.isLoading ? (
                  <SkeletonTable rows={5} columns={3} />
                ) : utilizationCategoriesQuery.isError ? (
                  <ErrorState
                    error={utilizationCategoriesQuery.error}
                    onRetry={() => utilizationCategoriesQuery.refetch()}
                  />
                ) : lines.length === 0 ? (
                  <EmptyState
                    title="No utilisation categories configured"
                    subtitle="Ask the scheme administrator to configure fund-utilisation categories before creating applications."
                  />
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Category label</TableHead>
                        <TableHead className="text-right">Amount</TableHead>
                        <TableHead>Remarks</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {lines.map((line, idx) => (
                        <TableRow key={line.categoryId}>
                          <TableCell>
                            <div className="font-medium">
                              {line.categoryLabel ?? line.categoryId}
                            </div>
                            <div className="text-xs text-muted-foreground">
                              Scheme-configured utilisation bucket
                            </div>
                          </TableCell>
                          <TableCell className="text-right tabular-nums">
                            <AmountInput
                              value={
                                line.amount === '' || line.amount == null
                                  ? undefined
                                  : Number(line.amount)
                              }
                              onChange={(n) => {
                                const next = [...form.getValues('lines')];
                                next[idx] = {
                                  ...next[idx]!,
                                  amount: n === undefined ? '' : String(n),
                                };
                                form.setValue('lines', next, {
                                  shouldValidate: true,
                                });
                              }}
                            />
                          </TableCell>
                          <TableCell>
                            <Input
                              value={line.remarks ?? ''}
                              onChange={(e) => {
                                const next = [...form.getValues('lines')];
                                next[idx] = {
                                  ...next[idx]!,
                                  remarks: e.target.value || null,
                                };
                                form.setValue('lines', next);
                              }}
                            />
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
                {form.formState.errors.lines && (
                  <p className="text-sm text-destructive">
                    {String(form.formState.errors.lines.message ?? '')}
                  </p>
                )}
              </div>
            )}

            {step === 'documents' && (
              <div className="space-y-4">
                <UploadStager onAdd={stageDocument} />
                {stagedDocuments.length === 0 ? (
                  <p className="text-sm text-muted-foreground">
                    No documents staged yet. Documents are uploaded onto the draft application
                    before the final submit call.
                  </p>
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>File</TableHead>
                        <TableHead>Type</TableHead>
                        <TableHead className="w-12" />
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {stagedDocuments.map((d) => (
                        <TableRow key={d.id}>
                          <TableCell>{d.file.name}</TableCell>
                          <TableCell>{d.documentType}</TableCell>
                          <TableCell>
                            <Button
                              type="button"
                              variant="ghost"
                              size="icon"
                              onClick={() => removeStagedDocument(d.id)}
                              aria-label="Remove staged document"
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </div>
            )}

            {step === 'review' && (
              <ReviewPanel form={form} stagedDocCount={stagedDocuments.length} />
            )}
          </FormShell>
        </form>
      </Form>
    </div>
  );
}

function UploadStager({
  onAdd,
}: {
  onAdd: (file: File, documentType: string) => void;
}): JSX.Element {
  const [type, setType] = useState('SUPPORTING_DOCUMENT');
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Stage a document</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 items-end gap-3 md:grid-cols-3">
          <div className="space-y-2 md:col-span-1">
            <Label>Type</Label>
            <Select value={type} onValueChange={setType}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="BOARD_RESOLUTION">Board resolution</SelectItem>
                <SelectItem value="FINANCIAL_STATEMENT">Financial statement</SelectItem>
                <SelectItem value="PROJECT_PROPOSAL">Project proposal</SelectItem>
                <SelectItem value="SUPPORTING_DOCUMENT">Supporting document</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2 md:col-span-2">
            <Label>File</Label>
            <Input
              type="file"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) {
                  onAdd(file, type);
                  e.target.value = '';
                }
              }}
            />
          </div>
        </div>
        <p className="mt-3 flex items-center gap-1 text-xs text-muted-foreground">
          <CloudUpload className="h-3.5 w-3.5" />
          PDF / images up to 50 MB. Files are uploaded onto the draft application before the final
          submit call.
        </p>
      </CardContent>
    </Card>
  );
}

function ReviewPanel({
  form,
  stagedDocCount,
}: {
  form: ReturnType<typeof useForm<SubmitApplicationInput>>;
  stagedDocCount: number;
}): JSX.Element {
  const v = form.getValues();
  const sum = v.lines.reduce((acc, l) => acc + Number(l.amount || 0), 0);
  return (
    <div className="space-y-4 text-sm">
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <div>
          <p className="text-muted-foreground">Organisation</p>
          <p className="font-medium">{v.entityId || '—'}</p>
        </div>
        <div>
          <p className="text-muted-foreground">Product</p>
          <p className="font-medium">{v.productId || '—'}</p>
        </div>
        <div>
          <p className="text-muted-foreground">Requested amount</p>
          <p className="font-medium">
            <AmountDisplay amount={Number(v.requestedAmount || 0)} />
          </p>
        </div>
        <div>
          <p className="text-muted-foreground">Tenure</p>
          <p className="font-medium">{v.tenureMonths} months</p>
        </div>
      </div>
      <div>
        <p className="text-muted-foreground">Purpose</p>
        <p className="mt-1 whitespace-pre-line">{v.purposeDescription}</p>
      </div>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <div>
          <p className="text-muted-foreground">Project</p>
          <p className="font-medium">{v.projectName || '—'}</p>
        </div>
        <div>
          <p className="text-muted-foreground">Location</p>
          <p className="font-medium">{v.projectLocation || '—'}</p>
        </div>
        <div>
          <p className="text-muted-foreground">Primary lender</p>
          <p className="font-medium">{v.lenderName || '—'}</p>
        </div>
        <div>
          <p className="text-muted-foreground">Sanction reference</p>
          <p className="font-medium">{v.sanctionReference || '—'}</p>
        </div>
      </div>
      <div>
        <p className="mb-2 text-muted-foreground">Fund utilisation</p>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Category</TableHead>
              <TableHead className="text-right">Amount</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {v.lines.map((l) => (
              <TableRow key={l.categoryId}>
                <TableCell>{l.categoryLabel || l.categoryId}</TableCell>
                <TableCell className="text-right tabular-nums">
                  <AmountDisplay amount={Number(l.amount || 0)} />
                </TableCell>
              </TableRow>
            ))}
            <TableRow>
              <TableCell className="font-medium">Total</TableCell>
              <TableCell className="text-right font-medium tabular-nums">
                <AmountDisplay amount={sum} />
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </div>
      <p className="text-muted-foreground">
        {stagedDocCount === 0
          ? 'No documents staged. You can upload documents later from the application detail page.'
          : `${stagedDocCount} document(s) will be uploaded before submission.`}
      </p>
    </div>
  );
}
