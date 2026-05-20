import { format } from 'date-fns';
import { Save, Send } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';

import { AmountDisplay } from '@/components/common/AmountDisplay';
import { PageHeader } from '@/components/common/PageHeader';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Separator } from '@/components/ui/separator';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Textarea } from '@/components/ui/textarea';
import { useToast } from '@/hooks/use-toast';
import { showErrorToast } from '@/lib/errorToast';
import { logger } from "@/lib/logger";
import {
  paymentsApi,
  organizationsApi,
  vendorsApi,
  customersApi,
  accountsApi,
  tdsSectionsApi,
} from '@/services/api';

interface OutstandingDocument {
  documentType: string;
  documentId: string;
  documentNumber: string;
  documentDate: string;
  dueDate: string | null;
  totalAmount: number;
  paidAmount: number;
  outstandingAmount: number;
  daysOverdue: number;
  selected?: boolean;
  allocatedAmount?: number;
}

interface Allocation {
  documentType: string;
  documentId: string;
  documentNumber: string;
  documentDate: string;
  documentAmount: number;
  outstandingBefore: number;
  allocatedAmount: number;
}

interface OrganizationOption {
  id: string;
  name: string;
}

interface PartyOption {
  id: string;
  name: string;
  tdsApplicable?: boolean;
  tdsSectionId?: string | null;
}

interface AccountOption {
  id: string;
  name: string;
}

interface TdsSectionOption {
  id: string;
  sectionCode: string;
  description: string;
  rateCompany?: number | string | null;
}

interface PaymentDetail {
  id: string;
  organizationId: string;
  paymentType: string;
  paymentDate: string;
  partyType: string;
  vendorId?: string | null;
  customerId?: string | null;
  unitId?: string | null;
  paymentMode: string;
  bankAccountId?: string | null;
  cashAccountId?: string | null;
  amount: number | string;
  tdsAmount?: number | string | null;
  tdsSectionId?: string | null;
  tdsRate?: number | string | null;
  discountAmount?: number | string | null;
  writeOffAmount?: number | string | null;
  chequeNumber?: string | null;
  chequeDate?: string | null;
  chequeBankName?: string | null;
  chequeBranch?: string | null;
  referenceNumber?: string | null;
  narration?: string | null;
  allocations?: Allocation[];
}

interface PaymentFormState {
  organizationId: string;
  paymentType: string;
  paymentDate: string;
  partyType: string;
  vendorId: string;
  customerId: string;
  unitId: string;
  paymentMode: string;
  bankAccountId: string;
  cashAccountId: string;
  amount: string;
  tdsApplicable: boolean;
  tdsSectionId: string;
  tdsRate: string;
  tdsAmount: string;
  discountAmount: string;
  writeOffAmount: string;
  chequeNumber: string;
  chequeDate: string;
  chequeBankName: string;
  chequeBranch: string;
  referenceNumber: string;
  narration: string;
}

const PAYMENT_TYPES = [
  { value: 'VENDOR_PAYMENT', label: 'Vendor Payment', party: 'VENDOR' },
  { value: 'CUSTOMER_RECEIPT', label: 'Customer Receipt', party: 'CUSTOMER' },
  { value: 'ADVANCE_PAYMENT', label: 'Advance to Vendor', party: 'VENDOR' },
  { value: 'ADVANCE_RECEIPT', label: 'Advance from Customer', party: 'CUSTOMER' },
  { value: 'REFUND_PAYMENT', label: 'Refund to Customer', party: 'CUSTOMER' },
  { value: 'REFUND_RECEIPT', label: 'Refund from Vendor', party: 'VENDOR' },
];

const PAYMENT_MODES = [
  { value: 'CASH', label: 'Cash' },
  { value: 'CHEQUE', label: 'Cheque' },
  { value: 'NEFT', label: 'NEFT' },
  { value: 'RTGS', label: 'RTGS' },
  { value: 'IMPS', label: 'IMPS' },
  { value: 'UPI', label: 'UPI' },
  { value: 'BANK_TRANSFER', label: 'Bank Transfer' },
  { value: 'DEMAND_DRAFT', label: 'Demand Draft' },
];

