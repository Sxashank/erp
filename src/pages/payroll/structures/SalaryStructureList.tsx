/**
 * Salary Structure List Page
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Edit, Eye, Trash2, Search } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { PageHeader } from '@/components/common/PageHeader';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useToast } from '@/hooks/use-toast';
import { AmountDisplay } from '@/components/common/AmountDisplay';
import payrollService, { SalaryStructure } from '@/services/payrollService';
import { useRequiredActiveOrganizationId } from '@/hooks/useOrganization';

export default function SalaryStructureList() {
  const navigate = useNavigate();
  const { toast } = useToast();

  const [structures, setStructures] = useState<SalaryStructure[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [total, setTotal] = useState(0);

  const organizationId = useRequiredActiveOrganizationId();

  useEffect(() => {
    loadStructures();
  }, []);

  const loadStructures = async () => {
    try {
      setLoading(true);
      const response = await payrollService.listStructures({
        organization_id: organizationId,
        active_only: true,
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

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to deactivate this structure?')) return;

    try {
      await payrollService.deleteStructure(id);
      toast({
        title: 'Success',
        description: 'Structure deactivated successfully',
      });
      loadStructures();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to deactivate structure',
        variant: 'destructive',
      });
    }
  };

  const filteredStructures = structures.filter(
    (s) =>
      s.structure_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.structure_code.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="container mx-auto py-6 space-y-6">
      <PageHeader
        title="Salary Structures"
        subtitle="Define salary templates with component breakdowns"
        actions={
          <Button onClick={() => navigate('/payroll/structures/new')}>
            <Plus className="mr-2 h-4 w-4" />
            Add Structure
          </Button>
        }
      />

      <Card>
        <CardHeader>
          <div className="flex flex-col md:flex-row gap-4 justify-between">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
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
                  <TableCell colSpan={6} className="text-center py-8">
                    Loading...
                  </TableCell>
                </TableRow>
              ) : filteredStructures.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center py-8">
                    No structures found
                  </TableCell>
                </TableRow>
              ) : (
                filteredStructures.map((structure) => (
                  <TableRow key={structure.id}>
                    <TableCell className="font-mono">
                      {structure.structure_code}
                    </TableCell>
                    <TableCell className="font-medium">
                      {structure.structure_name}
                    </TableCell>
                    <TableCell>
                      {structure.ctc_from && structure.ctc_to ? (
                        <>
                          <AmountDisplay amount={structure.ctc_from} compact /> -{' '}
                          <AmountDisplay amount={structure.ctc_to} compact />
                        </>
                      ) : (
                        <span className="text-muted-foreground">Not specified</span>
                      )}
                    </TableCell>
                    <TableCell>
                      {structure.components?.length || 0} components
                    </TableCell>
                    <TableCell>
                      <Badge variant={structure.is_active ? 'default' : 'secondary'}>
                        {structure.is_active ? 'Active' : 'Inactive'}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-2">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() =>
                            navigate(`/payroll/structures/${structure.id}`)
                          }
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() =>
                            navigate(`/payroll/structures/${structure.id}/edit`)
                          }
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleDelete(structure.id)}
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
