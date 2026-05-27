/**
 * BI/Analytics API service
 */

import type { AxiosResponse } from 'axios';

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

type RawBiRecord = Record<string, unknown>;

function withData<T>(response: AxiosResponse<unknown>, data: T): AxiosResponse<T> {
  return {
    ...response,
    data,
  };
}

function normalizeDashboardRoleAccess(raw: RawBiRecord): DashboardRoleAccess {
  return {
    id: String(raw.id ?? ''),
    dashboard_id: String(raw.dashboard_id ?? raw.dashboardId ?? ''),
    role_id: String(raw.role_id ?? raw.roleId ?? ''),
    role_name: (raw.role_name ?? raw.roleName) as string | undefined,
    role_code: (raw.role_code ?? raw.roleCode) as string | undefined,
    can_view: Boolean(raw.can_view ?? raw.canView ?? false),
    can_edit: Boolean(raw.can_edit ?? raw.canEdit ?? false),
    show_on_landing: Boolean(raw.show_on_landing ?? raw.showOnLanding ?? false),
    landing_order: Number(raw.landing_order ?? raw.landingOrder ?? 0),
    created_at: String(raw.created_at ?? raw.createdAt ?? ''),
    updated_at: (raw.updated_at ?? raw.updatedAt) as string | undefined,
    is_active: Boolean(raw.is_active ?? raw.isActive ?? true),
  };
}

function normalizeDashboardWidget(raw: RawBiRecord): DashboardWidget {
  const chartDefinition = raw.chart_definition ?? raw.chartDefinition;
  const dataSource = raw.data_source ?? raw.dataSource;

  return {
    id: String(raw.id ?? ''),
    dashboard_id: String(raw.dashboard_id ?? raw.dashboardId ?? ''),
    widget_key: String(raw.widget_key ?? raw.widgetKey ?? ''),
    title: String(raw.title ?? ''),
    widget_type: String(
      raw.widget_type ?? raw.widgetType ?? 'KPI_CARD',
    ) as DashboardWidget['widget_type'],
    chart_definition_id: (raw.chart_definition_id ?? raw.chartDefinitionId) as string | undefined,
    data_source_id: (raw.data_source_id ?? raw.dataSourceId) as string | undefined,
    chart_definition:
      chartDefinition && typeof chartDefinition === 'object'
        ? {
            id: String((chartDefinition as RawBiRecord).id ?? ''),
            code: String((chartDefinition as RawBiRecord).code ?? ''),
            name: String((chartDefinition as RawBiRecord).name ?? ''),
            chart_type: String(
              (chartDefinition as RawBiRecord).chart_type ??
                (chartDefinition as RawBiRecord).chartType ??
                'TABLE',
            ) as ChartDefinition['chart_type'],
            module: String((chartDefinition as RawBiRecord).module ?? 'FINANCE') as BIModule,
          }
        : undefined,
    data_source:
      dataSource && typeof dataSource === 'object'
        ? {
            id: String((dataSource as RawBiRecord).id ?? ''),
            code: String((dataSource as RawBiRecord).code ?? ''),
            name: String((dataSource as RawBiRecord).name ?? ''),
          }
        : undefined,
    grid_x: Number(raw.grid_x ?? raw.gridX ?? 0),
    grid_y: Number(raw.grid_y ?? raw.gridY ?? 0),
    grid_w: Number(raw.grid_w ?? raw.gridW ?? 4),
    grid_h: Number(raw.grid_h ?? raw.gridH ?? 3),
    config: (raw.config as DashboardWidget['config']) ?? undefined,
    display_order: Number(raw.display_order ?? raw.displayOrder ?? 0),
    created_at: String(raw.created_at ?? raw.createdAt ?? ''),
    updated_at: (raw.updated_at ?? raw.updatedAt) as string | undefined,
    is_active: Boolean(raw.is_active ?? raw.isActive ?? true),
  };
}

