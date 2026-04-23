import { useState, useEffect } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { format } from 'date-fns';
import { ArrowLeft, Plus, Trash2, Save, Send } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { PageHeader } from '@/components/common/PageHeader';
import { Textarea } from '@/components/ui/textarea';
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
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import { Separator } from '@/components/ui/separator';
import { useToast } from '@/hooks/use-toast';
import {
  paymentsApi,
  organizationsApi,
  vendorsApi,
  customersApi,
  accountsApi,
  tdsSectionsApi,
} from '@/services/api';

interface OutstandingDocument {
  document_type: string;
  document_id: string;
  document_number: string;
  document_date: string;
  due_date: string | null;
  total_amount: number;
  paid_amount: number;
  outstanding_amount: number;
  days_overdue: number;
  selected?: boolean;
  allocated_amount?: number;
}

interface Allocation {
  document_type: string;
  document_id: string;
  document_number: string;
  document_date: string;
  document_amount: number;
  outstanding_before: number;
  allocated_amount: number;
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
  const [organizations, setOrganizations] = useState<any[]>([]);
  const [vendors, setVendors] = useState<any[]>([]);
  const [customers, setCustomers] = useState<any[]>([]);
  const [bankAccounts, setBankAccounts] = useState<any[]>([]);
  const [cashAccounts, setCashAccounts] = useState<any[]>([]);
  const [tdsSections, setTdsSections] = useState<any[]>([]);
  const [outstandingDocs, setOutstandingDocs] = useState<OutstandingDocument[]>([]);

  // Form state
  const [formData, setFormData] = useState({
    organization_id: '',
    payment_type: defaultType,
    payment_date: format(new Date(), 'yyyy-MM-dd'),
    party_type: PAYMENT_TYPES.find(t => t.value === defaultType)?.party || 'VENDOR',
    vendor_id: '',
    customer_id: '',
    unit_id: '',
    payment_mode: 'NEFT',
    bank_account_id: '',
    cash_account_id: '',
    amount: '',
    tds_applicable: false,
    tds_section_id: '',
    tds_rate: '',
    tds_amount: '',
    discount_amount: '0',
    write_off_amount: '0',
    cheque_number: '',
    cheque_date: '',
    cheque_bank_name: '',
    cheque_branch: '',
    reference_number: '',
    narration: '',
  });

  const [allocations, setAllocations] = useState<Allocation[]>([]);

  useEffect(() => {
    loadOrganizations();
    loadTdsSections();
  }, []);

  useEffect(() => {
    if (formData.organization_id) {
      loadAccounts();
      loadVendors();
      loadCustomers();
    }
  }, [formData.organization_id]);

  useEffect(() => {
    if (id && formData.organization_id) {
      loadPayment();
    }
  }, [id, formData.organization_id]);

  useEffect(() => {
    // Load outstanding documents when party is selected
    const partyId = formData.party_type === 'VENDOR' ? formData.vendor_id : formData.customer_id;
    if (formData.organization_id && partyId && !isEdit) {
      loadOutstandingDocuments();
    }
  }, [formData.organization_id, formData.vendor_id, formData.customer_id, formData.party_type]);

  useEffect(() => {
    // Update party type when payment type changes
    const paymentTypeConfig = PAYMENT_TYPES.find(t => t.value === formData.payment_type);
    if (paymentTypeConfig && paymentTypeConfig.party !== formData.party_type) {
      setFormData(prev => ({
        ...prev,
        party_type: paymentTypeConfig.party,
        vendor_id: '',
        customer_id: '',
      }));
      setOutstandingDocs([]);
      setAllocations([]);
    }
  }, [formData.payment_type]);

  const loadOrganizations = async () => {
    try {
      const response = await organizationsApi.list({ include_inactive: false });
      setOrganizations(response.data.items || []);
      if (response.data.items?.length > 0 && !formData.organization_id) {
        setFormData(prev => ({ ...prev, organization_id: response.data.items[0].id }));
      }
    } catch (error) {
      console.error('Failed to load organizations:', error);
    }
  };

  const loadAccounts = async () => {
    if (!formData.organization_id) return;
    try {
      // Load bank accounts
      const bankResponse = await accountsApi.list({
        organization_id: formData.organization_id,
        account_type: 'BANK',
      });
      setBankAccounts(bankResponse.data.items || []);

      // Load cash accounts
      const cashResponse = await accountsApi.list({
        organization_id: formData.organization_id,
        account_type: 'CASH',
      });
      setCashAccounts(cashResponse.data.items || []);
    } catch (error) {
      console.error('Failed to load accounts:', error);
    }
  };

  const loadVendors = async () => {
    if (!formData.organization_id) return;
    try {
      const response = await vendorsApi.getActive({ organization_id: formData.organization_id });
      setVendors(response.data || []);
    } catch (error) {
      console.error('Failed to load vendors:', error);
    }
  };

