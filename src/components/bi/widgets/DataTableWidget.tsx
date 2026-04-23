/**
 * Data Table Widget - displays tabular data
 */

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { DataTableConfig } from '@/types/bi';

interface DataTableWidgetProps {
  config: DataTableConfig;
  data: Record<string, unknown>[];
}

const formatValue = (
  value: unknown,
  format?: 'text' | 'number' | 'currency' | 'date' | 'percentage'
): string => {
  if (value === undefined || value === null) return '-';

  switch (format) {
    case 'currency':
      const num = Number(value) || 0;
      if (Math.abs(num) >= 10000000) {
        return `₹${(num / 10000000).toFixed(2)} Cr`;
      }
      if (Math.abs(num) >= 100000) {
        return `₹${(num / 100000).toFixed(2)} L`;
      }
      return `₹${num.toLocaleString('en-IN')}`;

    case 'number':
      return Number(value).toLocaleString('en-IN');

    case 'percentage':
      return `${Number(value).toFixed(2)}%`;

    case 'date':
      return new Date(value as string).toLocaleDateString('en-IN');

    default:
      return String(value);
  }
};

export function DataTableWidget({ config, data }: DataTableWidgetProps) {
  const pageSize = config.pageSize || 10;
  const displayData = data.slice(0, pageSize);

  return (
    <div className="h-full w-full overflow-auto p-2">
      <Table>
        <TableHeader>
          <TableRow>
            {config.columns.map((col) => (
              <TableHead
                key={col.key}
                style={{ width: col.width ? `${col.width}px` : undefined }}
                className={col.align === 'right' ? 'text-right' : col.align === 'center' ? 'text-center' : ''}
              >
                {col.header}
              </TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {displayData.length === 0 ? (
            <TableRow>
              <TableCell colSpan={config.columns.length} className="text-center text-muted-foreground">
                No data available
              </TableCell>
            </TableRow>
          ) : (
            displayData.map((row, rowIndex) => (
              <TableRow key={rowIndex}>
                {config.columns.map((col) => (
                  <TableCell
                    key={col.key}
                    className={col.align === 'right' ? 'text-right' : col.align === 'center' ? 'text-center' : ''}
                  >
                    {formatValue(row[col.key], col.format)}
                  </TableCell>
                ))}
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
      {data.length > pageSize && (
        <p className="text-xs text-muted-foreground text-center mt-2">
          Showing {pageSize} of {data.length} rows
        </p>
      )}
    </div>
  );
}
