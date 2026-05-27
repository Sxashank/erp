import {
  Calculator,
  Download,
  TrendingUp,
  TrendingDown,
  Warehouse,
  Package,
  PieChart,
  Calendar,
} from 'lucide-react';
import { useState } from 'react';

import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
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
const formatPercentage = (value: number) => {
  return `${value.toFixed(1)}%`;
};

// Mock data - Valuation by Item
const itemValuation = [
  {
    id: '1',
    code: 'ITM-001',
    name: 'A4 Paper (500 sheets)',
    category: 'Office Supplies',
    quantity: 150,
    avgCost: 250,
    fifoValue: 37500,
    lifoValue: 38000,
    weightedAvgValue: 37750,
    method: 'WEIGHTED_AVG',
  },
  {
    id: '2',
    code: 'ITM-002',
    name: 'Ball Pen Blue',
    category: 'Stationery',
    quantity: 500,
    avgCost: 10,
    fifoValue: 5000,
    lifoValue: 5200,
    weightedAvgValue: 5100,
    method: 'WEIGHTED_AVG',
  },
  {
    id: '3',
    code: 'ITM-003',
    name: 'HP LaserJet Toner',
    category: 'IT Equipment',
    quantity: 25,
    avgCost: 3500,
    fifoValue: 87500,
    lifoValue: 90000,
    weightedAvgValue: 88750,
    method: 'FIFO',
  },
  {
    id: '4',
    code: 'ITM-004',
    name: 'Dell Laptop',
    category: 'IT Equipment',
    quantity: 10,
    avgCost: 55000,
    fifoValue: 550000,
    lifoValue: 560000,
    weightedAvgValue: 555000,
    method: 'FIFO',
  },
  {
    id: '5',
    code: 'ITM-005',
    name: 'Office Chair',
    category: 'Furniture',
    quantity: 30,
    avgCost: 8000,
    fifoValue: 240000,
    lifoValue: 245000,
    weightedAvgValue: 242500,
    method: 'WEIGHTED_AVG',
  },
  {
    id: '6',
    code: 'ITM-006',
    name: 'Stapler',
    category: 'Office Supplies',
    quantity: 45,
    avgCost: 150,
    fifoValue: 6750,
    lifoValue: 6900,
    weightedAvgValue: 6825,
    method: 'WEIGHTED_AVG',
  },
];

// Mock data - Valuation by Category
const categoryValuation = [
  {
    id: '1',
    name: 'Office Supplies',
    itemCount: 45,
    totalQuantity: 1250,
    fifoValue: 125000,
    lifoValue: 128000,
    weightedAvgValue: 126500,
    percentOfTotal: 3.2,
  },
  {
    id: '2',
    name: 'IT Equipment',
    itemCount: 120,
    totalQuantity: 450,
    fifoValue: 2850000,
    lifoValue: 2920000,
    weightedAvgValue: 2885000,
    percentOfTotal: 72.5,
  },
  {
    id: '3',
    name: 'Stationery',
    itemCount: 78,
    totalQuantity: 3500,
    fifoValue: 85000,
    lifoValue: 87500,
    weightedAvgValue: 86250,
    percentOfTotal: 2.2,
  },
  {
    id: '4',
    name: 'Furniture',
    itemCount: 25,
    totalQuantity: 180,
    fifoValue: 880000,
    lifoValue: 895000,
    weightedAvgValue: 887500,
    percentOfTotal: 22.1,
  },
];

// Mock data - Valuation by Warehouse
const warehouseValuation = [
  {
    id: '1',
    code: 'WH-001',
    name: 'Main Warehouse',
    itemCount: 450,
    fifoValue: 2800000,
    lifoValue: 2870000,
    weightedAvgValue: 2835000,
    percentOfTotal: 70.5,
  },
  {
    id: '2',
    code: 'WH-002',
    name: 'Branch A Store',
    itemCount: 120,
    fifoValue: 750000,
    lifoValue: 768000,
    weightedAvgValue: 759000,
    percentOfTotal: 18.9,
  },
  {
    id: '3',
    code: 'WH-003',
    name: 'Branch B Store',
    itemCount: 85,
    fifoValue: 390000,
    lifoValue: 402000,
    weightedAvgValue: 396000,
    percentOfTotal: 9.9,
  },
  {
    id: '4',
    code: 'WH-004',
    name: 'Transit Warehouse',
    itemCount: 10,
    fifoValue: 28000,
    lifoValue: 29000,
    weightedAvgValue: 28500,
    percentOfTotal: 0.7,
  },
];

