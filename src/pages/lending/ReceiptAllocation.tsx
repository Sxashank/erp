import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, Receipt, Check, AlertCircle, Calculator } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import { Checkbox } from '@/components/ui/checkbox';
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
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { formatCurrency, formatDate } from '@/lib/utils';

// Mock data
const receiptDetails = {
  id: '1',
  receipt_number: 'RCP/2025/00243',
  loan_account: 'SMFC/LA/2024/00156',
  entity: 'Metro Logistics',
  receipt_date: '2025-01-14',
  value_date: '2025-01-14',
  total_amount: 500000,
  allocated_amount: 0,
  unallocated_amount: 500000,
  receipt_type: 'REGULAR',
  receipt_mode: 'NEFT',
};

const outstandingDemands = [
  {
    id: '1',
    demand_date: '2025-01-01',
    due_date: '2025-01-05',
    demand_type: 'EMI',
    principal: 200000,
    interest: 75000,
    penalty: 5000,
    other_charges: 0,
    total: 280000,
    paid: 0,
    outstanding: 280000,
    overdue_days: 9,
    selected: false,
    allocated: 0,
  },
  {
    id: '2',
    demand_date: '2024-12-01',
    due_date: '2024-12-05',
    demand_type: 'EMI',
    principal: 195000,
    interest: 80000,
    penalty: 15000,
    other_charges: 2500,
    total: 292500,
    paid: 100000,
    outstanding: 192500,
    overdue_days: 40,
    selected: false,
    allocated: 0,
  },
  {
    id: '3',
    demand_date: '2024-11-01',
    due_date: '2024-11-05',
    demand_type: 'EMI',
    principal: 190000,
    interest: 85000,
    penalty: 25000,
    other_charges: 5000,
    total: 305000,
    paid: 305000,
    outstanding: 0,
    overdue_days: 0,
    selected: false,
    allocated: 0,
  },
];

export default function ReceiptAllocation() {
  const navigate = useNavigate();
  const { id } = useParams();
  const [isLoading, setIsLoading] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);
  const [allocationMethod, setAllocationMethod] = useState('FIFO');
  const [demands, setDemands] = useState(outstandingDemands);
  const [remainingAmount, setRemainingAmount] = useState(receiptDetails.unallocated_amount);

  const handleSelectDemand = (demandId: string, checked: boolean) => {
    setDemands(
      demands.map((d) => (d.id === demandId ? { ...d, selected: checked } : d))
    );
  };

  const handleAllocationChange = (demandId: string, amount: string) => {
    const value = parseFloat(amount) || 0;
    setDemands(
      demands.map((d) => (d.id === demandId ? { ...d, allocated: value } : d))
    );
  };

  const totalAllocated = demands.reduce((sum, d) => sum + d.allocated, 0);
  const unallocatedBalance = receiptDetails.unallocated_amount - totalAllocated;

  const handleAutoAllocate = () => {
    let remaining = receiptDetails.unallocated_amount;
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
        })
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
    setIsLoading(true);
    await new Promise((resolve) => setTimeout(resolve, 1500));
    setIsLoading(false);
    setShowSuccess(true);
  };

  if (showSuccess) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <Check className="h-8 w-8 text-green-600" />
          </div>
          <h2 className="text-2xl font-bold mb-2">Receipt Allocated Successfully</h2>
          <p className="text-muted-foreground mb-2">
            Amount allocated: {formatCurrency(totalAllocated)}
          </p>
          {unallocatedBalance > 0 && (
            <p className="text-orange-600 mb-6">
              Unallocated balance: {formatCurrency(unallocatedBalance)}
            </p>
          )}
          <div className="flex gap-4 justify-center">
            <Button variant="outline" onClick={() => navigate('/lending/receipts')}>
              View All Receipts
            </Button>
            <Button variant="outline" onClick={() => navigate(`/lending/receipts/${id}`)}>
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
        subtitle={`${receiptDetails.receipt_number} - ${receiptDetails.entity}`}
        breadcrumbs={[
          { label: 'Receipts', to: '/lending/receipts' },
          { label: 'Allocate' },
        ]}
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Allocation Table */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Outstanding Demands</CardTitle>
                <CardDescription>Select demands to allocate the receipt</CardDescription>
              </div>
              <div className="flex gap-2">
                <Select value={allocationMethod} onValueChange={setAllocationMethod}>
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
                  <Calculator className="h-4 w-4 mr-2" />
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
                {demands.filter((d) => d.outstanding > 0).map((demand) => (
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
              <div className="text-center py-8 text-muted-foreground">
                No outstanding demands found
              </div>
            )}

            <div className="flex gap-4 justify-end mt-6">
              <Button type="button" variant="outline" onClick={() => navigate(-1)}>
                Cancel
              </Button>
              <Button onClick={handleSubmit} disabled={isLoading || totalAllocated === 0}>
                <Receipt className="h-4 w-4 mr-2" />
                {isLoading ? 'Allocating...' : 'Confirm Allocation'}
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
                <p className="font-mono">{receiptDetails.receipt_number}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Loan Account</p>
                <p className="font-mono">{receiptDetails.loan_account}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Receipt Date</p>
                <p>{formatDate(receiptDetails.receipt_date)}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Receipt Mode</p>
                <Badge variant="outline">{receiptDetails.receipt_mode}</Badge>
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
                <p className="text-2xl font-bold">
                  {formatCurrency(receiptDetails.total_amount)}
                </p>
              </div>

              <div className="border-t pt-4">
                <p className="text-sm text-muted-foreground">Already Allocated</p>
                <p className="font-medium">
                  {formatCurrency(receiptDetails.allocated_amount)}
                </p>
              </div>

              <div>
                <p className="text-sm text-muted-foreground">Available for Allocation</p>
                <p className="text-xl font-bold text-green-600">
                  {formatCurrency(receiptDetails.unallocated_amount)}
                </p>
              </div>

              <div className="border-t pt-4">
                <p className="text-sm text-muted-foreground">Current Allocation</p>
                <p className="text-xl font-bold">
                  {formatCurrency(totalAllocated)}
                </p>
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

              {totalAllocated > receiptDetails.unallocated_amount && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertTitle>Over-allocation</AlertTitle>
                  <AlertDescription>
                    Allocation exceeds available amount by{' '}
                    {formatCurrency(totalAllocated - receiptDetails.unallocated_amount)}
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
