import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, Edit, FileText, Settings } from 'lucide-react';
import { Button } from '@/components/ui/button';
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
import { Badge } from '@/components/ui/badge';
import { StatusBadge } from '@/components/lending/common/StatusBadge';
import { AmountDisplay } from '@/components/lending/common/AmountDisplay';
import { PercentageDisplay } from '@/components/lending/common/PercentageDisplay';

// Mock product data
const mockProduct = {
  id: '1',
  productCode: 'TL-CORP-001',
  productName: 'Corporate Term Loan',
  description:
    'Term loan facility for established corporate entities with proven track record. Suitable for capex, working capital, and business expansion.',
  category: 'TERM_LOAN',
  subCategory: 'CORPORATE',
  minAmount: 10000000,
  maxAmount: 5000000000,
  minTenureMonths: 12,
  maxTenureMonths: 120,
  interestType: 'FLOATING',
  baseRate: 'SMFC_BR',
  currentBaseRate: 10.5,
  spreadBps: 200,
  effectiveRate: 12.5,
  processingFeePercent: 1.0,
  processingFeeMin: 100000,
  processingFeeMax: 5000000,
  prepaymentAllowed: true,
  prepaymentChargePercent: 2.0,
  prepaymentLockInMonths: 12,
  moratoriumAllowed: true,
  maxMoratoriumMonths: 6,
  repaymentFrequency: ['MONTHLY', 'QUARTERLY'],
  dayCountConvention: 'ACT_365',
  status: 'ACTIVE',
  fees: [
    {
      feeType: 'DOCUMENTATION',
      feeName: 'Documentation Charges',
      chargeType: 'FIXED',
      fixedAmount: 50000,
      isMandatory: true,
    },
    {
      feeType: 'LEGAL',
      feeName: 'Legal & Vetting Charges',
      chargeType: 'FIXED',
      fixedAmount: 100000,
      isMandatory: true,
    },
    {
      feeType: 'VALUATION',
      feeName: 'Property Valuation',
      chargeType: 'FIXED',
      fixedAmount: 25000,
      isMandatory: false,
    },
  ],
  documentChecklist: [
    { documentType: 'KYC', documentName: 'PAN Card', stage: 'APPLICATION', isMandatory: true },
    {
      documentType: 'KYC',
      documentName: 'Certificate of Incorporation',
      stage: 'APPLICATION',
      isMandatory: true,
    },
    {
      documentType: 'KYC',
      documentName: 'MOA & AOA',
      stage: 'APPLICATION',
      isMandatory: true,
    },
    {
      documentType: 'FINANCIAL',
      documentName: 'Audited Financials (3 years)',
      stage: 'APPRAISAL',
      isMandatory: true,
    },
    {
      documentType: 'FINANCIAL',
      documentName: 'ITR (3 years)',
      stage: 'APPRAISAL',
      isMandatory: true,
    },
    {
      documentType: 'FINANCIAL',
      documentName: 'Bank Statements (12 months)',
      stage: 'APPRAISAL',
      isMandatory: true,
    },
    {
      documentType: 'COLLATERAL',
      documentName: 'Property Documents',
      stage: 'SANCTION',
      isMandatory: true,
    },
    {
      documentType: 'LEGAL',
      documentName: 'Board Resolution',
      stage: 'DISBURSEMENT',
      isMandatory: true,
    },
    {
      documentType: 'LEGAL',
      documentName: 'Signed Loan Agreement',
      stage: 'DISBURSEMENT',
      isMandatory: true,
    },
  ],
  createdAt: '2025-01-01',
  updatedAt: '2025-01-10',
};

const dayCountLabels: Record<string, string> = {
  ACT_365: 'Actual/365',
  ACT_360: 'Actual/360',
  THIRTY_360: '30/360',
};

const categoryLabels: Record<string, string> = {
  TERM_LOAN: 'Term Loan',
  WORKING_CAPITAL: 'Working Capital',
  PROJECT_FINANCE: 'Project Finance',
  LAP: 'Loan Against Property',
  EQUIPMENT_FINANCE: 'Equipment Finance',
  BILL_DISCOUNTING: 'Bill Discounting',
};