function normalizeDashboardListItem(raw: RawBiRecord): DashboardListItem {
  return {
    id: String(raw.id ?? ''),
    code: String(raw.code ?? ''),
    name: String(raw.name ?? ''),
    description: (raw.description as string | undefined) ?? undefined,
    is_default: Boolean(raw.is_default ?? raw.isDefault ?? false),
    is_public: Boolean(raw.is_public ?? raw.isPublic ?? false),
    display_order: Number(raw.display_order ?? raw.displayOrder ?? 0),
    widget_count: Number(raw.widget_count ?? raw.widgetCount ?? 0),
    is_active: Boolean(raw.is_active ?? raw.isActive ?? true),
  };
}

function normalizeDashboard(raw: RawBiRecord): Dashboard {
  const roleAccess = raw.role_access ?? raw.roleAccess;
  return {
    id: String(raw.id ?? ''),
    code: String(raw.code ?? ''),
    name: String(raw.name ?? ''),
    description: (raw.description as string | undefined) ?? undefined,
    organization_id: (raw.organization_id ?? raw.organizationId) as string | undefined,
    is_default: Boolean(raw.is_default ?? raw.isDefault ?? false),
    is_public: Boolean(raw.is_public ?? raw.isPublic ?? false),
    layout_config: (raw.layout_config ?? raw.layoutConfig) as Record<string, unknown> | undefined,
    display_order: Number(raw.display_order ?? raw.displayOrder ?? 0),
    auto_refresh: Boolean(raw.auto_refresh ?? raw.autoRefresh ?? false),
    refresh_interval_seconds: Number(
      raw.refresh_interval_seconds ?? raw.refreshIntervalSeconds ?? 60,
    ),
    widgets: Array.isArray(raw.widgets)
      ? raw.widgets.map((widget) => normalizeDashboardWidget(widget as RawBiRecord))
      : [],
    role_access: Array.isArray(roleAccess)
      ? roleAccess.map((access) => normalizeDashboardRoleAccess(access as RawBiRecord))
      : [],
    created_at: String(raw.created_at ?? raw.createdAt ?? ''),
    updated_at: (raw.updated_at ?? raw.updatedAt) as string | undefined,
    is_active: Boolean(raw.is_active ?? raw.isActive ?? true),
  };
}

function normalizeLandingDashboard(raw: RawBiRecord): LandingDashboard {
  return {
    id: String(raw.id ?? ''),
    code: String(raw.code ?? ''),
    name: String(raw.name ?? ''),
    description: (raw.description as string | undefined) ?? undefined,
    display_order: Number(raw.display_order ?? raw.displayOrder ?? 0),
    landing_order: Number(raw.landing_order ?? raw.landingOrder ?? 0),
    auto_refresh: Boolean(raw.auto_refresh ?? raw.autoRefresh ?? false),
    refresh_interval_seconds: Number(
      raw.refresh_interval_seconds ?? raw.refreshIntervalSeconds ?? 60,
    ),
    widgets: Array.isArray(raw.widgets)
      ? raw.widgets.map((widget) => normalizeDashboardWidget(widget as RawBiRecord))
      : [],
  };
}

function normalizeChartDefinitionListItem(raw: RawBiRecord): ChartDefinitionListItem {
  const defaultDataSourceId = raw.default_data_source_id ?? raw.defaultDataSourceId;
  return {
    id: String(raw.id ?? ''),
    code: String(raw.code ?? ''),
    name: String(raw.name ?? ''),
    description: (raw.description as string | undefined) ?? undefined,
    module: String(raw.module ?? 'FINANCE') as ChartDefinitionListItem['module'],
    chart_type: String(
      raw.chart_type ?? raw.chartType ?? 'TABLE',
    ) as ChartDefinitionListItem['chart_type'],
    is_system: Boolean(raw.is_system ?? raw.isSystem ?? false),
    has_data_source: Boolean(raw.has_data_source ?? raw.hasDataSource ?? defaultDataSourceId),
    is_active: Boolean(raw.is_active ?? raw.isActive ?? true),
  };
}

