import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, Save, Loader2 } from 'lucide-react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
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
import { Separator } from '@/components/ui/separator';
import { treasuryApi, CreateLenderRequest } from '@/services/lending/treasuryApi';
import { useToast } from '@/components/ui/use-toast';

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

const lenderFormSchema = z.object({
  lender_name: z.string().min(1, 'Lender name is required').max(200),
  lender_type: z.string().min(1, 'Lender type is required'),
  pan: z.string().regex(/^[A-Z]{5}[0-9]{4}[A-Z]{1}$/, 'Invalid PAN format').optional().or(z.literal('')),
  cin: z.string().max(25).optional().or(z.literal('')),
  gstin: z.string().regex(/^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$/, 'Invalid GSTIN format').optional().or(z.literal('')),
  rbi_registration: z.string().max(50).optional().or(z.literal('')),
  registered_address: z.string().optional().or(z.literal('')),
  contact_person: z.string().max(100).optional().or(z.literal('')),
  contact_email: z.string().email('Invalid email').optional().or(z.literal('')),
  contact_phone: z.string().max(20).optional().or(z.literal('')),
  bank_name: z.string().max(100).optional().or(z.literal('')),
  bank_branch: z.string().max(100).optional().or(z.literal('')),
  bank_account_number: z.string().max(30).optional().or(z.literal('')),
  bank_ifsc: z.string().regex(/^[A-Z]{4}0[A-Z0-9]{6}$/, 'Invalid IFSC code').optional().or(z.literal('')),
  external_rating: z.string().max(20).optional().or(z.literal('')),
  rating_agency: z.string().max(50).optional().or(z.literal('')),
  rating_date: z.string().optional().or(z.literal('')),
  total_sanction_limit: z.coerce.number().nonnegative().optional(),
  remarks: z.string().optional().or(z.literal('')),
});

type LenderFormData = z.infer<typeof lenderFormSchema>;

export default function LenderForm() {
  const navigate = useNavigate();
  const { id } = useParams();
  const { toast } = useToast();
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const isEditMode = Boolean(id);

  const form = useForm<LenderFormData>({
    resolver: zodResolver(lenderFormSchema) as any,
    defaultValues: {
      lender_name: '',
      lender_type: '',
      pan: '',
      cin: '',
      gstin: '',
      rbi_registration: '',
      registered_address: '',
      contact_person: '',
      contact_email: '',
      contact_phone: '',
      bank_name: '',
      bank_branch: '',
      bank_account_number: '',
      bank_ifsc: '',
      external_rating: '',
      rating_agency: '',
      rating_date: '',
      total_sanction_limit: undefined,
      remarks: '',
    },
  });

  useEffect(() => {
    if (isEditMode && id) {
      loadLender(id);
    }
  }, [id, isEditMode]);

  const loadLender = async (lenderId: string) => {
    setLoading(true);
    try {
      const lender = await treasuryApi.getLender(lenderId);
      form.reset({
        lender_name: lender.lender_name || '',
        lender_type: lender.lender_type || '',
        pan: lender.pan || '',
        cin: lender.cin || '',
        gstin: lender.gstin || '',
        rbi_registration: lender.rbi_registration || '',
        registered_address: lender.registered_address || '',
        contact_person: lender.contact_person || '',
        contact_email: lender.contact_email || '',
        contact_phone: lender.contact_phone || '',
        bank_name: lender.bank_name || '',
        bank_branch: lender.bank_branch || '',
        bank_account_number: lender.bank_account_number || '',
        bank_ifsc: lender.bank_ifsc || '',
        external_rating: lender.external_rating || '',
        rating_agency: lender.rating_agency || '',
        rating_date: lender.rating_date || '',
        total_sanction_limit: lender.total_sanction_limit || undefined,
        remarks: lender.remarks || '',
      });
    } catch (error) {
      console.error('Failed to load lender:', error);
      toast({
        variant: 'destructive',
        title: 'Error',
        description: 'Failed to load lender details',
      });
    } finally {
      setLoading(false);
    }
  };

  const onSubmit = async (data: LenderFormData) => {
    setSaving(true);
    try {
      const payload: CreateLenderRequest = {
        lender_name: data.lender_name,
        lender_type: data.lender_type as CreateLenderRequest['lender_type'],
        contact_person: data.contact_person || undefined,
        contact_email: data.contact_email || undefined,
        contact_phone: data.contact_phone || undefined,
        address: data.registered_address || undefined,
        remarks: data.remarks || undefined,
      };

      if (isEditMode && id) {
        await treasuryApi.updateLender(id, payload);
        toast({
          title: 'Success',
          description: 'Lender updated successfully',
        });
      } else {
        const newLender = await treasuryApi.createLender(payload);
        toast({
          title: 'Success',
          description: 'Lender created successfully',
        });
        navigate(`/admin/lending/treasury/lenders/${newLender.lender_id}`);
        return;
      }
      navigate('/admin/lending/treasury/lenders');
    } catch (error) {
      console.error('Failed to save lender:', error);
      toast({
        variant: 'destructive',
        title: 'Error',
        description: `Failed to ${isEditMode ? 'update' : 'create'} lender`,
      });
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => navigate(-1)}>
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div>
          <h1 className="text-2xl font-semibold">
            {isEditMode ? 'Edit Lender' : 'Add New Lender'}
          </h1>
          <p className="text-muted-foreground">
            {isEditMode
              ? 'Update lender/funding source details'
              : 'Create a new lender/funding source record'}
          </p>
        </div>
      </div>

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit as any)} className="space-y-6">
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
                  name="lender_name"
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
                  name="lender_type"
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
                          onChange={(e) =>
                            field.onChange(e.target.value.toUpperCase())
                          }
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
                          onChange={(e) =>
                            field.onChange(e.target.value.toUpperCase())
                          }
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
                  name="rbi_registration"
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
                  name="total_sanction_limit"
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
                name="registered_address"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Registered Address</FormLabel>
                    <FormControl>
                      <Textarea
                        placeholder="Full registered address"
                        {...field}
                        rows={2}
                      />
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
                  name="contact_person"
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
                  name="contact_email"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Email</FormLabel>
                      <FormControl>
                        <Input
                          type="email"
                          placeholder="email@example.com"
                          {...field}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="contact_phone"
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
              <CardDescription>
                Bank account details for payment processing
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <FormField
                  control={form.control}
                  name="bank_name"
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
                  name="bank_branch"
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
                  name="bank_account_number"
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
                  name="bank_ifsc"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>IFSC Code</FormLabel>
                      <FormControl>
                        <Input
                          placeholder="HDFC0001234"
                          {...field}
                          className="uppercase"
                          onChange={(e) =>
                            field.onChange(e.target.value.toUpperCase())
                          }
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
                  name="external_rating"
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
                  name="rating_agency"
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
                  name="rating_date"
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
                      <Textarea
                        placeholder="Any additional notes or remarks"
                        {...field}
                        rows={3}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </CardContent>
          </Card>

          {/* Actions */}
          <div className="flex justify-end gap-4">
            <Button
              type="button"
              variant="outline"
              onClick={() => navigate(-1)}
              disabled={saving}
            >
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
