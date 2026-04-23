/**
 * Entity Addresses Tab
 * Inline management of entity addresses (NO MODALS)
 */

import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Plus, Edit, Trash2, X, Check, Loader2 } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
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
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

import { entityApi } from '@/services/lending';
import type { EntityAddress } from '@/types/lending';

const ADDRESS_TYPES = [
  { value: 'REGISTERED', label: 'Registered Office' },
  { value: 'CORRESPONDENCE', label: 'Correspondence' },
  { value: 'CORPORATE', label: 'Corporate Office' },
  { value: 'PLANT', label: 'Plant/Factory' },
  { value: 'WAREHOUSE', label: 'Warehouse' },
  { value: 'OTHER', label: 'Other' },
];

const INDIAN_STATES = [
  'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chhattisgarh',
  'Goa', 'Gujarat', 'Haryana', 'Himachal Pradesh', 'Jharkhand',
  'Karnataka', 'Kerala', 'Madhya Pradesh', 'Maharashtra', 'Manipur',
  'Meghalaya', 'Mizoram', 'Nagaland', 'Odisha', 'Punjab',
  'Rajasthan', 'Sikkim', 'Tamil Nadu', 'Telangana', 'Tripura',
  'Uttar Pradesh', 'Uttarakhand', 'West Bengal',
  'Delhi', 'Chandigarh', 'Puducherry', 'Ladakh', 'Jammu and Kashmir',
  'Andaman and Nicobar Islands', 'Dadra and Nagar Haveli and Daman and Diu', 'Lakshadweep',
];

const addressSchema = z.object({
  address_type: z.enum(['REGISTERED', 'CORRESPONDENCE', 'CORPORATE', 'PLANT', 'WAREHOUSE', 'OTHER']),
  address_line1: z.string().min(5, 'Address must be at least 5 characters'),
  address_line2: z.string().optional(),
  city: z.string().min(2, 'City is required'),
  state: z.string().min(2, 'State is required'),
  pincode: z.string().regex(/^\d{6}$/, 'Pincode must be 6 digits'),
  country: z.string().default('India'),
  is_primary: z.boolean().default(false),
});

type AddressFormData = z.infer<typeof addressSchema>;

interface EntityAddressesTabProps {
  entityId: string;
}

