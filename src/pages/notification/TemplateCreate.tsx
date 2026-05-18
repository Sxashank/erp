/**
 * Create Notification Template Page
 */

import { zodResolver } from '@hookform/resolvers/zod';
import { ArrowLeft, Save, Eye, Plus, X } from 'lucide-react';
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate } from 'react-router-dom';
import { z } from 'zod';

import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from '@/components/ui/card';
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
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Textarea } from '@/components/ui/textarea';
import { useToast } from '@/hooks/use-toast';
import { templateApi } from '@/services/notificationApi';
import type { NotificationChannel } from '@/types/notification';
import { NotificationCategory, NotificationTemplateType } from '@/types/notification';
import { getErrorMessage } from "@/lib/errorMessage";

const formSchema = z.object({
  code: z.string().min(1, 'Code is required').max(100),
  name: z.string().min(1, 'Name is required').max(255),
  description: z.string().optional(),
  template_type: z.enum(['transactional', 'marketing', 'system', 'reminder', 'alert']),
  category: z.enum(['system', 'workflow', 'loan', 'payment', 'collection', 'reminder', 'alert', 'announcement', 'marketing']),
  channels: z.array(z.string()).min(1, 'Select at least one channel'),

  email_subject: z.string().optional(),
  email_body_html: z.string().optional(),
  email_body_text: z.string().optional(),

  sms_body: z.string().max(1000).optional(),

  push_title: z.string().max(100).optional(),
  push_body: z.string().max(500).optional(),
  push_image_url: z.string().url().optional().or(z.literal('')),

  in_app_title: z.string().max(255).optional(),
  in_app_message: z.string().optional(),

  whatsapp_template_id: z.string().optional(),

  trigger_event: z.string().optional(),
  is_active: z.boolean(),
});

type FormValues = z.infer<typeof formSchema>;

const CHANNEL_OPTIONS: { value: NotificationChannel; label: string }[] = [
  { value: 'email', label: 'Email' },
  { value: 'sms', label: 'SMS' },
  { value: 'push', label: 'Push Notification' },
  { value: 'in_app', label: 'In-App' },
  { value: 'whatsapp', label: 'WhatsApp' },
];

