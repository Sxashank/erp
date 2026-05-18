import { Edit, Settings } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';

import { EmptyState } from '@/components/common/EmptyState';
import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { formatCurrency } from '@/lib/utils';
import { approvalsApi, type ApprovalWorkflowResponse } from '@/services/api';

export default function ApprovalMatrixDetail() {
  const { id } = useParams();
  const [matrix, setMatrix] = useState<ApprovalWorkflowResponse | null>(null);
  const [loadFailed, setLoadFailed] = useState(false);

  useEffect(() => {
    if (!id) return;
    approvalsApi
      .getWorkflow(id)
      .then((response) => {
        setMatrix(response.data);
        setLoadFailed(false);
      })
      .catch(() => {
        setMatrix(null);
        setLoadFailed(true);
      });
  }, [id]);

  return (
    <div className="container mx-auto space-y-6 py-6">
      <PageHeader
        title={matrix?.workflowName || 'Approval Matrix Rule'}
        subtitle={matrix?.description || 'Approval rule details'}
        breadcrumbs={[
          { label: 'Approval Matrix', to: '/admin/accounting/approval-matrix' },
          { label: matrix?.workflowName || id || 'Rule' },
        ]}
        actions={
          <div className="flex gap-2">
            {id && (
              <Link to={`/admin/accounting/approval-matrix/${id}/edit`}>
                <Button variant="outline">
                  <Edit className="mr-2 h-4 w-4" />
                  Edit
                </Button>
              </Link>
            )}
            <Link to="/admin/accounting/approval-matrix">
              <Button variant="outline">Back to Rules</Button>
            </Link>
          </div>
        }
      />

      {!matrix && (
        <Card>
          <CardContent className="pt-6">
            <EmptyState
              icon={Settings}
              title={loadFailed ? 'Unable to load approval rule' : 'Loading approval rule'}
              subtitle="Approval matrix details are loaded from the core maker-checker workflow engine."
            />
          </CardContent>
        </Card>
      )}

      {matrix && (
        <>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Transaction Type
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="font-semibold">{matrix.workflowType.replace(/_/g, ' ')}</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Threshold
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="font-semibold">
                  {formatCurrency(Number(matrix.thresholdAmount))}
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Levels
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="font-semibold">{matrix.approvalLevels}</div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Status
                </CardTitle>
              </CardHeader>
              <CardContent>
                <Badge variant={matrix.isActive ? 'default' : 'secondary'}>
                  {matrix.isActive ? 'Active' : 'Inactive'}
                </Badge>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Approval Levels</CardTitle>
              <CardDescription>Server-side approver routing configuration</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Level</TableHead>
                    <TableHead>Name</TableHead>
                    <TableHead className="text-right">Threshold</TableHead>
                    <TableHead>Approver Roles</TableHead>
                    <TableHead className="text-center">Min Approvers</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {matrix.levels.map((level) => (
                    <TableRow key={level.id}>
                      <TableCell>{level.levelNumber}</TableCell>
                      <TableCell>{level.levelName}</TableCell>
                      <TableCell className="text-right">
                        {formatCurrency(Number(level.thresholdAmount || 0))}
                      </TableCell>
                      <TableCell>{level.approverRoles?.join(', ') || '-'}</TableCell>
                      <TableCell className="text-center">{level.minApprovers}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
