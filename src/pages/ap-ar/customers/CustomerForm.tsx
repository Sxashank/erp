import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, Save, Loader2, Copy } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { PageHeader } from '@/components/common/PageHeader';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/hooks/use-toast';
import {
  customersApi,
  organizationsApi,
  tdsSectionsApi,
  accountsApi,
  paymentTermsApi,
} from '@/services/api';

interface Organization {
  id: string;
  code: string;
  name: string;
}

interface TDSSection {
  id: string;
  section_code: string;
  description: string;
}

interface Account {
  id: string;
  code: string;
  name: string;
}

interface PaymentTerms {
  id: string;
  code: string;
  name: string;
}

const INDIAN_STATES = [
  { code: '01', name: 'Jammu & Kashmir' },
  { code: '02', name: 'Himachal Pradesh' },
  { code: '03', name: 'Punjab' },
  { code: '04', name: 'Chandigarh' },
  { code: '05', name: 'Uttarakhand' },
  { code: '06', name: 'Haryana' },
  { code: '07', name: 'Delhi' },
  { code: '08', name: 'Rajasthan' },
  { code: '09', name: 'Uttar Pradesh' },
  { code: '10', name: 'Bihar' },
  { code: '11', name: 'Sikkim' },
  { code: '12', name: 'Arunachal Pradesh' },
  { code: '13', name: 'Nagaland' },
  { code: '14', name: 'Manipur' },
  { code: '15', name: 'Mizoram' },
  { code: '16', name: 'Tripura' },
  { code: '17', name: 'Meghalaya' },
  { code: '18', name: 'Assam' },
  { code: '19', name: 'West Bengal' },
  { code: '20', name: 'Jharkhand' },
  { code: '21', name: 'Odisha' },
  { code: '22', name: 'Chhattisgarh' },
  { code: '23', name: 'Madhya Pradesh' },
  { code: '24', name: 'Gujarat' },
  { code: '26', name: 'Dadra & Nagar Haveli and Daman & Diu' },
  { code: '27', name: 'Maharashtra' },
  { code: '29', name: 'Karnataka' },
  { code: '30', name: 'Goa' },
  { code: '31', name: 'Lakshadweep' },
  { code: '32', name: 'Kerala' },
  { code: '33', name: 'Tamil Nadu' },
  { code: '34', name: 'Puducherry' },
  { code: '35', name: 'Andaman & Nicobar Islands' },
  { code: '36', name: 'Telangana' },
  { code: '37', name: 'Andhra Pradesh' },
  { code: '38', name: 'Ladakh' },
];

