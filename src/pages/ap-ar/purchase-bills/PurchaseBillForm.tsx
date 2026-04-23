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
  purchaseBillsApi,
  organizationsApi,
  unitsApi,
  vendorsApi,
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

interface Vendor {
  id: string;
  code: string;
  name: string;
  gstin: string | null;
  state_code: string | null;
  tds_applicable: boolean;
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

interface BillLine {
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
  expense_account_id: string;
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

export function PurchaseBillForm() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { toast } = useToast();
  const isEdit = Boolean(id);

  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [units, setUnits] = useState<Unit[]>([]);
  const [vendors, setVendors] = useState<Vendor[]>([]);
  const [gstRates, setGstRates] = useState<GSTRate[]>([]);
  const [expenseAccounts, setExpenseAccounts] = useState<Account[]>([]);
  const [orgStateCode, setOrgStateCode] = useState<string>('');

  // Form state
  const [selectedOrgId, setSelectedOrgId] = useState<string>('');
  const [unitId, setUnitId] = useState<string>('');
  const [vendorId, setVendorId] = useState<string>('');
  const [vendorInvoiceNumber, setVendorInvoiceNumber] = useState<string>('');
  const [vendorInvoiceDate, setVendorInvoiceDate] = useState<string>('');
  const [billDate, setBillDate] = useState<string>(new Date().toISOString().split('T')[0]);
  const [dueDate, setDueDate] = useState<string>('');
  const [placeOfSupply, setPlaceOfSupply] = useState<string>('');
  const [isReverseCharge, setIsReverseCharge] = useState(false);
  const [tdsAmount, setTdsAmount] = useState<number>(0);
  const [roundOff, setRoundOff] = useState<number>(0);
  const [narration, setNarration] = useState<string>('');
  const [referenceNumber, setReferenceNumber] = useState<string>('');

  const [lines, setLines] = useState<BillLine[]>([createEmptyLine(1)]);

  // Computed totals
  const [subtotal, setSubtotal] = useState(0);
  const [totalDiscount, setTotalDiscount] = useState(0);
  const [totalTaxable, setTotalTaxable] = useState(0);
  const [totalCgst, setTotalCgst] = useState(0);
  const [totalSgst, setTotalSgst] = useState(0);
  const [totalIgst, setTotalIgst] = useState(0);
  const [totalCess, setTotalCess] = useState(0);
  const [grandTotal, setGrandTotal] = useState(0);

  function createEmptyLine(lineNumber: number): BillLine {
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
      expense_account_id: '',
    };
  }

  useEffect(() => {
    loadOrganizations();
  }, []);

  useEffect(() => {
    if (selectedOrgId) {
      loadUnits();
      loadVendors();
      loadGstRates();
      loadExpenseAccounts();
    }
  }, [selectedOrgId]);

  useEffect(() => {
    if (isEdit && id && selectedOrgId) {
      loadBill(id);
    }
  }, [id, isEdit, selectedOrgId]);

  useEffect(() => {
    calculateTotals();
  }, [lines, tdsAmount, roundOff]);

  useEffect(() => {
    // Auto-set place of supply when vendor changes
    if (vendorId) {
      const vendor = vendors.find((v) => v.id === vendorId);
      if (vendor?.state_code) {
        setPlaceOfSupply(vendor.state_code);
      }
    }
  }, [vendorId, vendors]);

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
        // Get org's state code from first GST registration
        // For now, using a default state code (27 = Maharashtra)
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

