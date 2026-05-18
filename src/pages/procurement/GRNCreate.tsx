import { zodResolver } from '@hookform/resolvers/zod';
import {
  ArrowLeft,
  Package,
  Save,
  CheckCircle,
  AlertTriangle,
} from 'lucide-react';
import { useState, useEffect } from 'react';
import { useForm, useFieldArray } from 'react-hook-form';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { z } from 'zod';

import { PageHeader } from '@/components/common/PageHeader';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
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


const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(value);
};

const grnItemSchema = z.object({
  itemId: z.string(),
  description: z.string(),
  orderedQty: z.number(),
  previouslyReceived: z.number(),
  pendingQty: z.number(),
  receivedQty: z.number().min(0),
  acceptedQty: z.number().min(0),
  rejectedQty: z.number().min(0),
  unitPrice: z.number(),
  remarks: z.string().optional(),
});

const grnSchema = z.object({
  poId: z.string().min(1, 'PO is required'),
  invoiceNumber: z.string().min(1, 'Invoice number is required'),
  invoiceDate: z.string().min(1, 'Invoice date is required'),
  invoiceAmount: z.number().min(0),
  receivedDate: z.string().min(1, 'Received date is required'),
  transportMode: z.string().optional(),
  vehicleNumber: z.string().optional(),
  challanNumber: z.string().optional(),
  items: z.array(grnItemSchema),
  remarks: z.string().optional(),
});

type GRNFormData = z.infer<typeof grnSchema>;

// Mock pending POs
const pendingPOs = [
  {
    id: 'PO2025010001',
    vendor: 'ABC Suppliers Ltd',
    vendorCode: 'V001',
    totalAmount: 145000,
    deliveryDate: '2025-01-25',
    items: [
      { id: '1', description: 'Ergonomic Office Chair', orderedQty: 50, previouslyReceived: 30, pendingQty: 20, unitPrice: 1500 },
      { id: '2', description: 'Standing Desk', orderedQty: 25, previouslyReceived: 20, pendingQty: 5, unitPrice: 3000 },
    ],
  },
  {
    id: 'PO2025010003',
    vendor: 'Furniture Hub',
    vendorCode: 'V005',
    totalAmount: 485000,
    deliveryDate: '2025-02-10',
    items: [
      { id: '1', description: 'Executive Desk', orderedQty: 10, previouslyReceived: 0, pendingQty: 10, unitPrice: 15000 },
      { id: '2', description: 'Conference Chair', orderedQty: 40, previouslyReceived: 0, pendingQty: 40, unitPrice: 5000 },
      { id: '3', description: 'Bookshelf', orderedQty: 15, previouslyReceived: 0, pendingQty: 15, unitPrice: 8000 },
    ],
  },
];

