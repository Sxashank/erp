export const SUPER_ADMIN_PERMISSION = 'SUPER_ADMIN';

export interface ModuleAccessNavChild {
  label: string;
  href: string;
}

export interface ModuleAccessNavItem {
  label: string;
  href?: string;
  children?: ModuleAccessNavChild[];
}

export interface ErpModuleDefinition {
  key: string;
  label: string;
  scope: string;
  accountingFit: string;
  aclPrinciple: string;
}

interface AccessRule {
  pathPrefix: string;
  permissions: readonly string[];
}

const FINANCE_PERMISSIONS = [
  'FIN_FY_VIEW',
  'FIN_COA_VIEW',
  'FIN_VTYPE_VIEW',
  'FIN_VOUCHER_VIEW',
  'FIN_REPORT_VIEW',
] as const;

const AP_AR_PERMISSIONS = [
  'APAR_TERMS_VIEW',
  'APAR_VENDOR_VIEW',
  'APAR_CUSTOMER_VIEW',
  'APAR_BILL_VIEW',
  'APAR_INVOICE_VIEW',
  'APAR_PAYMENT_VIEW',
] as const;

const LENDING_PERMISSIONS = [
  'LOS_ENTITY_VIEW',
  'LOS_PRODUCT_VIEW',
  'LOS_APPLICATION_VIEW',
  'LOS_SANCTION_VIEW',
  'LMS_ACCOUNT_VIEW',
  'LMS_RECEIPT_CREATE',
  'COLLECTIONS_READ',
  'NPA_READ',
  'LEGAL_READ',
] as const;

const TREASURY_PERMISSIONS = ['TREASURY_READ', 'TREASURY_WRITE', 'TREASURY_APPROVE'] as const;

const REPORT_PERMISSIONS = [
  'FIN_REPORT_VIEW',
  'REPORT_REGULATORY_VIEW',
  'REPORT_MIS_VIEW',
  'REPORT_DASHBOARD_VIEW',
] as const;

const HRIS_PERMISSIONS = [
  'HRIS_EMPLOYEE_VIEW',
  'HRIS_SHIFT_VIEW',
  'HRIS_HOLIDAY_VIEW',
  'HRIS_LEAVE_TYPE_VIEW',
  'HRIS_LEAVE_VIEW',
  'HRIS_ATTENDANCE_VIEW',
  'HRIS_SEPARATION_VIEW',
  'HRIS_TRAINING_VIEW',
  'HRIS_APPRAISAL_VIEW',
] as const;

const PAYROLL_PERMISSIONS = [
  'PAYROLL_COMPONENT_VIEW',
  'PAYROLL_STRUCTURE_VIEW',
  'PAYROLL_RUN_VIEW',
  'PAYROLL_PAYSLIP_VIEW',
  'PAYROLL_REPORT_VIEW',
] as const;

const FIXED_ASSET_PERMISSIONS = [
  'FA_CATEGORY_VIEW',
  'FA_ASSET_VIEW',
  'FA_DEPRECIATION_VIEW',
  'FA_REPORT_VIEW',
] as const;

const FIXED_DEPOSIT_PERMISSIONS = [
  'FD_PRODUCT_VIEW',
  'FD_DEPOSIT_VIEW',
  'FD_INTEREST_ACCRUE',
  'FD_REPORT_VIEW',
] as const;

const INVENTORY_PERMISSIONS = [
  'INV_CATEGORY_VIEW',
  'INV_ITEM_VIEW',
  'INV_WAREHOUSE_VIEW',
  'INV_STOCK_VIEW',
  'INV_REPORT_VIEW',
] as const;

const PROCUREMENT_PERMISSIONS = [
  'APAR_VENDOR_VIEW',
  'APAR_BILL_VIEW',
  'APAR_PAYMENT_VIEW',
  'VENDOR_PO_VIEW',
] as const;

