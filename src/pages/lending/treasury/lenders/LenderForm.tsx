import { zodResolver } from '@hookform/resolvers/zod';
import { Save, Loader2 } from 'lucide-react';
import { useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate, useParams } from 'react-router-dom';

import { ErrorState } from '@/components/common/ErrorState';
import { PageHeader } from '@/components/common/PageHeader';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
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
import { useToast } from '@/components/ui/use-toast';
import { useCreateLender, useLender, useUpdateLender } from '@/hooks/lending/useLenders';
import {
  defaultLenderFormValues,
  lenderDetailToFormValues,
  lenderFormSchema,
  lenderFormToRequest,
  type LenderFormData,
} from '@/schemas/lending/treasuryLenderSchema';

const LENDER_TYPES = [
  { value: 'BANK', label: 'Bank' },
  { value: 'DFI', label: 'Development Finance Institution' },
  { value: 'NBFC', label: 'NBFC' },
  { value: 'MUTUAL_FUND', label: 'Mutual Fund' },
  { value: 'INSURANCE_COMPANY', label: 'Insurance Company' },
  { value: 'PENSION_FUND', label: 'Pension Fund' },
  { value: 'FII', label: 'Foreign Institutional Investor' },
  { value: 'NCD', label: 'NCD Trustee/Bondholders' },
  { value: 'CP', label: 'Commercial Paper Holders' },
  { value: 'ECB', label: 'External Commercial Borrowing' },
  { value: 'SUBORDINATED_DEBT', label: 'Subordinated Debt' },
  { value: 'RELATED_PARTY', label: 'Related Party' },
  { value: 'OTHER', label: 'Other' },
];

