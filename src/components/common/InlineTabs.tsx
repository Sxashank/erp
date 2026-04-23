/**
 * InlineTabs — shadcn tabs wrapper with a consistent URL-param sync option.
 * See CLAUDE.md §9.2.
 */

import { useSearchParams } from 'react-router-dom';

import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { cn } from '@/lib/utils';

export interface TabItem {
  value: string;
  label: React.ReactNode;
  content: React.ReactNode;
  disabled?: boolean;
}

export interface InlineTabsProps {
  tabs: TabItem[];
  defaultValue?: string;
  /** URL query param used to persist the active tab. */
  paramName?: string;
  className?: string;
  listClassName?: string;
}

export function InlineTabs({
  tabs,
  defaultValue,
  paramName,
  className,
  listClassName,
}: InlineTabsProps): JSX.Element {
  const [params, setParams] = useSearchParams();
  const initial = defaultValue ?? tabs[0]?.value ?? '';
  const active = paramName ? (params.get(paramName) ?? initial) : undefined;

  return (
    <Tabs
      {...(paramName
        ? {
            value: active,
            onValueChange: (v: string) => {
              const next = new URLSearchParams(params);
              next.set(paramName, v);
              setParams(next, { replace: true });
            },
          }
        : { defaultValue: initial })}
      className={cn('w-full', className)}
    >
      <TabsList className={cn('mb-4', listClassName)}>
        {tabs.map((t) => (
          <TabsTrigger key={t.value} value={t.value} disabled={t.disabled}>
            {t.label}
          </TabsTrigger>
        ))}
      </TabsList>
      {tabs.map((t) => (
        <TabsContent key={t.value} value={t.value}>
          {t.content}
        </TabsContent>
      ))}
    </Tabs>
  );
}
