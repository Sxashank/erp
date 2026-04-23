/**
 * Export utilities for generating Excel and PDF files from report data.
 *
 * Excel export uses exceljs (replaced xlsx in STAGE-8-PENDING-xlsx-replacement
 * closure — xlsx carried two unfixable high-sev advisories: CVE prototype
 * pollution and a ReDoS).
 */

import ExcelJS from 'exceljs';
import { jsPDF } from 'jspdf';
import autoTable from 'jspdf-autotable';

// Type for table data
interface TableColumn {
  header: string;
  key: string;
  align?: 'left' | 'center' | 'right';
  format?: 'currency' | 'date' | 'number' | 'text';
}

interface ExportOptions {
  filename: string;
  title: string;
  subtitle?: string;
  organization?: string;
  period?: string;
  columns: TableColumn[];
  data: Record<string, any>[];
  totals?: Record<string, any>;
  generatedAt?: string;
}

/**
 * Format a value based on the specified format type
 */
const formatValue = (value: any, format?: string): string => {
  if (value === null || value === undefined) return '-';

  switch (format) {
    case 'currency':
      return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        minimumFractionDigits: 2,
      }).format(Number(value));
    case 'date':
      return new Date(value).toLocaleDateString('en-IN', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
      });
    case 'number':
      return new Intl.NumberFormat('en-IN').format(Number(value));
    default:
      return String(value);
  }
};

type CellValue = string | number | null | undefined;

/**
 * Trigger a browser download for an in-memory workbook.
 *
 * Why Blob-and-anchor instead of `workbook.xlsx.writeFile`: `writeFile` only
 * exists in the Node build of exceljs. In the browser we must buffer-and-save.
 */
