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

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top Navigation */}
      <header className="sticky top-0 z-50 border-b bg-white shadow-sm">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4">
          {/* Logo & Mobile Menu Toggle */}
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="icon"
              className="md:hidden"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            >
              {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </Button>
            <Link to="/ess/dashboard" className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600">
                <Building2 className="h-5 w-5 text-white" />
              </div>
              <span className="hidden text-lg font-semibold sm:block">ESS Portal</span>
            </Link>
          </div>

          {/* Desktop Navigation */}
          <nav className="hidden items-center gap-1 md:flex">
            {navItems.map((item) => {
              const isActive = location.pathname === item.href;
              return (
                <Link
                  key={item.href}
                  to={item.href}
                  className={cn(
                    'flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-blue-50 text-blue-700'
                      : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900',
                  )}
                >
                  <item.icon className="h-4 w-4" />
                  <span className="hidden lg:inline">{item.label}</span>
                </Link>
              );
            })}
          </nav>

          {/* Right Side - Notifications & User Menu */}
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="icon" className="relative">
              <Bell className="h-5 w-5" />
              <span className="absolute right-1 top-1 h-2 w-2 rounded-full bg-red-500" />
            </Button>

            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="flex items-center gap-2 px-2">
                  <Avatar className="h-8 w-8">
                    <AvatarImage src="" />
                    <AvatarFallback className="bg-blue-600 text-sm text-white">
                      {(user?.employee_name ?? user?.name)?.charAt(0) || 'E'}
                    </AvatarFallback>
                  </Avatar>
                  <span className="hidden max-w-[120px] truncate text-sm font-medium sm:block">
                    {user?.employee_name ?? user?.name ?? 'Employee'}
                  </span>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56">
                <DropdownMenuLabel>
                  <div>
                    <p className="font-medium">{user?.employee_name ?? user?.name}</p>
                    <p className="text-xs text-gray-500">{user?.employee_code}</p>
                  </div>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={() => navigate('/ess/profile')}>
                  <User className="mr-2 h-4 w-4" />
                  My Profile
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => navigate('/ess/settings')}>
                  Settings
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={handleLogout} className="text-red-600">
                  <LogOut className="mr-2 h-4 w-4" />
                  Logout
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>

        {/* Mobile Navigation Menu */}
        {mobileMenuOpen && (
          <div className="border-t bg-white md:hidden">
            <nav className="flex flex-col space-y-1 p-4">
              {navItems.map((item) => {
                const isActive = location.pathname === item.href;
                return (
                  <Link
                    key={item.href}
                    to={item.href}
                    onClick={() => setMobileMenuOpen(false)}
                    className={cn(
                      'flex items-center justify-between rounded-lg px-4 py-3 text-sm font-medium transition-colors',
                      isActive ? 'bg-blue-50 text-blue-700' : 'text-gray-600 hover:bg-gray-100',
                    )}
                  >
                    <div className="flex items-center gap-3">
                      <item.icon className="h-5 w-5" />
                      {item.label}
                    </div>
                    <ChevronRight className="h-4 w-4" />
                  </Link>
                );
              })}
            </nav>
          </div>
        )}
      </header>

      {/* Main Content */}
      <main className="mx-auto max-w-7xl px-4 py-6">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="mt-auto border-t bg-white py-4">
        <div className="mx-auto max-w-7xl px-4 text-center text-sm text-gray-500">
          <p>© {new Date().getFullYear()} Employee Self Service Portal. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}