export default function TemplateCreate() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [saving, setSaving] = useState(false);
  const [variables, setVariables] = useState<string[]>([]);
  const [newVariable, setNewVariable] = useState('');

  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      code: '',
      name: '',
      description: '',
      template_type: 'transactional',
      category: 'system',
      channels: ['in_app'],
      email_subject: '',
      email_body_html: '',
      email_body_text: '',
      sms_body: '',
      push_title: '',
      push_body: '',
      push_image_url: '',
      in_app_title: '',
      in_app_message: '',
      whatsapp_template_id: '',
      trigger_event: '',
      is_active: true,
    },
  });

  const onSubmit = async (data: FormValues) => {
    try {
      setSaving(true);
      await templateApi.createTemplate({
        ...data,
        variables: variables.length > 0 ? variables : undefined,
      } as unknown as Parameters<typeof templateApi.createTemplate>[0]);
      toast({ title: 'Template created successfully' });
      navigate('/admin/notifications/templates');
    } catch (error: unknown) {
      toast({
        title: 'Error',
        description: getErrorMessage(error, 'Failed to create template'),
        variant: 'destructive',
      });
    } finally {
      setSaving(false);
    }
  };

  const addVariable = () => {
    if (newVariable && !variables.includes(newVariable)) {
      setVariables([...variables, newVariable]);
      setNewVariable('');
    }
  };

  const removeVariable = (variable: string) => {
    setVariables(variables.filter((v) => v !== variable));
  };

  const insertVariable = (variable: string, fieldName: string) => {
    const currentValue = (form.getValues(fieldName as keyof FormValues) ?? '') as string;
    form.setValue(fieldName as keyof FormValues, currentValue + `{${variable}}`);
  };

  const selectedChannels = form.watch('channels');

  return (
    <div className="container mx-auto py-6 space-y-6">
      <PageHeader
        title="Create Template"
        subtitle="Create a new notification template"
        breadcrumbs={[
          { label: 'Notifications', to: '/admin/notifications' },
          { label: 'Templates', to: '/admin/notifications/templates' },
          { label: 'New' },
        ]}
      />

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Main Form */}
            <div className="lg:col-span-2 space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Basic Information</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <FormField
                      control={form.control}
                      name="code"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Template Code</FormLabel>
                          <FormControl>
                            <Input placeholder="LOAN_APPROVAL" {...field} />
                          </FormControl>
                          <FormDescription>Unique identifier for this template</FormDescription>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                    <FormField
                      control={form.control}
                      name="name"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Name</FormLabel>
                          <FormControl>
                            <Input placeholder="Loan Approval Notification" {...field} />
                          </FormControl>
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
                          <Textarea placeholder="Describe when this template is used..." {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <div className="grid grid-cols-2 gap-4">
                    <FormField
                      control={form.control}
                      name="template_type"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Template Type</FormLabel>
                          <Select onValueChange={field.onChange} defaultValue={field.value}>
                            <FormControl>
                              <SelectTrigger>
                                <SelectValue />
                              </SelectTrigger>
                            </FormControl>
                            <SelectContent>
                              <SelectItem value="transactional">Transactional</SelectItem>
                              <SelectItem value="marketing">Marketing</SelectItem>
                              <SelectItem value="system">System</SelectItem>
                              <SelectItem value="reminder">Reminder</SelectItem>
                              <SelectItem value="alert">Alert</SelectItem>
                            </SelectContent>
                          </Select>
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
                          <Select onValueChange={field.onChange} defaultValue={field.value}>
                            <FormControl>
                              <SelectTrigger>
                                <SelectValue />
                              </SelectTrigger>
                            </FormControl>
                            <SelectContent>
                              <SelectItem value="system">System</SelectItem>
                              <SelectItem value="workflow">Workflow</SelectItem>
                              <SelectItem value="loan">Loan</SelectItem>
                              <SelectItem value="payment">Payment</SelectItem>
                              <SelectItem value="collection">Collection</SelectItem>
                              <SelectItem value="reminder">Reminder</SelectItem>
                              <SelectItem value="alert">Alert</SelectItem>
                              <SelectItem value="announcement">Announcement</SelectItem>
                              <SelectItem value="marketing">Marketing</SelectItem>
                            </SelectContent>
                          </Select>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>

                  <FormField
                    control={form.control}
                    name="channels"
                    render={() => (
                      <FormItem>
                        <FormLabel>Channels</FormLabel>
                        <div className="flex flex-wrap gap-4">
                          {CHANNEL_OPTIONS.map((channel) => (
                            <FormField
                              key={channel.value}
                              control={form.control}
                              name="channels"
                              render={({ field }) => (
                                <FormItem className="flex items-center space-x-2">
                                  <FormControl>
                                    <Checkbox
                                      checked={field.value?.includes(channel.value)}
                                      onCheckedChange={(checked) => {
                                        return checked
                                          ? field.onChange([...field.value, channel.value])
                                          : field.onChange(
                                              field.value?.filter((v) => v !== channel.value)
                                            );
                                      }}
                                    />
                                  </FormControl>
                                  <FormLabel className="font-normal cursor-pointer">
                                    {channel.label}
                                  </FormLabel>
                                </FormItem>
                              )}
                            />
                          ))}
                        </div>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </CardContent>
              </Card>

              {/* Channel-specific content */}
              <Card>
                <CardHeader>
                  <CardTitle>Channel Content</CardTitle>
                  <CardDescription>Configure content for each notification channel</CardDescription>
                </CardHeader>
                <CardContent>
                  <Tabs defaultValue="in_app">
                    <TabsList>
                      {selectedChannels.includes('in_app') && <TabsTrigger value="in_app">In-App</TabsTrigger>}
                      {selectedChannels.includes('email') && <TabsTrigger value="email">Email</TabsTrigger>}
                      {selectedChannels.includes('sms') && <TabsTrigger value="sms">SMS</TabsTrigger>}
                      {selectedChannels.includes('push') && <TabsTrigger value="push">Push</TabsTrigger>}
                      {selectedChannels.includes('whatsapp') && <TabsTrigger value="whatsapp">WhatsApp</TabsTrigger>}
                    </TabsList>

                    <TabsContent value="in_app" className="space-y-4 mt-4">
                      <FormField
                        control={form.control}
                        name="in_app_title"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Title</FormLabel>
                            <FormControl>
                              <Input placeholder="Notification title" {...field} />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                      <FormField
                        control={form.control}
                        name="in_app_message"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Message</FormLabel>
                            <FormControl>
                              <Textarea placeholder="Notification message..." rows={4} {...field} />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                    </TabsContent>

                    <TabsContent value="email" className="space-y-4 mt-4">
                      <FormField
                        control={form.control}
                        name="email_subject"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Subject</FormLabel>
                            <FormControl>
                              <Input placeholder="Email subject" {...field} />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                      <FormField
                        control={form.control}
                        name="email_body_html"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>HTML Body</FormLabel>
                            <FormControl>
                              <Textarea placeholder="<html>...</html>" rows={10} {...field} />
                            </FormControl>
                            <FormDescription>HTML content for the email</FormDescription>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                      <FormField
                        control={form.control}
                        name="email_body_text"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Plain Text Body</FormLabel>
                            <FormControl>
                              <Textarea placeholder="Plain text fallback..." rows={4} {...field} />
                            </FormControl>
                            <FormDescription>Fallback for email clients that don't support HTML</FormDescription>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                    </TabsContent>

                    <TabsContent value="sms" className="space-y-4 mt-4">
                      <FormField
                        control={form.control}
                        name="sms_body"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>SMS Body</FormLabel>
                            <FormControl>
                              <Textarea placeholder="SMS message (max 160 chars for single SMS)" rows={3} {...field} />
                            </FormControl>
                            <FormDescription>
                              Character count: {field.value?.length || 0}/160
                            </FormDescription>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                    </TabsContent>

                    <TabsContent value="push" className="space-y-4 mt-4">
                      <FormField
                        control={form.control}
                        name="push_title"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Title</FormLabel>
                            <FormControl>
                              <Input placeholder="Push notification title" {...field} />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                      <FormField
                        control={form.control}
                        name="push_body"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Body</FormLabel>
                            <FormControl>
                              <Textarea placeholder="Push notification body" rows={3} {...field} />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                      <FormField
                        control={form.control}
                        name="push_image_url"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Image URL (optional)</FormLabel>
                            <FormControl>
                              <Input placeholder="https://..." {...field} />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                    </TabsContent>

                    <TabsContent value="whatsapp" className="space-y-4 mt-4">
                      <FormField
                        control={form.control}
                        name="whatsapp_template_id"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>WhatsApp Template ID</FormLabel>
                            <FormControl>
                              <Input placeholder="Approved WhatsApp template ID" {...field} />
                            </FormControl>
                            <FormDescription>
                              Use pre-approved WhatsApp Business template
                            </FormDescription>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                    </TabsContent>
                  </Tabs>
                </CardContent>
              </Card>
            </div>

            {/* Sidebar */}
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Settings</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <FormField
                    control={form.control}
                    name="is_active"
                    render={({ field }) => (
                      <FormItem className="flex items-center justify-between">
                        <FormLabel>Active</FormLabel>
                        <FormControl>
                          <Switch checked={field.value} onCheckedChange={field.onChange} />
                        </FormControl>
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="trigger_event"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Trigger Event</FormLabel>
                        <FormControl>
                          <Input placeholder="loan.approved" {...field} />
                        </FormControl>
                        <FormDescription>Event that triggers this notification</FormDescription>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Variables</CardTitle>
                  <CardDescription>Template placeholders for dynamic content</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex gap-2">
                    <Input
                      placeholder="variable_name"
                      value={newVariable}
                      onChange={(e) => setNewVariable(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addVariable())}
                    />
                    <Button type="button" variant="outline" size="sm" onClick={addVariable}>
                      <Plus className="h-4 w-4" />
                    </Button>
                  </div>

                  <div className="flex flex-wrap gap-2">
                    {variables.map((variable) => (
                      <Badge key={variable} variant="secondary" className="flex items-center gap-1">
                        {`{${variable}}`}
                        <button
                          type="button"
                          onClick={() => removeVariable(variable)}
                          className="ml-1 hover:text-destructive"
                        >
                          <X className="h-3 w-3" />
                        </button>
                      </Badge>
                    ))}
                  </div>

                  {variables.length > 0 && (
                    <p className="text-xs text-muted-foreground">
                      Click on a variable to insert it into the content fields
                    </p>
                  )}
                </CardContent>
              </Card>

              <div className="flex gap-2">
                <Button type="submit" className="flex-1" disabled={saving}>
                  <Save className="h-4 w-4 mr-2" />
                  {saving ? 'Creating...' : 'Create Template'}
                </Button>
              </div>
            </div>
          </div>
        </form>
      </Form>
    </div>
  );
}