const downloadWorkbook = async (wb: ExcelJS.Workbook, filename: string): Promise<void> => {
  const buffer = await wb.xlsx.writeBuffer();
  const blob = new Blob([buffer as ArrayBuffer], {
    type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename.endsWith('.xlsx') ? filename : `${filename}.xlsx`;
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  URL.revokeObjectURL(url);
};

/**
 * Populate an exceljs worksheet from a 2D array + apply column widths.
 * Widths are in characters (exceljs uses the same unit as xlsx `wch`).
 */
const applySheet = (
  ws: ExcelJS.Worksheet,
  rows: CellValue[][],
  columnCharWidths?: number[]
): void => {
  rows.forEach((row) => {
    ws.addRow(row);
  });
  if (columnCharWidths) {
    columnCharWidths.forEach((width, idx) => {
      ws.getColumn(idx + 1).width = width;
    });
  }
};

/**
 * Export data to Excel format
 */
export const exportToExcel = async (options: ExportOptions): Promise<void> => {
  const { filename, title, subtitle, organization, period, columns, data, totals, generatedAt } = options;

  // Create worksheet data
  const wsData: CellValue[][] = [];

  // Add header rows
  if (organization) {
    wsData.push([organization]);
    wsData.push([]);
  }
  wsData.push([title]);
  if (subtitle) {
    wsData.push([subtitle]);
  }
  if (period) {
    wsData.push([period]);
  }
  wsData.push([]);

  // Add column headers
  wsData.push(columns.map((col) => col.header));

  // Add data rows
  data.forEach((row) => {
    wsData.push(
      columns.map((col) => {
        const value = row[col.key];
        if (col.format === 'currency' || col.format === 'number') {
          return typeof value === 'number' ? value : 0;
        }
        return formatValue(value, col.format);
      })
    );
  });

  // Add totals row if provided
  if (totals) {
    wsData.push(
      columns.map((col) => {
        const value = totals[col.key];
        if (value !== undefined) {
          if (col.format === 'currency' || col.format === 'number') {
            return typeof value === 'number' ? value : 0;
          }
          return formatValue(value, col.format);
        }
        return '';
      })
    );
  }

  // Add footer
  wsData.push([]);
  if (generatedAt) {
    wsData.push([`Generated on: ${new Date(generatedAt).toLocaleString('en-IN')}`]);
  }

  // Create workbook + sheet with column widths, then stream to browser.
  const wb = new ExcelJS.Workbook();
  const ws = wb.addWorksheet('Report');
  const colWidths = columns.map((col) => Math.max(col.header.length, 15));
  applySheet(ws, wsData, colWidths);
  await downloadWorkbook(wb, filename);
};

/**
 * Export data to PDF format
 */
export const exportToPDF = (options: ExportOptions): void => {
  const { filename, title, subtitle, organization, period, columns, data, totals, generatedAt } = options;

  // Create PDF document (A4 landscape for reports with many columns)
  const doc = new jsPDF({
    orientation: columns.length > 5 ? 'landscape' : 'portrait',
    unit: 'mm',
    format: 'a4',
  });

  let yPosition = 15;

  // Add organization name
  if (organization) {
    doc.setFontSize(16);
    doc.setFont('helvetica', 'bold');
    doc.text(organization, doc.internal.pageSize.getWidth() / 2, yPosition, { align: 'center' });
    yPosition += 8;
  }

  // Add title
  doc.setFontSize(14);
  doc.setFont('helvetica', 'bold');
  doc.text(title, doc.internal.pageSize.getWidth() / 2, yPosition, { align: 'center' });
  yPosition += 6;

  // Add subtitle
  if (subtitle) {
    doc.setFontSize(10);
    doc.setFont('helvetica', 'normal');
    doc.text(subtitle, doc.internal.pageSize.getWidth() / 2, yPosition, { align: 'center' });
    yPosition += 5;
  }

  // Add period
  if (period) {
    doc.setFontSize(10);
    doc.setFont('helvetica', 'normal');
    doc.text(period, doc.internal.pageSize.getWidth() / 2, yPosition, { align: 'center' });
    yPosition += 8;
  }

  // Prepare table headers
  const headers = columns.map((col) => col.header);

  // Prepare table body
  const body = data.map((row) =>
    columns.map((col) => formatValue(row[col.key], col.format))
  );

  // Add totals row if provided
  if (totals) {
    body.push(
      columns.map((col) => {
        const value = totals[col.key];
        if (value !== undefined) {
          return formatValue(value, col.format);
        }
        return '';
      })
    );
  }

  // Column alignments
  const columnStyles: Record<number, { halign: 'left' | 'center' | 'right' }> = {};
  columns.forEach((col, index) => {
    columnStyles[index] = {
      halign: col.align || (col.format === 'currency' || col.format === 'number' ? 'right' : 'left'),
    };
  });

  // Generate table
  autoTable(doc, {
    head: [headers],
    body: body,
    startY: yPosition,
    styles: {
      fontSize: 8,
      cellPadding: 2,
    },
    headStyles: {
      fillColor: [71, 85, 105], // slate-600
      textColor: [255, 255, 255],
      fontStyle: 'bold',
    },
    alternateRowStyles: {
      fillColor: [248, 250, 252], // slate-50
    },
    columnStyles: columnStyles,
    // Style the totals row (last row if totals provided)
    didParseCell: (data) => {
      if (totals && data.row.index === body.length - 1) {
        data.cell.styles.fillColor = [226, 232, 240]; // slate-200
        data.cell.styles.fontStyle = 'bold';
      }
    },
  });

  // Add footer
  const pageHeight = doc.internal.pageSize.getHeight();
  doc.setFontSize(8);
  doc.setFont('helvetica', 'normal');
  doc.setTextColor(100);

  if (generatedAt) {
    doc.text(
      `Generated on: ${new Date(generatedAt).toLocaleString('en-IN')}`,
      14,
      pageHeight - 10
    );
  }

  // Add page numbers
  const pageCount = doc.getNumberOfPages();
  for (let i = 1; i <= pageCount; i++) {
    doc.setPage(i);
    doc.text(
      `Page ${i} of ${pageCount}`,
      doc.internal.pageSize.getWidth() - 30,
      pageHeight - 10
    );
  }

  // Save the PDF
  doc.save(`${filename}.pdf`);
};

/**
 * Export Trial Balance to Excel
 */
export const exportTrialBalanceToExcel = (reportData: any): Promise<void> => {
  return exportToExcel({
    filename: `Trial_Balance_${reportData.organization_name}_${reportData.to_date}`,
    title: 'Trial Balance',
    organization: reportData.organization_name,
    period: `For the period ${new Date(reportData.from_date).toLocaleDateString('en-IN')} to ${new Date(reportData.to_date).toLocaleDateString('en-IN')}`,
    columns: [
      { header: 'Code', key: 'account_code', align: 'left' },
      { header: 'Account Name', key: 'account_name', align: 'left' },
      { header: 'Group', key: 'account_group_name', align: 'left' },
      { header: 'Opening Dr', key: 'opening_debit', format: 'currency', align: 'right' },
      { header: 'Opening Cr', key: 'opening_credit', format: 'currency', align: 'right' },
      { header: 'Period Dr', key: 'period_debit', format: 'currency', align: 'right' },
      { header: 'Period Cr', key: 'period_credit', format: 'currency', align: 'right' },
      { header: 'Closing Dr', key: 'closing_debit', format: 'currency', align: 'right' },
      { header: 'Closing Cr', key: 'closing_credit', format: 'currency', align: 'right' },
    ],
    data: reportData.items,
    totals: {
      account_code: 'TOTAL',
      opening_debit: reportData.total_opening_debit,
      opening_credit: reportData.total_opening_credit,
      period_debit: reportData.total_period_debit,
      period_credit: reportData.total_period_credit,
      closing_debit: reportData.total_closing_debit,
      closing_credit: reportData.total_closing_credit,
    },
    generatedAt: reportData.generated_at,
  });
};

/**
 * Export Trial Balance to PDF
 */
export const exportTrialBalanceToPDF = (reportData: any): void => {
  exportToPDF({
    filename: `Trial_Balance_${reportData.organization_name}_${reportData.to_date}`,
    title: 'Trial Balance',
    organization: reportData.organization_name,
    period: `For the period ${new Date(reportData.from_date).toLocaleDateString('en-IN')} to ${new Date(reportData.to_date).toLocaleDateString('en-IN')}`,
    columns: [
      { header: 'Code', key: 'account_code', align: 'left' },
      { header: 'Account Name', key: 'account_name', align: 'left' },
      { header: 'Group', key: 'account_group_name', align: 'left' },
      { header: 'Opening Dr', key: 'opening_debit', format: 'currency', align: 'right' },
      { header: 'Opening Cr', key: 'opening_credit', format: 'currency', align: 'right' },
      { header: 'Closing Dr', key: 'closing_debit', format: 'currency', align: 'right' },
      { header: 'Closing Cr', key: 'closing_credit', format: 'currency', align: 'right' },
    ],
    data: reportData.items,
    totals: {
      account_code: 'TOTAL',
      opening_debit: reportData.total_opening_debit,
      opening_credit: reportData.total_opening_credit,
      closing_debit: reportData.total_closing_debit,
      closing_credit: reportData.total_closing_credit,
    },
    generatedAt: reportData.generated_at,
  });
};

/**
 * Export Account Ledger to Excel
 */
export const exportAccountLedgerToExcel = (reportData: any): Promise<void> => {
  return exportToExcel({
    filename: `Account_Ledger_${reportData.account_code}_${reportData.to_date}`,
    title: 'Account Ledger',
    subtitle: `${reportData.account_code} - ${reportData.account_name}`,
    organization: reportData.organization_name,
    period: `For the period ${new Date(reportData.from_date).toLocaleDateString('en-IN')} to ${new Date(reportData.to_date).toLocaleDateString('en-IN')}`,
    columns: [
      { header: 'Date', key: 'voucher_date', format: 'date', align: 'left' },
      { header: 'Voucher No.', key: 'voucher_number', align: 'left' },
      { header: 'Type', key: 'voucher_type', align: 'left' },
      { header: 'Narration', key: 'narration', align: 'left' },
      { header: 'Debit', key: 'debit_amount', format: 'currency', align: 'right' },
      { header: 'Credit', key: 'credit_amount', format: 'currency', align: 'right' },
      { header: 'Balance', key: 'running_balance', format: 'currency', align: 'right' },
      { header: 'Type', key: 'balance_type', align: 'center' },
    ],
    data: reportData.entries,
    totals: {
      voucher_date: 'TOTAL',
      debit_amount: reportData.total_debit,
      credit_amount: reportData.total_credit,
      running_balance: reportData.closing_balance,
      balance_type: reportData.closing_balance_type,
    },
    generatedAt: reportData.generated_at,
  });
};

/**
 * Export Account Ledger to PDF
 */
export const exportAccountLedgerToPDF = (reportData: any): void => {
  exportToPDF({
    filename: `Account_Ledger_${reportData.account_code}_${reportData.to_date}`,
    title: 'Account Ledger',
    subtitle: `${reportData.account_code} - ${reportData.account_name}`,
    organization: reportData.organization_name,
    period: `For the period ${new Date(reportData.from_date).toLocaleDateString('en-IN')} to ${new Date(reportData.to_date).toLocaleDateString('en-IN')}`,
    columns: [
      { header: 'Date', key: 'voucher_date', format: 'date', align: 'left' },
      { header: 'Voucher No.', key: 'voucher_number', align: 'left' },
      { header: 'Type', key: 'voucher_type', align: 'left' },
      { header: 'Narration', key: 'narration', align: 'left' },
      { header: 'Debit', key: 'debit_amount', format: 'currency', align: 'right' },
      { header: 'Credit', key: 'credit_amount', format: 'currency', align: 'right' },
      { header: 'Balance', key: 'running_balance', format: 'currency', align: 'right' },
    ],
    data: reportData.entries,
    totals: {
      voucher_date: 'TOTAL',
      debit_amount: reportData.total_debit,
      credit_amount: reportData.total_credit,
      running_balance: reportData.closing_balance,
    },
    generatedAt: reportData.generated_at,
  });
};

/**
 * Export Day Book to Excel
 */
export const exportDayBookToExcel = (reportData: any): Promise<void> => {
  return exportToExcel({
    filename: `Day_Book_${reportData.organization_name}_${reportData.to_date}`,
    title: 'Day Book / Journal Register',
    organization: reportData.organization_name,
    period: `From ${new Date(reportData.from_date).toLocaleDateString('en-IN')} to ${new Date(reportData.to_date).toLocaleDateString('en-IN')}`,
    columns: [
      { header: 'Date', key: 'voucher_date', format: 'date', align: 'left' },
      { header: 'Voucher No.', key: 'voucher_number', align: 'left' },
      { header: 'Type', key: 'voucher_type', align: 'left' },
      { header: 'Narration', key: 'narration', align: 'left' },
      { header: 'Lines', key: 'line_count', format: 'number', align: 'center' },
      { header: 'Debit', key: 'total_debit', format: 'currency', align: 'right' },
      { header: 'Credit', key: 'total_credit', format: 'currency', align: 'right' },
    ],
    data: reportData.entries,
    totals: {
      voucher_date: `TOTAL (${reportData.total_vouchers} vouchers)`,
      total_debit: reportData.total_debit,
      total_credit: reportData.total_credit,
    },
    generatedAt: reportData.generated_at,
  });
};

/**
 * Export Day Book to PDF
 */
export const exportDayBookToPDF = (reportData: any): void => {
  exportToPDF({
    filename: `Day_Book_${reportData.organization_name}_${reportData.to_date}`,
    title: 'Day Book / Journal Register',
    organization: reportData.organization_name,
    period: `From ${new Date(reportData.from_date).toLocaleDateString('en-IN')} to ${new Date(reportData.to_date).toLocaleDateString('en-IN')}`,
    columns: [
      { header: 'Date', key: 'voucher_date', format: 'date', align: 'left' },
      { header: 'Voucher No.', key: 'voucher_number', align: 'left' },
      { header: 'Type', key: 'voucher_type', align: 'left' },
      { header: 'Narration', key: 'narration', align: 'left' },
      { header: 'Debit', key: 'total_debit', format: 'currency', align: 'right' },
      { header: 'Credit', key: 'total_credit', format: 'currency', align: 'right' },
    ],
    data: reportData.entries,
    totals: {
      voucher_date: `TOTAL (${reportData.total_vouchers})`,
      total_debit: reportData.total_debit,
      total_credit: reportData.total_credit,
    },
    generatedAt: reportData.generated_at,
  });
};

/**
 * Export Cash Flow Statement to PDF (custom format for cash flow)
 */
export const exportCashFlowToPDF = (reportData: any): void => {
  const doc = new jsPDF({
    orientation: 'portrait',
    unit: 'mm',
    format: 'a4',
  });

  const pageWidth = doc.internal.pageSize.getWidth();
  let yPosition = 15;

  const formatCurrency = (amount: number) =>
    new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 2,
    }).format(Math.abs(amount));

  // Header
  doc.setFontSize(16);
  doc.setFont('helvetica', 'bold');
  doc.text(reportData.organization_name, pageWidth / 2, yPosition, { align: 'center' });
  yPosition += 8;

  doc.setFontSize(14);
  doc.text('Cash Flow Statement', pageWidth / 2, yPosition, { align: 'center' });
  yPosition += 6;

  doc.setFontSize(10);
  doc.setFont('helvetica', 'normal');
  doc.text(
    `For the period ${new Date(reportData.from_date).toLocaleDateString('en-IN')} to ${new Date(reportData.to_date).toLocaleDateString('en-IN')}`,
    pageWidth / 2,
    yPosition,
    { align: 'center' }
  );
  yPosition += 5;
  doc.text('(Prepared using Indirect Method)', pageWidth / 2, yPosition, { align: 'center' });
  yPosition += 10;

  // Helper function to render a section
  const renderSection = (section: any) => {
    doc.setFillColor(241, 245, 249); // slate-100
    doc.rect(14, yPosition - 4, pageWidth - 28, 8, 'F');
    doc.setFontSize(11);
    doc.setFont('helvetica', 'bold');
    doc.text(section.section_name, 16, yPosition);
    yPosition += 8;

    doc.setFont('helvetica', 'normal');
    doc.setFontSize(9);

    section.items.forEach((item: any) => {
      if (item.is_subtotal) {
        doc.setFont('helvetica', 'bold');
        doc.setFillColor(226, 232, 240); // slate-200
        doc.rect(14, yPosition - 3, pageWidth - 28, 6, 'F');
      }

      doc.text(item.label, 20, yPosition);
      const amountText = item.amount < 0 ? `(${formatCurrency(item.amount)})` : formatCurrency(item.amount);
      doc.text(amountText, pageWidth - 20, yPosition, { align: 'right' });
      yPosition += 5;

      doc.setFont('helvetica', 'normal');
    });

    // Net Cash Flow for section
    doc.setFont('helvetica', 'bold');
    doc.setFillColor(71, 85, 105); // slate-600
    doc.setTextColor(255, 255, 255);
    doc.rect(14, yPosition - 3, pageWidth - 28, 7, 'F');
    doc.text(`Net Cash from ${section.section_name.replace('Cash Flow from ', '')}`, 20, yPosition + 1);
    const netText = section.net_cash_flow < 0 ? `(${formatCurrency(section.net_cash_flow)})` : formatCurrency(section.net_cash_flow);
    doc.text(netText, pageWidth - 20, yPosition + 1, { align: 'right' });
    doc.setTextColor(0, 0, 0);
    yPosition += 12;
  };

  // Render sections
  renderSection(reportData.operating_activities);
  renderSection(reportData.investing_activities);
  renderSection(reportData.financing_activities);

  // Summary
  yPosition += 5;
  doc.setFillColor(30, 41, 59); // slate-800
  doc.setTextColor(255, 255, 255);
  doc.rect(14, yPosition - 4, pageWidth - 28, 30, 'F');

  doc.setFontSize(10);
  doc.setFont('helvetica', 'bold');
  doc.text('Summary', 20, yPosition + 2);
  yPosition += 8;

  doc.setFont('helvetica', 'normal');
  doc.setFontSize(9);

  const netText = reportData.net_increase_in_cash < 0 ? `(${formatCurrency(reportData.net_increase_in_cash)})` : formatCurrency(reportData.net_increase_in_cash);
  doc.text('Net Change in Cash & Cash Equivalents:', 20, yPosition);
  doc.text(netText, pageWidth - 20, yPosition, { align: 'right' });
  yPosition += 5;

  doc.text('Opening Cash & Cash Equivalents:', 20, yPosition);
  doc.text(formatCurrency(reportData.opening_cash_balance), pageWidth - 20, yPosition, { align: 'right' });
  yPosition += 5;

  doc.setFont('helvetica', 'bold');
  doc.text('Closing Cash & Cash Equivalents:', 20, yPosition);
  doc.text(formatCurrency(reportData.closing_cash_balance), pageWidth - 20, yPosition, { align: 'right' });

  doc.setTextColor(0, 0, 0);

  // Footer
  const pageHeight = doc.internal.pageSize.getHeight();
  doc.setFontSize(8);
  doc.setFont('helvetica', 'normal');
  doc.text(`Generated on: ${new Date(reportData.generated_at).toLocaleString('en-IN')}`, 14, pageHeight - 10);

  doc.save(`Cash_Flow_Statement_${reportData.organization_name}_${reportData.to_date}.pdf`);
};

