/**
 * Dashboard Grid - container for widgets with drag-drop support
 */

import { useMemo, useCallback } from 'react';
import type { Layout, LayoutItem } from 'react-grid-layout';
import GridLayout from 'react-grid-layout';

import 'react-grid-layout/css/styles.css';
import 'react-resizable/css/styles.css';
import { WidgetCard } from './WidgetCard';

import type { DashboardWidget, GridLayoutItem } from '@/types/bi';

interface DashboardGridProps {
  widgets: DashboardWidget[];
  isEditing?: boolean;
  autoRefresh?: boolean;
  refreshInterval?: number;
  onLayoutChange?: (layouts: GridLayoutItem[]) => void;
  onWidgetEdit?: (widget: DashboardWidget) => void;
  onWidgetDelete?: (widget: DashboardWidget) => void;
  onWidgetRefresh?: (widget: DashboardWidget) => void;
}

const COLS = 12;
const ROW_HEIGHT = 80;
const MARGIN: [number, number] = [16, 16];

export function DashboardGrid({
  widgets,
  isEditing = false,
  autoRefresh = false,
  refreshInterval = 60000,
  onLayoutChange,
  onWidgetEdit,
  onWidgetDelete,
  onWidgetRefresh,
}: DashboardGridProps) {
  // Convert widgets to grid layout format
  const layout: Layout = useMemo(() => {
    return widgets.map((widget) => ({
      i: widget.id,
      x: widget.grid_x,
      y: widget.grid_y,
      w: widget.grid_w,
      h: widget.grid_h,
      minW: 2,
      minH: 2,
      maxW: 12,
      maxH: 8,
      static: !isEditing,
    }));
  }, [widgets, isEditing]);

  // Handle layout changes
  const handleLayoutChange = useCallback(
    (newLayout: Layout) => {
      if (!isEditing || !onLayoutChange) return;

      const updatedLayouts: GridLayoutItem[] = newLayout.map((item: LayoutItem) => ({
        i: item.i,
        x: item.x,
        y: item.y,
        w: item.w,
        h: item.h,
      }));

      onLayoutChange(updatedLayouts);
    },
    [isEditing, onLayoutChange]
  );

  // Map widgets by ID for quick lookup
  const widgetMap = useMemo(() => {
    return new Map(widgets.map((w) => [w.id, w]));
  }, [widgets]);

  if (widgets.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 border-2 border-dashed rounded-lg">
        <p className="text-muted-foreground">
          No widgets yet. {isEditing ? 'Click "Add Widget" to get started.' : ''}
        </p>
      </div>
    );
  }

  return (
    <div className="relative">
      <GridLayout
        className="layout"
        layout={layout}
        width={1200}
        gridConfig={{
          cols: COLS,
          rowHeight: ROW_HEIGHT,
          margin: MARGIN,
        }}
        dragConfig={{
          enabled: isEditing,
          handle: '.drag-handle',
        }}
        resizeConfig={{
          enabled: isEditing,
        }}
        onLayoutChange={handleLayoutChange}
      >
        {layout.map((item) => {
          const widget = widgetMap.get(item.i);
          if (!widget) return null;

          return (
            <div key={item.i} className={isEditing ? 'drag-handle cursor-move' : ''}>
              <WidgetCard
                widget={widget}
                isEditing={isEditing}
                autoRefresh={autoRefresh}
                refreshInterval={refreshInterval}
                onEdit={onWidgetEdit}
                onDelete={onWidgetDelete}
                onRefresh={onWidgetRefresh}
              />
            </div>
          );
        })}
      </GridLayout>
    </div>
  );
}

/**
 * Responsive Dashboard Grid - uses percentage-based width
 */
export function ResponsiveDashboardGrid({
  widgets,
  autoRefresh = false,
  refreshInterval = 60000,
}: {
  widgets: DashboardWidget[];
  autoRefresh?: boolean;
  refreshInterval?: number;
}) {
  if (widgets.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 border-2 border-dashed rounded-lg">
        <p className="text-muted-foreground">No widgets configured</p>
      </div>
    );
  }

  // Simple CSS grid layout for read-only view
  return (
    <div
      className="grid gap-4"
      style={{
        gridTemplateColumns: 'repeat(12, 1fr)',
      }}
    >
      {widgets.map((widget) => (
        <div
          key={widget.id}
          style={{
            gridColumn: `span ${widget.grid_w}`,
            gridRow: `span ${widget.grid_h}`,
            minHeight: `${widget.grid_h * 80}px`,
          }}
        >
          <WidgetCard
            widget={widget}
            isEditing={false}
            autoRefresh={autoRefresh}
            refreshInterval={refreshInterval}
          />
        </div>
      ))}
    </div>
  );
}
