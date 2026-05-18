/**
 * Vendor Portal Layout Component
 */

import {
  LayoutDashboard,
  FileText,
  ShoppingCart,
  Truck,
  CreditCard,
  Shield,
  User,
  Bell,
  LogOut,
  Menu,
  X,
  ChevronDown,
  Building2,
} from 'lucide-react';
import { useState, useEffect } from 'react';
import { Link, Outlet, useNavigate, useLocation } from 'react-router-dom';

import { Avatar, AvatarFallback } from '@/components/ui/avatar';
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
import { useToast } from '@/hooks/use-toast';
import { vendorComplianceApi } from '@/services/vendorApi';
import type { VendorUser } from '@/types/vendor';

import { logger } from "@/lib/logger";
const navigation = [
  { name: 'Dashboard', href: '/vendor/dashboard', icon: LayoutDashboard },
  { name: 'Purchase Orders', href: '/vendor/purchase-orders', icon: ShoppingCart },
  { name: 'Invoices', href: '/vendor/invoices', icon: FileText },
  { name: 'Shipments (ASN)', href: '/vendor/asn', icon: Truck },
  { name: 'Payments', href: '/vendor/payments', icon: CreditCard },
  { name: 'Compliance', href: '/vendor/compliance', icon: Shield },
  { name: 'Profile', href: '/vendor/profile', icon: User },
];

export default function VendorLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const { toast } = useToast();

  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [user, setUser] = useState<VendorUser | null>(null);
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    // Check authentication
    const token = localStorage.getItem('vendor_access_token');
    const userStr = localStorage.getItem('vendor_user');

    if (!token || !userStr) {
      navigate('/vendor/login');
      return;
    }

    try {
      const userData = JSON.parse(userStr);
      setUser(userData);
    } catch {
      navigate('/vendor/login');
    }
  }, [navigate]);

  useEffect(() => {
    // Fetch unread notification count
    const fetchNotifications = async () => {
      try {
        const response = await vendorComplianceApi.getUnreadCount();
        setUnreadCount(response.data.unread_count);
      } catch (error) {
        logger.error('Failed to fetch notifications:', error);
      }
    };

    if (user) {
      fetchNotifications();
      // Poll every 30 seconds
      const interval = setInterval(fetchNotifications, 30000);
      return () => clearInterval(interval);
    }
  }, [user]);

  const handleLogout = () => {
    localStorage.removeItem('vendor_access_token');
    localStorage.removeItem('vendor_refresh_token');
    localStorage.removeItem('vendor_user');
    toast({ title: 'Logged out successfully' });
    navigate('/vendor/login');
  };

  const getInitials = () => {
    if (!user) return 'V';
    const first = user.first_name?.[0] || '';
    const last = user.last_name?.[0] || '';
    return (first + last).toUpperCase() || 'V';
  };

  if (!user) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-purple-600 shadow-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo */}
            <div className="flex items-center">
              <Link to="/vendor/dashboard" className="flex items-center space-x-2">
                <div className="w-8 h-8 bg-white rounded-lg flex items-center justify-center">
                  <Building2 className="h-5 w-5 text-purple-600" />
                </div>
                <span className="text-white font-semibold text-lg hidden sm:block">
                  Vendor Portal
                </span>
              </Link>
            </div>

            {/* Desktop Navigation */}
            <nav className="hidden md:flex space-x-1">
              {navigation.map((item) => {
                const isActive = location.pathname === item.href ||
                  location.pathname.startsWith(item.href + '/');
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                      isActive
                        ? 'bg-purple-700 text-white'
                        : 'text-purple-100 hover:bg-purple-500 hover:text-white'
                    }`}
                  >
                    {item.name}
                  </Link>
                );
              })}
            </nav>

            {/* Right side - Notifications & User Menu */}
            <div className="flex items-center space-x-4">
              {/* Notifications */}
              <Button
                variant="ghost"
                size="icon"
                className="relative text-white hover:bg-purple-500"
                onClick={() => navigate('/vendor/notifications')}
              >
                <Bell className="h-5 w-5" />
                {unreadCount > 0 && (
                  <Badge
                    className="absolute -top-1 -right-1 h-5 w-5 flex items-center justify-center p-0 bg-red-500 text-white text-xs"
                  >
                    {unreadCount > 9 ? '9+' : unreadCount}
                  </Badge>
                )}
              </Button>

              {/* User Menu */}
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" className="flex items-center space-x-2 text-white hover:bg-purple-500">
                    <Avatar className="h-8 w-8">
                      <AvatarFallback className="bg-purple-800 text-white text-sm">
                        {getInitials()}
                      </AvatarFallback>
                    </Avatar>
                    <span className="hidden sm:block text-sm font-medium">
                      {user.first_name}
                    </span>
                    <ChevronDown className="h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-56">
                  <DropdownMenuLabel>
                    <div className="flex flex-col space-y-1">
                      <p className="text-sm font-medium">
                        {user.first_name} {user.last_name}
                      </p>
                      <p className="text-xs text-gray-500 truncate">{user.email}</p>
                    </div>
                  </DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={() => navigate('/vendor/profile')}>
                    <User className="mr-2 h-4 w-4" />
                    Profile Settings
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={handleLogout} className="text-red-600">
                    <LogOut className="mr-2 h-4 w-4" />
                    Sign out
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>

              {/* Mobile menu button */}
              <Button
                variant="ghost"
                size="icon"
                className="md:hidden text-white hover:bg-purple-500"
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              >
                {mobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
              </Button>
            </div>
          </div>
        </div>

        {/* Mobile Navigation */}
        {mobileMenuOpen && (
          <div className="md:hidden bg-purple-700 border-t border-purple-500">
            <div className="px-2 pt-2 pb-3 space-y-1">
              {navigation.map((item) => {
                const isActive = location.pathname === item.href ||
                  location.pathname.startsWith(item.href + '/');
                const Icon = item.icon;
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={`flex items-center px-3 py-2 rounded-md text-base font-medium ${
                      isActive
                        ? 'bg-purple-800 text-white'
                        : 'text-purple-100 hover:bg-purple-600 hover:text-white'
                    }`}
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    <Icon className="mr-3 h-5 w-5" />
                    {item.name}
                  </Link>
                );
              })}
            </div>
          </div>
        )}
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="bg-white border-t mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex flex-col sm:flex-row justify-between items-center text-sm text-gray-500">
            <p>&copy; {new Date().getFullYear()} TalentFino ERP. All rights reserved.</p>
            <div className="mt-2 flex space-x-4 sm:mt-0">
              <button type="button" className="hover:text-gray-700">
                Help
              </button>
              <button type="button" className="hover:text-gray-700">
                Privacy
              </button>
              <button type="button" className="hover:text-gray-700">
                Terms
              </button>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
