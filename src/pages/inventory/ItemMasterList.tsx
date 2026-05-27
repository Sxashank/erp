import { Plus, Search, Filter, Edit, Trash2, Eye, Package } from 'lucide-react';
import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

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
// Mock data
const categories = [
  { id: '1', name: 'Office Supplies' },
  { id: '2', name: 'IT Equipment' },
  { id: '3', name: 'Stationery' },
  { id: '4', name: 'Furniture' },
];

const items = [
  {
    id: '1',
    code: 'ITM-001',
    name: 'A4 Paper Ream',
    category: 'Stationery',
    uom: 'REAM',
    type: 'STOCK',
    standardCost: 250,
    sellingPrice: 300,
    currentStock: 450,
    minStock: 100,
    maxStock: 1000,
    status: 'ACTIVE',
  },
  {
    id: '2',
    code: 'ITM-002',
    name: 'HP LaserJet Cartridge',
    category: 'IT Equipment',
    uom: 'EACH',
    type: 'STOCK',
    standardCost: 3500,
    sellingPrice: 4500,
    currentStock: 15,
    minStock: 20,
    maxStock: 100,
    status: 'ACTIVE',
  },
  {
    id: '3',
    code: 'ITM-003',
    name: 'Ball Point Pen (Blue)',
    category: 'Stationery',
    uom: 'EACH',
    type: 'STOCK',
    standardCost: 10,
    sellingPrice: 15,
    currentStock: 500,
    minStock: 200,
    maxStock: 2000,
    status: 'ACTIVE',
  },
  {
    id: '4',
    code: 'ITM-004',
    name: 'Office Chair - Executive',
    category: 'Furniture',
    uom: 'EACH',
    type: 'FIXED_ASSET',
    standardCost: 15000,
    sellingPrice: 18000,
    currentStock: 10,
    minStock: 5,
    maxStock: 50,
    status: 'ACTIVE',
  },
  {
    id: '5',
    code: 'ITM-005',
    name: 'Stapler Heavy Duty',
    category: 'Office Supplies',
    uom: 'EACH',
    type: 'STOCK',
    standardCost: 350,
    sellingPrice: 450,
    currentStock: 0,
    minStock: 10,
    maxStock: 100,
    status: 'INACTIVE',
  },
];

export default function ItemMasterList() {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const navigate = useNavigate();

  const filteredItems = items.filter((item) => {
    const matchesSearch =
      item.code.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.name.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = selectedCategory === 'all' || item.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  const getStockStatus = (current: number, min: number) => {
    if (current === 0) return { label: 'Out of Stock', variant: 'destructive' as const };
    if (current < min) return { label: 'Low Stock', variant: 'secondary' as const };
    return { label: 'In Stock', variant: 'default' as const };
  };

  return (
    <div className="container mx-auto space-y-6 py-6">
      <PageHeader
        title="Item Master"
        subtitle="Manage inventory items"
        actions={
          <div className="flex gap-2">
            <Button variant="outline" asChild>
              <Link to="/admin/inventory/categories">
                <Filter className="mr-2 h-4 w-4" />
                Categories
              </Link>
            </Button>
            <Button onClick={() => navigate('/admin/inventory/items/new')}>
              <Plus className="mr-2 h-4 w-4" />
              Add Item
            </Button>
          </div>
        }
      />

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col gap-4 md:flex-row">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 transform text-muted-foreground" />
              <Input
                placeholder="Search by code or name..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            <Select value={selectedCategory} onValueChange={setSelectedCategory}>
              <SelectTrigger className="w-full md:w-48">
                <SelectValue placeholder="All Categories" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Categories</SelectItem>
                {categories.map((cat) => (
                  <SelectItem key={cat.id} value={cat.name}>
                    {cat.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Items Table */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Package className="h-5 w-5" />
            Items ({filteredItems.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Item Code</TableHead>
                <TableHead>Item Name</TableHead>
                <TableHead>Category</TableHead>
                <TableHead>Type</TableHead>
                <TableHead className="text-right">Cost</TableHead>
                <TableHead className="text-right">Price</TableHead>
                <TableHead className="text-right">Stock</TableHead>
                <TableHead>Stock Status</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredItems.map((item) => {
                const stockStatus = getStockStatus(item.currentStock, item.minStock);
                return (
                  <TableRow key={item.id}>
                    <TableCell className="font-medium">{item.code}</TableCell>
                    <TableCell>{item.name}</TableCell>
                    <TableCell>{item.category}</TableCell>
                    <TableCell>
                      <Badge variant="outline">{item.type}</Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      {formatIndianCompactCurrency(item.standardCost)}
                    </TableCell>
                    <TableCell className="text-right">
                      {formatIndianCompactCurrency(item.sellingPrice)}
                    </TableCell>
                    <TableCell className="text-right font-medium">
                      {item.currentStock} {item.uom}
                    </TableCell>
                    <TableCell>
                      <Badge variant={stockStatus.variant}>{stockStatus.label}</Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant={item.status === 'ACTIVE' ? 'default' : 'secondary'}>
                        {item.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-2">
                        <Button variant="ghost" size="icon" asChild>
                          <Link to={`/admin/inventory/items/${item.id}`}>
                            <Eye className="h-4 w-4" />
                          </Link>
                        </Button>
                        <Button variant="ghost" size="icon" asChild>
                          <Link to={`/admin/inventory/items/${item.id}/edit`}>
                            <Edit className="h-4 w-4" />
                          </Link>
                        </Button>
                        <Button variant="ghost" size="icon">
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