function normalizeChartDefinition(raw: RawBiRecord): ChartDefinition {
  const roleAccess = raw.role_access ?? raw.roleAccess;
  return {
    id: String(raw.id ?? ''),
    code: String(raw.code ?? ''),
    name: String(raw.name ?? ''),
    description: (raw.description as string | undefined) ?? undefined,
    organization_id: (raw.organization_id ?? raw.organizationId) as string | undefined,
    module: String(raw.module ?? 'FINANCE') as ChartDefinition['module'],
    chart_type: String(raw.chart_type ?? raw.chartType ?? 'TABLE') as ChartDefinition['chart_type'],
    default_data_source_id: (raw.default_data_source_id ?? raw.defaultDataSourceId) as
      | string
      | undefined,
    config: (raw.config as Record<string, unknown> | undefined) ?? undefined,
    data_mapping: (raw.data_mapping ?? raw.dataMapping) as Record<string, unknown> | undefined,
    is_system: Boolean(raw.is_system ?? raw.isSystem ?? false),
    role_access: Array.isArray(roleAccess)
      ? roleAccess.map((access) => ({
          id: String((access as RawBiRecord).id ?? ''),
          chart_definition_id: String(
            (access as RawBiRecord).chart_definition_id ??
              (access as RawBiRecord).chartDefinitionId ??
              '',
          ),
          role_id: String((access as RawBiRecord).role_id ?? (access as RawBiRecord).roleId ?? ''),
          role_name: ((access as RawBiRecord).role_name ?? (access as RawBiRecord).roleName) as
            | string
            | undefined,
          role_code: ((access as RawBiRecord).role_code ?? (access as RawBiRecord).roleCode) as
            | string
            | undefined,
          created_at: String(
            (access as RawBiRecord).created_at ?? (access as RawBiRecord).createdAt ?? '',
          ),
          updated_at: ((access as RawBiRecord).updated_at ?? (access as RawBiRecord).updatedAt) as
            | string
            | undefined,
          is_active: Boolean(
            (access as RawBiRecord).is_active ?? (access as RawBiRecord).isActive ?? true,
          ),
        }))
      : [],
    created_at: String(raw.created_at ?? raw.createdAt ?? ''),
    updated_at: (raw.updated_at ?? raw.updatedAt) as string | undefined,
    is_active: Boolean(raw.is_active ?? raw.isActive ?? true),
  };
}

function normalizeDataSourceListItem(raw: RawBiRecord): DataSourceListItem {
  return {
    id: String(raw.id ?? ''),
    code: String(raw.code ?? ''),
    name: String(raw.name ?? ''),
    description: (raw.description as string | undefined) ?? undefined,
    source_type: String(
      raw.source_type ?? raw.sourceType ?? 'STATIC',
    ) as DataSourceListItem['source_type'],
    organization_id: (raw.organization_id ?? raw.organizationId) as string | undefined,
    cache_ttl_seconds: Number(raw.cache_ttl_seconds ?? raw.cacheTtlSeconds ?? 0),
    is_active: Boolean(raw.is_active ?? raw.isActive ?? true),
  };
}

function normalizeDataSource(raw: RawBiRecord): DataSource {
  return {
    id: String(raw.id ?? ''),
    code: String(raw.code ?? ''),
    name: String(raw.name ?? ''),
    description: (raw.description as string | undefined) ?? undefined,
    organization_id: (raw.organization_id ?? raw.organizationId) as string | undefined,
    source_type: String(raw.source_type ?? raw.sourceType ?? 'STATIC') as DataSource['source_type'],
    api_endpoint: (raw.api_endpoint ?? raw.apiEndpoint) as string | undefined,
    api_method: String(raw.api_method ?? raw.apiMethod ?? 'GET') as DataSource['api_method'],
    query_template: (raw.query_template ?? raw.queryTemplate) as string | undefined,
    static_data: (raw.static_data ?? raw.staticData) as Record<string, unknown> | undefined,
    parameters_schema: (raw.parameters_schema ?? raw.parametersSchema) as
      | Record<string, unknown>
      | undefined,
    response_transform: (raw.response_transform ?? raw.responseTransform) as
      | Record<string, unknown>
      | undefined,
    cache_ttl_seconds: Number(raw.cache_ttl_seconds ?? raw.cacheTtlSeconds ?? 0),
    created_at: String(raw.created_at ?? raw.createdAt ?? ''),
    updated_at: (raw.updated_at ?? raw.updatedAt) as string | undefined,
    is_active: Boolean(raw.is_active ?? raw.isActive ?? true),
  };
}

