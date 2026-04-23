/**
 * FormShell — canonical wrapper for edit/create pages. See CLAUDE.md §9.2.
 */

import { Card, CardContent } from '@/components/ui/card';
import { cn } from '@/lib/utils';

export interface FormShellProps {
  children: React.ReactNode;
  footer?: React.ReactNode;
  className?: string;
}

export function FormShell({ children, footer, className }: FormShellProps): JSX.Element {
  return (
    <div className={cn('space-y-6', className)}>
      <Card>
        <CardContent className="pt-6">{children}</CardContent>
      </Card>
      {footer && (
        <div className="sticky bottom-0 -mx-6 border-t bg-background/95 px-6 py-3 backdrop-blur">
          <div className="flex items-center justify-end gap-2">{footer}</div>
        </div>
      )}
    </div>
  );
}

/**
 * FormSection — logical grouping of fields inside a FormShell.
 */
export interface FormSectionProps {
  title: string;
  description?: string;
  children: React.ReactNode;
  className?: string;
}

export function FormSection({
  title,
  description,
  children,
  className,
}: FormSectionProps): JSX.Element {
  return (
    <section className={cn('space-y-4 border-b pb-6 last:border-b-0 last:pb-0', className)}>
      <div>
        <h2 className="text-base font-semibold">{title}</h2>
        {description && (
          <p className="mt-0.5 text-sm text-muted-foreground">{description}</p>
        )}
      </div>
      <div className="grid gap-4 md:grid-cols-2">{children}</div>
    </section>
  );
}
