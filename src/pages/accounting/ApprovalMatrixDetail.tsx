import { useState } from 'react';
import { Link, useParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { PageHeader } from '@/components/common/PageHeader';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  ArrowLeft,
  Shield,
  Edit,
  CheckCircle,
  XCircle,
  Clock,
  User,
  Calendar,
  BarChart3,
  AlertTriangle,
  History,
} from 'lucide-react';

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(value);
};

// Mock matrix detail
const matrixDetail = {
  id: '1',
  name: 'GL Posting Approval',
  description: 'Approval workflow for GL postings based on transaction amount',
  transactionType: 'GL_POSTING',
  transactionTypeName: 'GL Posting',
  isActive: true,
  createdBy: 'Admin',
  createdAt: '2024-10-01 10:00:00',
  updatedBy: 'Finance Manager',
  updatedAt: '2024-12-15 14:30:00',
  levels: [
    {
      level: 1,
      roleId: 'ROLE001',
      roleName: 'Branch Manager',
      minAmount: 0,
      maxAmount: 100000,
      isOptional: false,
    },
    {
      level: 2,
      roleId: 'ROLE003',
      roleName: 'Finance Manager',
      minAmount: 100000,
      maxAmount: 500000,
      isOptional: false,
    },
    {
      level: 3,
      roleId: 'ROLE004',
      roleName: 'CFO',
      minAmount: 500000,
      maxAmount: 5000000,
      isOptional: false,
    },
    {
      level: 4,
      roleId: 'ROLE005',
      roleName: 'CEO',
      minAmount: 5000000,
      maxAmount: 999999999,
      isOptional: false,
    },
  ],
  statistics: {
    totalApprovals: 245,
    approvedCount: 220,
    rejectedCount: 15,
    pendingCount: 10,
    avgApprovalTime: '4.2 hours',
  },
  recentActivity: [
    { action: 'APPROVED', postingId: 'GLP2025010001', amount: 1250000, by: 'CFO', at: '2025-01-15 14:00:00' },
    { action: 'APPROVED', postingId: 'GLP2025010002', amount: 75000, by: 'Branch Manager', at: '2025-01-14 16:30:00' },
    { action: 'REJECTED', postingId: 'GLP2025010003', amount: 250000, by: 'Finance Manager', at: '2025-01-14 11:00:00' },
    { action: 'APPROVED', postingId: 'GLP2025010004', amount: 450000, by: 'Finance Manager', at: '2025-01-13 15:45:00' },
    { action: 'APPROVED', postingId: 'GLP2025010005', amount: 6500000, by: 'CEO', at: '2025-01-12 10:30:00' },
  ],
};

