/**
 * BI/Analytics API service
 */

import type {
  Dashboard,
  DashboardCreate,
  DashboardUpdate,
  DashboardListItem,
  LandingDashboard,
  DashboardWidget,
  DashboardWidgetCreate,
  DashboardWidgetUpdate,
  BulkLayoutUpdateRequest,
  DashboardRoleAccess,
  DashboardRoleAccessCreate,
  DashboardRoleAccessUpdate,
  ChartDefinition,
  ChartDefinitionCreate,
  ChartDefinitionUpdate,
  ChartDefinitionListItem,
  SetChartRoleAccessRequest,
  DataSource,
  DataSourceCreate,
  DataSourceUpdate,
  DataSourceListItem,
  DataSourceFetchRequest,
  DataSourceFetchResponse,
  BIModule,
} from '../types/bi';

import api from './api';

// ==========================================
// DASHBOARDS
// ==========================================

export const biDashboardApi = {
  // List all dashboards
  list: () =>
    api.get<DashboardListItem[]>('/bi/dashboards', {
      params: {},
    }),

  // Get dashboards for landing page
  getLanding: () =>
    api.get<LandingDashboard[]>('/bi/dashboards/landing'),

  // Get accessible dashboards for current user
  getAccessible: () =>
    api.get<DashboardListItem[]>('/bi/dashboards/accessible'),

  // Get single dashboard
  get: (id: string) =>
    api.get<Dashboard>(`/bi/dashboards/${id}`),

  // Create dashboard
  create: (data: DashboardCreate) =>
    api.post<Dashboard>('/bi/dashboards', data),

  // Update dashboard
  update: (id: string, data: DashboardUpdate) =>
    api.put<Dashboard>(`/bi/dashboards/${id}`, data),

  // Delete dashboard
  delete: (id: string) =>
    api.delete(`/bi/dashboards/${id}`),

  // Set as default
  setDefault: (id: string) =>
    api.post<Dashboard>(`/bi/dashboards/${id}/set-default`),
};

// ==========================================
// DASHBOARD ROLE ACCESS
// ==========================================

export const biDashboardAccessApi = {
  // List role access for a dashboard
  list: (dashboardId: string) =>
    api.get<DashboardRoleAccess[]>(`/bi/dashboards/${dashboardId}/access`),

  // Create role access
  create: (dashboardId: string, data: DashboardRoleAccessCreate) =>
    api.post<DashboardRoleAccess>(`/bi/dashboards/${dashboardId}/access`, data),

  // Update role access
  update: (dashboardId: string, accessId: string, data: DashboardRoleAccessUpdate) =>
    api.put<DashboardRoleAccess>(`/bi/dashboards/${dashboardId}/access/${accessId}`, data),

  // Delete role access
  delete: (dashboardId: string, accessId: string) =>
    api.delete(`/bi/dashboards/${dashboardId}/access/${accessId}`),
};

// ==========================================
// WIDGETS
// ==========================================

export const biWidgetApi = {
  // List widgets in a dashboard
  list: (dashboardId: string) =>
    api.get<DashboardWidget[]>(`/bi/dashboards/${dashboardId}/widgets`),

  // Get single widget
  get: (dashboardId: string, widgetId: string) =>
    api.get<DashboardWidget>(`/bi/dashboards/${dashboardId}/widgets/${widgetId}`),

  // Create widget
  create: (dashboardId: string, data: DashboardWidgetCreate) =>
    api.post<DashboardWidget>(`/bi/dashboards/${dashboardId}/widgets`, data),

  // Update widget
  update: (dashboardId: string, widgetId: string, data: DashboardWidgetUpdate) =>
    api.put<DashboardWidget>(`/bi/dashboards/${dashboardId}/widgets/${widgetId}`, data),

  // Delete widget
  delete: (dashboardId: string, widgetId: string) =>
    api.delete(`/bi/dashboards/${dashboardId}/widgets/${widgetId}`),

  // Bulk update layout
  updateLayout: (dashboardId: string, data: BulkLayoutUpdateRequest) =>
    api.put<DashboardWidget[]>(`/bi/dashboards/${dashboardId}/widgets/layout`, data),
};

// ==========================================
// CHART DEFINITIONS
// ==========================================

export const biChartApi = {
  // List all chart definitions
  list: (params?: { module?: BIModule; include_system?: boolean }) =>
    api.get<ChartDefinitionListItem[]>('/bi/chart-definitions', { params }),

  // List accessible charts for current user
  getAccessible: (module?: BIModule) =>
    api.get<ChartDefinitionListItem[]>('/bi/chart-definitions/accessible', {
      params: { module },
    }),

  // Get single chart definition
  get: (id: string) =>
    api.get<ChartDefinition>(`/bi/chart-definitions/${id}`),

  // Create chart definition
  create: (data: ChartDefinitionCreate) =>
    api.post<ChartDefinition>('/bi/chart-definitions', data),

  // Update chart definition
  update: (id: string, data: ChartDefinitionUpdate) =>
    api.put<ChartDefinition>(`/bi/chart-definitions/${id}`, data),

  // Delete chart definition
  delete: (id: string) =>
    api.delete(`/bi/chart-definitions/${id}`),

  // Set role access
  setRoleAccess: (id: string, data: SetChartRoleAccessRequest) =>
    api.put<ChartDefinition>(`/bi/chart-definitions/${id}/role-access`, data),
};

// ==========================================
// DATA SOURCES
// ==========================================

export const biDataSourceApi = {
  // List all data sources
  list: (params?: { include_system?: boolean }) =>
    api.get<DataSourceListItem[]>('/bi/data-sources', { params }),

  // Get single data source
  get: (id: string) =>
    api.get<DataSource>(`/bi/data-sources/${id}`),

  // Create data source
  create: (data: DataSourceCreate) =>
    api.post<DataSource>('/bi/data-sources', data),

  // Update data source
  update: (id: string, data: DataSourceUpdate) =>
    api.put<DataSource>(`/bi/data-sources/${id}`, data),

  // Delete data source
  delete: (id: string) =>
    api.delete(`/bi/data-sources/${id}`),

  // Fetch data from source
  fetch: (id: string, data?: DataSourceFetchRequest) =>
    api.post<DataSourceFetchResponse>(`/bi/data-sources/${id}/fetch`, data || {}),

  // Preview data source
  preview: (id: string) =>
    api.get<DataSourceFetchResponse>(`/bi/data-sources/${id}/preview`),
};

// Combined export
export const biApi = {
  dashboards: biDashboardApi,
  access: biDashboardAccessApi,
  widgets: biWidgetApi,
  charts: biChartApi,
  dataSources: biDataSourceApi,
};

export default biApi;