/**
 * Export Cash Flow Statement to Excel
 */
export const exportCashFlowToExcel = async (reportData: any): Promise<void> => {
  const wsData: CellValue[][] = [];

  // Header
  wsData.push([reportData.organization_name]);
  wsData.push(['Cash Flow Statement']);
  wsData.push([`For the period ${new Date(reportData.from_date).toLocaleDateString('en-IN')} to ${new Date(reportData.to_date).toLocaleDateString('en-IN')}`]);
  wsData.push(['(Prepared using Indirect Method)']);
  wsData.push([]);

  // Helper to add section
  const addSection = (section: any) => {
    wsData.push([section.section_name]);
    section.items.forEach((item: any) => {
      wsData.push([item.label, item.amount]);
    });
    wsData.push([`Net Cash from ${section.section_name.replace('Cash Flow from ', '')}`, section.net_cash_flow]);
    wsData.push([]);
  };

  addSection(reportData.operating_activities);
  addSection(reportData.investing_activities);
  addSection(reportData.financing_activities);

  // Summary
  wsData.push(['Summary']);
  wsData.push(['Net Change in Cash & Cash Equivalents', reportData.net_increase_in_cash]);
  wsData.push(['Opening Cash & Cash Equivalents', reportData.opening_cash_balance]);
  wsData.push(['Closing Cash & Cash Equivalents', reportData.closing_cash_balance]);
  wsData.push([]);
  wsData.push([`Generated on: ${new Date(reportData.generated_at).toLocaleString('en-IN')}`]);

  const wb = new ExcelJS.Workbook();
  const ws = wb.addWorksheet('Cash Flow Statement');
  applySheet(ws, wsData, [50, 20]);
  await downloadWorkbook(
    wb,
    `Cash_Flow_Statement_${reportData.organization_name}_${reportData.to_date}`
  );
};