export const ERP_MODULES: readonly ErpModuleDefinition[] = [
  {
    key: 'dashboard',
    label: 'Dashboard / Command Center',
    scope:
      'Enterprise cockpit for management visibility across finance, lending, treasury, HR, compliance, and operations.',
    accountingFit: 'Aggregates posted and operational data without replacing source ledgers.',
    aclPrinciple: 'Visible to authenticated users; widgets must still honor domain permissions.',
  },
  {
    key: 'masters',
    label: 'Masters & Organization',
    scope:
      'Organization, units, departments, designations, cost centers, financial periods, and statutory setup masters.',
    accountingFit:
      'Provides Tally/Zoho-style master controls that drive ledger posting, GST/TDS treatment, and reporting dimensions.',
    aclPrinciple: 'Restricted by organization-unit and master-data administration permissions.',
  },
  {
    key: 'users_acl',
    label: 'Users, Roles & ACL',
    scope:
      'Users, roles, permissions, maker-checker assignment, portal access, and organization visibility.',
    accountingFit:
      'Protects segregation of duties for vouchers, approvals, payroll, treasury, and statutory workflows.',
    aclPrinciple: 'Only user administrators and super admins manage access.',
  },
  {
    key: 'finance',
    label: 'Finance, GL & Vouchers',
    scope:
      'Chart of accounts, voucher types, vouchers, recurring vouchers, year-end close, ledgers, trial balance, P&L, and balance sheet.',
    accountingFit:
      'Indian double-entry accounting with period controls, balanced vouchers, cost centers, statutory ledgers, and audit trail.',
    aclPrinciple:
      'Finance users see finance surfaces based on voucher, COA, posting, approval, and report permissions.',
  },
  {
    key: 'gst',
    label: 'GST',
    scope:
      'GST rates, HSN/SAC, registrations, GST returns, ITC, challans, e-invoice, and e-waybill lifecycle.',
    accountingFit:
      'Supports Indian GST accounting manually now; GSTN/IRP/e-waybill integration is release-gated for later.',
    aclPrinciple: 'Tax team permissions control GST setup, return preparation, and filing actions.',
  },
  {
    key: 'tds_tcs',
    label: 'TDS / TCS',
    scope: 'TDS sections, deductions, challans, returns, certificates, and statutory reporting.',
    accountingFit:
      'Indian TDS/TCS compliance with effective-date rates, PAN rules, challan tracking, and Form 16A/return preparation.',
    aclPrinciple: 'Tax/payroll/finance users receive section-specific access.',
  },
  {
    key: 'ap_ar',
    label: 'AP / AR, Vendors, Customers & BRS',
    scope:
      'Vendors, customers, purchase bills, sales invoices, payments, receipts, bank reconciliation, and aging reports.',
    accountingFit:
      'Manual AP/AR and BRS workflows aligned to Indian accounting practice; bank integrations remain future-state.',
    aclPrinciple:
      'Payables, receivables, and bank users are separated by party/payment permissions.',
  },
  {
    key: 'lending',
    label: 'Lending LOS / LMS / Collections',
    scope:
      'Corporate borrower onboarding, products, applications, sanctions, loan accounts, disbursements, schedules, manual receipts, collections, NPA, OTS, and legal handoff.',
    accountingFit:
      'Loan interest, principal, penal charges, provisions, and write-offs feed finance through controlled posting flows.',
    aclPrinciple:
      'Credit, operations, collections, legal, and treasury permissions expose only their workflow stages.',
  },
  {
    key: 'treasury_alm',
    label: 'Treasury, Borrowings, ALM & Investments',
    scope:
      'Lenders, borrowings, source of funds, ALM buckets, gap analysis, interest-rate risk, investments, and treasury dashboards.',
    accountingFit:
      'Tracks cost of funds, borrowing obligations, investment values, interest expense, and spread/NII analytics.',
    aclPrinciple: 'Treasury access is restricted to authorized funding and ALM users.',
  },
  {
    key: 'regulatory_reports',
    label: 'Regulatory, MIS & BI Reports',
    scope:
      'RBI/NBFC reports, ALM, CRILC-ready data, MIS, dashboards, schedules, exports, and analytics.',
    accountingFit: 'Reports derive from governed ledgers and sub-ledgers, preserving auditability.',
    aclPrinciple: 'Report access is granted by report family and export/generation permissions.',
  },
  {
    key: 'fixed_assets',
    label: 'Fixed Assets',
    scope:
      'Asset categories, asset register, capitalization, depreciation, verification, maintenance, insurance, disposal, and write-off.',
    accountingFit:
      'Indian fixed-asset accounting with capitalization thresholds, depreciation runs, gain/loss on disposal, and GL postings.',
    aclPrinciple: 'Asset custodians, finance, and approvers receive separate permissions.',
  },
  {
    key: 'fixed_deposits',
    label: 'Fixed Deposits',
    scope:
      'FD products, interest slabs, deposits, renewals, maturity, closure, accruals, and collateral tracking.',
    accountingFit:
      'FD interest accrual, TDS deduction, maturity payable, and collateral lien accounting.',
    aclPrinciple: 'Treasury and deposit operations control product, deposit, and payout access.',
  },
  {
    key: 'hris_payroll',
    label: 'HRIS, Payroll & ESS',
    scope:
      'Employees, attendance, leave, separation, training, performance, salary structures, statutory setup, payroll runs, payslips, and employee self-service.',
    accountingFit:
      'Payroll postings, PF/ESI/PT/TDS compliance, expense accounting, and bank payout files.',
    aclPrinciple: 'HR, payroll, managers, and employees have distinct data visibility.',
  },
  {
    key: 'inventory_procurement',
    label: 'Inventory & Procurement',
    scope:
      'Item categories, items, warehouses, stock movement, valuation, RFQ, purchase orders, GRN, and vendor-facing procurement.',
    accountingFit:
      'Purchase-to-pay, stock valuation, GRN accruals, vendor bills, GST ITC, and inventory adjustments.',
    aclPrinciple: 'Stores, procurement, finance, and vendor users are separated.',
  },
  {
    key: 'compliance_legal_dms',
    label: 'Compliance, Legal & DMS',
    scope:
      'Compliance calendar, legal cases, notices, advocates, expenses, document folders, uploads, downloads, tags, and audit records.',
    accountingFit:
      'Compliance costs, legal expenses, statutory evidence, and document retention are auditable.',
    aclPrinciple:
      'Sensitive cases and documents are restricted by role, unit, and document classification.',
  },
  {
    key: 'notifications_settings_portals',
    label: 'Notifications, Settings & Portals',
    scope:
      'Notification templates, logs, integration settings, borrower portal, vendor portal, and employee portal administration.',
    accountingFit:
      'External integrations are configured but disabled/manual-first until explicitly released.',
    aclPrinciple:
      'Platform settings, tenant settings, and portal administration are separately permissioned.',
  },
] as const;

