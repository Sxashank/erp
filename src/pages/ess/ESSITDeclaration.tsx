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
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

import { PageHeader } from '@/components/common/PageHeader';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Progress } from '@/components/ui/progress';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { essITDeclarationApi } from '@/services/essApi';
import { useEssAuthStore } from '@/stores/essAuthStore';
import type { ITDeclaration, ITDeclarationSection, ITDeclarationItem, TaxCalculation } from '@/types/ess';

import { logger } from "@/lib/logger";
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

  const currentFY = '2024-25';

  useEffect(() => {
    if (!accessToken) {
      navigate('/ess/login');
      return;
    }
    fetchData();
  }, [accessToken, navigate]);

  const fetchData = async () => {
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
  };

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
        investment_date: formData.get('investment_date') as string || undefined,
        policy_number: formData.get('policy_number') as string || undefined,
        institution_name: formData.get('institution_name') as string || undefined,
      });
      setAddItemDialogOpen(false);
      setSelectedSection(null);
      fetchData();
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
      fetchData();
    } catch (error) {
      logger.error('Failed to submit declaration:', error);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(amount);
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
        <Icon className="h-3 w-3 mr-1" />
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
    return declaration?.items
      .filter((item) => item.section_code === sectionCode)
      .reduce((sum, item) => sum + item.declared_amount, 0) || 0;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
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
              <Send className="h-4 w-4 mr-2" />
              Submit Declaration
            </Button>
          ) : undefined
        }
      />

      {/* Status & Summary */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-500">Status</span>
              {declaration && getStatusBadge(declaration.status)}
            </div>
            <p className="text-sm text-gray-500">Tax Regime</p>
            <p className="font-medium">{declaration?.tax_regime === 'OLD' ? 'Old Regime' : 'New Regime'}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-2">
              <IndianRupee className="h-4 w-4 text-blue-600" />
              <span className="text-sm text-gray-500">Total Declared</span>
            </div>
            <p className="text-xl font-bold">{formatCurrency(declaration?.total_declared_amount || 0)}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-2">
              <Calculator className="h-4 w-4 text-purple-600" />
              <span className="text-sm text-gray-500">Est. Tax Liability</span>
            </div>
            <p className="text-xl font-bold">{formatCurrency(taxCalculation?.total_tax_liability || 0)}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2 mb-2">
              <Calculator className="h-4 w-4 text-green-600" />
              <span className="text-sm text-gray-500">Monthly TDS</span>
            </div>
            <p className="text-xl font-bold">{formatCurrency(taxCalculation?.monthly_tds || 0)}</p>
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
                  <AccordionItem key={category} value={category} className="border rounded-lg px-4">
                    <AccordionTrigger className="hover:no-underline">
                      <div className="flex items-center justify-between w-full mr-4">
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
                          const progress = section.max_limit > 0
                            ? Math.min((sectionTotal / section.max_limit) * 100, 100)
                            : 0;
                          const sectionItems = declaration?.items.filter(
                            (item) => item.section_code === section.section_code
                          ) || [];

                          return (
                            <div key={section.id} className="p-4 bg-gray-50 rounded-lg">
                              <div className="flex items-start justify-between mb-2">
                                <div>
                                  <div className="flex items-center gap-2">
                                    <span className="font-medium">{section.section_code}</span>
                                    <span className="text-sm text-gray-600">{section.section_name}</span>
                                  </div>
                                  {section.help_text && (
                                    <p className="text-xs text-gray-500 mt-1">{section.help_text}</p>
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
                                  <Plus className="h-3 w-3 mr-1" />
                                  Add
                                </Button>
                              </div>

                              {section.max_limit > 0 && (
                                <div className="mb-3">
                                  <div className="flex justify-between text-xs text-gray-500 mb-1">
                                    <span>Declared: {formatCurrency(sectionTotal)}</span>
                                    <span>Limit: {formatCurrency(section.max_limit)}</span>
                                  </div>
                                  <Progress value={progress} className="h-2" />
                                </div>
                              )}

                              {sectionItems.length > 0 && (
                                <div className="space-y-2 mt-3">
                                  {sectionItems.map((item) => (
                                    <div
                                      key={item.id}
                                      className="flex items-center justify-between p-2 bg-white rounded border"
                                    >
                                      <div>
                                        <p className="text-sm font-medium">{item.particular}</p>
                                        {item.institution_name && (
                                          <p className="text-xs text-gray-500">{item.institution_name}</p>
                                        )}
                                      </div>
                                      <div className="text-right">
                                        <p className="font-medium">{formatCurrency(item.declared_amount)}</p>
                                        {item.is_verified && (
                                          <Badge variant="secondary" className="text-xs bg-green-100 text-green-700">
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
              <CardTitle className="text-base flex items-center gap-2">
                <Home className="h-4 w-4" />
                HRA Exemption Details
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <Label>Monthly Rent</Label>
                  <p className="text-lg font-medium">{formatCurrency(declaration?.rent_paid_monthly || 0)}</p>
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

              <div className="p-4 bg-green-50 rounded-lg">
                <p className="text-sm text-gray-600">Estimated HRA Exemption</p>
                <p className="text-2xl font-bold text-green-700">
                  {formatCurrency(declaration?.hra_declared || 0)}
                </p>
              </div>

              {/* Monthly Receipts */}
              {declaration?.hra_receipts && declaration.hra_receipts.length > 0 && (
                <div>
                  <Label className="mb-2 block">Monthly Rent Receipts</Label>
                  <div className="grid grid-cols-3 md:grid-cols-6 gap-2">
                    {declaration.hra_receipts.map((receipt) => (
                      <div
                        key={receipt.id}
                        className={`p-2 text-center rounded border ${
                          receipt.receipt_uploaded ? 'bg-green-50 border-green-200' : 'bg-gray-50'
                        }`}
                      >
                        <p className="text-xs text-gray-500">{receipt.month}</p>
                        <p className="font-medium text-sm">{formatCurrency(receipt.rent_amount)}</p>
                        {receipt.receipt_uploaded && (
                          <CheckCircle className="h-3 w-3 text-green-600 mx-auto mt-1" />
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
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                <div>
                  <Label>Interest Paid (Annual)</Label>
                  <p className="text-lg font-medium">{formatCurrency(declaration?.home_loan_interest || 0)}</p>
                </div>
                <div>
                  <Label>Principal Paid (Annual)</Label>
                  <p className="text-lg font-medium">{formatCurrency(declaration?.home_loan_principal || 0)}</p>
                </div>
                <div>
                  <Label>Lender Name</Label>
                  <p className="font-medium">{declaration?.lender_name || '-'}</p>
                </div>
              </div>

              <div className="p-4 bg-blue-50 rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <Info className="h-4 w-4 text-blue-600" />
                  <span className="text-sm font-medium text-blue-700">Deduction Limits</span>
                </div>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li>• Self-occupied property: Max ₹2,00,000 interest deduction (Section 24b)</li>
                  <li>• Principal repayment: Included in 80C limit (₹1,50,000)</li>
                  <li>• First-time buyer (80EE): Additional ₹50,000 if loan ≤ ₹35L, property ≤ ₹50L</li>
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
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                    <div className="p-4 bg-gray-50 rounded-lg">
                      <p className="text-sm text-gray-500">Gross Income</p>
                      <p className="text-xl font-bold">{formatCurrency(taxCalculation.gross_income)}</p>
                    </div>
                    <div className="p-4 bg-green-50 rounded-lg">
                      <p className="text-sm text-gray-500">Total Deductions</p>
                      <p className="text-xl font-bold text-green-700">
                        -{formatCurrency(taxCalculation.chapter_vi_a_deductions + taxCalculation.standard_deduction)}
                      </p>
                    </div>
                    <div className="p-4 bg-blue-50 rounded-lg">
                      <p className="text-sm text-gray-500">Taxable Income</p>
                      <p className="text-xl font-bold">{formatCurrency(taxCalculation.taxable_income)}</p>
                    </div>
                  </div>

                  {/* Tax Slabs */}
                  <div>
                    <h4 className="font-medium mb-3">Tax Computation</h4>
                    <div className="space-y-2">
                      {taxCalculation.breakdown?.tax_slabs?.map((slab, idx) => (
                        <div key={idx} className="flex justify-between p-2 bg-gray-50 rounded">
                          <span className="text-sm">{slab.slab} @ {slab.rate}%</span>
                          <span className="font-medium">{formatCurrency(slab.tax)}</span>
                        </div>
                      ))}
                      <div className="flex justify-between p-2 bg-gray-100 rounded">
                        <span>Tax on Income</span>
                        <span className="font-medium">{formatCurrency(taxCalculation.tax_on_income)}</span>
                      </div>
                      {taxCalculation.surcharge > 0 && (
                        <div className="flex justify-between p-2">
                          <span className="text-sm text-gray-600">Surcharge</span>
                          <span>{formatCurrency(taxCalculation.surcharge)}</span>
                        </div>
                      )}
                      <div className="flex justify-between p-2">
                        <span className="text-sm text-gray-600">Education Cess (4%)</span>
                        <span>{formatCurrency(taxCalculation.education_cess)}</span>
                      </div>
                      <div className="flex justify-between p-3 bg-red-50 rounded font-bold">
                        <span>Total Tax Liability</span>
                        <span className="text-red-700">{formatCurrency(taxCalculation.total_tax_liability)}</span>
                      </div>
                      <div className="flex justify-between p-3 bg-blue-50 rounded">
                        <span className="font-medium">Monthly TDS</span>
                        <span className="font-bold text-blue-700">{formatCurrency(taxCalculation.monthly_tds)}</span>
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <Calculator className="h-8 w-8 mx-auto mb-2 opacity-50" />
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
              <Input id="particular" name="particular" placeholder="e.g., LIC Policy, PPF, ELSS Fund" required />
            </div>
            <div>
              <Label htmlFor="declared_amount">Amount (₹)</Label>
              <Input id="declared_amount" name="declared_amount" type="number" placeholder="Enter amount" required />
            </div>
            <div>
              <Label htmlFor="institution_name">Institution/Company Name</Label>
              <Input id="institution_name" name="institution_name" placeholder="e.g., LIC, SBI, HDFC" />
            </div>
            <div>
              <Label htmlFor="policy_number">Policy/Account Number</Label>
              <Input id="policy_number" name="policy_number" placeholder="Enter reference number" />
            </div>
            <div>
              <Label htmlFor="investment_date">Investment Date</Label>
              <Input id="investment_date" name="investment_date" type="date" />
            </div>
            <div className="flex gap-3 justify-end">
              <Button type="button" variant="outline" onClick={() => setAddItemDialogOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={submitting}>
                {submitting && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                Add Investment
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
