import { Loader2, Plus, Save, Trash2 } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

import { AmountDisplay } from '@/components/common/AmountDisplay';
import { PageHeader } from '@/components/common/PageHeader';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
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
  reg_state_code?: string | null;
  state_code?: string | null;
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
  cgstRate: number;
  sgstRate: number;
  igstRate: number;
  cessRate: number;
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

interface InvoiceLineApi {
  id?: string;
  lineNumber: number;
  description: string;
  hsnSacCode?: string | null;
  quantity: number;
  unitPrice: number;
  discountPercent?: number | null;
  discountAmount?: number | null;
  taxableAmount: number;
  gstRateId?: string | null;
  cgstRate?: number | null;
  cgstAmount?: number | null;
  sgstRate?: number | null;
  sgstAmount?: number | null;
  igstRate?: number | null;
  igstAmount?: number | null;
  cessRate?: number | null;
  cessAmount?: number | null;
  totalAmount: number;
  revenueAccountId?: string | null;
}

interface SalesInvoiceApi {
  organizationId: string;
  unitId?: string | null;
  customerId: string;
  invoiceDate: string;
  dueDate: string;
  placeOfSupply?: string | null;
  isReverseCharge?: boolean | null;
  eInvoiceRequired?: boolean | null;
  irn?: string | null;
  irnDate?: string | null;
  ackNumber?: string | null;
  ackDate?: string | null;
  eInvoiceStatus?: string | null;
  tcsAmount?: number | null;
  roundOff?: number | null;
  narration?: string | null;
  referenceNumber?: string | null;
  poNumber?: string | null;
  poDate?: string | null;
  shippingAddress?: string | null;
  transporterName?: string | null;
  vehicleNumber?: string | null;
  ewayBillNumber?: string | null;
  ewayBillDate?: string | null;
  lines?: InvoiceLineApi[];
}