export default function EntityAddressesTab({ entityId }: EntityAddressesTabProps) {
  const [addresses, setAddresses] = useState<EntityAddress[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [isAdding, setIsAdding] = useState(false);
  const [saving, setSaving] = useState(false);

  const form = useForm<AddressFormData>({
    resolver: zodResolver(addressSchema) as any,
    defaultValues: {
      address_type: 'REGISTERED',
      address_line1: '',
      address_line2: '',
      city: '',
      state: '',
      pincode: '',
      country: 'India',
      is_primary: false,
    },
  });

  // Load addresses
  useEffect(() => {
    loadAddresses();
  }, [entityId]);

  const loadAddresses = async () => {
    setLoading(true);
    try {
      const data = await entityApi.getEntityAddresses(entityId);
      setAddresses(data);
    } catch (error) {
      console.error('Failed to load addresses:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddNew = () => {
    form.reset({
      address_type: 'REGISTERED',
      address_line1: '',
      address_line2: '',
      city: '',
      state: '',
      pincode: '',
      country: 'India',
      is_primary: false,
    });
    setIsAdding(true);
    setEditingId(null);
  };

  const handleEdit = (address: EntityAddress) => {
    form.reset({
      address_type: address.address_type as AddressFormData['address_type'],
      address_line1: address.address_line1,
      address_line2: address.address_line2 || '',
      city: address.city,
      state: address.state,
      pincode: address.pincode,
      country: address.country,
      is_primary: address.is_primary,
    });
    setEditingId(address.address_id);
    setIsAdding(false);
  };

  const handleCancel = () => {
    form.reset();
    setEditingId(null);
    setIsAdding(false);
  };

  const handleSave = async (data: AddressFormData) => {
    setSaving(true);
    try {
      if (editingId) {
        await entityApi.updateEntityAddress(entityId, editingId, data as any);
      } else {
        await entityApi.addEntityAddress(entityId, data as any);
      }
      await loadAddresses();
      handleCancel();
    } catch (error) {
      console.error('Failed to save address:', error);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (addressId: string) => {
    if (!confirm('Are you sure you want to delete this address?')) return;
    try {
      await entityApi.deleteEntityAddress(entityId, addressId);
      await loadAddresses();
    } catch (error) {
      console.error('Failed to delete address:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-48">
        <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
      </div>
    );
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle>Addresses</CardTitle>
          <CardDescription>
            Registered, correspondence, and other addresses
          </CardDescription>
        </div>
        {!isAdding && !editingId && (
          <Button onClick={handleAddNew}>
            <Plus className="mr-2 h-4 w-4" />
            Add Address
          </Button>
        )}
      </CardHeader>
      <CardContent>
        {/* Add/Edit Form */}
        {(isAdding || editingId) && (
          <div className="mb-6 p-4 border rounded-lg bg-gray-50">
            <h4 className="font-medium mb-4">
              {editingId ? 'Edit Address' : 'Add New Address'}
            </h4>
            <Form {...form}>
              <form onSubmit={form.handleSubmit(handleSave as any)} className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <FormField
                    control={form.control}
                    name="address_type"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Address Type *</FormLabel>
                        <Select onValueChange={field.onChange} value={field.value}>
                          <FormControl>
                            <SelectTrigger>
                              <SelectValue />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            {ADDRESS_TYPES.map((type) => (
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
                    name="pincode"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Pincode *</FormLabel>
                        <FormControl>
                          <Input placeholder="6-digit pincode" maxLength={6} {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="address_line1"
                    render={({ field }) => (
                      <FormItem className="md:col-span-2">
                        <FormLabel>Address Line 1 *</FormLabel>
                        <FormControl>
                          <Input placeholder="Building, Street, Area" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="address_line2"
                    render={({ field }) => (
                      <FormItem className="md:col-span-2">
                        <FormLabel>Address Line 2</FormLabel>
                        <FormControl>
                          <Input placeholder="Landmark, Additional details" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="city"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>City *</FormLabel>
                        <FormControl>
                          <Input placeholder="City name" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="state"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>State *</FormLabel>
                        <Select onValueChange={field.onChange} value={field.value}>
                          <FormControl>
                            <SelectTrigger>
                              <SelectValue placeholder="Select state" />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            {INDIAN_STATES.map((state) => (
                              <SelectItem key={state} value={state}>
                                {state}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>

                <FormField
                  control={form.control}
                  name="is_primary"
                  render={({ field }) => (
                    <FormItem className="flex items-center space-x-2 space-y-0">
                      <FormControl>
                        <Checkbox
                          checked={field.value}
                          onCheckedChange={field.onChange}
                        />
                      </FormControl>
                      <FormLabel className="font-normal">Primary Address</FormLabel>
                    </FormItem>
                  )}
                />

                <div className="flex gap-2">
                  <Button type="submit" disabled={saving}>
                    {saving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                    <Check className="mr-2 h-4 w-4" />
                    Save
                  </Button>
                  <Button type="button" variant="outline" onClick={handleCancel}>
                    <X className="mr-2 h-4 w-4" />
                    Cancel
                  </Button>
                </div>
              </form>
            </Form>
          </div>
        )}

        {/* Addresses List */}
        {addresses.length === 0 && !isAdding ? (
          <p className="text-center py-8 text-gray-500">
            No addresses added yet. Click "Add Address" to add one.
          </p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {addresses.map((address) => (
              <div
                key={address.address_id}
                className={`p-4 border rounded-lg ${
                  editingId === address.address_id ? 'hidden' : ''
                }`}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-2 mb-2">
                      <Badge variant="outline">
                        {ADDRESS_TYPES.find(t => t.value === address.address_type)?.label || address.address_type}
                      </Badge>
                      {address.is_primary && <Badge>Primary</Badge>}
                    </div>
                    <p className="text-sm">
                      {address.address_line1}
                      {address.address_line2 && <>, {address.address_line2}</>}
                    </p>
                    <p className="text-sm">
                      {address.city}, {address.state} - {address.pincode}
                    </p>
                    <p className="text-sm text-gray-500">{address.country}</p>
                  </div>
                  <div className="flex gap-1">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleEdit(address)}
                    >
                      <Edit className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDelete(address.address_id)}
                    >
                      <Trash2 className="h-4 w-4 text-red-500" />
                    </Button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
