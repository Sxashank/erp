import { useState } from 'react';
import { useForm, useFieldArray } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Link, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { PageHeader } from '@/components/common/PageHeader';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  ArrowLeft,
  FileText,
  Plus,
  Trash2,
  Save,
  Send,
} from 'lucide-react';

const lineItemSchema = z.object({
  description: z.string().min(1, 'Description is required'),
  quantity: z.number().min(1, 'Quantity must be at least 1'),
  uom: z.string().min(1, 'UOM is required'),
  specifications: z.string().optional(),
});

const rfqSchema = z.object({
  title: z.string().min(1, 'Title is required'),
  category: z.string().min(1, 'Category is required'),
  description: z.string().optional(),
  startDate: z.string().min(1, 'Start date is required'),
  endDate: z.string().min(1, 'End date is required'),
  deliveryDate: z.string().min(1, 'Expected delivery date is required'),
  deliveryLocation: z.string().min(1, 'Delivery location is required'),
  paymentTerms: z.string().min(1, 'Payment terms required'),
  vendors: z.array(z.string()).min(1, 'At least one vendor required'),
  lineItems: z.array(lineItemSchema).min(1, 'At least one item required'),
  termsConditions: z.string().optional(),
});

type RFQFormData = z.infer<typeof rfqSchema>;

// Mock categories
const categories = [
  { id: 'FURNITURE', name: 'Furniture' },
  { id: 'IT_HARDWARE', name: 'IT Hardware' },
  { id: 'IT_SOFTWARE', name: 'IT Software' },
  { id: 'OFFICE_SUPPLIES', name: 'Office Supplies' },
  { id: 'SERVICES', name: 'Services' },
  { id: 'MAINTENANCE', name: 'Maintenance' },
];

// Mock vendors
const availableVendors = [
  { id: 'V001', name: 'ABC Suppliers Ltd', category: 'FURNITURE' },
  { id: 'V002', name: 'XYZ Tech Solutions', category: 'IT_HARDWARE' },
  { id: 'V003', name: 'Office Pro', category: 'OFFICE_SUPPLIES' },
  { id: 'V004', name: 'Tech World', category: 'IT_HARDWARE' },
  { id: 'V005', name: 'Furniture Hub', category: 'FURNITURE' },
  { id: 'V006', name: 'Services Plus', category: 'SERVICES' },
];

const uomOptions = [
  { id: 'PCS', name: 'Pieces' },
  { id: 'NOS', name: 'Numbers' },
  { id: 'KG', name: 'Kilograms' },
  { id: 'MTR', name: 'Meters' },
  { id: 'SET', name: 'Sets' },
  { id: 'LOT', name: 'Lots' },
];