export default function ProductView() {
  const navigate = useNavigate();
  const { id } = useParams();
  const product = mockProduct; // Would fetch from API based on id

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => navigate('/admin/lending/products')}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-semibold">{product.productName}</h1>
            <StatusBadge status={product.status} type="product" />
          </div>
          <p className="text-muted-foreground font-mono">{product.productCode}</p>
        </div>
        <Button variant="outline" onClick={() => navigate(`/admin/lending/products/${id}/edit`)}>
          <Edit className="mr-2 h-4 w-4" />
          Edit Product
        </Button>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Amount Range</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-1 text-lg font-semibold">
              <AmountDisplay amount={product.minAmount} abbreviated /> -{' '}
              <AmountDisplay amount={product.maxAmount} abbreviated />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Tenure</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-lg font-semibold">
              {product.minTenureMonths} - {product.maxTenureMonths} Months
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Effective Rate
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-lg font-semibold">
              <PercentageDisplay value={product.effectiveRate} /> p.a.
            </div>
            <p className="text-xs text-muted-foreground">
              {product.baseRate} + {product.spreadBps} bps
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Processing Fee
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-lg font-semibold">
              <PercentageDisplay value={product.processingFeePercent} />
            </div>
            <p className="text-xs text-muted-foreground">
              Min: <AmountDisplay amount={product.processingFeeMin} abbreviated /> | Max:{' '}
              <AmountDisplay amount={product.processingFeeMax} abbreviated />
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="details">
        <TabsList>
          <TabsTrigger value="details">Product Details</TabsTrigger>
          <TabsTrigger value="interest">Interest & Terms</TabsTrigger>
          <TabsTrigger value="fees">Fee Structure</TabsTrigger>
          <TabsTrigger value="documents">Document Checklist</TabsTrigger>
        </TabsList>

        {/* Details Tab */}
        <TabsContent value="details" className="space-y-6 mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Basic Information</CardTitle>
            </CardHeader>
            <CardContent>
              <dl className="grid gap-4 md:grid-cols-2">
                <div>
                  <dt className="text-sm font-medium text-muted-foreground">Product Code</dt>
                  <dd className="font-mono">{product.productCode}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-muted-foreground">Product Name</dt>
                  <dd>{product.productName}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-muted-foreground">Category</dt>
                  <dd>
                    <Badge variant="outline">{categoryLabels[product.category]}</Badge>
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-muted-foreground">Sub Category</dt>
                  <dd>{product.subCategory}</dd>
                </div>
                <div className="md:col-span-2">
                  <dt className="text-sm font-medium text-muted-foreground">Description</dt>
                  <dd className="text-sm">{product.description}</dd>
                </div>
              </dl>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Amount & Tenure Limits</CardTitle>
            </CardHeader>
            <CardContent>
              <dl className="grid gap-4 md:grid-cols-2">
                <div>
                  <dt className="text-sm font-medium text-muted-foreground">Minimum Amount</dt>
                  <dd>
                    <AmountDisplay amount={product.minAmount} showFull />
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-muted-foreground">Maximum Amount</dt>
                  <dd>
                    <AmountDisplay amount={product.maxAmount} showFull />
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-muted-foreground">Minimum Tenure</dt>
                  <dd>{product.minTenureMonths} Months</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-muted-foreground">Maximum Tenure</dt>
                  <dd>{product.maxTenureMonths} Months</dd>
                </div>
              </dl>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Interest & Terms Tab */}
        <TabsContent value="interest" className="space-y-6 mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Interest Configuration</CardTitle>
            </CardHeader>
            <CardContent>
              <dl className="grid gap-4 md:grid-cols-2">
                <div>
                  <dt className="text-sm font-medium text-muted-foreground">Interest Type</dt>
                  <dd>
                    <Badge variant={product.interestType === 'FLOATING' ? 'default' : 'secondary'}>
                      {product.interestType}
                    </Badge>
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-muted-foreground">Day Count Convention</dt>
                  <dd>{dayCountLabels[product.dayCountConvention]}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-muted-foreground">Base Rate</dt>
                  <dd>
                    {product.baseRate} @ <PercentageDisplay value={product.currentBaseRate} />
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-muted-foreground">Spread</dt>
                  <dd>{product.spreadBps} bps ({(product.spreadBps / 100).toFixed(2)}%)</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-muted-foreground">Effective Rate</dt>
                  <dd className="text-lg font-semibold">
                    <PercentageDisplay value={product.effectiveRate} /> p.a.
                  </dd>
                </div>
              </dl>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Repayment Terms</CardTitle>
            </CardHeader>
            <CardContent>
              <dl className="grid gap-4 md:grid-cols-2">
                <div>
                  <dt className="text-sm font-medium text-muted-foreground">
                    Repayment Frequencies
                  </dt>
                  <dd className="flex gap-2">
                    {product.repaymentFrequency.map((freq) => (
                      <Badge key={freq} variant="outline">
                        {freq}
                      </Badge>
                    ))}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-muted-foreground">Moratorium</dt>
                  <dd>
                    {product.moratoriumAllowed
                      ? `Up to ${product.maxMoratoriumMonths} months`
                      : 'Not Allowed'}
                  </dd>
                </div>
              </dl>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Prepayment Terms</CardTitle>
            </CardHeader>
            <CardContent>
              <dl className="grid gap-4 md:grid-cols-2">
                <div>
                  <dt className="text-sm font-medium text-muted-foreground">Prepayment</dt>
                  <dd>
                    <Badge variant={product.prepaymentAllowed ? 'default' : 'secondary'}>
                      {product.prepaymentAllowed ? 'Allowed' : 'Not Allowed'}
                    </Badge>
                  </dd>
                </div>
                {product.prepaymentAllowed && (
                  <>
                    <div>
                      <dt className="text-sm font-medium text-muted-foreground">Lock-in Period</dt>
                      <dd>{product.prepaymentLockInMonths} months</dd>
                    </div>
                    <div>
                      <dt className="text-sm font-medium text-muted-foreground">
                        Prepayment Charge
                      </dt>
                      <dd>
                        <PercentageDisplay value={product.prepaymentChargePercent} /> of prepaid
                        amount
                      </dd>
                    </div>
                  </>
                )}
              </dl>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Fee Structure Tab */}
        <TabsContent value="fees" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Fee Structure</CardTitle>
              <CardDescription>
                Additional fees applicable to this product
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Fee Type</TableHead>
                    <TableHead>Fee Name</TableHead>
                    <TableHead>Charge Type</TableHead>
                    <TableHead className="text-right">Amount/Rate</TableHead>
                    <TableHead>Mandatory</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {/* Processing Fee */}
                  <TableRow>
                    <TableCell className="font-medium">PROCESSING</TableCell>
                    <TableCell>Processing Fee</TableCell>
                    <TableCell>Percentage</TableCell>
                    <TableCell className="text-right">
                      <PercentageDisplay value={product.processingFeePercent} />
                    </TableCell>
                    <TableCell>
                      <Badge>Mandatory</Badge>
                    </TableCell>
                  </TableRow>
                  {/* Other Fees */}
                  {product.fees.map((fee, index) => (
                    <TableRow key={index}>
                      <TableCell className="font-medium">{fee.feeType}</TableCell>
                      <TableCell>{fee.feeName}</TableCell>
                      <TableCell>{fee.chargeType}</TableCell>
                      <TableCell className="text-right">
                        {fee.chargeType === 'PERCENTAGE' ? (
                          <PercentageDisplay value={(fee as any).percentage || 0} />
                        ) : (
                          <AmountDisplay amount={fee.fixedAmount || 0} />
                        )}
                      </TableCell>
                      <TableCell>
                        <Badge variant={fee.isMandatory ? 'default' : 'outline'}>
                          {fee.isMandatory ? 'Mandatory' : 'Optional'}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Document Checklist Tab */}
        <TabsContent value="documents" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Document Checklist</CardTitle>
              <CardDescription>
                Required documents at each stage of the loan process
              </CardDescription>
            </CardHeader>
            <CardContent>
              {['APPLICATION', 'APPRAISAL', 'SANCTION', 'DISBURSEMENT'].map((stage) => {
                const stageDocs = product.documentChecklist.filter((doc) => doc.stage === stage);
                if (stageDocs.length === 0) return null;

                return (
                  <div key={stage} className="mb-6 last:mb-0">
                    <h4 className="font-medium mb-3 flex items-center gap-2">
                      <FileText className="h-4 w-4" />
                      {stage.charAt(0) + stage.slice(1).toLowerCase()} Stage
                      <Badge variant="outline" className="ml-2">
                        {stageDocs.length} documents
                      </Badge>
                    </h4>
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Document Type</TableHead>
                          <TableHead>Document Name</TableHead>
                          <TableHead>Requirement</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {stageDocs.map((doc, index) => (
                          <TableRow key={index}>
                            <TableCell>
                              <Badge variant="outline">{doc.documentType}</Badge>
                            </TableCell>
                            <TableCell>{doc.documentName}</TableCell>
                            <TableCell>
                              <Badge variant={doc.isMandatory ? 'default' : 'secondary'}>
                                {doc.isMandatory ? 'Mandatory' : 'Optional'}
                              </Badge>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                );
              })}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
