/**
 * ESS IT Declaration Page
 * Manage tax declarations and investments
 */

import {
  Calculator,
  Plus,
  Loader2,
  FileText,
  Home,
  Send,
  IndianRupee,
  Info,
  CheckCircle,
  Clock,
  AlertTriangle,
} from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { PageHeader } from '@/components/common/PageHeader';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { logger } from '@/lib/logger';
import { essITDeclarationApi } from '@/services/essApi';
import { useEssAuthStore } from '@/stores/essAuthStore';
import type { ITDeclaration, ITDeclarationSection, TaxCalculation } from '@/types/ess';

function getCurrentIndianFinancialYear() {
  const today = new Date();
  const startYear = today.getMonth() >= 3 ? today.getFullYear() : today.getFullYear() - 1;
  const endYear = String((startYear + 1) % 100).padStart(2, '0');
  return `${startYear}-${endYear}`;
}

export default function ESSITDeclarationPage() {
  const navigate = useNavigate();
  const accessToken = useEssAuthStore((state) => state.accessToken);
  const [loading, setLoading] = useState(true);
  const [declaration, setDeclaration] = useState<ITDeclaration | null>(null);
  const [sections, setSections] = useState<ITDeclarationSection[]>([]);
  const [taxCalculation, setTaxCalculation] = useState<TaxCalculation | null>(null);
  const [addItemDialogOpen, setAddItemDialogOpen] = useState(false);
  const [selectedSection, setSelectedSection] = useState<ITDeclarationSection | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const currentFY = getCurrentIndianFinancialYear();

  const fetchData = useCallback(async () => {
    try {
      const [declRes, sectionsRes] = await Promise.all([
        essITDeclarationApi.getDeclaration(currentFY),
        essITDeclarationApi.getSections(currentFY),
      ]);
      setDeclaration(declRes.data);
      setSections(sectionsRes.data || []);

      if (declRes.data?.id) {
        const taxRes = await essITDeclarationApi.calculateTax(declRes.data.id);
        setTaxCalculation(taxRes.data);
      }
    } catch (error) {
      logger.error('Failed to fetch data:', error);
    } finally {
      setLoading(false);
    }
  }, [currentFY]);

  useEffect(() => {
    if (!accessToken) {
      navigate('/ess/login');
      return;
    }
    void fetchData();
  }, [accessToken, fetchData, navigate]);

  const handleAddItem = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!declaration || !selectedSection) return;

    const formData = new FormData(e.currentTarget);
    setSubmitting(true);
    try {
      await essITDeclarationApi.addItem(declaration.id, {
        section_code: selectedSection.section_code,
        particular: formData.get('particular') as string,
        declared_amount: Number(formData.get('declared_amount')),
        investment_date: (formData.get('investment_date') as string) || undefined,
        policy_number: (formData.get('policy_number') as string) || undefined,
        institution_name: (formData.get('institution_name') as string) || undefined,
      });
      setAddItemDialogOpen(false);
      setSelectedSection(null);
      void fetchData();
    } catch (error) {
      logger.error('Failed to add item:', error);
    } finally {
      setSubmitting(false);
    }
  };

  const handleSubmitDeclaration = async () => {
    if (!declaration) return;
    try {
      await essITDeclarationApi.submitDeclaration(declaration.id);
      void fetchData();
    } catch (error) {
      logger.error('Failed to submit declaration:', error);
    }
  };
  const getStatusBadge = (status: string) => {
    const styles: Record<string, { bg: string; icon: typeof Clock }> = {
      DRAFT: { bg: 'bg-gray-100 text-gray-700', icon: FileText },
      SUBMITTED: { bg: 'bg-blue-100 text-blue-700', icon: Clock },
      VERIFIED: { bg: 'bg-green-100 text-green-700', icon: CheckCircle },
      APPROVED: { bg: 'bg-emerald-100 text-emerald-700', icon: CheckCircle },
      REJECTED: { bg: 'bg-red-100 text-red-700', icon: AlertTriangle },
    };
    const style = styles[status] || styles.DRAFT;
    const Icon = style.icon;
    return (
      <Badge className={style.bg}>
        <Icon className="mr-1 h-3 w-3" />
        {status}
      </Badge>
    );
  };

  const groupSectionsByCategory = () => {
    const grouped: Record<string, ITDeclarationSection[]> = {};
    sections.forEach((section) => {
      const category = section.category || 'Other';
      if (!grouped[category]) grouped[category] = [];
      grouped[category].push(section);
    });
    return grouped;
  };

  const getSectionTotal = (sectionCode: string) => {
    return (
      declaration?.items
        .filter((item) => item.section_code === sectionCode)
        .reduce((sum, item) => sum + item.declared_amount, 0) || 0
    );
  };

  if (loading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  const groupedSections = groupSectionsByCategory();

  return (
    <div className="space-y-6">
      <PageHeader
        title="IT Declaration"
        subtitle={`Financial Year ${currentFY}`}
        actions={
          declaration?.status === 'DRAFT' ? (
            <Button onClick={handleSubmitDeclaration}>
              <Send className="mr-2 h-4 w-4" />
              Submit Declaration
            </Button>
          ) : undefined
        }
      />

      {/* Status & Summary */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="p-4">
            <div className="mb-2 flex items-center justify-between">
              <span className="text-sm text-gray-500">Status</span>
              {declaration && getStatusBadge(declaration.status)}
            </div>
            <p className="text-sm text-gray-500">Tax Regime</p>
            <p className="font-medium">
              {declaration?.tax_regime === 'OLD' ? 'Old Regime' : 'New Regime'}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="mb-2 flex items-center gap-2">
              <IndianRupee className="h-4 w-4 text-blue-600" />
              <span className="text-sm text-gray-500">Total Declared</span>
            </div>
            <p className="text-xl font-bold">
              {formatIndianCompactCurrency(declaration?.total_declared_amount || 0)}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="mb-2 flex items-center gap-2">
              <Calculator className="h-4 w-4 text-purple-600" />
              <span className="text-sm text-gray-500">Est. Tax Liability</span>
            </div>
            <p className="text-xl font-bold">
              {formatIndianCompactCurrency(taxCalculation?.total_tax_liability || 0)}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="mb-2 flex items-center gap-2">
              <Calculator className="h-4 w-4 text-green-600" />
              <span className="text-sm text-gray-500">Monthly TDS</span>
            </div>
            <p className="text-xl font-bold">
              {formatIndianCompactCurrency(taxCalculation?.monthly_tds || 0)}
            </p>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="investments" className="space-y-6">
        <TabsList>
          <TabsTrigger value="investments">Investments & Deductions</TabsTrigger>
          <TabsTrigger value="hra">HRA Details</TabsTrigger>
          <TabsTrigger value="homeloan">Home Loan</TabsTrigger>
          <TabsTrigger value="taxcalc">Tax Calculation</TabsTrigger>
        </TabsList>

        <TabsContent value="investments">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Investment Declarations</CardTitle>
              <CardDescription>Add your investments under various sections</CardDescription>
            </CardHeader>
            <CardContent>
              <Accordion type="multiple" className="space-y-2">
                {Object.entries(groupedSections).map(([category, categorySections]) => (
                  <AccordionItem key={category} value={category} className="rounded-lg border px-4">
                    <AccordionTrigger className="hover:no-underline">
                      <div className="mr-4 flex w-full items-center justify-between">
                        <span className="font-medium">{category}</span>
                        <span className="text-sm text-gray-500">
                          {categorySections.length} sections
                        </span>
                      </div>
                    </AccordionTrigger>
                    <AccordionContent>
                      <div className="space-y-4 pt-2">
                        {categorySections.map((section) => {
                          const sectionTotal = getSectionTotal(section.section_code);
                          const progress =
                            section.max_limit > 0
                              ? Math.min((sectionTotal / section.max_limit) * 100, 100)
                              : 0;
                          const sectionItems =
                            declaration?.items.filter(
                              (item) => item.section_code === section.section_code,
                            ) || [];

                          return (
                            <div key={section.id} className="rounded-lg bg-gray-50 p-4">
                              <div className="mb-2 flex items-start justify-between">
                                <div>
                                  <div className="flex items-center gap-2">
                                    <span className="font-medium">{section.section_code}</span>
                                    <span className="text-sm text-gray-600">
                                      {section.section_name}
                                    </span>
                                  </div>
                                  {section.help_text && (
                                    <p className="mt-1 text-xs text-gray-500">
                                      {section.help_text}
                                    </p>
                                  )}
                                </div>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => {
                                    setSelectedSection(section);
                                    setAddItemDialogOpen(true);
                                  }}
                                  disabled={declaration?.status !== 'DRAFT'}
                                >
                                  <Plus className="mr-1 h-3 w-3" />
                                  Add
                                </Button>
                              </div>

                              {section.max_limit > 0 && (
                                <div className="mb-3">
                                  <div className="mb-1 flex justify-between text-xs text-gray-500">
                                    <span>
                                      Declared: {formatIndianCompactCurrency(sectionTotal)}
                                    </span>
                                    <span>
                                      Limit: {formatIndianCompactCurrency(section.max_limit)}
                                    </span>
                                  </div>
                                  <Progress value={progress} className="h-2" />
                                </div>
                              )}

                              {sectionItems.length > 0 && (
                                <div className="mt-3 space-y-2">
                                  {sectionItems.map((item) => (
                                    <div
                                      key={item.id}
                                      className="flex items-center justify-between rounded border bg-white p-2"
                                    >
                                      <div>
                                        <p className="text-sm font-medium">{item.particular}</p>
                                        {item.institution_name && (
                                          <p className="text-xs text-gray-500">
                                            {item.institution_name}
                                          </p>
                                        )}
                                      </div>
                                      <div className="text-right">
                                        <p className="font-medium">
                                          {formatIndianCompactCurrency(item.declared_amount)}
                                        </p>
                                        {item.is_verified && (
                                          <Badge
                                            variant="secondary"
                                            className="bg-green-100 text-xs text-green-700"
                                          >
                                            Verified
                                          </Badge>
                                        )}
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    </AccordionContent>
                  </AccordionItem>
                ))}
              </Accordion>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="hra">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <Home className="h-4 w-4" />
                HRA Exemption Details
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
                <div>
                  <Label>Monthly Rent</Label>
                  <p className="text-lg font-medium">
                    {formatIndianCompactCurrency(declaration?.rent_paid_monthly || 0)}
                  </p>
                </div>
                <div>
                  <Label>Landlord Name</Label>
                  <p className="font-medium">{declaration?.landlord_name || '-'}</p>
                </div>
                <div>
                  <Label>Landlord PAN</Label>
                  <p className="font-medium">{declaration?.landlord_pan || '-'}</p>
                </div>
                <div>
                  <Label>Metro City</Label>
                  <p className="font-medium">{declaration?.metro_city ? 'Yes' : 'No'}</p>
                </div>
              </div>

              <div className="rounded-lg bg-green-50 p-4">
                <p className="text-sm text-gray-600">Estimated HRA Exemption</p>
                <p className="text-2xl font-bold text-green-700">
                  {formatIndianCompactCurrency(declaration?.hra_declared || 0)}
                </p>
              </div>

              {/* Monthly Receipts */}
              {declaration?.hra_receipts && declaration.hra_receipts.length > 0 && (
                <div>
                  <Label className="mb-2 block">Monthly Rent Receipts</Label>
                  <div className="grid grid-cols-3 gap-2 md:grid-cols-6">
                    {declaration.hra_receipts.map((receipt) => (
                      <div
                        key={receipt.id}
                        className={`rounded border p-2 text-center ${
                          receipt.receipt_uploaded ? 'border-green-200 bg-green-50' : 'bg-gray-50'
                        }`}
                      >
                        <p className="text-xs text-gray-500">{receipt.month}</p>
                        <p className="text-sm font-medium">
                          {formatIndianCompactCurrency(receipt.rent_amount)}
                        </p>
                        {receipt.receipt_uploaded && (
                          <CheckCircle className="mx-auto mt-1 h-3 w-3 text-green-600" />
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="homeloan">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Home Loan Interest (Section 24b)</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4 md:grid-cols-3">
                <div>
                  <Label>Interest Paid (Annual)</Label>
                  <p className="text-lg font-medium">
                    {formatIndianCompactCurrency(declaration?.home_loan_interest || 0)}
                  </p>
                </div>
                <div>
                  <Label>Principal Paid (Annual)</Label>
                  <p className="text-lg font-medium">
                    {formatIndianCompactCurrency(declaration?.home_loan_principal || 0)}
                  </p>
                </div>
                <div>
                  <Label>Lender Name</Label>
                  <p className="font-medium">{declaration?.lender_name || '-'}</p>
                </div>
              </div>

              <div className="rounded-lg bg-blue-50 p-4">
                <div className="mb-2 flex items-center gap-2">
                  <Info className="h-4 w-4 text-blue-600" />
                  <span className="text-sm font-medium text-blue-700">Deduction Limits</span>
                </div>
                <ul className="space-y-1 text-sm text-gray-600">
                  <li>• Self-occupied property: Max ₹2,00,000 interest deduction (Section 24b)</li>
                  <li>• Principal repayment: Included in 80C limit (₹1,50,000)</li>
                  <li>
                    • First-time buyer (80EE): Additional ₹50,000 if loan ≤ ₹35L, property ≤ ₹50L
                  </li>
                </ul>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="taxcalc">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Tax Calculation Summary</CardTitle>
              <CardDescription>Based on your declarations</CardDescription>
            </CardHeader>
            <CardContent>
              {taxCalculation ? (
                <div className="space-y-6">
                  <div className="grid grid-cols-2 gap-4 md:grid-cols-3">
                    <div className="rounded-lg bg-gray-50 p-4">
                      <p className="text-sm text-gray-500">Gross Income</p>
                      <p className="text-xl font-bold">
                        {formatIndianCompactCurrency(taxCalculation.gross_income)}
                      </p>
                    </div>
                    <div className="rounded-lg bg-green-50 p-4">
                      <p className="text-sm text-gray-500">Total Deductions</p>
                      <p className="text-xl font-bold text-green-700">
                        -
                        {formatIndianCompactCurrency(
                          taxCalculation.chapter_vi_a_deductions +
                            taxCalculation.standard_deduction,
                        )}
                      </p>
                    </div>
                    <div className="rounded-lg bg-blue-50 p-4">
                      <p className="text-sm text-gray-500">Taxable Income</p>
                      <p className="text-xl font-bold">
                        {formatIndianCompactCurrency(taxCalculation.taxable_income)}
                      </p>
                    </div>
                  </div>

                  {/* Tax Slabs */}
                  <div>
                    <h4 className="mb-3 font-medium">Tax Computation</h4>
                    <div className="space-y-2">
                      {taxCalculation.breakdown?.tax_slabs?.map((slab, idx) => (
                        <div key={idx} className="flex justify-between rounded bg-gray-50 p-2">
                          <span className="text-sm">
                            {slab.slab} @ {slab.rate}%
                          </span>
                          <span className="font-medium">
                            {formatIndianCompactCurrency(slab.tax)}
                          </span>
                        </div>
                      ))}
                      <div className="flex justify-between rounded bg-gray-100 p-2">
                        <span>Tax on Income</span>
                        <span className="font-medium">
                          {formatIndianCompactCurrency(taxCalculation.tax_on_income)}
                        </span>
                      </div>
                      {taxCalculation.surcharge > 0 && (
                        <div className="flex justify-between p-2">
                          <span className="text-sm text-gray-600">Surcharge</span>
                          <span>{formatIndianCompactCurrency(taxCalculation.surcharge)}</span>
                        </div>
                      )}
                      <div className="flex justify-between p-2">
                        <span className="text-sm text-gray-600">Education Cess (4%)</span>
                        <span>{formatIndianCompactCurrency(taxCalculation.education_cess)}</span>
                      </div>
                      <div className="flex justify-between rounded bg-red-50 p-3 font-bold">
                        <span>Total Tax Liability</span>
                        <span className="text-red-700">
                          {formatIndianCompactCurrency(taxCalculation.total_tax_liability)}
                        </span>
                      </div>
                      <div className="flex justify-between rounded bg-blue-50 p-3">
                        <span className="font-medium">Monthly TDS</span>
                        <span className="font-bold text-blue-700">
                          {formatIndianCompactCurrency(taxCalculation.monthly_tds)}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="py-8 text-center text-gray-500">
                  <Calculator className="mx-auto mb-2 h-8 w-8 opacity-50" />
                  <p>Tax calculation will be available after adding declarations</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Add Item Dialog */}
      <Dialog open={addItemDialogOpen} onOpenChange={setAddItemDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add Investment - {selectedSection?.section_code}</DialogTitle>
            <DialogDescription>{selectedSection?.section_name}</DialogDescription>
          </DialogHeader>
          <form onSubmit={handleAddItem} className="space-y-4">
            <div>
              <Label htmlFor="particular">Particular/Description</Label>
              <Input
                id="particular"
                name="particular"
                placeholder="e.g., LIC Policy, PPF, ELSS Fund"
                required
              />
            </div>
            <div>
              <Label htmlFor="declared_amount">Amount (₹)</Label>
              <Input
                id="declared_amount"
                name="declared_amount"
                type="number"
                placeholder="Enter amount"
                required
              />
            </div>
            <div>
              <Label htmlFor="institution_name">Institution/Company Name</Label>
              <Input
                id="institution_name"
                name="institution_name"
                placeholder="e.g., LIC, SBI, HDFC"
              />
            </div>
            <div>
              <Label htmlFor="policy_number">Policy/Account Number</Label>
              <Input id="policy_number" name="policy_number" placeholder="Enter reference number" />
            </div>
            <div>
              <Label htmlFor="investment_date">Investment Date</Label>
              <Input id="investment_date" name="investment_date" type="date" />
            </div>
            <div className="flex justify-end gap-3">
              <Button type="button" variant="outline" onClick={() => setAddItemDialogOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={submitting}>
                {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Add Investment
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
