/**
 * Vendor PO Acknowledge Page
 */

import { CheckCircle, Loader2, Calendar } from 'lucide-react';
import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

import { DateDisplay } from '@/components/common/DateDisplay';
import { PageHeader } from '@/components/common/PageHeader';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { useToast } from '@/hooks/use-toast';
import { vendorPOApi } from '@/services/vendorApi';
import type { PurchaseOrder } from '@/types/vendor';

import { logger } from '@/lib/logger';
export default function VendorPOAcknowledge() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { toast } = useToast();

  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [po, setPO] = useState<PurchaseOrder | null>(null);
  const [committedDate, setCommittedDate] = useState('');
  const [deliveryRemarks, setDeliveryRemarks] = useState('');

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
    setProcessing(true);
    try {
      await vendorPOApi.acknowledge(id!, {
        committed_delivery_date: committedDate || undefined,
        delivery_remarks: deliveryRemarks || undefined,
      });
      toast({ title: 'Purchase order acknowledged successfully' });
      navigate(`/vendor/purchase-orders/${id}`);
    } catch (error) {
      logger.error('Failed to acknowledge PO:', error);
      toast({
        variant: 'destructive',
        title: 'Error',
        description: 'Failed to acknowledge purchase order',
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
        title="Acknowledge Purchase Order"
        subtitle={`PO: ${po.po_number}`}
        breadcrumbs={[
          { label: 'Purchase Orders', to: '/vendor/purchase-orders' },
          { label: po.po_number, to: `/vendor/purchase-orders/${id}` },
          { label: 'Acknowledge' },
        ]}
      />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* PO Summary */}
        <Card>
          <CardHeader>
            <CardTitle>Order Summary</CardTitle>
            <CardDescription>Review the order details before acknowledging</CardDescription>
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

        {/* Acknowledge Form */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <CheckCircle className="mr-2 h-5 w-5 text-green-600" />
              Acknowledgement Details
            </CardTitle>
            <CardDescription>Confirm that you can fulfill this order</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="committedDate">
                  <Calendar className="mr-1 inline h-4 w-4" />
                  Committed Delivery Date
                </Label>
                <Input
                  id="committedDate"
                  type="date"
                  value={committedDate}
                  onChange={(e) => setCommittedDate(e.target.value)}
                  min={new Date().toISOString().split('T')[0]}
                />
                <p className="text-xs text-gray-500">
                  The date by which you commit to deliver the goods
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="remarks">Remarks (Optional)</Label>
                <Textarea
                  id="remarks"
                  placeholder="Any remarks about the delivery, special instructions, etc..."
                  value={deliveryRemarks}
                  onChange={(e) => setDeliveryRemarks(e.target.value)}
                  rows={4}
                />
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
                  disabled={processing}
                  className="bg-green-600 hover:bg-green-700"
                >
                  {processing && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  <CheckCircle className="mr-2 h-4 w-4" />
                  Acknowledge Order
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
