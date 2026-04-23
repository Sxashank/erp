import { useState } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
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
import { AmountDisplay } from '@/components/lending/common/AmountDisplay';

import { logger } from '@/lib/logger';
const sanctionSchema = z.object({
  applicationId: z.string().min(1, 'Application is required'),
  sanctionedAmount: z.number().min(1, 'Sanctioned amount is required'),
  interestType: z.enum(['FIXED', 'FLOATING']),
  baseRate: z.string().optional(),
  spreadBps: z.number().optional(),
  fixedRate: z.number().optional(),
  effectiveRate: z.number().min(0),
  tenureMonths: z.number().min(1, 'Tenure is required'),
  moratoriumMonths: z.number().default(0),
  repaymentFrequency: z.enum(['MONTHLY', 'QUARTERLY', 'HALF_YEARLY', 'YEARLY', 'BULLET']),
  repaymentMode: z.enum(['EMI', 'STRUCTURED', 'BULLET']),
  processingFee: z.number().min(0),
  validityDays: z.number().min(1).default(90),
  conditions: z.array(
    z.object({
      conditionType: z.enum(['PRE_DISBURSEMENT', 'POST_DISBURSEMENT']),
      condition: z.string().min(1),
      isMandatory: z.boolean().default(true),
    })
  ),
  securities: z.array(
    z.object({
      securityType: z.enum(['PRIMARY', 'COLLATERAL']),
      nature: z.string(),
      description: z.string(),
      value: z.number().min(0),
      margin: z.number().min(0).max(100),
    })
  ),
  covenants: z.array(
    z.object({
      covenantType: z.string(),
      description: z.string(),
      frequency: z.enum(['MONTHLY', 'QUARTERLY', 'YEARLY', 'ONE_TIME']),
      threshold: z.string().optional(),
    })
  ),
  remarks: z.string().optional(),
});

type SanctionFormData = z.infer<typeof sanctionSchema>;

// Mock application data
const mockApplication = {
  id: '1',
  applicationNumber: 'SMFC/TL/DEL/2025/A00001',
  entityName: 'ABC Industries Private Limited',
  entityCode: 'ENT/2025/00001',
  productName: 'Corporate Term Loan',
  requestedAmount: 250000000,
  requestedTenureMonths: 60,
  purpose: 'Expansion of manufacturing facility',
};

const defaultValues: Partial<SanctionFormData> = {
  interestType: 'FLOATING',
  baseRate: 'SMFC_BR',
  spreadBps: 200,
  effectiveRate: 12.5,
  repaymentFrequency: 'MONTHLY',
  repaymentMode: 'EMI',
  processingFee: 2500000,
  validityDays: 90,
  moratoriumMonths: 0,
  conditions: [
    {
      conditionType: 'PRE_DISBURSEMENT',
      condition: 'Creation of mortgage on primary security',
      isMandatory: true,
    },
    {
      conditionType: 'PRE_DISBURSEMENT',
      condition: 'Submission of insurance policy for assets',
      isMandatory: true,
    },
    {
      conditionType: 'POST_DISBURSEMENT',
      condition: 'Submission of utilization certificate',
      isMandatory: true,
    },
  ],
  securities: [
    {
      securityType: 'PRIMARY',
      nature: 'PROPERTY',
      description: 'Industrial land and building',
      value: 400000000,
      margin: 25,
    },
  ],
  covenants: [
    {
      covenantType: 'FINANCIAL',
      description: 'Minimum DSCR to be maintained',
      frequency: 'YEARLY',
      threshold: '1.5x',
    },
    {
      covenantType: 'FINANCIAL',
      description: 'Maximum Debt-Equity ratio',
      frequency: 'YEARLY',
      threshold: '2:1',
    },
  ],
};