/**
 * Export Profit & Loss to Excel
 */
export const exportProfitLossToExcel = async (reportData: any): Promise<void> => {
  const wsData: CellValue[][] = [];

  // Header
  wsData.push([reportData.organization_name]);
  wsData.push(['Profit & Loss Statement']);
  wsData.push([`For the period ${new Date(reportData.from_date).toLocaleDateString('en-IN')} to ${new Date(reportData.to_date).toLocaleDateString('en-IN')}`]);
  wsData.push([]);

  // Income Section
  wsData.push(['INCOME']);
  reportData.income_items.forEach((item: any) => {
    wsData.push([item.account_group_name, item.amount]);
  });
  wsData.push(['Total Income', reportData.total_income]);
  wsData.push([]);

  // Expenses Section
  wsData.push(['EXPENSES']);
  reportData.expense_items.forEach((item: any) => {
    wsData.push([item.account_group_name, item.amount]);
  });
  wsData.push(['Total Expenses', reportData.total_expenses]);
  wsData.push([]);

  // Net Profit/Loss
  wsData.push([`Net ${reportData.profit_loss_type === 'PROFIT' ? 'Profit' : 'Loss'}`, reportData.net_profit_loss]);
  wsData.push([]);
  wsData.push([`Generated on: ${new Date(reportData.generated_at).toLocaleString('en-IN')}`]);

  const wb = new ExcelJS.Workbook();
  const ws = wb.addWorksheet('Profit & Loss');
  applySheet(ws, wsData, [40, 20]);
  await downloadWorkbook(
    wb,
    `Profit_Loss_${reportData.organization_name}_${reportData.to_date}`
  );
};

