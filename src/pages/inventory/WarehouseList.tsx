import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Plus, Search, Edit, Trash2, Warehouse, MapPin, Star } from 'lucide-react';

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(value);
};

// Mock data
const warehouses = [
  {
    id: '1',
    code: 'WH-001',
    name: 'Main Warehouse',
    type: 'MAIN',
    branch: 'Head Office',
    city: 'Mumbai',
    state: 'Maharashtra',
    contactPerson: 'Rajesh Kumar',
    contactPhone: '9876543210',
    isDefault: true,
    allowNegativeStock: false,
    totalItems: 850,
    totalValue: 32000000,
    status: 'ACTIVE',
  },
  {
    id: '2',
    code: 'WH-002',
    name: 'Branch A Store',
    type: 'BRANCH',
    branch: 'Branch A',
    city: 'Pune',
    state: 'Maharashtra',
    contactPerson: 'Amit Sharma',
    contactPhone: '9876543211',
    isDefault: false,
    allowNegativeStock: false,
    totalItems: 200,
    totalValue: 6500000,
    status: 'ACTIVE',
  },
  {
    id: '3',
    code: 'WH-003',
    name: 'Branch B Store',
    type: 'BRANCH',
    branch: 'Branch B',
    city: 'Delhi',
    state: 'Delhi',
    contactPerson: 'Priya Singh',
    contactPhone: '9876543212',
    isDefault: false,
    allowNegativeStock: true,
    totalItems: 150,
    totalValue: 4500000,
    status: 'ACTIVE',
  },
  {
    id: '4',
    code: 'WH-004',
    name: 'Transit Warehouse',
    type: 'TRANSIT',
    branch: null,
    city: 'Mumbai',
    state: 'Maharashtra',
    contactPerson: 'Vijay Patil',
    contactPhone: '9876543213',
    isDefault: false,
    allowNegativeStock: false,
    totalItems: 50,
    totalValue: 2000000,
    status: 'ACTIVE',
  },
];

export default function WarehouseList() {
  const [searchTerm, setSearchTerm] = useState('');

  const filteredWarehouses = warehouses.filter(
    (wh) =>
      wh.code.toLowerCase().includes(searchTerm.toLowerCase()) ||
      wh.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      wh.city.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getTypeVariant = (type: string) => {
    switch (type) {
      case 'MAIN':
        return 'default';
      case 'BRANCH':
        return 'secondary';
      case 'TRANSIT':
        return 'outline';
      default:
        return 'secondary';
    }
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      <PageHeader
        title="Warehouses"
        subtitle="Manage storage locations"
        actions={
          <Button asChild>
            <Link to="/inventory/warehouses/new">
              <Plus className="h-4 w-4 mr-2" />
              Add Warehouse
            </Link>
          </Button>
        }
      />

      {/* Search */}
      <Card>
        <CardContent className="pt-6">
          <div className="relative max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search warehouses..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>
        </CardContent>
      </Card>

      {/* Warehouses Table */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Warehouse className="h-5 w-5" />
            Warehouses ({filteredWarehouses.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Code</TableHead>
                <TableHead>Warehouse Name</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Location</TableHead>
                <TableHead>Contact</TableHead>
                <TableHead className="text-right">Items</TableHead>
                <TableHead className="text-right">Value</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredWarehouses.map((wh) => (
                <TableRow key={wh.id}>
                  <TableCell className="font-medium">
                    <div className="flex items-center gap-2">
                      {wh.code}
                      {wh.isDefault && (
                        <Star className="h-4 w-4 text-yellow-500 fill-yellow-500" />
                      )}
                    </div>
                  </TableCell>
                  <TableCell>{wh.name}</TableCell>
                  <TableCell>
                    <Badge variant={getTypeVariant(wh.type)}>{wh.type}</Badge>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-1">
                      <MapPin className="h-3 w-3 text-muted-foreground" />
                      {wh.city}, {wh.state}
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="text-sm">
                      <div>{wh.contactPerson}</div>
                      <div className="text-muted-foreground">{wh.contactPhone}</div>
                    </div>
                  </TableCell>
                  <TableCell className="text-right">{wh.totalItems}</TableCell>
                  <TableCell className="text-right">
                    {formatCurrency(wh.totalValue)}
                  </TableCell>
                  <TableCell>
                    <Badge variant={wh.status === 'ACTIVE' ? 'default' : 'secondary'}>
                      {wh.status}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end gap-2">
                      <Button variant="ghost" size="icon" asChild>
                        <Link to={`/inventory/warehouses/${wh.id}/edit`}>
                          <Edit className="h-4 w-4" />
                        </Link>
                      </Button>
                      <Button variant="ghost" size="icon" disabled={wh.isDefault}>
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
