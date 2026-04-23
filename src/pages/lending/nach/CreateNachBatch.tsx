/**
 * Create NACH Batch Page
 * Generate a new NACH batch from due EMIs
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Calendar,
  Search,
  CheckCircle,
  AlertCircle,
  Loader2,
  FileText,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { AmountDisplay } from '@/components/lending/common/AmountDisplay';
import { DateDisplay } from '@/components/lending/common/DateDisplay';

interface DueEMI {
  id: string;
  loanAccountId: string;
  loanAccountNumber: string;
  borrowerName: string;
  umrn: string;
  mandateStatus: 'ACTIVE' | 'PENDING' | 'EXPIRED';
  bankName: string;
  accountNumberMasked: string;
  emiAmount: number;
  dueDate: string;
  emiNumber: number;
  dpd: number;
  selected: boolean;
}

// Mock data for due EMIs
const mockDueEMIs: DueEMI[] = [
  {
    id: '1',
    loanAccountId: 'la1',
    loanAccountNumber: 'SMFC/TL/DEL/2024/L00001',
    borrowerName: 'ABC Industries Private Limited',
    umrn: 'RATN50000000001234',
    mandateStatus: 'ACTIVE',
    bankName: 'HDFC Bank',
    accountNumberMasked: 'XXXX1234',
    emiAmount: 125000,
    dueDate: '2025-01-15',
    emiNumber: 5,
    dpd: 0,
    selected: true,
  },
  {
    id: '2',
    loanAccountId: 'la2',
    loanAccountNumber: 'SMFC/WC/MUM/2024/L00089',
    borrowerName: 'XYZ Traders LLP',
    umrn: 'RATN50000000001235',
    mandateStatus: 'ACTIVE',
    bankName: 'ICICI Bank',
    accountNumberMasked: 'XXXX5678',
    emiAmount: 225000,
    dueDate: '2025-01-15',
    emiNumber: 8,
    dpd: 0,
    selected: true,
  },
  {
    id: '3',
    loanAccountId: 'la3',
    loanAccountNumber: 'SMFC/LAP/BLR/2024/L00045',
    borrowerName: 'Tech Solutions India Pvt Ltd',
    umrn: 'RATN50000000001236',
    mandateStatus: 'ACTIVE',
    bankName: 'Axis Bank',
    accountNumberMasked: 'XXXX9012',
    emiAmount: 150000,
    dueDate: '2025-01-15',
    emiNumber: 12,
    dpd: 0,
    selected: true,
  },
  {
    id: '4',
    loanAccountId: 'la4',
    loanAccountNumber: 'SMFC/TL/CHN/2023/L00034',
    borrowerName: 'Southern Motors Corp',
    umrn: '',
    mandateStatus: 'PENDING',
    bankName: 'SBI',
    accountNumberMasked: 'XXXX3456',
    emiAmount: 100000,
    dueDate: '2025-01-15',
    emiNumber: 15,
    dpd: 5,
    selected: false,
  },
  {
    id: '5',
    loanAccountId: 'la5',
    loanAccountNumber: 'SMFC/WC/KOL/2024/L00067',
    borrowerName: 'Eastern Exports Ltd',
    umrn: 'RATN50000000001238',
    mandateStatus: 'ACTIVE',
    bankName: 'Punjab National Bank',
    accountNumberMasked: 'XXXX7890',
    emiAmount: 175000,
    dueDate: '2025-01-15',
    emiNumber: 3,
    dpd: 0,
    selected: true,
  },
  {
    id: '6',
    loanAccountId: 'la6',
    loanAccountNumber: 'SMFC/TL/HYD/2024/L00078',
    borrowerName: 'Deccan Enterprises',
    umrn: 'RATN50000000001239',
    mandateStatus: 'ACTIVE',
    bankName: 'Kotak Mahindra Bank',
    accountNumberMasked: 'XXXX2345',
    emiAmount: 95000,
    dueDate: '2025-01-15',
    emiNumber: 6,
    dpd: 0,
    selected: true,
  },
  {
    id: '7',
    loanAccountId: 'la7',
    loanAccountNumber: 'SMFC/LAP/PUN/2024/L00090',
    borrowerName: 'Western Infra Projects',
    umrn: 'RATN50000000001240',
    mandateStatus: 'EXPIRED',
    bankName: 'Bank of Baroda',
    accountNumberMasked: 'XXXX6789',
    emiAmount: 125000,
    dueDate: '2025-01-15',
    emiNumber: 4,
    dpd: 10,
    selected: false,
  },
  {
    id: '8',
    loanAccountId: 'la8',
    loanAccountNumber: 'SMFC/WC/AHM/2024/L00056',
    borrowerName: 'Gujarat Textiles Pvt Ltd',
    umrn: 'RATN50000000001241',
    mandateStatus: 'ACTIVE',
    bankName: 'Yes Bank',
    accountNumberMasked: 'XXXX0123',
    emiAmount: 80000,
    dueDate: '2025-01-15',
    emiNumber: 9,
    dpd: 0,
    selected: true,
  },
];

const mandateStatusConfig: Record<
  string,
  { label: string; color: string }
> = {
  ACTIVE: { label: 'Active', color: 'bg-green-100 text-green-700' },
  PENDING: { label: 'Pending', color: 'bg-amber-100 text-amber-700' },
  EXPIRED: { label: 'Expired', color: 'bg-red-100 text-red-700' },
};

export default function CreateNachBatch() {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [provider, setProvider] = useState('RAZORPAY');
  const [debitDate, setDebitDate] = useState('');
  const [dueEMIs, setDueEMIs] = useState<DueEMI[]>(mockDueEMIs);

  // Filter EMIs with active mandates
  const eligibleEMIs = dueEMIs.filter((emi) => emi.mandateStatus === 'ACTIVE');
  const ineligibleEMIs = dueEMIs.filter((emi) => emi.mandateStatus !== 'ACTIVE');

  const filteredEMIs = eligibleEMIs.filter((emi) => {
    return (
      emi.loanAccountNumber.toLowerCase().includes(searchQuery.toLowerCase()) ||
      emi.borrowerName.toLowerCase().includes(searchQuery.toLowerCase())
    );
  });

  const selectedEMIs = dueEMIs.filter((emi) => emi.selected && emi.mandateStatus === 'ACTIVE');
  const totalAmount = selectedEMIs.reduce((sum, emi) => sum + emi.emiAmount, 0);

  const handleSelectAll = (checked: boolean) => {
    setDueEMIs(
      dueEMIs.map((emi) => ({
        ...emi,
        selected: emi.mandateStatus === 'ACTIVE' ? checked : false,
      }))
    );
  };

  const handleSelectEMI = (id: string, checked: boolean) => {
    setDueEMIs(
      dueEMIs.map((emi) =>
        emi.id === id ? { ...emi, selected: checked } : emi
      )
    );
  };

  const handleGenerateBatch = async () => {
    if (selectedEMIs.length === 0) {
      return;
    }

    setIsSubmitting(true);
    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 2000));
    setIsSubmitting(false);

    // Navigate to batch list
    navigate('/admin/lending/nach/batches');
  };

  const allSelected =
    eligibleEMIs.length > 0 && eligibleEMIs.every((emi) => emi.selected);
  const someSelected =
    eligibleEMIs.some((emi) => emi.selected) && !allSelected;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => navigate('/admin/lending/nach/batches')}
        >
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div>
          <h1 className="text-2xl font-semibold">Generate NACH Batch</h1>
          <p className="text-muted-foreground">
            Create a new batch from due EMIs with active mandates
          </p>
        </div>
      </div>

      {/* Configuration */}
      <Card>
        <CardHeader>
          <CardTitle>Batch Configuration</CardTitle>
          <CardDescription>
            Set the provider and debit date for this batch
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-6 md:grid-cols-3">
            <div className="space-y-2">
              <Label htmlFor="provider">NACH Provider</Label>
              <Select value={provider} onValueChange={setProvider}>
                <SelectTrigger id="provider">
                  <SelectValue placeholder="Select provider" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="RAZORPAY">Razorpay NACH</SelectItem>
                  <SelectItem value="CASHFREE">Cashfree Auto-Collect</SelectItem>
                  <SelectItem value="NPCI_DIRECT">NPCI Direct</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="debitDate">Debit Date</Label>
              <div className="relative">
                <Calendar className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input
                  id="debitDate"
                  type="date"
                  value={debitDate}
                  onChange={(e) => setDebitDate(e.target.value)}
                  className="pl-10"
                  min={new Date().toISOString().split('T')[0]}
                />
              </div>
              <p className="text-xs text-muted-foreground">
                Minimum T+2 working days from submission
              </p>
            </div>
            <div className="space-y-2">
              <Label>Due EMIs</Label>
              <div className="text-3xl font-bold">{eligibleEMIs.length}</div>
              <p className="text-xs text-muted-foreground">
                EMIs with active mandates
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Ineligible EMIs Alert */}
      {ineligibleEMIs.length > 0 && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Ineligible EMIs</AlertTitle>
          <AlertDescription>
            {ineligibleEMIs.length} EMI(s) cannot be included in this batch due to
            inactive or missing mandates. Please register mandates for these
            accounts.
          </AlertDescription>
        </Alert>
      )}

      {/* EMI Selection */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Select EMIs for Batch</CardTitle>
              <CardDescription>
                Choose which EMIs to include in this NACH presentation
              </CardDescription>
            </div>
            <div className="relative">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search by account or borrower..."
                className="pl-8 w-[300px]"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[50px]">
                  <Checkbox
                    checked={allSelected}
                    onCheckedChange={(checked) =>
                      handleSelectAll(checked as boolean)
                    }
                    aria-label="Select all"
                    className={someSelected ? 'data-[state=checked]:bg-muted' : ''}
                  />
                </TableHead>
                <TableHead>Loan Account</TableHead>
                <TableHead>Borrower</TableHead>
                <TableHead>Mandate</TableHead>
                <TableHead>Bank</TableHead>
                <TableHead className="text-right">EMI Amount</TableHead>
                <TableHead>Due Date</TableHead>
                <TableHead className="text-center">DPD</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredEMIs.length === 0 ? (
                <TableRow>
                  <TableCell
                    colSpan={8}
                    className="text-center py-8 text-muted-foreground"
                  >
                    No eligible EMIs found
                  </TableCell>
                </TableRow>
              ) : (
                filteredEMIs.map((emi) => {
                  const mandateStatus = mandateStatusConfig[emi.mandateStatus];
                  return (
                    <TableRow key={emi.id}>
                      <TableCell>
                        <Checkbox
                          checked={emi.selected}
                          onCheckedChange={(checked) =>
                            handleSelectEMI(emi.id, checked as boolean)
                          }
                          disabled={emi.mandateStatus !== 'ACTIVE'}
                          aria-label={`Select ${emi.loanAccountNumber}`}
                        />
                      </TableCell>
                      <TableCell className="font-mono text-sm">
                        {emi.loanAccountNumber}
                      </TableCell>
                      <TableCell className="max-w-[200px] truncate">
                        {emi.borrowerName}
                      </TableCell>
                      <TableCell>
                        <div className="space-y-1">
                          <Badge
                            variant="outline"
                            className={mandateStatus.color}
                          >
                            {mandateStatus.label}
                          </Badge>
                          {emi.umrn && (
                            <div className="text-xs text-muted-foreground font-mono">
                              {emi.umrn}
                            </div>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div>{emi.bankName}</div>
                        <div className="text-xs text-muted-foreground">
                          {emi.accountNumberMasked}
                        </div>
                      </TableCell>
                      <TableCell className="text-right">
                        <AmountDisplay amount={emi.emiAmount} />
                      </TableCell>
                      <TableCell>
                        <DateDisplay date={emi.dueDate} />
                      </TableCell>
                      <TableCell className="text-center">
                        <Badge
                          variant={emi.dpd > 0 ? 'destructive' : 'secondary'}
                          className={
                            emi.dpd === 0
                              ? 'bg-green-100 text-green-700'
                              : ''
                          }
                        >
                          {emi.dpd}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>
        </CardContent>
        <CardFooter className="flex items-center justify-between border-t p-4">
          <div className="flex items-center gap-6">
            <div>
              <span className="text-sm text-muted-foreground">Selected:</span>
              <span className="ml-2 font-semibold">{selectedEMIs.length}</span>
              <span className="text-muted-foreground"> of {eligibleEMIs.length}</span>
            </div>
            <div>
              <span className="text-sm text-muted-foreground">Total Amount:</span>
              <AmountDisplay amount={totalAmount} className="ml-2 font-semibold" />
            </div>
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={() => navigate('/admin/lending/nach/batches')}
            >
              Cancel
            </Button>
            <Button
              onClick={handleGenerateBatch}
              disabled={selectedEMIs.length === 0 || !debitDate || isSubmitting}
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Generating...
                </>
              ) : (
                <>
                  <FileText className="mr-2 h-4 w-4" />
                  Generate Batch ({selectedEMIs.length})
                </>
              )}
            </Button>
          </div>
        </CardFooter>
      </Card>

      {/* Ineligible EMIs Table */}
      {ineligibleEMIs.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-amber-600">
              <AlertCircle className="h-5 w-5" />
              EMIs Without Active Mandates ({ineligibleEMIs.length})
            </CardTitle>
            <CardDescription>
              These EMIs cannot be included. Register mandates to enable NACH
              collection.
            </CardDescription>
          </CardHeader>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Loan Account</TableHead>
                  <TableHead>Borrower</TableHead>
                  <TableHead>Mandate Status</TableHead>
                  <TableHead className="text-right">EMI Amount</TableHead>
                  <TableHead>Due Date</TableHead>
                  <TableHead>Action</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {ineligibleEMIs.map((emi) => {
                  const mandateStatus = mandateStatusConfig[emi.mandateStatus];
                  return (
                    <TableRow key={emi.id} className="bg-muted/30">
                      <TableCell className="font-mono text-sm">
                        {emi.loanAccountNumber}
                      </TableCell>
                      <TableCell className="max-w-[200px] truncate">
                        {emi.borrowerName}
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline" className={mandateStatus.color}>
                          {mandateStatus.label}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <AmountDisplay amount={emi.emiAmount} />
                      </TableCell>
                      <TableCell>
                        <DateDisplay date={emi.dueDate} />
                      </TableCell>
                      <TableCell>
                        <Button
                          variant="link"
                          size="sm"
                          className="p-0 h-auto"
                          onClick={() =>
                            navigate(
                              `/admin/lending/accounts/${emi.loanAccountId}`
                            )
                          }
                        >
                          Register Mandate
                        </Button>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
