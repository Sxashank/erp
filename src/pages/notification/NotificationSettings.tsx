/**
 * Notification Settings Page - User preferences for notifications
 */

import { ArrowLeft, Bell, Mail, MessageSquare, Smartphone, Save } from 'lucide-react';
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

import { PageHeader } from '@/components/common/PageHeader';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Separator } from '@/components/ui/separator';
import { Switch } from '@/components/ui/switch';
import { useToast } from '@/hooks/use-toast';
import { notificationApi } from '@/services/notificationApi';
import type { NotificationCategory } from '@/types/notification';
import { NotificationPreference } from '@/types/notification';

const CATEGORIES: { value: NotificationCategory; label: string; description: string }[] = [
  { value: 'system', label: 'System', description: 'System-wide notifications and updates' },
  { value: 'workflow', label: 'Workflow', description: 'Approval requests and workflow updates' },
  { value: 'loan', label: 'Loan', description: 'Loan application and disbursement updates' },
  { value: 'payment', label: 'Payment', description: 'Payment confirmations and receipts' },
  { value: 'collection', label: 'Collection', description: 'Collection reminders and follow-ups' },
  { value: 'reminder', label: 'Reminder', description: 'General reminders and due date alerts' },
  { value: 'alert', label: 'Alert', description: 'Important alerts and warnings' },
  { value: 'announcement', label: 'Announcement', description: 'Company announcements and news' },
];

interface PreferenceState {
  email_enabled: boolean;
  sms_enabled: boolean;
  push_enabled: boolean;
  in_app_enabled: boolean;
  whatsapp_enabled: boolean;
  digest_mode: boolean;
  digest_frequency?: string;
  quiet_hours_start?: string;
  quiet_hours_end?: string;
}

const DEFAULT_PREFERENCE: PreferenceState = {
  email_enabled: true,
  sms_enabled: false,
  push_enabled: true,
  in_app_enabled: true,
  whatsapp_enabled: false,
  digest_mode: false,
};

