import {
  Building2,
  Bell,
  Calculator,
  ChevronDown,
  ChevronRight,
  HelpCircle,
  LayoutGrid,
  LogOut,
  Menu,
  Palette,
  Search,
  Settings,
  Users,
  Network,
  X,
  Percent,
  BarChart3,
  Landmark,
  Wallet,
  FileCheck,
  Gavel,
  Package,
  FolderOpen,
  UserCheck,
  GitBranch,
  HardDrive,
} from 'lucide-react';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { Link, Outlet, useLocation, useNavigate } from 'react-router-dom';

import { RequireModuleAccess } from '@/components/common/RequireModuleAccess';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Input } from '@/components/ui/input';
import { useAppTheme } from '@/contexts/AppThemeContext';
import { Separator } from '@/components/ui/separator';
import { filterNavItemsByAccess } from '@/lib/moduleAccess';
import { cn } from '@/lib/utils';
import { useAuthStore } from '@/stores/authStore';

interface NavItem {
  label: string;
  icon: React.ElementType;
  href?: string;
  children?: { label: string; href: string }[];
}

const navItems: NavItem[] = [
  {
    label: 'Dashboard',
    icon: LayoutGrid,
    href: '/admin',
  },
  {
    label: 'MIS & Reports',
    icon: BarChart3,
    children: [
      { label: 'Report Dashboard', href: '/admin/reports' },
      { label: 'MIS Command Center', href: '/admin/reports/mis' },
      { label: 'Regulatory Reports', href: '/admin/reports/regulatory' },
      { label: 'Scheduled Reports', href: '/admin/reports/scheduler' },
      { label: 'Export History', href: '/admin/reports/history' },
      { label: 'Trial Balance', href: '/admin/reports/trial-balance' },
      { label: 'Profit & Loss', href: '/admin/reports/profit-loss' },
      { label: 'Balance Sheet', href: '/admin/reports/balance-sheet' },
      { label: 'Cash Flow Statement', href: '/admin/reports/cash-flow-statement' },
      { label: 'Account Ledger', href: '/admin/reports/account-ledger' },
      { label: 'Day Book', href: '/admin/reports/day-book' },
      { label: 'BI Dashboards', href: '/admin/bi/dashboards' },
    ],
  },
  {
    label: 'Lending',
    icon: Landmark,
    children: [
      { label: 'Dashboard', href: '/admin/lending' },
      { label: 'Pipeline Dashboard', href: '/admin/lending/dashboards/pipeline' },
      { label: 'Master Data', href: '/admin/lending/masters' },
      { label: 'Loan Products', href: '/admin/lending/products' },
      { label: 'Entities/Borrowers', href: '/admin/lending/entities' },
      { label: 'Applications', href: '/admin/lending/applications' },
      { label: 'Sanctions', href: '/admin/lending/sanctions' },
      { label: 'Loan Accounts', href: '/admin/lending/accounts' },
      { label: 'Disbursement Readiness', href: '/admin/lending/disbursement-readiness' },
      { label: 'Disbursements', href: '/admin/lending/disbursements' },
      { label: 'Receipts', href: '/admin/lending/receipts' },
      { label: 'Closure & Release', href: '/admin/lending/closure-cockpit' },
      { label: 'Reports & Analytics', href: '/admin/lending/reports' },
    ],
  },
  {
    label: 'Collections & Risk',
    icon: UserCheck,
    children: [
      { label: 'Collection Cockpit', href: '/admin/lending/collection-cockpit' },
      { label: 'Follow-ups', href: '/admin/lending/collections/followups' },
      { label: 'NPA Accounts', href: '/admin/lending/collections/npa' },
      { label: 'Credit Risk Cockpit', href: '/admin/lending/risk-cockpit' },
      { label: 'OTS Proposals', href: '/admin/lending/collections/ots' },
      { label: 'Legal Cases', href: '/admin/lending/collections/legal' },
    ],
  },
  {
    label: 'Interest Subvention',
    icon: Percent,
    children: [
      { label: 'Enrollments', href: '/admin/lending/iif/enrollments' },
      { label: 'Claims', href: '/admin/lending/iif/claims' },
    ],
  },
  {
    label: 'Treasury & Borrowings',
    icon: Wallet,
    children: [
      { label: 'Dashboard', href: '/admin/treasury' },
      { label: 'Funding Sources / Lenders', href: '/admin/treasury/lenders' },
      { label: 'Borrowing Facilities / Loans Taken', href: '/admin/treasury/borrowings' },
      { label: 'Borrowing-to-Loan Mapping', href: '/admin/treasury/source-of-funds' },
      { label: 'ALM Dashboard', href: '/admin/treasury/alm' },
      { label: 'Gap Analysis', href: '/admin/treasury/alm/gap' },
      { label: 'Interest Rate Risk', href: '/admin/treasury/alm/irs' },
      { label: 'Investments', href: '/admin/treasury/investments' },
    ],
  },
  {
    label: 'Finance & Accounting',
    icon: Calculator,
    children: [
      { label: 'Vouchers', href: '/admin/finance/vouchers' },
      { label: 'Recurring Vouchers', href: '/admin/finance/recurring-vouchers' },
      { label: 'Year-End Closing', href: '/admin/finance/year-end-closing' },
      { label: 'Vendors', href: '/admin/ap-ar/vendors' },
      { label: 'Customers', href: '/admin/ap-ar/customers' },
      { label: 'Purchase Bills', href: '/admin/ap-ar/purchase-bills' },
      { label: 'Sales Invoices', href: '/admin/ap-ar/sales-invoices' },
      { label: 'Payments & Receipts', href: '/admin/ap-ar/payments' },
      { label: 'Bank Reconciliation', href: '/admin/ap-ar/bank-reconciliation' },
      { label: 'AP Aging Report', href: '/admin/ap-ar/aging-reports/ap' },
      { label: 'AR Aging Report', href: '/admin/ap-ar/aging-reports/ar' },
    ],
  },
  {
    label: 'Tax & Compliance',
    icon: FileCheck,
    children: [
      { label: 'GST Dashboard', href: '/admin/gst/gstn' },
      { label: 'GSTR-1', href: '/admin/gst/gstn/gstr1' },
      { label: 'GSTR-3B', href: '/admin/gst/gstn/gstr3b' },
      { label: 'ITC Reconciliation', href: '/admin/gst/gstn/itc' },
      { label: 'TDS Entries', href: '/admin/tds/entries' },
      { label: 'TDS Challans', href: '/admin/tds/challans' },
      { label: 'TDS Returns', href: '/admin/tds/returns' },
      { label: 'TDS Certificates', href: '/admin/tds/certificates' },
      { label: 'Compliance Dashboard', href: '/admin/compliance' },
      { label: 'Returns Calendar', href: '/admin/regulatory/returns' },
      { label: 'CRAR Dashboard', href: '/admin/regulatory/crar' },
      { label: 'Exposure Reports', href: '/admin/regulatory/exposure' },
    ],
  },
  {
    label: 'HRIS & Payroll',
    icon: Users,
    children: [
      { label: 'HR Dashboard', href: '/admin/hris' },
      { label: 'Employees', href: '/admin/hris/employees' },
      { label: 'Leave Applications', href: '/admin/hris/leave-applications' },
      { label: 'Attendance', href: '/admin/hris/attendance' },
      { label: 'Separation & F&F', href: '/admin/hris/separation' },
      { label: 'Training', href: '/admin/hris/training' },
      { label: 'Performance', href: '/admin/hris/performance/cycles' },
      { label: 'Employee Salary', href: '/admin/payroll/employee-salary' },
      { label: 'Payroll Batches', href: '/admin/payroll/batches' },
    ],
  },
  {
    label: 'Procurement & Inventory',
    icon: Package,
    children: [
      { label: 'Inventory Dashboard', href: '/admin/inventory' },
      { label: 'Items', href: '/admin/inventory/items' },
      { label: 'Stock In', href: '/admin/inventory/stock-in' },
      { label: 'Stock Out', href: '/admin/inventory/stock-out' },
      { label: 'Stock Transfer', href: '/admin/inventory/stock-transfer' },
      { label: 'Valuation', href: '/admin/inventory/valuation' },
      { label: 'RFQ', href: '/admin/procurement/rfq' },
      { label: 'Purchase Orders', href: '/admin/procurement/po' },
      { label: 'GRN', href: '/admin/procurement/grn' },
    ],
  },
  {
    label: 'Fixed Assets & Deposits',
    icon: HardDrive,
    children: [
      { label: 'Asset Register', href: '/admin/fixed-assets/assets' },
      { label: 'Depreciation Runs', href: '/admin/fixed-assets/depreciation' },
      { label: 'Physical Verification', href: '/admin/fixed-assets/verification' },
      { label: 'Disposal & Write-off', href: '/admin/fixed-assets/disposal' },
      { label: 'Fixed Asset Reports', href: '/admin/fixed-assets/reports' },
      { label: 'FD Dashboard', href: '/admin/fixed-deposits/dashboard' },
      { label: 'Deposits', href: '/admin/fixed-deposits' },
    ],
  },
  {
    label: 'Legal',
    icon: Gavel,
    children: [
      { label: 'Dashboard', href: '/admin/legal' },
      { label: 'Law Firms', href: '/admin/legal/law-firms' },
      { label: 'Advocates', href: '/admin/legal/advocates' },
      { label: 'Cases', href: '/admin/legal/cases' },
      { label: 'Notices', href: '/admin/legal/notices' },
      { label: 'Expenses', href: '/admin/legal/expenses' },
    ],
  },
  {
    label: 'Workflow',
    icon: GitBranch,
    children: [
      { label: 'My Tasks', href: '/admin/workflow/tasks' },
      { label: 'All Instances', href: '/admin/workflow/instances' },
      { label: 'Definitions', href: '/admin/workflow/definitions' },
    ],
  },
  {
    label: 'DMS',
    icon: FolderOpen,
    children: [
      { label: 'Dashboard', href: '/admin/dms' },
      { label: 'Document Studio', href: '/admin/dms/document-studio' },
      { label: 'Folders', href: '/admin/dms/folders' },
      { label: 'Upload', href: '/admin/dms/upload' },
      { label: 'Search', href: '/admin/dms/search' },
      { label: 'Tags', href: '/admin/dms/tags' },
    ],
  },
  {
    label: 'Portals & Notifications',
    icon: Bell,
    children: [
      { label: 'Portal Users', href: '/admin/portal/users' },
      { label: 'Portal Registrations', href: '/admin/portal/registrations' },
      { label: 'Notifications', href: '/admin/notifications' },
      { label: 'Notification Logs', href: '/admin/notifications/logs' },
    ],
  },
  {
    label: 'Settings',
    icon: Network,
    children: [
      { label: 'Organization Setup', href: '/admin/organizations' },
      { label: 'Units', href: '/admin/units' },
      { label: 'Departments', href: '/admin/departments' },
      { label: 'Designations', href: '/admin/designations' },
      { label: 'Users', href: '/admin/users' },
      { label: 'Roles', href: '/admin/roles' },
      { label: 'Financial Years', href: '/admin/finance/financial-years' },
      { label: 'Chart of Accounts', href: '/admin/finance/account-groups' },
      { label: 'Accounts', href: '/admin/finance/accounts' },
      { label: 'Voucher Types', href: '/admin/finance/voucher-types' },
      { label: 'Voucher Templates', href: '/admin/finance/voucher-templates' },
      { label: 'Payment Terms', href: '/admin/ap-ar/payment-terms' },
      { label: 'GST Rates', href: '/admin/gst/rates' },
      { label: 'GST Registrations', href: '/admin/gst/registrations' },
      { label: 'HSN/SAC Masters', href: '/admin/gst/hsn-sac' },
      { label: 'TDS Sections', href: '/admin/tds/sections' },
      { label: 'Lending Setup', href: '/admin/lending/masters' },
      { label: 'Asset Categories', href: '/admin/fixed-assets/categories' },
      { label: 'FD Products', href: '/admin/fixed-deposits/products' },
      { label: 'FD Interest Slabs', href: '/admin/fixed-deposits/interest' },
      { label: 'Shifts', href: '/admin/hris/shifts' },
      { label: 'Holiday Calendar', href: '/admin/hris/holidays' },
      { label: 'Leave Types', href: '/admin/hris/leave-types' },
      { label: 'Salary Components', href: '/admin/payroll/components' },
      { label: 'Salary Structures', href: '/admin/payroll/structures' },
      { label: 'Payroll Statutory Setup', href: '/admin/payroll/statutory' },
      { label: 'Item Categories', href: '/admin/inventory/categories' },
      { label: 'Warehouses', href: '/admin/inventory/warehouses' },
      { label: 'Compliance Items', href: '/admin/compliance/items' },
      { label: 'DMS Tags', href: '/admin/dms/tags' },
      { label: 'BI Chart Definitions', href: '/admin/bi/chart-definitions' },
      { label: 'BI Data Sources', href: '/admin/bi/data-sources' },
      { label: 'Integrations', href: '/admin/settings/integrations' },
      { label: 'Notification Settings', href: '/admin/notifications/settings' },
      { label: 'Notification Templates', href: '/admin/notifications/templates' },
    ],
  },
];

