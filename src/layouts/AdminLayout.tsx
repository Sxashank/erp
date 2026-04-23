import { useState } from 'react';
import { Link, Outlet, useLocation, useNavigate } from 'react-router-dom';
import {
  Building2,
  Bell,
  BookOpen,
  Calculator,
  Calendar,
  ChevronDown,
  ChevronRight,
  FileText,
  FolderTree,
  HelpCircle,
  LayoutGrid,
  LogOut,
  Menu,
  Receipt,
  Search,
  Settings,
  Shield,
  Users,
  Network,
  Briefcase,
  Building,
  X,
  Percent,
  FileSpreadsheet,
  BarChart3,
  CreditCard,
  Landmark,
  Scale,
  Wallet,
  FileCheck,
  Banknote,
  TrendingUp,
  AlertTriangle,
  Gavel,
  Package,
  Truck,
  ClipboardCheck,
  FolderOpen,
  PieChart,
  UserCheck,
  DollarSign,
  GitBranch,
  HardDrive,
  Wrench,
} from 'lucide-react';

import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Input } from '@/components/ui/input';
import { Separator } from '@/components/ui/separator';
import { cn } from '@/lib/utils';

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
    label: 'Masters',
    icon: Building,
    children: [
      { label: 'Organizations', href: '/admin/organizations' },
      { label: 'Units', href: '/admin/units' },
      { label: 'Departments', href: '/admin/departments' },
      { label: 'Designations', href: '/admin/designations' },
    ],
  },
  {
    label: 'Finance',
    icon: Calculator,
    children: [
      { label: 'Financial Years', href: '/admin/finance/financial-years' },
      { label: 'Chart of Accounts', href: '/admin/finance/account-groups' },
      { label: 'Accounts', href: '/admin/finance/accounts' },
      { label: 'Voucher Types', href: '/admin/finance/voucher-types' },
      { label: 'Vouchers', href: '/admin/finance/vouchers' },
      { label: 'Voucher Templates', href: '/admin/finance/voucher-templates' },
      { label: 'Recurring Vouchers', href: '/admin/finance/recurring-vouchers' },
      { label: 'Year-End Closing', href: '/admin/finance/year-end-closing' },
    ],
  },
  {
    label: 'GST',
    icon: Percent,
    children: [
      { label: 'GST Rates', href: '/admin/gst/rates' },
    ],
  },
  {
    label: 'TDS/TCS',
    icon: FileText,
    children: [
      { label: 'TDS Sections', href: '/admin/tds/sections' },
    ],
  },
  {
    label: 'AP/AR',
    icon: CreditCard,
    children: [
      { label: 'Payment Terms', href: '/admin/ap-ar/payment-terms' },
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
    label: 'Reports',
    icon: BarChart3,
    children: [
      { label: 'Trial Balance', href: '/admin/reports/trial-balance' },
      { label: 'Profit & Loss', href: '/admin/reports/profit-loss' },
      { label: 'Balance Sheet', href: '/admin/reports/balance-sheet' },
      { label: 'Cash Flow Statement', href: '/admin/reports/cash-flow-statement' },
      { label: 'Account Ledger', href: '/admin/reports/account-ledger' },
      { label: 'Day Book', href: '/admin/reports/day-book' },
    ],
  },
  {
    label: 'User Management',
    icon: Users,
    children: [
      { label: 'Users', href: '/admin/users' },
      { label: 'Roles', href: '/admin/roles' },
    ],
  },
  {
    label: 'Lending',
    icon: Landmark,
    children: [
      { label: 'Dashboard', href: '/admin/lending' },
      { label: 'Entities/Borrowers', href: '/admin/lending/entities' },
      { label: 'Loan Products', href: '/admin/lending/products' },
      { label: 'Applications', href: '/admin/lending/applications' },
      { label: 'Sanctions', href: '/admin/lending/sanctions' },
      { label: 'Loan Accounts', href: '/admin/lending/accounts' },
      { label: 'Disbursements', href: '/admin/lending/disbursements' },
      { label: 'Receipts', href: '/admin/lending/receipts' },
      { label: 'Follow-ups', href: '/admin/lending/collections/followups' },
      { label: 'NPA Accounts', href: '/admin/lending/collections/npa' },
      { label: 'OTS Proposals', href: '/admin/lending/collections/ots' },
      { label: 'Legal Cases', href: '/admin/lending/collections/legal' },
      { label: 'NACH Batches', href: '/admin/lending/nach/batches' },
      { label: 'AA Consents', href: '/admin/lending/aa/consents' },
      { label: 'AA Fetched Data', href: '/admin/lending/aa/fetched-data' },
      { label: 'Reports & Analytics', href: '/admin/lending/reports' },
    ],
  },
  {
    label: 'Treasury',
    icon: Wallet,
    children: [
      { label: 'Dashboard', href: '/admin/treasury' },
      { label: 'Lenders', href: '/admin/treasury/lenders' },
      { label: 'Borrowings', href: '/admin/treasury/borrowings' },
      { label: 'ALM Dashboard', href: '/admin/treasury/alm' },
      { label: 'Gap Analysis', href: '/admin/treasury/alm/gap' },
      { label: 'Interest Rate Risk', href: '/admin/treasury/alm/irs' },
      { label: 'Risk Dashboard', href: '/admin/treasury/risk-dashboard' },
      { label: 'Investments', href: '/admin/treasury/investments' },
    ],
  },
  {
    label: 'Regulatory',
    icon: FileCheck,
    children: [
      { label: 'CRAR Dashboard', href: '/admin/regulatory/crar' },
      { label: 'Exposure Reports', href: '/admin/regulatory/exposure' },
      { label: 'Infrastructure Ratio', href: '/admin/regulatory/infrastructure' },
      { label: 'Returns Calendar', href: '/admin/regulatory/returns' },
    ],
  },
  {
    label: 'Fixed Assets',
    icon: HardDrive,
    children: [
      { label: 'Asset Categories', href: '/admin/fixed-assets/categories' },
      { label: 'Asset Register', href: '/admin/fixed-assets/assets' },
      { label: 'Depreciation Runs', href: '/admin/fixed-assets/depreciation' },
      { label: 'Physical Verification', href: '/admin/fixed-assets/verification' },
      { label: 'Maintenance & AMC', href: '/admin/fixed-assets/maintenance' },
      { label: 'Insurance', href: '/admin/fixed-assets/insurance' },
      { label: 'Disposal & Write-off', href: '/admin/fixed-assets/disposal' },
    ],
  },
  {
    label: 'HRIS',
    icon: Users,
    children: [
      { label: 'Dashboard', href: '/admin/hris' },
      { label: 'Employees', href: '/admin/hris/employees' },
      { label: 'Shifts', href: '/admin/hris/shifts' },
      { label: 'Holiday Calendar', href: '/admin/hris/holidays' },
      { label: 'Leave Types', href: '/admin/hris/leave-types' },
      { label: 'Leave Applications', href: '/admin/hris/leave-applications' },
      { label: 'Attendance', href: '/admin/hris/attendance' },
      { label: 'Separation & F&F', href: '/admin/hris/separation' },
      { label: 'Training', href: '/admin/hris/training' },
      { label: 'Performance', href: '/admin/hris/performance/cycles' },
    ],
  },
  {
    label: 'Payroll',
    icon: DollarSign,
    children: [
      { label: 'Salary Components', href: '/admin/payroll/components' },
      { label: 'Salary Structures', href: '/admin/payroll/structures' },
      { label: 'Employee Salary', href: '/admin/payroll/employee-salary' },
      { label: 'Statutory Setup', href: '/admin/payroll/statutory' },
      { label: 'Payroll Batches', href: '/admin/payroll/batches' },
    ],
  },
  {
    label: 'Workflow',
    icon: GitBranch,
    children: [
      { label: 'Definitions', href: '/admin/workflow/definitions' },
      { label: 'My Tasks', href: '/admin/workflow/tasks' },
      { label: 'All Instances', href: '/admin/workflow/instances' },
    ],
  },
  {
    label: 'Inventory',
    icon: Package,
    children: [
      { label: 'Dashboard', href: '/admin/inventory' },
      { label: 'Item Categories', href: '/admin/inventory/categories' },
      { label: 'Items', href: '/admin/inventory/items' },
      { label: 'Warehouses', href: '/admin/inventory/warehouses' },
      { label: 'Stock In', href: '/admin/inventory/stock-in' },
      { label: 'Stock Out', href: '/admin/inventory/stock-out' },
      { label: 'Stock Transfer', href: '/admin/inventory/stock-transfer' },
      { label: 'Valuation', href: '/admin/inventory/valuation' },
    ],
  },
  {
    label: 'Procurement',
    icon: Truck,
    children: [
      { label: 'RFQ', href: '/admin/procurement/rfq' },
      { label: 'Purchase Orders', href: '/admin/procurement/po' },
      { label: 'GRN', href: '/admin/procurement/grn' },
    ],
  },
  {
    label: 'Compliance',
    icon: ClipboardCheck,
    children: [
      { label: 'Dashboard', href: '/admin/compliance' },
      { label: 'Compliance Items', href: '/admin/compliance/items' },
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
    label: 'DMS',
    icon: FolderOpen,
    children: [
      { label: 'Dashboard', href: '/admin/dms' },
      { label: 'Folders', href: '/admin/dms/folders' },
      { label: 'Upload', href: '/admin/dms/upload' },
      { label: 'Search', href: '/admin/dms/search' },
      { label: 'Tags', href: '/admin/dms/tags' },
    ],
  },
  {
    label: 'BI & Analytics',
    icon: PieChart,
    children: [
      { label: 'Dashboards', href: '/admin/bi/dashboards' },
      { label: 'Chart Definitions', href: '/admin/bi/chart-definitions' },
      { label: 'Data Sources', href: '/admin/bi/data-sources' },
    ],
  },
  {
    label: 'Settings',
    icon: Network,
    children: [
      { label: 'Integrations', href: '/admin/settings/integrations' },
      { label: 'Notifications', href: '/admin/notifications' },
      { label: 'Templates', href: '/admin/notifications/templates' },
    ],
  },
];

export function AdminLayout() {
  const location = useLocation();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [expandedItems, setExpandedItems] = useState<string[]>([]);

  const toggleExpand = (label: string) => {
    setExpandedItems((prev) =>
      prev.includes(label) ? prev.filter((item) => item !== label) : [...prev, label]
    );
  };

  const isActive = (href: string) => location.pathname === href;
  const isParentActive = (children?: { label: string; href: string }[]) =>
    children?.some((child) => location.pathname.startsWith(child.href));

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    navigate('/login');
  };

  const renderNavItem = (item: NavItem) => {
    const hasChildren = item.children && item.children.length > 0;
    const isExpanded = expandedItems.includes(item.label);
    const active = item.href ? isActive(item.href) : isParentActive(item.children);

    if (hasChildren) {
      return (
        <div key={item.label}>
          <button
            onClick={() => toggleExpand(item.label)}
            className={cn(
              'flex w-full items-center justify-between gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
              active
                ? 'bg-blue-50 text-blue-700'
                : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
            )}
          >
            <span className="flex items-center gap-2">
              <item.icon className="h-4 w-4" />
              {item.label}
            </span>
            {isExpanded ? (
              <ChevronDown className="h-4 w-4" />
            ) : (
              <ChevronRight className="h-4 w-4" />
            )}
          </button>
          {isExpanded && (
            <div className="ml-4 mt-1 space-y-1 border-l border-slate-200 pl-3">
              {item.children?.map((child) => (
                <Link
                  key={child.href}
                  to={child.href}
                  onClick={() => setSidebarOpen(false)}
                  className={cn(
                    'block rounded-lg px-3 py-2 text-sm transition-colors',
                    isActive(child.href)
                      ? 'bg-blue-50 font-medium text-blue-700'
                      : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
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
          'flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
          active
            ? 'bg-blue-50 text-blue-700'
            : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
        )}
      >
        <item.icon className="h-4 w-4" />
        {item.label}
      </Link>
    );
  };

  return (
    <div className="h-screen flex flex-col bg-slate-50 text-slate-900 overflow-hidden">
      {/* Header - Fixed at top */}
      <header className="flex-shrink-0 z-30 border-b border-slate-200 bg-white">
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
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-600 text-white">
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
          <div
            className="fixed inset-0 z-40 bg-black/50 lg:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        {/* Sidebar - Scrolls independently */}
        <aside
          className={cn(
            'fixed top-0 left-0 z-50 h-full w-64 transform border-r border-slate-200 bg-white transition-transform lg:static lg:z-auto lg:h-auto lg:translate-x-0',
            sidebarOpen ? 'translate-x-0' : '-translate-x-full'
          )}
        >
          <div className="flex h-full flex-col">
            <div className="flex items-center justify-between border-b border-slate-200 p-4 lg:hidden">
              <span className="font-semibold">Navigation</span>
              <Button variant="ghost" size="icon" onClick={() => setSidebarOpen(false)}>
                <X className="h-5 w-5" />
              </Button>
            </div>
            <nav className="flex-1 space-y-1 overflow-y-auto p-4">
              {navItems.map(renderNavItem)}
            </nav>
          </div>
        </aside>

        {/* Main content - Scrolls independently */}
        <main className="flex-1 overflow-y-auto p-4 lg:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
