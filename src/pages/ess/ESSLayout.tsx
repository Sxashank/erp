/**
 * ESS Portal Layout
 * Wrapper layout for all ESS pages with navigation
 */

import {
  LayoutDashboard,
  User,
  FileText,
  Receipt,
  HelpCircle,
  Calculator,
  Clock,
  CalendarCheck,
  Laptop,
  GraduationCap,
  Target,
  ClipboardCheck,
  LogOut,
  Menu,
  X,
  Bell,
  Building2,
  ChevronRight,
} from 'lucide-react';
import { useState } from 'react';
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom';

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
import { cn } from '@/lib/utils';
import { useEssAuthStore } from '@/stores/essAuthStore';

const navItems = [
  { label: 'Dashboard', href: '/ess/dashboard', icon: LayoutDashboard },
  { label: 'Profile', href: '/ess/profile', icon: User },
  { label: 'Attendance', href: '/ess/attendance', icon: Clock },
  { label: 'Leave', href: '/ess/leave', icon: CalendarCheck },
  { label: 'Payslips', href: '/ess/payslips', icon: FileText },
  { label: 'Reimbursements', href: '/ess/reimbursements', icon: Receipt },
  { label: 'Helpdesk', href: '/ess/helpdesk', icon: HelpCircle },
  { label: 'IT Declaration', href: '/ess/it-declaration', icon: Calculator },
  { label: 'Assets', href: '/ess/assets', icon: Laptop },
  { label: 'Training', href: '/ess/training', icon: GraduationCap },
  { label: 'Goals', href: '/ess/goals', icon: Target },
  { label: 'Self Appraisal', href: '/ess/self-appraisal', icon: ClipboardCheck },
];

export default function ESSLayout() {
  const location = useLocation();
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const user = useEssAuthStore((state) => state.user);
  const clearSession = useEssAuthStore((state) => state.clear);

  const handleLogout = () => {
    clearSession();
    navigate('/ess/login');
  };

  const navigation = (
    <nav className="flex flex-col gap-1">
      {navItems.map((item) => {
        const isActive = location.pathname === item.href;
        return (
          <Link
            key={item.href}
            to={item.href}
            onClick={() => setMobileMenuOpen(false)}
            className={cn(
              'flex items-center justify-between rounded-lg px-4 py-3 text-sm font-medium transition-colors',
              isActive
                ? 'bg-blue-50 text-blue-700'
                : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900',
            )}
          >
            <div className="flex min-w-0 items-center gap-3">
              <item.icon className="h-5 w-5 shrink-0" />
              <span className="truncate">{item.label}</span>
            </div>
            <ChevronRight
              className={cn('h-4 w-4 shrink-0', isActive ? 'opacity-100' : 'opacity-40')}
            />
          </Link>
        );
      })}
    </nav>
  );

  const utilityMenu = (
    <div className="flex items-center gap-2">
      <Button variant="ghost" size="icon" className="relative">
        <Bell className="h-5 w-5" />
        <span className="absolute right-1 top-1 h-2 w-2 rounded-full bg-red-500" />
      </Button>

      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" className="flex min-w-0 items-center gap-2 px-2">
            <Avatar className="h-8 w-8 shrink-0">
              <AvatarImage src="" />
              <AvatarFallback className="bg-blue-600 text-sm text-white">
                {(user?.employeeName ?? user?.name)?.charAt(0) || 'E'}
              </AvatarFallback>
            </Avatar>
            <span className="hidden max-w-[120px] truncate text-sm font-medium sm:block lg:inline">
              {user?.employeeName ?? user?.name ?? 'Employee'}
            </span>
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-56">
          <DropdownMenuLabel>
            <div>
              <p className="font-medium">{user?.employeeName ?? user?.name}</p>
              <p className="text-xs text-gray-500">{user?.employeeCode}</p>
            </div>
          </DropdownMenuLabel>
          <DropdownMenuSeparator />
          <DropdownMenuItem onClick={() => navigate('/ess/profile')}>
            <User className="mr-2 h-4 w-4" />
            My Profile
          </DropdownMenuItem>
          <DropdownMenuItem onClick={() => navigate('/ess/settings')}>Settings</DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem onClick={handleLogout} className="text-red-600">
            <LogOut className="mr-2 h-4 w-4" />
            Logout
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50 lg:pl-64">
      {/* Mobile Navigation */}
      <header className="sticky top-0 z-50 border-b bg-white shadow-sm lg:hidden">
        <div className="flex h-16 items-center justify-between px-4">
          {/* Logo & Mobile Menu Toggle */}
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" onClick={() => setMobileMenuOpen(!mobileMenuOpen)}>
              {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </Button>
            <Link to="/ess/dashboard" className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600">
                <Building2 className="h-5 w-5 text-white" />
              </div>
              <span className="hidden text-lg font-semibold sm:block">ESS Portal</span>
            </Link>
          </div>

          {utilityMenu}
        </div>

        {/* Mobile Navigation Menu */}
        {mobileMenuOpen && (
          <div className="max-h-[calc(100vh-4rem)] overflow-y-auto border-t bg-white p-4 lg:hidden">
            {navigation}
          </div>
        )}
      </header>

      <aside className="fixed inset-y-0 left-0 z-50 hidden w-64 border-r bg-white lg:block">
        <div className="flex h-full flex-col overflow-y-auto p-4">
          <Link to="/ess/dashboard" className="mb-8 flex h-12 items-center gap-3 px-2">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-blue-600">
              <Building2 className="h-5 w-5 text-white" />
            </div>
            <div className="min-w-0">
              <p className="truncate text-base font-semibold text-gray-900">ESS Portal</p>
              <p className="truncate text-xs text-gray-500">Employee Self Service</p>
            </div>
          </Link>
          <div className="mb-3 px-4 text-xs font-semibold uppercase tracking-wide text-gray-400">
            Employee Services
          </div>
          <div className="min-h-0 flex-1">{navigation}</div>
          <div className="mt-4 border-t pt-4">{utilityMenu}</div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="mx-auto max-w-7xl px-4 py-6 lg:px-8 lg:py-8">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="mt-auto border-t bg-white py-4">
        <div className="mx-auto max-w-7xl px-4 text-center text-sm text-gray-500 lg:px-8">
          <p>© {new Date().getFullYear()} Employee Self Service Portal. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}