export default function ApprovalMatrixDetail() {
  const { id } = useParams();
  const navigate = useNavigate();

  const getStatusBadge = (action: string) => {
    switch (action) {
      case 'APPROVED':
        return <Badge variant="default" className="bg-green-100 text-green-800"><CheckCircle className="h-3 w-3 mr-1" />Approved</Badge>;
      case 'REJECTED':
        return <Badge variant="destructive"><XCircle className="h-3 w-3 mr-1" />Rejected</Badge>;
      case 'PENDING':
        return <Badge variant="secondary"><Clock className="h-3 w-3 mr-1" />Pending</Badge>;
      default:
        return <Badge variant="outline">{action}</Badge>;
    }
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
      <PageHeader
        title={matrixDetail.name}
        subtitle={matrixDetail.description}
        breadcrumbs={[
          { label: 'Approval Matrix', to: '/admin/accounting/approval-matrix' },
          { label: matrixDetail.name },
        ]}
        actions={
          <div className="flex items-center gap-2">
            <Badge
              variant={matrixDetail.isActive ? 'default' : 'secondary'}
              className={matrixDetail.isActive ? 'bg-green-100 text-green-800' : ''}
            >
              {matrixDetail.isActive ? 'Active' : 'Inactive'}
            </Badge>
            <Link to={`/admin/accounting/approval-matrix/${id}/edit`}>
              <Button variant="outline">
                <Edit className="h-4 w-4 mr-2" />
                Edit
              </Button>
            </Link>
          </div>
        }
      />

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Total Approvals</div>
            <div className="text-2xl font-bold mt-1">{matrixDetail.statistics.totalApprovals}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <CheckCircle className="h-4 w-4 text-green-500" />
              Approved
            </div>
            <div className="text-2xl font-bold mt-1 text-green-600">{matrixDetail.statistics.approvedCount}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <XCircle className="h-4 w-4 text-red-500" />
              Rejected
            </div>
            <div className="text-2xl font-bold mt-1 text-red-600">{matrixDetail.statistics.rejectedCount}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Clock className="h-4 w-4 text-yellow-500" />
              Pending
            </div>
            <div className="text-2xl font-bold mt-1 text-yellow-600">{matrixDetail.statistics.pendingCount}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="text-sm text-muted-foreground">Avg. Approval Time</div>
            <div className="text-2xl font-bold mt-1">{matrixDetail.statistics.avgApprovalTime}</div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Approval Levels */}
          <Card>
            <CardHeader>
              <CardTitle>Approval Levels</CardTitle>
              <CardDescription>Hierarchy of approval based on transaction amount</CardDescription>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[80px]">Level</TableHead>
                    <TableHead>Approving Role</TableHead>
                    <TableHead>Amount Range</TableHead>
                    <TableHead className="text-center">Optional</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {matrixDetail.levels.map((level) => (
                    <TableRow key={level.level}>
                      <TableCell>
                        <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center font-bold text-primary">
                          {level.level}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="font-medium">{level.roleName}</div>
                      </TableCell>
                      <TableCell>
                        <div className="text-sm">
                          {formatCurrency(level.minAmount)} - {level.maxAmount === 999999999 ? 'No Limit' : formatCurrency(level.maxAmount)}
                        </div>
                      </TableCell>
                      <TableCell className="text-center">
                        {level.isOptional ? (
                          <Badge variant="outline">Optional</Badge>
                        ) : (
                          <Badge variant="secondary">Required</Badge>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

              {/* Visual Flow */}
              <div className="mt-6 p-4 bg-muted rounded-lg">
                <h4 className="font-medium mb-3">Approval Flow</h4>
                <div className="flex items-center flex-wrap gap-2">
                  {matrixDetail.levels.map((level, index) => (
                    <div key={level.level} className="flex items-center gap-2">
                      <div className="bg-background border rounded-lg p-3 text-center min-w-[140px]">
                        <div className="h-6 w-6 rounded-full bg-primary text-white flex items-center justify-center text-xs mx-auto mb-1">
                          {level.level}
                        </div>
                        <div className="font-medium text-sm">{level.roleName}</div>
                        <div className="text-xs text-muted-foreground mt-1">
                          {formatCurrency(level.minAmount)} - {level.maxAmount === 999999999 ? '∞' : formatCurrency(level.maxAmount)}
                        </div>
                      </div>
                      {index < matrixDetail.levels.length - 1 && (
                        <div className="text-muted-foreground text-xl">→</div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Recent Activity */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <History className="h-5 w-5" />
                Recent Activity
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Posting ID</TableHead>
                    <TableHead>Amount</TableHead>
                    <TableHead>Approved By</TableHead>
                    <TableHead>Date & Time</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {matrixDetail.recentActivity.map((activity, index) => (
                    <TableRow key={index}>
                      <TableCell>
                        <Link to={`/admin/accounting/gl-postings/${activity.postingId}`} className="font-mono text-sm text-primary hover:underline">
                          {activity.postingId}
                        </Link>
                      </TableCell>
                      <TableCell className="font-medium">{formatCurrency(activity.amount)}</TableCell>
                      <TableCell>{activity.by}</TableCell>
                      <TableCell className="text-sm text-muted-foreground">{activity.at}</TableCell>
                      <TableCell>{getStatusBadge(activity.action)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Details */}
          <Card>
            <CardHeader>
              <CardTitle>Matrix Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 text-sm">
              <div>
                <p className="text-muted-foreground">Transaction Type</p>
                <Badge variant="outline" className="mt-1">{matrixDetail.transactionTypeName}</Badge>
              </div>
              <div>
                <p className="text-muted-foreground">Status</p>
                <Badge variant={matrixDetail.isActive ? 'default' : 'secondary'} className={`mt-1 ${matrixDetail.isActive ? 'bg-green-100 text-green-800' : ''}`}>
                  {matrixDetail.isActive ? 'Active' : 'Inactive'}
                </Badge>
              </div>
              <div>
                <p className="text-muted-foreground">Levels</p>
                <p className="font-medium">{matrixDetail.levels.length}</p>
              </div>
            </CardContent>
          </Card>

          {/* Audit Information */}
          <Card>
            <CardHeader>
              <CardTitle>Audit Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 text-sm">
              <div className="flex items-center gap-2">
                <User className="h-4 w-4 text-muted-foreground" />
                <div>
                  <p className="text-muted-foreground">Created By</p>
                  <p className="font-medium">{matrixDetail.createdBy}</p>
                  <p className="text-xs text-muted-foreground">{matrixDetail.createdAt}</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Calendar className="h-4 w-4 text-muted-foreground" />
                <div>
                  <p className="text-muted-foreground">Last Updated By</p>
                  <p className="font-medium">{matrixDetail.updatedBy}</p>
                  <p className="text-xs text-muted-foreground">{matrixDetail.updatedAt}</p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Quick Stats */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5" />
                Approval Rate
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-center">
                <div className="text-4xl font-bold text-green-600">
                  {Math.round((matrixDetail.statistics.approvedCount / matrixDetail.statistics.totalApprovals) * 100)}%
                </div>
                <p className="text-sm text-muted-foreground mt-1">Approval Rate</p>
              </div>
              <div className="mt-4 space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Approved</span>
                  <span className="font-medium">{matrixDetail.statistics.approvedCount}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Rejected</span>
                  <span className="font-medium">{matrixDetail.statistics.rejectedCount}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Pending</span>
                  <span className="font-medium">{matrixDetail.statistics.pendingCount}</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Actions */}
          <Card>
            <CardHeader>
              <CardTitle>Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Link to={`/admin/accounting/approval-matrix/${id}/edit`} className="block">
                <Button variant="outline" className="w-full">
                  <Edit className="h-4 w-4 mr-2" />
                  Edit Matrix
                </Button>
              </Link>
              <Link to="/admin/accounting/pending-approvals" className="block">
                <Button variant="outline" className="w-full">
                  <Clock className="h-4 w-4 mr-2" />
                  View Pending Approvals
                </Button>
              </Link>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
