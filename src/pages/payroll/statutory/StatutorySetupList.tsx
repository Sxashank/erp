/**
 * Statutory Setup List Page
 */

import { Plus, Edit, Settings } from 'lucide-react';
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

import { DateDisplay } from '@/components/common/DateDisplay';
import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
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
import type { StatutorySetup } from '@/services/payrollService';
import payrollService from '@/services/payrollService';

const STATUTORY_TYPES = {
  PF: { label: 'Provident Fund (PF)', description: 'Employee & Employer contribution to PF' },
  ESI: { label: 'Employee State Insurance (ESI)', description: 'Health insurance scheme' },
  PT: { label: 'Professional Tax (PT)', description: 'State-level professional tax' },
  LWF: { label: 'Labour Welfare Fund (LWF)', description: 'Labour welfare contribution' },
  GRATUITY: { label: 'Gratuity', description: 'Gratuity provision' },
};

export default function StatutorySetupList() {
  const navigate = useNavigate();
  const { toast } = useToast();

  const [setups, setSetups] = useState<StatutorySetup[]>([]);
  const [loading, setLoading] = useState(true);

  const organizationId = useRequiredActiveOrganizationId();

  useEffect(() => {
    loadSetups();
  }, []);

  const loadSetups = async () => {
    try {
      setLoading(true);
      const data = await payrollService.listStatutorySetup({
        organization_id: organizationId,
      });
      setSetups(data);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load statutory setup',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const getSetupByType = (type: string) => {
    return setups.find((s) => s.statutory_type === type);
  };

  return (
    <div className="container mx-auto space-y-6 py-6">
      <PageHeader
        title="Statutory Setup"
        subtitle="Configure statutory compliance for payroll"
        breadcrumbs={[{ label: 'Payroll', to: '/admin/payroll' }, { label: 'Statutory Setup' }]}
      />

      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        {Object.entries(STATUTORY_TYPES).map(([type, info]) => {
          const setup = getSetupByType(type);
          return (
            <Card key={type}>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle className="text-lg">{info.label}</CardTitle>
                    <CardDescription>{info.description}</CardDescription>
                  </div>
                  {setup ? (
                    <Badge variant={setup.is_applicable ? 'default' : 'secondary'}>
                      {setup.is_applicable ? 'Active' : 'Inactive'}
                    </Badge>
                  ) : (
                    <Badge variant="outline">Not Configured</Badge>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                {setup ? (
                  <div className="space-y-3">
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      {setup.employer_contribution_pct !== undefined &&
                        setup.employer_contribution_pct !== null && (
                          <div>
                            <span className="text-muted-foreground">Employer Rate:</span>
                            <p className="font-medium">{setup.employer_contribution_pct}%</p>
                          </div>
                        )}
                      {setup.employee_contribution_pct !== undefined &&
                        setup.employee_contribution_pct !== null && (
                          <div>
                            <span className="text-muted-foreground">Employee Rate:</span>
                            <p className="font-medium">{setup.employee_contribution_pct}%</p>
                          </div>
                        )}
                      {setup.wage_ceiling !== undefined && setup.wage_ceiling !== null && (
                        <div>
                          <span className="text-muted-foreground">Wage Ceiling:</span>
                          <p className="font-medium">₹{setup.wage_ceiling.toLocaleString()}</p>
                        </div>
                      )}
                      {setup.admin_charges_pct !== undefined &&
                        setup.admin_charges_pct !== null && (
                          <div>
                            <span className="text-muted-foreground">Admin Charges:</span>
                            <p className="font-medium">{setup.admin_charges_pct}%</p>
                          </div>
                        )}
                    </div>
                    <div className="text-sm text-muted-foreground">
                      Effective from: <DateDisplay date={setup.effective_from} />
                    </div>
                    <Button
                      variant="outline"
                      className="w-full"
                      onClick={() => navigate(`/admin/payroll/statutory/${setup.id}/edit`)}
                    >
                      <Edit className="mr-2 h-4 w-4" />
                      Edit Configuration
                    </Button>
                  </div>
                ) : (
                  <div className="py-4 text-center">
                    <Settings className="mx-auto mb-2 h-8 w-8 text-muted-foreground" />
                    <p className="mb-4 text-sm text-muted-foreground">Not yet configured</p>
                    <Button
                      variant="outline"
                      onClick={() => navigate(`/admin/payroll/statutory/new?type=${type}`)}
                    >
                      <Plus className="mr-2 h-4 w-4" />
                      Configure {info.label}
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>All Configurations</CardTitle>
          <CardDescription>Historical view of all statutory configurations</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Type</TableHead>
                <TableHead>Employee %</TableHead>
                <TableHead>Employer %</TableHead>
                <TableHead>Wage Ceiling</TableHead>
                <TableHead>Effective From</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={7} className="py-8 text-center">
                    Loading...
                  </TableCell>
                </TableRow>
              ) : setups.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} className="py-8 text-center">
                    No statutory configurations found
                  </TableCell>
                </TableRow>
              ) : (
                setups.map((setup) => (
                  <TableRow key={setup.id}>
                    <TableCell className="font-medium">
                      {STATUTORY_TYPES[setup.statutory_type as keyof typeof STATUTORY_TYPES]
                        ?.label || setup.statutory_type}
                    </TableCell>
                    <TableCell>
                      {setup.employee_contribution_pct !== null
                        ? `${setup.employee_contribution_pct}%`
                        : '-'}
                    </TableCell>
                    <TableCell>
                      {setup.employer_contribution_pct !== null
                        ? `${setup.employer_contribution_pct}%`
                        : '-'}
                    </TableCell>
                    <TableCell>
                      {setup.wage_ceiling != null ? `₹${setup.wage_ceiling.toLocaleString()}` : '-'}
                    </TableCell>
                    <TableCell><DateDisplay date={setup.effective_from} /></TableCell>
                    <TableCell>
                      <Badge variant={setup.is_applicable ? 'default' : 'secondary'}>
                        {setup.is_applicable ? 'Active' : 'Inactive'}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => navigate(`/admin/payroll/statutory/${setup.id}/edit`)}
                      >
                        <Edit className="h-4 w-4" />
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
