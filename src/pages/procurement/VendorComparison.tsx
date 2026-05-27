import {
  ArrowLeft,
  BarChart3,
  CheckCircle,
  Award,
  TrendingDown,
  TrendingUp,
  Clock,
  Shield,
  Download,
} from 'lucide-react';
import { useState } from 'react';
import { Link, useParams, useNavigate } from 'react-router-dom';

import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Textarea } from '@/components/ui/textarea';
// Mock comparison data
const rfqData = {
  rfqNumber: 'RFQ2025010001',
  title: 'Office Furniture - Q1 2025',
  estimatedValue: 500000,
  lineItems: [
    { id: 1, description: 'Ergonomic Office Chair', quantity: 50, uom: 'PCS' },
    { id: 2, description: 'Standing Desk - Electric', quantity: 25, uom: 'PCS' },
    { id: 3, description: 'Filing Cabinet - 4 Drawer', quantity: 30, uom: 'PCS' },
    { id: 4, description: 'Conference Table - 10 Seater', quantity: 5, uom: 'PCS' },
  ],
};

const quotations = [
  {
    vendorId: 'V005',
    vendorName: 'Furniture Hub',
    totalAmount: 485000,
    deliveryDays: 20,
    warranty: '2 years',
    rating: 4.2,
    pastOrders: 12,
    onTimeDelivery: 92,
    items: [
      { itemId: 1, unitPrice: 4500 },
      { itemId: 2, unitPrice: 6500 },
      { itemId: 3, unitPrice: 2800 },
      { itemId: 4, unitPrice: 2700 },
    ],
  },
  {
    vendorId: 'V007',
    vendorName: 'Office Solutions',
    totalAmount: 520000,
    deliveryDays: 15,
    warranty: '3 years',
    rating: 4.5,
    pastOrders: 8,
    onTimeDelivery: 98,
    items: [
      { itemId: 1, unitPrice: 4800 },
      { itemId: 2, unitPrice: 7000 },
      { itemId: 3, unitPrice: 3000 },
      { itemId: 4, unitPrice: 3000 },
    ],
  },
  {
    vendorId: 'V008',
    vendorName: 'Premium Furnishings',
    totalAmount: 545000,
    deliveryDays: 25,
    warranty: '5 years',
    rating: 4.8,
    pastOrders: 5,
    onTimeDelivery: 100,
    items: [
      { itemId: 1, unitPrice: 5000 },
      { itemId: 2, unitPrice: 7500 },
      { itemId: 3, unitPrice: 3200 },
      { itemId: 4, unitPrice: 2300 },
    ],
  },
];

