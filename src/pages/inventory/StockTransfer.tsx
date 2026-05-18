import { zodResolver } from '@hookform/resolvers/zod';
import { ArrowLeft, Save, Plus, Trash2, ArrowRightLeft, MoveRight } from 'lucide-react';
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
const transferLineSchema = z.object({
  itemId: z.string().min(1, 'Item is required'),
  itemCode: z.string(),
  itemName: z.string(),
  availableQty: z.number(),
  quantity: z.number().min(0.01, 'Quantity must be greater than 0'),
  batchNumber: z.string().optional(),
  remarks: z.string().optional(),
});

const stockTransferSchema = z
  .object({
    fromWarehouseId: z.string().min(1, 'Source warehouse is required'),
    toWarehouseId: z.string().min(1, 'Destination warehouse is required'),
    transactionDate: z.string().min(1, 'Date is required'),
    transferType: z.enum(['DIRECT', 'TRANSIT']),
    requestedBy: z.string().optional(),
    approvedBy: z.string().optional(),
    remarks: z.string().optional(),
    lines: z.array(transferLineSchema).min(1, 'At least one item is required'),
  })
  .refine((data) => data.fromWarehouseId !== data.toWarehouseId, {
    message: 'Source and destination warehouses must be different',
    path: ['toWarehouseId'],
  });

type StockTransferFormData = z.infer<typeof stockTransferSchema>;

const warehouses = [
  { id: '1', name: 'Main Warehouse', code: 'WH-001' },
  { id: '2', name: 'Branch A Store', code: 'WH-002' },
  { id: '3', name: 'Branch B Store', code: 'WH-003' },
  { id: '4', name: 'Transit Warehouse', code: 'WH-004' },
];

const items = [
  { id: '1', code: 'ITM-001', name: 'A4 Paper (500 sheets)', uom: 'Pack', availableQty: 150 },
  { id: '2', code: 'ITM-002', name: 'Ball Pen Blue', uom: 'Pcs', availableQty: 500 },
  { id: '3', code: 'ITM-003', name: 'HP LaserJet Toner', uom: 'Pcs', availableQty: 25 },
  { id: '4', code: 'ITM-004', name: 'Dell Laptop', uom: 'Pcs', availableQty: 10 },
  { id: '5', code: 'ITM-005', name: 'Office Chair', uom: 'Pcs', availableQty: 30 },
];

const transferTypes = [
  {
    value: 'DIRECT',
    label: 'Direct Transfer',
    description: 'Stock moves directly between warehouses',
  },
  { value: 'TRANSIT', label: 'Via Transit', description: 'Stock goes through transit warehouse' },
];

