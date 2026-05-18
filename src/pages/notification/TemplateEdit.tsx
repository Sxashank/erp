/**
 * Edit Notification Template Page
 */

import { zodResolver } from '@hookform/resolvers/zod';
import { ArrowLeft, Save, Eye, Plus, X } from 'lucide-react';
import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { useParams, useNavigate } from 'react-router-dom';
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
import type { NotificationTemplate, NotificationChannel } from '@/types/notification';
import { getErrorMessage } from "@/lib/errorMessage";

const formSchema = z.object({
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

export default function TemplateEdit() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();

  const [template, setTemplate] = useState<NotificationTemplate | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [variables, setVariables] = useState<string[]>([]);
  const [newVariable, setNewVariable] = useState('');

  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
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

  useEffect(() => {
    if (id) {
      loadTemplate();
    }
  }, [id]);

  const loadTemplate = async () => {
    try {
      setLoading(true);
      const data = await templateApi.getTemplate(id!);
      setTemplate(data);
      setVariables(data.variables || []);

      form.reset({
        name: data.name,
        description: data.description || '',
        template_type: data.template_type,
        category: data.category,
        channels: data.channels,
        email_subject: data.email_subject || '',
        email_body_html: data.email_body_html || '',
        email_body_text: data.email_body_text || '',
        sms_body: data.sms_body || '',
        push_title: data.push_title || '',
        push_body: data.push_body || '',
        push_image_url: data.push_image_url || '',
        in_app_title: data.in_app_title || '',
        in_app_message: data.in_app_message || '',
        whatsapp_template_id: data.whatsapp_template_id || '',
        trigger_event: data.trigger_event || '',
        is_active: data.is_active,
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load template',
        variant: 'destructive',
      });
      navigate('/admin/notifications/templates');
    } finally {
      setLoading(false);
    }
  };

  const onSubmit = async (data: FormValues) => {
    try {
      setSaving(true);
      await templateApi.updateTemplate(id!, {
        ...data,
        variables: variables.length > 0 ? variables : undefined,
      } as unknown as Parameters<typeof templateApi.updateTemplate>[1]);
      toast({ title: 'Template updated successfully' });
      navigate('/admin/notifications/templates');
    } catch (error: unknown) {
      toast({
        title: 'Error',
        description: getErrorMessage(error, 'Failed to update template'),
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

  const selectedChannels = form.watch('channels');

  if (loading) {
    return (
      <div className="container mx-auto py-6">
        <div className="text-center py-8">Loading...</div>
      </div>
    );
  }

  if (!template) {
    return (
      <div className="container mx-auto py-6">
        <div className="text-center py-8">Template not found</div>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-6 space-y-6">
      <PageHeader
        title="Edit Template"
        subtitle={template.code}
        breadcrumbs={[
          { label: 'Notifications', to: '/admin/notifications' },
          { label: 'Templates', to: '/admin/notifications/templates' },
          { label: 'Edit' },
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
                  <FormField
                    control={form.control}
                    name="name"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Name</FormLabel>
                        <FormControl>
                          <Input {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="description"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Description</FormLabel>
                        <FormControl>
                          <Textarea {...field} />
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
                          <Select onValueChange={field.onChange} value={field.value}>
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
                          <Select onValueChange={field.onChange} value={field.value}>
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
                              <Input {...field} />
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
                              <Textarea rows={4} {...field} />
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
                              <Input {...field} />
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
                              <Textarea rows={10} {...field} />
                            </FormControl>
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
                              <Textarea rows={4} {...field} />
                            </FormControl>
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
                              <Textarea rows={3} {...field} />
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
                              <Input {...field} />
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
                              <Textarea rows={3} {...field} />
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
                            <FormLabel>Image URL</FormLabel>
                            <FormControl>
                              <Input {...field} />
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
                              <Input {...field} />
                            </FormControl>
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
                          <Input {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <div className="pt-4 border-t">
                    <p className="text-sm text-muted-foreground">
                      Usage count: {template.usage_count}
                    </p>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Variables</CardTitle>
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
                </CardContent>
              </Card>

              <Button type="submit" className="w-full" disabled={saving}>
                <Save className="h-4 w-4 mr-2" />
                {saving ? 'Saving...' : 'Save Changes'}
              </Button>
            </div>
          </div>
        </form>
      </Form>
    </div>
  );
}
