import { Laptop, Monitor, Smartphone, Key, Car, Package } from 'lucide-react';

import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';


const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(value);
};

interface AssignedAsset {
  id: string;
  assetCode: string;
  name: string;
  category: string;
  serialNumber: string;
  assignedDate: string;
  condition: string;
  value: number;
  warranty: string | null;
  icon: string;
}

const assets: AssignedAsset[] = [];

export default function ESSAssetList() {
  const getAssetIcon = (iconName: string) => {
    switch (iconName) {
      case 'Laptop':
        return <Laptop className="h-5 w-5 text-blue-500" />;
      case 'Monitor':
        return <Monitor className="h-5 w-5 text-purple-500" />;
      case 'Smartphone':
        return <Smartphone className="h-5 w-5 text-green-500" />;
      case 'Key':
        return <Key className="h-5 w-5 text-orange-500" />;
      case 'Car':
        return <Car className="h-5 w-5 text-red-500" />;
      default:
        return <Package className="h-5 w-5 text-gray-500" />;
    }
  };

  const getConditionBadge = (condition: string) => {
    switch (condition) {
      case 'GOOD':
        return <Badge variant="default" className="bg-green-500">Good</Badge>;
      case 'FAIR':
        return <Badge variant="secondary" className="bg-yellow-100 text-yellow-800">Fair</Badge>;
      case 'POOR':
        return <Badge variant="destructive">Poor</Badge>;
      default:
        return <Badge variant="outline">{condition}</Badge>;
    }
  };

  const isWarrantyExpiring = (warrantyDate: string | null) => {
    if (!warrantyDate) return false;
    const warranty = new Date(warrantyDate);
    const threeMonthsFromNow = new Date();
    threeMonthsFromNow.setMonth(threeMonthsFromNow.getMonth() + 3);
    return warranty <= threeMonthsFromNow && warranty >= new Date();
  };

  const totalAssetValue = assets.reduce((sum, asset) => sum + asset.value, 0);

  return (
    <div className="space-y-6">
      <PageHeader
        title="My Assets"
        subtitle="Company assets assigned to you"
      />

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-blue-100 rounded-lg">
                <Package className="h-6 w-6 text-blue-600" />
              </div>
              <div>
                <div className="text-2xl font-bold">{assets.length}</div>
                <div className="text-sm text-muted-foreground">Total Assets</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-green-100 rounded-lg">
                <Laptop className="h-6 w-6 text-green-600" />
              </div>
              <div>
                <div className="text-2xl font-bold">
                  {assets.filter((asset) => ['Laptop', 'Monitor', 'Mobile'].includes(asset.category)).length}
                </div>
                <div className="text-sm text-muted-foreground">IT Equipment</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-purple-100 rounded-lg">
                <Car className="h-6 w-6 text-purple-600" />
              </div>
              <div>
                <div className="text-2xl font-bold">
                  {assets.filter((asset) => asset.category === 'Vehicle').length}
                </div>
                <div className="text-sm text-muted-foreground">Vehicle</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-center">
              <div className="text-xl font-bold">{formatCurrency(totalAssetValue)}</div>
              <div className="text-sm text-muted-foreground">Total Value</div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Assets Table */}
      <Card>
        <CardHeader>
          <CardTitle>Assigned Assets</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Asset</TableHead>
                <TableHead>Asset Code</TableHead>
                <TableHead>Serial Number</TableHead>
                <TableHead>Assigned Date</TableHead>
                <TableHead>Condition</TableHead>
                <TableHead className="text-right">Value</TableHead>
                <TableHead>Warranty</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {assets.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} className="py-8 text-center text-sm text-muted-foreground">
                    Asset assignment data is pending backend ESS asset endpoints. Once fixed-asset custody is exposed to ESS, assigned assets will appear here.
                  </TableCell>
                </TableRow>
              ) : assets.map((asset) => (
                <TableRow key={asset.id}>
                  <TableCell>
                    <div className="flex items-center gap-3">
                      {getAssetIcon(asset.icon)}
                      <div>
                        <div className="font-medium">{asset.name}</div>
                        <div className="text-sm text-muted-foreground">{asset.category}</div>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell className="font-mono text-sm">{asset.assetCode}</TableCell>
                  <TableCell className="font-mono text-sm">{asset.serialNumber}</TableCell>
                  <TableCell>{asset.assignedDate}</TableCell>
                  <TableCell>{getConditionBadge(asset.condition)}</TableCell>
                  <TableCell className="text-right">{formatCurrency(asset.value)}</TableCell>
                  <TableCell>
                    {asset.warranty ? (
                      <div className="flex items-center gap-2">
                        <span className={isWarrantyExpiring(asset.warranty) ? 'text-orange-600' : ''}>
                          {asset.warranty}
                        </span>
                        {isWarrantyExpiring(asset.warranty) && (
                          <Badge variant="secondary" className="bg-orange-100 text-orange-800 text-xs">
                            Expiring Soon
                          </Badge>
                        )}
                      </div>
                    ) : (
                      <span className="text-muted-foreground">N/A</span>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Asset Acknowledgment Note */}
      <Card className="bg-muted/50">
        <CardContent className="pt-6">
          <div className="text-sm text-muted-foreground">
            <strong>Note:</strong> You are responsible for the safekeeping and proper use of all assigned assets.
            Any damage or loss must be reported immediately to the IT/Admin department.
            Assets must be returned upon separation or when requested.
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
