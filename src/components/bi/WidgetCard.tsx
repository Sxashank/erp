/**
 * Widget Card - wrapper card for dashboard widgets
 */

import { MoreVertical, Edit, Trash2, RefreshCw, Maximize2 } from 'lucide-react';

import { WidgetRenderer } from './widgets/WidgetRenderer';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import type { DashboardWidget } from '@/types/bi';


interface WidgetCardProps {
  widget: DashboardWidget;
  isEditing?: boolean;
  autoRefresh?: boolean;
  refreshInterval?: number;
  onEdit?: (widget: DashboardWidget) => void;
  onDelete?: (widget: DashboardWidget) => void;
  onRefresh?: (widget: DashboardWidget) => void;
}

export function WidgetCard({
  widget,
  isEditing = false,
  autoRefresh = false,
  refreshInterval = 60000,
  onEdit,
  onDelete,
  onRefresh,
}: WidgetCardProps) {
  return (
    <Card className="h-full flex flex-col overflow-hidden">
      <CardHeader className="pb-2 flex-shrink-0">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium truncate">
            {widget.title}
          </CardTitle>
          {isEditing && (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" className="h-8 w-8">
                  <MoreVertical className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => onRefresh?.(widget)}>
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Refresh
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => onEdit?.(widget)}>
                  <Edit className="h-4 w-4 mr-2" />
                  Edit
                </DropdownMenuItem>
                <DropdownMenuItem
                  onClick={() => onDelete?.(widget)}
                  className="text-red-600"
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  Delete
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          )}
        </div>
      </CardHeader>
      <CardContent className="flex-1 overflow-hidden p-2">
        <WidgetRenderer
          widget={widget}
          autoRefresh={autoRefresh}
          refreshInterval={refreshInterval}
        />
      </CardContent>
    </Card>
  );
}