// Mock data - Aging Analysis
const agingAnalysis = [
  {
    id: '1',
    code: 'ITM-001',
    name: 'A4 Paper (500 sheets)',
    within30: 100,
    days31to60: 30,
    days61to90: 15,
    over90: 5,
    totalQty: 150,
    value: 37500,
  },
  {
    id: '2',
    code: 'ITM-002',
    name: 'Ball Pen Blue',
    within30: 350,
    days31to60: 100,
    days61to90: 50,
    over90: 0,
    totalQty: 500,
    value: 5000,
  },
  {
    id: '3',
    code: 'ITM-003',
    name: 'HP LaserJet Toner',
    within30: 10,
    days31to60: 8,
    days61to90: 5,
    over90: 2,
    totalQty: 25,
    value: 87500,
  },
  {
    id: '4',
    code: 'ITM-005',
    name: 'Office Chair',
    within30: 20,
    days31to60: 5,
    days61to90: 3,
    over90: 2,
    totalQty: 30,
    value: 240000,
  },
];

const warehouses = [
  { id: ALL_OPTION_VALUE, name: 'All Warehouses' },
  { id: '1', name: 'Main Warehouse' },
  { id: '2', name: 'Branch A Store' },
  { id: '3', name: 'Branch B Store' },
];

const valuationMethods = [
  { value: 'FIFO', label: 'First In, First Out (FIFO)' },
  { value: 'LIFO', label: 'Last In, First Out (LIFO)' },
  { value: 'WEIGHTED_AVG', label: 'Weighted Average' },
];