// ==========================================
// DASHBOARDS
// ==========================================

export const biDashboardApi = {
  // List all dashboards
  list: async () => {
    const response = await api.get<RawBiRecord[]>('/bi/dashboards', {
      params: {},
    });
    return withData(response, response.data.map(normalizeDashboardListItem));
  },

  // Get dashboards for landing page
  getLanding: async () => {
    const response = await api.get<RawBiRecord[]>('/bi/dashboards/landing');
    return withData(response, response.data.map(normalizeLandingDashboard));
  },

  // Get accessible dashboards for current user
  getAccessible: async () => {
    const response = await api.get<RawBiRecord[]>('/bi/dashboards/accessible');
    return withData(response, response.data.map(normalizeDashboardListItem));
  },

  // Get single dashboard
  get: async (id: string) => {
    const response = await api.get<RawBiRecord>(`/bi/dashboards/${id}`);
    return withData(response, normalizeDashboard(response.data));
  },

  // Create dashboard
  create: async (data: DashboardCreate) => {
    const response = await api.post<RawBiRecord>('/bi/dashboards', data);
    return withData(response, normalizeDashboard(response.data));
  },

  // Update dashboard
  update: async (id: string, data: DashboardUpdate) => {
    const response = await api.put<RawBiRecord>(`/bi/dashboards/${id}`, data);
    return withData(response, normalizeDashboard(response.data));
  },

  // Delete dashboard
  delete: (id: string) => api.delete(`/bi/dashboards/${id}`),

  // Set as default
  setDefault: async (id: string) => {
    const response = await api.post<RawBiRecord>(`/bi/dashboards/${id}/set-default`);
    return withData(response, normalizeDashboard(response.data));
  },
};

// ==========================================
// DASHBOARD ROLE ACCESS
// ==========================================

export const biDashboardAccessApi = {
  // List role access for a dashboard
  list: async (dashboardId: string) => {
    const response = await api.get<RawBiRecord[]>(`/bi/dashboards/${dashboardId}/access`);
    return withData(response, response.data.map(normalizeDashboardRoleAccess));
  },

  // Create role access
  create: async (dashboardId: string, data: DashboardRoleAccessCreate) => {
    const response = await api.post<RawBiRecord>(`/bi/dashboards/${dashboardId}/access`, data);
    return withData(response, normalizeDashboardRoleAccess(response.data));
  },

  // Update role access
  update: async (dashboardId: string, accessId: string, data: DashboardRoleAccessUpdate) => {
    const response = await api.put<RawBiRecord>(
      `/bi/dashboards/${dashboardId}/access/${accessId}`,
      data,
    );
    return withData(response, normalizeDashboardRoleAccess(response.data));
  },

  // Delete role access
  delete: (dashboardId: string, accessId: string) =>
    api.delete(`/bi/dashboards/${dashboardId}/access/${accessId}`),
};

// ==========================================
// WIDGETS
// ==========================================