export function AdminLayout() {
  const location = useLocation();
  const navigate = useNavigate();
  const permissions = useAuthStore((state) => state.permissions);
  const { theme, setTheme, themes } = useAppTheme();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  // Single-open accordion: only one parent menu is expanded at a time.
  // Storing one string (not a list) makes the "only that menu activates"
  // contract obvious in the type.
  const [expandedItem, setExpandedItem] = useState<string | null>(null);
  const visibleNavItems = useMemo(
    () => filterNavItemsByAccess(navItems, permissions),
    [permissions],
  );

  const toggleExpand = (label: string) => {
    // Click on the open one → close it. Click on any other → switch.
    setExpandedItem((prev) => (prev === label ? null : label));
  };

  // Path matches a route if it equals it OR is a descendant of it
  // (separated by '/'). Plain startsWith would match `/admin/lending`
  // against `/admin/lending-foo` which is wrong, and would also let
  // siblings claim activity for nested routes.
  const isPathInside = useCallback(
    (href: string) => location.pathname === href || location.pathname.startsWith(href + '/'),
    [location.pathname],
  );

  const isActive = (href: string) => location.pathname === href;

  // For each parent, the "match length" is the length of the longest child
  // href that is a prefix of the current path. The parent with the longest
  // match wins — so /admin/lending/iif/enrollments activates "Interest
  // Subvention" (whose child '/admin/lending/iif/enrollments' is a full
  // match, length 38) rather than "Lending" (whose child '/admin/lending'
  // is only a prefix, length 14).
  const parentMatchLength = useCallback(
    (item: NavItem): number => {
      if (!item.children) return 0;
      let best = 0;
      for (const c of item.children) {
        if (isPathInside(c.href) && c.href.length > best) {
          best = c.href.length;
        }
      }
      return best;
    },
    [isPathInside],
  );

  // Find the single most-specific parent for the current path.
  const activeParentLabel = useMemo(() => {
    let label: string | null = null;
    let bestLength = 0;
    for (const item of visibleNavItems) {
      const len = parentMatchLength(item);
      if (len > bestLength) {
        bestLength = len;
        label = item.label;
      }
    }
    return label;
  }, [visibleNavItems, parentMatchLength]);

  const isParentActive = (item: NavItem) => activeParentLabel === item.label;

  // Auto-open the active parent on navigation, collapse everything else.
  useEffect(() => {
    setExpandedItem(activeParentLabel);
  }, [activeParentLabel]);

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    navigate('/login');
  };

  const renderNavItem = (item: NavItem) => {
    const hasChildren = item.children && item.children.length > 0;
    const isExpanded = expandedItem === item.label;
    const active = item.href ? isActive(item.href) : isParentActive(item);

    if (hasChildren) {
      return (
        <div key={item.label}>
          <button
            onClick={() => toggleExpand(item.label)}
            className={cn(
              'app-sidebar-item flex w-full items-center justify-between gap-3 rounded-lg px-3 py-2 text-left text-sm font-medium leading-5 transition-colors',
              active
                ? 'app-sidebar-item-active'
                : '',
            )}
          >
            <span className="flex min-w-0 flex-1 items-center gap-3">
              <item.icon className="h-4 w-4 shrink-0" />
              <span className="min-w-0 flex-1">{item.label}</span>
            </span>
            {isExpanded ? (
              <ChevronDown className="h-4 w-4 shrink-0" />
            ) : (
              <ChevronRight className="h-4 w-4 shrink-0" />
            )}
          </button>
          {isExpanded && (
            <div className="app-sidebar-subnav ml-4 mt-1 space-y-1 border-l pl-3">
              {item.children?.map((child) => (
                <Link
                  key={child.href}
                  to={child.href}
                  onClick={() => setSidebarOpen(false)}
                  className={cn(
                    'app-sidebar-item block rounded-lg px-3 py-2 text-left text-sm leading-5 transition-colors',
                    isActive(child.href)
                      ? 'app-sidebar-item-active font-medium'
                      : '',
                  )}
                >
                  {child.label}
                </Link>
              ))}
            </div>
          )}
        </div>
      );
    }

    return (
      <Link
        key={item.label}
        to={item.href!}
        onClick={() => setSidebarOpen(false)}
        className={cn(
          'app-sidebar-item flex items-center gap-3 rounded-lg px-3 py-2 text-left text-sm font-medium leading-5 transition-colors',
          active
            ? 'app-sidebar-item-active'
            : '',
        )}
      >
        <item.icon className="h-4 w-4 shrink-0" />
        <span className="min-w-0 flex-1">{item.label}</span>
      </Link>
    );
  };

  return (
    <div className="app-shell flex h-screen flex-col overflow-hidden text-slate-900">
      {/* Header - Fixed at top */}
      <header className="app-header z-30 flex-shrink-0 border-b">
        <div className="flex items-center gap-4 px-4 py-3 lg:px-6">
          <Button
            variant="ghost"
            size="icon"
            className="lg:hidden"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu className="h-5 w-5" />
          </Button>

          <div className="flex items-center gap-3">
            <div className="app-brand-mark flex h-10 w-10 items-center justify-center rounded-xl">
              <Building2 className="h-5 w-5" />
            </div>
            <div className="hidden sm:block">
              <p className="text-xs font-semibold text-slate-500">SMFCL ERP</p>
              <p className="text-sm font-semibold">Enterprise Command Center</p>
            </div>
          </div>

          <Separator orientation="vertical" className="hidden h-8 lg:block" />

          <div className="relative ml-auto hidden w-[320px] items-center lg:flex">
            <Search className="absolute left-3 h-4 w-4 text-slate-400" />
            <Input className="pl-9" placeholder="Search..." />
          </div>

          <div className="ml-auto flex items-center gap-1 lg:ml-0">
            <Button variant="ghost" size="icon">
              <HelpCircle className="h-5 w-5" />
            </Button>
            <Button variant="ghost" size="icon">
              <Bell className="h-5 w-5" />
            </Button>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" aria-label="Change appearance">
                  <Palette className="h-5 w-5" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-72">
                <DropdownMenuLabel>Appearance</DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuRadioGroup
                  value={theme}
                  onValueChange={(value) => setTheme(value as typeof theme)}
                >
                  {themes.map((themeOption) => (
                    <DropdownMenuRadioItem
                      key={themeOption.id}
                      value={themeOption.id}
                      className="items-start gap-3 py-2"
                    >
                      <div className="mt-0.5 flex gap-1.5">
                        {themeOption.swatches.map((swatch, index) => (
                          <span
                            key={`${themeOption.id}-${index}`}
                            className="app-theme-swatch h-3.5 w-3.5 rounded-full"
                            style={{ backgroundColor: swatch }}
                          />
                        ))}
                      </div>
                      <div className="min-w-0">
                        <div className="font-medium text-slate-900">{themeOption.label}</div>
                        <div className="text-xs leading-5 text-slate-500">
                          {themeOption.description}
                        </div>
                      </div>
                    </DropdownMenuRadioItem>
                  ))}
                </DropdownMenuRadioGroup>
              </DropdownMenuContent>
            </DropdownMenu>
            <Button variant="ghost" size="icon">
              <Settings className="h-5 w-5" />
            </Button>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="flex items-center gap-2">
                  <Avatar className="h-8 w-8">
                    <AvatarImage src="" alt="User" />
                    <AvatarFallback>AD</AvatarFallback>
                  </Avatar>
                  <span className="hidden text-sm font-medium md:inline">Admin</span>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-48">
                <DropdownMenuLabel>Account</DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem>Profile</DropdownMenuItem>
                <DropdownMenuItem>Preferences</DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={handleLogout}>
                  <LogOut className="mr-2 h-4 w-4" />
                  Sign out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </header>

      {/* Body - Sidebar and Main content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Mobile sidebar backdrop */}
        {sidebarOpen && (
          <button
            type="button"
            aria-label="Close navigation"
            className="fixed inset-0 z-40 bg-slate-950/50 lg:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        {/* Sidebar - Scrolls independently */}
        <aside
          className={cn(
            'app-sidebar fixed left-0 top-0 z-50 h-full w-80 transform border-r transition-transform lg:static lg:z-auto lg:h-auto lg:w-80 lg:translate-x-0',
            sidebarOpen ? 'translate-x-0' : '-translate-x-full',
          )}
        >
          <div className="flex h-full flex-col">
            <div className="flex items-center justify-between border-b border-slate-200/10 p-4 lg:hidden">
              <span className="font-semibold">Navigation</span>
              <Button variant="ghost" size="icon" onClick={() => setSidebarOpen(false)}>
                <X className="h-5 w-5" />
              </Button>
            </div>
            <div className="hidden border-b border-white/10 p-4 lg:block">
              <div className="flex items-center gap-3">
                <div className="app-brand-mark flex h-11 w-11 items-center justify-center rounded-xl">
                  <Building2 className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-xs font-semibold text-white/60">SMFCL ERP</p>
                  <p className="text-sm font-semibold text-white">Navigation</p>
                </div>
              </div>
            </div>
            <nav className="flex-1 space-y-1 overflow-y-auto p-4">
              {visibleNavItems.map(renderNavItem)}
            </nav>
          </div>
        </aside>

        {/* Main content - Scrolls independently */}
        <main className="app-main flex-1 overflow-y-auto p-4 lg:p-6">
          <RequireModuleAccess>
            <Outlet />
          </RequireModuleAccess>
        </main>
      </div>
    </div>
  );
}
