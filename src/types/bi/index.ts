/**
 * BI/Analytics module types
 */

// ==========================================
// ENUMS
// ==========================================

export type WidgetType =
  | 'KPI_CARD'
  | 'LINE_CHART'
  | 'BAR_CHART'
  | 'PIE_CHART'
  | 'DONUT_CHART'
  | 'AREA_CHART'
  | 'DATA_TABLE'
  | 'TEXT_MARKDOWN'
  | 'GAUGE_PROGRESS';

export type ChartType =
  | 'LINE'
  | 'BAR'
  | 'PIE'
  | 'DONUT'
  | 'AREA'
  | 'GAUGE'
  | 'KPI'
  | 'TABLE';

export type BIModule =
  | 'FINANCE'
  | 'LENDING'
  | 'HR'
  | 'TREASURY'
  | 'PROCUREMENT'
  | 'INVENTORY'
  | 'TAX'
  | 'COLLECTIONS'
  | 'LEGAL'
  | 'PORTAL';

export type DataSourceType = 'API_ENDPOINT' | 'SQL_QUERY' | 'STATIC';

export type APIMethod = 'GET' | 'POST';

// ==========================================
// DATA SOURCE
// ==========================================

export interface DataSource {
  id: string;
  code: string;
  name: string;
  description?: string;
  organization_id?: string;
  source_type: DataSourceType;
  api_endpoint?: string;
  api_method?: APIMethod;
  query_template?: string;
  static_data?: Record<string, unknown>;
  parameters_schema?: Record<string, unknown>;
  response_transform?: Record<string, unknown>;
  cache_ttl_seconds: number;
  created_at: string;
  updated_at?: string;
  is_active: boolean;
}

export interface DataSourceCreate {
  code: string;
  name: string;
  description?: string;
  organization_id?: string;
  source_type: DataSourceType;
  api_endpoint?: string;
  api_method?: APIMethod;
  query_template?: string;
  static_data?: Record<string, unknown>;
  parameters_schema?: Record<string, unknown>;
  response_transform?: Record<string, unknown>;
  cache_ttl_seconds?: number;
}

export interface DataSourceUpdate {
  code?: string;
  name?: string;
  description?: string;
  source_type?: DataSourceType;
  api_endpoint?: string;
  api_method?: APIMethod;
  query_template?: string;
  static_data?: Record<string, unknown> | null;
  parameters_schema?: Record<string, unknown>;
  response_transform?: Record<string, unknown>;
  cache_ttl_seconds?: number;
}

export interface DataSourceListItem {
  id: string;
  code: string;
  name: string;
  description?: string;
  source_type: DataSourceType;
  organization_id?: string;
  cache_ttl_seconds?: number;
  is_active: boolean;
}

export interface DataSourceFetchRequest {
  parameters?: Record<string, unknown>;
}

export interface DataSourceFetchResponse {
  data: Record<string, unknown>;
  cached: boolean;
}

// ==========================================
// CHART DEFINITION
// ==========================================

export interface ChartRoleAccess {
  id: string;
  chart_definition_id: string;
  role_id: string;
  role_name?: string;
  role_code?: string;
  created_at: string;
  updated_at?: string;
  is_active: boolean;
}

export interface ChartDefinition {
  id: string;
  code: string;
  name: string;
  description?: string;
  organization_id?: string;
  module: BIModule;
  chart_type: ChartType;
  default_data_source_id?: string;
  config?: Record<string, unknown>;
  data_mapping?: Record<string, unknown>;
  is_system: boolean;
  role_access: ChartRoleAccess[];
  created_at: string;
  updated_at?: string;
  is_active: boolean;
}

export interface ChartDefinitionCreate {
  code: string;
  name: string;
  description?: string;
  organization_id?: string;
  module: BIModule;
  chart_type: ChartType;
  default_data_source_id?: string;
  config?: Record<string, unknown>;
  data_mapping?: Record<string, unknown>;
  is_system?: boolean;
  role_ids?: string[];
}

export interface ChartDefinitionUpdate {
  code?: string;
  name?: string;
  description?: string;
  module?: BIModule;
  chart_type?: ChartType;
  default_data_source_id?: string;
  config?: Record<string, unknown>;
  data_mapping?: Record<string, unknown>;
}

export interface ChartDefinitionListItem {
  id: string;
  code: string;
  name: string;
  description?: string;
  module: BIModule;
  chart_type: ChartType;
  is_system: boolean;
  has_data_source: boolean;
  is_active: boolean;
}

export interface SetChartRoleAccessRequest {
  role_ids: string[];
}

// ==========================================
// DASHBOARD WIDGET
// ==========================================

export interface ChartDefinitionBrief {
  id: string;
  code: string;
  name: string;
  chart_type: ChartType;
  module: BIModule;
}

export interface DataSourceBrief {
  id: string;
  code: string;
  name: string;
}

export interface DashboardWidget {
  id: string;
  dashboard_id: string;
  widget_key: string;
  title: string;
  widget_type: WidgetType;
  chart_definition_id?: string;
  data_source_id?: string;
  chart_definition?: ChartDefinitionBrief;
  data_source?: DataSourceBrief;
  grid_x: number;
  grid_y: number;
  grid_w: number;
  grid_h: number;
  config?: WidgetConfig;
  display_order: number;
  created_at: string;
  updated_at?: string;
  is_active: boolean;
}

