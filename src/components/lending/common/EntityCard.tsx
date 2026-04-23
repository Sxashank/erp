/**
 * EntityCard Component
 * Compact entity/borrower summary card
 */

import { cn } from '@/lib/utils';
import { Card, CardContent } from '@/components/ui/card';
import { EntityStatusBadge } from './StatusBadge';
import { RatingBadge } from './RatingBadge';
import type { Entity } from '@/types/lending';

export interface EntityCardProps {
  entity: Entity;
  className?: string;
  variant?: 'default' | 'compact' | 'detailed';
  onClick?: () => void;
  selected?: boolean;
}

export function EntityCard({
  entity,
  className,
  variant = 'default',
  onClick,
  selected = false,
}: EntityCardProps) {
  if (variant === 'compact') {
    return (
      <div
        className={cn(
          'flex items-center gap-3 p-3 rounded-lg border transition-colors',
          onClick && 'cursor-pointer hover:bg-accent',
          selected && 'border-primary bg-primary/5',
          className
        )}
        onClick={onClick}
      >
        <div className="flex-1 min-w-0">
          <p className="font-medium truncate">{entity.legal_name}</p>
          <p className="text-sm text-muted-foreground">{entity.entity_code}</p>
        </div>
        <EntityStatusBadge status={entity.status} size="sm" />
      </div>
    );
  }

  if (variant === 'detailed') {
    return (
      <Card
        className={cn(
          'transition-colors',
          onClick && 'cursor-pointer hover:shadow-md',
          selected && 'ring-2 ring-primary',
          className
        )}
        onClick={onClick}
      >
        <CardContent className="p-4">
          <div className="flex items-start justify-between mb-3">
            <div>
              <h3 className="font-semibold text-lg">{entity.legal_name}</h3>
              <p className="text-sm text-muted-foreground">{entity.entity_code}</p>
            </div>
            <EntityStatusBadge status={entity.status} />
          </div>

          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-muted-foreground">Entity Type</p>
              <p className="font-medium">{formatEntityType(entity.entity_type)}</p>
            </div>
            <div>
              <p className="text-muted-foreground">PAN</p>
              <p className="font-medium font-mono">{entity.pan}</p>
            </div>
            {entity.cin && (
              <div>
                <p className="text-muted-foreground">CIN</p>
                <p className="font-medium font-mono text-xs">{entity.cin}</p>
              </div>
            )}
            <div>
              <p className="text-muted-foreground">Credit Rating</p>
              {entity.internal_rating ? (
                <RatingBadge rating={entity.internal_rating} size="sm" />
              ) : (
                <span className="text-muted-foreground">Not Rated</span>
              )}
            </div>
            {entity.relationship_manager_name && (
              <div className="col-span-2">
                <p className="text-muted-foreground">Relationship Manager</p>
                <p className="font-medium">{entity.relationship_manager_name}</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    );
  }

  // Default variant
  return (
    <Card
      className={cn(
        'transition-colors',
        onClick && 'cursor-pointer hover:shadow-md',
        selected && 'ring-2 ring-primary',
        className
      )}
      onClick={onClick}
    >
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <h3 className="font-medium truncate">{entity.legal_name}</h3>
            <p className="text-sm text-muted-foreground">{entity.entity_code}</p>
            <div className="flex items-center gap-2 mt-2">
              <span className="text-xs text-muted-foreground">{formatEntityType(entity.entity_type)}</span>
              <span className="text-muted-foreground">·</span>
              <span className="text-xs font-mono">{entity.pan}</span>
            </div>
          </div>
          <div className="flex flex-col items-end gap-2">
            <EntityStatusBadge status={entity.status} size="sm" />
            {entity.internal_rating && (
              <RatingBadge rating={entity.internal_rating} size="sm" />
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * Entity search/select item
 */
export function EntitySelectItem({
  entity,
  selected,
  onSelect,
}: {
  entity: Entity;
  selected?: boolean;
  onSelect?: () => void;
}) {
  return (
    <EntityCard
      entity={entity}
      variant="compact"
      selected={selected}
      onClick={onSelect}
    />
  );
}

/**
 * Mini entity reference (for inline display)
 */
export function EntityReference({
  entity,
  className,
}: {
  entity: Pick<Entity, 'legal_name' | 'entity_code'>;
  className?: string;
}) {
  return (
    <div className={cn('inline-flex items-center gap-1', className)}>
      <span className="font-medium">{entity.legal_name}</span>
      <span className="text-muted-foreground text-sm">({entity.entity_code})</span>
    </div>
  );
}

function formatEntityType(type: string): string {
  const typeMap: Record<string, string> = {
    CORPORATE: 'Corporate',
    INDIVIDUAL: 'Individual',
    LLP: 'LLP',
    PARTNERSHIP: 'Partnership',
    TRUST: 'Trust',
    HUF: 'HUF',
  };
  return typeMap[type] || type;
}
