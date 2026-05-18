import { zodResolver } from '@hookform/resolvers/zod';
import { ArrowLeft, Save, Plus, Trash2, PackageMinus } from 'lucide-react';
import { useState } from 'react';
import { useForm, useFieldArray } from 'react-hook-form';
import { useNavigate } from 'react-router-dom';
import { z } from 'zod';

import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
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
import { Textarea } from '@/components/ui/textarea';
import { logger } from '@/lib/logger';

const NONE_OPTION_VALUE = '__none__';
const stockOutLineSchema = z.object({
  itemId: z.string().min(1, 'Item is required'),
  itemCode: z.string(),
  itemName: z.string(),
  availableQty: z.number(),
  quantity: z.number().min(0.01, 'Quantity must be greater than 0'),
  batchNumber: z.string().optional(),
  serialNumbers: z.string().optional(),
  remarks: z.string().optional(),
});

const stockOutSchema = z.object({
  warehouseId: z.string().min(1, 'Warehouse is required'),
  transactionDate: z.string().min(1, 'Date is required'),
  referenceType: z.enum(['CONSUMPTION', 'SALE', 'TRANSFER', 'DAMAGE', 'EXPIRED', 'OTHER']),
  referenceNumber: z.string().optional(),
  issuedTo: z.string().optional(),
  departmentId: z.string().optional(),
  remarks: z.string().optional(),
  lines: z.array(stockOutLineSchema).min(1, 'At least one item is required'),
});

type StockOutFormData = z.infer<typeof stockOutSchema>;

const warehouses = [
  { id: '1', name: 'Main Warehouse' },
  { id: '2', name: 'Branch A Store' },
  { id: '3', name: 'Branch B Store' },
];

const departments = [
  { id: '1', name: 'Administration' },
  { id: '2', name: 'Finance' },
  { id: '3', name: 'IT' },
  { id: '4', name: 'Operations' },
  { id: '5', name: 'Sales' },
];

const items = [
  {
    id: '1',
    code: 'ITM-001',
    name: 'A4 Paper (500 sheets)',
    uom: 'Pack',
    availableQty: 150,
    avgCost: 250,
  },
  { id: '2', code: 'ITM-002', name: 'Ball Pen Blue', uom: 'Pcs', availableQty: 500, avgCost: 10 },
  {
    id: '3',
    code: 'ITM-003',
    name: 'HP LaserJet Toner',
    uom: 'Pcs',
    availableQty: 25,
    avgCost: 3500,
  },
  { id: '4', code: 'ITM-004', name: 'Dell Laptop', uom: 'Pcs', availableQty: 10, avgCost: 55000 },
  { id: '5', code: 'ITM-005', name: 'Office Chair', uom: 'Pcs', availableQty: 30, avgCost: 8000 },
];

const referenceTypes = [
  { value: 'CONSUMPTION', label: 'Internal Consumption' },
  { value: 'SALE', label: 'Sales Issue' },
  { value: 'TRANSFER', label: 'Transfer Out' },
  { value: 'DAMAGE', label: 'Damaged Goods' },
  { value: 'EXPIRED', label: 'Expired Stock' },
  { value: 'OTHER', label: 'Other' },
];