const ACCESS_RULES: readonly AccessRule[] = [
  { pathPrefix: '/admin/profile', permissions: [] },
  { pathPrefix: '/admin/organizations', permissions: ['MASTER_ORG_VIEW'] },
  { pathPrefix: '/admin/units', permissions: ['MASTER_UNIT_VIEW'] },
  { pathPrefix: '/admin/departments', permissions: ['MASTER_DEPT_VIEW'] },
  { pathPrefix: '/admin/designations', permissions: ['MASTER_DESIG_VIEW'] },
  { pathPrefix: '/admin/users', permissions: ['USER_VIEW'] },
  { pathPrefix: '/admin/roles', permissions: ['ROLE_VIEW'] },
  { pathPrefix: '/admin/finance/financial-years', permissions: ['FIN_FY_VIEW'] },
  { pathPrefix: '/admin/finance/account-groups', permissions: ['FIN_COA_VIEW'] },
  { pathPrefix: '/admin/finance/accounts', permissions: ['FIN_COA_VIEW'] },
  { pathPrefix: '/admin/finance/voucher-types', permissions: ['FIN_VTYPE_VIEW'] },
  { pathPrefix: '/admin/finance/vouchers', permissions: ['FIN_VOUCHER_VIEW'] },
  { pathPrefix: '/admin/finance/voucher-templates', permissions: ['FIN_VOUCHER_VIEW'] },
  { pathPrefix: '/admin/finance/recurring-vouchers', permissions: ['FIN_VOUCHER_VIEW'] },
  {
    pathPrefix: '/admin/finance/year-end-closing',
    permissions: ['FIN_FY_CLOSE', 'FIN_REPORT_VIEW'],
  },
  { pathPrefix: '/admin/finance', permissions: FINANCE_PERMISSIONS },
  {
    pathPrefix: '/admin/gst',
    permissions: ['GST_RATE_VIEW', 'GST_RETURN_VIEW', 'GST_ITC_VIEW', 'GST_CHALLAN_VIEW'],
  },
  {
    pathPrefix: '/admin/tds',
    permissions: [
      'TDS_SECTION_VIEW',
      'TDS_RETURN_VIEW',
      'TDS_CHALLAN_VIEW',
      'TDS_CERTIFICATE_VIEW',
    ],
  },
  { pathPrefix: '/admin/ap-ar/payment-terms', permissions: ['APAR_TERMS_VIEW'] },
  { pathPrefix: '/admin/ap-ar/vendors', permissions: ['APAR_VENDOR_VIEW'] },
  { pathPrefix: '/admin/ap-ar/customers', permissions: ['APAR_CUSTOMER_VIEW'] },
  { pathPrefix: '/admin/ap-ar/purchase-bills', permissions: ['APAR_BILL_VIEW'] },
  { pathPrefix: '/admin/ap-ar/sales-invoices', permissions: ['APAR_INVOICE_VIEW'] },
  { pathPrefix: '/admin/ap-ar/payments', permissions: ['APAR_PAYMENT_VIEW'] },
  {
    pathPrefix: '/admin/ap-ar/bank-reconciliation',
    permissions: ['APAR_PAYMENT_VIEW', 'FIN_REPORT_VIEW'],
  },
  { pathPrefix: '/admin/ap-ar/aging-reports', permissions: AP_AR_PERMISSIONS },
  { pathPrefix: '/admin/ap-ar', permissions: AP_AR_PERMISSIONS },
  { pathPrefix: '/admin/reports/regulatory', permissions: ['REPORT_REGULATORY_VIEW'] },
  { pathPrefix: '/admin/reports/mis', permissions: ['REPORT_MIS_VIEW'] },
  { pathPrefix: '/admin/reports/scheduler', permissions: ['REPORT_SCHEDULE_VIEW'] },
  { pathPrefix: '/admin/reports/history', permissions: REPORT_PERMISSIONS },
  { pathPrefix: '/admin/reports', permissions: REPORT_PERMISSIONS },
  { pathPrefix: '/admin/portal/users', permissions: ['PORTAL_USER_VIEW', 'TREASURY_READ'] },
  { pathPrefix: '/admin/portal/registrations', permissions: ['PORTAL_USER_VIEW', 'TREASURY_READ'] },
  { pathPrefix: '/admin/lending/entities', permissions: ['LOS_ENTITY_VIEW'] },
  { pathPrefix: '/admin/lending/products', permissions: ['LOS_PRODUCT_VIEW'] },
  { pathPrefix: '/admin/lending/applications', permissions: ['LOS_APPLICATION_VIEW'] },
  { pathPrefix: '/admin/lending/sanctions', permissions: ['LOS_SANCTION_VIEW'] },
  { pathPrefix: '/admin/lending/accounts', permissions: ['LMS_ACCOUNT_VIEW'] },
  {
    pathPrefix: '/admin/lending/disbursements',
    permissions: ['LMS_ACCOUNT_VIEW', 'LMS_DISBURSEMENT_PROCESS'],
  },
  {
    pathPrefix: '/admin/lending/disbursement-readiness',
    permissions: ['LMS_ACCOUNT_VIEW', 'LMS_DISBURSEMENT_PROCESS'],
  },
  {
    pathPrefix: '/admin/lending/receipts',
    permissions: ['LMS_RECEIPT_CREATE', 'LMS_RECEIPT_ALLOCATE'],
  },
  { pathPrefix: '/admin/lending/collection-cockpit', permissions: ['COLLECTIONS_READ'] },
  { pathPrefix: '/admin/lending/collections/followups', permissions: ['COLLECTIONS_READ'] },
  { pathPrefix: '/admin/lending/collections/npa', permissions: ['NPA_READ'] },
  {
    pathPrefix: '/admin/lending/collections/ots',
    permissions: ['OTS_CREATE', 'OTS_UPDATE', 'OTS_APPROVE'],
  },
  { pathPrefix: '/admin/lending/collections/legal', permissions: ['LEGAL_READ'] },
  {
    pathPrefix: '/admin/lending/closure-cockpit',
    permissions: ['LMS_ACCOUNT_VIEW', 'COLLECTIONS_READ'],
  },
  { pathPrefix: '/admin/lending/risk-cockpit', permissions: ['NPA_READ', 'REPORT_MIS_VIEW'] },
  { pathPrefix: '/admin/lending/nach', permissions: ['PG_NACH_BATCH_VIEW', 'LMS_MANDATE_CREATE'] },
  { pathPrefix: '/admin/lending/aa', permissions: ['KYC_DOC_VIEW', 'LOS_APPLICATION_VIEW'] },
  { pathPrefix: '/admin/lending/reports', permissions: ['REPORT_MIS_VIEW', 'FIN_REPORT_VIEW'] },
  {
    pathPrefix: '/admin/lending/checklist',
    permissions: ['LOS_APPLICATION_VIEW', 'LOS_SANCTION_VIEW', 'TREASURY_READ'],
  },
  { pathPrefix: '/admin/lending/iif', permissions: ['LOS_APPLICATION_VIEW', 'REPORT_MIS_VIEW'] },
  { pathPrefix: '/admin/lending', permissions: LENDING_PERMISSIONS },
  { pathPrefix: '/admin/treasury', permissions: TREASURY_PERMISSIONS },
  { pathPrefix: '/admin/regulatory', permissions: ['REPORT_REGULATORY_VIEW', 'TREASURY_READ'] },
  { pathPrefix: '/admin/fixed-assets/categories', permissions: ['FA_CATEGORY_VIEW'] },
  { pathPrefix: '/admin/fixed-assets/assets', permissions: ['FA_ASSET_VIEW'] },
  { pathPrefix: '/admin/fixed-assets/depreciation', permissions: ['FA_DEPRECIATION_VIEW'] },
  { pathPrefix: '/admin/fixed-assets', permissions: FIXED_ASSET_PERMISSIONS },
  { pathPrefix: '/admin/fixed-deposits/products', permissions: ['FD_PRODUCT_VIEW'] },
  { pathPrefix: '/admin/fixed-deposits', permissions: FIXED_DEPOSIT_PERMISSIONS },
  { pathPrefix: '/admin/hris/employees', permissions: ['HRIS_EMPLOYEE_VIEW'] },
  { pathPrefix: '/admin/hris/shifts', permissions: ['HRIS_SHIFT_VIEW'] },
  { pathPrefix: '/admin/hris/holidays', permissions: ['HRIS_HOLIDAY_VIEW'] },
  { pathPrefix: '/admin/hris/leave-types', permissions: ['HRIS_LEAVE_TYPE_VIEW'] },
  { pathPrefix: '/admin/hris/leave-applications', permissions: ['HRIS_LEAVE_VIEW'] },
  { pathPrefix: '/admin/hris/attendance', permissions: ['HRIS_ATTENDANCE_VIEW'] },
  { pathPrefix: '/admin/hris/separation', permissions: ['HRIS_SEPARATION_VIEW'] },
  { pathPrefix: '/admin/hris/training', permissions: ['HRIS_TRAINING_VIEW'] },
  { pathPrefix: '/admin/hris/performance', permissions: ['HRIS_APPRAISAL_VIEW'] },
  { pathPrefix: '/admin/hris', permissions: HRIS_PERMISSIONS },
  { pathPrefix: '/admin/payroll/components', permissions: ['PAYROLL_COMPONENT_VIEW'] },
  { pathPrefix: '/admin/payroll/structures', permissions: ['PAYROLL_STRUCTURE_VIEW'] },
  {
    pathPrefix: '/admin/payroll/employee-salary',
    permissions: ['PAYROLL_STRUCTURE_VIEW', 'PAYROLL_RUN_VIEW'],
  },
  {
    pathPrefix: '/admin/payroll/statutory',
    permissions: ['PAYROLL_COMPONENT_VIEW', 'PAYROLL_REPORT_VIEW'],
  },
  { pathPrefix: '/admin/payroll/batches', permissions: ['PAYROLL_RUN_VIEW'] },
  { pathPrefix: '/admin/payroll', permissions: PAYROLL_PERMISSIONS },
  {
    pathPrefix: '/admin/workflow/tasks',
    permissions: ['APPROVAL_PENDING_VIEW', 'APPROVAL_REQUEST_VIEW'],
  },
  {
    pathPrefix: '/admin/workflow/instances',
    permissions: ['WORKFLOW_VIEW', 'APPROVAL_REQUEST_VIEW'],
  },
  {
    pathPrefix: '/admin/workflow',
    permissions: ['WORKFLOW_VIEW', 'APPROVAL_CONFIG_VIEW', 'APPROVAL_PENDING_VIEW'],
  },
  { pathPrefix: '/admin/inventory/categories', permissions: ['INV_CATEGORY_VIEW'] },
  { pathPrefix: '/admin/inventory/items', permissions: ['INV_ITEM_VIEW'] },
  { pathPrefix: '/admin/inventory/warehouses', permissions: ['INV_WAREHOUSE_VIEW'] },
  { pathPrefix: '/admin/inventory', permissions: INVENTORY_PERMISSIONS },
  { pathPrefix: '/admin/procurement', permissions: PROCUREMENT_PERMISSIONS },
  { pathPrefix: '/admin/compliance/items', permissions: ['COMPLIANCE_ITEM_VIEW'] },
  {
    pathPrefix: '/admin/compliance',
    permissions: ['COMPLIANCE_DASHBOARD_VIEW', 'COMPLIANCE_ITEM_VIEW'],
  },
  { pathPrefix: '/admin/legal/law-firms', permissions: ['LEGAL_LAWFIRM_VIEW', 'LEGAL_READ'] },
  { pathPrefix: '/admin/legal/advocates', permissions: ['LEGAL_ADVOCATE_VIEW', 'LEGAL_READ'] },
  { pathPrefix: '/admin/legal/cases', permissions: ['LEGAL_CASE_VIEW', 'LEGAL_READ'] },
  { pathPrefix: '/admin/legal/notices', permissions: ['LEGAL_NOTICE_VIEW', 'LEGAL_READ'] },
  { pathPrefix: '/admin/legal/expenses', permissions: ['LEGAL_EXPENSE_VIEW', 'LEGAL_READ'] },
  {
    pathPrefix: '/admin/legal',
    permissions: ['LEGAL_DASHBOARD_VIEW', 'LEGAL_REPORT_VIEW', 'LEGAL_READ'],
  },
  { pathPrefix: '/admin/dms/folders', permissions: ['DMS_FOLDER_VIEW'] },
  { pathPrefix: '/admin/dms/upload', permissions: ['DMS_DOCUMENT_UPLOAD'] },
  { pathPrefix: '/admin/dms/search', permissions: ['DMS_DOCUMENT_VIEW'] },
  { pathPrefix: '/admin/dms/tags', permissions: ['DMS_TAG_VIEW'] },
  { pathPrefix: '/admin/dms', permissions: ['DMS_FOLDER_VIEW', 'DMS_DOCUMENT_VIEW'] },
  { pathPrefix: '/admin/bi', permissions: ['REPORT_DASHBOARD_VIEW', 'REPORT_MIS_VIEW'] },
  {
    pathPrefix: '/admin/settings',
    permissions: ['NOTIF_SETTINGS_VIEW', 'PORTAL_SETTINGS_VIEW', 'TREASURY_READ'],
  },
  { pathPrefix: '/admin/notifications/templates', permissions: ['NOTIF_TEMPLATE_VIEW'] },
  { pathPrefix: '/admin/notifications/settings', permissions: ['NOTIF_SETTINGS_VIEW'] },
  { pathPrefix: '/admin/notifications/logs', permissions: ['NOTIF_LOG_VIEW'] },
  {
    pathPrefix: '/admin/notifications',
    permissions: ['NOTIF_VIEW', 'NOTIF_TEMPLATE_VIEW', 'NOTIF_SETTINGS_VIEW'],
  },
] as const;

