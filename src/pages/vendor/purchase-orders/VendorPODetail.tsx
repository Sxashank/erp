/**
 * Vendor Purchase Order Detail
 */

import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  ArrowLeft,
  CheckCircle,
  XCircle,
  Download,
  Loader2,
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
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
      console.error('Failed to fetch PO:', error);
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

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
    }).format(amount);
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
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-purple-600" />
      </div>
    );
  }

  if (!po) {
    return null;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Button variant="ghost" onClick={() => navigate('/vendor/purchase-orders')}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">PO: {po.po_number}</h1>
            <p className="text-gray-600">
              Date: {new Date(po.po_date).toLocaleDateString()}
            </p>
          </div>
        </div>
        <div className="flex items-center space-x-2">
          {getStatusBadge()}
          <Button variant="outline" onClick={() => vendorPOApi.downloadPdf(id!)}>
            <Download className="h-4 w-4 mr-2" />
            Download PDF
          </Button>
        </div>
      </div>

      {/* Action Buttons for Pending POs */}
      {(!acknowledgement || acknowledgement.status === 'PENDING') && (
        <Card className="bg-yellow-50 border-yellow-200">
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
                    className="text-red-600 hover:text-red-700 border-red-300"
                  >
                    <XCircle className="h-4 w-4 mr-2" />
                    Reject
                  </Button>
                </Link>
                <Link to={`/vendor/purchase-orders/${id}/acknowledge`}>
                  <Button className="bg-green-600 hover:bg-green-700">
                    <CheckCircle className="h-4 w-4 mr-2" />
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
        <Card className={
          acknowledgement.status === 'ACKNOWLEDGED' ? 'bg-green-50 border-green-200' :
          acknowledgement.status === 'REJECTED' ? 'bg-red-50 border-red-200' :
          'bg-yellow-50 border-yellow-200'
        }>
          <CardContent className="pt-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <Label className="text-gray-500">Status</Label>
                <p className="font-medium">{acknowledgement.status}</p>
              </div>
              {acknowledgement.acknowledged_at && (
                <div>
                  <Label className="text-gray-500">Acknowledged On</Label>
                  <p className="font-medium">
                    {new Date(acknowledgement.acknowledged_at).toLocaleDateString()}
                  </p>
                </div>
              )}
              {acknowledgement.committed_delivery_date && (
                <div>
                  <Label className="text-gray-500">Committed Delivery</Label>
                  <p className="font-medium">
                    {new Date(acknowledgement.committed_delivery_date).toLocaleDateString()}
                  </p>
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
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
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
                <p className="font-medium">{new Date(po.po_date).toLocaleDateString()}</p>
              </div>
              <div>
                <Label className="text-gray-500">Delivery Date</Label>
                <p className="font-medium">
                  {po.delivery_date ? new Date(po.delivery_date).toLocaleDateString() : '-'}
                </p>
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
              <span>{formatCurrency(po.subtotal)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Discount</span>
              <span>-{formatCurrency(po.discount_amount)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Taxable Amount</span>
              <span>{formatCurrency(po.taxable_amount)}</span>
            </div>
            {po.cgst_amount > 0 && (
              <div className="flex justify-between">
                <span className="text-gray-500">CGST</span>
                <span>{formatCurrency(po.cgst_amount)}</span>
              </div>
            )}
            {po.sgst_amount > 0 && (
              <div className="flex justify-between">
                <span className="text-gray-500">SGST</span>
                <span>{formatCurrency(po.sgst_amount)}</span>
              </div>
            )}
            {po.igst_amount > 0 && (
              <div className="flex justify-between">
                <span className="text-gray-500">IGST</span>
                <span>{formatCurrency(po.igst_amount)}</span>
              </div>
            )}
            <div className="border-t pt-2 mt-2">
              <div className="flex justify-between font-bold text-lg">
                <span>Total</span>
                <span className="text-purple-600">{formatCurrency(po.total_amount)}</span>
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
                      {line.item_code && (
                        <p className="text-sm text-gray-500">{line.item_code}</p>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>{line.hsn_sac_code || '-'}</TableCell>
                  <TableCell className="text-right">
                    {line.quantity} {line.uom}
                  </TableCell>
                  <TableCell className="text-right">{formatCurrency(line.unit_price)}</TableCell>
                  <TableCell className="text-right">
                    {formatCurrency(line.cgst_amount + line.sgst_amount + line.igst_amount)}
                  </TableCell>
                  <TableCell className="text-right font-medium">
                    {formatCurrency(line.net_amount)}
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
