import { zodResolver } from '@hookform/resolvers/zod';
import { ArrowLeft, Save } from 'lucide-react';
import { useForm } from 'react-hook-form';
import { useNavigate, useParams } from 'react-router-dom';
import { z } from 'zod';

import { PageHeader } from '@/components/common/PageHeader';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import {
  Form,
  FormControl,
  FormDescription,
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
import { Textarea } from '@/components/ui/textarea';
import { logger } from '@/lib/logger';

const NONE_OPTION_VALUE = '__none__';

const categorySchema = z.object({
  categoryCode: z.string().min(1, 'Category code is required').max(20),
  categoryName: z.string().min(1, 'Category name is required').max(100),
  description: z.string().optional(),
  parentCategoryId: z.string().optional(),
  isStockable: z.boolean(),
  requiresSerialNumber: z.boolean(),
  requiresBatchNumber: z.boolean(),
  glInventoryAccountId: z.string().optional(),
  glExpenseAccountId: z.string().optional(),
});

type CategoryFormData = z.infer<typeof categorySchema>;

const parentCategories = [
  { id: '1', name: 'Office Supplies' },
  { id: '2', name: 'IT Equipment' },
  { id: '4', name: 'Furniture' },
];

const glAccounts = [
  { id: '1', code: '1401', name: 'Inventory - Office Supplies' },
  { id: '2', code: '1402', name: 'Inventory - IT Equipment' },
  { id: '3', code: '5101', name: 'Expense - Office Supplies' },
  { id: '4', code: '5102', name: 'Expense - IT Equipment' },
];

export default function ItemCategoryForm() {
  const navigate = useNavigate();
  const { id } = useParams();
  const isEdit = Boolean(id);

  const form = useForm<CategoryFormData>({
    resolver: zodResolver(categorySchema),
    defaultValues: {
      categoryCode: '',
      categoryName: '',
      description: '',
      parentCategoryId: '',
      isStockable: true,
      requiresSerialNumber: false,
      requiresBatchNumber: false,
      glInventoryAccountId: '',
      glExpenseAccountId: '',
    },
  });

  const onSubmit = (data: CategoryFormData) => {
    logger.debug('Form submitted:', data);
    navigate('/admin/inventory/categories');
  };

  return (
    <div className="container mx-auto space-y-6 py-6">
      <PageHeader
        title={isEdit ? 'Edit Category' : 'Create Category'}
        subtitle={isEdit ? 'Update category details' : 'Add a new item category'}
        breadcrumbs={[
          { label: 'Categories', to: '/admin/inventory/categories' },
          { label: isEdit ? 'Edit' : 'New' },
        ]}
      />

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Category Information</CardTitle>
            </CardHeader>
            <CardContent className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <FormField
                control={form.control}
                name="categoryCode"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Category Code *</FormLabel>
                    <FormControl>
                      <Input placeholder="CAT-001" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="categoryName"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Category Name *</FormLabel>
                    <FormControl>
                      <Input placeholder="Enter category name" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="parentCategoryId"
                render={({ field }) => (
                    <FormItem>
                      <FormLabel>Parent Category</FormLabel>
                    <Select
                      onValueChange={(value) =>
                        field.onChange(value === NONE_OPTION_VALUE ? '' : value)
                      }
                      value={field.value || NONE_OPTION_VALUE}
                    >
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Select parent (optional)" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value={NONE_OPTION_VALUE}>None (Root Category)</SelectItem>
                        {parentCategories.map((cat) => (
                          <SelectItem key={cat.id} value={cat.id}>
                            {cat.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormDescription>Leave empty for top-level category</FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <div className="md:col-span-2">
                <FormField
                  control={form.control}
                  name="description"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Description</FormLabel>
                      <FormControl>
                        <Textarea placeholder="Enter category description" rows={3} {...field} />
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
              <CardTitle>Tracking Settings</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                <FormField
                  control={form.control}
                  name="isStockable"
                  render={({ field }) => (
                    <FormItem className="flex items-center space-x-2 space-y-0">
                      <FormControl>
                        <Checkbox checked={field.value} onCheckedChange={field.onChange} />
                      </FormControl>
                      <div>
                        <FormLabel className="font-normal">Is Stockable</FormLabel>
                        <FormDescription>Items in this category are stocked</FormDescription>
                      </div>
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="requiresSerialNumber"
                  render={({ field }) => (
                    <FormItem className="flex items-center space-x-2 space-y-0">
                      <FormControl>
                        <Checkbox checked={field.value} onCheckedChange={field.onChange} />
                      </FormControl>
                      <div>
                        <FormLabel className="font-normal">Requires Serial Number</FormLabel>
                        <FormDescription>Track items by serial number</FormDescription>
                      </div>
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="requiresBatchNumber"
                  render={({ field }) => (
                    <FormItem className="flex items-center space-x-2 space-y-0">
                      <FormControl>
                        <Checkbox checked={field.value} onCheckedChange={field.onChange} />
                      </FormControl>
                      <div>
                        <FormLabel className="font-normal">Requires Batch Number</FormLabel>
                        <FormDescription>Track items by batch</FormDescription>
                      </div>
                    </FormItem>
                  )}
                />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>GL Account Mapping</CardTitle>
            </CardHeader>
            <CardContent className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <FormField
                control={form.control}
                name="glInventoryAccountId"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Inventory GL Account</FormLabel>
                    <Select onValueChange={field.onChange} value={field.value}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Select account" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {glAccounts
                          .filter((acc) => acc.code.startsWith('14'))
                          .map((acc) => (
                            <SelectItem key={acc.id} value={acc.id}>
                              {acc.code} - {acc.name}
                            </SelectItem>
                          ))}
                      </SelectContent>
                    </Select>
                    <FormDescription>Asset account for inventory</FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="glExpenseAccountId"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Expense GL Account</FormLabel>
                    <Select onValueChange={field.onChange} value={field.value}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Select account" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {glAccounts
                          .filter((acc) => acc.code.startsWith('51'))
                          .map((acc) => (
                            <SelectItem key={acc.id} value={acc.id}>
                              {acc.code} - {acc.name}
                            </SelectItem>
                          ))}
                      </SelectContent>
                    </Select>
                    <FormDescription>Expense account for consumption</FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </CardContent>
          </Card>

          <div className="flex justify-end gap-4">
            <Button type="button" variant="outline" onClick={() => navigate(-1)}>
              Cancel
            </Button>
            <Button type="submit">
              <Save className="mr-2 h-4 w-4" />
              {isEdit ? 'Update Category' : 'Create Category'}
            </Button>
          </div>
        </form>
      </Form>
    </div>
  );
}