export default function StockOut() {
  const navigate = useNavigate();
  const [selectedItem, setSelectedItem] = useState<string>('');

  const form = useForm<StockOutFormData>({
    resolver: zodResolver(stockOutSchema),
    defaultValues: {
      warehouseId: '',
      transactionDate: new Date().toISOString().split('T')[0],
      referenceType: 'CONSUMPTION',
      referenceNumber: '',
      issuedTo: '',
      departmentId: '',
      remarks: '',
      lines: [],
    },
  });

  const { fields, append, remove } = useFieldArray({
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
      availableQty: item.availableQty,
      quantity: 1,
      batchNumber: '',
      serialNumbers: '',
      remarks: '',
    });
    setSelectedItem('');
  };

  const onSubmit = (data: StockOutFormData) => {
    // Validate quantities don't exceed available
    const invalidLines = data.lines.filter((line) => line.quantity > line.availableQty);
    if (invalidLines.length > 0) {
      alert('Some items have quantity exceeding available stock');
      return;
    }

    logger.debug('Stock Out submitted:', data);
    navigate('/admin/inventory/dashboard');
  };

  const totalValue = fields.reduce((sum, field, index) => {
    const quantity = form.watch(`lines.${index}.quantity`) || 0;
    const item = items.find((i) => i.id === field.itemId);
    return sum + quantity * (item?.avgCost || 0);
  }, 0);

  return (
    <div className="container mx-auto space-y-6 py-6">
      <PageHeader
        title="Stock Out"
        subtitle="Record outgoing stock / consumption"
        breadcrumbs={[{ label: 'Inventory', to: '/admin/inventory' }, { label: 'Stock Out' }]}
      />

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Transaction Details</CardTitle>
            </CardHeader>
            <CardContent className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
              <FormField
                control={form.control}
                name="warehouseId"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>From Warehouse *</FormLabel>
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
                name="transactionDate"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Date *</FormLabel>
                    <FormControl>
                      <Input type="date" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="referenceType"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Issue Type *</FormLabel>
                    <Select onValueChange={field.onChange} value={field.value}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Select type" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {referenceTypes.map((type) => (
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
                      <Input placeholder="Issue/Request number" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="departmentId"
                render={({ field }) => (
                    <FormItem>
                      <FormLabel>Department</FormLabel>
                    <Select
                      onValueChange={(value) =>
                        field.onChange(value === NONE_OPTION_VALUE ? '' : value)
                      }
                      value={field.value || NONE_OPTION_VALUE}
                    >
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Select department" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value={NONE_OPTION_VALUE}>None</SelectItem>
                        {departments.map((dept) => (
                          <SelectItem key={dept.id} value={dept.id}>
                            {dept.name}
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
                name="issuedTo"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Issued To</FormLabel>
                    <FormControl>
                      <Input placeholder="Employee name / Customer" {...field} />
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
                        <Textarea placeholder="Enter any remarks" rows={2} {...field} />
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
              <CardTitle>Items</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-2">
                <Select value={selectedItem} onValueChange={setSelectedItem}>
                  <SelectTrigger className="max-w-md">
                    <SelectValue placeholder="Select item to issue" />
                  </SelectTrigger>
                  <SelectContent>
                    {items.map((item) => (
                      <SelectItem key={item.id} value={item.id}>
                        {item.code} - {item.name} (Avl: {item.availableQty})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Button type="button" onClick={addItem} disabled={!selectedItem}>
                  <Plus className="mr-2 h-4 w-4" />
                  Add Item
                </Button>
              </div>

              {fields.length > 0 ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Item Code</TableHead>
                      <TableHead>Item Name</TableHead>
                      <TableHead className="text-right">Available</TableHead>
                      <TableHead className="w-24">Issue Qty</TableHead>
                      <TableHead className="w-32 text-right">Unit Cost</TableHead>
                      <TableHead className="w-32 text-right">Total Value</TableHead>
                      <TableHead className="w-16"></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {fields.map((field, index) => {
                      const quantity = form.watch(`lines.${index}.quantity`) || 0;
                      const item = items.find((i) => i.id === field.itemId);
                      const lineTotal = quantity * (item?.avgCost || 0);
                      const isOverQty = quantity > field.availableQty;

                      return (
                        <TableRow key={field.id}>
                          <TableCell className="font-medium">{field.itemCode}</TableCell>
                          <TableCell>{field.itemName}</TableCell>
                          <TableCell className="text-right">
                            <Badge variant={field.availableQty > 10 ? 'default' : 'destructive'}>
                              {field.availableQty}
                            </Badge>
                          </TableCell>
                          <TableCell>
                            <FormField
                              control={form.control}
                              name={`lines.${index}.quantity`}
                              render={({ field: inputField }) => (
                                <Input
                                  type="number"
                                  min="0.01"
                                  max={field.availableQty}
                                  step="0.01"
                                  className={`w-24 ${isOverQty ? 'border-red-500' : ''}`}
                                  {...inputField}
                                  onChange={(e) =>
                                    inputField.onChange(parseFloat(e.target.value) || 0)
                                  }
                                />
                              )}
                            />
                            {isOverQty && (
                              <span className="text-xs text-red-500">Exceeds available</span>
                            )}
                          </TableCell>
                          <TableCell className="text-right">
                            {(item?.avgCost || 0).toLocaleString('en-IN', {
                              style: 'currency',
                              currency: 'INR',
                              maximumFractionDigits: 0,
                            })}
                          </TableCell>
                          <TableCell className="text-right font-medium">
                            {lineTotal.toLocaleString('en-IN', {
                              style: 'currency',
                              currency: 'INR',
                              maximumFractionDigits: 0,
                            })}
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
                <div className="py-8 text-center text-muted-foreground">
                  No items added. Select an item and click "Add Item" to begin.
                </div>
              )}

              {fields.length > 0 && (
                <div className="flex justify-end">
                  <div className="rounded-lg bg-muted p-4">
                    <div className="text-sm text-muted-foreground">Total Issue Value</div>
                    <div className="text-2xl font-bold">
                      {totalValue.toLocaleString('en-IN', {
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
              <Save className="mr-2 h-4 w-4" />
              Save Stock Out
            </Button>
          </div>
        </form>
      </Form>
    </div>
  );
}
