import {
  BarChart3,
  Download,
  FileText,
  Filter,
  Package,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Calendar,
  Warehouse,
} from 'lucide-react';
import { useState } from 'react';

import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

const ALL_OPTION_VALUE = '__all__';
// Mock data - Stock Summary Report
const stockSummary = [
  {
    id: '1',
    code: 'ITM-001',
    name: 'A4 Paper (500 sheets)',
    category: 'Office Supplies',
    warehouse: 'Main Warehouse',
    quantity: 150,
    unitCost: 250,
    totalValue: 37500,
    reorderLevel: 50,
    status: 'OK',
  },
  {
    id: '2',
    code: 'ITM-002',
    name: 'Ball Pen Blue',
    category: 'Stationery',
    warehouse: 'Main Warehouse',
    quantity: 500,
    unitCost: 10,
    totalValue: 5000,
    reorderLevel: 100,
    status: 'OK',
  },
  {
    id: '3',
    code: 'ITM-003',
    name: 'HP LaserJet Toner',
    category: 'IT Equipment',
    warehouse: 'Main Warehouse',
    quantity: 5,
    unitCost: 3500,
    totalValue: 17500,
    reorderLevel: 10,
    status: 'LOW',
  },
  {
    id: '4',
    code: 'ITM-004',
    name: 'Dell Laptop',
    category: 'IT Equipment',
    warehouse: 'Main Warehouse',
    quantity: 0,
    unitCost: 55000,
    totalValue: 0,
    reorderLevel: 5,
    status: 'OUT',
  },
  {
    id: '5',
    code: 'ITM-005',
    name: 'Office Chair',
    category: 'Furniture',
    warehouse: 'Branch A Store',
    quantity: 30,
    unitCost: 8000,
    totalValue: 240000,
    reorderLevel: 10,
    status: 'OK',
  },
  {
    id: '6',
    code: 'ITM-006',
    name: 'Stapler',
    category: 'Office Supplies',
    warehouse: 'Main Warehouse',
    quantity: 8,
    unitCost: 150,
    totalValue: 1200,
    reorderLevel: 15,
    status: 'LOW',
  },
];

// Mock data - Transaction History
const transactionHistory = [
  {
    id: '1',
    date: '2025-01-15',
    type: 'IN',
    refType: 'PURCHASE',
    refNo: 'PO-2025-001',
    item: 'A4 Paper (500 sheets)',
    warehouse: 'Main Warehouse',
    qty: 100,
    unitCost: 250,
    totalValue: 25000,
  },
  {
    id: '2',
    date: '2025-01-14',
    type: 'OUT',
    refType: 'CONSUMPTION',
    refNo: 'ISS-2025-023',
    item: 'Ball Pen Blue',
    warehouse: 'Main Warehouse',
    qty: 50,
    unitCost: 10,
    totalValue: 500,
  },
  {
    id: '3',
    date: '2025-01-14',
    type: 'IN',
    refType: 'PURCHASE',
    refNo: 'PO-2025-002',
    item: 'HP LaserJet Toner',
    warehouse: 'Main Warehouse',
    qty: 10,
    unitCost: 3500,
    totalValue: 35000,
  },
  {
    id: '4',
    date: '2025-01-13',
    type: 'OUT',
    refType: 'TRANSFER',
    refNo: 'TRF-2025-005',
    item: 'Office Chair',
    warehouse: 'Main Warehouse',
    qty: 5,
    unitCost: 8000,
    totalValue: 40000,
  },
  {
    id: '5',
    date: '2025-01-13',
    type: 'IN',
    refType: 'TRANSFER',
    refNo: 'TRF-2025-005',
    item: 'Office Chair',
    warehouse: 'Branch A Store',
    qty: 5,
    unitCost: 8000,
    totalValue: 40000,
  },
  {
    id: '6',
    date: '2025-01-12',
    type: 'OUT',
    refType: 'DAMAGE',
    refNo: 'ADJ-2025-001',
    item: 'Dell Laptop',
    warehouse: 'Main Warehouse',
    qty: 1,
    unitCost: 55000,
    totalValue: 55000,
  },
];

