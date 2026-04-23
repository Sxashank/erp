import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, Loader2, Plus, Save, Trash2 } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { PageHeader } from '@/components/common/PageHeader';
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
import { Checkbox } from '@/components/ui/checkbox';
import { useToast } from '@/hooks/use-toast';
import {
  salesInvoicesApi,
  organizationsApi,
  unitsApi,
  customersApi,
  gstRatesApi,
  accountsApi,
} from '@/services/api';

interface Organization {
  id: string;
  code: string;
  name: string;
}

interface Unit {
  id: string;
  code: string;
  name: string;
}

interface Customer {
  id: string;
  code: string;
  name: string;
  gstin: string | null;
  billing_state_code: string | null;
  tcs_applicable: boolean;
}

interface GSTRate {
  id: string;
  code: string;
  name: string;
  rate: number;
  cgst_rate: number;
  sgst_rate: number;
  igst_rate: number;
  cess_rate: number;
}

interface Account {
  id: string;
  code: string;
  name: string;
}

interface InvoiceLine {
  id?: string;
  line_number: number;
  description: string;
  hsn_sac_code: string;
  quantity: number;
  unit_price: number;
  discount_percent: number;
  discount_amount: number;
  taxable_amount: number;
  gst_rate_id: string;
  cgst_rate: number;
  cgst_amount: number;
  sgst_rate: number;
  sgst_amount: number;
  igst_rate: number;
  igst_amount: number;
  cess_rate: number;
  cess_amount: number;
  total_amount: number;
  revenue_account_id: string;
}

const stateList = [
  { code: '01', name: 'Jammu & Kashmir' },
  { code: '02', name: 'Himachal Pradesh' },
  { code: '03', name: 'Punjab' },
  { code: '04', name: 'Chandigarh' },
  { code: '05', name: 'Uttarakhand' },
  { code: '06', name: 'Haryana' },
  { code: '07', name: 'Delhi' },
  { code: '08', name: 'Rajasthan' },
  { code: '09', name: 'Uttar Pradesh' },
  { code: '10', name: 'Bihar' },
  { code: '11', name: 'Sikkim' },
  { code: '12', name: 'Arunachal Pradesh' },
  { code: '13', name: 'Nagaland' },
  { code: '14', name: 'Manipur' },
  { code: '15', name: 'Mizoram' },
  { code: '16', name: 'Tripura' },
  { code: '17', name: 'Meghalaya' },
  { code: '18', name: 'Assam' },
  { code: '19', name: 'West Bengal' },
  { code: '20', name: 'Jharkhand' },
  { code: '21', name: 'Odisha' },
  { code: '22', name: 'Chhattisgarh' },
  { code: '23', name: 'Madhya Pradesh' },
  { code: '24', name: 'Gujarat' },
  { code: '26', name: 'Dadra & Nagar Haveli and Daman & Diu' },
  { code: '27', name: 'Maharashtra' },
  { code: '29', name: 'Karnataka' },
  { code: '30', name: 'Goa' },
  { code: '31', name: 'Lakshadweep' },
  { code: '32', name: 'Kerala' },
  { code: '33', name: 'Tamil Nadu' },
  { code: '34', name: 'Puducherry' },
  { code: '35', name: 'Andaman & Nicobar Islands' },
  { code: '36', name: 'Telangana' },
  { code: '37', name: 'Andhra Pradesh' },
  { code: '38', name: 'Ladakh' },
];

