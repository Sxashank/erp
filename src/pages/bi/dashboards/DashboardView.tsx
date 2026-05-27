/**
 * Dashboard View Page - read-only dashboard view
 */

import { Edit, Loader2, RefreshCw } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

import { ResponsiveDashboardGrid } from '@/components/bi/DashboardGrid';
import { PageHeader } from '@/components/common/PageHeader';
import { Button } from '@/components/ui/button';
import { useToast } from '@/hooks/use-toast';
import { hasPermission, Permissions } from '@/lib/permissions';
import { biDashboardApi } from '@/services/biApi';
import { useAuthStore } from '@/stores/authStore';
import type { Dashboard } from '@/types/bi';

import { logger } from '@/lib/logger';
export function DashboardView() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshKey, setRefreshKey] = useState(0);

  const userPermissions = Array.from(useAuthStore((state) => state.permissions));
  const canEdit = hasPermission(userPermissions, Permissions.BI_DASHBOARD_UPDATE);

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

  useEffect(() => {
    fetchDashboard();
  }, [id]);

  const handleRefresh = () => {
    setRefreshKey((prev) => prev + 1);
    toast({
      title: 'Refreshing',
      description: 'Dashboard data is being refreshed',
    });
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
        subtitle={dashboard.description || undefined}
        breadcrumbs={[
          { label: 'Dashboards', to: '/admin/bi/dashboards' },
          { label: dashboard.name },
        ]}
        actions={
          <div className="flex items-center gap-2">
            <Button variant="outline" size="icon" onClick={handleRefresh}>
              <RefreshCw className="h-4 w-4" />
            </Button>
            {canEdit && (
              <Button onClick={() => navigate(`/admin/bi/dashboards/${id}/edit`)}>
                <Edit className="mr-2 h-4 w-4" />
                Edit Dashboard
              </Button>
            )}
          </div>
        }
      />

      <div key={refreshKey}>
        <ResponsiveDashboardGrid
          widgets={dashboard.widgets}
          autoRefresh={dashboard.auto_refresh}
          refreshInterval={dashboard.refresh_interval_seconds * 1000}
        />
      </div>
    </div>
  );
}
