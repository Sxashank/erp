import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, Save, Plus, Trash2 } from 'lucide-react';
import { useForm, useFieldArray } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Switch } from '@/components/ui/switch';
import { AmountInput } from '@/components/lending/common/AmountInput';

import { logger } from '@/lib/logger';
const productSchema = z.object({
  productCode: z.string().min(1, 'Product code is required'),
  productName: z.string().min(1, 'Product name is required'),
  description: z.string().optional(),
  category: z.enum([
    'TERM_LOAN',
    'WORKING_CAPITAL',
    'PROJECT_FINANCE',
    'LAP',
    'EQUIPMENT_FINANCE',
    'BILL_DISCOUNTING',
  ]),
  subCategory: z.string().optional(),
  minAmount: z.number().min(0, 'Minimum amount must be positive'),
  maxAmount: z.number().min(0, 'Maximum amount must be positive'),
  minTenureMonths: z.number().min(1, 'Minimum tenure must be at least 1 month'),
  maxTenureMonths: z.number().min(1, 'Maximum tenure must be at least 1 month'),
  interestType: z.enum(['FIXED', 'FLOATING']),
  baseRate: z.string().optional(),
  spreadBps: z.number().default(0),
  fixedRate: z.number().optional(),
  processingFeePercent: z.number().min(0).max(10),
  processingFeeMin: z.number().optional(),
  processingFeeMax: z.number().optional(),
  prepaymentAllowed: z.boolean().default(true),
  prepaymentChargePercent: z.number().optional(),
  prepaymentLockInMonths: z.number().optional(),
  moratoriumAllowed: z.boolean().default(true),
  maxMoratoriumMonths: z.number().optional(),
  repaymentFrequency: z.array(z.enum(['MONTHLY', 'QUARTERLY', 'HALF_YEARLY', 'YEARLY', 'BULLET'])),
  dayCountConvention: z.enum(['ACT_365', 'ACT_360', 'THIRTY_360']),
  fees: z
    .array(
      z.object({
        feeType: z.string(),
        feeName: z.string(),
        chargeType: z.enum(['PERCENTAGE', 'FIXED', 'SLAB']),
        percentage: z.number().optional(),
        fixedAmount: z.number().optional(),
        minAmount: z.number().optional(),
        maxAmount: z.number().optional(),
        isMandatory: z.boolean().default(false),
      })
    )
    .optional(),
  documentChecklist: z
    .array(
      z.object({
        documentType: z.string(),
        documentName: z.string(),
        isMandatory: z.boolean().default(false),
        stage: z.enum(['APPLICATION', 'APPRAISAL', 'SANCTION', 'DISBURSEMENT']),
      })
    )
    .optional(),
  status: z.enum(['ACTIVE', 'INACTIVE', 'DISCONTINUED']).default('ACTIVE'),
});

type ProductFormData = z.infer<typeof productSchema>;

const defaultValues: Partial<ProductFormData> = {
  category: 'TERM_LOAN',
  interestType: 'FLOATING',
  baseRate: 'SMFC_BR',
  spreadBps: 200,
  processingFeePercent: 1.0,
  prepaymentAllowed: true,
  moratoriumAllowed: true,
  repaymentFrequency: ['MONTHLY'],
  dayCountConvention: 'ACT_365',
  status: 'ACTIVE',
  fees: [],
  documentChecklist: [],
};

