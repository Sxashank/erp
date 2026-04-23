/**
 * Vendor Portal Dashboard
 */

import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  ShoppingCart,
  FileText,
  Truck,
  CreditCard,
  Shield,
  AlertCircle,
  Bell,
  ArrowRight,
  Loader2,
  TrendingUp,
  Clock,
  CheckCircle,
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { PageHeader } from '@/components/common/PageHeader';
import { ScrollArea } from '@/components/ui/scroll-area';
import { vendorDashboardApi } from '@/services/vendorApi';
import type { VendorDashboardSummary, PendingAction, VendorNotification } from '@/types/vendor';

export default function VendorDashboard() {
  const [loading, setLoading] = useState(true);
  const [summary, setSummary] = useState<VendorDashboardSummary | null>(null);
  const [pendingActions, setPendingActions] = useState<PendingAction[]>([]);
  const [notifications, setNotifications] = useState<VendorNotification[]>([]);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const [summaryRes, actionsRes, notificationsRes] = await Promise.all([
        vendorDashboardApi.getSummary(),
        vendorDashboardApi.getPendingActions(),
        vendorDashboardApi.getNotifications(),
      ]);

      setSummary(summaryRes.data);
      setPendingActions(actionsRes.data.actions || []);
      setNotifications(notificationsRes.data.items || []);
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount: number | undefined) => {
    if (amount === undefined || amount === null) return '-';
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const getPriorityBadge = (priority: string) => {
    const colors: Record<string, string> = {
      critical: 'bg-red-100 text-red-800',
      high: 'bg-orange-100 text-orange-800',
      medium: 'bg-yellow-100 text-yellow-800',
      low: 'bg-green-100 text-green-800',
    };
    return colors[priority] || colors.medium;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-purple-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Welcome to Vendor Portal"
        subtitle="Manage your purchase orders, invoices, and payments in one place"
      />

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* PO Stats */}
        <Card className="hover:shadow-lg transition-shadow">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Pending POs</CardTitle>
            <ShoppingCart className="h-5 w-5 text-purple-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {summary?.purchase_orders?.pending_acknowledgement || 0}
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Awaiting acknowledgement
            </p>
            <Link to="/vendor/purchase-orders?status=pending">
              <Button variant="link" className="px-0 text-purple-600 mt-2">
                View all <ArrowRight className="ml-1 h-4 w-4" />
              </Button>
            </Link>
          </CardContent>
        </Card>

        {/* Invoice Stats */}
        <Card className="hover:shadow-lg transition-shadow">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Draft Invoices</CardTitle>
            <FileText className="h-5 w-5 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {summary?.invoices?.draft || 0}
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Ready to submit
            </p>
            <Link to="/vendor/invoices?status=draft">
              <Button variant="link" className="px-0 text-purple-600 mt-2">
                View all <ArrowRight className="ml-1 h-4 w-4" />
              </Button>
            </Link>
          </CardContent>
        </Card>

        {/* Outstanding Amount */}
        <Card className="hover:shadow-lg transition-shadow">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Outstanding</CardTitle>
            <CreditCard className="h-5 w-5 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {formatCurrency(summary?.payments?.total_outstanding)}
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Total receivable
            </p>
            <Link to="/vendor/payments">
              <Button variant="link" className="px-0 text-purple-600 mt-2">
                View details <ArrowRight className="ml-1 h-4 w-4" />
              </Button>
            </Link>
          </CardContent>
        </Card>

        {/* Compliance */}
        <Card className="hover:shadow-lg transition-shadow">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">Compliance</CardTitle>
            <Shield className="h-5 w-5 text-orange-600" />
          </CardHeader>
          <CardContent>
            <div className="flex items-center space-x-2">
              <div className="text-2xl font-bold">
                {summary?.compliance?.verified || 0}
              </div>
              <span className="text-sm text-gray-500">
                / {summary?.compliance?.total_documents || 0}
              </span>
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Documents verified
            </p>
            <Link to="/vendor/compliance">
              <Button variant="link" className="px-0 text-purple-600 mt-2">
                Manage <ArrowRight className="ml-1 h-4 w-4" />
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>

      {/* Pending Actions & Notifications */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Pending Actions */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center">
                  <AlertCircle className="h-5 w-5 mr-2 text-orange-500" />
                  Pending Actions
                </CardTitle>
                <CardDescription>Items requiring your attention</CardDescription>
              </div>
              <Badge variant="secondary">{pendingActions.length}</Badge>
            </div>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[300px]">
              {pendingActions.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-gray-500">
                  <CheckCircle className="h-12 w-12 text-green-500 mb-2" />
                  <p>All caught up!</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {pendingActions.map((action, index) => (
                    <div
                      key={index}
                      className="flex items-start space-x-3 p-3 rounded-lg bg-gray-50 hover:bg-gray-100 transition-colors"
                    >
                      <div className="flex-1">
                        <div className="flex items-center space-x-2">
                          <p className="font-medium text-sm">{action.title}</p>
                          <Badge className={`text-xs ${getPriorityBadge(action.priority)}`}>
                            {action.priority}
                          </Badge>
                        </div>
                        <p className="text-sm text-gray-500 mt-1">{action.description}</p>
                      </div>
                      <Link
                        to={`/vendor/${action.type === 'po_acknowledgement' ? 'purchase-orders' : action.type}/${action.reference_id}`}
                      >
                        <Button variant="ghost" size="sm">
                          <ArrowRight className="h-4 w-4" />
                        </Button>
                      </Link>
                    </div>
                  ))}
                </div>
              )}
            </ScrollArea>
          </CardContent>
        </Card>

        {/* Recent Notifications */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center">
                  <Bell className="h-5 w-5 mr-2 text-blue-500" />
                  Notifications
                </CardTitle>
                <CardDescription>Recent updates and alerts</CardDescription>
              </div>
              <Link to="/vendor/notifications">
                <Button variant="ghost" size="sm">
                  View all
                </Button>
              </Link>
            </div>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[300px]">
              {notifications.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-gray-500">
                  <Bell className="h-12 w-12 text-gray-300 mb-2" />
                  <p>No notifications</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {notifications.map((notification) => (
                    <div
                      key={notification.id}
                      className={`p-3 rounded-lg border-l-4 ${
                        notification.is_read
                          ? 'bg-white border-gray-200'
                          : 'bg-purple-50 border-purple-500'
                      }`}
                    >
                      <div className="flex items-start justify-between">
                        <div>
                          <p className="font-medium text-sm">{notification.title}</p>
                          <p className="text-sm text-gray-500 mt-1">{notification.message}</p>
                        </div>
                        <Badge variant="outline" className="text-xs">
                          {notification.category}
                        </Badge>
                      </div>
                      <p className="text-xs text-gray-400 mt-2">
                        {new Date(notification.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </ScrollArea>
          </CardContent>
        </Card>
      </div>

      {/* Quick Access */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
          <CardDescription>Common tasks and shortcuts</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Link to="/vendor/invoices/new">
              <Button variant="outline" className="w-full h-20 flex flex-col items-center justify-center space-y-2">
                <FileText className="h-6 w-6 text-purple-600" />
                <span className="text-sm">Create Invoice</span>
              </Button>
            </Link>
            <Link to="/vendor/asn/new">
              <Button variant="outline" className="w-full h-20 flex flex-col items-center justify-center space-y-2">
                <Truck className="h-6 w-6 text-purple-600" />
                <span className="text-sm">Create ASN</span>
              </Button>
            </Link>
            <Link to="/vendor/payments/statement">
              <Button variant="outline" className="w-full h-20 flex flex-col items-center justify-center space-y-2">
                <TrendingUp className="h-6 w-6 text-purple-600" />
                <span className="text-sm">Account Statement</span>
              </Button>
            </Link>
            <Link to="/vendor/compliance">
              <Button variant="outline" className="w-full h-20 flex flex-col items-center justify-center space-y-2">
                <Shield className="h-6 w-6 text-purple-600" />
                <span className="text-sm">Upload Documents</span>
              </Button>
            </Link>
          </div>
        </CardContent>
      </Card>

      {/* Recent Activity */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center">
                <Clock className="h-5 w-5 mr-2 text-gray-500" />
                Recent Activity
              </CardTitle>
              <CardDescription>Your latest actions and updates</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* Summary Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
              <div className="p-4 bg-blue-50 rounded-lg">
                <p className="text-2xl font-bold text-blue-600">
                  {summary?.purchase_orders?.acknowledged || 0}
                </p>
                <p className="text-xs text-gray-600">POs Acknowledged</p>
              </div>
              <div className="p-4 bg-green-50 rounded-lg">
                <p className="text-2xl font-bold text-green-600">
                  {summary?.invoices?.approved || 0}
                </p>
                <p className="text-xs text-gray-600">Invoices Approved</p>
              </div>
              <div className="p-4 bg-purple-50 rounded-lg">
                <p className="text-2xl font-bold text-purple-600">
                  {summary?.asn?.delivered || 0}
                </p>
                <p className="text-xs text-gray-600">Shipments Delivered</p>
              </div>
              <div className="p-4 bg-orange-50 rounded-lg">
                <p className="text-2xl font-bold text-orange-600">
                  {summary?.payments?.pending_payments || 0}
                </p>
                <p className="text-xs text-gray-600">Pending Payments</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
