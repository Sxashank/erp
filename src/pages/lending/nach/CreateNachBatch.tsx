/**
 * Create NACH Batch Page
 * Generate a new NACH batch from due EMIs
 */

import { Calendar, Search, AlertCircle, Loader2, FileText } from 'lucide-react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { PageHeader } from '@/components/common/PageHeader';
import { AmountDisplay } from '@/components/lending/common/AmountDisplay';
import { DateDisplay } from '@/components/lending/common/DateDisplay';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
  CardFooter,
} from '@/components/ui/card';
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
import { useCreateNachBatch, extractNachErrorMessage } from '@/hooks/lending/useNachBatches';
import { useToast } from '@/hooks/use-toast';
import { useRequiredActiveOrganizationId } from '@/hooks/useOrganization';

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

// Due EMIs load from /lending/nach/due-emis (TBD) once the BE endpoint
// is wired — it should return EMIs falling due in the next N days with
// the borrower's NACH mandate joined in. Until then, the list starts
// empty so the wizard doesn't surface fabricated due dates.
const initialDueEMIs: DueEMI[] = [];

const mandateStatusConfig: Record<string, { label: string; color: string }> = {
  ACTIVE: { label: 'Active', color: 'bg-green-100 text-green-700' },
  PENDING: { label: 'Pending', color: 'bg-amber-100 text-amber-700' },
  EXPIRED: { label: 'Expired', color: 'bg-red-100 text-red-700' },
};

export default function CreateNachBatch() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const organizationId = useRequiredActiveOrganizationId();
  const createBatch = useCreateNachBatch();
  const [searchQuery, setSearchQuery] = useState('');
  const [provider, setProvider] = useState('RAZORPAY');
  const [debitDate, setDebitDate] = useState('');
  const [dueEMIs, setDueEMIs] = useState<DueEMI[]>(initialDueEMIs);

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
      })),
    );
  };

  const handleSelectEMI = (id: string, checked: boolean) => {
    setDueEMIs(dueEMIs.map((emi) => (emi.id === id ? { ...emi, selected: checked } : emi)));
  };

  const handleGenerateBatch = () => {
    if (!debitDate) {
      toast({
        title: 'Debit date required',
        description: 'Pick a debit date before generating the batch.',
        variant: 'destructive',
      });
      return;
    }

    // Pass the selected loan accounts when the operator narrowed the set;
    // otherwise let the backend scan all due EMIs for the org. The form
    // does not currently expose a product / DPD filter — the BE defaults
    // (includeOverdue=true, maxDpd=90) apply.
    const loanAccountIds = selectedEMIs.map((emi) => emi.loanAccountId);

    createBatch.mutate(
      {
        organizationId,
        debitDate,
        ...(loanAccountIds.length > 0 ? { loanAccountIds } : {}),
      },
      {
        onSuccess: (batch) => {
          toast({
            title: 'NACH batch generated',
            description: `Batch ${batch.batchReference} created with ${batch.totalTransactions} transactions.`,
          });
          navigate('/admin/lending/nach/batches');
        },
        onError: (err) => {
          toast({
            title: 'Failed to generate batch',
            description: extractNachErrorMessage(err, 'Could not generate NACH batch.'),
            variant: 'destructive',
          });
        },
      },
    );
  };

  const allSelected = eligibleEMIs.length > 0 && eligibleEMIs.every((emi) => emi.selected);
  const someSelected = eligibleEMIs.some((emi) => emi.selected) && !allSelected;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Generate NACH Batch"
        subtitle="Create a new batch from due EMIs with active mandates"
        breadcrumbs={[
          { label: 'NACH Batches', to: '/admin/lending/nach/batches' },
          { label: 'New Batch' },
        ]}
      />

      {/* Configuration */}
      <Card>
        <CardHeader>
          <CardTitle>Batch Configuration</CardTitle>
          <CardDescription>Set the provider and debit date for this batch</CardDescription>
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
              <p className="text-xs text-muted-foreground">EMIs with active mandates</p>
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
            {ineligibleEMIs.length} EMI(s) cannot be included in this batch due to inactive or
            missing mandates. Please register mandates for these accounts.
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
                className="w-[300px] pl-8"
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
                    onCheckedChange={(checked) => handleSelectAll(checked as boolean)}
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
                  <TableCell colSpan={8} className="py-8 text-center text-muted-foreground">
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
                          onCheckedChange={(checked) => handleSelectEMI(emi.id, checked as boolean)}
                          disabled={emi.mandateStatus !== 'ACTIVE'}
                          aria-label={`Select ${emi.loanAccountNumber}`}
                        />
                      </TableCell>
                      <TableCell className="font-mono text-sm">{emi.loanAccountNumber}</TableCell>
                      <TableCell className="max-w-[200px] truncate">{emi.borrowerName}</TableCell>
                      <TableCell>
                        <div className="space-y-1">
                          <Badge variant="outline" className={mandateStatus.color}>
                            {mandateStatus.label}
                          </Badge>
                          {emi.umrn && (
                            <div className="font-mono text-xs text-muted-foreground">
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
                          className={emi.dpd === 0 ? 'bg-green-100 text-green-700' : ''}
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
            <Button variant="outline" onClick={() => navigate('/admin/lending/nach/batches')}>
              Cancel
            </Button>
            <Button onClick={handleGenerateBatch} disabled={!debitDate || createBatch.isPending}>
              {createBatch.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Generating...
                </>
              ) : (
                <>
                  <FileText className="mr-2 h-4 w-4" />
                  Generate Batch{selectedEMIs.length > 0 ? ` (${selectedEMIs.length})` : ''}
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
              These EMIs cannot be included. Register mandates to enable NACH collection.
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
                      <TableCell className="font-mono text-sm">{emi.loanAccountNumber}</TableCell>
                      <TableCell className="max-w-[200px] truncate">{emi.borrowerName}</TableCell>
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
                          className="h-auto p-0"
                          onClick={() => navigate(`/admin/lending/accounts/${emi.loanAccountId}`)}
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
