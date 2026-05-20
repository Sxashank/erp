/**
 * Scheme Portal Layout
 * Common layout wrapper with navigation for scheme portal pages
 */

import {
  Wallet,
  LayoutDashboard,
  FileText,
  Bell,
  User,
  LogOut,
  Menu,
  X,
  ChevronDown,
  FileSignature,
  Award,
  Building2,
  BarChart3,
} from 'lucide-react';
import { useState, useEffect } from 'react';
import { Outlet, Link, useNavigate, useLocation } from 'react-router-dom';

import { DateDisplay } from '@/components/common/DateDisplay';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useActiveEntity } from '@/hooks/portal/useActiveEntity';
import { resolvePortalActorRole } from '@/hooks/portal/usePortalSession';
import { clearPortalSession, portalAuthApi, portalCommunicationApi } from '@/services/portalApi';
import type { PortalUser, Notification } from '@/types/portal';

import { logger } from "@/lib/logger";
function navItemsForRole(role: string) {
  const base = [
    { label: 'Workbench', href: '/portal/workbench', icon: LayoutDashboard },
    { label: 'Applications', href: '/portal/applications', icon: FileSignature },
    { label: 'Claims', href: '/portal/claims', icon: Award },
    { label: 'Reports', href: '/portal/reports', icon: BarChart3 },
  ];
  if (role === 'scheme_borrower') {
    return [
      ...base,
      { label: 'Loans', href: '/portal/loans', icon: Wallet },
      { label: 'Documents', href: '/portal/documents', icon: FileText },
    ];
  }
  if (role === 'scheme_smfcl_reviewer' || role === 'scheme_admin') {
    return [...base, { label: 'Registrations', href: '/portal/registrations', icon: FileText }];
  }
  return base;
}

function resolvePortalUserDisplayName(user: PortalUser | null): string {
  return user?.displayName || user?.display_name || user?.fullName || user?.full_name || 'Borrower';
}