export const biWidgetApi = {
  // List widgets in a dashboard
  list: async (dashboardId: string) => {
    const response = await api.get<RawBiRecord[]>(`/bi/dashboards/${dashboardId}/widgets`);
    return withData(response, response.data.map(normalizeDashboardWidget));
  },

  // Get single widget
  get: async (dashboardId: string, widgetId: string) => {
    const response = await api.get<RawBiRecord>(
      `/bi/dashboards/${dashboardId}/widgets/${widgetId}`,
    );
    return withData(response, normalizeDashboardWidget(response.data));
  },

  // Create widget
  create: async (dashboardId: string, data: DashboardWidgetCreate) => {
    const response = await api.post<RawBiRecord>(`/bi/dashboards/${dashboardId}/widgets`, data);
    return withData(response, normalizeDashboardWidget(response.data));
  },

  // Update widget
  update: async (dashboardId: string, widgetId: string, data: DashboardWidgetUpdate) => {
    const response = await api.put<RawBiRecord>(
      `/bi/dashboards/${dashboardId}/widgets/${widgetId}`,
      data,
    );
    return withData(response, normalizeDashboardWidget(response.data));
  },

  // Delete widget
  delete: (dashboardId: string, widgetId: string) =>
    api.delete(`/bi/dashboards/${dashboardId}/widgets/${widgetId}`),

  // Bulk update layout
  updateLayout: async (dashboardId: string, data: BulkLayoutUpdateRequest) => {
    const response = await api.put<RawBiRecord[]>(
      `/bi/dashboards/${dashboardId}/widgets/layout`,
      data,
    );
    return withData(response, response.data.map(normalizeDashboardWidget));
  },
};

// ==========================================
// CHART DEFINITIONS
// ==========================================

export const biChartApi = {
  // List all chart definitions
  list: async (params?: { module?: BIModule; include_system?: boolean }) => {
    const response = await api.get<RawBiRecord[]>('/bi/chart-definitions', { params });
    return withData(response, response.data.map(normalizeChartDefinitionListItem));
  },

  // List accessible charts for current user
  getAccessible: async (module?: BIModule) => {
    const response = await api.get<RawBiRecord[]>('/bi/chart-definitions/accessible', {
      params: { module },
    });
    return withData(response, response.data.map(normalizeChartDefinitionListItem));
  },

  // Get single chart definition
  get: async (id: string) => {
    const response = await api.get<RawBiRecord>(`/bi/chart-definitions/${id}`);
    return withData(response, normalizeChartDefinition(response.data));
  },

  // Create chart definition
  create: async (data: ChartDefinitionCreate) => {
    const response = await api.post<RawBiRecord>('/bi/chart-definitions', data);
    return withData(response, normalizeChartDefinition(response.data));
  },

  // Update chart definition
  update: async (id: string, data: ChartDefinitionUpdate) => {
    const response = await api.put<RawBiRecord>(`/bi/chart-definitions/${id}`, data);
    return withData(response, normalizeChartDefinition(response.data));
  },

  // Delete chart definition
  delete: (id: string) => api.delete(`/bi/chart-definitions/${id}`),

  // Set role access
  setRoleAccess: async (id: string, data: SetChartRoleAccessRequest) => {
    const response = await api.put<RawBiRecord>(`/bi/chart-definitions/${id}/role-access`, data);
    return withData(response, normalizeChartDefinition(response.data));
  },
};

// ==========================================
// DATA SOURCES
// ==========================================

export const biDataSourceApi = {
  // List all data sources
  list: async (params?: { include_system?: boolean }) => {
    const response = await api.get<RawBiRecord[]>('/bi/data-sources', { params });
    return withData(response, response.data.map(normalizeDataSourceListItem));
  },

  // Get single data source
  get: async (id: string) => {
    const response = await api.get<RawBiRecord>(`/bi/data-sources/${id}`);
    return withData(response, normalizeDataSource(response.data));
  },

  // Create data source
  create: async (data: DataSourceCreate) => {
    const response = await api.post<RawBiRecord>('/bi/data-sources', data);
    return withData(response, normalizeDataSource(response.data));
  },

  // Update data source
  update: async (id: string, data: DataSourceUpdate) => {
    const response = await api.put<RawBiRecord>(`/bi/data-sources/${id}`, data);
    return withData(response, normalizeDataSource(response.data));
  },

  // Delete data source
  delete: (id: string) => api.delete(`/bi/data-sources/${id}`),

  // Fetch data from source
  fetch: (id: string, data?: DataSourceFetchRequest) =>
    api.post<DataSourceFetchResponse>(`/bi/data-sources/${id}/fetch`, data || {}),

  // Preview data source
  preview: (id: string) => api.get<DataSourceFetchResponse>(`/bi/data-sources/${id}/preview`),
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