/**
 * Export Profit & Loss to PDF
 */
export const exportProfitLossToPDF = (reportData: any): void => {
  const doc = new jsPDF({
    orientation: 'portrait',
    unit: 'mm',
    format: 'a4',
  });

  const pageWidth = doc.internal.pageSize.getWidth();
  let yPosition = 15;

  const formatCurrency = (amount: number) =>
    new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 2,
    }).format(amount);

  // Header
  doc.setFontSize(16);
  doc.setFont('helvetica', 'bold');
  doc.text(reportData.organization_name, pageWidth / 2, yPosition, { align: 'center' });
  yPosition += 8;

  doc.setFontSize(14);
  doc.text('Profit & Loss Statement', pageWidth / 2, yPosition, { align: 'center' });
  yPosition += 6;

  doc.setFontSize(10);
  doc.setFont('helvetica', 'normal');
  doc.text(
    `For the period ${new Date(reportData.from_date).toLocaleDateString('en-IN')} to ${new Date(reportData.to_date).toLocaleDateString('en-IN')}`,
    pageWidth / 2,
    yPosition,
    { align: 'center' }
  );
  yPosition += 10;

  // Income Section
  doc.setFillColor(16, 185, 129); // emerald-500
  doc.setTextColor(255, 255, 255);
  doc.rect(14, yPosition - 4, pageWidth - 28, 8, 'F');
  doc.setFontSize(11);
  doc.setFont('helvetica', 'bold');
  doc.text('INCOME', 16, yPosition);
  yPosition += 8;
  doc.setTextColor(0, 0, 0);

  doc.setFont('helvetica', 'normal');
  doc.setFontSize(9);
  reportData.income_items.forEach((item: any) => {
    doc.text(item.account_group_name, 20, yPosition);
    doc.text(formatCurrency(item.amount), pageWidth - 20, yPosition, { align: 'right' });
    yPosition += 5;
  });

  doc.setFont('helvetica', 'bold');
  doc.setFillColor(16, 185, 129);
  doc.setTextColor(255, 255, 255);
  doc.rect(14, yPosition - 3, pageWidth - 28, 7, 'F');
  doc.text('Total Income', 20, yPosition + 1);
  doc.text(formatCurrency(reportData.total_income), pageWidth - 20, yPosition + 1, { align: 'right' });
  doc.setTextColor(0, 0, 0);
  yPosition += 12;

  // Expenses Section
  doc.setFillColor(239, 68, 68); // red-500
  doc.setTextColor(255, 255, 255);
  doc.rect(14, yPosition - 4, pageWidth - 28, 8, 'F');
  doc.setFontSize(11);
  doc.setFont('helvetica', 'bold');
  doc.text('EXPENSES', 16, yPosition);
  yPosition += 8;
  doc.setTextColor(0, 0, 0);

  doc.setFont('helvetica', 'normal');
  doc.setFontSize(9);
  reportData.expense_items.forEach((item: any) => {
    doc.text(item.account_group_name, 20, yPosition);
    doc.text(formatCurrency(item.amount), pageWidth - 20, yPosition, { align: 'right' });
    yPosition += 5;
  });

  doc.setFont('helvetica', 'bold');
  doc.setFillColor(239, 68, 68);
  doc.setTextColor(255, 255, 255);
  doc.rect(14, yPosition - 3, pageWidth - 28, 7, 'F');
  doc.text('Total Expenses', 20, yPosition + 1);
  doc.text(formatCurrency(reportData.total_expenses), pageWidth - 20, yPosition + 1, { align: 'right' });
  doc.setTextColor(0, 0, 0);
  yPosition += 12;

  // Net Profit/Loss
  const isProfit = reportData.profit_loss_type === 'PROFIT';
  doc.setFillColor(isProfit ? 16 : 239, isProfit ? 185 : 68, isProfit ? 129 : 68);
  doc.setTextColor(255, 255, 255);
  doc.rect(14, yPosition - 4, pageWidth - 28, 10, 'F');
  doc.setFontSize(12);
  doc.text(`Net ${isProfit ? 'Profit' : 'Loss'}`, 20, yPosition + 2);
  doc.text(formatCurrency(reportData.net_profit_loss), pageWidth - 20, yPosition + 2, { align: 'right' });
  doc.setTextColor(0, 0, 0);

  // Footer
  const pageHeight = doc.internal.pageSize.getHeight();
  doc.setFontSize(8);
  doc.setFont('helvetica', 'normal');
  doc.text(`Generated on: ${new Date(reportData.generated_at).toLocaleString('en-IN')}`, 14, pageHeight - 10);

  doc.save(`Profit_Loss_${reportData.organization_name}_${reportData.to_date}.pdf`);
};

