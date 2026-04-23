/**
 * FD Interest Slabs Page
 */

import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, Plus, Edit, Trash2, Save, X } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
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
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { useToast } from '@/hooks/use-toast';
import fixedDepositService, {
  FDProduct,
  FDInterestSlab,
  FDCustomerCategory,
} from '@/services/fixedDepositService';

const CUSTOMER_CATEGORIES: { value: FDCustomerCategory; label: string }[] = [
  { value: 'GENERAL', label: 'General' },
  { value: 'SENIOR_CITIZEN', label: 'Senior Citizen' },
  { value: 'STAFF', label: 'Staff' },
  { value: 'NRI', label: 'NRI' },
  { value: 'CORPORATE', label: 'Corporate' },
];

interface SlabForm {
  customer_category: FDCustomerCategory;
  min_tenure_days: number;
  max_tenure_days: number;
  min_amount?: number;
  max_amount?: number;
  interest_rate: number;
  effective_from: string;
  effective_to?: string;
  is_active: boolean;
}

export default function FDInterestSlabs() {
  const navigate = useNavigate();
  const { id: productId } = useParams();
  const { toast } = useToast();

  const [product, setProduct] = useState<FDProduct | null>(null);
  const [loading, setLoading] = useState(true);
  const [editingSlabId, setEditingSlabId] = useState<string | null>(null);
  const [showNewForm, setShowNewForm] = useState(false);
  const [saving, setSaving] = useState(false);

  const [formData, setFormData] = useState<SlabForm>({
    customer_category: 'GENERAL',
    min_tenure_days: 7,
    max_tenure_days: 365,
    interest_rate: 5.5,
    effective_from: new Date().toISOString().split('T')[0],
    is_active: true,
  });

  useEffect(() => {
    if (productId) {
      loadProduct(productId);
    }
  }, [productId]);

  const loadProduct = async (id: string) => {
    try {
      setLoading(true);
      const data = await fixedDepositService.getProduct(id);
      setProduct(data);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load product',
        variant: 'destructive',
      });
      navigate('/admin/fixed-deposits/products');
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setFormData({
      customer_category: 'GENERAL',
      min_tenure_days: 7,
      max_tenure_days: 365,
      interest_rate: 5.5,
      effective_from: new Date().toISOString().split('T')[0],
      is_active: true,
    });
    setEditingSlabId(null);
    setShowNewForm(false);
  };

  const handleEdit = (slab: FDInterestSlab) => {
    setFormData({
      customer_category: slab.customer_category,
      min_tenure_days: slab.min_tenure_days,
      max_tenure_days: slab.max_tenure_days,
      min_amount: slab.min_amount,
      max_amount: slab.max_amount,
      interest_rate: slab.interest_rate,
      effective_from: slab.effective_from,
      effective_to: slab.effective_to,
      is_active: slab.is_active,
    });
    setEditingSlabId(slab.id);
    setShowNewForm(false);
  };

  const handleSave = async () => {
    if (!productId) return;

    try {
      setSaving(true);
      if (editingSlabId) {
        await fixedDepositService.updateInterestSlab(editingSlabId, formData);
        toast({
          title: 'Success',
          description: 'Interest slab updated successfully',
        });
      } else {
        await fixedDepositService.addInterestSlab(productId, formData);
        toast({
          title: 'Success',
          description: 'Interest slab added successfully',
        });
      }
      resetForm();
      loadProduct(productId);
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to save interest slab',
        variant: 'destructive',
      });
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (slabId: string) => {
    if (!confirm('Are you sure you want to delete this interest slab?')) return;

    try {
      await fixedDepositService.deleteInterestSlab(slabId);
      toast({
        title: 'Success',
        description: 'Interest slab deleted successfully',
      });
      if (productId) {
        loadProduct(productId);
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to delete interest slab',
        variant: 'destructive',
      });
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto py-6">
        <div className="text-center py-8">Loading...</div>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-6 space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => navigate(-1)}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div className="flex-1">
          <h1 className="text-2xl font-bold">Interest Slabs</h1>
          <p className="text-muted-foreground">
            {product?.product_code} - {product?.product_name}
          </p>
        </div>
        {!showNewForm && !editingSlabId && (
          <Button onClick={() => setShowNewForm(true)}>
            <Plus className="mr-2 h-4 w-4" />
            Add Slab
          </Button>
        )}
      </div>

      {/* Form */}
      {(showNewForm || editingSlabId) && (
        <Card>
          <CardHeader>
            <CardTitle>{editingSlabId ? 'Edit Interest Slab' : 'New Interest Slab'}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label>Customer Category</Label>
                <Select
                  value={formData.customer_category}
                  onValueChange={(value: FDCustomerCategory) =>
                    setFormData({ ...formData, customer_category: value })
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {CUSTOMER_CATEGORIES.map((cat) => (
                      <SelectItem key={cat.value} value={cat.value}>
                        {cat.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Min Tenure (Days)</Label>
                <Input
                  type="number"
                  value={formData.min_tenure_days}
                  onChange={(e) =>
                    setFormData({ ...formData, min_tenure_days: parseInt(e.target.value) })
                  }
                  min={1}
                />
              </div>
              <div className="space-y-2">
                <Label>Max Tenure (Days)</Label>
                <Input
                  type="number"
                  value={formData.max_tenure_days}
                  onChange={(e) =>
                    setFormData({ ...formData, max_tenure_days: parseInt(e.target.value) })
                  }
                  min={1}
                />
              </div>
              <div className="space-y-2">
                <Label>Interest Rate (%)</Label>
                <Input
                  type="number"
                  value={formData.interest_rate}
                  onChange={(e) =>
                    setFormData({ ...formData, interest_rate: parseFloat(e.target.value) })
                  }
                  min={0}
                  max={20}
                  step="0.01"
                />
              </div>
              <div className="space-y-2">
                <Label>Effective From</Label>
                <Input
                  type="date"
                  value={formData.effective_from}
                  onChange={(e) =>
                    setFormData({ ...formData, effective_from: e.target.value })
                  }
                />
              </div>
              <div className="space-y-2">
                <Label>Effective To</Label>
                <Input
                  type="date"
                  value={formData.effective_to || ''}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      effective_to: e.target.value || undefined,
                    })
                  }
                />
              </div>
              <div className="space-y-2">
                <Label>Min Amount</Label>
                <Input
                  type="number"
                  value={formData.min_amount || ''}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      min_amount: e.target.value ? parseFloat(e.target.value) : undefined,
                    })
                  }
                  placeholder="No minimum"
                />
              </div>
              <div className="space-y-2">
                <Label>Max Amount</Label>
                <Input
                  type="number"
                  value={formData.max_amount || ''}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      max_amount: e.target.value ? parseFloat(e.target.value) : undefined,
                    })
                  }
                  placeholder="No maximum"
                />
              </div>
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={resetForm}>
                <X className="mr-2 h-4 w-4" />
                Cancel
              </Button>
              <Button onClick={handleSave} disabled={saving}>
                <Save className="mr-2 h-4 w-4" />
                {saving ? 'Saving...' : 'Save'}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Slabs Table */}
      <Card>
        <CardHeader>
          <CardTitle>Interest Rate Slabs</CardTitle>
          <CardDescription>
            Configure interest rates based on tenure and customer category
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Category</TableHead>
                <TableHead>Tenure Range</TableHead>
                <TableHead>Amount Range</TableHead>
                <TableHead>Interest Rate</TableHead>
                <TableHead>Effective Period</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {product?.interest_slabs.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} className="text-center py-8">
                    No interest slabs configured
                  </TableCell>
                </TableRow>
              ) : (
                product?.interest_slabs.map((slab) => (
                  <TableRow key={slab.id}>
                    <TableCell>
                      <Badge variant="outline">{slab.customer_category}</Badge>
                    </TableCell>
                    <TableCell>
                      {slab.min_tenure_days} - {slab.max_tenure_days} days
                    </TableCell>
                    <TableCell>
                      {slab.min_amount || slab.max_amount
                        ? `${slab.min_amount?.toLocaleString() || '0'} - ${
                            slab.max_amount?.toLocaleString() || '∞'
                          }`
                        : 'Any'}
                    </TableCell>
                    <TableCell className="font-medium">
                      {slab.interest_rate.toFixed(2)}%
                    </TableCell>
                    <TableCell>
                      {slab.effective_from}
                      {slab.effective_to && ` to ${slab.effective_to}`}
                    </TableCell>
                    <TableCell>
                      <Badge variant={slab.is_active ? 'default' : 'secondary'}>
                        {slab.is_active ? 'Active' : 'Inactive'}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-2">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleEdit(slab)}
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleDelete(slab.id)}
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
