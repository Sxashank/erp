import * as React from "react"
import { format } from "date-fns"
import { Calendar as CalendarIcon } from "lucide-react"

import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"
import { Input } from "@/components/ui/input"

interface DatePickerProps {
  date?: Date | null;
  onSelect?: (date: Date | undefined) => void;
  placeholder?: string;
  disabled?: boolean;
  className?: string;
}

export function DatePicker({
  date,
  onSelect,
  placeholder = "Pick a date",
  disabled = false,
  className,
}: DatePickerProps) {
  const handleDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    if (value) {
      onSelect?.(new Date(value));
    } else {
      onSelect?.(undefined);
    }
  };

  return (
    <div className={cn("relative", className)}>
      <Input
        type="date"
        value={date ? format(date, "yyyy-MM-dd") : ""}
        onChange={handleDateChange}
        disabled={disabled}
        className="w-full"
        placeholder={placeholder}
      />
    </div>
  );
}

export function DateRangePicker({
  from,
  to,
  onFromChange,
  onToChange,
  className,
}: {
  from?: Date | null;
  to?: Date | null;
  onFromChange?: (date: Date | undefined) => void;
  onToChange?: (date: Date | undefined) => void;
  className?: string;
}) {
  return (
    <div className={cn("flex gap-2 items-center", className)}>
      <DatePicker date={from} onSelect={onFromChange} placeholder="From date" />
      <span className="text-muted-foreground">to</span>
      <DatePicker date={to} onSelect={onToChange} placeholder="To date" />
    </div>
  );
}