// Mock data - Low Stock Items
const lowStockItems = [
  {
    id: '3',
    code: 'ITM-003',
    name: 'HP LaserJet Toner',
    category: 'IT Equipment',
    currentQty: 5,
    reorderLevel: 10,
    maxLevel: 50,
    suggestedOrder: 45,
  },
  {
    id: '4',
    code: 'ITM-004',
    name: 'Dell Laptop',
    category: 'IT Equipment',
    currentQty: 0,
    reorderLevel: 5,
    maxLevel: 20,
    suggestedOrder: 20,
  },
  {
    id: '6',
    code: 'ITM-006',
    name: 'Stapler',
    category: 'Office Supplies',
    currentQty: 8,
    reorderLevel: 15,
    maxLevel: 50,
    suggestedOrder: 42,
  },
];

// Mock data - Warehouse wise summary
const warehouseSummary = [
  {
    id: '1',
    code: 'WH-001',
    name: 'Main Warehouse',
    totalItems: 450,
    totalValue: 32000000,
    lowStockItems: 3,
    outOfStockItems: 1,
  },
  {
    id: '2',
    code: 'WH-002',
    name: 'Branch A Store',
    totalItems: 120,
    totalValue: 6500000,
    lowStockItems: 1,
    outOfStockItems: 0,
  },
  {
    id: '3',
    code: 'WH-003',
    name: 'Branch B Store',
    totalItems: 85,
    totalValue: 4500000,
    lowStockItems: 0,
    outOfStockItems: 0,
  },
];

const warehouses = [
  { id: ALL_OPTION_VALUE, name: 'All Warehouses' },
  { id: '1', name: 'Main Warehouse' },
  { id: '2', name: 'Branch A Store' },
  { id: '3', name: 'Branch B Store' },
];

const categories = [
  { id: ALL_OPTION_VALUE, name: 'All Categories' },
  { id: '1', name: 'Office Supplies' },
  { id: '2', name: 'IT Equipment' },
  { id: '3', name: 'Stationery' },
  { id: '4', name: 'Furniture' },
];

