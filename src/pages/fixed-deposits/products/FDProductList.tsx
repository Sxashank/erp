/**
 * FD Product List Page
 */

import { Plus, Edit, Trash2, Search, Percent } from 'lucide-react';
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

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
import { useToast } from '@/hooks/use-toast';
import { useRequiredActiveOrganizationId } from '@/hooks/useOrganization';
import type { FDProduct } from '@/services/fixedDepositService';
import fixedDepositService from '@/services/fixedDepositService';

export default function FDProductList() {
  const navigate = useNavigate();
  const { toast } = useToast();

  const [products, setProducts] = useState<FDProduct[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [total, setTotal] = useState(0);

  const organizationId = useRequiredActiveOrganizationId();

  useEffect(() => {
    loadProducts();
  }, [organizationId]);

  const loadProducts = async () => {
    try {
      setLoading(true);
      const response = await fixedDepositService.listProducts({
        active_only: false,
      });
      setProducts(response.items);
      setTotal(response.total);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load FD products',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to deactivate this product?')) return;

    try {
      await fixedDepositService.deleteProduct(id);
      toast({
        title: 'Success',
        description: 'Product deactivated successfully',
      });
      loadProducts();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to deactivate product',
        variant: 'destructive',
      });
    }
  };

  const filteredProducts = products.filter(
    (product) =>
      product.product_code.toLowerCase().includes(searchTerm.toLowerCase()) ||
      product.product_name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const formatFrequency = (freq: string) => {
    return freq.replace('_', ' ').toLowerCase().replace(/\b\w/g, (l) => l.toUpperCase());
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      <PageHeader
        title="FD Products"
        subtitle="Manage fixed deposit product configurations"
        actions={
          <Button onClick={() => navigate('/admin/fixed-deposits/products/new')}>
            <Plus className="mr-2 h-4 w-4" />
            Add Product
          </Button>
        }
      />

      <Card>
        <CardHeader>
          <div className="flex flex-col md:flex-row gap-4 justify-between">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
              <Input
                placeholder="Search products..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Code</TableHead>
                <TableHead>Name</TableHead>
                <TableHead>Tenure (Days)</TableHead>
                <TableHead>Amount Range</TableHead>
                <TableHead>Interest Payout</TableHead>
                <TableHead>Compounding</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={8} className="text-center py-8">
                    Loading...
                  </TableCell>
                </TableRow>
              ) : filteredProducts.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8} className="text-center py-8">
                    No products found
                  </TableCell>
                </TableRow>
              ) : (
                filteredProducts.map((product) => (
                  <TableRow key={product.id}>
                    <TableCell className="font-mono">{product.product_code}</TableCell>
                    <TableCell className="font-medium">{product.product_name}</TableCell>
                    <TableCell>
                      {product.min_tenure_days} - {product.max_tenure_days}
                    </TableCell>
                    <TableCell>
                      {product.min_amount.toLocaleString()}
                      {product.max_amount
                        ? ` - ${product.max_amount.toLocaleString()}`
                        : '+'}
                    </TableCell>
                    <TableCell>{formatFrequency(product.interest_payout_frequency)}</TableCell>
                    <TableCell>{formatFrequency(product.compounding_frequency)}</TableCell>
                    <TableCell>
                      <Badge variant={product.is_active ? 'default' : 'secondary'}>
                        {product.is_active ? 'Active' : 'Inactive'}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-2">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() =>
                            navigate(`/admin/fixed-deposits/products/${product.id}/slabs`)
                          }
                          title="Interest Slabs"
                        >
                          <Percent className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() =>
                            navigate(`/admin/fixed-deposits/products/${product.id}/edit`)
                          }
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleDelete(product.id)}
                        >
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