export default function InventoryValuation() {
  const [selectedWarehouse, setSelectedWarehouse] = useState(ALL_OPTION_VALUE);
  const [selectedMethod, setSelectedMethod] = useState<'FIFO' | 'LIFO' | 'WEIGHTED_AVG'>(
    'WEIGHTED_AVG',
  );
  const [asOfDate, setAsOfDate] = useState(new Date().toISOString().split('T')[0]);

  const totalFIFO = itemValuation.reduce((sum, item) => sum + item.fifoValue, 0);
  const totalLIFO = itemValuation.reduce((sum, item) => sum + item.lifoValue, 0);
  const totalWeightedAvg = itemValuation.reduce((sum, item) => sum + item.weightedAvgValue, 0);

  const getSelectedValue = (item: (typeof itemValuation)[0]) => {
    switch (selectedMethod) {
      case 'FIFO':
        return item.fifoValue;
      case 'LIFO':
        return item.lifoValue;
      case 'WEIGHTED_AVG':
        return item.weightedAvgValue;
    }
  };

  const getCategoryValue = (cat: (typeof categoryValuation)[0]) => {
    switch (selectedMethod) {
      case 'FIFO':
        return cat.fifoValue;
      case 'LIFO':
        return cat.lifoValue;
      case 'WEIGHTED_AVG':
        return cat.weightedAvgValue;
    }
  };

  const getWarehouseValue = (wh: (typeof warehouseValuation)[0]) => {
    switch (selectedMethod) {
      case 'FIFO':
        return wh.fifoValue;
      case 'LIFO':
        return wh.lifoValue;
      case 'WEIGHTED_AVG':
        return wh.weightedAvgValue;
    }
  };

  const totalSelected =
    selectedMethod === 'FIFO'
      ? totalFIFO
      : selectedMethod === 'LIFO'
        ? totalLIFO
        : totalWeightedAvg;

  return (
    <div className="container mx-auto space-y-6 py-6">
      <PageHeader
        title="Inventory Valuation"
        subtitle="View inventory value using different costing methods"
        actions={
          <Button variant="outline">
            <Download className="mr-2 h-4 w-4" />
            Export Report
          </Button>
        }
      />

      {/* Valuation Summary Cards */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
        <Card className={selectedMethod === 'FIFO' ? 'ring-2 ring-primary' : ''}>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="rounded-lg bg-blue-100 p-3">
                <TrendingUp className="h-6 w-6 text-blue-600" />
              </div>
              <div>
                <div className="text-sm text-muted-foreground">FIFO Value</div>
                <div className="text-xl font-bold">{formatIndianCompactCurrency(totalFIFO)}</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className={selectedMethod === 'LIFO' ? 'ring-2 ring-primary' : ''}>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="rounded-lg bg-green-100 p-3">
                <TrendingDown className="h-6 w-6 text-green-600" />
              </div>
              <div>
                <div className="text-sm text-muted-foreground">LIFO Value</div>
                <div className="text-xl font-bold">{formatIndianCompactCurrency(totalLIFO)}</div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className={selectedMethod === 'WEIGHTED_AVG' ? 'ring-2 ring-primary' : ''}>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="rounded-lg bg-purple-100 p-3">
                <Calculator className="h-6 w-6 text-purple-600" />
              </div>
              <div>
                <div className="text-sm text-muted-foreground">Weighted Avg</div>
                <div className="text-xl font-bold">
                  {formatIndianCompactCurrency(totalWeightedAvg)}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="rounded-lg bg-orange-100 p-3">
                <Package className="h-6 w-6 text-orange-600" />
              </div>
              <div>
                <div className="text-sm text-muted-foreground">Total Items</div>
                <div className="text-xl font-bold">655</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-wrap items-end gap-4">
            <div className="min-w-[200px] flex-1">
              <label className="mb-2 block text-sm font-medium">Valuation Method</label>
              <Select
                value={selectedMethod}
                onValueChange={(v: 'FIFO' | 'LIFO' | 'WEIGHTED_AVG') => setSelectedMethod(v)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {valuationMethods.map((method) => (
                    <SelectItem key={method.value} value={method.value}>
                      {method.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
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
            <div className="min-w-[150px] flex-1">
              <label className="mb-2 block text-sm font-medium">As of Date</label>
              <input
                type="date"
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background"
                value={asOfDate}
                onChange={(e) => setAsOfDate(e.target.value)}
              />
            </div>
            <Button>
              <Calendar className="mr-2 h-4 w-4" />
              Generate Report
            </Button>
          </div>
        </CardContent>
      </Card>

      <Tabs defaultValue="item" className="space-y-4">
        <TabsList>
          <TabsTrigger value="item">By Item</TabsTrigger>
          <TabsTrigger value="category">By Category</TabsTrigger>
          <TabsTrigger value="warehouse">By Warehouse</TabsTrigger>
          <TabsTrigger value="aging">Aging Analysis</TabsTrigger>
        </TabsList>

        <TabsContent value="item">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Package className="h-5 w-5" />
                Item-wise Valuation (
                {valuationMethods.find((m) => m.value === selectedMethod)?.label})
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Item Code</TableHead>
                    <TableHead>Item Name</TableHead>
                    <TableHead>Category</TableHead>
                    <TableHead className="text-right">Quantity</TableHead>
                    <TableHead className="text-right">Avg Cost</TableHead>
                    <TableHead className="text-right">Valuation</TableHead>
                    <TableHead>Method</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {itemValuation.map((item) => (
                    <TableRow key={item.id}>
                      <TableCell className="font-medium">{item.code}</TableCell>
                      <TableCell>{item.name}</TableCell>
                      <TableCell>
                        <Badge variant="outline">{item.category}</Badge>
                      </TableCell>
                      <TableCell className="text-right">{item.quantity}</TableCell>
                      <TableCell className="text-right">
                        {formatIndianCompactCurrency(item.avgCost)}
                      </TableCell>
                      <TableCell className="text-right font-bold">
                        {formatIndianCompactCurrency(getSelectedValue(item))}
                      </TableCell>
                      <TableCell>
                        <Badge variant={item.method === selectedMethod ? 'default' : 'secondary'}>
                          {item.method}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                  <TableRow className="bg-muted/50 font-bold">
                    <TableCell colSpan={5}>Total</TableCell>
                    <TableCell className="text-right">
                      {formatIndianCompactCurrency(totalSelected)}
                    </TableCell>
                    <TableCell></TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="category">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <PieChart className="h-5 w-5" />
                Category-wise Valuation
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Category</TableHead>
                    <TableHead className="text-right">Items</TableHead>
                    <TableHead className="text-right">Total Qty</TableHead>
                    <TableHead className="text-right">FIFO</TableHead>
                    <TableHead className="text-right">LIFO</TableHead>
                    <TableHead className="text-right">Weighted Avg</TableHead>
                    <TableHead className="text-right">% of Total</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {categoryValuation.map((cat) => (
                    <TableRow key={cat.id}>
                      <TableCell className="font-medium">{cat.name}</TableCell>
                      <TableCell className="text-right">{cat.itemCount}</TableCell>
                      <TableCell className="text-right">{cat.totalQuantity}</TableCell>
                      <TableCell
                        className={`text-right ${selectedMethod === 'FIFO' ? 'font-bold' : ''}`}
                      >
                        {formatIndianCompactCurrency(cat.fifoValue)}
                      </TableCell>
                      <TableCell
                        className={`text-right ${selectedMethod === 'LIFO' ? 'font-bold' : ''}`}
                      >
                        {formatIndianCompactCurrency(cat.lifoValue)}
                      </TableCell>
                      <TableCell
                        className={`text-right ${selectedMethod === 'WEIGHTED_AVG' ? 'font-bold' : ''}`}
                      >
                        {formatIndianCompactCurrency(cat.weightedAvgValue)}
                      </TableCell>
                      <TableCell className="text-right">
                        <Badge variant="outline">{formatPercentage(cat.percentOfTotal)}</Badge>
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
                Warehouse-wise Valuation
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Code</TableHead>
                    <TableHead>Warehouse</TableHead>
                    <TableHead className="text-right">Items</TableHead>
                    <TableHead className="text-right">FIFO</TableHead>
                    <TableHead className="text-right">LIFO</TableHead>
                    <TableHead className="text-right">Weighted Avg</TableHead>
                    <TableHead className="text-right">% of Total</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {warehouseValuation.map((wh) => (
                    <TableRow key={wh.id}>
                      <TableCell className="font-medium">{wh.code}</TableCell>
                      <TableCell>{wh.name}</TableCell>
                      <TableCell className="text-right">{wh.itemCount}</TableCell>
                      <TableCell
                        className={`text-right ${selectedMethod === 'FIFO' ? 'font-bold' : ''}`}
                      >
                        {formatIndianCompactCurrency(wh.fifoValue)}
                      </TableCell>
                      <TableCell
                        className={`text-right ${selectedMethod === 'LIFO' ? 'font-bold' : ''}`}
                      >
                        {formatIndianCompactCurrency(wh.lifoValue)}
                      </TableCell>
                      <TableCell
                        className={`text-right ${selectedMethod === 'WEIGHTED_AVG' ? 'font-bold' : ''}`}
                      >
                        {formatIndianCompactCurrency(wh.weightedAvgValue)}
                      </TableCell>
                      <TableCell className="text-right">
                        <Badge variant="outline">{formatPercentage(wh.percentOfTotal)}</Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="aging">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Calendar className="h-5 w-5" />
                Inventory Aging Analysis
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Item Code</TableHead>
                    <TableHead>Item Name</TableHead>
                    <TableHead className="text-right">0-30 Days</TableHead>
                    <TableHead className="text-right">31-60 Days</TableHead>
                    <TableHead className="text-right">61-90 Days</TableHead>
                    <TableHead className="text-right">Over 90 Days</TableHead>
                    <TableHead className="text-right">Total Qty</TableHead>
                    <TableHead className="text-right">Value</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {agingAnalysis.map((item) => {
                    const over90Percent = (item.over90 / item.totalQty) * 100;
                    return (
                      <TableRow key={item.id}>
                        <TableCell className="font-medium">{item.code}</TableCell>
                        <TableCell>{item.name}</TableCell>
                        <TableCell className="text-right">
                          <Badge variant="default">{item.within30}</Badge>
                        </TableCell>
                        <TableCell className="text-right">
                          <Badge variant="secondary">{item.days31to60}</Badge>
                        </TableCell>
                        <TableCell className="text-right">
                          <Badge variant="secondary" className="bg-yellow-100 text-yellow-800">
                            {item.days61to90}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-right">
                          {item.over90 > 0 ? (
                            <Badge variant="destructive">{item.over90}</Badge>
                          ) : (
                            <span className="text-muted-foreground">0</span>
                          )}
                        </TableCell>
                        <TableCell className="text-right font-medium">{item.totalQty}</TableCell>
                        <TableCell className="text-right font-bold">
                          {formatIndianCompactCurrency(item.value)}
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>

              <div className="mt-6 rounded-lg bg-muted p-4">
                <h4 className="mb-2 font-medium">Aging Legend</h4>
                <div className="flex gap-4 text-sm">
                  <div className="flex items-center gap-2">
                    <Badge variant="default">0-30 Days</Badge>
                    <span>Fresh Stock</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant="secondary">31-60 Days</Badge>
                    <span>Normal</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant="secondary" className="bg-yellow-100 text-yellow-800">
                      61-90 Days
                    </Badge>
                    <span>Aging</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant="destructive">Over 90 Days</Badge>
                    <span>Slow Moving</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