export default function ProductForm() {
  const navigate = useNavigate();
  const { id } = useParams();
  const isEdit = Boolean(id);
  const [activeTab, setActiveTab] = useState('basic');

  const {
    register,
    control,
    handleSubmit,
    watch,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<ProductFormData>({
    resolver: zodResolver(productSchema) as any,
    defaultValues,
  });

  const {
    fields: feeFields,
    append: appendFee,
    remove: removeFee,
  } = useFieldArray({
    control,
    name: 'fees',
  });

  const {
    fields: documentFields,
    append: appendDocument,
    remove: removeDocument,
  } = useFieldArray({
    control,
    name: 'documentChecklist',
  });

  const interestType = watch('interestType');

  const onSubmit = async (data: ProductFormData) => {
    logger.debug('Product data:', data);
    // API call would go here
    navigate('/admin/lending/products');
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => navigate('/admin/lending/products')}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div className="flex-1">
          <h1 className="text-2xl font-semibold">
            {isEdit ? 'Edit Loan Product' : 'Create Loan Product'}
          </h1>
          <p className="text-muted-foreground">
            {isEdit
              ? 'Update product configuration and terms'
              : 'Configure a new loan product with terms and conditions'}
          </p>
        </div>
        <Button onClick={handleSubmit(onSubmit as any)} disabled={isSubmitting}>
          <Save className="mr-2 h-4 w-4" />
          {isEdit ? 'Update Product' : 'Create Product'}
        </Button>
      </div>

      <form onSubmit={handleSubmit(onSubmit as any)}>
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="basic">Basic Info</TabsTrigger>
            <TabsTrigger value="interest">Interest & Fees</TabsTrigger>
            <TabsTrigger value="terms">Terms & Conditions</TabsTrigger>
            <TabsTrigger value="fees">Fee Structure</TabsTrigger>
            <TabsTrigger value="documents">Document Checklist</TabsTrigger>
          </TabsList>

          {/* Basic Info Tab */}
          <TabsContent value="basic" className="space-y-6 mt-6">
            <Card>
              <CardHeader>
                <CardTitle>Product Details</CardTitle>
                <CardDescription>Basic product identification and categorization</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="productCode">Product Code *</Label>
                    <Input
                      id="productCode"
                      placeholder="e.g., TL-CORP-001"
                      {...register('productCode')}
                    />
                    {errors.productCode && (
                      <p className="text-sm text-destructive">{errors.productCode.message}</p>
                    )}
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="productName">Product Name *</Label>
                    <Input
                      id="productName"
                      placeholder="e.g., Corporate Term Loan"
                      {...register('productName')}
                    />
                    {errors.productName && (
                      <p className="text-sm text-destructive">{errors.productName.message}</p>
                    )}
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="description">Description</Label>
                  <Textarea
                    id="description"
                    placeholder="Brief description of the product..."
                    rows={3}
                    {...register('description')}
                  />
                </div>

                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label>Category *</Label>
                    <Select
                      value={watch('category')}
                      onValueChange={(v) => setValue('category', v as ProductFormData['category'])}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select category" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="TERM_LOAN">Term Loan</SelectItem>
                        <SelectItem value="WORKING_CAPITAL">Working Capital</SelectItem>
                        <SelectItem value="PROJECT_FINANCE">Project Finance</SelectItem>
                        <SelectItem value="LAP">Loan Against Property</SelectItem>
                        <SelectItem value="EQUIPMENT_FINANCE">Equipment Finance</SelectItem>
                        <SelectItem value="BILL_DISCOUNTING">Bill Discounting</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="subCategory">Sub Category</Label>
                    <Input
                      id="subCategory"
                      placeholder="e.g., Corporate, SME, Retail"
                      {...register('subCategory')}
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>Status</Label>
                  <Select
                    value={watch('status')}
                    onValueChange={(v) => setValue('status', v as ProductFormData['status'])}
                  >
                    <SelectTrigger className="w-[200px]">
                      <SelectValue placeholder="Select status" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="ACTIVE">Active</SelectItem>
                      <SelectItem value="INACTIVE">Inactive</SelectItem>
                      <SelectItem value="DISCONTINUED">Discontinued</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Amount & Tenure Limits</CardTitle>
                <CardDescription>Define the permissible range for loan amounts and tenures</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label>Minimum Loan Amount *</Label>
                    <AmountInput
                      value={watch('minAmount') || 0}
                      onChange={(v) => setValue('minAmount', v ?? 0)}
                      placeholder="Enter minimum amount"
                    />
                    {errors.minAmount && (
                      <p className="text-sm text-destructive">{errors.minAmount.message}</p>
                    )}
                  </div>
                  <div className="space-y-2">
                    <Label>Maximum Loan Amount *</Label>
                    <AmountInput
                      value={watch('maxAmount') || 0}
                      onChange={(v) => setValue('maxAmount', v ?? 0)}
                      placeholder="Enter maximum amount"
                    />
                    {errors.maxAmount && (
                      <p className="text-sm text-destructive">{errors.maxAmount.message}</p>
                    )}
                  </div>
                </div>

                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="minTenureMonths">Minimum Tenure (Months) *</Label>
                    <Input
                      id="minTenureMonths"
                      type="number"
                      min={1}
                      {...register('minTenureMonths', { valueAsNumber: true })}
                    />
                    {errors.minTenureMonths && (
                      <p className="text-sm text-destructive">{errors.minTenureMonths.message}</p>
                    )}
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="maxTenureMonths">Maximum Tenure (Months) *</Label>
                    <Input
                      id="maxTenureMonths"
                      type="number"
                      min={1}
                      {...register('maxTenureMonths', { valueAsNumber: true })}
                    />
                    {errors.maxTenureMonths && (
                      <p className="text-sm text-destructive">{errors.maxTenureMonths.message}</p>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Interest & Fees Tab */}
          <TabsContent value="interest" className="space-y-6 mt-6">
            <Card>
              <CardHeader>
                <CardTitle>Interest Configuration</CardTitle>
                <CardDescription>Define interest rate type and calculation parameters</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label>Interest Type *</Label>
                    <Select
                      value={interestType}
                      onValueChange={(v) =>
                        setValue('interestType', v as ProductFormData['interestType'])
                      }
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select interest type" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="FIXED">Fixed Rate</SelectItem>
                        <SelectItem value="FLOATING">Floating Rate</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Day Count Convention *</Label>
                    <Select
                      value={watch('dayCountConvention')}
                      onValueChange={(v) =>
                        setValue('dayCountConvention', v as ProductFormData['dayCountConvention'])
                      }
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select convention" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="ACT_365">Actual/365</SelectItem>
                        <SelectItem value="ACT_360">Actual/360</SelectItem>
                        <SelectItem value="THIRTY_360">30/360</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                {interestType === 'FLOATING' ? (
                  <div className="grid gap-4 md:grid-cols-2">
                    <div className="space-y-2">
                      <Label>Base Rate *</Label>
                      <Select
                        value={watch('baseRate')}
                        onValueChange={(v) => setValue('baseRate', v)}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select base rate" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="SMFC_BR">SMFC Base Rate</SelectItem>
                          <SelectItem value="MCLR">MCLR</SelectItem>
                          <SelectItem value="REPO_LINKED">Repo Linked</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="spreadBps">Spread (Basis Points) *</Label>
                      <Input
                        id="spreadBps"
                        type="number"
                        min={0}
                        placeholder="e.g., 200 for 2%"
                        {...register('spreadBps', { valueAsNumber: true })}
                      />
                      <p className="text-xs text-muted-foreground">
                        100 bps = 1%. Effective Rate = Base Rate + Spread
                      </p>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-2">
                    <Label htmlFor="fixedRate">Fixed Interest Rate (% p.a.) *</Label>
                    <Input
                      id="fixedRate"
                      type="number"
                      step="0.01"
                      min={0}
                      max={30}
                      placeholder="e.g., 12.50"
                      {...register('fixedRate', { valueAsNumber: true })}
                    />
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Processing Fee</CardTitle>
                <CardDescription>Define processing fee structure</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-4 md:grid-cols-3">
                  <div className="space-y-2">
                    <Label htmlFor="processingFeePercent">Processing Fee (%) *</Label>
                    <Input
                      id="processingFeePercent"
                      type="number"
                      step="0.01"
                      min={0}
                      max={10}
                      {...register('processingFeePercent', { valueAsNumber: true })}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Minimum Fee</Label>
                    <AmountInput
                      value={watch('processingFeeMin') || 0}
                      onChange={(v) => setValue('processingFeeMin', v)}
                      placeholder="Minimum fee amount"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label>Maximum Fee</Label>
                    <AmountInput
                      value={watch('processingFeeMax') || 0}
                      onChange={(v) => setValue('processingFeeMax', v)}
                      placeholder="Maximum fee amount"
                    />
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Terms & Conditions Tab */}
          <TabsContent value="terms" className="space-y-6 mt-6">
            <Card>
              <CardHeader>
                <CardTitle>Repayment Terms</CardTitle>
                <CardDescription>Configure repayment frequencies and moratorium options</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>Repayment Frequency Options</Label>
                  <div className="flex flex-wrap gap-4">
                    {['MONTHLY', 'QUARTERLY', 'HALF_YEARLY', 'YEARLY', 'BULLET'].map((freq) => (
                      <label key={freq} className="flex items-center gap-2">
                        <input
                          type="checkbox"
                          value={freq}
                          {...register('repaymentFrequency')}
                          className="h-4 w-4 rounded border-gray-300"
                        />
                        <span className="text-sm">{freq.replace('_', ' ')}</span>
                      </label>
                    ))}
                  </div>
                </div>

                <div className="flex items-center justify-between rounded-lg border p-4">
                  <div className="space-y-0.5">
                    <Label>Moratorium Allowed</Label>
                    <p className="text-sm text-muted-foreground">
                      Allow moratorium period at the start of the loan
                    </p>
                  </div>
                  <Switch
                    checked={watch('moratoriumAllowed')}
                    onCheckedChange={(v) => setValue('moratoriumAllowed', v)}
                  />
                </div>

                {watch('moratoriumAllowed') && (
                  <div className="space-y-2">
                    <Label htmlFor="maxMoratoriumMonths">Maximum Moratorium Period (Months)</Label>
                    <Input
                      id="maxMoratoriumMonths"
                      type="number"
                      min={0}
                      className="w-[200px]"
                      {...register('maxMoratoriumMonths', { valueAsNumber: true })}
                    />
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Prepayment Terms</CardTitle>
                <CardDescription>Configure prepayment options and charges</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between rounded-lg border p-4">
                  <div className="space-y-0.5">
                    <Label>Prepayment Allowed</Label>
                    <p className="text-sm text-muted-foreground">
                      Allow borrower to prepay the loan
                    </p>
                  </div>
                  <Switch
                    checked={watch('prepaymentAllowed')}
                    onCheckedChange={(v) => setValue('prepaymentAllowed', v)}
                  />
                </div>

                {watch('prepaymentAllowed') && (
                  <div className="grid gap-4 md:grid-cols-2">
                    <div className="space-y-2">
                      <Label htmlFor="prepaymentLockInMonths">Lock-in Period (Months)</Label>
                      <Input
                        id="prepaymentLockInMonths"
                        type="number"
                        min={0}
                        placeholder="Months before prepayment allowed"
                        {...register('prepaymentLockInMonths', { valueAsNumber: true })}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="prepaymentChargePercent">Prepayment Charge (%)</Label>
                      <Input
                        id="prepaymentChargePercent"
                        type="number"
                        step="0.01"
                        min={0}
                        max={10}
                        placeholder="Charge on prepaid amount"
                        {...register('prepaymentChargePercent', { valueAsNumber: true })}
                      />
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Fee Structure Tab */}
          <TabsContent value="fees" className="space-y-6 mt-6">
            <Card>
              <CardHeader>
                <CardTitle>Fee Structure</CardTitle>
                <CardDescription>Define additional fees applicable to this product</CardDescription>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Fee Type</TableHead>
                      <TableHead>Fee Name</TableHead>
                      <TableHead>Charge Type</TableHead>
                      <TableHead>Value</TableHead>
                      <TableHead>Mandatory</TableHead>
                      <TableHead className="w-[50px]"></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {feeFields.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={6} className="text-center py-8 text-muted-foreground">
                          No fees configured. Click "Add Fee" to add fee structures.
                        </TableCell>
                      </TableRow>
                    ) : (
                      feeFields.map((field, index) => (
                        <TableRow key={field.id}>
                          <TableCell>
                            <Select
                              value={watch(`fees.${index}.feeType`)}
                              onValueChange={(v) => setValue(`fees.${index}.feeType`, v)}
                            >
                              <SelectTrigger className="w-[150px]">
                                <SelectValue placeholder="Select type" />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="DOCUMENTATION">Documentation</SelectItem>
                                <SelectItem value="LEGAL">Legal</SelectItem>
                                <SelectItem value="VALUATION">Valuation</SelectItem>
                                <SelectItem value="INSURANCE">Insurance</SelectItem>
                                <SelectItem value="STAMP_DUTY">Stamp Duty</SelectItem>
                                <SelectItem value="OTHER">Other</SelectItem>
                              </SelectContent>
                            </Select>
                          </TableCell>
                          <TableCell>
                            <Input
                              placeholder="Fee name"
                              {...register(`fees.${index}.feeName`)}
                              className="w-[180px]"
                            />
                          </TableCell>
                          <TableCell>
                            <Select
                              value={watch(`fees.${index}.chargeType`)}
                              onValueChange={(v) =>
                                setValue(`fees.${index}.chargeType`, v as 'PERCENTAGE' | 'FIXED' | 'SLAB')
                              }
                            >
                              <SelectTrigger className="w-[130px]">
                                <SelectValue placeholder="Type" />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="PERCENTAGE">Percentage</SelectItem>
                                <SelectItem value="FIXED">Fixed</SelectItem>
                                <SelectItem value="SLAB">Slab-based</SelectItem>
                              </SelectContent>
                            </Select>
                          </TableCell>
                          <TableCell>
                            {watch(`fees.${index}.chargeType`) === 'PERCENTAGE' ? (
                              <Input
                                type="number"
                                step="0.01"
                                placeholder="%"
                                {...register(`fees.${index}.percentage`, { valueAsNumber: true })}
                                className="w-[100px]"
                              />
                            ) : (
                              <Input
                                type="number"
                                placeholder="Amount"
                                {...register(`fees.${index}.fixedAmount`, { valueAsNumber: true })}
                                className="w-[120px]"
                              />
                            )}
                          </TableCell>
                          <TableCell>
                            <Switch
                              checked={watch(`fees.${index}.isMandatory`)}
                              onCheckedChange={(v) => setValue(`fees.${index}.isMandatory`, v)}
                            />
                          </TableCell>
                          <TableCell>
                            <Button
                              type="button"
                              variant="ghost"
                              size="icon"
                              onClick={() => removeFee(index)}
                            >
                              <Trash2 className="h-4 w-4 text-destructive" />
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
                <Button
                  type="button"
                  variant="outline"
                  className="mt-4"
                  onClick={() =>
                    appendFee({
                      feeType: 'OTHER',
                      feeName: '',
                      chargeType: 'FIXED',
                      isMandatory: false,
                    })
                  }
                >
                  <Plus className="mr-2 h-4 w-4" />
                  Add Fee
                </Button>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Document Checklist Tab */}
          <TabsContent value="documents" className="space-y-6 mt-6">
            <Card>
              <CardHeader>
                <CardTitle>Document Checklist</CardTitle>
                <CardDescription>Define required documents for this product at each stage</CardDescription>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Document Type</TableHead>
                      <TableHead>Document Name</TableHead>
                      <TableHead>Stage</TableHead>
                      <TableHead>Mandatory</TableHead>
                      <TableHead className="w-[50px]"></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {documentFields.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={5} className="text-center py-8 text-muted-foreground">
                          No documents configured. Click "Add Document" to add to the checklist.
                        </TableCell>
                      </TableRow>
                    ) : (
                      documentFields.map((field, index) => (
                        <TableRow key={field.id}>
                          <TableCell>
                            <Select
                              value={watch(`documentChecklist.${index}.documentType`)}
                              onValueChange={(v) =>
                                setValue(`documentChecklist.${index}.documentType`, v)
                              }
                            >
                              <SelectTrigger className="w-[150px]">
                                <SelectValue placeholder="Select type" />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="KYC">KYC</SelectItem>
                                <SelectItem value="FINANCIAL">Financial</SelectItem>
                                <SelectItem value="LEGAL">Legal</SelectItem>
                                <SelectItem value="COLLATERAL">Collateral</SelectItem>
                                <SelectItem value="PROJECT">Project</SelectItem>
                                <SelectItem value="OTHER">Other</SelectItem>
                              </SelectContent>
                            </Select>
                          </TableCell>
                          <TableCell>
                            <Input
                              placeholder="Document name"
                              {...register(`documentChecklist.${index}.documentName`)}
                              className="w-[200px]"
                            />
                          </TableCell>
                          <TableCell>
                            <Select
                              value={watch(`documentChecklist.${index}.stage`)}
                              onValueChange={(v) =>
                                setValue(
                                  `documentChecklist.${index}.stage`,
                                  v as 'APPLICATION' | 'APPRAISAL' | 'SANCTION' | 'DISBURSEMENT'
                                )
                              }
                            >
                              <SelectTrigger className="w-[140px]">
                                <SelectValue placeholder="Stage" />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="APPLICATION">Application</SelectItem>
                                <SelectItem value="APPRAISAL">Appraisal</SelectItem>
                                <SelectItem value="SANCTION">Sanction</SelectItem>
                                <SelectItem value="DISBURSEMENT">Disbursement</SelectItem>
                              </SelectContent>
                            </Select>
                          </TableCell>
                          <TableCell>
                            <Switch
                              checked={watch(`documentChecklist.${index}.isMandatory`)}
                              onCheckedChange={(v) =>
                                setValue(`documentChecklist.${index}.isMandatory`, v)
                              }
                            />
                          </TableCell>
                          <TableCell>
                            <Button
                              type="button"
                              variant="ghost"
                              size="icon"
                              onClick={() => removeDocument(index)}
                            >
                              <Trash2 className="h-4 w-4 text-destructive" />
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))
                    )}
                  </TableBody>
                </Table>
                <Button
                  type="button"
                  variant="outline"
                  className="mt-4"
                  onClick={() =>
                    appendDocument({
                      documentType: 'KYC',
                      documentName: '',
                      isMandatory: false,
                      stage: 'APPLICATION',
                    })
                  }
                >
                  <Plus className="mr-2 h-4 w-4" />
                  Add Document
                </Button>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </form>
    </div>
  );
}