  const loadCustomers = async () => {
    if (!formData.organization_id) return;
    try {
      const response = await customersApi.getActive({ organization_id: formData.organization_id });
      setCustomers(response.data || []);
    } catch (error) {
      console.error('Failed to load customers:', error);
    }
  };

  const loadTdsSections = async () => {
    try {
      const response = await tdsSectionsApi.getActive({ is_tcs: false });
      setTdsSections(response.data || []);
    } catch (error) {
      console.error('Failed to load TDS sections:', error);
    }
  };

  const loadOutstandingDocuments = async () => {
    const partyId = formData.party_type === 'VENDOR' ? formData.vendor_id : formData.customer_id;
    if (!partyId) return;

    try {
      const response = await paymentsApi.getOutstandingDocuments(
        formData.party_type,
        partyId,
        { organization_id: formData.organization_id }
      );
      setOutstandingDocs((response.data || []).map((doc: OutstandingDocument) => ({
        ...doc,
        selected: false,
        allocated_amount: 0,
      })));
    } catch (error) {
      console.error('Failed to load outstanding documents:', error);
    }
  };

  const loadPayment = async () => {
    setLoading(true);
    try {
      const response = await paymentsApi.get(id!);
      const payment = response.data;

      setFormData({
        organization_id: payment.organization_id,
        payment_type: payment.payment_type,
        payment_date: payment.payment_date,
        party_type: payment.party_type,
        vendor_id: payment.vendor_id || '',
        customer_id: payment.customer_id || '',
        unit_id: payment.unit_id || '',
        payment_mode: payment.payment_mode,
        bank_account_id: payment.bank_account_id || '',
        cash_account_id: payment.cash_account_id || '',
        amount: payment.amount.toString(),
        tds_applicable: payment.tds_amount > 0,
        tds_section_id: payment.tds_section_id || '',
        tds_rate: payment.tds_rate?.toString() || '',
        tds_amount: payment.tds_amount?.toString() || '0',
        discount_amount: payment.discount_amount?.toString() || '0',
        write_off_amount: payment.write_off_amount?.toString() || '0',
        cheque_number: payment.cheque_number || '',
        cheque_date: payment.cheque_date || '',
        cheque_bank_name: payment.cheque_bank_name || '',
        cheque_branch: payment.cheque_branch || '',
        reference_number: payment.reference_number || '',
        narration: payment.narration || '',
      });

      setAllocations(payment.allocations || []);
    } catch (error) {
      console.error('Failed to load payment:', error);
      toast({
        title: 'Error',
        description: 'Failed to load payment details',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleVendorChange = (vendorId: string) => {
    const vendor = vendors.find(v => v.id === vendorId);
    setFormData(prev => ({
      ...prev,
      vendor_id: vendorId,
      tds_applicable: vendor?.tds_applicable || false,
      tds_section_id: vendor?.tds_section_id || '',
    }));

    if (vendor?.tds_section_id) {
      const section = tdsSections.find(s => s.id === vendor.tds_section_id);
      if (section) {
        setFormData(prev => ({
          ...prev,
          tds_rate: section.rate_company?.toString() || '',
        }));
      }
    }
  };

  const handleTdsSectionChange = (sectionId: string) => {
    const section = tdsSections.find(s => s.id === sectionId);
    setFormData(prev => ({
      ...prev,
      tds_section_id: sectionId,
      tds_rate: section?.rate_company?.toString() || '',
    }));
  };

  const handleDocumentSelect = (index: number, selected: boolean) => {
    const updatedDocs = [...outstandingDocs];
    updatedDocs[index].selected = selected;
    if (!selected) {
      updatedDocs[index].allocated_amount = 0;
    }
    setOutstandingDocs(updatedDocs);
    updateAllocations(updatedDocs);
  };

  const handleAllocationChange = (index: number, amount: number) => {
    const updatedDocs = [...outstandingDocs];
    updatedDocs[index].allocated_amount = Math.min(amount, updatedDocs[index].outstanding_amount);
    setOutstandingDocs(updatedDocs);
    updateAllocations(updatedDocs);
  };

  const updateAllocations = (docs: OutstandingDocument[]) => {
    const newAllocations = docs
      .filter(doc => doc.selected && (doc.allocated_amount || 0) > 0)
      .map(doc => ({
        document_type: doc.document_type,
        document_id: doc.document_id,
        document_number: doc.document_number,
        document_date: doc.document_date,
        document_amount: doc.total_amount,
        outstanding_before: doc.outstanding_amount,
        allocated_amount: doc.allocated_amount || 0,
      }));
    setAllocations(newAllocations);
  };

  const calculateTdsAmount = () => {
    if (!formData.tds_applicable || !formData.tds_rate || !formData.amount) {
      return 0;
    }
    return (parseFloat(formData.amount) * parseFloat(formData.tds_rate)) / 100;
  };

  const calculateNetAmount = () => {
    const amount = parseFloat(formData.amount) || 0;
    const tds = formData.tds_applicable ? calculateTdsAmount() : 0;
    const discount = parseFloat(formData.discount_amount) || 0;
    const writeOff = parseFloat(formData.write_off_amount) || 0;
    return amount - tds - discount - writeOff;
  };

  const handleSave = async (submit = false) => {
    if (!formData.organization_id || !formData.payment_type || !formData.amount) {
      toast({
        title: 'Validation Error',
        description: 'Please fill all required fields',
        variant: 'destructive',
      });
      return;
    }

    if (formData.party_type === 'VENDOR' && !formData.vendor_id) {
      toast({
        title: 'Validation Error',
        description: 'Please select a vendor',
        variant: 'destructive',
      });
      return;
    }

    if (formData.party_type === 'CUSTOMER' && !formData.customer_id) {
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
        organization_id: formData.organization_id,
        payment_type: formData.payment_type,
        payment_date: formData.payment_date,
        party_type: formData.party_type,
        vendor_id: formData.party_type === 'VENDOR' ? formData.vendor_id : null,
        customer_id: formData.party_type === 'CUSTOMER' ? formData.customer_id : null,
        unit_id: formData.unit_id || null,
        payment_mode: formData.payment_mode,
        bank_account_id: formData.payment_mode !== 'CASH' ? formData.bank_account_id : null,
        cash_account_id: formData.payment_mode === 'CASH' ? formData.cash_account_id : null,
        amount: parseFloat(formData.amount),
        tds_section_id: formData.tds_applicable ? formData.tds_section_id : null,
        tds_rate: formData.tds_applicable ? parseFloat(formData.tds_rate) || 0 : 0,
        tds_amount: formData.tds_applicable ? calculateTdsAmount() : 0,
        discount_amount: parseFloat(formData.discount_amount) || 0,
        write_off_amount: parseFloat(formData.write_off_amount) || 0,
        cheque_number: formData.payment_mode === 'CHEQUE' ? formData.cheque_number : null,
        cheque_date: formData.payment_mode === 'CHEQUE' ? formData.cheque_date : null,
        cheque_bank_name: formData.payment_mode === 'CHEQUE' ? formData.cheque_bank_name : null,
        cheque_branch: formData.payment_mode === 'CHEQUE' ? formData.cheque_branch : null,
        reference_number: formData.reference_number || null,
        narration: formData.narration || null,
        allocations: allocations.map(a => ({
          document_type: a.document_type,
          document_id: a.document_id,
          allocated_amount: a.allocated_amount,
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
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to save payment',
        variant: 'destructive',
      });
    } finally {
      setSaving(false);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 2,
    }).format(amount);
  };

  if (loading) {
    return <div className="p-8 text-center">Loading...</div>;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={isEdit ? 'Edit Payment' : 'New Payment/Receipt'}
        subtitle={
          formData.party_type === 'VENDOR'
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
                    value={formData.organization_id}
                    onValueChange={(value) => handleInputChange('organization_id', value)}
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
                    value={formData.payment_type}
                    onValueChange={(value) => handleInputChange('payment_type', value)}
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
                    value={formData.payment_date}
                    onChange={(e) => handleInputChange('payment_date', e.target.value)}
                  />
                </div>

                <div className="space-y-2">
                  <Label>{formData.party_type === 'VENDOR' ? 'Vendor' : 'Customer'} *</Label>
                  {formData.party_type === 'VENDOR' ? (
                    <Select
                      value={formData.vendor_id}
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
                      value={formData.customer_id}
                      onValueChange={(value) => handleInputChange('customer_id', value)}
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
                    value={formData.payment_mode}
                    onValueChange={(value) => handleInputChange('payment_mode', value)}
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

                {formData.payment_mode === 'CASH' ? (
                  <div className="space-y-2">
                    <Label>Cash Account *</Label>
                    <Select
                      value={formData.cash_account_id}
                      onValueChange={(value) => handleInputChange('cash_account_id', value)}
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
                      value={formData.bank_account_id}
                      onValueChange={(value) => handleInputChange('bank_account_id', value)}
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
                    value={formData.reference_number}
                    onChange={(e) => handleInputChange('reference_number', e.target.value)}
                    placeholder="UTR/Transaction ID"
                  />
                </div>
              </div>

              {/* Cheque Details */}
              {formData.payment_mode === 'CHEQUE' && (
                <>
                  <Separator />
                  <div className="grid gap-4 md:grid-cols-2">
                    <div className="space-y-2">
                      <Label>Cheque Number *</Label>
                      <Input
                        value={formData.cheque_number}
                        onChange={(e) => handleInputChange('cheque_number', e.target.value)}
                        placeholder="Enter cheque number"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Cheque Date *</Label>
                      <Input
                        type="date"
                        value={formData.cheque_date}
                        onChange={(e) => handleInputChange('cheque_date', e.target.value)}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Bank Name</Label>
                      <Input
                        value={formData.cheque_bank_name}
                        onChange={(e) => handleInputChange('cheque_bank_name', e.target.value)}
                        placeholder="Enter bank name"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Branch</Label>
                      <Input
                        value={formData.cheque_branch}
                        onChange={(e) => handleInputChange('cheque_branch', e.target.value)}
                        placeholder="Enter branch"
                      />
                    </div>
                  </div>
                </>
              )}

              {/* TDS Section (for vendor payments) */}
              {formData.party_type === 'VENDOR' && (
                <>
                  <Separator />
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="tds_applicable"
                      checked={formData.tds_applicable}
                      onCheckedChange={(checked) => handleInputChange('tds_applicable', checked)}
                    />
                    <Label htmlFor="tds_applicable">TDS Applicable</Label>
                  </div>

                  {formData.tds_applicable && (
                    <div className="grid gap-4 md:grid-cols-3">
                      <div className="space-y-2">
                        <Label>TDS Section</Label>
                        <Select
                          value={formData.tds_section_id}
                          onValueChange={handleTdsSectionChange}
                        >
                          <SelectTrigger>
                            <SelectValue placeholder="Select Section" />
                          </SelectTrigger>
                          <SelectContent>
                            {tdsSections.map((section) => (
                              <SelectItem key={section.id} value={section.id}>
                                {section.section_code} - {section.description}
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
                          value={formData.tds_rate}
                          onChange={(e) => handleInputChange('tds_rate', e.target.value)}
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
                <CardTitle>Outstanding {formData.party_type === 'VENDOR' ? 'Bills' : 'Invoices'}</CardTitle>
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
                        <TableRow key={doc.document_id}>
                          <TableCell>
                            <Checkbox
                              checked={doc.selected}
                              onCheckedChange={(checked) => handleDocumentSelect(index, checked as boolean)}
                            />
                          </TableCell>
                          <TableCell className="font-medium">{doc.document_number}</TableCell>
                          <TableCell>{format(new Date(doc.document_date), 'dd MMM yyyy')}</TableCell>
                          <TableCell>
                            {doc.due_date ? format(new Date(doc.due_date), 'dd MMM yyyy') : '-'}
                            {doc.days_overdue > 0 && (
                              <span className="ml-2 text-xs text-red-600">
                                ({doc.days_overdue}d overdue)
                              </span>
                            )}
                          </TableCell>
                          <TableCell className="text-right">
                            {formatCurrency(doc.outstanding_amount)}
                          </TableCell>
                          <TableCell className="text-right">
                            <Input
                              type="number"
                              step="0.01"
                              className="w-[120px] text-right"
                              value={doc.allocated_amount || ''}
                              onChange={(e) => handleAllocationChange(index, parseFloat(e.target.value) || 0)}
                              disabled={!doc.selected}
                              max={doc.outstanding_amount}
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
                          <TableCell className="font-medium">{alloc.document_number}</TableCell>
                          <TableCell>{format(new Date(alloc.document_date), 'dd MMM yyyy')}</TableCell>
                          <TableCell className="text-right">
                            {formatCurrency(alloc.document_amount)}
                          </TableCell>
                          <TableCell className="text-right">
                            {formatCurrency(alloc.allocated_amount)}
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
                <span className="font-medium">{formatCurrency(parseFloat(formData.amount) || 0)}</span>
              </div>
              {formData.tds_applicable && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">TDS Deduction</span>
                  <span className="font-medium text-red-600">
                    -{formatCurrency(calculateTdsAmount())}
                  </span>
                </div>
              )}
              {parseFloat(formData.discount_amount) > 0 && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Discount</span>
                  <span className="font-medium text-red-600">
                    -{formatCurrency(parseFloat(formData.discount_amount))}
                  </span>
                </div>
              )}
              <Separator />
              <div className="flex justify-between text-lg font-semibold">
                <span>Net {formData.party_type === 'VENDOR' ? 'Payment' : 'Receipt'}</span>
                <span>{formatCurrency(calculateNetAmount())}</span>
              </div>

              {allocations.length > 0 && (
                <>
                  <Separator />
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Allocated Amount</span>
                    <span className="font-medium">
                      {formatCurrency(allocations.reduce((sum, a) => sum + a.allocated_amount, 0))}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Unallocated</span>
                    <span className="font-medium">
                      {formatCurrency(
                        calculateNetAmount() - allocations.reduce((sum, a) => sum + a.allocated_amount, 0)
                      )}
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
