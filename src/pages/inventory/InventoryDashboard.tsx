import {
  Package,
  Warehouse,
  ArrowDownCircle,
  ArrowUpCircle,
  AlertTriangle,
  TrendingUp,
  RefreshCw,
} from 'lucide-react';
import { useState } from 'react';
import { Link } from 'react-router-dom';

import { DateDisplay } from '@/components/common/DateDisplay';
import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
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

// Mock data
const dashboardStats = {
  totalItems: 1250,
  totalWarehouses: 5,
  totalStockValue: 45000000,
  lowStockItems: 23,
  pendingTransfers: 8,
  todayTransactions: 45,
};

const lowStockItems = [
  {
    id: '1',
    code: 'ITM-001',
    name: 'A4 Paper Ream',
    currentStock: 50,
    minStock: 100,
    unit: 'Reams',
  },
  {
    id: '2',
    code: 'ITM-045',
    name: 'Printer Cartridge',
    currentStock: 5,
    minStock: 20,
    unit: 'Pcs',
  },
  { id: '3', code: 'ITM-089', name: 'Stapler Pins', currentStock: 10, minStock: 50, unit: 'Boxes' },
  {
    id: '4',
    code: 'ITM-112',
    name: 'Envelope Large',
    currentStock: 200,
    minStock: 500,
    unit: 'Pcs',
  },
  { id: '5', code: 'ITM-156', name: 'Marker Pens', currentStock: 15, minStock: 40, unit: 'Pcs' },
];

const recentTransactions = [
  {
    id: '1',
    number: 'STK2501150001',
    type: 'STOCK_IN',
    item: 'A4 Paper Ream',
    qty: 500,
    warehouse: 'Main Warehouse',
    date: '2025-01-15',
  },
  {
    id: '2',
    number: 'STK2501150002',
    type: 'STOCK_OUT',
    item: 'Printer Cartridge',
    qty: 10,
    warehouse: 'Branch A',
    date: '2025-01-15',
  },
  {
    id: '3',
    number: 'STK2501150003',
    type: 'TRANSFER',
    item: 'Staplers',
    qty: 20,
    warehouse: 'Main to Branch B',
    date: '2025-01-15',
  },
  {
    id: '4',
    number: 'STK2501140004',
    type: 'ADJUSTMENT',
    item: 'Pens Blue',
    qty: -5,
    warehouse: 'Main Warehouse',
    date: '2025-01-14',
  },
  {
    id: '5',
    number: 'STK2501140005',
    type: 'STOCK_IN',
    item: 'Files Folders',
    qty: 100,
    warehouse: 'Main Warehouse',
    date: '2025-01-14',
  },
];

const warehouseSummary = [
  { id: '1', name: 'Main Warehouse', items: 850, value: 32000000, utilization: 78 },
  { id: '2', name: 'Branch A Store', items: 200, value: 6500000, utilization: 45 },
  { id: '3', name: 'Branch B Store', items: 150, value: 4500000, utilization: 38 },
  { id: '4', name: 'Transit Warehouse', items: 50, value: 2000000, utilization: 15 },
];

