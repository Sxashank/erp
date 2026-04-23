/**
 * CustomerPicker — searchable select for customer records.
 * See CLAUDE.md §5.1, §5.4.
 */

import { Check, ChevronsUpDown, Loader2, Search } from 'lucide-react';
import { useMemo, useState } from 'react';

import { Button } from '@/components/ui/button';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Input } from '@/components/ui/input';
import { cn } from '@/lib/utils';
import { useCustomer, useCustomers } from '@/hooks/ap_ar/useCustomers';

export interface CustomerPickerProps {
  value: string | null;
  onChange: (id: string | null) => void;
  placeholder?: string;
  disabled?: boolean;
  className?: string;
}

export function CustomerPicker({
  value,
  onChange,
  placeholder = 'Select customer…',
  disabled,
  className,
}: CustomerPickerProps): JSX.Element {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState('');

  const { data: list = [], isLoading, error } = useCustomers({ search });
  const { data: selected } = useCustomer(value);

  const filtered = useMemo(() => {
    if (!search) return list;
    const q = search.toLowerCase();
    return list.filter(
      (c) =>
        c.customer_name.toLowerCase().includes(q) ||
        c.customer_code.toLowerCase().includes(q),
    );
  }, [list, search]);

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          type="button"
          variant="outline"
          role="combobox"
          aria-expanded={open}
          disabled={disabled}
          className={cn('w-full justify-between font-normal', className)}
        >
          <span className="truncate text-left">
            {selected
              ? `${selected.customer_code} — ${selected.customer_name}`
              : placeholder}
          </span>
          <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" aria-hidden="true" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[var(--radix-popover-trigger-width)] p-0" align="start">
        <div className="flex items-center gap-2 border-b px-3 py-2">
          <Search className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
          <Input
            type="search"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by name or code"
            className="h-8 border-0 px-0 focus-visible:ring-0"
            autoFocus
          />
        </div>
        <ScrollArea className="max-h-72">
          {isLoading ? (
            <div className="flex items-center gap-2 px-3 py-4 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" /> Loading customers…
            </div>
          ) : error ? (
            <div className="px-3 py-4 text-sm text-destructive">Failed to load customers.</div>
          ) : filtered.length === 0 ? (
            <div className="px-3 py-4 text-sm text-muted-foreground">
              No customers match your search.
            </div>
          ) : (
            <ul role="listbox" className="py-1">
              {filtered.map((c) => {
                const isActive = c.id === value;
                return (
                  <li key={c.id}>
                    <button
                      type="button"
                      role="option"
                      aria-selected={isActive}
                      className={cn(
                        'flex w-full items-center gap-2 px-3 py-2 text-left text-sm hover:bg-muted',
                        isActive && 'bg-muted',
                      )}
                      onClick={() => {
                        onChange(c.id);
                        setOpen(false);
                      }}
                    >
                      <Check
                        className={cn(
                          'h-4 w-4 shrink-0',
                          isActive ? 'opacity-100' : 'opacity-0',
                        )}
                        aria-hidden="true"
                      />
                      <span className="truncate">
                        <span className="font-mono text-xs text-muted-foreground">
                          {c.customer_code}
                        </span>{' '}
                        {c.customer_name}
                      </span>
                    </button>
                  </li>
                );
              })}
            </ul>
          )}
        </ScrollArea>
      </PopoverContent>
    </Popover>
  );
}
