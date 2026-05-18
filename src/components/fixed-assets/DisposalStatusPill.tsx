import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import type { DisposalRegisterStatus } from '@/types/fixed-assets';

const statusClasses: Record<DisposalRegisterStatus, string> = {
  COMPLETED: 'bg-emerald-100 text-emerald-700 border-emerald-300',
  PENDING_APPROVAL: 'bg-amber-100 text-amber-700 border-amber-300',
  REJECTED: 'bg-red-100 text-red-700 border-red-300',
  RETURNED: 'bg-orange-100 text-orange-700 border-orange-300',
  CANCELLED: 'bg-slate-100 text-slate-700 border-slate-300',
};

export function DisposalStatusPill({
  status,
  className,
}: {
  status: DisposalRegisterStatus;
  className?: string;
}): JSX.Element {
  return (
    <Badge
      variant="outline"
      className={cn('border font-medium', statusClasses[status], className)}
    >
      {status.replace(/_/g, ' ')}
    </Badge>
  );
}
