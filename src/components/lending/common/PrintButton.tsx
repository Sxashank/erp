/**
 * PrintButton Component
 * Print functionality for documents/reports
 */

import * as React from 'react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';

export interface PrintButtonProps {
  contentId?: string;
  title?: string;
  className?: string;
  variant?: 'default' | 'outline' | 'ghost';
  size?: 'default' | 'sm' | 'lg' | 'icon';
  children?: React.ReactNode;
}

export function PrintButton({
  contentId,
  title = 'Document',
  className,
  variant = 'outline',
  size = 'default',
  children,
}: PrintButtonProps) {
  const handlePrint = () => {
    if (contentId) {
      // Print specific element
      const element = document.getElementById(contentId);
      if (!element) {
        console.error(`Element with id "${contentId}" not found`);
        return;
      }

      const printWindow = window.open('', '_blank');
      if (!printWindow) {
        alert('Please allow popups to print');
        return;
      }

      // Get all stylesheets
      const styles = Array.from(document.styleSheets)
        .map((styleSheet) => {
          try {
            return Array.from(styleSheet.cssRules)
              .map((rule) => rule.cssText)
              .join('\n');
          } catch {
            // External stylesheets may throw security errors
            if (styleSheet.href) {
              return `@import url("${styleSheet.href}");`;
            }
            return '';
          }
        })
        .join('\n');

      printWindow.document.write(`
        <!DOCTYPE html>
        <html>
        <head>
          <title>${title}</title>
          <style>
            ${styles}
            @media print {
              body {
                print-color-adjust: exact;
                -webkit-print-color-adjust: exact;
              }
              @page {
                size: A4;
                margin: 15mm;
              }
            }
            body {
              font-family: system-ui, -apple-system, sans-serif;
              padding: 20px;
            }
          </style>
        </head>
        <body>
          ${element.innerHTML}
        </body>
        </html>
      `);

      printWindow.document.close();
      printWindow.focus();

      // Wait for styles to load
      setTimeout(() => {
        printWindow.print();
        printWindow.close();
      }, 250);
    } else {
      // Print entire page
      window.print();
    }
  };

  return (
    <Button
      type="button"
      variant={variant}
      size={size}
      onClick={handlePrint}
      className={cn('gap-2', className)}
    >
      <svg
        className="w-4 h-4"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z"
        />
      </svg>
      {children || 'Print'}
    </Button>
  );
}

/**
 * Print icon button (compact)
 */
export function PrintIconButton({
  contentId,
  title,
  className,
}: {
  contentId?: string;
  title?: string;
  className?: string;
}) {
  return (
    <PrintButton
      contentId={contentId}
      title={title}
      variant="ghost"
      size="icon"
      className={className}
    >
      <span className="sr-only">Print</span>
    </PrintButton>
  );
}

/**
 * Printable container wrapper
 * Applies print-specific styles
 */
export function PrintableContainer({
  children,
  className,
  id,
  hideOnScreen = false,
}: {
  children: React.ReactNode;
  className?: string;
  id?: string;
  hideOnScreen?: boolean;
}) {
  return (
    <div
      id={id}
      className={cn(
        'print:block print:p-0 print:m-0 print:shadow-none',
        hideOnScreen && 'hidden print:block',
        className
      )}
    >
      {children}
    </div>
  );
}

/**
 * Element that only appears when printing
 */
export function PrintOnly({ children, className }: { children: React.ReactNode; className?: string }) {
  return <div className={cn('hidden print:block', className)}>{children}</div>;
}

/**
 * Element that is hidden when printing
 */
export function NoPrint({ children, className }: { children: React.ReactNode; className?: string }) {
  return <div className={cn('print:hidden', className)}>{children}</div>;
}

/**
 * Print header with logo and date
 */
export function PrintHeader({
  title,
  subtitle,
  logo,
  showDate = true,
  className,
}: {
  title: string;
  subtitle?: string;
  logo?: React.ReactNode;
  showDate?: boolean;
  className?: string;
}) {
  return (
    <PrintOnly className={cn('mb-6', className)}>
      <div className="flex items-start justify-between border-b pb-4">
        <div className="flex items-center gap-4">
          {logo && <div className="w-16 h-16">{logo}</div>}
          <div>
            <h1 className="text-xl font-bold">{title}</h1>
            {subtitle && <p className="text-sm text-muted-foreground">{subtitle}</p>}
          </div>
        </div>
        {showDate && (
          <div className="text-right text-sm text-muted-foreground">
            <p>Generated on</p>
            <p className="font-medium">{new Date().toLocaleDateString('en-IN', {
              day: '2-digit',
              month: 'short',
              year: 'numeric',
              hour: '2-digit',
              minute: '2-digit',
            })}</p>
          </div>
        )}
      </div>
    </PrintOnly>
  );
}