export default function VendorComparison() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [selectedVendor, setSelectedVendor] = useState<string>('');
  const [remarks, setRemarks] = useState('');

  const lowestPrice = Math.min(...quotations.map((q) => q.totalAmount));
  const fastestDelivery = Math.min(...quotations.map((q) => q.deliveryDays));
  const longestWarranty = Math.max(...quotations.map((q) => parseInt(q.warranty)));

  const getLowestPriceForItem = (itemId: number) => {
    const prices = quotations.map((q) => q.items.find((i) => i.itemId === itemId)?.unitPrice || 0);
    return Math.min(...prices);
  };

  const handleAwardPO = () => {
    if (selectedVendor) {
      navigate(`/admin/procurement/po/new?rfq=${rfqData.rfqNumber}&vendor=${selectedVendor}`);
    }
  };

  return (
    <div className="container mx-auto space-y-6 py-6">
      <PageHeader
        title="Vendor Comparison"
        subtitle={`${rfqData.rfqNumber} - ${rfqData.title}`}
        breadcrumbs={[
          { label: 'RFQ', to: '/admin/procurement/rfq' },
          { label: rfqData.rfqNumber, to: `/admin/procurement/rfq/${id}` },
          { label: 'Compare' },
        ]}
        actions={
          <Button variant="outline">
            <Download className="mr-2 h-4 w-4" />
            Export Comparison
          </Button>
        }
      />

      {/* Summary Comparison */}
      <Card>
        <CardHeader>
          <CardTitle>Quotation Summary</CardTitle>
          <CardDescription>Compare key metrics across all vendors</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[200px]">Criteria</TableHead>
                {quotations.map((q) => (
                  <TableHead key={q.vendorId} className="text-center">
                    <div className="font-semibold">{q.vendorName}</div>
                    <div className="text-xs font-normal text-muted-foreground">{q.vendorId}</div>
                  </TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              <TableRow>
                <TableCell className="font-medium">Total Amount</TableCell>
                {quotations.map((q) => (
                  <TableCell key={q.vendorId} className="text-center">
                    <div className="flex items-center justify-center gap-2">
                      <span
                        className={q.totalAmount === lowestPrice ? 'font-bold text-green-600' : ''}
                      >
                        {formatIndianCompactCurrency(q.totalAmount)}
                      </span>
                      {q.totalAmount === lowestPrice && (
                        <Badge variant="default" className="bg-green-100 text-green-800">
                          <TrendingDown className="mr-1 h-3 w-3" />
                          Lowest
                        </Badge>
                      )}
                    </div>
                  </TableCell>
                ))}
              </TableRow>
              <TableRow>
                <TableCell className="font-medium">Delivery Time</TableCell>
                {quotations.map((q) => (
                  <TableCell key={q.vendorId} className="text-center">
                    <div className="flex items-center justify-center gap-2">
                      <Clock className="h-4 w-4 text-muted-foreground" />
                      <span
                        className={
                          q.deliveryDays === fastestDelivery ? 'font-bold text-green-600' : ''
                        }
                      >
                        {q.deliveryDays} days
                      </span>
                      {q.deliveryDays === fastestDelivery && (
                        <Badge variant="default" className="bg-green-100 text-green-800">
                          Fastest
                        </Badge>
                      )}
                    </div>
                  </TableCell>
                ))}
              </TableRow>
              <TableRow>
                <TableCell className="font-medium">Warranty</TableCell>
                {quotations.map((q) => (
                  <TableCell key={q.vendorId} className="text-center">
                    <div className="flex items-center justify-center gap-2">
                      <Shield className="h-4 w-4 text-muted-foreground" />
                      <span
                        className={
                          parseInt(q.warranty) === longestWarranty ? 'font-bold text-green-600' : ''
                        }
                      >
                        {q.warranty}
                      </span>
                      {parseInt(q.warranty) === longestWarranty && (
                        <Badge variant="default" className="bg-green-100 text-green-800">
                          Best
                        </Badge>
                      )}
                    </div>
                  </TableCell>
                ))}
              </TableRow>
              <TableRow>
                <TableCell className="font-medium">Vendor Rating</TableCell>
                {quotations.map((q) => (
                  <TableCell key={q.vendorId} className="text-center">
                    <span className="font-medium text-yellow-600">★ {q.rating.toFixed(1)}</span>
                  </TableCell>
                ))}
              </TableRow>
              <TableRow>
                <TableCell className="font-medium">Past Orders</TableCell>
                {quotations.map((q) => (
                  <TableCell key={q.vendorId} className="text-center">
                    {q.pastOrders}
                  </TableCell>
                ))}
              </TableRow>
              <TableRow>
                <TableCell className="font-medium">On-Time Delivery %</TableCell>
                {quotations.map((q) => (
                  <TableCell key={q.vendorId} className="text-center">
                    <span className={q.onTimeDelivery >= 95 ? 'font-medium text-green-600' : ''}>
                      {q.onTimeDelivery}%
                    </span>
                  </TableCell>
                ))}
              </TableRow>
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Line Item Comparison */}
      <Card>
        <CardHeader>
          <CardTitle>Item-wise Price Comparison</CardTitle>
          <CardDescription>Compare unit prices for each line item</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Item Description</TableHead>
                <TableHead className="text-center">Qty</TableHead>
                {quotations.map((q) => (
                  <TableHead key={q.vendorId} className="text-right">
                    {q.vendorName}
                  </TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              {rfqData.lineItems.map((item) => {
                const lowestItemPrice = getLowestPriceForItem(item.id);
                return (
                  <TableRow key={item.id}>
                    <TableCell className="font-medium">{item.description}</TableCell>
                    <TableCell className="text-center">
                      {item.quantity} {item.uom}
                    </TableCell>
                    {quotations.map((q) => {
                      const quotedItem = q.items.find((i) => i.itemId === item.id);
                      const isLowest = quotedItem?.unitPrice === lowestItemPrice;
                      return (
                        <TableCell key={q.vendorId} className="text-right">
                          <span className={isLowest ? 'font-bold text-green-600' : ''}>
                            {quotedItem ? formatIndianCompactCurrency(quotedItem.unitPrice) : '-'}
                          </span>
                        </TableCell>
                      );
                    })}
                  </TableRow>
                );
              })}
              <TableRow className="bg-muted/50 font-bold">
                <TableCell>Total</TableCell>
                <TableCell></TableCell>
                {quotations.map((q) => (
                  <TableCell key={q.vendorId} className="text-right">
                    {formatIndianCompactCurrency(q.totalAmount)}
                  </TableCell>
                ))}
              </TableRow>
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Vendor Selection for Award */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Award className="h-5 w-5" />
            Award Purchase Order
          </CardTitle>
          <CardDescription>Select a vendor to award this RFQ</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <RadioGroup value={selectedVendor} onValueChange={setSelectedVendor}>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
              {quotations.map((q) => (
                <div
                  key={q.vendorId}
                  className={`relative cursor-pointer rounded-lg border p-4 transition-colors ${
                    selectedVendor === q.vendorId
                      ? 'border-primary bg-primary/5'
                      : 'hover:bg-muted/50'
                  }`}
                  onClick={() => setSelectedVendor(q.vendorId)}
                >
                  <div className="flex items-start gap-3">
                    <RadioGroupItem value={q.vendorId} id={q.vendorId} />
                    <div className="flex-1">
                      <Label htmlFor={q.vendorId} className="cursor-pointer font-semibold">
                        {q.vendorName}
                      </Label>
                      <div className="mt-2 space-y-1 text-sm">
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Amount:</span>
                          <span className="font-medium">
                            {formatIndianCompactCurrency(q.totalAmount)}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Delivery:</span>
                          <span>{q.deliveryDays} days</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Warranty:</span>
                          <span>{q.warranty}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                  {q.totalAmount === lowestPrice && (
                    <Badge className="absolute right-2 top-2 bg-green-100 text-green-800">L1</Badge>
                  )}
                </div>
              ))}
            </div>
          </RadioGroup>

          <div>
            <Label htmlFor="remarks">Justification / Remarks</Label>
            <Textarea
              id="remarks"
              placeholder="Provide justification for vendor selection..."
              value={remarks}
              onChange={(e) => setRemarks(e.target.value)}
              rows={3}
              className="mt-2"
            />
          </div>

          <div className="flex gap-2">
            <Button onClick={handleAwardPO} disabled={!selectedVendor}>
              <CheckCircle className="mr-2 h-4 w-4" />
              Award & Create PO
            </Button>
            <Button variant="outline" onClick={() => navigate(-1)}>
              Cancel
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
