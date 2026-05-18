/**
 * Employee Salary List Page
 */

import { Plus, Eye, Search } from 'lucide-react';
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

import { AmountDisplay } from '@/components/common/AmountDisplay';
import { DateDisplay } from '@/components/common/DateDisplay';
import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
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
import type { EmployeeSalary } from '@/services/payrollService';
import payrollService from '@/services/payrollService';

export default function EmployeeSalaryList() {
  const navigate = useNavigate();
  const { toast } = useToast();

  const [salaries, setSalaries] = useState<EmployeeSalary[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [total, setTotal] = useState(0);

  useEffect(() => {
    loadSalaries();
  }, []);

  const loadSalaries = async () => {
    try {
      setLoading(true);
      const response = await payrollService.listEmployeeSalaries({
        active_only: true,
        limit: 100,
      });
      setSalaries(response.items);
      setTotal(response.total);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load employee salaries',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const filteredSalaries = salaries.filter((salary) => {
    if (!searchTerm) return true;
    const search = searchTerm.toLowerCase();
    return (
      salary.employee?.first_name?.toLowerCase().includes(search) ||
      salary.employee?.last_name?.toLowerCase().includes(search) ||
      salary.employee?.employee_code?.toLowerCase().includes(search)
    );
  });

  return (
    <div className="container mx-auto space-y-6 py-6">
      <PageHeader
        title="Employee Salaries"
        subtitle="View and manage employee salary assignments"
        actions={
          <Button onClick={() => navigate('/admin/payroll/employee-salary/new')}>
            <Plus className="mr-2 h-4 w-4" />
            Assign Salary
          </Button>
        }
      />

      <Card>
        <CardHeader>
          <div className="flex flex-col justify-between gap-4 md:flex-row">
            <div className="relative max-w-sm flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 transform text-muted-foreground" />
              <Input
                placeholder="Search employees..."
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
                <TableHead>Employee</TableHead>
                <TableHead>Structure</TableHead>
                <TableHead>Effective From</TableHead>
                <TableHead className="text-right">Gross Salary</TableHead>
                <TableHead className="text-right">Net Salary</TableHead>
                <TableHead className="text-right">CTC</TableHead>
                <TableHead>Revision</TableHead>
                <TableHead>Status</TableHead>
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
              ) : filteredSalaries.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={9} className="py-8 text-center">
                    No employee salaries found
                  </TableCell>
                </TableRow>
              ) : (
                filteredSalaries.map((salary) => (
                  <TableRow key={salary.id}>
                    <TableCell>
                      <div>
                        <span className="font-medium">
                          {salary.employee?.first_name} {salary.employee?.last_name}
                        </span>
                        <br />
                        <span className="text-sm text-muted-foreground">
                          {salary.employee?.employee_code}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell>{salary.structure?.structure_name || '-'}</TableCell>
                    <TableCell><DateDisplay date={salary.effective_from} /></TableCell>
                    <TableCell className="text-right">
                      <AmountDisplay amount={salary.gross_salary} compact />
                    </TableCell>
                    <TableCell className="text-right">
                      <AmountDisplay amount={salary.net_salary} compact />
                    </TableCell>
                    <TableCell className="text-right font-medium">
                      <AmountDisplay amount={salary.ctc} compact />
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">Rev {salary.revision_number}</Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant={salary.status === 'ACTIVE' ? 'default' : 'secondary'}>
                        {salary.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => navigate(`/admin/payroll/employee-salary/${salary.id}`)}
                      >
                        <Eye className="h-4 w-4" />
                      </Button>
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