export default function LenderForm() {
  const navigate = useNavigate();
  const { id } = useParams();
  const { toast } = useToast();
  const isEditMode = Boolean(id);
  const { data: lender, isLoading, isError, error, refetch } = useLender(id);
  const createLenderMutation = useCreateLender();
  const updateLenderMutation = useUpdateLender();
  const saving = createLenderMutation.isPending || updateLenderMutation.isPending;

  const form = useForm<LenderFormData>({
    resolver: zodResolver(lenderFormSchema),
    defaultValues: defaultLenderFormValues,
  });

  useEffect(() => {
    if (lender) {
      form.reset(lenderDetailToFormValues(lender));
      return;
    }
    if (!isEditMode) {
      form.reset(defaultLenderFormValues);
    }
  }, [form, isEditMode, lender]);

  const onSubmit = async (data: LenderFormData) => {
    try {
      const payload = lenderFormToRequest(data);

      if (isEditMode && id) {
        await updateLenderMutation.mutateAsync({ lenderId: id, payload });
        toast({
          title: 'Success',
          description: 'Lender updated successfully',
        });
      } else {
        const newLender = await createLenderMutation.mutateAsync(payload);
        toast({
          title: 'Success',
          description: 'Lender created successfully',
        });
        navigate(`/admin/treasury/lenders/${newLender.lenderId}`);
        return;
      }
      navigate('/admin/treasury/lenders');
    } catch {
      toast({
        variant: 'destructive',
        title: 'Error',
        description: `Failed to ${isEditMode ? 'update' : 'create'} lender`,
      });
    }
  };

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (isEditMode && isError) {
    return (
      <ErrorState
        title="Could not load lender details"
        error={error}
        onRetry={() => void refetch()}
      />
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={isEditMode ? 'Edit Lender' : 'Add New Lender'}
        subtitle={
          isEditMode
            ? 'Update lender/funding source details'
            : 'Create a new lender/funding source record'
        }
        breadcrumbs={[
          { label: 'Lenders', to: '/admin/treasury/lenders' },
          { label: isEditMode ? 'Edit' : 'New' },
        ]}
      />

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
          {/* Basic Information */}
          <Card>
            <CardHeader>
              <CardTitle>Basic Information</CardTitle>
              <CardDescription>Lender identification details</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <FormField
                  control={form.control}
                  name="lenderName"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Lender Name *</FormLabel>
                      <FormControl>
                        <Input placeholder="e.g., HDFC Bank Ltd" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="lenderType"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Lender Type *</FormLabel>
                      <Select onValueChange={field.onChange} value={field.value}>
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder="Select lender type" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          {LENDER_TYPES.map((type) => (
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
              </div>

              <div className="grid gap-4 md:grid-cols-3">
                <FormField
                  control={form.control}
                  name="pan"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>PAN</FormLabel>
                      <FormControl>
                        <Input
                          placeholder="ABCDE1234F"
                          {...field}
                          className="uppercase"
                          onChange={(e) => field.onChange(e.target.value.toUpperCase())}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="cin"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>CIN</FormLabel>
                      <FormControl>
                        <Input placeholder="Corporate Identity Number" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="gstin"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>GSTIN</FormLabel>
                      <FormControl>
                        <Input
                          placeholder="22AAAAA0000A1Z5"
                          {...field}
                          className="uppercase"
                          onChange={(e) => field.onChange(e.target.value.toUpperCase())}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                <FormField
                  control={form.control}
                  name="rbiRegistration"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>RBI Registration</FormLabel>
                      <FormControl>
                        <Input placeholder="RBI registration number" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="totalSanctionLimit"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Total Sanction Limit</FormLabel>
                      <FormControl>
                        <Input
                          type="number"
                          placeholder="Maximum borrowing limit"
                          {...field}
                          onChange={(e) =>
                            field.onChange(e.target.value ? Number(e.target.value) : undefined)
                          }
                        />
                      </FormControl>
                      <FormDescription>
                        Maximum aggregate borrowing limit from this lender
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>

              <FormField
                control={form.control}
                name="registeredAddress"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Registered Address</FormLabel>
                    <FormControl>
                      <Textarea placeholder="Full registered address" {...field} rows={2} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </CardContent>
          </Card>

          {/* Contact Information */}
          <Card>
            <CardHeader>
              <CardTitle>Contact Information</CardTitle>
              <CardDescription>Primary contact details for communication</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-3">
                <FormField
                  control={form.control}
                  name="contactPerson"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Contact Person</FormLabel>
                      <FormControl>
                        <Input placeholder="Name of contact person" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="contactEmail"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Email</FormLabel>
                      <FormControl>
                        <Input type="email" placeholder="email@example.com" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="contactPhone"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Phone</FormLabel>
                      <FormControl>
                        <Input placeholder="+91 9876543210" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>
            </CardContent>
          </Card>

          {/* Bank Details */}
          <Card>
            <CardHeader>
              <CardTitle>Bank Details</CardTitle>
              <CardDescription>Bank account details for payment processing</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <FormField
                  control={form.control}
                  name="bankName"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Bank Name</FormLabel>
                      <FormControl>
                        <Input placeholder="Bank name" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="bankBranch"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Branch</FormLabel>
                      <FormControl>
                        <Input placeholder="Branch name" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>
              <div className="grid gap-4 md:grid-cols-2">
                <FormField
                  control={form.control}
                  name="bankAccountNumber"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Account Number</FormLabel>
                      <FormControl>
                        <Input placeholder="Bank account number" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="bankIfsc"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>IFSC Code</FormLabel>
                      <FormControl>
                        <Input
                          placeholder="HDFC0001234"
                          {...field}
                          className="uppercase"
                          onChange={(e) => field.onChange(e.target.value.toUpperCase())}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>
            </CardContent>
          </Card>

          {/* Credit Rating */}
          <Card>
            <CardHeader>
              <CardTitle>Credit Rating</CardTitle>
              <CardDescription>External credit rating information</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-3">
                <FormField
                  control={form.control}
                  name="externalRating"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Rating</FormLabel>
                      <FormControl>
                        <Input placeholder="e.g., AAA, AA+, A1+" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="ratingAgency"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Rating Agency</FormLabel>
                      <Select onValueChange={field.onChange} value={field.value}>
                        <FormControl>
                          <SelectTrigger>
                            <SelectValue placeholder="Select agency" />
                          </SelectTrigger>
                        </FormControl>
                        <SelectContent>
                          <SelectItem value="CRISIL">CRISIL</SelectItem>
                          <SelectItem value="ICRA">ICRA</SelectItem>
                          <SelectItem value="CARE">CARE</SelectItem>
                          <SelectItem value="India Ratings">India Ratings</SelectItem>
                          <SelectItem value="Acuite">Acuite</SelectItem>
                          <SelectItem value="Brickwork">Brickwork</SelectItem>
                        </SelectContent>
                      </Select>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="ratingDate"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Rating Date</FormLabel>
                      <FormControl>
                        <Input type="date" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>
            </CardContent>
          </Card>

          {/* Additional Information */}
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
                      <Textarea placeholder="Any additional notes or remarks" {...field} rows={3} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </CardContent>
          </Card>

          {/* Actions */}
          <div className="flex justify-end gap-4">
            <Button type="button" variant="outline" onClick={() => navigate(-1)} disabled={saving}>
              Cancel
            </Button>
            <Button type="submit" disabled={saving}>
              {saving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              <Save className="mr-2 h-4 w-4" />
              {isEditMode ? 'Update Lender' : 'Create Lender'}
            </Button>
          </div>
        </form>
      </Form>
    </div>
  );
}