export default function SanctionForm() {
  const navigate = useNavigate();
  const { id } = useParams();
  const [searchParams] = useSearchParams();
  const applicationId = searchParams.get('applicationId');
  const isEdit = Boolean(id);
  const [activeTab, setActiveTab] = useState('terms');

  const {
    register,
    control,
    handleSubmit,
    watch,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<SanctionFormData>({
    resolver: zodResolver(sanctionSchema) as any,
    defaultValues: {
      ...defaultValues,
      applicationId: applicationId || '',
      sanctionedAmount: mockApplication.requestedAmount,
      tenureMonths: mockApplication.requestedTenureMonths,
    },
  });

  const {
    fields: conditionFields,
    append: appendCondition,
    remove: removeCondition,
  } = useFieldArray({
    control,
    name: 'conditions',
  });

  const {
    fields: securityFields,
    append: appendSecurity,
    remove: removeSecurity,
  } = useFieldArray({
    control,
    name: 'securities',
  });

  const {
    fields: covenantFields,
    append: appendCovenant,
    remove: removeCovenant,
  } = useFieldArray({
    control,
    name: 'covenants',
  });

  const interestType = watch('interestType');

  const onSubmit = async (data: SanctionFormData) => {
    logger.debug('Sanction data:', data);
    navigate('/admin/lending/sanctions');
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => navigate('/admin/lending/sanctions')}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div className="flex-1">
          <h1 className="text-2xl font-semibold">
            {isEdit ? 'Edit Sanction' : 'Create Sanction'}
          </h1>
          <p className="text-muted-foreground">
            Define sanction terms, conditions, and covenants for the loan
          </p>
        </div>
        <Button onClick={handleSubmit(onSubmit as any)} disabled={isSubmitting}>
          <Save className="mr-2 h-4 w-4" />
          {isEdit ? 'Update Sanction' : 'Create Sanction'}
        </Button>
      </div>

      {/* Application Summary */}
      <Card>
        <CardHeader>
          <CardTitle>Application Details</CardTitle>
          <CardDescription>Sanction for application {mockApplication.applicationNumber}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-4">
            <div>
              <dt className="text-sm font-medium text-muted-foreground">Entity</dt>
              <dd className="font-medium">{mockApplication.entityName}</dd>
              <dd className="text-sm text-muted-foreground">{mockApplication.entityCode}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-muted-foreground">Product</dt>
              <dd>{mockApplication.productName}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-muted-foreground">Requested Amount</dt>
              <dd>
                <AmountDisplay amount={mockApplication.requestedAmount} showFull />
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-muted-foreground">Requested Tenure</dt>
              <dd>{mockApplication.requestedTenureMonths} Months</dd>
            </div>
          </div>
        </CardContent>
      </Card>

      <form onSubmit={handleSubmit(onSubmit as any)}>
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="terms">Sanction Terms</TabsTrigger>
            <TabsTrigger value="conditions">Conditions</TabsTrigger>
            <TabsTrigger value="security">Security</TabsTrigger>
            <TabsTrigger value="covenants">Covenants</TabsTrigger>
          </TabsList>

          {/* Sanction Terms Tab */}
          <TabsContent value="terms" className="space-y-6 mt-6">
            <Card>
              <CardHeader>
                <CardTitle>Loan Amount & Tenure</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-4 md:grid-cols-3">
                  <div className="space-y-2">
                    <Label>Sanctioned Amount *</Label>
                    <AmountInput
                      value={watch('sanctionedAmount') || 0}
                      onChange={(v) => setValue('sanctionedAmount', v ?? 0)}
                      placeholder="Enter sanctioned amount"
                    />
                    {errors.sanctionedAmount && (
                      <p className="text-sm text-destructive">{errors.sanctionedAmount.message}</p>
                    )}
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="tenureMonths">Tenure (Months) *</Label>
                    <Input
                      id="tenureMonths"
                      type="number"
                      min={1}
                      {...register('tenureMonths', { valueAsNumber: true })}
                    />
                    {errors.tenureMonths && (
                      <p className="text-sm text-destructive">{errors.tenureMonths.message}</p>
                    )}
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="moratoriumMonths">Moratorium (Months)</Label>
                    <Input
                      id="moratoriumMonths"
                      type="number"
                      min={0}
                      {...register('moratoriumMonths', { valueAsNumber: true })}
                    />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Interest Configuration</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label>Interest Type *</Label>
                    <Select
                      value={interestType}
                      onValueChange={(v) =>
                        setValue('interestType', v as SanctionFormData['interestType'])
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
                </div>

                {interestType === 'FLOATING' ? (
                  <div className="grid gap-4 md:grid-cols-3">
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
                          <SelectItem value="SMFC_BR">SMFC Base Rate (10.50%)</SelectItem>
                          <SelectItem value="MCLR">MCLR (9.50%)</SelectItem>
                          <SelectItem value="REPO_LINKED">Repo Linked (6.50%)</SelectItem>
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
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="effectiveRate">Effective Rate (% p.a.)</Label>
                      <Input
                        id="effectiveRate"
                        type="number"
                        step="0.01"
                        {...register('effectiveRate', { valueAsNumber: true })}
                        readOnly
                        className="bg-muted"
                      />
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
                      className="w-[200px]"
                      {...register('fixedRate', { valueAsNumber: true })}
                    />
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Repayment Terms</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label>Repayment Frequency *</Label>
                    <Select
                      value={watch('repaymentFrequency')}
                      onValueChange={(v) =>
                        setValue('repaymentFrequency', v as SanctionFormData['repaymentFrequency'])
                      }
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select frequency" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="MONTHLY">Monthly</SelectItem>
                        <SelectItem value="QUARTERLY">Quarterly</SelectItem>
                        <SelectItem value="HALF_YEARLY">Half Yearly</SelectItem>
                        <SelectItem value="YEARLY">Yearly</SelectItem>
                        <SelectItem value="BULLET">Bullet</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label>Repayment Mode *</Label>
                    <Select
                      value={watch('repaymentMode')}
                      onValueChange={(v) =>
                        setValue('repaymentMode', v as SanctionFormData['repaymentMode'])
                      }
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select mode" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="EMI">EMI (Equated Monthly Installment)</SelectItem>
                        <SelectItem value="STRUCTURED">Structured Repayment</SelectItem>
                        <SelectItem value="BULLET">Bullet Payment</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Fees & Validity</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label>Processing Fee</Label>
                    <AmountInput
                      value={watch('processingFee') || 0}
                      onChange={(v) => setValue('processingFee', v ?? 0)}
                      placeholder="Processing fee amount"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="validityDays">Sanction Validity (Days)</Label>
                    <Input
                      id="validityDays"
                      type="number"
                      min={1}
                      className="w-[200px]"
                      {...register('validityDays', { valueAsNumber: true })}
                    />
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Conditions Tab */}
          <TabsContent value="conditions" className="space-y-6 mt-6">
            <Card>
              <CardHeader>
                <CardTitle>Pre-Disbursement Conditions</CardTitle>
                <CardDescription>
                  Conditions that must be satisfied before any disbursement
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-[50px]">#</TableHead>
                      <TableHead>Condition</TableHead>
                      <TableHead className="w-[120px]">Mandatory</TableHead>
                      <TableHead className="w-[50px]"></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {conditionFields
                      .filter((_, i) => watch(`conditions.${i}.conditionType`) === 'PRE_DISBURSEMENT')
                      .map((field, displayIndex) => {
                        const actualIndex = conditionFields.findIndex((f) => f.id === field.id);
                        return (
                          <TableRow key={field.id}>
                            <TableCell>{displayIndex + 1}</TableCell>
                            <TableCell>
                              <Textarea
                                {...register(`conditions.${actualIndex}.condition`)}
                                rows={2}
                                placeholder="Enter condition..."
                              />
                            </TableCell>
                            <TableCell>
                              <Switch
                                checked={watch(`conditions.${actualIndex}.isMandatory`)}
                                onCheckedChange={(v) =>
                                  setValue(`conditions.${actualIndex}.isMandatory`, v)
                                }
                              />
                            </TableCell>
                            <TableCell>
                              <Button
                                type="button"
                                variant="ghost"
                                size="icon"
                                onClick={() => removeCondition(actualIndex)}
                              >
                                <Trash2 className="h-4 w-4 text-destructive" />
                              </Button>
                            </TableCell>
                          </TableRow>
                        );
                      })}
                  </TableBody>
                </Table>
                <Button
                  type="button"
                  variant="outline"
                  className="mt-4"
                  onClick={() =>
                    appendCondition({
                      conditionType: 'PRE_DISBURSEMENT',
                      condition: '',
                      isMandatory: true,
                    })
                  }
                >
                  <Plus className="mr-2 h-4 w-4" />
                  Add Pre-Disbursement Condition
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Post-Disbursement Conditions</CardTitle>
                <CardDescription>
                  Conditions to be complied with after disbursement
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-[50px]">#</TableHead>
                      <TableHead>Condition</TableHead>
                      <TableHead className="w-[120px]">Mandatory</TableHead>
                      <TableHead className="w-[50px]"></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {conditionFields
                      .filter((_, i) => watch(`conditions.${i}.conditionType`) === 'POST_DISBURSEMENT')
                      .map((field, displayIndex) => {
                        const actualIndex = conditionFields.findIndex((f) => f.id === field.id);
                        return (
                          <TableRow key={field.id}>
                            <TableCell>{displayIndex + 1}</TableCell>
                            <TableCell>
                              <Textarea
                                {...register(`conditions.${actualIndex}.condition`)}
                                rows={2}
                                placeholder="Enter condition..."
                              />
                            </TableCell>
                            <TableCell>
                              <Switch
                                checked={watch(`conditions.${actualIndex}.isMandatory`)}
                                onCheckedChange={(v) =>
                                  setValue(`conditions.${actualIndex}.isMandatory`, v)
                                }
                              />
                            </TableCell>
                            <TableCell>
                              <Button
                                type="button"
                                variant="ghost"
                                size="icon"
                                onClick={() => removeCondition(actualIndex)}
                              >
                                <Trash2 className="h-4 w-4 text-destructive" />
                              </Button>
                            </TableCell>
                          </TableRow>
                        );
                      })}
                  </TableBody>
                </Table>
                <Button
                  type="button"
                  variant="outline"
                  className="mt-4"
                  onClick={() =>
                    appendCondition({
                      conditionType: 'POST_DISBURSEMENT',
                      condition: '',
                      isMandatory: true,
                    })
                  }
                >
                  <Plus className="mr-2 h-4 w-4" />
                  Add Post-Disbursement Condition
                </Button>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Security Tab */}
          <TabsContent value="security" className="mt-6">
            <Card>
              <CardHeader>
                <CardTitle>Security/Collateral Details</CardTitle>
                <CardDescription>
                  Define primary security and collateral for the loan
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Type</TableHead>
                      <TableHead>Nature</TableHead>
                      <TableHead>Description</TableHead>
                      <TableHead className="text-right">Value</TableHead>
                      <TableHead className="text-right">Margin %</TableHead>
                      <TableHead className="w-[50px]"></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {securityFields.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={6} className="text-center py-8 text-muted-foreground">
                          No security added. Click "Add Security" to add collateral.
                        </TableCell>
                      </TableRow>
                    ) : (
                      securityFields.map((field, index) => (
                        <TableRow key={field.id}>
                          <TableCell>
                            <Select
                              value={watch(`securities.${index}.securityType`)}
                              onValueChange={(v) =>
                                setValue(`securities.${index}.securityType`, v as 'PRIMARY' | 'COLLATERAL')
                              }
                            >
                              <SelectTrigger className="w-[130px]">
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="PRIMARY">Primary</SelectItem>
                                <SelectItem value="COLLATERAL">Collateral</SelectItem>
                              </SelectContent>
                            </Select>
                          </TableCell>
                          <TableCell>
                            <Select
                              value={watch(`securities.${index}.nature`)}
                              onValueChange={(v) => setValue(`securities.${index}.nature`, v)}
                            >
                              <SelectTrigger className="w-[150px]">
                                <SelectValue placeholder="Select nature" />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="PROPERTY">Property</SelectItem>
                                <SelectItem value="PLANT_MACHINERY">Plant & Machinery</SelectItem>
                                <SelectItem value="FIXED_DEPOSIT">Fixed Deposit</SelectItem>
                                <SelectItem value="RECEIVABLES">Receivables</SelectItem>
                                <SelectItem value="INVENTORY">Inventory</SelectItem>
                                <SelectItem value="GUARANTEE">Guarantee</SelectItem>
                              </SelectContent>
                            </Select>
                          </TableCell>
                          <TableCell>
                            <Input
                              {...register(`securities.${index}.description`)}
                              placeholder="Description"
                            />
                          </TableCell>
                          <TableCell className="text-right">
                            <Input
                              type="number"
                              {...register(`securities.${index}.value`, { valueAsNumber: true })}
                              placeholder="Value"
                              className="w-[150px]"
                            />
                          </TableCell>
                          <TableCell className="text-right">
                            <Input
                              type="number"
                              {...register(`securities.${index}.margin`, { valueAsNumber: true })}
                              placeholder="%"
                              className="w-[80px]"
                            />
                          </TableCell>
                          <TableCell>
                            <Button
                              type="button"
                              variant="ghost"
                              size="icon"
                              onClick={() => removeSecurity(index)}
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
                    appendSecurity({
                      securityType: 'PRIMARY',
                      nature: '',
                      description: '',
                      value: 0,
                      margin: 0,
                    })
                  }
                >
                  <Plus className="mr-2 h-4 w-4" />
                  Add Security
                </Button>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Covenants Tab */}
          <TabsContent value="covenants" className="mt-6">
            <Card>
              <CardHeader>
                <CardTitle>Financial & Other Covenants</CardTitle>
                <CardDescription>
                  Define covenants that the borrower must comply with
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Covenant Type</TableHead>
                      <TableHead>Description</TableHead>
                      <TableHead>Frequency</TableHead>
                      <TableHead>Threshold</TableHead>
                      <TableHead className="w-[50px]"></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {covenantFields.length === 0 ? (
                      <TableRow>
                        <TableCell colSpan={5} className="text-center py-8 text-muted-foreground">
                          No covenants added. Click "Add Covenant" to define covenants.
                        </TableCell>
                      </TableRow>
                    ) : (
                      covenantFields.map((field, index) => (
                        <TableRow key={field.id}>
                          <TableCell>
                            <Select
                              value={watch(`covenants.${index}.covenantType`)}
                              onValueChange={(v) => setValue(`covenants.${index}.covenantType`, v)}
                            >
                              <SelectTrigger className="w-[130px]">
                                <SelectValue placeholder="Type" />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="FINANCIAL">Financial</SelectItem>
                                <SelectItem value="REPORTING">Reporting</SelectItem>
                                <SelectItem value="OPERATIONAL">Operational</SelectItem>
                                <SelectItem value="NEGATIVE">Negative</SelectItem>
                              </SelectContent>
                            </Select>
                          </TableCell>
                          <TableCell>
                            <Input
                              {...register(`covenants.${index}.description`)}
                              placeholder="Covenant description"
                            />
                          </TableCell>
                          <TableCell>
                            <Select
                              value={watch(`covenants.${index}.frequency`)}
                              onValueChange={(v) =>
                                setValue(
                                  `covenants.${index}.frequency`,
                                  v as 'MONTHLY' | 'QUARTERLY' | 'YEARLY' | 'ONE_TIME'
                                )
                              }
                            >
                              <SelectTrigger className="w-[120px]">
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="MONTHLY">Monthly</SelectItem>
                                <SelectItem value="QUARTERLY">Quarterly</SelectItem>
                                <SelectItem value="YEARLY">Yearly</SelectItem>
                                <SelectItem value="ONE_TIME">One Time</SelectItem>
                              </SelectContent>
                            </Select>
                          </TableCell>
                          <TableCell>
                            <Input
                              {...register(`covenants.${index}.threshold`)}
                              placeholder="e.g., 1.5x, 2:1"
                              className="w-[100px]"
                            />
                          </TableCell>
                          <TableCell>
                            <Button
                              type="button"
                              variant="ghost"
                              size="icon"
                              onClick={() => removeCovenant(index)}
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
                    appendCovenant({
                      covenantType: 'FINANCIAL',
                      description: '',
                      frequency: 'YEARLY',
                      threshold: '',
                    })
                  }
                >
                  <Plus className="mr-2 h-4 w-4" />
                  Add Covenant
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Additional Remarks</CardTitle>
              </CardHeader>
              <CardContent>
                <Textarea
                  {...register('remarks')}
                  placeholder="Any additional remarks or special conditions..."
                  rows={4}
                />
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </form>
    </div>
  );
}
