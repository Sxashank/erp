/**
 * Entity Addresses Tab
 * Inline management of entity addresses (NO MODALS)
 */

import { zodResolver } from '@hookform/resolvers/zod';
import { Plus, Edit, Trash2, X, Check, Loader2 } from 'lucide-react';
import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
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
import { entityApi } from '@/services/lending';
import type { EntityAddress } from '@/types/lending';

const ADDRESS_TYPES = [
  { value: 'REGISTERED', label: 'Registered Office' },
  { value: 'CORRESPONDENCE', label: 'Correspondence' },
  { value: 'BRANCH', label: 'Branch Office' },
  { value: 'PLANT', label: 'Plant/Factory' },
  { value: 'WAREHOUSE', label: 'Warehouse' },
  { value: 'PROJECT_SITE', label: 'Project Site' },
];

const INDIAN_STATES = [
  { code: '27', name: 'Maharashtra' },
  { code: '07', name: 'Delhi' },
  { code: '29', name: 'Karnataka' },
  { code: '24', name: 'Gujarat' },
  { code: '33', name: 'Tamil Nadu' },
  { code: '36', name: 'Telangana' },
  { code: '09', name: 'Uttar Pradesh' },
  { code: '19', name: 'West Bengal' },
];

const addressSchema = z.object({
  addressType: z.enum([
    'REGISTERED',
    'CORRESPONDENCE',
    'BRANCH',
    'PLANT',
    'WAREHOUSE',
    'PROJECT_SITE',
  ]),
  addressLine1: z.string().min(5, 'Address must be at least 5 characters'),
  addressLine2: z.string().optional(),
  city: z.string().min(2, 'City is required'),
  state: z.string().min(2, 'State is required'),
  stateCode: z.string().length(2, 'State code is required'),
  pincode: z.string().regex(/^\d{6}$/, 'Pincode must be 6 digits'),
  country: z.string(),
  isPrimary: z.boolean(),
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
    resolver: zodResolver(addressSchema),
    defaultValues: {
      addressType: 'REGISTERED',
      addressLine1: '',
      addressLine2: '',
      city: '',
      state: '',
      stateCode: '',
      pincode: '',
      country: 'India',
      isPrimary: false,
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
    } catch {
    } finally {
      setLoading(false);
    }
  };

  const handleAddNew = () => {
    form.reset({
      addressType: 'REGISTERED',
      addressLine1: '',
      addressLine2: '',
      city: '',
      state: '',
      stateCode: '',
      pincode: '',
      country: 'India',
      isPrimary: false,
    });
    setIsAdding(true);
    setEditingId(null);
  };

  const handleEdit = (address: EntityAddress) => {
    form.reset({
      addressType: address.addressType as AddressFormData['addressType'],
      addressLine1: address.addressLine1,
      addressLine2: address.addressLine2 || '',
      city: address.city,
      state: address.state,
      stateCode: address.stateCode || '',
      pincode: address.pincode,
      country: address.country,
      isPrimary: address.isPrimary,
    });
    setEditingId(address.id);
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
        await entityApi.updateEntityAddress(entityId, editingId, data);
      } else {
        await entityApi.addEntityAddress(entityId, data);
      }
      await loadAddresses();
      handleCancel();
    } catch {
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (addressId: string) => {
    if (!confirm('Are you sure you want to delete this address?')) return;
    try {
      await entityApi.deleteEntityAddress(entityId, addressId);
      await loadAddresses();
    } catch {}
  };

  if (loading) {
    return (
      <div className="flex h-48 items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
      </div>
    );
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle>Addresses</CardTitle>
          <CardDescription>Registered, correspondence, and other addresses</CardDescription>
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
          <div className="mb-6 rounded-lg border bg-gray-50 p-4">
            <h4 className="mb-4 font-medium">{editingId ? 'Edit Address' : 'Add New Address'}</h4>
            <Form {...form}>
              <form onSubmit={form.handleSubmit(handleSave)} className="space-y-4">
                <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                  <FormField
                    control={form.control}
                    name="addressType"
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
                    name="addressLine1"
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
                    name="addressLine2"
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
                        <Select
                          onValueChange={(value) => {
                            field.onChange(value);
                            form.setValue(
                              'stateCode',
                              INDIAN_STATES.find((state) => state.name === value)?.code ?? '',
                            );
                          }}
                          value={field.value}
                        >
                          <FormControl>
                            <SelectTrigger>
                              <SelectValue placeholder="Select state" />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            {INDIAN_STATES.map((state) => (
                              <SelectItem key={state.code} value={state.name}>
                                {state.name}
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
                  name="isPrimary"
                  render={({ field }) => (
                    <FormItem className="flex items-center space-x-2 space-y-0">
                      <FormControl>
                        <Checkbox checked={field.value} onCheckedChange={field.onChange} />
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
          <p className="py-8 text-center text-gray-500">
            No addresses added yet. Click "Add Address" to add one.
          </p>
        ) : (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            {addresses.map((address) => (
              <div
                key={address.id}
                className={`rounded-lg border p-4 ${editingId === address.id ? 'hidden' : ''}`}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <div className="mb-2 flex items-center gap-2">
                      <Badge variant="outline">
                        {ADDRESS_TYPES.find((t) => t.value === address.addressType)?.label ||
                          address.addressType}
                      </Badge>
                      {address.isPrimary && <Badge>Primary</Badge>}
                    </div>
                    <p className="text-sm">
                      {address.addressLine1}
                      {address.addressLine2 && <>, {address.addressLine2}</>}
                    </p>
                    <p className="text-sm">
                      {address.city}, {address.state} - {address.pincode}
                    </p>
                    <p className="text-sm text-gray-500">{address.country}</p>
                  </div>
                  <div className="flex gap-1">
                    <Button variant="ghost" size="sm" onClick={() => handleEdit(address)}>
                      <Edit className="h-4 w-4" />
                    </Button>
                    <Button variant="ghost" size="sm" onClick={() => handleDelete(address.id)}>
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