function hasAnyPermission(permissions: ReadonlySet<string>, required: readonly string[]): boolean {
  if (permissions.has(SUPER_ADMIN_PERMISSION)) {
    return true;
  }
  if (required.length === 0) {
    return true;
  }
  return required.some((permission) => permissions.has(permission));
}

function normalizePath(pathname: string): string {
  const [path] = pathname.split(/[?#]/);
  if (path.length > 1 && path.endsWith('/')) {
    return path.slice(0, -1);
  }
  return path;
}

function matchesPrefix(pathname: string, pathPrefix: string): boolean {
  return pathname === pathPrefix || pathname.startsWith(`${pathPrefix}/`);
}

export function getAccessRuleForAdminPath(pathname: string): AccessRule | null {
  const path = normalizePath(pathname);
  if (path === '/admin') {
    return { pathPrefix: '/admin', permissions: [] };
  }
  return ACCESS_RULES.find((rule) => matchesPrefix(path, rule.pathPrefix)) ?? null;
}

export function canAccessAdminPath(pathname: string, permissions: ReadonlySet<string>): boolean {
  const rule = getAccessRuleForAdminPath(pathname);
  if (!rule) {
    return permissions.has(SUPER_ADMIN_PERMISSION);
  }
  return hasAnyPermission(permissions, rule.permissions);
}

export function filterNavItemsByAccess<T extends ModuleAccessNavItem>(
  items: readonly T[],
  permissions: ReadonlySet<string>,
): T[] {
  return items.flatMap((item) => {
    const children = item.children?.filter((child) => canAccessAdminPath(child.href, permissions));
    const canAccessItem = item.href ? canAccessAdminPath(item.href, permissions) : false;

    if (children) {
      if (children.length === 0 && !canAccessItem) {
        return [];
      }
      return [{ ...item, children }] as T[];
    }

    return canAccessItem ? [item] : [];
  });
}
