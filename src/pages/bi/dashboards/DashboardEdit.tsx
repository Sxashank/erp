/**
 * Dashboard Edit Page - dashboard builder with drag-drop widgets
 */

import { Plus, Save, Loader2, Eye, Settings } from 'lucide-react';
import { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

import { DashboardGrid } from '@/components/bi/DashboardGrid';
import { PageHeader } from '@/components/common/PageHeader';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet';
import { Switch } from '@/components/ui/switch';
import { Textarea } from '@/components/ui/textarea';
import { useToast } from '@/hooks/use-toast';
import { biDashboardApi, biWidgetApi, biChartApi } from '@/services/biApi';
import { logger } from "@/lib/logger";
import type {
  Dashboard,
  DashboardUpdate,
  DashboardWidget,
  DashboardWidgetCreate,
  GridLayoutItem,
  ChartDefinitionListItem,
  WidgetType,
} from '@/types/bi';
import { getErrorMessage } from "@/lib/errorMessage";

const WIDGET_TYPES: { value: WidgetType; label: string }[] = [
  { value: 'KPI_CARD', label: 'KPI Card' },
  { value: 'LINE_CHART', label: 'Line Chart' },
  { value: 'BAR_CHART', label: 'Bar Chart' },
  { value: 'PIE_CHART', label: 'Pie Chart' },
  { value: 'DONUT_CHART', label: 'Donut Chart' },
  { value: 'AREA_CHART', label: 'Area Chart' },
  { value: 'DATA_TABLE', label: 'Data Table' },
  { value: 'TEXT_MARKDOWN', label: 'Text/Markdown' },
  { value: 'GAUGE_PROGRESS', label: 'Gauge/Progress' },
];

export function DashboardEdit() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();

  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [pendingLayouts, setPendingLayouts] = useState<GridLayoutItem[]>([]);

  // Widget drawer state
  const [widgetDrawerOpen, setWidgetDrawerOpen] = useState(false);
  const [charts, setCharts] = useState<ChartDefinitionListItem[]>([]);
  const [addingWidget, setAddingWidget] = useState(false);
  const [newWidget, setNewWidget] = useState<Partial<DashboardWidgetCreate>>({
    widget_type: 'KPI_CARD',
    grid_w: 4,
    grid_h: 3,
  });

  // Delete widget state
  const [deleteWidget, setDeleteWidget] = useState<DashboardWidget | null>(null);
  const [deletingWidget, setDeletingWidget] = useState(false);

  // Settings panel state
  const [settingsOpen, setSettingsOpen] = useState(false);

  const fetchDashboard = async () => {
    if (!id) return;

    try {
      setLoading(true);
      const response = await biDashboardApi.get(id);
      setDashboard(response.data);
    } catch (error) {
      logger.error('Error fetching dashboard:', error);
      toast({
        title: 'Error',
        description: 'Failed to load dashboard',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const fetchCharts = async () => {
    try {
      const response = await biChartApi.getAccessible();
      setCharts(response.data);
    } catch (error) {
      logger.error('Error fetching charts:', error);
    }
  };

  useEffect(() => {
    fetchDashboard();
    fetchCharts();
  }, [id]);

  const handleLayoutChange = useCallback((layouts: GridLayoutItem[]) => {
    setPendingLayouts(layouts);
  }, []);

  const handleSaveLayout = async () => {
    if (!id || pendingLayouts.length === 0) return;

    try {
      setSaving(true);
      await biWidgetApi.updateLayout(id, {
        layouts: pendingLayouts.map((l) => ({
          widget_id: l.i,
          grid_x: l.x,
          grid_y: l.y,
          grid_w: l.w,
          grid_h: l.h,
        })),
      });
      toast({
        title: 'Success',
        description: 'Layout saved successfully',
      });
      setPendingLayouts([]);
      fetchDashboard();
    } catch (error) {
      logger.error('Error saving layout:', error);
      toast({
        title: 'Error',
        description: 'Failed to save layout',
        variant: 'destructive',
      });
    } finally {
      setSaving(false);
    }
  };

  const handleAddWidget = async () => {
    if (!id || !newWidget.widget_key || !newWidget.title || !newWidget.widget_type) {
      toast({
        title: 'Error',
        description: 'Please fill in all required fields',
        variant: 'destructive',
      });
      return;
    }

    try {
      setAddingWidget(true);

      // Calculate position for new widget
      const maxY = Math.max(0, ...(dashboard?.widgets || []).map((w) => w.grid_y + w.grid_h));

      await biWidgetApi.create(id, {
        ...newWidget,
        grid_x: 0,
        grid_y: maxY,
        grid_w: newWidget.grid_w || 4,
        grid_h: newWidget.grid_h || 3,
      } as DashboardWidgetCreate);

      toast({
        title: 'Success',
        description: 'Widget added successfully',
      });

      setWidgetDrawerOpen(false);
      setNewWidget({ widget_type: 'KPI_CARD', grid_w: 4, grid_h: 3 });
      fetchDashboard();
    } catch (error: unknown) {
      logger.error('Error adding widget:', error);
      toast({
        title: 'Error',
        description: getErrorMessage(error, 'Failed to add widget'),
        variant: 'destructive',
      });
    } finally {
      setAddingWidget(false);
    }
  };

  const handleDeleteWidget = async () => {
    if (!id || !deleteWidget) return;

    try {
      setDeletingWidget(true);
      await biWidgetApi.delete(id, deleteWidget.id);
      toast({
        title: 'Success',
        description: 'Widget deleted successfully',
      });
      setDeleteWidget(null);
      fetchDashboard();
    } catch (error) {
      logger.error('Error deleting widget:', error);
      toast({
        title: 'Error',
        description: 'Failed to delete widget',
        variant: 'destructive',
      });
    } finally {
      setDeletingWidget(false);
    }
  };

  const handleSaveSettings = async (data: DashboardUpdate) => {
    if (!id) return;

    try {
      setSaving(true);
      await biDashboardApi.update(id, data);
      toast({
        title: 'Success',
        description: 'Dashboard settings saved',
      });
      setSettingsOpen(false);
      fetchDashboard();
    } catch (error) {
      logger.error('Error saving settings:', error);
      toast({
        title: 'Error',
        description: 'Failed to save settings',
        variant: 'destructive',
      });
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  if (!dashboard) {
    return (
      <div className="py-12 text-center">
        <p className="text-muted-foreground">Dashboard not found</p>
        <Button variant="outline" className="mt-4" onClick={() => navigate('/admin/bi/dashboards')}>
          Back to Dashboards
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={dashboard.name}
        subtitle="Edit dashboard layout and widgets"
        breadcrumbs={[
          { label: 'Dashboards', to: '/admin/bi/dashboards' },
          { label: dashboard.name, to: `/admin/bi/dashboards/${id}` },
          { label: 'Edit' },
        ]}
        actions={
          <div className="flex items-center gap-2">
            <Button variant="outline" onClick={() => setSettingsOpen(true)}>
              <Settings className="mr-2 h-4 w-4" />
              Settings
            </Button>
            <Button variant="outline" onClick={() => navigate(`/admin/bi/dashboards/${id}`)}>
              <Eye className="mr-2 h-4 w-4" />
              Preview
            </Button>
            <Button onClick={() => setWidgetDrawerOpen(true)}>
              <Plus className="mr-2 h-4 w-4" />
              Add Widget
            </Button>
            {pendingLayouts.length > 0 && (
              <Button onClick={handleSaveLayout} disabled={saving}>
                {saving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                <Save className="mr-2 h-4 w-4" />
                Save Layout
              </Button>
            )}
          </div>
        }
      />

      <Card>
        <CardContent className="pt-6">
          <DashboardGrid
            widgets={dashboard.widgets}
            isEditing={true}
            autoRefresh={false}
            onLayoutChange={handleLayoutChange}
            onWidgetEdit={(widget) =>
              navigate(`/admin/bi/dashboards/${id}/widgets/${widget.id}/edit`)
            }
            onWidgetDelete={setDeleteWidget}
          />
        </CardContent>
      </Card>

      {/* Add Widget Drawer */}
      <Sheet open={widgetDrawerOpen} onOpenChange={setWidgetDrawerOpen}>
        <SheetContent>
          <SheetHeader>
            <SheetTitle>Add Widget</SheetTitle>
            <SheetDescription>Add a new widget to your dashboard</SheetDescription>
          </SheetHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="widget_key">Widget Key *</Label>
              <Input
                id="widget_key"
                placeholder="revenue_kpi"
                value={newWidget.widget_key || ''}
                onChange={(e) => setNewWidget({ ...newWidget, widget_key: e.target.value })}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="widget_title">Title *</Label>
              <Input
                id="widget_title"
                placeholder="Revenue MTD"
                value={newWidget.title || ''}
                onChange={(e) => setNewWidget({ ...newWidget, title: e.target.value })}
              />
            </div>

            <div className="space-y-2">
              <Label>Widget Type *</Label>
              <Select
                value={newWidget.widget_type}
                onValueChange={(value) =>
                  setNewWidget({ ...newWidget, widget_type: value as WidgetType })
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select widget type" />
                </SelectTrigger>
                <SelectContent>
                  {WIDGET_TYPES.map((type) => (
                    <SelectItem key={type.value} value={type.value}>
                      {type.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Chart Definition (Optional)</Label>
              <Select
                value={newWidget.chart_definition_id || ''}
                onValueChange={(value) =>
                  setNewWidget({ ...newWidget, chart_definition_id: value || undefined })
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select a chart" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="__none__">None</SelectItem>
                  {charts.map((chart) => (
                    <SelectItem key={chart.id} value={chart.id}>
                      {chart.name} ({chart.module})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="grid_w">Width (columns)</Label>
                <Input
                  id="grid_w"
                  type="number"
                  min={2}
                  max={12}
                  value={newWidget.grid_w || 4}
                  onChange={(e) => setNewWidget({ ...newWidget, grid_w: parseInt(e.target.value) })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="grid_h">Height (rows)</Label>
                <Input
                  id="grid_h"
                  type="number"
                  min={2}
                  max={8}
                  value={newWidget.grid_h || 3}
                  onChange={(e) => setNewWidget({ ...newWidget, grid_h: parseInt(e.target.value) })}
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-4">
              <Button variant="outline" onClick={() => setWidgetDrawerOpen(false)}>
                Cancel
              </Button>
              <Button onClick={handleAddWidget} disabled={addingWidget}>
                {addingWidget && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Add Widget
              </Button>
            </div>
          </div>
        </SheetContent>
      </Sheet>

      {/* Settings Drawer */}
      <Sheet open={settingsOpen} onOpenChange={setSettingsOpen}>
        <SheetContent>
          <SheetHeader>
            <SheetTitle>Dashboard Settings</SheetTitle>
            <SheetDescription>Configure dashboard settings</SheetDescription>
          </SheetHeader>
          <DashboardSettingsForm
            dashboard={dashboard}
            onSave={handleSaveSettings}
            saving={saving}
            onCancel={() => setSettingsOpen(false)}
          />
        </SheetContent>
      </Sheet>

      {/* Delete Widget Confirmation */}
      <AlertDialog open={!!deleteWidget} onOpenChange={() => setDeleteWidget(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Widget</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete the widget "{deleteWidget?.title}"? This action cannot
              be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteWidget}
              disabled={deletingWidget}
              className="bg-red-600 hover:bg-red-700"
            >
              {deletingWidget && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

// Settings form component
function DashboardSettingsForm({
  dashboard,
  onSave,
  saving,
  onCancel,
}: {
  dashboard: Dashboard;
  onSave: (data: DashboardUpdate) => void;
  saving: boolean;
  onCancel: () => void;
}) {
  const [formData, setFormData] = useState<DashboardUpdate>({
    name: dashboard.name,
    description: dashboard.description || '',
    is_default: dashboard.is_default,
    is_public: dashboard.is_public,
    auto_refresh: dashboard.auto_refresh,
    refresh_interval_seconds: dashboard.refresh_interval_seconds,
  });

  return (
    <div className="space-y-4 py-4">
      <div className="space-y-2">
        <Label htmlFor="name">Name</Label>
        <Input
          id="name"
          value={formData.name || ''}
          onChange={(e) => setFormData({ ...formData, name: e.target.value })}
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="description">Description</Label>
        <Textarea
          id="description"
          value={formData.description || ''}
          onChange={(e) => setFormData({ ...formData, description: e.target.value })}
          rows={3}
        />
      </div>

      <div className="flex items-center justify-between">
        <div>
          <Label>Default Dashboard</Label>
          <p className="text-sm text-muted-foreground">Set as organization default</p>
        </div>
        <Switch
          checked={formData.is_default || false}
          onCheckedChange={(checked) => setFormData({ ...formData, is_default: checked })}
        />
      </div>

      <div className="flex items-center justify-between">
        <div>
          <Label>Public Dashboard</Label>
          <p className="text-sm text-muted-foreground">Visible to all users</p>
        </div>
        <Switch
          checked={formData.is_public || false}
          onCheckedChange={(checked) => setFormData({ ...formData, is_public: checked })}
        />
      </div>

      <div className="flex items-center justify-between">
        <div>
          <Label>Auto Refresh</Label>
          <p className="text-sm text-muted-foreground">Refresh widgets automatically</p>
        </div>
        <Switch
          checked={formData.auto_refresh || false}
          onCheckedChange={(checked) => setFormData({ ...formData, auto_refresh: checked })}
        />
      </div>

      {formData.auto_refresh && (
        <div className="space-y-2">
          <Label htmlFor="refresh_interval">Refresh Interval (seconds)</Label>
          <Input
            id="refresh_interval"
            type="number"
            min={10}
            value={formData.refresh_interval_seconds || 60}
            onChange={(e) =>
              setFormData({ ...formData, refresh_interval_seconds: parseInt(e.target.value) })
            }
          />
        </div>
      )}

      <div className="flex justify-end gap-2 pt-4">
        <Button variant="outline" onClick={onCancel}>
          Cancel
        </Button>
        <Button onClick={() => onSave(formData)} disabled={saving}>
          {saving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          Save Settings
        </Button>
      </div>
    </div>
  );
}
