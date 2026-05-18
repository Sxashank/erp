/**
 * EntityCard Component
 * Compact entity/borrower summary card
 */

import { RatingBadge } from './RatingBadge';
import { EntityStatusBadge } from './StatusBadge';

import { Card, CardContent } from '@/components/ui/card';
import { cn } from '@/lib/utils';
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
          'flex items-center gap-3 rounded-lg border p-3 transition-colors',
          onClick && 'cursor-pointer hover:bg-accent',
          selected && 'border-primary bg-primary/5',
          className,
        )}
        onClick={onClick}
      >
        <div className="min-w-0 flex-1">
          <p className="truncate font-medium">{entity.legalName}</p>
          <p className="text-sm text-muted-foreground">{entity.entityCode}</p>
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
          className,
        )}
        onClick={onClick}
      >
        <CardContent className="p-4">
          <div className="mb-3 flex items-start justify-between">
            <div>
              <h3 className="text-lg font-semibold">{entity.legalName}</h3>
              <p className="text-sm text-muted-foreground">{entity.entityCode}</p>
            </div>
            <EntityStatusBadge status={entity.status} />
          </div>

          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-muted-foreground">Entity Type</p>
              <p className="font-medium">{formatEntityType(entity.entityType)}</p>
            </div>
            <div>
              <p className="text-muted-foreground">PAN</p>
              <p className="font-mono font-medium">{entity.pan}</p>
            </div>
            {entity.cin && (
              <div>
                <p className="text-muted-foreground">CIN</p>
                <p className="font-mono text-xs font-medium">{entity.cin}</p>
              </div>
            )}
            <div>
              <p className="text-muted-foreground">Credit Rating</p>
              {entity.internalRating ? (
                <RatingBadge rating={entity.internalRating} size="sm" />
              ) : (
                <span className="text-muted-foreground">Not Rated</span>
              )}
            </div>
            {entity.relationshipManagerName && (
              <div className="col-span-2">
                <p className="text-muted-foreground">Relationship Manager</p>
                <p className="font-medium">{entity.relationshipManagerName}</p>
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
        className,
      )}
      onClick={onClick}
    >
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div className="min-w-0 flex-1">
            <h3 className="truncate font-medium">{entity.legalName}</h3>
            <p className="text-sm text-muted-foreground">{entity.entityCode}</p>
            <div className="mt-2 flex items-center gap-2">
              <span className="text-xs text-muted-foreground">
                {formatEntityType(entity.entityType)}
              </span>
              <span className="text-muted-foreground">·</span>
              <span className="font-mono text-xs">{entity.pan}</span>
            </div>
          </div>
          <div className="flex flex-col items-end gap-2">
            <EntityStatusBadge status={entity.status} size="sm" />
            {entity.internalRating && <RatingBadge rating={entity.internalRating} size="sm" />}
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
  return <EntityCard entity={entity} variant="compact" selected={selected} onClick={onSelect} />;
}

/**
 * Mini entity reference (for inline display)
 */
export function EntityReference({
  entity,
  className,
}: {
  entity: Pick<Entity, 'legalName' | 'entityCode'>;
  className?: string;
}) {
  return (
    <div className={cn('inline-flex items-center gap-1', className)}>
      <span className="font-medium">{entity.legalName}</span>
      <span className="text-sm text-muted-foreground">({entity.entityCode})</span>
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