export function PaymentForm() {
  const navigate = useNavigate();
  const { id } = useParams();
  const [searchParams] = useSearchParams();
  const { toast } = useToast();

  const isEdit = Boolean(id);
  const defaultType = searchParams.get('type') || 'VENDOR_PAYMENT';

  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  // Lookups
  const [organizations, setOrganizations] = useState<OrganizationOption[]>([]);
  const [vendors, setVendors] = useState<PartyOption[]>([]);
  const [customers, setCustomers] = useState<PartyOption[]>([]);
  const [bankAccounts, setBankAccounts] = useState<AccountOption[]>([]);
  const [cashAccounts, setCashAccounts] = useState<AccountOption[]>([]);
  const [tdsSections, setTdsSections] = useState<TdsSectionOption[]>([]);
  const [outstandingDocs, setOutstandingDocs] = useState<OutstandingDocument[]>([]);

  // Form state
  const [formData, setFormData] = useState<PaymentFormState>({
    organizationId: '',
    paymentType: defaultType,
    paymentDate: format(new Date(), 'yyyy-MM-dd'),
    partyType: PAYMENT_TYPES.find(t => t.value === defaultType)?.party || 'VENDOR',
    vendorId: '',
    customerId: '',
    unitId: '',
    paymentMode: 'NEFT',
    bankAccountId: '',
    cashAccountId: '',
    amount: '',
    tdsApplicable: false,
    tdsSectionId: '',
    tdsRate: '',
    tdsAmount: '',
    discountAmount: '0',
    writeOffAmount: '0',
    chequeNumber: '',
    chequeDate: '',
    chequeBankName: '',
    chequeBranch: '',
    referenceNumber: '',
    narration: '',
  });

  const [allocations, setAllocations] = useState<Allocation[]>([]);

  const loadOrganizations = useCallback(async () => {
    try {
      const response = await organizationsApi.list({ includeInactive: false });
      setOrganizations(response.data.items || []);
      if (response.data.items?.length > 0 && !formData.organizationId) {
        setFormData(prev => ({ ...prev, organizationId: response.data.items[0].id }));
      }
    } catch (error) {
      logger.error('Failed to load organizations:', error);
    }
  }, [formData.organizationId]);

  const loadAccounts = useCallback(async () => {
    if (!formData.organizationId) return;
    try {
      // Load bank accounts
      const bankResponse = await accountsApi.list({
        accountType: 'BANK',
      });
      setBankAccounts(bankResponse.data.items || []);

      // Load cash accounts
      const cashResponse = await accountsApi.list({
        accountType: 'CASH',
      });
      setCashAccounts(cashResponse.data.items || []);
    } catch (error) {
      logger.error('Failed to load accounts:', error);
    }
  }, [formData.organizationId]);

  const loadVendors = useCallback(async () => {
    if (!formData.organizationId) return;
    try {
      const response = await vendorsApi.getActive({});
      setVendors(response.data || []);
    } catch (error) {
      logger.error('Failed to load vendors:', error);
    }
  }, [formData.organizationId]);

  const loadCustomers = useCallback(async () => {
    if (!formData.organizationId) return;
    try {
      const response = await customersApi.getActive({});
      setCustomers(response.data || []);
    } catch (error) {
      logger.error('Failed to load customers:', error);
    }
  }, [formData.organizationId]);

  const loadTdsSections = useCallback(async () => {
    try {
      const response = await tdsSectionsApi.getActive({ isTcs: false });
      setTdsSections(response.data || []);
    } catch (error) {
      logger.error('Failed to load TDS sections:', error);
    }
  }, []);

  const loadOutstandingDocuments = useCallback(async () => {
    const partyId = formData.partyType === 'VENDOR' ? formData.vendorId : formData.customerId;
    if (!partyId) return;

    try {
      const response = await paymentsApi.getOutstandingDocuments(formData.partyType, partyId);
      setOutstandingDocs((response.data || []).map((doc: OutstandingDocument) => ({
        ...doc,
        selected: false,
        allocatedAmount: 0,
      })));
    } catch (error) {
      logger.error('Failed to load outstanding documents:', error);
    }
  }, [formData.customerId, formData.organizationId, formData.partyType, formData.vendorId]);

  const loadPayment = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    try {
      const response = await paymentsApi.get(id);
      const payment = response.data as PaymentDetail;

      setFormData({
        organizationId: payment.organizationId,
        paymentType: payment.paymentType,
        paymentDate: payment.paymentDate,
        partyType: payment.partyType,
        vendorId: payment.vendorId || '',
        customerId: payment.customerId || '',
        unitId: payment.unitId || '',
        paymentMode: payment.paymentMode,
        bankAccountId: payment.bankAccountId || '',
        cashAccountId: payment.cashAccountId || '',
        amount: payment.amount.toString(),
        tdsApplicable: Number(payment.tdsAmount ?? 0) > 0,
        tdsSectionId: payment.tdsSectionId || '',
        tdsRate: payment.tdsRate?.toString() || '',
        tdsAmount: payment.tdsAmount?.toString() || '0',
        discountAmount: payment.discountAmount?.toString() || '0',
        writeOffAmount: payment.writeOffAmount?.toString() || '0',
        chequeNumber: payment.chequeNumber || '',
        chequeDate: payment.chequeDate || '',
        chequeBankName: payment.chequeBankName || '',
        chequeBranch: payment.chequeBranch || '',
        referenceNumber: payment.referenceNumber || '',
        narration: payment.narration || '',
      });

      setAllocations(payment.allocations || []);
    } catch (error) {
      logger.error('Failed to load payment:', error);
      showErrorToast(error, toast);
    } finally {
      setLoading(false);
    }
  }, [id, toast]);

  useEffect(() => {
    loadOrganizations();
    loadTdsSections();
  }, [loadOrganizations, loadTdsSections]);

  useEffect(() => {
    if (formData.organizationId) {
      loadAccounts();
      loadVendors();
      loadCustomers();
    }
  }, [formData.organizationId, loadAccounts, loadCustomers, loadVendors]);

  useEffect(() => {
    if (id && formData.organizationId) {
      loadPayment();
    }
  }, [formData.organizationId, id, loadPayment]);

  useEffect(() => {
    const partyId = formData.partyType === 'VENDOR' ? formData.vendorId : formData.customerId;
    if (formData.organizationId && partyId && !isEdit) {
      loadOutstandingDocuments();
    }
  }, [
    formData.customerId,
    formData.organizationId,
    formData.partyType,
    formData.vendorId,
    isEdit,
    loadOutstandingDocuments,
  ]);

  useEffect(() => {
    const paymentTypeConfig = PAYMENT_TYPES.find(t => t.value === formData.paymentType);
    if (paymentTypeConfig && paymentTypeConfig.party !== formData.partyType) {
      setFormData(prev => ({
        ...prev,
        partyType: paymentTypeConfig.party,
        vendorId: '',
        customerId: '',
      }));
      setOutstandingDocs([]);
      setAllocations([]);
    }
  }, [formData.partyType, formData.paymentType]);

  const handleInputChange = <K extends keyof PaymentFormState>(
    field: K,
    value: PaymentFormState[K]
  ) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleVendorChange = (vendorId: string) => {
    const vendor = vendors.find(v => v.id === vendorId);
    setFormData(prev => ({
      ...prev,
      vendorId: vendorId,
      tdsApplicable: vendor?.tdsApplicable || false,
      tdsSectionId: vendor?.tdsSectionId || '',
    }));

    if (vendor?.tdsSectionId) {
      const section = tdsSections.find(s => s.id === vendor.tdsSectionId);
      if (section) {
        setFormData(prev => ({
          ...prev,
          tdsRate: section.rateCompany?.toString() || '',
        }));
      }
    }
  };

  const handleTdsSectionChange = (sectionId: string) => {
    const section = tdsSections.find(s => s.id === sectionId);
    setFormData(prev => ({
      ...prev,
      tdsSectionId: sectionId,
      tdsRate: section?.rateCompany?.toString() || '',
    }));
  };

  const handleDocumentSelect = (index: number, selected: boolean) => {
    const updatedDocs = [...outstandingDocs];
    updatedDocs[index].selected = selected;
    if (!selected) {
      updatedDocs[index].allocatedAmount = 0;
    }
    setOutstandingDocs(updatedDocs);
    updateAllocations(updatedDocs);
  };

  const handleAllocationChange = (index: number, amount: number) => {
    const updatedDocs = [...outstandingDocs];
    updatedDocs[index].allocatedAmount = Math.min(amount, updatedDocs[index].outstandingAmount);
    setOutstandingDocs(updatedDocs);
    updateAllocations(updatedDocs);
  };

  const updateAllocations = (docs: OutstandingDocument[]) => {
    const newAllocations = docs
      .filter(doc => doc.selected && (doc.allocatedAmount || 0) > 0)
      .map(doc => ({
        documentType: doc.documentType,
        documentId: doc.documentId,
        documentNumber: doc.documentNumber,
        documentDate: doc.documentDate,
        documentAmount: doc.totalAmount,
        outstandingBefore: doc.outstandingAmount,
        allocatedAmount: doc.allocatedAmount || 0,
      }));
    setAllocations(newAllocations);
  };

  const calculateTdsAmount = () => {
    if (!formData.tdsApplicable || !formData.tdsRate || !formData.amount) {
      return 0;
    }
    return (parseFloat(formData.amount) * parseFloat(formData.tdsRate)) / 100;
  };

  const calculateNetAmount = () => {
    const amount = parseFloat(formData.amount) || 0;
    const tds = formData.tdsApplicable ? calculateTdsAmount() : 0;
    const discount = parseFloat(formData.discountAmount) || 0;
    const writeOff = parseFloat(formData.writeOffAmount) || 0;
    return amount - tds - discount - writeOff;
  };

  const handleSave = async (submit = false) => {
    if (!formData.organizationId || !formData.paymentType || !formData.amount) {
      toast({
        title: 'Validation Error',
        description: 'Please fill all required fields',
        variant: 'destructive',
      });
      return;
    }

    if (formData.partyType === 'VENDOR' && !formData.vendorId) {
      toast({
        title: 'Validation Error',
        description: 'Please select a vendor',
        variant: 'destructive',
      });
      return;
    }

    if (formData.partyType === 'CUSTOMER' && !formData.customerId) {
      toast({
        title: 'Validation Error',
        description: 'Please select a customer',
        variant: 'destructive',
      });
      return;
    }

    setSaving(true);
    try {
      const payload = {
        paymentType: formData.paymentType,
        paymentDate: formData.paymentDate,
        partyType: formData.partyType,
        vendorId: formData.partyType === 'VENDOR' ? formData.vendorId : null,
        customerId: formData.partyType === 'CUSTOMER' ? formData.customerId : null,
        unitId: formData.unitId || null,
        paymentMode: formData.paymentMode,
        bankAccountId: formData.paymentMode !== 'CASH' ? formData.bankAccountId : null,
        cashAccountId: formData.paymentMode === 'CASH' ? formData.cashAccountId : null,
        amount: parseFloat(formData.amount),
        tdsSectionId: formData.tdsApplicable ? formData.tdsSectionId : null,
        tdsRate: formData.tdsApplicable ? parseFloat(formData.tdsRate) || 0 : 0,
        tdsAmount: formData.tdsApplicable ? calculateTdsAmount() : 0,
        discountAmount: parseFloat(formData.discountAmount) || 0,
        writeOffAmount: parseFloat(formData.writeOffAmount) || 0,
        chequeNumber: formData.paymentMode === 'CHEQUE' ? formData.chequeNumber : null,
        chequeDate: formData.paymentMode === 'CHEQUE' ? formData.chequeDate : null,
        chequeBankName: formData.paymentMode === 'CHEQUE' ? formData.chequeBankName : null,
        chequeBranch: formData.paymentMode === 'CHEQUE' ? formData.chequeBranch : null,
        referenceNumber: formData.referenceNumber || null,
        narration: formData.narration || null,
        allocations: allocations.map(a => ({
          documentType: a.documentType,
          documentId: a.documentId,
          allocatedAmount: a.allocatedAmount,
        })),
      };

      let response;
      if (isEdit) {
        response = await paymentsApi.update(id!, payload);
      } else {
        response = await paymentsApi.create(payload);
      }

      if (submit) {
        await paymentsApi.submit(response.data.id);
        toast({ title: 'Success', description: 'Payment submitted for approval' });
      } else {
        toast({ title: 'Success', description: `Payment ${isEdit ? 'updated' : 'created'} successfully` });
      }

      navigate('/admin/ap-ar/payments');
    } catch (error) {
      showErrorToast(error, toast);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="p-8 text-center">Loading...</div>;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={isEdit ? 'Edit Payment' : 'New Payment/Receipt'}
        subtitle={
          formData.partyType === 'VENDOR'
            ? 'Make payment to vendor'
            : 'Record receipt from customer'
        }
        breadcrumbs={[
          { label: 'Payments & Receipts', to: '/admin/ap-ar/payments' },
          { label: isEdit ? 'Edit' : 'New' },
        ]}
      />

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Main Form */}
        <div className="lg:col-span-2 space-y-6">
          {/* Basic Information */}
          <Card>
            <CardHeader>
              <CardTitle>Payment Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label>Organization *</Label>
                  <Select
                    value={formData.organizationId}
                    onValueChange={(value) => handleInputChange('organizationId', value)}
                    disabled={isEdit}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select Organization" />
                    </SelectTrigger>
                    <SelectContent>
                      {organizations.map((org) => (
                        <SelectItem key={org.id} value={org.id}>
                          {org.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label>Payment Type *</Label>
                  <Select
                    value={formData.paymentType}
                    onValueChange={(value) => handleInputChange('paymentType', value)}
                    disabled={isEdit}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select Type" />
                    </SelectTrigger>
                    <SelectContent>
                      {PAYMENT_TYPES.map((type) => (
                        <SelectItem key={type.value} value={type.value}>
                          {type.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label>Payment Date *</Label>
                  <Input
                    type="date"
                    value={formData.paymentDate}
                    onChange={(e) => handleInputChange('paymentDate', e.target.value)}
                  />
                </div>

                <div className="space-y-2">
                  <Label>{formData.partyType === 'VENDOR' ? 'Vendor' : 'Customer'} *</Label>
                  {formData.partyType === 'VENDOR' ? (
                    <Select
                      value={formData.vendorId}
                      onValueChange={handleVendorChange}
                      disabled={isEdit}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select Vendor" />
                      </SelectTrigger>
                      <SelectContent>
                        {vendors.map((vendor) => (
                          <SelectItem key={vendor.id} value={vendor.id}>
                            {vendor.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  ) : (
                    <Select
                      value={formData.customerId}
                      onValueChange={(value) => handleInputChange('customerId', value)}
                      disabled={isEdit}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select Customer" />
                      </SelectTrigger>
                      <SelectContent>
                        {customers.map((customer) => (
                          <SelectItem key={customer.id} value={customer.id}>
                            {customer.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  )}
                </div>
              </div>

              <Separator />

              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label>Payment Mode *</Label>
                  <Select
                    value={formData.paymentMode}
                    onValueChange={(value) => handleInputChange('paymentMode', value)}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select Mode" />
                    </SelectTrigger>
                    <SelectContent>
                      {PAYMENT_MODES.map((mode) => (
                        <SelectItem key={mode.value} value={mode.value}>
                          {mode.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {formData.paymentMode === 'CASH' ? (
                  <div className="space-y-2">
                    <Label>Cash Account *</Label>
                    <Select
                      value={formData.cashAccountId}
                      onValueChange={(value) => handleInputChange('cashAccountId', value)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select Cash Account" />
                      </SelectTrigger>
                      <SelectContent>
                        {cashAccounts.map((account) => (
                          <SelectItem key={account.id} value={account.id}>
                            {account.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                ) : (
                  <div className="space-y-2">
                    <Label>Bank Account *</Label>
                    <Select
                      value={formData.bankAccountId}
                      onValueChange={(value) => handleInputChange('bankAccountId', value)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select Bank Account" />
                      </SelectTrigger>
                      <SelectContent>
                        {bankAccounts.map((account) => (
                          <SelectItem key={account.id} value={account.id}>
                            {account.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                )}

                <div className="space-y-2">
                  <Label>Amount *</Label>
                  <Input
                    type="number"
                    step="0.01"
                    value={formData.amount}
                    onChange={(e) => handleInputChange('amount', e.target.value)}
                    placeholder="0.00"
                  />
                </div>

                <div className="space-y-2">
                  <Label>Reference Number</Label>
                  <Input
                    value={formData.referenceNumber}
                    onChange={(e) => handleInputChange('referenceNumber', e.target.value)}
                    placeholder="UTR/Transaction ID"
                  />
                </div>
              </div>

              {/* Cheque Details */}
              {formData.paymentMode === 'CHEQUE' && (
                <>
                  <Separator />
                  <div className="grid gap-4 md:grid-cols-2">
                    <div className="space-y-2">
                      <Label>Cheque Number *</Label>
                      <Input
                        value={formData.chequeNumber}
                        onChange={(e) => handleInputChange('chequeNumber', e.target.value)}
                        placeholder="Enter cheque number"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Cheque Date *</Label>
                      <Input
                        type="date"
                        value={formData.chequeDate}
                        onChange={(e) => handleInputChange('chequeDate', e.target.value)}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Bank Name</Label>
                      <Input
                        value={formData.chequeBankName}
                        onChange={(e) => handleInputChange('chequeBankName', e.target.value)}
                        placeholder="Enter bank name"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Branch</Label>
                      <Input
                        value={formData.chequeBranch}
                        onChange={(e) => handleInputChange('chequeBranch', e.target.value)}
                        placeholder="Enter branch"
                      />
                    </div>
                  </div>
                </>
              )}

              {/* TDS Section (for vendor payments) */}
              {formData.partyType === 'VENDOR' && (
                <>
                  <Separator />
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="tdsApplicable"
                      checked={formData.tdsApplicable}
                      onCheckedChange={(checked) => handleInputChange('tdsApplicable', checked === true)}
                    />
                    <Label htmlFor="tdsApplicable">TDS Applicable</Label>
                  </div>

                  {formData.tdsApplicable && (
                    <div className="grid gap-4 md:grid-cols-3">
                      <div className="space-y-2">
                        <Label>TDS Section</Label>
                        <Select
                          value={formData.tdsSectionId}
                          onValueChange={handleTdsSectionChange}
                        >
                          <SelectTrigger>
                            <SelectValue placeholder="Select Section" />
                          </SelectTrigger>
                          <SelectContent>
                            {tdsSections.map((section) => (
                              <SelectItem key={section.id} value={section.id}>
                                {section.sectionCode} - {section.description}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="space-y-2">
                        <Label>TDS Rate (%)</Label>
                        <Input
                          type="number"
                          step="0.01"
                          value={formData.tdsRate}
                          onChange={(e) => handleInputChange('tdsRate', e.target.value)}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>TDS Amount</Label>
                        <Input
                          type="number"
                          value={calculateTdsAmount().toFixed(2)}
                          disabled
                        />
                      </div>
                    </div>
                  )}
                </>
              )}

              <div className="space-y-2">
                <Label>Narration</Label>
                <Textarea
                  value={formData.narration}
                  onChange={(e) => handleInputChange('narration', e.target.value)}
                  placeholder="Enter payment narration..."
                  rows={3}
                />
              </div>
            </CardContent>
          </Card>

          {/* Outstanding Documents */}
          {!isEdit && outstandingDocs.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Outstanding {formData.partyType === 'VENDOR' ? 'Bills' : 'Invoices'}</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="rounded-md border">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="w-[50px]">Select</TableHead>
                        <TableHead>Document</TableHead>
                        <TableHead>Date</TableHead>
                        <TableHead>Due Date</TableHead>
                        <TableHead className="text-right">Outstanding</TableHead>
                        <TableHead className="text-right">Allocate</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {outstandingDocs.map((doc, index) => (
                        <TableRow key={doc.documentId}>
                          <TableCell>
                            <Checkbox
                              checked={doc.selected}
                              onCheckedChange={(checked) => handleDocumentSelect(index, checked as boolean)}
                            />
                          </TableCell>
                          <TableCell className="font-medium">{doc.documentNumber}</TableCell>
                          <TableCell>{format(new Date(doc.documentDate), 'dd MMM yyyy')}</TableCell>
                          <TableCell>
                            {doc.dueDate ? format(new Date(doc.dueDate), 'dd MMM yyyy') : '-'}
                            {doc.daysOverdue > 0 && (
                              <span className="ml-2 text-xs text-red-600">
                                ({doc.daysOverdue}d overdue)
                              </span>
                            )}
                          </TableCell>
                          <TableCell className="text-right">
                            <AmountDisplay amount={doc.outstandingAmount} />
                          </TableCell>
                          <TableCell className="text-right">
                            <Input
                              type="number"
                              step="0.01"
                              className="w-[120px] text-right"
                              value={doc.allocatedAmount || ''}
                              onChange={(e) => handleAllocationChange(index, parseFloat(e.target.value) || 0)}
                              disabled={!doc.selected}
                              max={doc.outstandingAmount}
                            />
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Allocations Summary (for edit mode) */}
          {isEdit && allocations.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Allocations</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="rounded-md border">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Document</TableHead>
                        <TableHead>Date</TableHead>
                        <TableHead className="text-right">Document Amount</TableHead>
                        <TableHead className="text-right">Allocated</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {allocations.map((alloc, index) => (
                        <TableRow key={index}>
                          <TableCell className="font-medium">{alloc.documentNumber}</TableCell>
                          <TableCell>{format(new Date(alloc.documentDate), 'dd MMM yyyy')}</TableCell>
                          <TableCell className="text-right">
                            <AmountDisplay amount={alloc.documentAmount} />
                          </TableCell>
                          <TableCell className="text-right">
                            <AmountDisplay amount={alloc.allocatedAmount} />
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Summary Sidebar */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Payment Summary</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Gross Amount</span>
                <AmountDisplay amount={parseFloat(formData.amount) || 0} className="font-medium" />
              </div>
              {formData.tdsApplicable && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">TDS Deduction</span>
                  <span className="font-medium text-red-600">
                    -<AmountDisplay amount={calculateTdsAmount()} />
                  </span>
                </div>
              )}
              {parseFloat(formData.discountAmount) > 0 && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Discount</span>
                  <span className="font-medium text-red-600">
                    -<AmountDisplay amount={parseFloat(formData.discountAmount)} />
                  </span>
                </div>
              )}
              <Separator />
              <div className="flex justify-between text-lg font-semibold">
                <span>Net {formData.partyType === 'VENDOR' ? 'Payment' : 'Receipt'}</span>
                <AmountDisplay amount={calculateNetAmount()} />
              </div>

              {allocations.length > 0 && (
                <>
                  <Separator />
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Allocated Amount</span>
                    <span className="font-medium">
                      <AmountDisplay amount={allocations.reduce((sum, a) => sum + a.allocatedAmount, 0)} />
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Unallocated</span>
                    <span className="font-medium">
                      <AmountDisplay
                        amount={
                          calculateNetAmount() -
                          allocations.reduce((sum, a) => sum + a.allocatedAmount, 0)
                        }
                      />
                    </span>
                  </div>
                </>
              )}
            </CardContent>
          </Card>

          <div className="flex flex-col gap-2">
            <Button onClick={() => handleSave(false)} disabled={saving}>
              <Save className="mr-2 h-4 w-4" />
              {saving ? 'Saving...' : 'Save as Draft'}
            </Button>
            <Button variant="outline" onClick={() => handleSave(true)} disabled={saving}>
              <Send className="mr-2 h-4 w-4" />
              Save & Submit
            </Button>
            <Button variant="ghost" onClick={() => navigate(-1)}>
              Cancel
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