export default function PortalLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const [user, setUser] = useState<PortalUser | null>(null);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { entities, activeEntityId, setActiveEntityId, setEntities } = useActiveEntity();
  const showEntitySwitcher = entities.length > 1;
  const actorRole = resolvePortalActorRole(user);
  const navItems = navItemsForRole(actorRole);

  useEffect(() => {
    const token = localStorage.getItem('portal_access_token');
    if (!token) {
      navigate('/portal/login');
      return;
    }

    const storedUser = localStorage.getItem('portal_user');
    if (storedUser) {
      const parsed = JSON.parse(storedUser) as PortalUser;
      setUser(parsed);
      const linked = parsed.linkedEntities ?? parsed.linked_entities ?? [];
      setEntities(
        linked.map((entity) => ({
          id: entity.id,
          legalName:
            ('legalName' in entity ? entity.legalName : undefined) ??
            ('legal_name' in entity ? entity.legal_name : undefined) ??
            entity.id,
        })),
      );
    }

    fetchNotifications();
  }, [navigate, setEntities]);

  const fetchNotifications = async () => {
    try {
      const response = await portalCommunicationApi.getNotifications({ unread_only: true });
      const items = Array.isArray(response.data) ? response.data : (response.data.items ?? []);
      setNotifications(items.slice(0, 5));
      setUnreadCount(items.filter((notification: Notification) => !notification.is_read).length);
    } catch (error) {
      logger.error('Failed to fetch notifications:', error);
    }
  };

  const handleLogout = async () => {
    try {
      await portalAuthApi.logout();
    } catch (error) {
      logger.error('Logout error:', error);
    } finally {
      clearPortalSession();
      setEntities([]);
      navigate('/portal/login');
    }
  };

  const markNotificationRead = async (notificationId: string) => {
    try {
      await portalCommunicationApi.markAsRead(notificationId);
      setNotifications((prev) => prev.filter((n) => n.id !== notificationId));
      setUnreadCount((prev) => Math.max(0, prev - 1));
    } catch (error) {
      logger.error('Failed to mark notification as read:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="sticky top-0 z-50 border-b bg-white">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex h-16 items-center justify-between">
            {/* Logo */}
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-emerald-600 p-2">
                <Wallet className="h-5 w-5 text-white" />
              </div>
              <span className="text-lg font-bold text-gray-900">Scheme Portal</span>
            </div>

            {/* Desktop Navigation */}
            <nav className="hidden items-center gap-1 md:flex">
              {navItems.map((item) => {
                const isActive = location.pathname.startsWith(item.href);
                return (
                  <Link
                    key={`${item.href}:${item.label}`}
                    to={item.href}
                    className={`flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                      isActive
                        ? 'bg-emerald-50 text-emerald-700'
                        : 'text-gray-600 hover:bg-gray-100'
                    }`}
                  >
                    <item.icon className="h-4 w-4" />
                    {item.label}
                  </Link>
                );
              })}
            </nav>

            {/* Right Section */}
            <div className="flex items-center gap-2">
              {/* Entity Switcher (only if user has multiple linked entities) */}
              {showEntitySwitcher && (
                <div className="hidden items-center gap-2 md:flex">
                  <Building2 className="h-4 w-4 text-gray-500" aria-hidden="true" />
                  <Select
                    value={activeEntityId ?? ''}
                    onValueChange={(v) => setActiveEntityId(v || null)}
                  >
                    <SelectTrigger className="h-9 w-[200px]">
                      <SelectValue placeholder="Choose an organisation" />
                    </SelectTrigger>
                    <SelectContent>
                      {entities.map((e) => (
                        <SelectItem key={e.id} value={e.id}>
                          {e.legalName}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}
              {/* Notifications */}
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="icon" className="relative">
                    <Bell className="h-5 w-5" />
                    {unreadCount > 0 && (
                      <Badge className="absolute -right-1 -top-1 flex h-5 w-5 items-center justify-center bg-red-500 p-0">
                        {unreadCount}
                      </Badge>
                    )}
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-80">
                  <DropdownMenuLabel>Notifications</DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  {notifications.length > 0 ? (
                    notifications.map((notification) => (
                      <DropdownMenuItem
                        key={notification.id}
                        className="flex cursor-pointer flex-col items-start gap-1 p-3"
                        onClick={() => markNotificationRead(notification.id)}
                      >
                        <span className="text-sm font-medium">{notification.title}</span>
                        <span className="line-clamp-2 text-xs text-gray-500">
                          {notification.message}
                        </span>
                        <DateDisplay date={notification.created_at} className="text-xs text-gray-400" />
                      </DropdownMenuItem>
                    ))
                  ) : (
                    <div className="p-4 text-center text-sm text-gray-500">
                      No new notifications
                    </div>
                  )}
                </DropdownMenuContent>
              </DropdownMenu>

              {/* User Menu */}
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" className="flex items-center gap-2">
                    <div className="flex h-8 w-8 items-center justify-center rounded-full bg-emerald-100">
                      <User className="h-4 w-4 text-emerald-600" />
                    </div>
                    <span className="hidden text-sm font-medium md:inline">
                      {resolvePortalUserDisplayName(user)}
                    </span>
                    <ChevronDown className="hidden h-4 w-4 md:inline" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-56">
                  <DropdownMenuLabel>
                    <div>
                      <p className="font-medium">{resolvePortalUserDisplayName(user)}</p>
                      <p className="text-xs text-gray-500">{user?.mobile}</p>
                    </div>
                  </DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={handleLogout} className="text-red-600">
                    <LogOut className="mr-2 h-4 w-4" />
                    Sign Out
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>

              {/* Mobile Menu Button */}
              <Button
                variant="ghost"
                size="icon"
                className="md:hidden"
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              >
                {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
              </Button>
            </div>
          </div>
        </div>

        {/* Mobile Navigation */}
        {mobileMenuOpen && (
          <nav className="border-t bg-white md:hidden">
            <div className="space-y-1 px-4 py-2">
              {navItems.map((item) => {
                const isActive = location.pathname.startsWith(item.href);
                return (
                  <Link
                    key={item.href}
                    to={item.href}
                    onClick={() => setMobileMenuOpen(false)}
                    className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium ${
                      isActive
                        ? 'bg-emerald-50 text-emerald-700'
                        : 'text-gray-600 hover:bg-gray-100'
                    }`}
                  >
                    <item.icon className="h-5 w-5" />
                    {item.label}
                  </Link>
                );
              })}
            </div>
          </nav>
        )}
      </header>

      {/* Main Content */}
      <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="mt-auto border-t bg-white">
        <div className="mx-auto max-w-7xl px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex flex-col items-center justify-between gap-4 text-sm text-gray-500 md:flex-row">
            <p>&copy; {new Date().getFullYear()} TalentFino. All rights reserved.</p>
            <div className="flex items-center gap-4">
              <span>Institutional borrower access only</span>
              <span>SMFCL scheme operations</span>
              <span>Support via scheme administrator</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
