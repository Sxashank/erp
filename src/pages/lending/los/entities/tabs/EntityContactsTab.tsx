/**
 * Entity Contacts Tab
 * Inline management of entity contacts (NO MODALS)
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
import type { EntityContact } from '@/types/lending';

const CONTACT_TYPES = [
  { value: 'DIRECTOR', label: 'Director' },
  { value: 'PROMOTER', label: 'Promoter' },
  { value: 'KEY_PERSON', label: 'Key Management Person' },
  { value: 'AUTHORIZED_SIGNATORY', label: 'Authorized Signatory' },
  { value: 'CONTACT_PERSON', label: 'Contact Person' },
];

const contactSchema = z.object({
  contact_type: z.enum(['DIRECTOR', 'PROMOTER', 'KEY_PERSON', 'AUTHORIZED_SIGNATORY', 'CONTACT_PERSON']),
  name: z.string().min(2, 'Name must be at least 2 characters'),
  designation: z.string().optional(),
  email: z.string().email('Invalid email').optional().or(z.literal('')),
  phone: z.string().regex(/^[6-9]\d{9}$/, 'Invalid phone number').optional().or(z.literal('')),
  din: z.string().regex(/^\d{8}$/, 'DIN must be 8 digits').optional().or(z.literal('')),
  is_primary: z.boolean().default(false),
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

  const form = useForm<ContactFormData>({
    resolver: zodResolver(contactSchema) as any,
    defaultValues: {
      contact_type: 'CONTACT_PERSON',
      name: '',
      designation: '',
      email: '',
      phone: '',
      din: '',
      is_primary: false,
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
    } catch (error) {
      console.error('Failed to load contacts:', error);
    } finally {
      setLoading(false);
    }
  };

  // Start adding new contact
  const handleAddNew = () => {
    form.reset({
      contact_type: 'CONTACT_PERSON',
      name: '',
      designation: '',
      email: '',
      phone: '',
      din: '',
      is_primary: false,
    });
    setIsAdding(true);
    setEditingId(null);
  };

  // Start editing existing contact
  const handleEdit = (contact: EntityContact) => {
    form.reset({
      contact_type: contact.contact_type as ContactFormData['contact_type'],
      name: contact.name,
      designation: contact.designation || '',
      email: contact.email || '',
      phone: contact.phone || '',
      din: contact.din || '',
      is_primary: contact.is_primary,
    });
    setEditingId(contact.contact_id);
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
        await entityApi.updateEntityContact(entityId, editingId, data as any);
      } else {
        // Add new
        await entityApi.addEntityContact(entityId, data as any);
      }
      await loadContacts();
      handleCancel();
    } catch (error) {
      console.error('Failed to save contact:', error);
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
    } catch (error) {
      console.error('Failed to delete contact:', error);
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
          <CardTitle>Contacts</CardTitle>
          <CardDescription>
            Directors, key persons, and authorized signatories
          </CardDescription>
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
          <div className="mb-6 p-4 border rounded-lg bg-gray-50">
            <h4 className="font-medium mb-4">
              {editingId ? 'Edit Contact' : 'Add New Contact'}
            </h4>
            <Form {...form}>
              <form onSubmit={form.handleSubmit(handleSave as any)} className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <FormField
                    control={form.control}
                    name="contact_type"
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
                            {CONTACT_TYPES.map((type) => (
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
                  name="is_primary"
                  render={({ field }) => (
                    <FormItem className="flex items-center space-x-2 space-y-0">
                      <FormControl>
                        <Checkbox
                          checked={field.value}
                          onCheckedChange={field.onChange}
                        />
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
          <p className="text-center py-8 text-gray-500">
            No contacts added yet. Click "Add Contact" to add one.
          </p>
        ) : (
          <div className="space-y-3">
            {contacts.map((contact) => (
              <div
                key={contact.contact_id}
                className={`flex items-start justify-between p-4 border rounded-lg ${
                  editingId === contact.contact_id ? 'hidden' : ''
                }`}
              >
                <div>
                  <div className="flex items-center gap-2">
                    <p className="font-medium">{contact.name}</p>
                    <Badge variant="outline">
                      {CONTACT_TYPES.find(t => t.value === contact.contact_type)?.label || contact.contact_type}
                    </Badge>
                    {contact.is_primary && <Badge>Primary</Badge>}
                  </div>
                  {contact.designation && (
                    <p className="text-sm text-gray-500">{contact.designation}</p>
                  )}
                  <div className="mt-2 flex gap-4 text-sm text-gray-600">
                    {contact.email && <span>{contact.email}</span>}
                    {contact.phone && <span>{contact.phone}</span>}
                  </div>
                  {contact.din && (
                    <p className="text-xs text-gray-400 mt-1">DIN: {contact.din}</p>
                  )}
                </div>
                <div className="flex gap-1">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleEdit(contact)}
                  >
                    <Edit className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleDelete(contact.contact_id)}
                  >
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