export function SalesInvoiceForm() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { toast } = useToast();
  const isEdit = Boolean(id);

  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [units, setUnits] = useState<Unit[]>([]);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [gstRates, setGstRates] = useState<GSTRate[]>([]);
  const [revenueAccounts, setRevenueAccounts] = useState<Account[]>([]);
  const [orgStateCode, setOrgStateCode] = useState<string>('');

  // Form state
  const [selectedOrgId, setSelectedOrgId] = useState<string>('');
  const [unitId, setUnitId] = useState<string>('');
  const [customerId, setCustomerId] = useState<string>('');
  const [invoiceDate, setInvoiceDate] = useState<string>(new Date().toISOString().split('T')[0]);
  const [dueDate, setDueDate] = useState<string>('');
  const [placeOfSupply, setPlaceOfSupply] = useState<string>('');
  const [isReverseCharge, setIsReverseCharge] = useState(false);
  const [eInvoiceRequired, setEInvoiceRequired] = useState(false);
  const [tcsAmount, setTcsAmount] = useState<number>(0);
  const [roundOff, setRoundOff] = useState<number>(0);
  const [narration, setNarration] = useState<string>('');
  const [referenceNumber, setReferenceNumber] = useState<string>('');
  const [poNumber, setPoNumber] = useState<string>('');
  const [poDate, setPoDate] = useState<string>('');

  // Shipping details
  const [shippingAddress, setShippingAddress] = useState<string>('');
  const [transporterName, setTransporterName] = useState<string>('');
  const [vehicleNumber, setVehicleNumber] = useState<string>('');
  const [ewayBillNumber, setEwayBillNumber] = useState<string>('');
  const [ewayBillDate, setEwayBillDate] = useState<string>('');

  const [lines, setLines] = useState<InvoiceLine[]>([createEmptyLine(1)]);

  // Computed totals
  const [subtotal, setSubtotal] = useState(0);
  const [totalDiscount, setTotalDiscount] = useState(0);
  const [totalTaxable, setTotalTaxable] = useState(0);
  const [totalCgst, setTotalCgst] = useState(0);
  const [totalSgst, setTotalSgst] = useState(0);
  const [totalIgst, setTotalIgst] = useState(0);
  const [totalCess, setTotalCess] = useState(0);
  const [grandTotal, setGrandTotal] = useState(0);

  function createEmptyLine(lineNumber: number): InvoiceLine {
    return {
      line_number: lineNumber,
      description: '',
      hsn_sac_code: '',
      quantity: 1,
      unit_price: 0,
      discount_percent: 0,
      discount_amount: 0,
      taxable_amount: 0,
      gst_rate_id: '',
      cgst_rate: 0,
      cgst_amount: 0,
      sgst_rate: 0,
      sgst_amount: 0,
      igst_rate: 0,
      igst_amount: 0,
      cess_rate: 0,
      cess_amount: 0,
      total_amount: 0,
      revenue_account_id: '',
    };
  }

  useEffect(() => {
    loadOrganizations();
  }, []);

  useEffect(() => {
    if (selectedOrgId) {
      loadUnits();
      loadCustomers();
      loadGstRates();
      loadRevenueAccounts();
    }
  }, [selectedOrgId]);

  useEffect(() => {
    if (isEdit && id && selectedOrgId) {
      loadInvoice(id);
    }
  }, [id, isEdit, selectedOrgId]);

  useEffect(() => {
    calculateTotals();
  }, [lines, tcsAmount, roundOff]);

  useEffect(() => {
    // Auto-set place of supply when customer changes
    if (customerId) {
      const customer = customers.find((c) => c.id === customerId);
      if (customer?.billing_state_code) {
        setPlaceOfSupply(customer.billing_state_code);
      }
    }
  }, [customerId, customers]);

  useEffect(() => {
    // Recalculate GST when place of supply changes
    recalculateGst();
  }, [placeOfSupply, orgStateCode]);

  const loadOrganizations = async () => {
    try {
      const response = await organizationsApi.list({ page_size: 100 });
      const orgs = response.data.items || [];
      setOrganizations(orgs);
      if (orgs.length > 0 && !isEdit) {
        setSelectedOrgId(orgs[0].id);
        // Get org's state code - default to Maharashtra
        setOrgStateCode('27');
      }
    } catch (error) {
      console.error('Failed to load organizations:', error);
    }
  };

  const loadUnits = async () => {
    if (!selectedOrgId) return;
    try {
      const response = await unitsApi.list({ organization_id: selectedOrgId, page_size: 100 });
      setUnits(response.data.items || []);
    } catch (error) {
      console.error('Failed to load units:', error);
    }
  };

  const loadCustomers = async () => {
    if (!selectedOrgId) return;
    try {
      const response = await customersApi.getActive({ organization_id: selectedOrgId });
      setCustomers(response.data || []);
    } catch (error) {
      console.error('Failed to load customers:', error);
    }
  };

  const loadGstRates = async () => {
    try {
      const response = await gstRatesApi.getActive({});
      setGstRates(response.data || []);
    } catch (error) {
      console.error('Failed to load GST rates:', error);
    }
  };

  const loadRevenueAccounts = async () => {
    if (!selectedOrgId) return;
    try {
      const response = await accountsApi.list({
        organization_id: selectedOrgId,
        page_size: 200,
      });
      // Filter for revenue accounts (nature = INCOME)
      const accounts = response.data.items || [];
      setRevenueAccounts(accounts);
    } catch (error) {
      console.error('Failed to load accounts:', error);
    }
  };

  const loadInvoice = async (invoiceId: string) => {
    try {
      setLoading(true);
      const response = await salesInvoicesApi.get(invoiceId);
      const invoice = response.data;

      setSelectedOrgId(invoice.organization_id);
      setUnitId(invoice.unit_id || '');
      setCustomerId(invoice.customer_id);
      setInvoiceDate(invoice.invoice_date);
      setDueDate(invoice.due_date);
      setPlaceOfSupply(invoice.place_of_supply || '');
      setIsReverseCharge(invoice.is_reverse_charge || false);
      setEInvoiceRequired(invoice.e_invoice_required || false);
      setTcsAmount(invoice.tcs_amount || 0);
      setRoundOff(invoice.round_off || 0);
      setNarration(invoice.narration || '');
      setReferenceNumber(invoice.reference_number || '');
      setPoNumber(invoice.po_number || '');
      setPoDate(invoice.po_date || '');
      setShippingAddress(invoice.shipping_address || '');
      setTransporterName(invoice.transporter_name || '');
      setVehicleNumber(invoice.vehicle_number || '');
      setEwayBillNumber(invoice.eway_bill_number || '');
      setEwayBillDate(invoice.eway_bill_date || '');

      if (invoice.lines && invoice.lines.length > 0) {
        setLines(
          invoice.lines.map((line: any) => ({
            id: line.id,
            line_number: line.line_number,
            description: line.description,
            hsn_sac_code: line.hsn_sac_code || '',
            quantity: line.quantity,
            unit_price: line.unit_price,
            discount_percent: line.discount_percent || 0,
            discount_amount: line.discount_amount || 0,
            taxable_amount: line.taxable_amount,
            gst_rate_id: line.gst_rate_id || '',
            cgst_rate: line.cgst_rate || 0,
            cgst_amount: line.cgst_amount || 0,
            sgst_rate: line.sgst_rate || 0,
            sgst_amount: line.sgst_amount || 0,
            igst_rate: line.igst_rate || 0,
            igst_amount: line.igst_amount || 0,
            cess_rate: line.cess_rate || 0,
            cess_amount: line.cess_amount || 0,
            total_amount: line.total_amount,
            revenue_account_id: line.revenue_account_id || '',
          }))
        );
      }
    } catch (error) {
      console.error('Failed to load invoice:', error);
      toast({
        title: 'Error',
        description: 'Failed to load sales invoice',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const isIntraState = () => {
    return placeOfSupply === orgStateCode;
  };

  const recalculateGst = () => {
    const newLines = lines.map((line) => {
      if (line.gst_rate_id) {
        return calculateLine(line);
      }
      return line;
    });
    setLines(newLines);
  };

  const calculateLine = (line: InvoiceLine): InvoiceLine => {
    const grossAmount = line.quantity * line.unit_price;
    const discountAmount = line.discount_percent > 0
      ? (grossAmount * line.discount_percent) / 100
      : line.discount_amount;
    const taxableAmount = grossAmount - discountAmount;

    const gstRate = gstRates.find((r) => r.id === line.gst_rate_id);
    let cgstRate = 0, cgstAmount = 0, sgstRate = 0, sgstAmount = 0, igstRate = 0, igstAmount = 0, cessRate = 0, cessAmount = 0;

    if (gstRate) {
      cessRate = gstRate.cess_rate || 0;
      cessAmount = (taxableAmount * cessRate) / 100;

      if (isIntraState()) {
        cgstRate = gstRate.cgst_rate;
        sgstRate = gstRate.sgst_rate;
        cgstAmount = (taxableAmount * cgstRate) / 100;
        sgstAmount = (taxableAmount * sgstRate) / 100;
      } else {
        igstRate = gstRate.igst_rate;
        igstAmount = (taxableAmount * igstRate) / 100;
      }
    }

    const totalAmount = taxableAmount + cgstAmount + sgstAmount + igstAmount + cessAmount;

    return {
      ...line,
      discount_amount: discountAmount,
      taxable_amount: taxableAmount,
      cgst_rate: cgstRate,
      cgst_amount: cgstAmount,
      sgst_rate: sgstRate,
      sgst_amount: sgstAmount,
      igst_rate: igstRate,
      igst_amount: igstAmount,
      cess_rate: cessRate,
      cess_amount: cessAmount,
      total_amount: totalAmount,
    };
  };

  const calculateTotals = () => {
    let sub = 0, disc = 0, taxable = 0, cgst = 0, sgst = 0, igst = 0, cess = 0;

    lines.forEach((line) => {
      sub += line.quantity * line.unit_price;
      disc += line.discount_amount;
      taxable += line.taxable_amount;
      cgst += line.cgst_amount;
      sgst += line.sgst_amount;
      igst += line.igst_amount;
      cess += line.cess_amount;
    });

    setSubtotal(sub);
    setTotalDiscount(disc);
    setTotalTaxable(taxable);
    setTotalCgst(cgst);
    setTotalSgst(sgst);
    setTotalIgst(igst);
    setTotalCess(cess);
    setGrandTotal(taxable + cgst + sgst + igst + cess + tcsAmount + roundOff);
  };

  const handleAddLine = () => {
    setLines([...lines, createEmptyLine(lines.length + 1)]);
  };

  const handleRemoveLine = (index: number) => {
    if (lines.length <= 1) return;
    const newLines = lines.filter((_, i) => i !== index).map((line, i) => ({
      ...line,
      line_number: i + 1,
    }));
    setLines(newLines);
  };

  const handleLineChange = (index: number, field: keyof InvoiceLine, value: any) => {
    const newLines = [...lines];
    (newLines[index] as any)[field] = value;

    // Recalculate line when relevant fields change
    if (['quantity', 'unit_price', 'discount_percent', 'discount_amount', 'gst_rate_id'].includes(field)) {
      newLines[index] = calculateLine(newLines[index]);
    }

    setLines(newLines);
  };

  const onSubmit = async () => {
    if (!customerId) {
      toast({
        title: 'Error',
        description: 'Please select a customer',
        variant: 'destructive',
      });
      return;
    }

    if (!invoiceDate || !dueDate) {
      toast({
        title: 'Error',
        description: 'Please enter invoice date and due date',
        variant: 'destructive',
      });
      return;
    }

    if (lines.filter((l) => l.description && l.taxable_amount > 0).length === 0) {
      toast({
        title: 'Error',
        description: 'Please add at least one line item',
        variant: 'destructive',
      });
      return;
    }

    try {
      setSubmitting(true);

      const invoiceData = {
        customer_id: customerId,
        invoice_date: invoiceDate,
        due_date: dueDate,
        organization_id: selectedOrgId,
        unit_id: unitId || undefined,
        place_of_supply: placeOfSupply || undefined,
        is_reverse_charge: isReverseCharge,
        supply_type: isIntraState() ? 'INTRA_STATE' : 'INTER_STATE',
        e_invoice_required: eInvoiceRequired,
        tcs_amount: tcsAmount,
        round_off: roundOff,
        narration: narration || undefined,
        reference_number: referenceNumber || undefined,
        po_number: poNumber || undefined,
        po_date: poDate || undefined,
        shipping_address: shippingAddress || undefined,
        transporter_name: transporterName || undefined,
        vehicle_number: vehicleNumber || undefined,
        eway_bill_number: ewayBillNumber || undefined,
        eway_bill_date: ewayBillDate || undefined,
        lines: lines
          .filter((l) => l.description && l.taxable_amount > 0)
          .map((l) => ({
            line_number: l.line_number,
            description: l.description,
            hsn_sac_code: l.hsn_sac_code || undefined,
            quantity: l.quantity,
            unit_price: l.unit_price,
            discount_percent: l.discount_percent,
            discount_amount: l.discount_amount,
            taxable_amount: l.taxable_amount,
            gst_rate_id: l.gst_rate_id || undefined,
            cgst_rate: l.cgst_rate,
            cgst_amount: l.cgst_amount,
            sgst_rate: l.sgst_rate,
            sgst_amount: l.sgst_amount,
            igst_rate: l.igst_rate,
            igst_amount: l.igst_amount,
            cess_rate: l.cess_rate,
            cess_amount: l.cess_amount,
            total_amount: l.total_amount,
            revenue_account_id: l.revenue_account_id || undefined,
          })),
      };

      if (isEdit && id) {
        await salesInvoicesApi.update(id, invoiceData);
        toast({
          title: 'Success',
          description: 'Sales invoice updated successfully',
        });
      } else {
        await salesInvoicesApi.create(invoiceData);
        toast({
          title: 'Success',
          description: 'Sales invoice created successfully',
        });
      }

      navigate('/admin/ap-ar/sales-invoices');
    } catch (error: any) {
      console.error('Failed to save sales invoice:', error);
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to save sales invoice',
        variant: 'destructive',
      });
    } finally {
      setSubmitting(false);
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
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-6 w-6 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={isEdit ? 'Edit Sales Invoice' : 'New Sales Invoice'}
        subtitle={
          isEdit
            ? 'Update sales invoice details'
            : 'Create a new sales invoice / customer bill'
        }
        breadcrumbs={[
          { label: 'Sales Invoices', to: '/admin/ap-ar/sales-invoices' },
          { label: isEdit ? 'Edit' : 'New' },
        ]}
      />

      <div className="space-y-6">
        {/* Header Section */}
        <Card>
          <CardHeader>
            <CardTitle>Invoice Details</CardTitle>
            <CardDescription>Basic sales invoice information</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-6">
            <div className="grid gap-4 md:grid-cols-4">
              <div className="space-y-2">
                <Label>Organization *</Label>
                <Select value={selectedOrgId} onValueChange={setSelectedOrgId} disabled={isEdit}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select organization" />
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
                <Label>Unit</Label>
                <Select value={unitId} onValueChange={setUnitId}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select unit" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">All Units</SelectItem>
                    {units.map((unit) => (
                      <SelectItem key={unit.id} value={unit.id}>
                        {unit.code} - {unit.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Customer *</Label>
                <Select value={customerId} onValueChange={setCustomerId}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select customer" />
                  </SelectTrigger>
                  <SelectContent>
                    {customers.map((customer) => (
                      <SelectItem key={customer.id} value={customer.id}>
                        {customer.code} - {customer.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Place of Supply *</Label>
                <Select value={placeOfSupply} onValueChange={setPlaceOfSupply}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select state" />
                  </SelectTrigger>
                  <SelectContent>
                    {stateList.map((state) => (
                      <SelectItem key={state.code} value={state.code}>
                        {state.code} - {state.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-4">
              <div className="space-y-2">
                <Label>Invoice Date *</Label>
                <Input
                  type="date"
                  value={invoiceDate}
                  onChange={(e) => setInvoiceDate(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label>Due Date *</Label>
                <Input
                  type="date"
                  value={dueDate}
                  onChange={(e) => setDueDate(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label>Reference Number</Label>
                <Input
                  value={referenceNumber}
                  onChange={(e) => setReferenceNumber(e.target.value)}
                  placeholder="Optional reference"
                />
              </div>
              <div className="space-y-2">
                <Label>PO Number</Label>
                <Input
                  value={poNumber}
                  onChange={(e) => setPoNumber(e.target.value)}
                  placeholder="Customer PO"
                />
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-4">
              <div className="space-y-2">
                <Label>PO Date</Label>
                <Input
                  type="date"
                  value={poDate}
                  onChange={(e) => setPoDate(e.target.value)}
                />
              </div>
              <div className="flex items-center gap-2 pt-8">
                <Checkbox
                  id="reverseCharge"
                  checked={isReverseCharge}
                  onCheckedChange={(checked) => setIsReverseCharge(checked === true)}
                />
                <label htmlFor="reverseCharge" className="text-sm">
                  Reverse Charge
                </label>
              </div>
              <div className="flex items-center gap-2 pt-8">
                <Checkbox
                  id="eInvoice"
                  checked={eInvoiceRequired}
                  onCheckedChange={(checked) => setEInvoiceRequired(checked === true)}
                />
                <label htmlFor="eInvoice" className="text-sm">
                  E-Invoice Required
                </label>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Line Items */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Line Items</CardTitle>
                <CardDescription>Add items with GST details</CardDescription>
              </div>
              <Button type="button" variant="outline" size="sm" onClick={handleAddLine}>
                <Plus className="mr-2 h-4 w-4" />
                Add Line
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[40px]">#</TableHead>
                    <TableHead className="w-[200px]">Description *</TableHead>
                    <TableHead className="w-[100px]">HSN/SAC</TableHead>
                    <TableHead className="w-[80px] text-right">Qty</TableHead>
                    <TableHead className="w-[100px] text-right">Unit Price</TableHead>
                    <TableHead className="w-[80px] text-right">Disc %</TableHead>
                    <TableHead className="w-[120px]">GST Rate</TableHead>
                    <TableHead className="w-[100px] text-right">Taxable</TableHead>
                    <TableHead className="w-[80px] text-right">GST</TableHead>
                    <TableHead className="w-[100px] text-right">Total</TableHead>
                    <TableHead className="w-[150px]">Revenue A/c</TableHead>
                    <TableHead className="w-[40px]"></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {lines.map((line, index) => (
                    <TableRow key={index}>
                      <TableCell>{line.line_number}</TableCell>
                      <TableCell>
                        <Input
                          value={line.description}
                          onChange={(e) => handleLineChange(index, 'description', e.target.value)}
                          placeholder="Item description"
                        />
                      </TableCell>
                      <TableCell>
                        <Input
                          value={line.hsn_sac_code}
                          onChange={(e) => handleLineChange(index, 'hsn_sac_code', e.target.value)}
                          placeholder="HSN/SAC"
                        />
                      </TableCell>
                      <TableCell>
                        <Input
                          type="number"
                          step="0.01"
                          min="0"
                          className="text-right"
                          value={line.quantity || ''}
                          onChange={(e) => handleLineChange(index, 'quantity', parseFloat(e.target.value) || 0)}
                        />
                      </TableCell>
                      <TableCell>
                        <Input
                          type="number"
                          step="0.01"
                          min="0"
                          className="text-right"
                          value={line.unit_price || ''}
                          onChange={(e) => handleLineChange(index, 'unit_price', parseFloat(e.target.value) || 0)}
                        />
                      </TableCell>
                      <TableCell>
                        <Input
                          type="number"
                          step="0.01"
                          min="0"
                          max="100"
                          className="text-right"
                          value={line.discount_percent || ''}
                          onChange={(e) => handleLineChange(index, 'discount_percent', parseFloat(e.target.value) || 0)}
                        />
                      </TableCell>
                      <TableCell>
                        <Select
                          value={line.gst_rate_id || undefined}
                          onValueChange={(value) => handleLineChange(index, 'gst_rate_id', value)}
                        >
                          <SelectTrigger>
                            <SelectValue placeholder="GST" />
                          </SelectTrigger>
                          <SelectContent>
                            {gstRates.map((rate) => (
                              <SelectItem key={rate.id} value={rate.id}>
                                {rate.name}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </TableCell>
                      <TableCell className="text-right">
                        {formatCurrency(line.taxable_amount)}
                      </TableCell>
                      <TableCell className="text-right text-sm">
                        {isIntraState() ? (
                          <span>
                            C: {formatCurrency(line.cgst_amount)}<br />
                            S: {formatCurrency(line.sgst_amount)}
                          </span>
                        ) : (
                          <span>I: {formatCurrency(line.igst_amount)}</span>
                        )}
                      </TableCell>
                      <TableCell className="text-right font-medium">
                        {formatCurrency(line.total_amount)}
                      </TableCell>
                      <TableCell>
                        <Select
                          value={line.revenue_account_id || undefined}
                          onValueChange={(value) => handleLineChange(index, 'revenue_account_id', value)}
                        >
                          <SelectTrigger>
                            <SelectValue placeholder="Account" />
                          </SelectTrigger>
                          <SelectContent>
                            {revenueAccounts.map((acc) => (
                              <SelectItem key={acc.id} value={acc.id}>
                                {acc.code} - {acc.name}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </TableCell>
                      <TableCell>
                        <Button
                          type="button"
                          variant="ghost"
                          size="icon"
                          onClick={() => handleRemoveLine(index)}
                          disabled={lines.length <= 1}
                        >
                          <Trash2 className="h-4 w-4 text-slate-400" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>

        {/* Shipping Details */}
        <Card>
          <CardHeader>
            <CardTitle>Shipping & Transport Details</CardTitle>
            <CardDescription>Optional shipping and e-way bill information</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label>Shipping Address</Label>
              <Textarea
                value={shippingAddress}
                onChange={(e) => setShippingAddress(e.target.value)}
                placeholder="Delivery address..."
                rows={3}
              />
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label>Transporter Name</Label>
                <Input
                  value={transporterName}
                  onChange={(e) => setTransporterName(e.target.value)}
                  placeholder="Transporter"
                />
              </div>
              <div className="space-y-2">
                <Label>Vehicle Number</Label>
                <Input
                  value={vehicleNumber}
                  onChange={(e) => setVehicleNumber(e.target.value)}
                  placeholder="MH01AB1234"
                />
              </div>
              <div className="space-y-2">
                <Label>E-Way Bill Number</Label>
                <Input
                  value={ewayBillNumber}
                  onChange={(e) => setEwayBillNumber(e.target.value)}
                  placeholder="E-Way Bill"
                />
              </div>
              <div className="space-y-2">
                <Label>E-Way Bill Date</Label>
                <Input
                  type="date"
                  value={ewayBillDate}
                  onChange={(e) => setEwayBillDate(e.target.value)}
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Totals & Summary */}
        <div className="grid gap-6 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Narration</CardTitle>
            </CardHeader>
            <CardContent>
              <Textarea
                value={narration}
                onChange={(e) => setNarration(e.target.value)}
                placeholder="Enter invoice narration or notes..."
                rows={4}
              />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Invoice Summary</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex justify-between">
                <span className="text-slate-600">Subtotal</span>
                <span>{formatCurrency(subtotal)}</span>
              </div>
              {totalDiscount > 0 && (
                <div className="flex justify-between text-green-600">
                  <span>Discount</span>
                  <span>- {formatCurrency(totalDiscount)}</span>
                </div>
              )}
              <div className="flex justify-between">
                <span className="text-slate-600">Taxable Amount</span>
                <span>{formatCurrency(totalTaxable)}</span>
              </div>
              {isIntraState() ? (
                <>
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-600">CGST</span>
                    <span>{formatCurrency(totalCgst)}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-600">SGST</span>
                    <span>{formatCurrency(totalSgst)}</span>
                  </div>
                </>
              ) : (
                <div className="flex justify-between text-sm">
                  <span className="text-slate-600">IGST</span>
                  <span>{formatCurrency(totalIgst)}</span>
                </div>
              )}
              {totalCess > 0 && (
                <div className="flex justify-between text-sm">
                  <span className="text-slate-600">Cess</span>
                  <span>{formatCurrency(totalCess)}</span>
                </div>
              )}
              <div className="flex justify-between items-center">
                <span className="text-slate-600">TCS</span>
                <Input
                  type="number"
                  step="0.01"
                  min="0"
                  className="w-32 text-right"
                  value={tcsAmount || ''}
                  onChange={(e) => setTcsAmount(parseFloat(e.target.value) || 0)}
                />
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-600">Round Off</span>
                <Input
                  type="number"
                  step="0.01"
                  className="w-32 text-right"
                  value={roundOff || ''}
                  onChange={(e) => setRoundOff(parseFloat(e.target.value) || 0)}
                />
              </div>
              <div className="border-t pt-3 flex justify-between font-bold text-lg">
                <span>Grand Total</span>
                <span>{formatCurrency(grandTotal)}</span>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Actions */}
        <div className="flex items-center justify-end gap-4">
          <Button type="button" variant="outline" onClick={() => navigate('/admin/ap-ar/sales-invoices')}>
            Cancel
          </Button>
          <Button onClick={onSubmit} disabled={submitting}>
            {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            <Save className="mr-2 h-4 w-4" />
            {isEdit ? 'Update Invoice' : 'Create Invoice'}
          </Button>
        </div>
      </div>
    </div>
  );
}