export default function StockTransfer() {
  const navigate = useNavigate();
  const [selectedItem, setSelectedItem] = useState<string>('');

  const form = useForm<StockTransferFormData>({
    resolver: zodResolver(stockTransferSchema),
    defaultValues: {
      fromWarehouseId: '',
      toWarehouseId: '',
      transactionDate: new Date().toISOString().split('T')[0],
      transferType: 'DIRECT',
      requestedBy: '',
      approvedBy: '',
      remarks: '',
      lines: [],
    },
  });

  const { fields, append, remove } = useFieldArray({
    control: form.control,
    name: 'lines',
  });

  const fromWarehouseId = form.watch('fromWarehouseId');
  const toWarehouseId = form.watch('toWarehouseId');

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
      remarks: '',
    });
    setSelectedItem('');
  };

  const onSubmit = (data: StockTransferFormData) => {
    // Validate quantities don't exceed available
    const invalidLines = data.lines.filter((line) => line.quantity > line.availableQty);
    if (invalidLines.length > 0) {
      alert('Some items have quantity exceeding available stock');
      return;
    }

    logger.debug('Stock Transfer submitted:', data);
    navigate('/admin/inventory/dashboard');
  };

  const totalItems = fields.reduce((sum, _, index) => {
    return sum + (form.watch(`lines.${index}.quantity`) || 0);
  }, 0);

  const fromWarehouse = warehouses.find((w) => w.id === fromWarehouseId);
  const toWarehouse = warehouses.find((w) => w.id === toWarehouseId);

  return (
    <div className="container mx-auto space-y-6 py-6">
      <PageHeader
        title="Stock Transfer"
        subtitle="Transfer stock between warehouses"
        breadcrumbs={[{ label: 'Inventory', to: '/admin/inventory' }, { label: 'Transfer' }]}
      />

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Transfer Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Transfer Visual */}
              <div className="flex items-center justify-center gap-4 rounded-lg bg-muted p-4">
                <div className="text-center">
                  <div className="mb-1 text-sm text-muted-foreground">From</div>
                  <div className="text-lg font-semibold">
                    {fromWarehouse ? fromWarehouse.name : 'Select Source'}
                  </div>
                  {fromWarehouse && <Badge variant="outline">{fromWarehouse.code}</Badge>}
                </div>
                <MoveRight className="h-8 w-8 text-muted-foreground" />
                <div className="text-center">
                  <div className="mb-1 text-sm text-muted-foreground">To</div>
                  <div className="text-lg font-semibold">
                    {toWarehouse ? toWarehouse.name : 'Select Destination'}
                  </div>
                  {toWarehouse && <Badge variant="outline">{toWarehouse.code}</Badge>}
                </div>
              </div>

              <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
                <FormField
                  control={form.control}
                  name="fromWarehouseId"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>From Warehouse *</FormLabel>
                      <Select onValueChange={field.onChange} value={field.value}>
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder="Select source" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          {warehouses.map((wh) => (
                            <SelectItem
                              key={wh.id}
                              value={wh.id}
                              disabled={wh.id === toWarehouseId}
                            >
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
                  name="toWarehouseId"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>To Warehouse *</FormLabel>
                      <Select onValueChange={field.onChange} value={field.value}>
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder="Select destination" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          {warehouses.map((wh) => (
                            <SelectItem
                              key={wh.id}
                              value={wh.id}
                              disabled={wh.id === fromWarehouseId}
                            >
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
                      <FormLabel>Transfer Date *</FormLabel>
                      <FormControl>
                        <Input type="date" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="transferType"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Transfer Type *</FormLabel>
                      <Select onValueChange={field.onChange} value={field.value}>
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder="Select type" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          {transferTypes.map((type) => (
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
                  name="requestedBy"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Requested By</FormLabel>
                      <FormControl>
                        <Input placeholder="Name of requester" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="approvedBy"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Approved By</FormLabel>
                      <FormControl>
                        <Input placeholder="Name of approver" {...field} />
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
                          <Textarea placeholder="Transfer notes" rows={2} {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Transfer Items</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-2">
                <Select
                  value={selectedItem}
                  onValueChange={setSelectedItem}
                  disabled={!fromWarehouseId}
                >
                  <SelectTrigger className="max-w-md">
                    <SelectValue
                      placeholder={
                        fromWarehouseId
                          ? 'Select item to transfer'
                          : 'Select source warehouse first'
                      }
                    />
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
                      <TableHead className="w-32">Transfer Qty</TableHead>
                      <TableHead>Batch #</TableHead>
                      <TableHead>Remarks</TableHead>
                      <TableHead className="w-16"></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {fields.map((field, index) => {
                      const quantity = form.watch(`lines.${index}.quantity`) || 0;
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
                                <div>
                                  <Input
                                    type="number"
                                    min="0.01"
                                    max={field.availableQty}
                                    step="0.01"
                                    className={`w-32 ${isOverQty ? 'border-red-500' : ''}`}
                                    {...inputField}
                                    onChange={(e) =>
                                      inputField.onChange(parseFloat(e.target.value) || 0)
                                    }
                                  />
                                  {isOverQty && (
                                    <span className="text-xs text-red-500">Exceeds available</span>
                                  )}
                                </div>
                              )}
                            />
                          </TableCell>
                          <TableCell>
                            <FormField
                              control={form.control}
                              name={`lines.${index}.batchNumber`}
                              render={({ field }) => (
                                <Input placeholder="Batch #" className="w-28" {...field} />
                              )}
                            />
                          </TableCell>
                          <TableCell>
                            <FormField
                              control={form.control}
                              name={`lines.${index}.remarks`}
                              render={({ field }) => (
                                <Input placeholder="Notes" className="w-32" {...field} />
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
                <div className="py-8 text-center text-muted-foreground">
                  No items added. Select a source warehouse and add items to transfer.
                </div>
              )}

              {fields.length > 0 && (
                <div className="flex justify-end">
                  <div className="rounded-lg bg-muted p-4">
                    <div className="text-sm text-muted-foreground">Total Items to Transfer</div>
                    <div className="text-2xl font-bold">{totalItems} units</div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          <div className="flex justify-end gap-4">
            <Button type="button" variant="outline" onClick={() => navigate(-1)}>
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={fields.length === 0 || !fromWarehouseId || !toWarehouseId}
            >
              <Save className="mr-2 h-4 w-4" />
              Create Transfer
            </Button>
          </div>
        </form>
      </Form>
    </div>
  );
}
