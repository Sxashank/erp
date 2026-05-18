import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import type { AssetStatus } from '@/types/fixed-assets';

const statusClasses: Record<AssetStatus, string> = {
  DRAFT: 'bg-slate-100 text-slate-700 border-slate-300',
  ACTIVE: 'bg-emerald-100 text-emerald-700 border-emerald-300',
  DISPOSED: 'bg-red-100 text-red-700 border-red-300',
  TRANSFERRED: 'bg-blue-100 text-blue-700 border-blue-300',
  UNDER_MAINTENANCE: 'bg-amber-100 text-amber-700 border-amber-300',
  FULLY_DEPRECIATED: 'bg-violet-100 text-violet-700 border-violet-300',
};

function formatStatus(status: string): string {
  return status.replace(/_/g, ' ').replace(/\b\w/g, (char) => char.toUpperCase());
}

export function FixedAssetStatusPill({
  status,
  className,
}: {
  status: AssetStatus;
  className?: string;
}): JSX.Element {
  return (
    <Badge
      variant="outline"
      className={cn('border font-medium', statusClasses[status], className)}
    >
      {formatStatus(status)}
    </Badge>
  );
}