export default function NotificationSettings() {
  const navigate = useNavigate();
  const { toast } = useToast();

  const [preferences, setPreferences] = useState<Record<string, PreferenceState>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [quietHoursStart, setQuietHoursStart] = useState('22:00');
  const [quietHoursEnd, setQuietHoursEnd] = useState('07:00');

  useEffect(() => {
    loadPreferences();
  }, []);

  const loadPreferences = async () => {
    try {
      setLoading(true);
      const data = await notificationApi.getPreferences();

      // Convert to map by category
      const prefMap: Record<string, PreferenceState> = {};
      data.forEach((pref) => {
        prefMap[pref.category] = {
          email_enabled: pref.email_enabled,
          sms_enabled: pref.sms_enabled,
          push_enabled: pref.push_enabled,
          in_app_enabled: pref.in_app_enabled,
          whatsapp_enabled: pref.whatsapp_enabled,
          digest_mode: pref.digest_mode,
          digest_frequency: pref.digest_frequency,
          quiet_hours_start: pref.quiet_hours_start,
          quiet_hours_end: pref.quiet_hours_end,
        };
        if (pref.quiet_hours_start) setQuietHoursStart(pref.quiet_hours_start);
        if (pref.quiet_hours_end) setQuietHoursEnd(pref.quiet_hours_end);
      });

      // Set defaults for missing categories
      CATEGORIES.forEach((cat) => {
        if (!prefMap[cat.value]) {
          prefMap[cat.value] = { ...DEFAULT_PREFERENCE };
        }
      });

      setPreferences(prefMap);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load preferences',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const updatePreference = (category: NotificationCategory, field: keyof PreferenceState, value: boolean | string) => {
    setPreferences((prev) => ({
      ...prev,
      [category]: {
        ...prev[category],
        [field]: value,
      },
    }));
  };

  const handleSave = async () => {
    try {
      setSaving(true);

      // Save each category preference
      for (const [category, pref] of Object.entries(preferences)) {
        await notificationApi.updatePreference(category as NotificationCategory, {
          ...pref,
          quiet_hours_start: quietHoursStart,
          quiet_hours_end: quietHoursEnd,
        });
      }

      toast({ title: 'Preferences saved successfully' });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to save preferences',
        variant: 'destructive',
      });
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto py-6">
        <div className="text-center py-8">Loading...</div>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-6 space-y-6">
      <PageHeader
        title="Notification Settings"
        subtitle="Manage your notification preferences"
        breadcrumbs={[
          { label: 'Notifications', to: '/admin/notifications' },
          { label: 'Settings' },
        ]}
        actions={
          <Button onClick={handleSave} disabled={saving}>
            <Save className="h-4 w-4 mr-2" />
            {saving ? 'Saving...' : 'Save Preferences'}
          </Button>
        }
      />

      {/* Global Settings */}
      <Card>
        <CardHeader>
          <CardTitle>Global Settings</CardTitle>
          <CardDescription>Configure quiet hours and digest preferences</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <Label>Quiet Hours Start</Label>
              <Input
                type="time"
                value={quietHoursStart}
                onChange={(e) => setQuietHoursStart(e.target.value)}
              />
              <p className="text-xs text-muted-foreground">
                No notifications during quiet hours
              </p>
            </div>
            <div className="space-y-2">
              <Label>Quiet Hours End</Label>
              <Input
                type="time"
                value={quietHoursEnd}
                onChange={(e) => setQuietHoursEnd(e.target.value)}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Category Preferences */}
      <Card>
        <CardHeader>
          <CardTitle>Category Preferences</CardTitle>
          <CardDescription>Choose how you want to receive notifications for each category</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            {CATEGORIES.map((category, index) => (
              <div key={category.value}>
                {index > 0 && <Separator className="mb-6" />}
                <div className="space-y-4">
                  <div>
                    <h4 className="font-medium">{category.label}</h4>
                    <p className="text-sm text-muted-foreground">{category.description}</p>
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                    <div className="flex items-center justify-between space-x-2">
                      <div className="flex items-center space-x-2">
                        <Bell className="h-4 w-4 text-muted-foreground" />
                        <Label htmlFor={`${category.value}-in_app`} className="text-sm">
                          In-App
                        </Label>
                      </div>
                      <Switch
                        id={`${category.value}-in_app`}
                        checked={preferences[category.value]?.in_app_enabled ?? true}
                        onCheckedChange={(checked) =>
                          updatePreference(category.value, 'in_app_enabled', checked)
                        }
                      />
                    </div>

                    <div className="flex items-center justify-between space-x-2">
                      <div className="flex items-center space-x-2">
                        <Mail className="h-4 w-4 text-muted-foreground" />
                        <Label htmlFor={`${category.value}-email`} className="text-sm">
                          Email
                        </Label>
                      </div>
                      <Switch
                        id={`${category.value}-email`}
                        checked={preferences[category.value]?.email_enabled ?? true}
                        onCheckedChange={(checked) =>
                          updatePreference(category.value, 'email_enabled', checked)
                        }
                      />
                    </div>

                    <div className="flex items-center justify-between space-x-2">
                      <div className="flex items-center space-x-2">
                        <MessageSquare className="h-4 w-4 text-muted-foreground" />
                        <Label htmlFor={`${category.value}-sms`} className="text-sm">
                          SMS
                        </Label>
                      </div>
                      <Switch
                        id={`${category.value}-sms`}
                        checked={preferences[category.value]?.sms_enabled ?? false}
                        onCheckedChange={(checked) =>
                          updatePreference(category.value, 'sms_enabled', checked)
                        }
                      />
                    </div>

                    <div className="flex items-center justify-between space-x-2">
                      <div className="flex items-center space-x-2">
                        <Smartphone className="h-4 w-4 text-muted-foreground" />
                        <Label htmlFor={`${category.value}-push`} className="text-sm">
                          Push
                        </Label>
                      </div>
                      <Switch
                        id={`${category.value}-push`}
                        checked={preferences[category.value]?.push_enabled ?? true}
                        onCheckedChange={(checked) =>
                          updatePreference(category.value, 'push_enabled', checked)
                        }
                      />
                    </div>

                    <div className="flex items-center justify-between space-x-2">
                      <div className="flex items-center space-x-2">
                        <MessageSquare className="h-4 w-4 text-green-600" />
                        <Label htmlFor={`${category.value}-whatsapp`} className="text-sm">
                          WhatsApp
                        </Label>
                      </div>
                      <Switch
                        id={`${category.value}-whatsapp`}
                        checked={preferences[category.value]?.whatsapp_enabled ?? false}
                        onCheckedChange={(checked) =>
                          updatePreference(category.value, 'whatsapp_enabled', checked)
                        }
                      />
                    </div>
                  </div>

                  <div className="flex items-center space-x-4">
                    <div className="flex items-center space-x-2">
                      <Switch
                        id={`${category.value}-digest`}
                        checked={preferences[category.value]?.digest_mode ?? false}
                        onCheckedChange={(checked) =>
                          updatePreference(category.value, 'digest_mode', checked)
                        }
                      />
                      <Label htmlFor={`${category.value}-digest`} className="text-sm">
                        Receive as digest
                      </Label>
                    </div>
                    {preferences[category.value]?.digest_mode && (
                      <Select
                        value={preferences[category.value]?.digest_frequency || 'daily'}
                        onValueChange={(value) =>
                          updatePreference(category.value, 'digest_frequency', value)
                        }
                      >
                        <SelectTrigger className="w-[120px]">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="daily">Daily</SelectItem>
                          <SelectItem value="weekly">Weekly</SelectItem>
                        </SelectContent>
                      </Select>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