  const loadVendors = async () => {
    if (!selectedOrgId) return;
    try {
      const response = await vendorsApi.getActive({ organization_id: selectedOrgId });
      setVendors(response.data || []);
    } catch (error) {
      console.error('Failed to load vendors:', error);
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

  const loadExpenseAccounts = async () => {
    if (!selectedOrgId) return;
    try {
      const response = await accountsApi.list({
        organization_id: selectedOrgId,
        page_size: 200,
      });
      // Filter for expense accounts (nature = EXPENSES)
      const accounts = response.data.items || [];
      setExpenseAccounts(accounts);
    } catch (error) {
      console.error('Failed to load accounts:', error);
    }
  };

  const loadBill = async (billId: string) => {
    try {
      setLoading(true);
      const response = await purchaseBillsApi.get(billId);
      const bill = response.data;

      setSelectedOrgId(bill.organization_id);
      setUnitId(bill.unit_id || '');
      setVendorId(bill.vendor_id);
      setVendorInvoiceNumber(bill.vendor_invoice_number || '');
      setVendorInvoiceDate(bill.vendor_invoice_date || '');
      setBillDate(bill.bill_date);
      setDueDate(bill.due_date);
      setPlaceOfSupply(bill.place_of_supply || '');
      setIsReverseCharge(bill.is_reverse_charge || false);
      setTdsAmount(bill.tds_amount || 0);
      setRoundOff(bill.round_off || 0);
      setNarration(bill.narration || '');
      setReferenceNumber(bill.reference_number || '');

      if (bill.lines && bill.lines.length > 0) {
        setLines(
          bill.lines.map((line: any) => ({
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
            expense_account_id: line.expense_account_id || '',
          }))
        );
      }
    } catch (error) {
      console.error('Failed to load bill:', error);
      toast({
        title: 'Error',
        description: 'Failed to load purchase bill',
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

  const calculateLine = (line: BillLine): BillLine => {
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
    setGrandTotal(taxable + cgst + sgst + igst + cess - tdsAmount + roundOff);
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

  const handleLineChange = (index: number, field: keyof BillLine, value: any) => {
    const newLines = [...lines];
    (newLines[index] as any)[field] = value;

    // Recalculate line when relevant fields change
    if (['quantity', 'unit_price', 'discount_percent', 'discount_amount', 'gst_rate_id'].includes(field)) {
      newLines[index] = calculateLine(newLines[index]);
    }

    setLines(newLines);
  };

  const onSubmit = async () => {
    if (!vendorId) {
      toast({
        title: 'Error',
        description: 'Please select a vendor',
        variant: 'destructive',
      });
      return;
    }

    if (!billDate || !dueDate) {
      toast({
        title: 'Error',
        description: 'Please enter bill date and due date',
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

      const billData = {
        vendor_id: vendorId,
        vendor_invoice_number: vendorInvoiceNumber || undefined,
        vendor_invoice_date: vendorInvoiceDate || undefined,
        bill_date: billDate,
        due_date: dueDate,
        organization_id: selectedOrgId,
        unit_id: unitId || undefined,
        place_of_supply: placeOfSupply || undefined,
        is_reverse_charge: isReverseCharge,
        supply_type: isIntraState() ? 'INTRA_STATE' : 'INTER_STATE',
        tds_amount: tdsAmount,
        round_off: roundOff,
        narration: narration || undefined,
        reference_number: referenceNumber || undefined,
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
            expense_account_id: l.expense_account_id || undefined,
          })),
      };

      if (isEdit && id) {
        await purchaseBillsApi.update(id, billData);
        toast({
          title: 'Success',
          description: 'Purchase bill updated successfully',
        });
      } else {
        await purchaseBillsApi.create(billData);
        toast({
          title: 'Success',
          description: 'Purchase bill created successfully',
        });
      }

      navigate('/admin/ap-ar/purchase-bills');
    } catch (error: any) {
      console.error('Failed to save purchase bill:', error);
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to save purchase bill',
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
        title={isEdit ? 'Edit Purchase Bill' : 'New Purchase Bill'}
        subtitle={
          isEdit
            ? 'Update purchase bill details'
            : 'Create a new purchase bill / vendor invoice'
        }
        breadcrumbs={[
          { label: 'Purchase Bills', to: '/admin/ap-ar/purchase-bills' },
          { label: isEdit ? 'Edit' : 'New' },
        ]}
      />

      <div className="space-y-6">
        {/* Header Section */}
        <Card>
          <CardHeader>
            <CardTitle>Bill Details</CardTitle>
            <CardDescription>Basic purchase bill information</CardDescription>
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
                <Label>Vendor *</Label>
                <Select value={vendorId} onValueChange={setVendorId}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select vendor" />
                  </SelectTrigger>
                  <SelectContent>
                    {vendors.map((vendor) => (
                      <SelectItem key={vendor.id} value={vendor.id}>
                        {vendor.code} - {vendor.name}
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
                <Label>Vendor Invoice No.</Label>
                <Input
                  value={vendorInvoiceNumber}
                  onChange={(e) => setVendorInvoiceNumber(e.target.value)}
                  placeholder="Vendor's invoice number"
                />
              </div>
              <div className="space-y-2">
                <Label>Vendor Invoice Date</Label>
                <Input
                  type="date"
                  value={vendorInvoiceDate}
                  onChange={(e) => setVendorInvoiceDate(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label>Bill Date *</Label>
                <Input
                  type="date"
                  value={billDate}
                  onChange={(e) => setBillDate(e.target.value)}
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
            </div>

            <div className="grid gap-4 md:grid-cols-4">
              <div className="space-y-2">
                <Label>Reference Number</Label>
                <Input
                  value={referenceNumber}
                  onChange={(e) => setReferenceNumber(e.target.value)}
                  placeholder="Optional reference"
                />
              </div>
              <div className="flex items-center gap-2 pt-8">
                <Checkbox
                  id="reverseCharge"
                  checked={isReverseCharge}
                  onCheckedChange={(checked) => setIsReverseCharge(checked === true)}
                />
                <label htmlFor="reverseCharge" className="text-sm">
                  Reverse Charge Applicable
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
                    <TableHead className="w-[150px]">Expense A/c</TableHead>
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
                          value={line.expense_account_id || undefined}
                          onValueChange={(value) => handleLineChange(index, 'expense_account_id', value)}
                        >
                          <SelectTrigger>
                            <SelectValue placeholder="Account" />
                          </SelectTrigger>
                          <SelectContent>
                            {expenseAccounts.map((acc) => (
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
                placeholder="Enter bill narration or notes..."
                rows={4}
              />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Bill Summary</CardTitle>
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
                <span className="text-slate-600">TDS</span>
                <Input
                  type="number"
                  step="0.01"
                  min="0"
                  className="w-32 text-right"
                  value={tdsAmount || ''}
                  onChange={(e) => setTdsAmount(parseFloat(e.target.value) || 0)}
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
          <Button type="button" variant="outline" onClick={() => navigate('/admin/ap-ar/purchase-bills')}>
            Cancel
          </Button>
          <Button onClick={onSubmit} disabled={submitting}>
            {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            <Save className="mr-2 h-4 w-4" />
            {isEdit ? 'Update Bill' : 'Create Bill'}
          </Button>
        </div>
      </div>
    </div>
  );
}