export default function InventoryDashboard() {
  return (
    <div className="container mx-auto space-y-6 py-6">
      <PageHeader
        title="Inventory Dashboard"
        subtitle="Overview of inventory status and operations"
        actions={
          <div className="flex gap-2">
            <Button variant="outline" asChild>
              <Link to="/admin/inventory/stock-in">
                <ArrowDownCircle className="mr-2 h-4 w-4" />
                Stock In
              </Link>
            </Button>
            <Button variant="outline" asChild>
              <Link to="/admin/inventory/stock-out">
                <ArrowUpCircle className="mr-2 h-4 w-4" />
                Stock Out
              </Link>
            </Button>
            <Button asChild>
              <Link to="/admin/inventory/items">
                <Package className="mr-2 h-4 w-4" />
                Manage Items
              </Link>
            </Button>
          </div>
        }
      />

      {/* Stats Cards */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-6">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-blue-100 p-2">
                <Package className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Total Items</p>
                <p className="text-xl font-bold">{dashboardStats.totalItems.toLocaleString()}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-green-100 p-2">
                <Warehouse className="h-5 w-5 text-green-600" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Warehouses</p>
                <p className="text-xl font-bold">{dashboardStats.totalWarehouses}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-purple-100 p-2">
                <TrendingUp className="h-5 w-5 text-purple-600" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Stock Value</p>
                <p className="text-xl font-bold">
                  {formatCurrency(dashboardStats.totalStockValue)}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-red-100 p-2">
                <AlertTriangle className="h-5 w-5 text-red-600" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Low Stock</p>
                <p className="text-xl font-bold">{dashboardStats.lowStockItems}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-orange-100 p-2">
                <RefreshCw className="h-5 w-5 text-orange-600" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Pending Transfers</p>
                <p className="text-xl font-bold">{dashboardStats.pendingTransfers}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-cyan-100 p-2">
                <ArrowDownCircle className="h-5 w-5 text-cyan-600" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Today's Txns</p>
                <p className="text-xl font-bold">{dashboardStats.todayTransactions}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Low Stock Alert */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-red-500" />
              Low Stock Alert
            </CardTitle>
            <Button variant="link" size="sm" asChild>
              <Link to="/admin/inventory/reports">View All</Link>
            </Button>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Item Code</TableHead>
                  <TableHead>Item Name</TableHead>
                  <TableHead className="text-right">Current</TableHead>
                  <TableHead className="text-right">Min Level</TableHead>
                  <TableHead className="text-right">Shortfall</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {lowStockItems.map((item) => (
                  <TableRow key={item.id}>
                    <TableCell className="font-medium">{item.code}</TableCell>
                    <TableCell>{item.name}</TableCell>
                    <TableCell className="text-right font-medium text-red-600">
                      {item.currentStock} {item.unit}
                    </TableCell>
                    <TableCell className="text-right">
                      {item.minStock} {item.unit}
                    </TableCell>
                    <TableCell className="text-right">
                      <Badge variant="destructive">{item.minStock - item.currentStock}</Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        {/* Warehouse Summary */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Warehouse className="h-5 w-5" />
              Warehouse Summary
            </CardTitle>
            <Button variant="link" size="sm" asChild>
              <Link to="/admin/inventory/warehouses">Manage</Link>
            </Button>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Warehouse</TableHead>
                  <TableHead className="text-right">Items</TableHead>
                  <TableHead className="text-right">Value</TableHead>
                  <TableHead className="text-right">Utilization</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {warehouseSummary.map((wh) => (
                  <TableRow key={wh.id}>
                    <TableCell className="font-medium">{wh.name}</TableCell>
                    <TableCell className="text-right">{wh.items}</TableCell>
                    <TableCell className="text-right">{formatCurrency(wh.value)}</TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-2">
                        <div className="h-2 w-16 overflow-hidden rounded-full bg-gray-200">
                          <div
                            className={`h-full rounded-full ${
                              wh.utilization > 80
                                ? 'bg-red-500'
                                : wh.utilization > 60
                                  ? 'bg-yellow-500'
                                  : 'bg-green-500'
                            }`}
                            style={{ width: `${wh.utilization}%` }}
                          />
                        </div>
                        <span className="text-sm">{wh.utilization}%</span>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>

      {/* Recent Transactions */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Recent Transactions</CardTitle>
          <Button variant="link" size="sm" asChild>
            <Link to="/admin/inventory/reports">View All</Link>
          </Button>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Transaction #</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Item</TableHead>
                <TableHead className="text-right">Quantity</TableHead>
                <TableHead>Warehouse</TableHead>
                <TableHead>Date</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {recentTransactions.map((txn) => (
                <TableRow key={txn.id}>
                  <TableCell className="font-medium">{txn.number}</TableCell>
                  <TableCell>
                    <Badge
                      variant={
                        txn.type === 'STOCK_IN'
                          ? 'default'
                          : txn.type === 'STOCK_OUT'
                            ? 'secondary'
                            : txn.type === 'TRANSFER'
                              ? 'outline'
                              : 'destructive'
                      }
                    >
                      {txn.type.replace('_', ' ')}
                    </Badge>
                  </TableCell>
                  <TableCell>{txn.item}</TableCell>
                  <TableCell
                    className={`text-right font-medium ${
                      txn.qty < 0 ? 'text-red-600' : 'text-green-600'
                    }`}
                  >
                    {txn.qty > 0 ? '+' : ''}
                    {txn.qty}
                  </TableCell>
                  <TableCell>{txn.warehouse}</TableCell>
                  <TableCell><DateDisplay date={txn.date} /></TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