export default function StockReport() {
  const [selectedWarehouse, setSelectedWarehouse] = useState(ALL_OPTION_VALUE);
  const [selectedCategory, setSelectedCategory] = useState(ALL_OPTION_VALUE);
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'OK':
        return <Badge variant="default">In Stock</Badge>;
      case 'LOW':
        return (
          <Badge variant="secondary" className="bg-yellow-100 text-yellow-800">
            Low Stock
          </Badge>
        );
      case 'OUT':
        return <Badge variant="destructive">Out of Stock</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const getTypeBadge = (type: string) => {
    return type === 'IN' ? (
      <Badge variant="default" className="bg-green-500">
        <TrendingUp className="mr-1 h-3 w-3" />
        IN
      </Badge>
    ) : (
      <Badge variant="destructive">
        <TrendingDown className="mr-1 h-3 w-3" />
        OUT
      </Badge>
    );
  };

  return (
    <div className="container mx-auto space-y-6 py-6">
      <PageHeader
        title="Stock Reports"
        subtitle="View inventory reports and analytics"
        actions={
          <Button variant="outline">
            <Download className="mr-2 h-4 w-4" />
            Export to Excel
          </Button>
        }
      />

      {/* Summary Cards */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="rounded-lg bg-blue-100 p-3">
                <Package className="h-6 w-6 text-blue-600" />
              </div>
              <div>
                <div className="text-2xl font-bold">655</div>
                <div className="text-sm text-muted-foreground">Total Items</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="rounded-lg bg-green-100 p-3">
                <TrendingUp className="h-6 w-6 text-green-600" />
              </div>
              <div>
                <div className="text-2xl font-bold">{formatIndianCompactCurrency(43000000)}</div>
                <div className="text-sm text-muted-foreground">Total Value</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="rounded-lg bg-yellow-100 p-3">
                <AlertTriangle className="h-6 w-6 text-yellow-600" />
              </div>
              <div>
                <div className="text-2xl font-bold">4</div>
                <div className="text-sm text-muted-foreground">Low Stock Items</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="rounded-lg bg-red-100 p-3">
                <Package className="h-6 w-6 text-red-600" />
              </div>
              <div>
                <div className="text-2xl font-bold">1</div>
                <div className="text-sm text-muted-foreground">Out of Stock</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="summary" className="space-y-4">
        <TabsList>
          <TabsTrigger value="summary">Stock Summary</TabsTrigger>
          <TabsTrigger value="transactions">Transaction History</TabsTrigger>
          <TabsTrigger value="lowstock">Low Stock Alert</TabsTrigger>
          <TabsTrigger value="warehouse">Warehouse Summary</TabsTrigger>
        </TabsList>

        {/* Filters */}
        <Card>
          <CardContent className="pt-6">
            <div className="flex flex-wrap items-end gap-4">
              <div className="min-w-[200px] flex-1">
                <label className="mb-2 block text-sm font-medium">Warehouse</label>
                <Select value={selectedWarehouse} onValueChange={setSelectedWarehouse}>
                  <SelectTrigger>
                    <SelectValue placeholder="All Warehouses" />
                  </SelectTrigger>
                  <SelectContent>
                    {warehouses.map((wh) => (
                      <SelectItem key={wh.id} value={wh.id}>
                        {wh.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="min-w-[200px] flex-1">
                <label className="mb-2 block text-sm font-medium">Category</label>
                <Select value={selectedCategory} onValueChange={setSelectedCategory}>
                  <SelectTrigger>
                    <SelectValue placeholder="All Categories" />
                  </SelectTrigger>
                  <SelectContent>
                    {categories.map((cat) => (
                      <SelectItem key={cat.id} value={cat.id}>
                        {cat.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="min-w-[150px] flex-1">
                <label className="mb-2 block text-sm font-medium">From Date</label>
                <Input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
              </div>
              <div className="min-w-[150px] flex-1">
                <label className="mb-2 block text-sm font-medium">To Date</label>
                <Input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
              </div>
              <Button variant="outline">
                <Filter className="mr-2 h-4 w-4" />
                Apply Filters
              </Button>
            </div>
          </CardContent>
        </Card>

        <TabsContent value="summary">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                Stock Summary Report
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Item Code</TableHead>
                    <TableHead>Item Name</TableHead>
                    <TableHead>Category</TableHead>
                    <TableHead>Warehouse</TableHead>
                    <TableHead className="text-right">Quantity</TableHead>
                    <TableHead className="text-right">Unit Cost</TableHead>
                    <TableHead className="text-right">Total Value</TableHead>
                    <TableHead className="text-right">Reorder Level</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {stockSummary.map((item) => (
                    <TableRow key={item.id}>
                      <TableCell className="font-medium">{item.code}</TableCell>
                      <TableCell>{item.name}</TableCell>
                      <TableCell>{item.category}</TableCell>
                      <TableCell>{item.warehouse}</TableCell>
                      <TableCell className="text-right">{item.quantity}</TableCell>
                      <TableCell className="text-right">
                        {formatIndianCompactCurrency(item.unitCost)}
                      </TableCell>
                      <TableCell className="text-right font-medium">
                        {formatIndianCompactCurrency(item.totalValue)}
                      </TableCell>
                      <TableCell className="text-right">{item.reorderLevel}</TableCell>
                      <TableCell>{getStatusBadge(item.status)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="transactions">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Calendar className="h-5 w-5" />
                Transaction History
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Date</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Reference Type</TableHead>
                    <TableHead>Reference No.</TableHead>
                    <TableHead>Item</TableHead>
                    <TableHead>Warehouse</TableHead>
                    <TableHead className="text-right">Quantity</TableHead>
                    <TableHead className="text-right">Unit Cost</TableHead>
                    <TableHead className="text-right">Total Value</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {transactionHistory.map((txn) => (
                    <TableRow key={txn.id}>
                      <TableCell>{txn.date}</TableCell>
                      <TableCell>{getTypeBadge(txn.type)}</TableCell>
                      <TableCell>
                        <Badge variant="outline">{txn.refType}</Badge>
                      </TableCell>
                      <TableCell className="font-medium">{txn.refNo}</TableCell>
                      <TableCell>{txn.item}</TableCell>
                      <TableCell>{txn.warehouse}</TableCell>
                      <TableCell className="text-right">{txn.qty}</TableCell>
                      <TableCell className="text-right">
                        {formatIndianCompactCurrency(txn.unitCost)}
                      </TableCell>
                      <TableCell className="text-right font-medium">
                        {formatIndianCompactCurrency(txn.totalValue)}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="lowstock">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-yellow-500" />
                Low Stock Alert Report
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Item Code</TableHead>
                    <TableHead>Item Name</TableHead>
                    <TableHead>Category</TableHead>
                    <TableHead className="text-right">Current Qty</TableHead>
                    <TableHead className="text-right">Reorder Level</TableHead>
                    <TableHead className="text-right">Max Level</TableHead>
                    <TableHead className="text-right">Suggested Order</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {lowStockItems.map((item) => (
                    <TableRow key={item.id}>
                      <TableCell className="font-medium">{item.code}</TableCell>
                      <TableCell>{item.name}</TableCell>
                      <TableCell>{item.category}</TableCell>
                      <TableCell className="text-right">
                        <span
                          className={
                            item.currentQty === 0
                              ? 'font-bold text-red-500'
                              : 'font-medium text-yellow-600'
                          }
                        >
                          {item.currentQty}
                        </span>
                      </TableCell>
                      <TableCell className="text-right">{item.reorderLevel}</TableCell>
                      <TableCell className="text-right">{item.maxLevel}</TableCell>
                      <TableCell className="text-right">
                        <Badge variant="default">{item.suggestedOrder}</Badge>
                      </TableCell>
                      <TableCell>
                        {item.currentQty === 0 ? (
                          <Badge variant="destructive">Out of Stock</Badge>
                        ) : (
                          <Badge variant="secondary" className="bg-yellow-100 text-yellow-800">
                            Low Stock
                          </Badge>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="warehouse">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Warehouse className="h-5 w-5" />
                Warehouse Summary Report
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Code</TableHead>
                    <TableHead>Warehouse Name</TableHead>
                    <TableHead className="text-right">Total Items</TableHead>
                    <TableHead className="text-right">Total Value</TableHead>
                    <TableHead className="text-right">Low Stock</TableHead>
                    <TableHead className="text-right">Out of Stock</TableHead>
                    <TableHead>Health</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {warehouseSummary.map((wh) => (
                    <TableRow key={wh.id}>
                      <TableCell className="font-medium">{wh.code}</TableCell>
                      <TableCell>{wh.name}</TableCell>
                      <TableCell className="text-right">{wh.totalItems}</TableCell>
                      <TableCell className="text-right font-medium">
                        {formatIndianCompactCurrency(wh.totalValue)}
                      </TableCell>
                      <TableCell className="text-right">
                        {wh.lowStockItems > 0 ? (
                          <Badge variant="secondary" className="bg-yellow-100 text-yellow-800">
                            {wh.lowStockItems}
                          </Badge>
                        ) : (
                          <span className="text-muted-foreground">0</span>
                        )}
                      </TableCell>
                      <TableCell className="text-right">
                        {wh.outOfStockItems > 0 ? (
                          <Badge variant="destructive">{wh.outOfStockItems}</Badge>
                        ) : (
                          <span className="text-muted-foreground">0</span>
                        )}
                      </TableCell>
                      <TableCell>
                        {wh.outOfStockItems > 0 ? (
                          <Badge variant="destructive">Needs Attention</Badge>
                        ) : wh.lowStockItems > 0 ? (
                          <Badge variant="secondary" className="bg-yellow-100 text-yellow-800">
                            Monitor
                          </Badge>
                        ) : (
                          <Badge variant="default">Healthy</Badge>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