/**
 * Export Balance Sheet to Excel
 */
export const exportBalanceSheetToExcel = async (reportData: any): Promise<void> => {
  const wsData: CellValue[][] = [];

  // Header
  wsData.push([reportData.organization_name]);
  wsData.push(['Balance Sheet']);
  wsData.push([`As on ${new Date(reportData.as_on_date).toLocaleDateString('en-IN')}`]);
  wsData.push([]);

  // Assets Section
  wsData.push(['ASSETS']);
  reportData.assets.items.forEach((item: any) => {
    wsData.push([item.account_group_name, item.amount]);
  });
  wsData.push(['Total Assets', reportData.assets.total]);
  wsData.push([]);

  // Liabilities Section
  wsData.push(['LIABILITIES']);
  reportData.liabilities.items.forEach((item: any) => {
    wsData.push([item.account_group_name, item.amount]);
  });
  wsData.push(['Total Liabilities', reportData.liabilities.total]);
  wsData.push([]);

  // Equity Section
  wsData.push(['EQUITY']);
  reportData.equity.items.forEach((item: any) => {
    wsData.push([item.account_group_name, item.amount]);
  });
  wsData.push(['Total Equity', reportData.equity.total]);
  wsData.push([]);

  // Summary
  wsData.push(['Net Profit/(Loss)', reportData.net_profit_loss]);
  wsData.push(['Total Liabilities + Equity', reportData.total_liabilities_equity]);
  wsData.push([]);
  wsData.push([`Generated on: ${new Date(reportData.generated_at).toLocaleString('en-IN')}`]);

  const wb = new ExcelJS.Workbook();
  const ws = wb.addWorksheet('Balance Sheet');
  applySheet(ws, wsData, [40, 20]);
  await downloadWorkbook(
    wb,
    `Balance_Sheet_${reportData.organization_name}_${reportData.as_on_date}`
  );
};

