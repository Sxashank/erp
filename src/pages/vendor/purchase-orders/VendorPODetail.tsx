/**
 * Vendor Purchase Order Detail
 */

import { CheckCircle, XCircle, Download, Loader2 } from 'lucide-react';
import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';

import { DateDisplay } from '@/components/common/DateDisplay';
import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { useToast } from '@/hooks/use-toast';
import { vendorPOApi } from '@/services/vendorApi';
import type { PurchaseOrder, POAcknowledgement } from '@/types/vendor';

import { logger } from '@/lib/logger';
export default function VendorPODetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { toast } = useToast();

  const [loading, setLoading] = useState(true);
  const [po, setPO] = useState<PurchaseOrder | null>(null);
  const [acknowledgement, setAcknowledgement] = useState<POAcknowledgement | null>(null);

  useEffect(() => {
    if (id) fetchPODetails();
  }, [id]);

  const fetchPODetails = async () => {
    try {
      const response = await vendorPOApi.get(id!);
      setPO(response.data.purchase_order);
      setAcknowledgement(response.data.acknowledgement || null);
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
  const getStatusBadge = () => {
    if (!acknowledgement) {
      return <Badge className="bg-orange-100 text-orange-800">Pending Acknowledgement</Badge>;
    }
    if (acknowledgement.status === 'ACKNOWLEDGED') {
      return <Badge className="bg-green-100 text-green-800">Acknowledged</Badge>;
    }
    if (acknowledgement.status === 'REJECTED') {
      return <Badge className="bg-red-100 text-red-800">Rejected</Badge>;
    }
    if (acknowledgement.status === 'CHANGE_REQUESTED') {
      return <Badge className="bg-yellow-100 text-yellow-800">Change Requested</Badge>;
    }
    return <Badge className="bg-orange-100 text-orange-800">Pending</Badge>;
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
        title={`PO: ${po.po_number}`}
        subtitle={`Date: ${new Date(po.po_date).toLocaleDateString()}`}
        breadcrumbs={[
          { label: 'Purchase Orders', to: '/vendor/purchase-orders' },
          { label: po.po_number },
        ]}
        actions={
          <div className="flex items-center gap-2">
            {getStatusBadge()}
            <Button variant="outline" onClick={() => vendorPOApi.downloadPdf(id!)}>
              <Download className="mr-2 h-4 w-4" />
              Download PDF
            </Button>
          </div>
        }
      />

      {/* Action Buttons for Pending POs */}
      {(!acknowledgement || acknowledgement.status === 'PENDING') && (
        <Card className="border-yellow-200 bg-yellow-50">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-semibold text-yellow-800">Action Required</h3>
                <p className="text-sm text-yellow-700">
                  Please acknowledge or reject this purchase order
                </p>
              </div>
              <div className="flex space-x-2">
                <Link to={`/vendor/purchase-orders/${id}/reject`}>
                  <Button
                    variant="outline"
                    className="border-red-300 text-red-600 hover:text-red-700"
                  >
                    <XCircle className="mr-2 h-4 w-4" />
                    Reject
                  </Button>
                </Link>
                <Link to={`/vendor/purchase-orders/${id}/acknowledge`}>
                  <Button className="bg-green-600 hover:bg-green-700">
                    <CheckCircle className="mr-2 h-4 w-4" />
                    Acknowledge
                  </Button>
                </Link>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Acknowledgement Info */}
      {acknowledgement && acknowledgement.status !== 'PENDING' && (
        <Card
          className={
            acknowledgement.status === 'ACKNOWLEDGED'
              ? 'border-green-200 bg-green-50'
              : acknowledgement.status === 'REJECTED'
                ? 'border-red-200 bg-red-50'
                : 'border-yellow-200 bg-yellow-50'
          }
        >
          <CardContent className="pt-6">
            <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
              <div>
                <Label className="text-gray-500">Status</Label>
                <p className="font-medium">{acknowledgement.status}</p>
              </div>
              {acknowledgement.acknowledged_at && (
                <div>
                  <Label className="text-gray-500">Acknowledged On</Label>
                  <DateDisplay date={acknowledgement.acknowledged_at} className="font-medium" />
                </div>
              )}
              {acknowledgement.committed_delivery_date && (
                <div>
                  <Label className="text-gray-500">Committed Delivery</Label>
                  <DateDisplay
                    date={acknowledgement.committed_delivery_date}
                    className="font-medium"
                  />
                </div>
              )}
              {acknowledgement.delivery_remarks && (
                <div>
                  <Label className="text-gray-500">Remarks</Label>
                  <p className="font-medium">{acknowledgement.delivery_remarks}</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* PO Details */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Order Details</CardTitle>
          </CardHeader>
          <CardContent>
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
                <Label className="text-gray-500">Delivery Date</Label>
                <DateDisplay date={po.delivery_date} className="font-medium" />
              </div>
              <div>
                <Label className="text-gray-500">Payment Terms</Label>
                <p className="font-medium">{po.payment_terms || '-'}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Amount Summary</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="flex justify-between">
              <span className="text-gray-500">Subtotal</span>
              <span>{formatIndianCompactCurrency(po.subtotal)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Discount</span>
              <span>-{formatIndianCompactCurrency(po.discount_amount)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Taxable Amount</span>
              <span>{formatIndianCompactCurrency(po.taxable_amount)}</span>
            </div>
            {po.cgst_amount > 0 && (
              <div className="flex justify-between">
                <span className="text-gray-500">CGST</span>
                <span>{formatIndianCompactCurrency(po.cgst_amount)}</span>
              </div>
            )}
            {po.sgst_amount > 0 && (
              <div className="flex justify-between">
                <span className="text-gray-500">SGST</span>
                <span>{formatIndianCompactCurrency(po.sgst_amount)}</span>
              </div>
            )}
            {po.igst_amount > 0 && (
              <div className="flex justify-between">
                <span className="text-gray-500">IGST</span>
                <span>{formatIndianCompactCurrency(po.igst_amount)}</span>
              </div>
            )}
            <div className="mt-2 border-t pt-2">
              <div className="flex justify-between text-lg font-bold">
                <span>Total</span>
                <span className="text-purple-600">
                  {formatIndianCompactCurrency(po.total_amount)}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Line Items */}
      <Card>
        <CardHeader>
          <CardTitle>Line Items</CardTitle>
          <CardDescription>{po.lines?.length || 0} items in this order</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>#</TableHead>
                <TableHead>Item</TableHead>
                <TableHead>HSN/SAC</TableHead>
                <TableHead className="text-right">Qty</TableHead>
                <TableHead className="text-right">Rate</TableHead>
                <TableHead className="text-right">Tax</TableHead>
                <TableHead className="text-right">Amount</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {po.lines?.map((line) => (
                <TableRow key={line.id}>
                  <TableCell>{line.line_number}</TableCell>
                  <TableCell>
                    <div>
                      <p className="font-medium">{line.item_description}</p>
                      {line.item_code && <p className="text-sm text-gray-500">{line.item_code}</p>}
                    </div>
                  </TableCell>
                  <TableCell>{line.hsn_sac_code || '-'}</TableCell>
                  <TableCell className="text-right">
                    {line.quantity} {line.uom}
                  </TableCell>
                  <TableCell className="text-right">
                    {formatIndianCompactCurrency(line.unit_price)}
                  </TableCell>
                  <TableCell className="text-right">
                    {formatIndianCompactCurrency(
                      line.cgst_amount + line.sgst_amount + line.igst_amount,
                    )}
                  </TableCell>
                  <TableCell className="text-right font-medium">
                    {formatIndianCompactCurrency(line.net_amount)}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
