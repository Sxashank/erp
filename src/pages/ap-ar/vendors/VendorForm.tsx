import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, Save, Loader2 } from 'lucide-react';

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
  vendorsApi,
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

export function VendorForm() {
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
    vendor_type: 'SUPPLIER',
    organization_id: '',

    // Tax & Compliance
    pan: '',
    gstin: '',
    gst_registration_type: '',
    msme_registered: false,
    msme_number: '',
    tds_applicable: false,
    tds_section_id: '',
    tds_rate_override: '',

    // Contact & Address
    contact_person: '',
    email: '',
    phone: '',
    mobile: '',
    address_line1: '',
    address_line2: '',
    city: '',
    state_code: '',
    pincode: '',
    country: 'India',

    // Banking Details
    bank_name: '',
    bank_account_number: '',
    bank_ifsc_code: '',
    bank_branch: '',
    payment_mode_preference: '',

    // Financial Settings
    control_account_id: '',
    expense_account_id: '',
    payment_terms_id: '',
    credit_days: '30',
    credit_limit: '',
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
      loadVendor(id);
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

      // Generate code for new vendor
      if (!isEditMode) {
        const codeRes = await vendorsApi.generateCode({ organization_id: orgId });
        setFormData((prev) => ({ ...prev, code: codeRes.data.code }));
      }
    } catch (error) {
      console.error('Failed to load organization data:', error);
    }
  };

  const loadVendor = async (vendorId: string) => {
    setLoading(true);
    try {
      const response = await vendorsApi.get(vendorId);
      const vendor = response.data;
      setFormData({
        code: vendor.code || '',
        name: vendor.name || '',
        display_name: vendor.display_name || '',
        vendor_type: vendor.vendor_type || 'SUPPLIER',
        organization_id: vendor.organization_id || '',

        pan: vendor.pan || '',
        gstin: vendor.gstin || '',
        gst_registration_type: vendor.gst_registration_type || '',
        msme_registered: vendor.msme_registered || false,
        msme_number: vendor.msme_number || '',
        tds_applicable: vendor.tds_applicable || false,
        tds_section_id: vendor.tds_section_id || '',
        tds_rate_override: vendor.tds_rate_override?.toString() || '',

        contact_person: vendor.contact_person || '',
        email: vendor.email || '',
        phone: vendor.phone || '',
        mobile: vendor.mobile || '',
        address_line1: vendor.address_line1 || '',
        address_line2: vendor.address_line2 || '',
        city: vendor.city || '',
        state_code: vendor.state_code || '',
        pincode: vendor.pincode || '',
        country: vendor.country || 'India',

        bank_name: vendor.bank_name || '',
        bank_account_number: vendor.bank_account_number || '',
        bank_ifsc_code: vendor.bank_ifsc_code || '',
        bank_branch: vendor.bank_branch || '',
        payment_mode_preference: vendor.payment_mode_preference || '',

        control_account_id: vendor.control_account_id || '',
        expense_account_id: vendor.expense_account_id || '',
        payment_terms_id: vendor.payment_terms_id || '',
        credit_days: vendor.credit_days?.toString() || '30',
        credit_limit: vendor.credit_limit?.toString() || '',
        currency_code: vendor.currency_code || 'INR',

        opening_balance: vendor.opening_balance?.toString() || '0',
        opening_balance_type: vendor.opening_balance_type || '',

        remarks: vendor.remarks || '',
        is_active: vendor.is_active ?? true,
      });
    } catch (error) {
      console.error('Failed to load vendor:', error);
      toast({
        title: 'Error',
        description: 'Failed to load vendor details',
        variant: 'destructive',
      });
      navigate('/admin/ap-ar/vendors');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (field: string, value: any) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
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
        description: 'Vendor code is required',
        variant: 'destructive',
      });
      return;
    }
    if (!formData.name.trim()) {
      toast({
        title: 'Validation Error',
        description: 'Vendor name is required',
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
        tds_rate_override: formData.tds_rate_override ? parseFloat(formData.tds_rate_override) : null,
        tds_section_id: formData.tds_section_id || null,
        control_account_id: formData.control_account_id || null,
        expense_account_id: formData.expense_account_id || null,
        payment_terms_id: formData.payment_terms_id || null,
        gst_registration_type: formData.gst_registration_type || null,
        opening_balance_type: formData.opening_balance_type || null,
        payment_mode_preference: formData.payment_mode_preference || null,
      };

      if (isEditMode && id) {
        await vendorsApi.update(id, payload);
        toast({
          title: 'Success',
          description: 'Vendor updated successfully',
        });
      } else {
        await vendorsApi.create(payload);
        toast({
          title: 'Success',
          description: 'Vendor created successfully',
        });
      }
      navigate('/admin/ap-ar/vendors');
    } catch (error: any) {
      console.error('Failed to save vendor:', error);
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to save vendor',
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
        title={isEditMode ? 'Edit Vendor' : 'New Vendor'}
        subtitle={
          isEditMode ? 'Update vendor details' : 'Create a new vendor record'
        }
        breadcrumbs={[
          { label: 'Vendors', to: '/admin/ap-ar/vendors' },
          { label: isEditMode ? 'Edit' : 'New' },
        ]}
      />

      <form onSubmit={handleSubmit}>
        <Tabs defaultValue="basic" className="space-y-6">
          <TabsList className="bg-slate-100">
            <TabsTrigger value="basic">Basic Info</TabsTrigger>
            <TabsTrigger value="tax">Tax & Compliance</TabsTrigger>
            <TabsTrigger value="contact">Contact & Address</TabsTrigger>
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
                    <Label htmlFor="code">Vendor Code *</Label>
                    <Input
                      id="code"
                      value={formData.code}
                      onChange={(e) => handleChange('code', e.target.value.toUpperCase())}
                      placeholder="V001"
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
                    <Label htmlFor="vendor_type">Vendor Type *</Label>
                    <Select
                      value={formData.vendor_type}
                      onValueChange={(value) => handleChange('vendor_type', value)}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="SUPPLIER">Supplier</SelectItem>
                        <SelectItem value="CONTRACTOR">Contractor</SelectItem>
                        <SelectItem value="SERVICE_PROVIDER">Service Provider</SelectItem>
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
                </div>

                <div className="border-t pt-4">
                  <h4 className="font-medium mb-3">MSME Details</h4>
                  <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="msme_registered"
                        checked={formData.msme_registered}
                        onCheckedChange={(checked) =>
                          handleChange('msme_registered', checked === true)
                        }
                      />
                      <Label htmlFor="msme_registered">MSME Registered</Label>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="msme_number">MSME/Udyam Number</Label>
                      <Input
                        id="msme_number"
                        value={formData.msme_number}
                        onChange={(e) => handleChange('msme_number', e.target.value.toUpperCase())}
                        placeholder="UDYAM-XX-00-0000000"
                        disabled={!formData.msme_registered}
                      />
                    </div>
                  </div>
                </div>

                <div className="border-t pt-4">
                  <h4 className="font-medium mb-3">TDS Configuration</h4>
                  <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="tds_applicable"
                        checked={formData.tds_applicable}
                        onCheckedChange={(checked) =>
                          handleChange('tds_applicable', checked === true)
                        }
                      />
                      <Label htmlFor="tds_applicable">TDS Applicable</Label>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="tds_section_id">TDS Section</Label>
                      <Select
                        value={formData.tds_section_id}
                        onValueChange={(value) => handleChange('tds_section_id', value)}
                        disabled={!formData.tds_applicable}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select section" />
                        </SelectTrigger>
                        <SelectContent>
                          {tdsSections.map((section) => (
                            <SelectItem key={section.id} value={section.id}>
                              {section.section_code} - {section.description}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="tds_rate_override">TDS Rate Override (%)</Label>
                      <Input
                        id="tds_rate_override"
                        type="number"
                        step="0.01"
                        value={formData.tds_rate_override}
                        onChange={(e) => handleChange('tds_rate_override', e.target.value)}
                        placeholder="Leave empty for default"
                        disabled={!formData.tds_applicable}
                      />
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Contact & Address Tab */}
          <TabsContent value="contact">
            <Card>
              <CardHeader>
                <CardTitle>Contact & Address</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
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
                      placeholder="vendor@example.com"
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

                <div className="border-t pt-4">
                  <h4 className="font-medium mb-3">Address</h4>
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="address_line1">Address Line 1</Label>
                      <Input
                        id="address_line1"
                        value={formData.address_line1}
                        onChange={(e) => handleChange('address_line1', e.target.value)}
                        placeholder="Building, Street"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="address_line2">Address Line 2</Label>
                      <Input
                        id="address_line2"
                        value={formData.address_line2}
                        onChange={(e) => handleChange('address_line2', e.target.value)}
                        placeholder="Area, Landmark"
                      />
                    </div>
                    <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                      <div className="space-y-2">
                        <Label htmlFor="city">City</Label>
                        <Input
                          id="city"
                          value={formData.city}
                          onChange={(e) => handleChange('city', e.target.value)}
                          placeholder="City"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="state_code">State</Label>
                        <Select
                          value={formData.state_code}
                          onValueChange={(value) => handleChange('state_code', value)}
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
                        <Label htmlFor="pincode">Pincode</Label>
                        <Input
                          id="pincode"
                          value={formData.pincode}
                          onChange={(e) => handleChange('pincode', e.target.value)}
                          placeholder="000000"
                          maxLength={6}
                        />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="country">Country</Label>
                      <Input
                        id="country"
                        value={formData.country}
                        onChange={(e) => handleChange('country', e.target.value)}
                        placeholder="Country"
                      />
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Banking Tab */}
          <TabsContent value="banking">
            <Card>
              <CardHeader>
                <CardTitle>Banking Details</CardTitle>
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
                    <Label htmlFor="control_account_id">Control Account (Payables)</Label>
                    <Select
                      value={formData.control_account_id}
                      onValueChange={(value) => handleChange('control_account_id', value)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select account" />
                      </SelectTrigger>
                      <SelectContent>
                        {accounts
                          .filter((a) => a.code.startsWith('2')) // Liability accounts
                          .map((account) => (
                            <SelectItem key={account.id} value={account.id}>
                              {account.code} - {account.name}
                            </SelectItem>
                          ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="expense_account_id">Default Expense Account</Label>
                    <Select
                      value={formData.expense_account_id}
                      onValueChange={(value) => handleChange('expense_account_id', value)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select account" />
                      </SelectTrigger>
                      <SelectContent>
                        {accounts
                          .filter((a) => a.code.startsWith('4') || a.code.startsWith('5')) // Expense accounts
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
                          <SelectItem value="CR">Credit (We Owe)</SelectItem>
                          <SelectItem value="DR">Debit (Advance Paid)</SelectItem>
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
            onClick={() => navigate('/admin/ap-ar/vendors')}
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
                {isEditMode ? 'Update Vendor' : 'Create Vendor'}
              </>
            )}
          </Button>
        </div>
      </form>
    </div>
  );
}