export function CustomerForm() {
  const navigate = useNavigate();
  const { id } = useParams();
  const { toast } = useToast();
  const isEditMode = Boolean(id);

  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [tdsSections, setTdsSections] = useState<TDSSection[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [paymentTerms, setPaymentTerms] = useState<PaymentTerms[]>([]);

  const [formData, setFormData] = useState({
    // Basic Info
    code: '',
    name: '',
    display_name: '',
    customer_type: 'COMPANY',
    organization_id: '',

    // Tax & Compliance
    pan: '',
    gstin: '',
    gst_registration_type: '',
    place_of_supply_state: '',
    tcs_applicable: false,
    tcs_section_id: '',

    // Contact & Billing Address
    contact_person: '',
    email: '',
    phone: '',
    mobile: '',
    billing_address_line1: '',
    billing_address_line2: '',
    billing_city: '',
    billing_state_code: '',
    billing_pincode: '',
    billing_country: 'India',

    // Shipping Address
    shipping_address_line1: '',
    shipping_address_line2: '',
    shipping_city: '',
    shipping_state_code: '',
    shipping_pincode: '',
    shipping_country: 'India',

    // Banking Details
    bank_name: '',
    bank_account_number: '',
    bank_ifsc_code: '',
    bank_branch: '',
    payment_mode_preference: '',

    // Financial Settings
    control_account_id: '',
    revenue_account_id: '',
    payment_terms_id: '',
    credit_days: '30',
    credit_limit: '',
    credit_limit_enabled: false,
    currency_code: 'INR',

    // Balances
    opening_balance: '0',
    opening_balance_type: '',

    // Notes
    remarks: '',
    is_active: true,
  });

  useEffect(() => {
    loadInitialData();
  }, []);

  useEffect(() => {
    if (isEditMode && id) {
      loadCustomer(id);
    }
  }, [id, isEditMode]);

  useEffect(() => {
    if (formData.organization_id) {
      loadOrganizationData(formData.organization_id);
    }
  }, [formData.organization_id]);

  const loadInitialData = async () => {
    try {
      const [orgsRes, tdsRes] = await Promise.all([
        organizationsApi.list({ page: 1, page_size: 100 }),
        tdsSectionsApi.list({ page: 1, page_size: 100, include_inactive: false }),
      ]);
      setOrganizations(orgsRes.data.items || []);
      setTdsSections(tdsRes.data.items || []);

      if (!isEditMode && orgsRes.data.items?.length > 0) {
        const firstOrg = orgsRes.data.items[0];
        setFormData((prev) => ({ ...prev, organization_id: firstOrg.id }));
      }
    } catch (error) {
      console.error('Failed to load initial data:', error);
      toast({
        title: 'Error',
        description: 'Failed to load form data',
        variant: 'destructive',
      });
    }
  };

  const loadOrganizationData = async (orgId: string) => {
    try {
      const [accountsRes, termsRes] = await Promise.all([
        accountsApi.list({ organization_id: orgId, page: 1, page_size: 500 }),
        paymentTermsApi.getActive({ organization_id: orgId }),
      ]);
      setAccounts(accountsRes.data.items || []);
      setPaymentTerms(termsRes.data || []);

      // Generate code for new customer
      if (!isEditMode) {
        const codeRes = await customersApi.generateCode({ organization_id: orgId });
        setFormData((prev) => ({ ...prev, code: codeRes.data.code }));
      }
    } catch (error) {
      console.error('Failed to load organization data:', error);
    }
  };

  const loadCustomer = async (customerId: string) => {
    setLoading(true);
    try {
      const response = await customersApi.get(customerId);
      const customer = response.data;
      setFormData({
        code: customer.code || '',
        name: customer.name || '',
        display_name: customer.display_name || '',
        customer_type: customer.customer_type || 'COMPANY',
        organization_id: customer.organization_id || '',

        pan: customer.pan || '',
        gstin: customer.gstin || '',
        gst_registration_type: customer.gst_registration_type || '',
        place_of_supply_state: customer.place_of_supply_state || '',
        tcs_applicable: customer.tcs_applicable || false,
        tcs_section_id: customer.tcs_section_id || '',

        contact_person: customer.contact_person || '',
        email: customer.email || '',
        phone: customer.phone || '',
        mobile: customer.mobile || '',
        billing_address_line1: customer.billing_address_line1 || '',
        billing_address_line2: customer.billing_address_line2 || '',
        billing_city: customer.billing_city || '',
        billing_state_code: customer.billing_state_code || '',
        billing_pincode: customer.billing_pincode || '',
        billing_country: customer.billing_country || 'India',

        shipping_address_line1: customer.shipping_address_line1 || '',
        shipping_address_line2: customer.shipping_address_line2 || '',
        shipping_city: customer.shipping_city || '',
        shipping_state_code: customer.shipping_state_code || '',
        shipping_pincode: customer.shipping_pincode || '',
        shipping_country: customer.shipping_country || 'India',

        bank_name: customer.bank_name || '',
        bank_account_number: customer.bank_account_number || '',
        bank_ifsc_code: customer.bank_ifsc_code || '',
        bank_branch: customer.bank_branch || '',
        payment_mode_preference: customer.payment_mode_preference || '',

        control_account_id: customer.control_account_id || '',
        revenue_account_id: customer.revenue_account_id || '',
        payment_terms_id: customer.payment_terms_id || '',
        credit_days: customer.credit_days?.toString() || '30',
        credit_limit: customer.credit_limit?.toString() || '',
        credit_limit_enabled: customer.credit_limit_enabled || false,
        currency_code: customer.currency_code || 'INR',

        opening_balance: customer.opening_balance?.toString() || '0',
        opening_balance_type: customer.opening_balance_type || '',

        remarks: customer.remarks || '',
        is_active: customer.is_active ?? true,
      });
    } catch (error) {
      console.error('Failed to load customer:', error);
      toast({
        title: 'Error',
        description: 'Failed to load customer details',
        variant: 'destructive',
      });
      navigate('/admin/ap-ar/customers');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (field: string, value: any) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const copyBillingToShipping = () => {
    setFormData((prev) => ({
      ...prev,
      shipping_address_line1: prev.billing_address_line1,
      shipping_address_line2: prev.billing_address_line2,
      shipping_city: prev.billing_city,
      shipping_state_code: prev.billing_state_code,
      shipping_pincode: prev.billing_pincode,
      shipping_country: prev.billing_country,
    }));
    toast({
      title: 'Copied',
      description: 'Billing address copied to shipping address',
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validation
    if (!formData.organization_id) {
      toast({
        title: 'Validation Error',
        description: 'Please select an organization',
        variant: 'destructive',
      });
      return;
    }
    if (!formData.code.trim()) {
      toast({
        title: 'Validation Error',
        description: 'Customer code is required',
        variant: 'destructive',
      });
      return;
    }
    if (!formData.name.trim()) {
      toast({
        title: 'Validation Error',
        description: 'Customer name is required',
        variant: 'destructive',
      });
      return;
    }

    setSaving(true);
    try {
      const payload = {
        ...formData,
        credit_days: parseInt(formData.credit_days) || 30,
        credit_limit: formData.credit_limit ? parseFloat(formData.credit_limit) : null,
        opening_balance: parseFloat(formData.opening_balance) || 0,
        tcs_section_id: formData.tcs_section_id || null,
        control_account_id: formData.control_account_id || null,
        revenue_account_id: formData.revenue_account_id || null,
        payment_terms_id: formData.payment_terms_id || null,
        gst_registration_type: formData.gst_registration_type || null,
        opening_balance_type: formData.opening_balance_type || null,
        payment_mode_preference: formData.payment_mode_preference || null,
        place_of_supply_state: formData.place_of_supply_state || null,
      };

      if (isEditMode && id) {
        await customersApi.update(id, payload);
        toast({
          title: 'Success',
          description: 'Customer updated successfully',
        });
      } else {
        await customersApi.create(payload);
        toast({
          title: 'Success',
          description: 'Customer created successfully',
        });
      }
      navigate('/admin/ap-ar/customers');
    } catch (error: any) {
      console.error('Failed to save customer:', error);
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to save customer',
        variant: 'destructive',
      });
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-slate-400" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={isEditMode ? 'Edit Customer' : 'New Customer'}
        subtitle={
          isEditMode ? 'Update customer details' : 'Create a new customer record'
        }
        breadcrumbs={[
          { label: 'Customers', to: '/admin/ap-ar/customers' },
          { label: isEditMode ? 'Edit' : 'New' },
        ]}
      />

      <form onSubmit={handleSubmit}>
        <Tabs defaultValue="basic" className="space-y-6">
          <TabsList className="bg-slate-100">
            <TabsTrigger value="basic">Basic Info</TabsTrigger>
            <TabsTrigger value="tax">Tax & Compliance</TabsTrigger>
            <TabsTrigger value="address">Addresses</TabsTrigger>
            <TabsTrigger value="banking">Banking</TabsTrigger>
            <TabsTrigger value="financial">Financial Settings</TabsTrigger>
          </TabsList>

          {/* Basic Info Tab */}
          <TabsContent value="basic">
            <Card>
              <CardHeader>
                <CardTitle>Basic Information</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="organization_id">Organization *</Label>
                    <Select
                      value={formData.organization_id}
                      onValueChange={(value) => handleChange('organization_id', value)}
                      disabled={isEditMode}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select organization" />
                      </SelectTrigger>
                      <SelectContent>
                        {organizations.map((org) => (
                          <SelectItem key={org.id} value={org.id}>
                            {org.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="code">Customer Code *</Label>
                    <Input
                      id="code"
                      value={formData.code}
                      onChange={(e) => handleChange('code', e.target.value.toUpperCase())}
                      placeholder="C001"
                      maxLength={20}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="name">Legal Name *</Label>
                    <Input
                      id="name"
                      value={formData.name}
                      onChange={(e) => handleChange('name', e.target.value)}
                      placeholder="Legal name as per registration"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="display_name">Display/Trade Name</Label>
                    <Input
                      id="display_name"
                      value={formData.display_name}
                      onChange={(e) => handleChange('display_name', e.target.value)}
                      placeholder="Trade name (optional)"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="customer_type">Customer Type *</Label>
                    <Select
                      value={formData.customer_type}
                      onValueChange={(value) => handleChange('customer_type', value)}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="INDIVIDUAL">Individual</SelectItem>
                        <SelectItem value="COMPANY">Company</SelectItem>
                        <SelectItem value="GOVERNMENT">Government</SelectItem>
                        <SelectItem value="OTHERS">Others</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="flex items-center space-x-2 pt-8">
                    <Checkbox
                      id="is_active"
                      checked={formData.is_active}
                      onCheckedChange={(checked) => handleChange('is_active', checked === true)}
                    />
                    <Label htmlFor="is_active">Active</Label>
                  </div>
                </div>

                <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="contact_person">Contact Person</Label>
                    <Input
                      id="contact_person"
                      value={formData.contact_person}
                      onChange={(e) => handleChange('contact_person', e.target.value)}
                      placeholder="Primary contact name"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="email">Email</Label>
                    <Input
                      id="email"
                      type="email"
                      value={formData.email}
                      onChange={(e) => handleChange('email', e.target.value)}
                      placeholder="customer@example.com"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="phone">Phone</Label>
                    <Input
                      id="phone"
                      value={formData.phone}
                      onChange={(e) => handleChange('phone', e.target.value)}
                      placeholder="Landline number"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="mobile">Mobile</Label>
                    <Input
                      id="mobile"
                      value={formData.mobile}
                      onChange={(e) => handleChange('mobile', e.target.value)}
                      placeholder="Mobile number"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="remarks">Remarks</Label>
                  <Textarea
                    id="remarks"
                    value={formData.remarks}
                    onChange={(e) => handleChange('remarks', e.target.value)}
                    placeholder="Additional notes..."
                    rows={3}
                  />
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Tax & Compliance Tab */}
          <TabsContent value="tax">
            <Card>
              <CardHeader>
                <CardTitle>Tax & Compliance</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="pan">PAN</Label>
                    <Input
                      id="pan"
                      value={formData.pan}
                      onChange={(e) => handleChange('pan', e.target.value.toUpperCase())}
                      placeholder="AAAAA0000A"
                      maxLength={10}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="gstin">GSTIN</Label>
                    <Input
                      id="gstin"
                      value={formData.gstin}
                      onChange={(e) => handleChange('gstin', e.target.value.toUpperCase())}
                      placeholder="22AAAAA0000A1Z5"
                      maxLength={15}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="gst_registration_type">GST Registration Type</Label>
                    <Select
                      value={formData.gst_registration_type}
                      onValueChange={(value) => handleChange('gst_registration_type', value)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select type" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="REGULAR">Regular</SelectItem>
                        <SelectItem value="COMPOSITION">Composition</SelectItem>
                        <SelectItem value="UNREGISTERED">Unregistered</SelectItem>
                        <SelectItem value="SEZ">SEZ</SelectItem>
                        <SelectItem value="DEEMED_EXPORT">Deemed Export</SelectItem>
                        <SelectItem value="OVERSEAS">Overseas</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="place_of_supply_state">Default Place of Supply</Label>
                    <Select
                      value={formData.place_of_supply_state}
                      onValueChange={(value) => handleChange('place_of_supply_state', value)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select state" />
                      </SelectTrigger>
                      <SelectContent>
                        {INDIAN_STATES.map((state) => (
                          <SelectItem key={state.code} value={state.code}>
                            {state.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="border-t pt-4">
                  <h4 className="font-medium mb-3">TCS Configuration</h4>
                  <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="tcs_applicable"
                        checked={formData.tcs_applicable}
                        onCheckedChange={(checked) =>
                          handleChange('tcs_applicable', checked === true)
                        }
                      />
                      <Label htmlFor="tcs_applicable">TCS Applicable</Label>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="tcs_section_id">TCS Section</Label>
                      <Select
                        value={formData.tcs_section_id}
                        onValueChange={(value) => handleChange('tcs_section_id', value)}
                        disabled={!formData.tcs_applicable}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select section" />
                        </SelectTrigger>
                        <SelectContent>
                          {tdsSections
                            .filter((s) => s.section_code.startsWith('206'))
                            .map((section) => (
                              <SelectItem key={section.id} value={section.id}>
                                {section.section_code} - {section.description}
                              </SelectItem>
                            ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Addresses Tab */}
          <TabsContent value="address">
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Billing Address</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="billing_address_line1">Address Line 1</Label>
                    <Input
                      id="billing_address_line1"
                      value={formData.billing_address_line1}
                      onChange={(e) => handleChange('billing_address_line1', e.target.value)}
                      placeholder="Building, Street"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="billing_address_line2">Address Line 2</Label>
                    <Input
                      id="billing_address_line2"
                      value={formData.billing_address_line2}
                      onChange={(e) => handleChange('billing_address_line2', e.target.value)}
                      placeholder="Area, Landmark"
                    />
                  </div>
                  <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                    <div className="space-y-2">
                      <Label htmlFor="billing_city">City</Label>
                      <Input
                        id="billing_city"
                        value={formData.billing_city}
                        onChange={(e) => handleChange('billing_city', e.target.value)}
                        placeholder="City"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="billing_state_code">State</Label>
                      <Select
                        value={formData.billing_state_code}
                        onValueChange={(value) => handleChange('billing_state_code', value)}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select state" />
                        </SelectTrigger>
                        <SelectContent>
                          {INDIAN_STATES.map((state) => (
                            <SelectItem key={state.code} value={state.code}>
                              {state.name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="billing_pincode">Pincode</Label>
                      <Input
                        id="billing_pincode"
                        value={formData.billing_pincode}
                        onChange={(e) => handleChange('billing_pincode', e.target.value)}
                        placeholder="000000"
                        maxLength={6}
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between">
                  <CardTitle>Shipping Address</CardTitle>
                  <Button type="button" variant="outline" size="sm" onClick={copyBillingToShipping}>
                    <Copy className="mr-2 h-4 w-4" />
                    Copy from Billing
                  </Button>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="shipping_address_line1">Address Line 1</Label>
                    <Input
                      id="shipping_address_line1"
                      value={formData.shipping_address_line1}
                      onChange={(e) => handleChange('shipping_address_line1', e.target.value)}
                      placeholder="Building, Street"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="shipping_address_line2">Address Line 2</Label>
                    <Input
                      id="shipping_address_line2"
                      value={formData.shipping_address_line2}
                      onChange={(e) => handleChange('shipping_address_line2', e.target.value)}
                      placeholder="Area, Landmark"
                    />
                  </div>
                  <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                    <div className="space-y-2">
                      <Label htmlFor="shipping_city">City</Label>
                      <Input
                        id="shipping_city"
                        value={formData.shipping_city}
                        onChange={(e) => handleChange('shipping_city', e.target.value)}
                        placeholder="City"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="shipping_state_code">State</Label>
                      <Select
                        value={formData.shipping_state_code}
                        onValueChange={(value) => handleChange('shipping_state_code', value)}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select state" />
                        </SelectTrigger>
                        <SelectContent>
                          {INDIAN_STATES.map((state) => (
                            <SelectItem key={state.code} value={state.code}>
                              {state.name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="shipping_pincode">Pincode</Label>
                      <Input
                        id="shipping_pincode"
                        value={formData.shipping_pincode}
                        onChange={(e) => handleChange('shipping_pincode', e.target.value)}
                        placeholder="000000"
                        maxLength={6}
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Banking Tab */}
          <TabsContent value="banking">
            <Card>
              <CardHeader>
                <CardTitle>Banking Details (for Refunds)</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="bank_name">Bank Name</Label>
                    <Input
                      id="bank_name"
                      value={formData.bank_name}
                      onChange={(e) => handleChange('bank_name', e.target.value)}
                      placeholder="Bank name"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="bank_branch">Branch</Label>
                    <Input
                      id="bank_branch"
                      value={formData.bank_branch}
                      onChange={(e) => handleChange('bank_branch', e.target.value)}
                      placeholder="Branch name"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="bank_account_number">Account Number</Label>
                    <Input
                      id="bank_account_number"
                      value={formData.bank_account_number}
                      onChange={(e) => handleChange('bank_account_number', e.target.value)}
                      placeholder="Bank account number"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="bank_ifsc_code">IFSC Code</Label>
                    <Input
                      id="bank_ifsc_code"
                      value={formData.bank_ifsc_code}
                      onChange={(e) => handleChange('bank_ifsc_code', e.target.value.toUpperCase())}
                      placeholder="XXXX0000000"
                      maxLength={11}
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="payment_mode_preference">Preferred Payment Mode</Label>
                  <Select
                    value={formData.payment_mode_preference}
                    onValueChange={(value) => handleChange('payment_mode_preference', value)}
                  >
                    <SelectTrigger className="w-[250px]">
                      <SelectValue placeholder="Select preference" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="NEFT">NEFT</SelectItem>
                      <SelectItem value="RTGS">RTGS</SelectItem>
                      <SelectItem value="CHEQUE">Cheque</SelectItem>
                      <SelectItem value="UPI">UPI</SelectItem>
                      <SelectItem value="BANK_TRANSFER">Bank Transfer</SelectItem>
                      <SelectItem value="CASH">Cash</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Financial Settings Tab */}
          <TabsContent value="financial">
            <Card>
              <CardHeader>
                <CardTitle>Financial Settings</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="control_account_id">Control Account (Receivables)</Label>
                    <Select
                      value={formData.control_account_id}
                      onValueChange={(value) => handleChange('control_account_id', value)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select account" />
                      </SelectTrigger>
                      <SelectContent>
                        {accounts
                          .filter((a) => a.code.startsWith('1')) // Asset accounts
                          .map((account) => (
                            <SelectItem key={account.id} value={account.id}>
                              {account.code} - {account.name}
                            </SelectItem>
                          ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="revenue_account_id">Default Revenue Account</Label>
                    <Select
                      value={formData.revenue_account_id}
                      onValueChange={(value) => handleChange('revenue_account_id', value)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select account" />
                      </SelectTrigger>
                      <SelectContent>
                        {accounts
                          .filter((a) => a.code.startsWith('3')) // Income accounts
                          .map((account) => (
                            <SelectItem key={account.id} value={account.id}>
                              {account.code} - {account.name}
                            </SelectItem>
                          ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                  <div className="space-y-2">
                    <Label htmlFor="payment_terms_id">Payment Terms</Label>
                    <Select
                      value={formData.payment_terms_id}
                      onValueChange={(value) => handleChange('payment_terms_id', value)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select terms" />
                      </SelectTrigger>
                      <SelectContent>
                        {paymentTerms.map((term) => (
                          <SelectItem key={term.id} value={term.id}>
                            {term.code} - {term.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="credit_days">Credit Days</Label>
                    <Input
                      id="credit_days"
                      type="number"
                      value={formData.credit_days}
                      onChange={(e) => handleChange('credit_days', e.target.value)}
                      placeholder="30"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="credit_limit">Credit Limit</Label>
                    <Input
                      id="credit_limit"
                      type="number"
                      step="0.01"
                      value={formData.credit_limit}
                      onChange={(e) => handleChange('credit_limit', e.target.value)}
                      placeholder="0.00"
                    />
                  </div>
                </div>

                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="credit_limit_enabled"
                    checked={formData.credit_limit_enabled}
                    onCheckedChange={(checked) =>
                      handleChange('credit_limit_enabled', checked === true)
                    }
                  />
                  <Label htmlFor="credit_limit_enabled">Enable Credit Limit Enforcement</Label>
                </div>

                <div className="border-t pt-4">
                  <h4 className="font-medium mb-3">Opening Balance</h4>
                  <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                    <div className="space-y-2">
                      <Label htmlFor="opening_balance">Amount</Label>
                      <Input
                        id="opening_balance"
                        type="number"
                        step="0.01"
                        value={formData.opening_balance}
                        onChange={(e) => handleChange('opening_balance', e.target.value)}
                        placeholder="0.00"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="opening_balance_type">Type</Label>
                      <Select
                        value={formData.opening_balance_type}
                        onValueChange={(value) => handleChange('opening_balance_type', value)}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select type" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="DR">Debit (They Owe Us)</SelectItem>
                          <SelectItem value="CR">Credit (Advance Received)</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="currency_code">Currency</Label>
                      <Input
                        id="currency_code"
                        value={formData.currency_code}
                        onChange={(e) => handleChange('currency_code', e.target.value.toUpperCase())}
                        placeholder="INR"
                        maxLength={3}
                      />
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Form Actions */}
        <div className="flex items-center justify-end gap-4 pt-6">
          <Button
            type="button"
            variant="outline"
            onClick={() => navigate('/admin/ap-ar/customers')}
          >
            Cancel
          </Button>
          <Button type="submit" disabled={saving}>
            {saving ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Save className="mr-2 h-4 w-4" />
                {isEditMode ? 'Update Customer' : 'Create Customer'}
              </>
            )}
          </Button>
        </div>
      </form>
    </div>
  );
}