/**
 * Export Balance Sheet to PDF
 */
export const exportBalanceSheetToPDF = (reportData: any): void => {
  const doc = new jsPDF({
    orientation: 'portrait',
    unit: 'mm',
    format: 'a4',
  });

  const pageWidth = doc.internal.pageSize.getWidth();
  let yPosition = 15;

  const formatCurrency = (amount: number) =>
    new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 2,
    }).format(amount);

  // Header
  doc.setFontSize(16);
  doc.setFont('helvetica', 'bold');
  doc.text(reportData.organization_name, pageWidth / 2, yPosition, { align: 'center' });
  yPosition += 8;

  doc.setFontSize(14);
  doc.text('Balance Sheet', pageWidth / 2, yPosition, { align: 'center' });
  yPosition += 6;

  doc.setFontSize(10);
  doc.setFont('helvetica', 'normal');
  doc.text(
    `As on ${new Date(reportData.as_on_date).toLocaleDateString('en-IN')}`,
    pageWidth / 2,
    yPosition,
    { align: 'center' }
  );
  yPosition += 10;

  const renderSection = (title: string, items: any[], total: number, color: number[]) => {
    doc.setFillColor(color[0], color[1], color[2]);
    doc.setTextColor(255, 255, 255);
    doc.rect(14, yPosition - 4, pageWidth - 28, 8, 'F');
    doc.setFontSize(11);
    doc.setFont('helvetica', 'bold');
    doc.text(title, 16, yPosition);
    yPosition += 8;
    doc.setTextColor(0, 0, 0);

    doc.setFont('helvetica', 'normal');
    doc.setFontSize(9);
    items.forEach((item: any) => {
      doc.text(item.account_group_name, 20, yPosition);
      doc.text(formatCurrency(item.amount), pageWidth - 20, yPosition, { align: 'right' });
      yPosition += 5;
    });

    doc.setFont('helvetica', 'bold');
    doc.setFillColor(color[0], color[1], color[2]);
    doc.setTextColor(255, 255, 255);
    doc.rect(14, yPosition - 3, pageWidth - 28, 7, 'F');
    doc.text(`Total ${title}`, 20, yPosition + 1);
    doc.text(formatCurrency(total), pageWidth - 20, yPosition + 1, { align: 'right' });
    doc.setTextColor(0, 0, 0);
    yPosition += 12;
  };

  // Render sections
  renderSection('ASSETS', reportData.assets.items, reportData.assets.total, [59, 130, 246]); // blue-500
  renderSection('LIABILITIES', reportData.liabilities.items, reportData.liabilities.total, [239, 68, 68]); // red-500
  renderSection('EQUITY', reportData.equity.items, reportData.equity.total, [139, 92, 246]); // purple-500

  // Summary
  doc.setFillColor(30, 41, 59); // slate-800
  doc.setTextColor(255, 255, 255);
  doc.rect(14, yPosition - 4, pageWidth - 28, 20, 'F');

  doc.setFontSize(9);
  doc.setFont('helvetica', 'normal');
  doc.text('Net Profit/(Loss)', 20, yPosition + 2);
  doc.text(formatCurrency(reportData.net_profit_loss), pageWidth - 20, yPosition + 2, { align: 'right' });
  yPosition += 7;

  doc.setFont('helvetica', 'bold');
  doc.text('Total Liabilities + Equity', 20, yPosition + 2);
  doc.text(formatCurrency(reportData.total_liabilities_equity), pageWidth - 20, yPosition + 2, { align: 'right' });

  doc.setTextColor(0, 0, 0);

  // Balance check
  yPosition += 15;
  if (reportData.is_balanced) {
    doc.setFillColor(16, 185, 129);
    doc.setTextColor(255, 255, 255);
    doc.rect(14, yPosition - 4, pageWidth - 28, 8, 'F');
    doc.setFontSize(10);
    doc.text('Balance Sheet is Balanced', pageWidth / 2, yPosition, { align: 'center' });
  } else {
    doc.setFillColor(239, 68, 68);
    doc.setTextColor(255, 255, 255);
    doc.rect(14, yPosition - 4, pageWidth - 28, 8, 'F');
    doc.setFontSize(10);
    const diff = Math.abs(reportData.assets.total - reportData.total_liabilities_equity);
    doc.text(`Difference: ${formatCurrency(diff)}`, pageWidth / 2, yPosition, { align: 'center' });
  }

  doc.setTextColor(0, 0, 0);

  // Footer
  const pageHeight = doc.internal.pageSize.getHeight();
  doc.setFontSize(8);
  doc.setFont('helvetica', 'normal');
  doc.text(`Generated on: ${new Date(reportData.generated_at).toLocaleString('en-IN')}`, 14, pageHeight - 10);

  doc.save(`Balance_Sheet_${reportData.organization_name}_${reportData.as_on_date}.pdf`);
};
