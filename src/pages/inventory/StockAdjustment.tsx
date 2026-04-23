import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm, useFieldArray } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { PageHeader } from '@/components/common/PageHeader';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
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
import { Badge } from '@/components/ui/badge';
import { ArrowLeft, Save, Plus, Trash2, ClipboardCheck, TrendingUp, TrendingDown, Minus } from 'lucide-react';

import { logger } from '@/lib/logger';
const adjustmentLineSchema = z.object({
  itemId: z.string().min(1, 'Item is required'),
  itemCode: z.string(),
  itemName: z.string(),
  systemQty: z.number(),
  physicalQty: z.number().min(0, 'Physical quantity cannot be negative'),
  adjustmentQty: z.number(),
  adjustmentType: z.enum(['INCREASE', 'DECREASE', 'NO_CHANGE']),
  unitCost: z.number().min(0),
  reason: z.string().optional(),
});

const stockAdjustmentSchema = z.object({
  warehouseId: z.string().min(1, 'Warehouse is required'),
  adjustmentDate: z.string().min(1, 'Date is required'),
  adjustmentType: z.enum(['PHYSICAL_COUNT', 'DAMAGE', 'EXPIRED', 'THEFT', 'OTHER']),
  referenceNumber: z.string().optional(),
  conductedBy: z.string().optional(),
  verifiedBy: z.string().optional(),
  remarks: z.string().optional(),
  lines: z.array(adjustmentLineSchema).min(1, 'At least one item is required'),
});

type StockAdjustmentFormData = z.infer<typeof stockAdjustmentSchema>;

const warehouses = [
  { id: '1', name: 'Main Warehouse' },
  { id: '2', name: 'Branch A Store' },
  { id: '3', name: 'Branch B Store' },
];

const items = [
  { id: '1', code: 'ITM-001', name: 'A4 Paper (500 sheets)', systemQty: 150, unitCost: 250 },
  { id: '2', code: 'ITM-002', name: 'Ball Pen Blue', systemQty: 500, unitCost: 10 },
  { id: '3', code: 'ITM-003', name: 'HP LaserJet Toner', systemQty: 25, unitCost: 3500 },
  { id: '4', code: 'ITM-004', name: 'Dell Laptop', systemQty: 10, unitCost: 55000 },
  { id: '5', code: 'ITM-005', name: 'Office Chair', systemQty: 30, unitCost: 8000 },
];

const adjustmentTypes = [
  { value: 'PHYSICAL_COUNT', label: 'Physical Count Adjustment' },
  { value: 'DAMAGE', label: 'Damage Write-off' },
  { value: 'EXPIRED', label: 'Expired Stock' },
  { value: 'THEFT', label: 'Theft / Pilferage' },
  { value: 'OTHER', label: 'Other Adjustment' },
];

