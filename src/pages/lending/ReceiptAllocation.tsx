import { Receipt, Check, AlertCircle, Calculator } from 'lucide-react';
import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

import { PageHeader } from '@/components/common/PageHeader';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import { Input } from '@/components/ui/input';
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
import {
  useAllocateReceipt,
  type AllocationMethod,
  type SpecificAllocation,
} from '@/hooks/lending/useReceipts';
import { useToast } from '@/hooks/use-toast';
import { showErrorToast } from '@/lib/errorToast';
import { formatCurrency, formatDate } from '@/lib/utils';

// Receipt + outstanding-demand wiring. Loads from
// GET /lending/receipts/{id} and GET /lending/loan-accounts/{la_id}/demands.
// Render-empty until those hooks land.
const receiptDetails = {
  id: '',
  receiptNumber: '',
  loanAccount: '',
  entity: '',
  receiptDate: '',
  valueDate: '',
  totalAmount: 0,
  allocatedAmount: 0,
  unallocatedAmount: 0,
  receiptType: '',
  receiptMode: '',
};

interface OutstandingDemand {
  id: string;
  demand_date: string;
  due_date: string;
  demand_type: string;
  principal: number;
  interest: number;
  penalty: number;
  other_charges: number;
  total: number;
  paid: number;
  outstanding: number;
  overdue_days: number;
  selected: boolean;
  allocated: number;
}

const outstandingDemands: OutstandingDemand[] = [];

