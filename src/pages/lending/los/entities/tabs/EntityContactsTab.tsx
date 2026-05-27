/**
 * Entity Contacts Tab
 * Inline management of entity contacts (NO MODALS)
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
import { masterRowsToOptions, useLendingOptionRows } from '@/hooks/lending/useLendingMasters';
import { entityApi } from '@/services/lending';
import type { EntityContact } from '@/types/lending';

const contactSchema = z.object({
  contactType: z.string().min(1, 'Contact type is required'),
  name: z.string().min(2, 'Name must be at least 2 characters'),
  designation: z.string().optional(),
  email: z.string().email('Invalid email').optional().or(z.literal('')),
  phone: z
    .string()
    .regex(/^[6-9]\d{9}$/, 'Invalid phone number')
    .optional()
    .or(z.literal('')),
  din: z
    .string()
    .regex(/^\d{8}$/, 'DIN must be 8 digits')
    .optional()
    .or(z.literal('')),
  isPrimary: z.boolean(),
});

type ContactFormData = z.infer<typeof contactSchema>;

interface EntityContactsTabProps {
  entityId: string;
}

export default function EntityContactsTab({ entityId }: EntityContactsTabProps) {
  const [contacts, setContacts] = useState<EntityContact[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [isAdding, setIsAdding] = useState(false);
  const [saving, setSaving] = useState(false);
  const contactTypesQuery = useLendingOptionRows('CONTACT_TYPE');
  const contactTypes = masterRowsToOptions(contactTypesQuery.data?.items);

  const form = useForm<ContactFormData>({
    resolver: zodResolver(contactSchema),
    defaultValues: {
      contactType: 'AUTHORIZED_SIGNATORY',
      name: '',
      designation: '',
      email: '',
      phone: '',
      din: '',
      isPrimary: false,
    },
  });

  // Load contacts
  useEffect(() => {
    loadContacts();
  }, [entityId]);

  const loadContacts = async () => {
    setLoading(true);
    try {
      const data = await entityApi.getEntityContacts(entityId);
      setContacts(data);
    } catch {
    } finally {
      setLoading(false);
    }
  };

  // Start adding new contact
  const handleAddNew = () => {
    form.reset({
      contactType: contactTypes[0]?.value ?? 'AUTHORIZED_SIGNATORY',
      name: '',
      designation: '',
      email: '',
      phone: '',
      din: '',
      isPrimary: false,
    });
    setIsAdding(true);
    setEditingId(null);
  };

  // Start editing existing contact
  const handleEdit = (contact: EntityContact) => {
    form.reset({
      contactType: contact.contactType,
      name: contact.name,
      designation: contact.designation || '',
      email: contact.email || '',
      phone: contact.phone || '',
      din: contact.din || '',
      isPrimary: contact.isPrimary,
    });
    setEditingId(contact.id);
    setIsAdding(false);
  };

  // Cancel editing/adding
  const handleCancel = () => {
    form.reset();
    setEditingId(null);
    setIsAdding(false);
  };

  // Save contact
  const handleSave = async (data: ContactFormData) => {
    setSaving(true);
    try {
      if (editingId) {
        // Update existing
        await entityApi.updateEntityContact(entityId, editingId, data);
      } else {
        // Add new
        await entityApi.addEntityContact(entityId, data);
      }
      await loadContacts();
      handleCancel();
    } catch {
    } finally {
      setSaving(false);
    }
  };

  // Delete contact
  const handleDelete = async (contactId: string) => {
    if (!confirm('Are you sure you want to delete this contact?')) return;
    try {
      await entityApi.deleteEntityContact(entityId, contactId);
      await loadContacts();
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
          <CardTitle>Contacts</CardTitle>
          <CardDescription>Directors, key persons, and authorized signatories</CardDescription>
        </div>
        {!isAdding && !editingId && (
          <Button onClick={handleAddNew}>
            <Plus className="mr-2 h-4 w-4" />
            Add Contact
          </Button>
        )}
      </CardHeader>
      <CardContent>
        {/* Add/Edit Form */}
        {(isAdding || editingId) && (
          <div className="mb-6 rounded-lg border bg-gray-50 p-4">
            <h4 className="mb-4 font-medium">{editingId ? 'Edit Contact' : 'Add New Contact'}</h4>
            <Form {...form}>
              <form onSubmit={form.handleSubmit(handleSave)} className="space-y-4">
                <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                  <FormField
                    control={form.control}
                    name="contactType"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Contact Type *</FormLabel>
                        <Select onValueChange={field.onChange} value={field.value}>
                          <FormControl>
                            <SelectTrigger>
                              <SelectValue />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            {contactTypes.map((type) => (
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
                    name="name"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Full Name *</FormLabel>
                        <FormControl>
                          <Input placeholder="Enter full name" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="designation"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Designation</FormLabel>
                        <FormControl>
                          <Input placeholder="e.g., Managing Director" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="email"
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
                    name="phone"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Phone</FormLabel>
                        <FormControl>
                          <Input placeholder="10-digit mobile" maxLength={10} {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="din"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>DIN</FormLabel>
                        <FormControl>
                          <Input placeholder="8-digit DIN" maxLength={8} {...field} />
                        </FormControl>
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
                      <FormLabel className="font-normal">Primary Contact</FormLabel>
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

        {/* Contacts List */}
        {contacts.length === 0 && !isAdding ? (
          <p className="py-8 text-center text-gray-500">
            No contacts added yet. Click "Add Contact" to add one.
          </p>
        ) : (
          <div className="space-y-3">
            {contacts.map((contact) => (
              <div
                key={contact.id}
                className={`flex items-start justify-between rounded-lg border p-4 ${
                  editingId === contact.id ? 'hidden' : ''
                }`}
              >
                <div>
                  <div className="flex items-center gap-2">
                    <p className="font-medium">{contact.name}</p>
                    <Badge variant="outline">
                      {contactTypes.find((t) => t.value === contact.contactType)?.label ||
                        contact.contactType}
                    </Badge>
                    {contact.isPrimary && <Badge>Primary</Badge>}
                  </div>
                  {contact.designation && (
                    <p className="text-sm text-gray-500">{contact.designation}</p>
                  )}
                  <div className="mt-2 flex gap-4 text-sm text-gray-600">
                    {contact.email && <span>{contact.email}</span>}
                    {contact.phone && <span>{contact.phone}</span>}
                  </div>
                  {contact.din && <p className="mt-1 text-xs text-gray-400">DIN: {contact.din}</p>}
                </div>
                <div className="flex gap-1">
                  <Button variant="ghost" size="sm" onClick={() => handleEdit(contact)}>
                    <Edit className="h-4 w-4" />
                  </Button>
                  <Button variant="ghost" size="sm" onClick={() => handleDelete(contact.id)}>
                    <Trash2 className="h-4 w-4 text-red-500" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
