/**
 * Salary Component List Page
 */

import { Plus, Edit, Trash2, Search, Filter } from 'lucide-react';
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

import { PageHeader } from '@/components/common/PageHeader';
import { PayrollConfirmDialog } from '@/components/payroll/PayrollConfirmDialog';
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
import { useToast } from '@/hooks/use-toast';
import { useRequiredActiveOrganizationId } from '@/hooks/useOrganization';
import type { SalaryComponent } from '@/services/payrollService';
import payrollService from '@/services/payrollService';

const COMPONENT_TYPES = ['EARNING', 'DEDUCTION'];
const CATEGORIES = ['BASIC', 'ALLOWANCE', 'REIMBURSEMENT', 'BONUS', 'STATUTORY', 'OTHER'];

export default function SalaryComponentList() {
  const navigate = useNavigate();
  const { toast } = useToast();

  const [components, setComponents] = useState<SalaryComponent[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [typeFilter, setTypeFilter] = useState<string>('');
  const [categoryFilter, setCategoryFilter] = useState<string>('');
  const [total, setTotal] = useState(0);
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);

  const organizationId = useRequiredActiveOrganizationId();

  useEffect(() => {
    loadComponents();
  }, [typeFilter, categoryFilter]);

  const loadComponents = async () => {
    try {
      setLoading(true);
      const response = await payrollService.listComponents({
        componentType: typeFilter || undefined,
        category: categoryFilter || undefined,
        activeOnly: true,
      });
      setComponents(response.items);
      setTotal(response.total);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load salary components',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteId) return;
    try {
      setDeleting(true);
      await payrollService.deleteComponent(deleteId);
      toast({
        title: 'Success',
        description: 'Component deactivated successfully',
      });
      setDeleteId(null);
      await loadComponents();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to deactivate component',
        variant: 'destructive',
      });
    } finally {
      setDeleting(false);
    }
  };

  const filteredComponents = components.filter(
    (comp) =>
      comp.componentName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      comp.componentCode.toLowerCase().includes(searchTerm.toLowerCase()),
  );

  return (
    <div className="container mx-auto space-y-6 py-6">
      <PageHeader
        title="Salary Components"
        subtitle="Manage earnings and deductions for payroll"
        actions={
          <Button onClick={() => navigate('/admin/payroll/components/new')}>
            <Plus className="mr-2 h-4 w-4" />
            Add Component
          </Button>
        }
      />

      <Card>
        <CardHeader>
          <div className="flex flex-col justify-between gap-4 md:flex-row">
            <div className="relative max-w-sm flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 transform text-muted-foreground" />
              <Input
                placeholder="Search components..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            <div className="flex gap-2">
              {/* Radix `<Select.Item>` forbids empty-string value; use a
                  `__all__` sentinel and map it to "" in the handler. */}
              <Select
                value={typeFilter || '__all__'}
                onValueChange={(v) => setTypeFilter(v === '__all__' ? '' : v)}
              >
                <SelectTrigger className="w-[150px]">
                  <SelectValue placeholder="All Types" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="__all__">All Types</SelectItem>
                  {COMPONENT_TYPES.map((type) => (
                    <SelectItem key={type} value={type}>
                      {type}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Select
                value={categoryFilter || '__all__'}
                onValueChange={(v) => setCategoryFilter(v === '__all__' ? '' : v)}
              >
                <SelectTrigger className="w-[150px]">
                  <SelectValue placeholder="All Categories" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="__all__">All Categories</SelectItem>
                  {CATEGORIES.map((cat) => (
                    <SelectItem key={cat} value={cat}>
                      {cat}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Code</TableHead>
                <TableHead>Name</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Category</TableHead>
                <TableHead>Calculation</TableHead>
                <TableHead>Tax</TableHead>
                <TableHead>PF</TableHead>
                <TableHead>ESI</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={9} className="py-8 text-center">
                    Loading...
                  </TableCell>
                </TableRow>
              ) : filteredComponents.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={9} className="py-8 text-center">
                    No components found
                  </TableCell>
                </TableRow>
              ) : (
                filteredComponents.map((component) => (
                  <TableRow key={component.id}>
                    <TableCell className="font-mono">{component.componentCode}</TableCell>
                    <TableCell className="font-medium">{component.componentName}</TableCell>
                    <TableCell>
                      <Badge
                        variant={component.componentType === 'EARNING' ? 'default' : 'secondary'}
                      >
                        {component.componentType}
                      </Badge>
                    </TableCell>
                    <TableCell>{component.category}</TableCell>
                    <TableCell>
                      {component.calculationType}
                      {component.calculationType === 'PERCENTAGE' &&
                        component.percentageValue && (
                          <span className="ml-1 text-muted-foreground">
                            ({component.percentageValue}%)
                          </span>
                        )}
                    </TableCell>
                    <TableCell>
                      <Badge variant={component.isTaxable ? 'destructive' : 'outline'}>
                        {component.isTaxable ? 'Yes' : 'No'}
                      </Badge>
                    </TableCell>
                    <TableCell>{component.affectsPf ? 'Yes' : 'No'}</TableCell>
                    <TableCell>{component.affectsEsi ? 'Yes' : 'No'}</TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-2">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => navigate(`/admin/payroll/components/${component.id}/edit`)}
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => setDeleteId(component.id)}
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

      <PayrollConfirmDialog
        open={Boolean(deleteId)}
        title="Deactivate salary component?"
        description="This removes the component from active payroll configuration lists. Existing payroll history is not changed."
        confirmLabel="Deactivate"
        destructive
        busy={deleting}
        onOpenChange={(open) => {
          if (!open && !deleting) setDeleteId(null);
        }}
        onConfirm={handleDelete}
      />
    </div>
  );
}
