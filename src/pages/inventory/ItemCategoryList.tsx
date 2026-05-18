import { Plus, Search, Edit, Trash2, FolderTree } from 'lucide-react';
import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
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
  {
    id: '1',
    code: 'CAT-001',
    name: 'Office Supplies',
    description: 'General office supplies and consumables',
    parentCategory: null,
    isStockable: true,
    requiresSerialNumber: false,
    requiresBatchNumber: false,
    itemCount: 45,
    status: 'ACTIVE',
  },
  {
    id: '2',
    code: 'CAT-002',
    name: 'IT Equipment',
    description: 'Computers, peripherals, and IT accessories',
    parentCategory: null,
    isStockable: true,
    requiresSerialNumber: true,
    requiresBatchNumber: false,
    itemCount: 120,
    status: 'ACTIVE',
  },
  {
    id: '3',
    code: 'CAT-003',
    name: 'Stationery',
    description: 'Paper, pens, and writing materials',
    parentCategory: 'Office Supplies',
    isStockable: true,
    requiresSerialNumber: false,
    requiresBatchNumber: true,
    itemCount: 78,
    status: 'ACTIVE',
  },
  {
    id: '4',
    code: 'CAT-004',
    name: 'Furniture',
    description: 'Office furniture and fixtures',
    parentCategory: null,
    isStockable: true,
    requiresSerialNumber: true,
    requiresBatchNumber: false,
    itemCount: 25,
    status: 'ACTIVE',
  },
  {
    id: '5',
    code: 'CAT-005',
    name: 'Printers & Accessories',
    description: 'Printers, cartridges, and printing supplies',
    parentCategory: 'IT Equipment',
    isStockable: true,
    requiresSerialNumber: false,
    requiresBatchNumber: true,
    itemCount: 35,
    status: 'INACTIVE',
  },
];

export default function ItemCategoryList() {
  const [searchTerm, setSearchTerm] = useState('');
  const navigate = useNavigate();

  const filteredCategories = categories.filter(
    (cat) =>
      cat.code.toLowerCase().includes(searchTerm.toLowerCase()) ||
      cat.name.toLowerCase().includes(searchTerm.toLowerCase()),
  );

  return (
    <div className="container mx-auto space-y-6 py-6">
      <PageHeader
        title="Item Categories"
        subtitle="Manage item category hierarchy"
        actions={
          <Button onClick={() => navigate('/admin/inventory/categories/new')}>
            <Plus className="mr-2 h-4 w-4" />
            Add Category
          </Button>
        }
      />

      {/* Search */}
      <Card>
        <CardContent className="pt-6">
          <div className="relative max-w-md">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 transform text-muted-foreground" />
            <Input
              placeholder="Search categories..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
        </CardContent>
      </Card>

      {/* Categories Table */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FolderTree className="h-5 w-5" />
            Categories ({filteredCategories.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Code</TableHead>
                <TableHead>Category Name</TableHead>
                <TableHead>Parent Category</TableHead>
                <TableHead>Description</TableHead>
                <TableHead className="text-center">Serial #</TableHead>
                <TableHead className="text-center">Batch #</TableHead>
                <TableHead className="text-right">Items</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredCategories.map((cat) => (
                <TableRow key={cat.id}>
                  <TableCell className="font-medium">{cat.code}</TableCell>
                  <TableCell>{cat.name}</TableCell>
                  <TableCell>
                    {cat.parentCategory ? (
                      <Badge variant="outline">{cat.parentCategory}</Badge>
                    ) : (
                      <span className="text-muted-foreground">-</span>
                    )}
                  </TableCell>
                  <TableCell className="max-w-xs truncate">{cat.description}</TableCell>
                  <TableCell className="text-center">
                    {cat.requiresSerialNumber ? (
                      <Badge variant="default">Yes</Badge>
                    ) : (
                      <Badge variant="secondary">No</Badge>
                    )}
                  </TableCell>
                  <TableCell className="text-center">
                    {cat.requiresBatchNumber ? (
                      <Badge variant="default">Yes</Badge>
                    ) : (
                      <Badge variant="secondary">No</Badge>
                    )}
                  </TableCell>
                  <TableCell className="text-right">{cat.itemCount}</TableCell>
                  <TableCell>
                    <Badge variant={cat.status === 'ACTIVE' ? 'default' : 'secondary'}>
                      {cat.status}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end gap-2">
                      <Button variant="ghost" size="icon" asChild>
                        <Link to={`/admin/inventory/categories/${cat.id}/edit`}>
                          <Edit className="h-4 w-4" />
                        </Link>
                      </Button>
                      <Button variant="ghost" size="icon">
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
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
