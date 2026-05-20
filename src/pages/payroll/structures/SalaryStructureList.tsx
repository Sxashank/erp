/**
 * Salary Structure List Page
 */

import { Plus, Edit, Eye, Trash2, Search } from 'lucide-react';
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

import { AmountDisplay } from '@/components/common/AmountDisplay';
import { PageHeader } from '@/components/common/PageHeader';
import { PayrollConfirmDialog } from '@/components/payroll/PayrollConfirmDialog';
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
import type { SalaryStructure } from '@/services/payrollService';
import payrollService from '@/services/payrollService';

export default function SalaryStructureList() {
  const navigate = useNavigate();
  const { toast } = useToast();

  const [structures, setStructures] = useState<SalaryStructure[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [total, setTotal] = useState(0);
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);

  const organizationId = useRequiredActiveOrganizationId();

  useEffect(() => {
    loadStructures();
  }, []);

  const loadStructures = async () => {
    try {
      setLoading(true);
      const response = await payrollService.listStructures({
        activeOnly: true,
      });
      setStructures(response.items);
      setTotal(response.total);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load salary structures',
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
      await payrollService.deleteStructure(deleteId);
      toast({
        title: 'Success',
        description: 'Structure deactivated successfully',
      });
      setDeleteId(null);
      await loadStructures();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to deactivate structure',
        variant: 'destructive',
      });
    } finally {
      setDeleting(false);
    }
  };

  const filteredStructures = structures.filter(
    (s) =>
      s.structureName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.structureCode.toLowerCase().includes(searchTerm.toLowerCase()),
  );

  return (
    <div className="container mx-auto space-y-6 py-6">
      <PageHeader
        title="Salary Structures"
        subtitle="Define salary templates with component breakdowns"
        actions={
          <Button onClick={() => navigate('/admin/payroll/structures/new')}>
            <Plus className="mr-2 h-4 w-4" />
            Add Structure
          </Button>
        }
      />

      <Card>
        <CardHeader>
          <div className="flex flex-col justify-between gap-4 md:flex-row">
            <div className="relative max-w-sm flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 transform text-muted-foreground" />
              <Input
                placeholder="Search structures..."
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
                <TableHead>CTC Range</TableHead>
                <TableHead>Components</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={6} className="py-8 text-center">
                    Loading...
                  </TableCell>
                </TableRow>
              ) : filteredStructures.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="py-8 text-center">
                    No structures found
                  </TableCell>
                </TableRow>
              ) : (
                filteredStructures.map((structure) => (
                  <TableRow key={structure.id}>
                    <TableCell className="font-mono">{structure.structureCode}</TableCell>
                    <TableCell className="font-medium">{structure.structureName}</TableCell>
                    <TableCell>
                      {structure.ctcFrom && structure.ctcTo ? (
                        <>
                          <AmountDisplay amount={structure.ctcFrom} compact /> -{' '}
                          <AmountDisplay amount={structure.ctcTo} compact />
                        </>
                      ) : (
                        <span className="text-muted-foreground">Not specified</span>
                      )}
                    </TableCell>
                    <TableCell>{structure.components?.length || 0} components</TableCell>
                    <TableCell>
                      <Badge variant={structure.isActive ? 'default' : 'secondary'}>
                        {structure.isActive ? 'Active' : 'Inactive'}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-2">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => navigate(`/admin/payroll/structures/${structure.id}`)}
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => navigate(`/admin/payroll/structures/${structure.id}/edit`)}
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => setDeleteId(structure.id)}
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
        title="Deactivate salary structure?"
        description="This removes the salary structure from active assignment lists. Existing employee salary history is not changed."
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