const recalculatedLineFields: (keyof InvoiceLine)[] = [
  'quantity',
  'unit_price',
  'discount_percent',
  'discount_amount',
  'gst_rate_id',
];

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
  const [irn, setIrn] = useState<string>('');
  const [irnDate, setIrnDate] = useState<string>('');
  const [ackNumber, setAckNumber] = useState<string>('');
  const [ackDate, setAckDate] = useState<string>('');
  const [eInvoiceStatus, setEInvoiceStatus] = useState<string>('NOT_APPLICABLE');
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

  const loadOrganizations = useCallback(async () => {
    try {
      const response = await organizationsApi.list({ pageSize: 100 });
      const orgs = response.data.items || [];
      setOrganizations(orgs);
      if (orgs.length > 0 && !isEdit) {
        setSelectedOrgId(orgs[0].id);
        setOrgStateCode(orgs[0].reg_state_code || orgs[0].state_code || '');
      }
    } catch (error) {
      logger.error('Failed to load organizations:', error);
    }
  }, [isEdit]);

  const loadUnits = useCallback(async () => {
    if (!selectedOrgId) return;
    try {
      const response = await unitsApi.list({ pageSize: 100 });
      setUnits(response.data.items || []);
    } catch (error) {
      logger.error('Failed to load units:', error);
    }
  }, [selectedOrgId]);

  const loadCustomers = useCallback(async () => {
    if (!selectedOrgId) return;
    try {
      const response = await customersApi.getActive({});
      setCustomers(response.data || []);
    } catch (error) {
      logger.error('Failed to load customers:', error);
    }
  }, [selectedOrgId]);

  const loadGstRates = useCallback(async () => {
    try {
      const response = await gstRatesApi.getActive({});
      setGstRates(response.data.items || []);
    } catch (error) {
      logger.error('Failed to load GST rates:', error);
    }
  }, []);

  const loadRevenueAccounts = useCallback(async () => {
    if (!selectedOrgId) return;
    try {
      const response = await accountsApi.list({
        pageSize: 100,
      });
      // Filter for revenue accounts (nature = INCOME)
      const accounts = response.data.items || [];
      setRevenueAccounts(accounts);
    } catch (error) {
      logger.error('Failed to load accounts:', error);
    }
  }, [selectedOrgId]);

  const loadInvoice = useCallback(async (invoiceId: string) => {
    try {
      setLoading(true);
      const response = await salesInvoicesApi.get(invoiceId);
      const invoice = response.data as SalesInvoiceApi;

      setSelectedOrgId(invoice.organizationId);
      setUnitId(invoice.unitId || '');
      setCustomerId(invoice.customerId);
      setInvoiceDate(invoice.invoiceDate);
      setDueDate(invoice.dueDate);
      setPlaceOfSupply(invoice.placeOfSupply || '');
      setIsReverseCharge(invoice.isReverseCharge || false);
      setEInvoiceRequired(invoice.eInvoiceRequired || false);
      setIrn(invoice.irn || '');
      setIrnDate(invoice.irnDate ? invoice.irnDate.slice(0, 16) : '');
      setAckNumber(invoice.ackNumber || '');
      setAckDate(invoice.ackDate ? invoice.ackDate.slice(0, 16) : '');
      setEInvoiceStatus(invoice.eInvoiceStatus || 'NOT_APPLICABLE');
      setTcsAmount(invoice.tcsAmount || 0);
      setRoundOff(invoice.roundOff || 0);
      setNarration(invoice.narration || '');
      setReferenceNumber(invoice.referenceNumber || '');
      setPoNumber(invoice.poNumber || '');
      setPoDate(invoice.poDate || '');
      setShippingAddress(invoice.shippingAddress || '');
      setTransporterName(invoice.transporterName || '');
      setVehicleNumber(invoice.vehicleNumber || '');
      setEwayBillNumber(invoice.ewayBillNumber || '');
      setEwayBillDate(invoice.ewayBillDate || '');

      if (invoice.lines && invoice.lines.length > 0) {
        setLines(
          invoice.lines.map((line) => ({
            id: line.id,
            line_number: line.lineNumber,
            description: line.description,
            hsn_sac_code: line.hsnSacCode || '',
            quantity: line.quantity,
            unit_price: line.unitPrice,
            discount_percent: line.discountPercent || 0,
            discount_amount: line.discountAmount || 0,
            taxable_amount: line.taxableAmount,
            gst_rate_id: line.gstRateId || '',
            cgst_rate: line.cgstRate || 0,
            cgst_amount: line.cgstAmount || 0,
            sgst_rate: line.sgstRate || 0,
            sgst_amount: line.sgstAmount || 0,
            igst_rate: line.igstRate || 0,
            igst_amount: line.igstAmount || 0,
            cess_rate: line.cessRate || 0,
            cess_amount: line.cessAmount || 0,
            total_amount: line.totalAmount,
            revenue_account_id: line.revenueAccountId || '',
          }))
        );
      }
    } catch (error) {
      logger.error('Failed to load invoice:', error);
      showErrorToast(error, toast);
    } finally {
      setLoading(false);
    }
  }, [toast]);

  const isIntraState = useCallback(() => {
    return placeOfSupply === orgStateCode;
  }, [orgStateCode, placeOfSupply]);

  const calculateLine = useCallback((line: InvoiceLine): InvoiceLine => {
    const grossAmount = line.quantity * line.unit_price;
    const discountAmount = line.discount_percent > 0
      ? (grossAmount * line.discount_percent) / 100
      : line.discount_amount;
    const taxableAmount = grossAmount - discountAmount;

    const gstRate = gstRates.find((r) => r.id === line.gst_rate_id);
    let cgstRate = 0, cgstAmount = 0, sgstRate = 0, sgstAmount = 0, igstRate = 0, igstAmount = 0, cessRate = 0, cessAmount = 0;

    if (gstRate) {
      cessRate = gstRate.cessRate || 0;
      cessAmount = (taxableAmount * cessRate) / 100;

      if (isIntraState()) {
        cgstRate = gstRate.cgstRate;
        sgstRate = gstRate.sgstRate;
        cgstAmount = (taxableAmount * cgstRate) / 100;
        sgstAmount = (taxableAmount * sgstRate) / 100;
      } else {
        igstRate = gstRate.igstRate;
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
  }, [gstRates, isIntraState]);

  const recalculateGst = useCallback(() => {
    setLines((currentLines) =>
      currentLines.map((line) => {
        if (line.gst_rate_id) {
          return calculateLine(line);
        }
        return line;
      })
    );
  }, [calculateLine]);

  const calculateTotals = useCallback(() => {
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
  }, [lines, roundOff, tcsAmount]);

  useEffect(() => {
    loadOrganizations();
  }, [loadOrganizations]);

  useEffect(() => {
    if (selectedOrgId) {
      const selectedOrg = organizations.find((org) => org.id === selectedOrgId);
      setOrgStateCode(selectedOrg?.reg_state_code || selectedOrg?.state_code || '');
      loadUnits();
      loadCustomers();
      loadGstRates();
      loadRevenueAccounts();
    }
  }, [loadCustomers, loadGstRates, loadRevenueAccounts, loadUnits, organizations, selectedOrgId]);

  useEffect(() => {
    if (isEdit && id && selectedOrgId) {
      loadInvoice(id);
    }
  }, [id, isEdit, loadInvoice, selectedOrgId]);

  useEffect(() => {
    calculateTotals();
  }, [calculateTotals]);

  useEffect(() => {
    if (customerId) {
      const customer = customers.find((c) => c.id === customerId);
      if (customer?.billing_state_code) {
        setPlaceOfSupply(customer.billing_state_code);
      }
    }
  }, [customerId, customers]);

  useEffect(() => {
    recalculateGst();
  }, [orgStateCode, placeOfSupply, recalculateGst]);

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

  const handleLineChange = (
    index: number,
    field: keyof InvoiceLine,
    value: InvoiceLine[keyof InvoiceLine]
  ) => {
    const newLines = [...lines];
    const updatedLine = { ...newLines[index], [field]: value } as InvoiceLine;

    if (recalculatedLineFields.includes(field)) {
      newLines[index] = calculateLine(updatedLine);
    } else {
      newLines[index] = updatedLine;
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
        customerId,
        invoiceDate,
        dueDate,
        unitId: unitId || undefined,
        placeOfSupply: placeOfSupply || undefined,
        isReverseCharge,
        supplyType: isIntraState() ? 'INTRA_STATE' : 'INTER_STATE',
        eInvoiceRequired,
        irn: irn || undefined,
        irnDate: irnDate || undefined,
        ackNumber: ackNumber || undefined,
        ackDate: ackDate || undefined,
        eInvoiceStatus,
        tcsAmount,
        roundOff,
        narration: narration || undefined,
        referenceNumber: referenceNumber || undefined,
        poNumber: poNumber || undefined,
        poDate: poDate || undefined,
        shippingAddress: shippingAddress || undefined,
        transporterName: transporterName || undefined,
        vehicleNumber: vehicleNumber || undefined,
        ewayBillNumber: ewayBillNumber || undefined,
        ewayBillDate: ewayBillDate || undefined,
        lines: lines
          .filter((l) => l.description && l.taxable_amount > 0)
          .map((l) => ({
            lineNumber: l.line_number,
            description: l.description,
            hsnSacCode: l.hsn_sac_code || undefined,
            quantity: l.quantity,
            unitPrice: l.unit_price,
            discountPercent: l.discount_percent,
            discountAmount: l.discount_amount,
            taxableAmount: l.taxable_amount,
            gstRateId: l.gst_rate_id || undefined,
            cgstRate: l.cgst_rate,
            cgstAmount: l.cgst_amount,
            sgstRate: l.sgst_rate,
            sgstAmount: l.sgst_amount,
            igstRate: l.igst_rate,
            igstAmount: l.igst_amount,
            cessRate: l.cess_rate,
            cessAmount: l.cess_amount,
            totalAmount: l.total_amount,
            revenueAccountId: l.revenue_account_id || undefined,
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
    } catch (error) {
      logger.error('Failed to save sales invoice:', error);
      showErrorToast(error, toast);
    } finally {
      setSubmitting(false);
    }
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
                <Select
                  value={unitId || '__all_units__'}
                  onValueChange={(value) => setUnitId(value === '__all_units__' ? '' : value)}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select unit" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="__all_units__">All Units</SelectItem>
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
                  onCheckedChange={(checked) => {
                    const required = checked === true;
                    setEInvoiceRequired(required);
                    setEInvoiceStatus(required ? 'PENDING' : 'NOT_APPLICABLE');
                  }}
                />
                <label htmlFor="eInvoice" className="text-sm">
                  E-Invoice Required
                </label>
              </div>
              <div className="space-y-2">
                <Label>E-Invoice Status</Label>
                <Select value={eInvoiceStatus} onValueChange={setEInvoiceStatus}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select status" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="NOT_APPLICABLE">Not Applicable</SelectItem>
                    <SelectItem value="PENDING">Pending</SelectItem>
                    <SelectItem value="GENERATED">Generated</SelectItem>
                    <SelectItem value="CANCELLED">Cancelled</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-4">
              <div className="space-y-2">
                <Label>IRN</Label>
                <Input
                  value={irn}
                  onChange={(e) => {
                    setIrn(e.target.value);
                    if (
                      e.target.value &&
                      ['NOT_APPLICABLE', 'PENDING'].includes(eInvoiceStatus)
                    ) {
                      setEInvoiceStatus('GENERATED');
                    }
                  }}
                  placeholder="Invoice Reference Number"
                />
              </div>
              <div className="space-y-2">
                <Label>IRN Date</Label>
                <Input
                  type="datetime-local"
                  value={irnDate}
                  onChange={(e) => setIrnDate(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label>Ack Number</Label>
                <Input
                  value={ackNumber}
                  onChange={(e) => setAckNumber(e.target.value)}
                  placeholder="Acknowledgement no."
                />
              </div>
              <div className="space-y-2">
                <Label>Ack Date</Label>
                <Input
                  type="datetime-local"
                  value={ackDate}
                  onChange={(e) => setAckDate(e.target.value)}
                />
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
                        <AmountDisplay amount={line.taxable_amount} />
                      </TableCell>
                      <TableCell className="text-right text-sm">
                        {isIntraState() ? (
                          <span>
                            C: <AmountDisplay amount={line.cgst_amount} /><br />
                            S: <AmountDisplay amount={line.sgst_amount} />
                          </span>
                        ) : (
                          <span>I: <AmountDisplay amount={line.igst_amount} /></span>
                        )}
                      </TableCell>
                      <TableCell className="text-right font-medium">
                        <AmountDisplay amount={line.total_amount} />
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
                <AmountDisplay amount={subtotal} />
              </div>
              {totalDiscount > 0 && (
                <div className="flex justify-between text-green-600">
                  <span>Discount</span>
                  <span>- <AmountDisplay amount={totalDiscount} /></span>
                </div>
              )}
              <div className="flex justify-between">
                <span className="text-slate-600">Taxable Amount</span>
                <AmountDisplay amount={totalTaxable} />
              </div>
              {isIntraState() ? (
                <>
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-600">CGST</span>
                    <AmountDisplay amount={totalCgst} />
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-600">SGST</span>
                    <AmountDisplay amount={totalSgst} />
                  </div>
                </>
              ) : (
                <div className="flex justify-between text-sm">
                  <span className="text-slate-600">IGST</span>
                  <AmountDisplay amount={totalIgst} />
                </div>
              )}
              {totalCess > 0 && (
                <div className="flex justify-between text-sm">
                  <span className="text-slate-600">Cess</span>
                  <AmountDisplay amount={totalCess} />
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
                <AmountDisplay amount={grandTotal} />
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