export default function RFQCreate() {
  const navigate = useNavigate();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [selectedVendors, setSelectedVendors] = useState<string[]>([]);

  const form = useForm<RFQFormData>({
    resolver: zodResolver(rfqSchema),
    defaultValues: {
      title: '',
      category: '',
      description: '',
      startDate: new Date().toISOString().split('T')[0],
      endDate: '',
      deliveryDate: '',
      deliveryLocation: 'Head Office',
      paymentTerms: '30_DAYS',
      vendors: [],
      lineItems: [
        { description: '', quantity: 1, uom: 'PCS', specifications: '' },
      ],
      termsConditions: '',
    },
  });

  const { fields, append, remove } = useFieldArray({
    control: form.control,
    name: 'lineItems',
  });

  const toggleVendor = (vendorId: string) => {
    const current = form.getValues('vendors');
    if (current.includes(vendorId)) {
      form.setValue('vendors', current.filter(v => v !== vendorId));
    } else {
      form.setValue('vendors', [...current, vendorId]);
    }
  };

  const onSubmit = async (data: RFQFormData, action: 'draft' | 'publish') => {
    setIsSubmitting(true);
    await new Promise(resolve => setTimeout(resolve, 1500));
    setIsSubmitting(false);
    navigate('/admin/procurement/rfq');
  };

  const selectedCategory = form.watch('category');
  const vendorsForCategory = availableVendors.filter(
    v => !selectedCategory || v.category === selectedCategory
  );

  return (
    <div className="container mx-auto py-6 space-y-6">
      <PageHeader
        title="Create RFQ"
        subtitle="Create a new request for quotation"
        breadcrumbs={[
          { label: 'Request for Quotation', to: '/admin/procurement/rfq' },
          { label: 'New' },
        ]}
      />

      <Form {...form}>
        <form className="space-y-6">
          {/* Basic Information */}
          <Card>
            <CardHeader>
              <CardTitle>Basic Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <FormField
                  control={form.control}
                  name="title"
                  render={({ field }) => (
                    <FormItem className="md:col-span-2">
                      <FormLabel>RFQ Title</FormLabel>
                      <FormControl>
                        <Input placeholder="Enter RFQ title" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="category"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Category</FormLabel>
                      <Select onValueChange={field.onChange} value={field.value}>
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder="Select category" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          {categories.map(cat => (
                            <SelectItem key={cat.id} value={cat.id}>{cat.name}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="paymentTerms"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Payment Terms</FormLabel>
                      <Select onValueChange={field.onChange} value={field.value}>
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder="Select payment terms" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          <SelectItem value="IMMEDIATE">Immediate</SelectItem>
                          <SelectItem value="15_DAYS">Net 15 Days</SelectItem>
                          <SelectItem value="30_DAYS">Net 30 Days</SelectItem>
                          <SelectItem value="45_DAYS">Net 45 Days</SelectItem>
                          <SelectItem value="60_DAYS">Net 60 Days</SelectItem>
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>

              <FormField
                control={form.control}
                name="description"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Description</FormLabel>
                    <FormControl>
                      <Textarea placeholder="Detailed description..." rows={3} {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </CardContent>
          </Card>

          {/* Timeline */}
          <Card>
            <CardHeader>
              <CardTitle>Timeline</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <FormField
                  control={form.control}
                  name="startDate"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>RFQ Start Date</FormLabel>
                      <FormControl>
                        <Input type="date" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="endDate"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>RFQ End Date</FormLabel>
                      <FormControl>
                        <Input type="date" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="deliveryDate"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Expected Delivery</FormLabel>
                      <FormControl>
                        <Input type="date" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>

              <FormField
                control={form.control}
                name="deliveryLocation"
                render={({ field }) => (
                  <FormItem className="mt-4">
                    <FormLabel>Delivery Location</FormLabel>
                    <FormControl>
                      <Input placeholder="Enter delivery location" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </CardContent>
          </Card>

          {/* Line Items */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>Line Items</span>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => append({ description: '', quantity: 1, uom: 'PCS', specifications: '' })}
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Add Item
                </Button>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[300px]">Description</TableHead>
                    <TableHead className="w-[100px]">Quantity</TableHead>
                    <TableHead className="w-[120px]">UOM</TableHead>
                    <TableHead>Specifications</TableHead>
                    <TableHead className="w-[60px]"></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {fields.map((field, index) => (
                    <TableRow key={field.id}>
                      <TableCell>
                        <FormField
                          control={form.control}
                          name={`lineItems.${index}.description`}
                          render={({ field }) => (
                            <Input placeholder="Item description" {...field} />
                          )}
                        />
                      </TableCell>
                      <TableCell>
                        <FormField
                          control={form.control}
                          name={`lineItems.${index}.quantity`}
                          render={({ field }) => (
                            <Input
                              type="number"
                              {...field}
                              onChange={(e) => field.onChange(Number(e.target.value))}
                            />
                          )}
                        />
                      </TableCell>
                      <TableCell>
                        <FormField
                          control={form.control}
                          name={`lineItems.${index}.uom`}
                          render={({ field }) => (
                            <Select onValueChange={field.onChange} value={field.value}>
                              <SelectTrigger>
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                {uomOptions.map(uom => (
                                  <SelectItem key={uom.id} value={uom.id}>{uom.name}</SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          )}
                        />
                      </TableCell>
                      <TableCell>
                        <FormField
                          control={form.control}
                          name={`lineItems.${index}.specifications`}
                          render={({ field }) => (
                            <Input placeholder="Specifications" {...field} />
                          )}
                        />
                      </TableCell>
                      <TableCell>
                        {fields.length > 1 && (
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            onClick={() => remove(index)}
                          >
                            <Trash2 className="h-4 w-4 text-red-500" />
                          </Button>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          {/* Vendor Selection */}
          <Card>
            <CardHeader>
              <CardTitle>Select Vendors</CardTitle>
              <CardDescription>Choose vendors to send this RFQ to</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {vendorsForCategory.map((vendor) => {
                  const isSelected = form.watch('vendors').includes(vendor.id);
                  return (
                    <div
                      key={vendor.id}
                      className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                        isSelected ? 'border-primary bg-primary/5' : 'hover:bg-muted/50'
                      }`}
                      onClick={() => toggleVendor(vendor.id)}
                    >
                      <div className="flex items-center gap-3">
                        <Checkbox checked={isSelected} />
                        <div>
                          <p className="font-medium">{vendor.name}</p>
                          <p className="text-sm text-muted-foreground">{vendor.id}</p>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
              {form.formState.errors.vendors && (
                <p className="text-sm text-red-500 mt-2">{form.formState.errors.vendors.message}</p>
              )}
            </CardContent>
          </Card>

          {/* Actions */}
          <div className="flex gap-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => onSubmit(form.getValues(), 'draft')}
              disabled={isSubmitting}
            >
              <Save className="h-4 w-4 mr-2" />
              Save as Draft
            </Button>
            <Button
              type="button"
              onClick={() => onSubmit(form.getValues(), 'publish')}
              disabled={isSubmitting}
            >
              <Send className="h-4 w-4 mr-2" />
              Publish & Send
            </Button>
            <Button type="button" variant="ghost" onClick={() => navigate(-1)}>
              Cancel
            </Button>
          </div>
        </form>
      </Form>
    </div>
  );
}