export default function ReceiptAllocation() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const { id } = useParams();
  const [showSuccess, setShowSuccess] = useState(false);
  const [allocationMethod, setAllocationMethod] = useState<'FIFO' | 'PROPORTIONAL' | 'SPECIFIC'>(
    'FIFO',
  );
  const [demands, setDemands] = useState(outstandingDemands);
  const allocateReceipt = useAllocateReceipt();

  const handleSelectDemand = (demandId: string, checked: boolean) => {
    setDemands(demands.map((d) => (d.id === demandId ? { ...d, selected: checked } : d)));
  };

  const handleAllocationChange = (demandId: string, amount: string) => {
    const value = parseFloat(amount) || 0;
    setDemands(demands.map((d) => (d.id === demandId ? { ...d, allocated: value } : d)));
  };

  const totalAllocated = demands.reduce((sum, d) => sum + d.allocated, 0);
  const unallocatedBalance = receiptDetails.unallocatedAmount - totalAllocated;

  const handleAutoAllocate = () => {
    let remaining = receiptDetails.unallocatedAmount;
    const sorted = [...demands].filter((d) => d.outstanding > 0);

    if (allocationMethod === 'FIFO') {
      // Sort by due date (oldest first)
      sorted.sort((a, b) => new Date(a.due_date).getTime() - new Date(b.due_date).getTime());
    } else if (allocationMethod === 'PROPORTIONAL') {
      // Allocate proportionally based on outstanding amounts
      const totalOutstanding = sorted.reduce((sum, d) => sum + d.outstanding, 0);
      setDemands(
        demands.map((d) => {
          if (d.outstanding > 0) {
            const proportion = d.outstanding / totalOutstanding;
            const allocated = Math.min(d.outstanding, Math.round(remaining * proportion));
            return { ...d, allocated, selected: true };
          }
          return d;
        }),
      );
      return;
    }

    // FIFO allocation
    const updatedDemands = demands.map((d) => {
      if (remaining <= 0 || d.outstanding <= 0) {
        return { ...d, allocated: 0, selected: false };
      }
      const allocation = Math.min(d.outstanding, remaining);
      remaining -= allocation;
      return { ...d, allocated: allocation, selected: allocation > 0 };
    });

    setDemands(updatedDemands);
  };

  const handleClearAllocation = () => {
    setDemands(demands.map((d) => ({ ...d, allocated: 0, selected: false })));
  };

  const handleSubmit = async () => {
    if (!id) {
      toast({
        title: 'Receipt id missing',
        description: 'Cannot allocate without a receipt identifier in the URL.',
        variant: 'destructive',
      });
      return;
    }
    try {
      const methodLower = allocationMethod.toLowerCase() as AllocationMethod;
      const specificAllocations: SpecificAllocation[] | undefined =
        methodLower === 'specific'
          ? demands
              .filter((d) => d.allocated > 0)
              .map((d) => ({
                installmentId: d.id,
                // BE expects the receipt allocation priority bucket. Default
                // here is current principal — when a richer demand-shape
                // ships (interest/principal split per row), this should be
                // multi-row per demand. For now SPECIFIC mode is best effort.
                component: 'CURRENT_PRINCIPAL' as const,
                amount: d.allocated,
              }))
          : undefined;
      await allocateReceipt.mutateAsync({
        receiptId: id,
        allocationMethod: methodLower,
        specificAllocations,
      });
      toast({
        title: 'Receipt allocated',
        description: `Allocated ${formatCurrency(totalAllocated)} across ${
          demands.filter((d) => d.allocated > 0).length
        } demand(s).`,
      });
      setShowSuccess(true);
    } catch (err) {
      showErrorToast(err, toast);
    }
  };

  if (showSuccess) {
    return (
      <div className="flex min-h-[60vh] flex-col items-center justify-center">
        <div className="text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-green-100">
            <Check className="h-8 w-8 text-green-600" />
          </div>
          <h2 className="mb-2 text-2xl font-bold">Receipt Allocated Successfully</h2>
          <p className="mb-2 text-muted-foreground">
            Amount allocated: {formatCurrency(totalAllocated)}
          </p>
          {unallocatedBalance > 0 && (
            <p className="mb-6 text-orange-600">
              Unallocated balance: {formatCurrency(unallocatedBalance)}
            </p>
          )}
          <div className="flex justify-center gap-4">
            <Button variant="outline" onClick={() => navigate('/admin/lending/receipts')}>
              View All Receipts
            </Button>
            <Button variant="outline" onClick={() => navigate(`/admin/lending/receipts/${id}`)}>
              View Receipt Details
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Allocate Receipt"
        subtitle={`${receiptDetails.receiptNumber} - ${receiptDetails.entity}`}
        breadcrumbs={[{ label: 'Receipts', to: '/admin/lending/receipts' }, { label: 'Allocate' }]}
      />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Allocation Table */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Outstanding Demands</CardTitle>
                <CardDescription>Select demands to allocate the receipt</CardDescription>
              </div>
              <div className="flex gap-2">
                <Select
                  value={allocationMethod}
                  onValueChange={(v) =>
                    setAllocationMethod(v as 'FIFO' | 'PROPORTIONAL' | 'SPECIFIC')
                  }
                >
                  <SelectTrigger className="w-40">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="FIFO">FIFO (Oldest First)</SelectItem>
                    <SelectItem value="PROPORTIONAL">Proportional</SelectItem>
                    <SelectItem value="SPECIFIC">Specific Selection</SelectItem>
                  </SelectContent>
                </Select>
                <Button variant="outline" onClick={handleAutoAllocate}>
                  <Calculator className="mr-2 h-4 w-4" />
                  Auto Allocate
                </Button>
                <Button variant="ghost" onClick={handleClearAllocation}>
                  Clear
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-10"></TableHead>
                  <TableHead>Due Date</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead className="text-right">Principal</TableHead>
                  <TableHead className="text-right">Interest</TableHead>
                  <TableHead className="text-right">Penalty</TableHead>
                  <TableHead className="text-right">Outstanding</TableHead>
                  <TableHead className="text-right">Allocate</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {demands
                  .filter((d) => d.outstanding > 0)
                  .map((demand) => (
                    <TableRow key={demand.id}>
                      <TableCell>
                        <Checkbox
                          checked={demand.selected}
                          onCheckedChange={(checked) =>
                            handleSelectDemand(demand.id, checked as boolean)
                          }
                        />
                      </TableCell>
                      <TableCell>
                        <div className="text-sm">{formatDate(demand.due_date)}</div>
                        {demand.overdue_days > 0 && (
                          <Badge variant="destructive" className="text-xs">
                            {demand.overdue_days} days overdue
                          </Badge>
                        )}
                      </TableCell>
                      <TableCell>
                        <Badge variant="outline">{demand.demand_type}</Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        {formatCurrency(demand.principal)}
                      </TableCell>
                      <TableCell className="text-right">
                        {formatCurrency(demand.interest)}
                      </TableCell>
                      <TableCell className="text-right">
                        {demand.penalty > 0 ? (
                          <span className="text-red-600">{formatCurrency(demand.penalty)}</span>
                        ) : (
                          '-'
                        )}
                      </TableCell>
                      <TableCell className="text-right font-medium">
                        {formatCurrency(demand.outstanding)}
                      </TableCell>
                      <TableCell className="text-right">
                        <Input
                          type="number"
                          className="w-28 text-right"
                          value={demand.allocated || ''}
                          onChange={(e) => handleAllocationChange(demand.id, e.target.value)}
                          max={Math.min(demand.outstanding, unallocatedBalance + demand.allocated)}
                        />
                      </TableCell>
                    </TableRow>
                  ))}
              </TableBody>
            </Table>

            {demands.filter((d) => d.outstanding > 0).length === 0 && (
              <div className="py-8 text-center text-muted-foreground">
                No outstanding demands found
              </div>
            )}

            <div className="mt-6 flex justify-end gap-4">
              <Button type="button" variant="outline" onClick={() => navigate(-1)}>
                Cancel
              </Button>
              <Button
                onClick={handleSubmit}
                disabled={
                  allocateReceipt.isPending ||
                  (allocationMethod === 'SPECIFIC' && totalAllocated === 0)
                }
              >
                <Receipt className="mr-2 h-4 w-4" />
                {allocateReceipt.isPending ? 'Allocating...' : 'Confirm Allocation'}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Summary Panel */}
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Receipt Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <p className="text-sm text-muted-foreground">Receipt Number</p>
                <p className="font-mono">{receiptDetails.receiptNumber}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Loan Account</p>
                <p className="font-mono">{receiptDetails.loanAccount}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Receipt Date</p>
                <p>{formatDate(receiptDetails.receiptDate)}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Receipt Mode</p>
                <Badge variant="outline">{receiptDetails.receiptMode}</Badge>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Allocation Summary</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <p className="text-sm text-muted-foreground">Total Receipt Amount</p>
                <p className="text-2xl font-bold">{formatCurrency(receiptDetails.totalAmount)}</p>
              </div>

              <div className="border-t pt-4">
                <p className="text-sm text-muted-foreground">Already Allocated</p>
                <p className="font-medium">{formatCurrency(receiptDetails.allocatedAmount)}</p>
              </div>

              <div>
                <p className="text-sm text-muted-foreground">Available for Allocation</p>
                <p className="text-xl font-bold text-green-600">
                  {formatCurrency(receiptDetails.unallocatedAmount)}
                </p>
              </div>

              <div className="border-t pt-4">
                <p className="text-sm text-muted-foreground">Current Allocation</p>
                <p className="text-xl font-bold">{formatCurrency(totalAllocated)}</p>
              </div>

              <div>
                <p className="text-sm text-muted-foreground">Remaining Unallocated</p>
                <p
                  className={`text-xl font-bold ${
                    unallocatedBalance > 0 ? 'text-orange-500' : 'text-green-600'
                  }`}
                >
                  {formatCurrency(unallocatedBalance)}
                </p>
              </div>

              {unallocatedBalance > 0 && totalAllocated > 0 && (
                <Alert>
                  <AlertCircle className="h-4 w-4" />
                  <AlertTitle>Partial Allocation</AlertTitle>
                  <AlertDescription>
                    {formatCurrency(unallocatedBalance)} will remain unallocated. You can allocate
                    it later or carry it forward.
                  </AlertDescription>
                </Alert>
              )}

              {totalAllocated > receiptDetails.unallocatedAmount && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertTitle>Over-allocation</AlertTitle>
                  <AlertDescription>
                    Allocation exceeds available amount by{' '}
                    {formatCurrency(totalAllocated - receiptDetails.unallocatedAmount)}
                  </AlertDescription>
                </Alert>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
