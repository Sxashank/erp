import { zodResolver } from '@hookform/resolvers/zod';
import { ArrowLeft, Save, Plus, Trash2, PackagePlus } from 'lucide-react';
import { useState } from 'react';
import { useForm, useFieldArray } from 'react-hook-form';
import { useNavigate } from 'react-router-dom';
import { z } from 'zod';

import { PageHeader } from '@/components/common/PageHeader';
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
const stockInLineSchema = z.object({
  itemId: z.string().min(1, 'Item is required'),
  itemCode: z.string(),
  itemName: z.string(),
  quantity: z.number().min(0.01, 'Quantity must be greater than 0'),
  unitCost: z.number().min(0, 'Unit cost must be positive'),
  batchNumber: z.string().optional(),
  serialNumbers: z.string().optional(),
  expiryDate: z.string().optional(),
  remarks: z.string().optional(),
});

const stockInSchema = z.object({
  warehouseId: z.string().min(1, 'Warehouse is required'),
  transactionDate: z.string().min(1, 'Date is required'),
  referenceType: z.enum(['PURCHASE', 'RETURN', 'TRANSFER', 'OPENING', 'OTHER']),
  referenceNumber: z.string().optional(),
  remarks: z.string().optional(),
  lines: z.array(stockInLineSchema).min(1, 'At least one item is required'),
});

type StockInFormData = z.infer<typeof stockInSchema>;

const warehouses = [
  { id: '1', name: 'Main Warehouse' },
  { id: '2', name: 'Branch A Store' },
  { id: '3', name: 'Branch B Store' },
];

const items = [
  {
    id: '1',
    code: 'ITM-001',
    name: 'A4 Paper (500 sheets)',
    uom: 'Pack',
    requiresBatch: true,
    requiresSerial: false,
  },
  {
    id: '2',
    code: 'ITM-002',
    name: 'Ball Pen Blue',
    uom: 'Pcs',
    requiresBatch: false,
    requiresSerial: false,
  },
  {
    id: '3',
    code: 'ITM-003',
    name: 'HP LaserJet Toner',
    uom: 'Pcs',
    requiresBatch: true,
    requiresSerial: false,
  },
  {
    id: '4',
    code: 'ITM-004',
    name: 'Dell Laptop',
    uom: 'Pcs',
    requiresBatch: false,
    requiresSerial: true,
  },
  {
    id: '5',
    code: 'ITM-005',
    name: 'Office Chair',
    uom: 'Pcs',
    requiresBatch: false,
    requiresSerial: true,
  },
];

const referenceTypes = [
  { value: 'PURCHASE', label: 'Purchase Receipt' },
  { value: 'RETURN', label: 'Sales Return' },
  { value: 'TRANSFER', label: 'Transfer In' },
  { value: 'OPENING', label: 'Opening Stock' },
  { value: 'OTHER', label: 'Other' },
];

export default function StockIn() {
  const navigate = useNavigate();
  const [selectedItem, setSelectedItem] = useState<string>('');

  const form = useForm<StockInFormData>({
    resolver: zodResolver(stockInSchema),
    defaultValues: {
      warehouseId: '',
      transactionDate: new Date().toISOString().split('T')[0],
      referenceType: 'PURCHASE',
      referenceNumber: '',
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

    // Check if item already exists
    const existingIndex = fields.findIndex((f) => f.itemId === selectedItem);
    if (existingIndex >= 0) {
      // Could update quantity instead
      return;
    }

    append({
      itemId: item.id,
      itemCode: item.code,
      itemName: item.name,
      quantity: 1,
      unitCost: 0,
      batchNumber: '',
      serialNumbers: '',
      expiryDate: '',
      remarks: '',
    });
    setSelectedItem('');
  };

  const onSubmit = (data: StockInFormData) => {
    logger.debug('Stock In submitted:', data);
    navigate('/admin/inventory/dashboard');
  };

  const totalValue = fields.reduce((sum, _, index) => {
    const quantity = form.watch(`lines.${index}.quantity`) || 0;
    const unitCost = form.watch(`lines.${index}.unitCost`) || 0;
    return sum + quantity * unitCost;
  }, 0);

  return (
    <div className="container mx-auto space-y-6 py-6">
      <PageHeader
        title="Stock In"
        subtitle="Record incoming stock"
        breadcrumbs={[{ label: 'Inventory', to: '/admin/inventory' }, { label: 'Stock In' }]}
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
                    <FormLabel>Reference Type *</FormLabel>
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
                      <Input placeholder="PO/Invoice number" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <div className="md:col-span-2 lg:col-span-4">
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
                    <SelectValue placeholder="Select item to add" />
                  </SelectTrigger>
                  <SelectContent>
                    {items.map((item) => (
                      <SelectItem key={item.id} value={item.id}>
                        {item.code} - {item.name}
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
                      <TableHead className="w-24">Quantity</TableHead>
                      <TableHead className="w-32">Unit Cost</TableHead>
                      <TableHead className="w-32">Batch #</TableHead>
                      <TableHead className="w-32">Expiry Date</TableHead>
                      <TableHead className="w-32 text-right">Total</TableHead>
                      <TableHead className="w-16"></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {fields.map((field, index) => {
                      const quantity = form.watch(`lines.${index}.quantity`) || 0;
                      const unitCost = form.watch(`lines.${index}.unitCost`) || 0;
                      const lineTotal = quantity * unitCost;
                      const item = items.find((i) => i.id === field.itemId);

                      return (
                        <TableRow key={field.id}>
                          <TableCell className="font-medium">{field.itemCode}</TableCell>
                          <TableCell>{field.itemName}</TableCell>
                          <TableCell>
                            <FormField
                              control={form.control}
                              name={`lines.${index}.quantity`}
                              render={({ field }) => (
                                <Input
                                  type="number"
                                  min="0.01"
                                  step="0.01"
                                  className="w-24"
                                  {...field}
                                  onChange={(e) => field.onChange(parseFloat(e.target.value) || 0)}
                                />
                              )}
                            />
                          </TableCell>
                          <TableCell>
                            <FormField
                              control={form.control}
                              name={`lines.${index}.unitCost`}
                              render={({ field }) => (
                                <Input
                                  type="number"
                                  min="0"
                                  step="0.01"
                                  className="w-32"
                                  {...field}
                                  onChange={(e) => field.onChange(parseFloat(e.target.value) || 0)}
                                />
                              )}
                            />
                          </TableCell>
                          <TableCell>
                            {item?.requiresBatch && (
                              <FormField
                                control={form.control}
                                name={`lines.${index}.batchNumber`}
                                render={({ field }) => (
                                  <Input placeholder="Batch #" className="w-32" {...field} />
                                )}
                              />
                            )}
                          </TableCell>
                          <TableCell>
                            {item?.requiresBatch && (
                              <FormField
                                control={form.control}
                                name={`lines.${index}.expiryDate`}
                                render={({ field }) => (
                                  <Input type="date" className="w-32" {...field} />
                                )}
                              />
                            )}
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
                    <div className="text-sm text-muted-foreground">Total Value</div>
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
              Save Stock In
            </Button>
          </div>
        </form>
      </Form>
    </div>
  );
}
