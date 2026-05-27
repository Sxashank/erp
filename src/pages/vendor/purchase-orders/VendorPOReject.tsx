/**
 * Vendor PO Reject Page
 */

import { XCircle, Loader2, AlertTriangle } from 'lucide-react';
import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

import { DateDisplay } from '@/components/common/DateDisplay';
import { PageHeader } from '@/components/common/PageHeader';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { useToast } from '@/hooks/use-toast';
import { vendorPOApi } from '@/services/vendorApi';
import type { PurchaseOrder } from '@/types/vendor';

import { logger } from '@/lib/logger';
export default function VendorPOReject() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { toast } = useToast();

  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [po, setPO] = useState<PurchaseOrder | null>(null);
  const [rejectReason, setRejectReason] = useState('');

  useEffect(() => {
    if (id) fetchPODetails();
  }, [id]);

  const fetchPODetails = async () => {
    try {
      const response = await vendorPOApi.get(id!);
      setPO(response.data.purchase_order);
    } catch (error) {
      logger.error('Failed to fetch PO:', error);
      toast({
        variant: 'destructive',
        title: 'Error',
        description: 'Failed to load purchase order',
      });
      navigate('/vendor/purchase-orders');
    } finally {
      setLoading(false);
    }
  };
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!rejectReason.trim()) {
      toast({ variant: 'destructive', title: 'Please provide a reason for rejection' });
      return;
    }

    setProcessing(true);
    try {
      await vendorPOApi.reject(id!, rejectReason);
      toast({ title: 'Purchase order rejected' });
      navigate(`/vendor/purchase-orders/${id}`);
    } catch (error) {
      logger.error('Failed to reject PO:', error);
      toast({
        variant: 'destructive',
        title: 'Error',
        description: 'Failed to reject purchase order',
      });
    } finally {
      setProcessing(false);
    }
  };

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-purple-600" />
      </div>
    );
  }

  if (!po) {
    return null;
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Reject Purchase Order"
        subtitle={`PO: ${po.po_number}`}
        breadcrumbs={[
          { label: 'Purchase Orders', to: '/vendor/purchase-orders' },
          { label: po.po_number, to: `/vendor/purchase-orders/${id}` },
          { label: 'Reject' },
        ]}
      />

      {/* Warning Banner */}
      <Card className="border-red-200 bg-red-50">
        <CardContent className="pt-6">
          <div className="flex items-start space-x-4">
            <AlertTriangle className="mt-0.5 h-6 w-6 text-red-600" />
            <div>
              <h3 className="font-semibold text-red-800">Important Notice</h3>
              <p className="mt-1 text-sm text-red-700">
                Rejecting this purchase order will notify the buyer. This action cannot be undone.
                Please provide a clear reason for the rejection.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* PO Summary */}
        <Card>
          <CardHeader>
            <CardTitle>Order Summary</CardTitle>
            <CardDescription>Review the order details</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-gray-500">PO Number</Label>
                <p className="font-medium">{po.po_number}</p>
              </div>
              <div>
                <Label className="text-gray-500">Order Date</Label>
                <DateDisplay date={po.po_date} className="font-medium" />
              </div>
              <div>
                <Label className="text-gray-500">Expected Delivery</Label>
                <DateDisplay date={po.delivery_date} className="font-medium" />
              </div>
              <div>
                <Label className="text-gray-500">Total Amount</Label>
                <p className="font-medium text-purple-600">
                  {formatIndianCompactCurrency(po.total_amount)}
                </p>
              </div>
            </div>
            <div>
              <Label className="text-gray-500">Items</Label>
              <p className="font-medium">{po.lines?.length || 0} line items</p>
            </div>
          </CardContent>
        </Card>

        {/* Reject Form */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center text-red-700">
              <XCircle className="mr-2 h-5 w-5" />
              Rejection Details
            </CardTitle>
            <CardDescription>Please provide a reason for rejecting this order</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="reason">Reason for Rejection *</Label>
                <Textarea
                  id="reason"
                  placeholder="Please explain why you are rejecting this purchase order..."
                  value={rejectReason}
                  onChange={(e) => setRejectReason(e.target.value)}
                  rows={6}
                  required
                  className="resize-none"
                />
                <p className="text-xs text-gray-500">This reason will be shared with the buyer</p>
              </div>

              <div className="flex justify-end space-x-4 pt-4">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => navigate(`/vendor/purchase-orders/${id}`)}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={processing || !rejectReason.trim()}
                  variant="destructive"
                >
                  {processing && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  <XCircle className="mr-2 h-4 w-4" />
                  Reject Order
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