export default function GRNCreate() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const poRef = searchParams.get('po');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [selectedPO, setSelectedPO] = useState<typeof pendingPOs[0] | null>(null);

  const form = useForm<GRNFormData>({
    resolver: zodResolver(grnSchema),
    defaultValues: {
      poId: poRef || '',
      invoiceNumber: '',
      invoiceDate: '',
      invoiceAmount: 0,
      receivedDate: new Date().toISOString().split('T')[0],
      transportMode: '',
      vehicleNumber: '',
      challanNumber: '',
      items: [],
      remarks: '',
    },
  });

  const { fields, replace } = useFieldArray({
    control: form.control,
    name: 'items',
  });

  const watchPoId = form.watch('poId');

  useEffect(() => {
    if (watchPoId) {
      const po = pendingPOs.find(p => p.id === watchPoId);
      setSelectedPO(po || null);
      if (po) {
        const items = po.items.map(item => ({
          itemId: item.id,
          description: item.description,
          orderedQty: item.orderedQty,
          previouslyReceived: item.previouslyReceived,
          pendingQty: item.pendingQty,
          receivedQty: 0,
          acceptedQty: 0,
          rejectedQty: 0,
          unitPrice: item.unitPrice,
          remarks: '',
        }));
        replace(items);
      }
    } else {
      setSelectedPO(null);
      replace([]);
    }
  }, [watchPoId, replace]);

  const watchItems = form.watch('items');

  const handleReceivedQtyChange = (index: number, qty: number) => {
    const pendingQty = watchItems[index].pendingQty;
    const validQty = Math.min(qty, pendingQty);
    form.setValue(`items.${index}.receivedQty`, validQty);
    form.setValue(`items.${index}.acceptedQty`, validQty);
    form.setValue(`items.${index}.rejectedQty`, 0);
  };

  const handleAcceptedQtyChange = (index: number, qty: number) => {
    const receivedQty = watchItems[index].receivedQty;
    const validQty = Math.min(qty, receivedQty);
    form.setValue(`items.${index}.acceptedQty`, validQty);
    form.setValue(`items.${index}.rejectedQty`, receivedQty - validQty);
  };

  const calculateTotalReceivedValue = () => {
    return watchItems.reduce((sum, item) => sum + (item.acceptedQty * item.unitPrice), 0);
  };

  const onSubmit = async (data: GRNFormData) => {
    setIsSubmitting(true);
    await new Promise(resolve => setTimeout(resolve, 1500));
    setIsSubmitting(false);
    navigate('/admin/procurement/grn');
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      <PageHeader
        title="Create Goods Receipt Note"
        subtitle="Record receipt of goods against a purchase order"
        breadcrumbs={[
          { label: 'GRN', to: '/admin/procurement/grn' },
          { label: 'New' },
        ]}
      />

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
          {/* PO Selection */}
          <Card>
            <CardHeader>
              <CardTitle>Purchase Order Selection</CardTitle>
            </CardHeader>
            <CardContent>
              <FormField
                control={form.control}
                name="poId"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Select Purchase Order</FormLabel>
                    <Select onValueChange={field.onChange} value={field.value}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Select a pending PO" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {pendingPOs.map(po => (
                          <SelectItem key={po.id} value={po.id}>
                            {po.id} - {po.vendor} ({formatCurrency(po.totalAmount)})
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />

              {selectedPO && (
                <div className="mt-4 p-4 bg-muted rounded-lg">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <span className="text-muted-foreground">Vendor:</span>
                      <p className="font-medium">{selectedPO.vendor}</p>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Vendor Code:</span>
                      <p className="font-medium">{selectedPO.vendorCode}</p>
                    </div>
                    <div>
                      <span className="text-muted-foreground">PO Amount:</span>
                      <p className="font-medium">{formatCurrency(selectedPO.totalAmount)}</p>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Expected Delivery:</span>
                      <p className="font-medium">{selectedPO.deliveryDate}</p>
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {selectedPO && (
            <>
              {/* Invoice & Receipt Details */}
              <Card>
                <CardHeader>
                  <CardTitle>Invoice & Receipt Details</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <FormField
                      control={form.control}
                      name="invoiceNumber"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Vendor Invoice Number</FormLabel>
                          <FormControl>
                            <Input placeholder="Enter invoice number" {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="invoiceDate"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Invoice Date</FormLabel>
                          <FormControl>
                            <Input type="date" {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="invoiceAmount"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Invoice Amount</FormLabel>
                          <FormControl>
                            <Input
                              type="number"
                              {...field}
                              onChange={(e) => field.onChange(Number(e.target.value))}
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="receivedDate"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Received Date</FormLabel>
                          <FormControl>
                            <Input type="date" {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="transportMode"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Transport Mode</FormLabel>
                          <Select onValueChange={field.onChange} value={field.value}>
                            <FormControl>
                              <SelectTrigger>
                                <SelectValue placeholder="Select transport mode" />
                              </SelectTrigger>
                            </FormControl>
                            <SelectContent>
                              <SelectItem value="ROAD">Road</SelectItem>
                              <SelectItem value="RAIL">Rail</SelectItem>
                              <SelectItem value="AIR">Air</SelectItem>
                              <SelectItem value="COURIER">Courier</SelectItem>
                            </SelectContent>
                          </Select>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="vehicleNumber"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Vehicle Number</FormLabel>
                          <FormControl>
                            <Input placeholder="Enter vehicle number" {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={form.control}
                      name="challanNumber"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Challan / LR Number</FormLabel>
                          <FormControl>
                            <Input placeholder="Enter challan number" {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>
                </CardContent>
              </Card>

              {/* Line Items */}
              <Card>
                <CardHeader>
                  <CardTitle>Items Received</CardTitle>
                  <CardDescription>Enter quantities received for each item</CardDescription>
                </CardHeader>
                <CardContent>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Description</TableHead>
                        <TableHead className="text-center">Ordered</TableHead>
                        <TableHead className="text-center">Previously Received</TableHead>
                        <TableHead className="text-center">Pending</TableHead>
                        <TableHead className="text-center w-[100px]">Received Now</TableHead>
                        <TableHead className="text-center w-[100px]">Accepted</TableHead>
                        <TableHead className="text-center w-[100px]">Rejected</TableHead>
                        <TableHead className="text-right">Value</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {fields.map((field, index) => {
                        const item = watchItems[index];
                        return (
                          <TableRow key={field.id}>
                            <TableCell className="font-medium">{item.description}</TableCell>
                            <TableCell className="text-center">{item.orderedQty}</TableCell>
                            <TableCell className="text-center">{item.previouslyReceived}</TableCell>
                            <TableCell className="text-center font-medium text-yellow-600">{item.pendingQty}</TableCell>
                            <TableCell>
                              <Input
                                type="number"
                                min={0}
                                max={item.pendingQty}
                                value={item.receivedQty}
                                onChange={(e) => handleReceivedQtyChange(index, Number(e.target.value))}
                                className="w-20 text-center"
                              />
                            </TableCell>
                            <TableCell>
                              <Input
                                type="number"
                                min={0}
                                max={item.receivedQty}
                                value={item.acceptedQty}
                                onChange={(e) => handleAcceptedQtyChange(index, Number(e.target.value))}
                                className="w-20 text-center"
                              />
                            </TableCell>
                            <TableCell className="text-center">
                              <span className={item.rejectedQty > 0 ? 'text-red-600 font-medium' : ''}>
                                {item.rejectedQty}
                              </span>
                            </TableCell>
                            <TableCell className="text-right font-medium">
                              {formatCurrency(item.acceptedQty * item.unitPrice)}
                            </TableCell>
                          </TableRow>
                        );
                      })}
                      <TableRow className="bg-muted/50 font-bold">
                        <TableCell colSpan={7}>Total Accepted Value</TableCell>
                        <TableCell className="text-right">
                          {formatCurrency(calculateTotalReceivedValue())}
                        </TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>

                  {watchItems.some(item => item.rejectedQty > 0) && (
                    <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg flex items-start gap-2">
                      <AlertTriangle className="h-5 w-5 text-yellow-600 mt-0.5" />
                      <div>
                        <p className="font-medium text-yellow-800">Items Rejected</p>
                        <p className="text-sm text-yellow-700">
                          Some items have been marked as rejected. Please ensure proper documentation for returns.
                        </p>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Remarks */}
              <Card>
                <CardHeader>
                  <CardTitle>Additional Information</CardTitle>
                </CardHeader>
                <CardContent>
                  <FormField
                    control={form.control}
                    name="remarks"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Remarks</FormLabel>
                        <FormControl>
                          <Textarea
                            placeholder="Any additional remarks about the receipt..."
                            rows={3}
                            {...field}
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </CardContent>
              </Card>

              {/* Actions */}
              <div className="flex gap-2">
                <Button type="submit" disabled={isSubmitting}>
                  <CheckCircle className="h-4 w-4 mr-2" />
                  Create GRN
                </Button>
                <Button type="button" variant="ghost" onClick={() => navigate(-1)}>
                  Cancel
                </Button>
              </div>
            </>
          )}
        </form>
      </Form>
    </div>
  );
}