export interface DashboardWidgetCreate {
  widget_key: string;
  title: string;
  widget_type: WidgetType;
  chart_definition_id?: string;
  data_source_id?: string;
  grid_x?: number;
  grid_y?: number;
  grid_w?: number;
  grid_h?: number;
  config?: WidgetConfig;
  display_order?: number;
}

export interface DashboardWidgetUpdate {
  title?: string;
  grid_x?: number;
  grid_y?: number;
  grid_w?: number;
  grid_h?: number;
  config?: WidgetConfig;
  display_order?: number;
  chart_definition_id?: string;
  data_source_id?: string;
}

export interface DashboardWidgetLayoutUpdate {
  widget_id: string;
  grid_x: number;
  grid_y: number;
  grid_w: number;
  grid_h: number;
}

export interface BulkLayoutUpdateRequest {
  layouts: DashboardWidgetLayoutUpdate[];
}

// ==========================================
// WIDGET CONFIG TYPES
// ==========================================

export interface KPICardConfig {
  valueField: string;
  subtitleField?: string;
  changeField?: string;
  icon?: string;
  valueFormat?: 'currency' | 'number' | 'percentage';
  prefix?: string;
  suffix?: string;
  decimals?: number;
}

export interface ChartSeries {
  dataKey: string;
  name: string;
  color?: string;
}

export interface LineChartConfig {
  xAxisField: string;
  series: ChartSeries[];
  showLegend?: boolean;
  showGrid?: boolean;
}

export interface BarChartConfig {
  xAxisField: string;
  series: ChartSeries[];
  showLegend?: boolean;
  stacked?: boolean;
}

export interface PieChartConfig {
  valueField: string;
  labelField: string;
  colors?: string[];
  showLegend?: boolean;
}

export interface DonutChartConfig extends PieChartConfig {
  innerRadius?: number;
  outerRadius?: number;
}

export interface AreaChartConfig {
  xAxisField: string;
  series: ChartSeries[];
  showLegend?: boolean;
  stacked?: boolean;
}

export interface TableColumn {
  key: string;
  header: string;
  width?: number;
  align?: 'left' | 'center' | 'right';
  format?: 'text' | 'number' | 'currency' | 'date' | 'percentage';
}

export interface DataTableConfig {
  columns: TableColumn[];
  pageSize?: number;
  sortable?: boolean;
}

export interface TextMarkdownConfig {
  content: string;
}

export interface GaugeThreshold {
  value: number;
  color: string;
}

export interface GaugeConfig {
  valueField: string;
  minValue?: number;
  maxValue?: number;
  thresholds?: GaugeThreshold[];
}

export type WidgetConfig =
  | KPICardConfig
  | LineChartConfig
  | BarChartConfig
  | PieChartConfig
  | DonutChartConfig
  | AreaChartConfig
  | DataTableConfig
  | TextMarkdownConfig
  | GaugeConfig
  | Record<string, unknown>;

// ==========================================
// DASHBOARD ROLE ACCESS
// ==========================================

export interface DashboardRoleAccess {
  id: string;
  dashboard_id: string;
  role_id: string;
  role_name?: string;
  role_code?: string;
  can_view: boolean;
  can_edit: boolean;
  show_on_landing: boolean;
  landing_order: number;
  created_at: string;
  updated_at?: string;
  is_active: boolean;
}

export interface DashboardRoleAccessCreate {
  role_id: string;
  can_view?: boolean;
  can_edit?: boolean;
  show_on_landing?: boolean;
  landing_order?: number;
}

export interface DashboardRoleAccessUpdate {
  can_view?: boolean;
  can_edit?: boolean;
  show_on_landing?: boolean;
  landing_order?: number;
}

// ==========================================
// DASHBOARD
// ==========================================

export interface Dashboard {
  id: string;
  code: string;
  name: string;
  description?: string;
  organization_id: string;
  is_default: boolean;
  is_public: boolean;
  layout_config?: Record<string, unknown>;
  display_order: number;
  auto_refresh: boolean;
  refresh_interval_seconds: number;
  widgets: DashboardWidget[];
  role_access: DashboardRoleAccess[];
  created_at: string;
  updated_at?: string;
  is_active: boolean;
}

export interface DashboardCreate {
  code: string;
  name: string;
  description?: string;
  organization_id: string;
  is_default?: boolean;
  is_public?: boolean;
  layout_config?: Record<string, unknown>;
  display_order?: number;
  auto_refresh?: boolean;
  refresh_interval_seconds?: number;
}

export interface DashboardUpdate {
  name?: string;
  description?: string;
  is_default?: boolean;
  is_public?: boolean;
  layout_config?: Record<string, unknown>;
  display_order?: number;
  auto_refresh?: boolean;
  refresh_interval_seconds?: number;
}

export interface DashboardListItem {
  id: string;
  code: string;
  name: string;
  description?: string;
  is_default: boolean;
  is_public: boolean;
  display_order: number;
  widget_count: number;
  is_active: boolean;
}

export interface LandingDashboard {
  id: string;
  code: string;
  name: string;
  description?: string;
  display_order: number;
  landing_order: number;
  auto_refresh: boolean;
  refresh_interval_seconds: number;
  widgets: DashboardWidget[];
}

// ==========================================
// GRID LAYOUT (react-grid-layout compatible)
// ==========================================

export interface GridLayoutItem {
  i: string; // widget_id
  x: number;
  y: number;
  w: number;
  h: number;
  minW?: number;
  maxW?: number;
  minH?: number;
  maxH?: number;
  static?: boolean;
}