export default function StockAdjustment() {
  const navigate = useNavigate();
  const [selectedItem, setSelectedItem] = useState<string>('');

  const form = useForm<StockAdjustmentFormData>({
    resolver: zodResolver(stockAdjustmentSchema),
    defaultValues: {
      warehouseId: '',
      adjustmentDate: new Date().toISOString().split('T')[0],
      adjustmentType: 'PHYSICAL_COUNT',
      referenceNumber: '',
      conductedBy: '',
      verifiedBy: '',
      remarks: '',
      lines: [],
    },
  });

  const { fields, append, remove, update } = useFieldArray({
    control: form.control,
    name: 'lines',
  });

  const addItem = () => {
    if (!selectedItem) return;
    const item = items.find((i) => i.id === selectedItem);
    if (!item) return;

    const existingIndex = fields.findIndex((f) => f.itemId === selectedItem);
    if (existingIndex >= 0) {
      return;
    }

    append({
      itemId: item.id,
      itemCode: item.code,
      itemName: item.name,
      systemQty: item.systemQty,
      physicalQty: item.systemQty,
      adjustmentQty: 0,
      adjustmentType: 'NO_CHANGE',
      unitCost: item.unitCost,
      reason: '',
    });
    setSelectedItem('');
  };

  const updateAdjustment = (index: number, physicalQty: number) => {
    const line = fields[index];
    const adjustmentQty = physicalQty - line.systemQty;
    let adjustmentType: 'INCREASE' | 'DECREASE' | 'NO_CHANGE' = 'NO_CHANGE';

    if (adjustmentQty > 0) adjustmentType = 'INCREASE';
    else if (adjustmentQty < 0) adjustmentType = 'DECREASE';

    form.setValue(`lines.${index}.physicalQty`, physicalQty);
    form.setValue(`lines.${index}.adjustmentQty`, adjustmentQty);
    form.setValue(`lines.${index}.adjustmentType`, adjustmentType);
  };

  const onSubmit = (data: StockAdjustmentFormData) => {
    logger.debug('Stock Adjustment submitted:', data);
    navigate('/inventory/dashboard');
  };

  const summary = fields.reduce(
    (acc, field, index) => {
      const adjustmentQty = form.watch(`lines.${index}.adjustmentQty`) || 0;
      const unitCost = field.unitCost;
      const value = Math.abs(adjustmentQty) * unitCost;

      if (adjustmentQty > 0) {
        acc.increaseCount++;
        acc.increaseValue += value;
      } else if (adjustmentQty < 0) {
        acc.decreaseCount++;
        acc.decreaseValue += value;
      }
      return acc;
    },
    { increaseCount: 0, increaseValue: 0, decreaseCount: 0, decreaseValue: 0 }
  );

  const getAdjustmentIcon = (type: string) => {
    switch (type) {
      case 'INCREASE':
        return <TrendingUp className="h-4 w-4 text-green-500" />;
      case 'DECREASE':
        return <TrendingDown className="h-4 w-4 text-red-500" />;
      default:
        return <Minus className="h-4 w-4 text-muted-foreground" />;
    }
  };

  const getAdjustmentBadge = (type: string, qty: number) => {
    switch (type) {
      case 'INCREASE':
        return <Badge variant="default" className="bg-green-500">+{qty}</Badge>;
      case 'DECREASE':
        return <Badge variant="destructive">{qty}</Badge>;
      default:
        return <Badge variant="secondary">No Change</Badge>;
    }
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      <PageHeader
        title="Stock Adjustment"
        subtitle="Adjust inventory based on physical count or write-offs"
        breadcrumbs={[
          { label: 'Inventory', to: '/inventory' },
          { label: 'Adjustment' },
        ]}
      />

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Adjustment Details</CardTitle>
            </CardHeader>
            <CardContent className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <FormField
                control={form.control}
                name="warehouseId"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Warehouse *</FormLabel>
                    <Select onValueChange={field.onChange} value={field.value}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Select warehouse" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {warehouses.map((wh) => (
                          <SelectItem key={wh.id} value={wh.id}>
                            {wh.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="adjustmentDate"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Adjustment Date *</FormLabel>
                    <FormControl>
                      <Input type="date" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="adjustmentType"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Adjustment Type *</FormLabel>
                    <Select onValueChange={field.onChange} value={field.value}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Select type" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {adjustmentTypes.map((type) => (
                          <SelectItem key={type.value} value={type.value}>
                            {type.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="referenceNumber"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Reference Number</FormLabel>
                    <FormControl>
                      <Input placeholder="Audit/Count reference" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="conductedBy"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Conducted By</FormLabel>
                    <FormControl>
                      <Input placeholder="Name of person" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="verifiedBy"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Verified By</FormLabel>
                    <FormControl>
                      <Input placeholder="Name of verifier" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <div className="md:col-span-2">
                <FormField
                  control={form.control}
                  name="remarks"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Remarks</FormLabel>
                      <FormControl>
                        <Textarea placeholder="Adjustment notes" rows={2} {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Adjustment Items</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-2">
                <Select
                  value={selectedItem}
                  onValueChange={setSelectedItem}
                  disabled={!form.watch('warehouseId')}
                >
                  <SelectTrigger className="max-w-md">
                    <SelectValue placeholder={form.watch('warehouseId') ? "Select item to adjust" : "Select warehouse first"} />
                  </SelectTrigger>
                  <SelectContent>
                    {items.map((item) => (
                      <SelectItem key={item.id} value={item.id}>
                        {item.code} - {item.name} (System: {item.systemQty})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Button type="button" onClick={addItem} disabled={!selectedItem}>
                  <Plus className="h-4 w-4 mr-2" />
                  Add Item
                </Button>
              </div>

              {fields.length > 0 ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Item Code</TableHead>
                      <TableHead>Item Name</TableHead>
                      <TableHead className="text-right">System Qty</TableHead>
                      <TableHead className="w-32">Physical Qty</TableHead>
                      <TableHead className="text-center">Adjustment</TableHead>
                      <TableHead className="text-right">Unit Cost</TableHead>
                      <TableHead className="text-right">Value Impact</TableHead>
                      <TableHead>Reason</TableHead>
                      <TableHead className="w-16"></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {fields.map((field, index) => {
                      const adjustmentQty = form.watch(`lines.${index}.adjustmentQty`) || 0;
                      const adjustmentType = form.watch(`lines.${index}.adjustmentType`) || 'NO_CHANGE';
                      const valueImpact = adjustmentQty * field.unitCost;

                      return (
                        <TableRow key={field.id}>
                          <TableCell className="font-medium">{field.itemCode}</TableCell>
                          <TableCell>{field.itemName}</TableCell>
                          <TableCell className="text-right">{field.systemQty}</TableCell>
                          <TableCell>
                            <Input
                              type="number"
                              min="0"
                              className="w-32"
                              value={form.watch(`lines.${index}.physicalQty`)}
                              onChange={(e) => updateAdjustment(index, parseInt(e.target.value) || 0)}
                            />
                          </TableCell>
                          <TableCell className="text-center">
                            <div className="flex items-center justify-center gap-2">
                              {getAdjustmentIcon(adjustmentType)}
                              {getAdjustmentBadge(adjustmentType, adjustmentQty)}
                            </div>
                          </TableCell>
                          <TableCell className="text-right">
                            {field.unitCost.toLocaleString('en-IN', {
                              style: 'currency',
                              currency: 'INR',
                              maximumFractionDigits: 0,
                            })}
                          </TableCell>
                          <TableCell className={`text-right font-medium ${valueImpact < 0 ? 'text-red-500' : valueImpact > 0 ? 'text-green-500' : ''}`}>
                            {valueImpact !== 0 && (valueImpact > 0 ? '+' : '')}
                            {valueImpact.toLocaleString('en-IN', {
                              style: 'currency',
                              currency: 'INR',
                              maximumFractionDigits: 0,
                            })}
                          </TableCell>
                          <TableCell>
                            <FormField
                              control={form.control}
                              name={`lines.${index}.reason`}
                              render={({ field }) => (
                                <Input placeholder="Reason" className="w-32" {...field} />
                              )}
                            />
                          </TableCell>
                          <TableCell>
                            <Button
                              type="button"
                              variant="ghost"
                              size="icon"
                              onClick={() => remove(index)}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  No items added. Select a warehouse and add items to adjust.
                </div>
              )}

              {fields.length > 0 && (
                <div className="flex justify-end gap-4">
                  <div className="bg-green-50 p-4 rounded-lg border border-green-200">
                    <div className="text-sm text-green-700">Increase</div>
                    <div className="text-lg font-bold text-green-700">
                      {summary.increaseCount} items
                    </div>
                    <div className="text-sm text-green-600">
                      +{summary.increaseValue.toLocaleString('en-IN', {
                        style: 'currency',
                        currency: 'INR',
                        maximumFractionDigits: 0,
                      })}
                    </div>
                  </div>
                  <div className="bg-red-50 p-4 rounded-lg border border-red-200">
                    <div className="text-sm text-red-700">Decrease</div>
                    <div className="text-lg font-bold text-red-700">
                      {summary.decreaseCount} items
                    </div>
                    <div className="text-sm text-red-600">
                      -{summary.decreaseValue.toLocaleString('en-IN', {
                        style: 'currency',
                        currency: 'INR',
                        maximumFractionDigits: 0,
                      })}
                    </div>
                  </div>
                  <div className="bg-muted p-4 rounded-lg">
                    <div className="text-sm text-muted-foreground">Net Impact</div>
                    <div className={`text-lg font-bold ${summary.increaseValue - summary.decreaseValue >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {(summary.increaseValue - summary.decreaseValue).toLocaleString('en-IN', {
                        style: 'currency',
                        currency: 'INR',
                        maximumFractionDigits: 0,
                      })}
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          <div className="flex justify-end gap-4">
            <Button type="button" variant="outline" onClick={() => navigate(-1)}>
              Cancel
            </Button>
            <Button type="submit" disabled={fields.length === 0}>
              <Save className="h-4 w-4 mr-2" />
              Submit Adjustment
            </Button>
          </div>
        </form>
      </Form>
    </div>
  );
}
