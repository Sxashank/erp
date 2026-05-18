import {
  AlertTriangle,
  Calendar,
  CheckCircle,
  Clock,
  MoreHorizontal,
  Plus,
  Search,
  Settings,
  Wrench,
} from 'lucide-react';
import { useEffect, useState } from 'react';

import { DateDisplay } from '@/components/common/DateDisplay';
import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { organizationsApi } from '@/services/api';
import type { Organization, PaginatedResponse } from '@/types';

import { logger } from "@/lib/logger";
interface MaintenanceRecord {
  id: string;
  asset_id: string;
  asset_code: string;
  asset_name: string;
  maintenance_type: 'PREVENTIVE' | 'CORRECTIVE' | 'EMERGENCY' | 'INSPECTION';
  scheduled_date: string;
  completed_date?: string;
  status: 'SCHEDULED' | 'IN_PROGRESS' | 'COMPLETED' | 'OVERDUE' | 'CANCELLED';
  priority: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  description: string;
  vendor_name?: string;
  estimated_cost: number;
  actual_cost?: number;
  next_maintenance_date?: string;
  assigned_to?: string;
}

interface AMCContract {
  id: string;
  contract_number: string;
  vendor_name: string;
  start_date: string;
  end_date: string;
  annual_cost: number;
  asset_count: number;
  status: 'ACTIVE' | 'EXPIRED' | 'EXPIRING_SOON';
  coverage_type: string;
}

const MAINTENANCE_TYPES = [
  { value: '', label: 'All Types' },
  { value: 'PREVENTIVE', label: 'Preventive' },
  { value: 'CORRECTIVE', label: 'Corrective' },
  { value: 'EMERGENCY', label: 'Emergency' },
  { value: 'INSPECTION', label: 'Inspection' },
];

const STATUSES = [
  { value: '', label: 'All Statuses' },
  { value: 'SCHEDULED', label: 'Scheduled' },
  { value: 'IN_PROGRESS', label: 'In Progress' },
  { value: 'COMPLETED', label: 'Completed' },
  { value: 'OVERDUE', label: 'Overdue' },
];

export function MaintenanceList() {
  const [maintenanceRecords, setMaintenanceRecords] = useState<MaintenanceRecord[]>([]);
  const [amcContracts, setAmcContracts] = useState<AMCContract[]>([]);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [selectedOrgId, setSelectedOrgId] = useState<string>('');
  const [selectedType, setSelectedType] = useState<string>('');
  const [selectedStatus, setSelectedStatus] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchOrganizations();
  }, []);

  useEffect(() => {
    if (selectedOrgId) {
      fetchMaintenanceRecords();
      fetchAMCContracts();
    }
  }, [selectedOrgId, selectedType, selectedStatus]);

  const fetchOrganizations = async () => {
    try {
      const response = await organizationsApi.list({ page_size: 100 });
      const data: PaginatedResponse<Organization> = response.data;
      setOrganizations(data.items);
      if (data.items.length > 0) {
        setSelectedOrgId(data.items[0].id);
      }
    } catch (error) {
      logger.error('Failed to fetch organizations:', error);
    }
  };

  const fetchMaintenanceRecords = async () => {
    try {
      setLoading(true);
      // Mock data - replace with actual API call
      const mockRecords: MaintenanceRecord[] = [
        {
          id: '1',
          asset_id: 'a1',
          asset_code: 'FA-001',
          asset_name: 'Dell Server R740',
          maintenance_type: 'PREVENTIVE',
          scheduled_date: '2024-12-15',
          status: 'SCHEDULED',
          priority: 'MEDIUM',
          description: 'Quarterly server maintenance and health check',
          vendor_name: 'Dell Support',
          estimated_cost: 15000,
          assigned_to: 'IT Team',
        },
        {
          id: '2',
          asset_id: 'a2',
          asset_code: 'FA-015',
          asset_name: 'AC Unit - Floor 2',
          maintenance_type: 'CORRECTIVE',
          scheduled_date: '2024-12-10',
          completed_date: '2024-12-10',
          status: 'COMPLETED',
          priority: 'HIGH',
          description: 'AC compressor replacement',
          vendor_name: 'Carrier India',
          estimated_cost: 45000,
          actual_cost: 48500,
        },
        {
          id: '3',
          asset_id: 'a3',
          asset_code: 'FA-022',
          asset_name: 'UPS System - DC',
          maintenance_type: 'PREVENTIVE',
          scheduled_date: '2024-12-05',
          status: 'OVERDUE',
          priority: 'CRITICAL',
          description: 'Battery replacement and testing',
          vendor_name: 'APC Support',
          estimated_cost: 120000,
        },
      ];
      setMaintenanceRecords(mockRecords);
    } catch (error) {
      logger.error('Failed to fetch maintenance records:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchAMCContracts = async () => {
    try {
      // Mock data - replace with actual API call
      const mockContracts: AMCContract[] = [
        {
          id: '1',
          contract_number: 'AMC-2024-001',
          vendor_name: 'Dell Technologies',
          start_date: '2024-01-01',
          end_date: '2024-12-31',
          annual_cost: 250000,
          asset_count: 15,
          status: 'EXPIRING_SOON',
          coverage_type: 'Comprehensive',
        },
        {
          id: '2',
          contract_number: 'AMC-2024-002',
          vendor_name: 'HP Enterprise',
          start_date: '2024-04-01',
          end_date: '2025-03-31',
          annual_cost: 180000,
          asset_count: 10,
          status: 'ACTIVE',
          coverage_type: 'Standard',
        },
      ];
      setAmcContracts(mockContracts);
    } catch (error) {
      logger.error('Failed to fetch AMC contracts:', error);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };


  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'SCHEDULED':
        return <Badge className="bg-blue-50 text-blue-700 hover:bg-blue-50">Scheduled</Badge>;
      case 'IN_PROGRESS':
        return <Badge className="bg-yellow-50 text-yellow-700 hover:bg-yellow-50">In Progress</Badge>;
      case 'COMPLETED':
        return <Badge className="bg-emerald-50 text-emerald-700 hover:bg-emerald-50">Completed</Badge>;
      case 'OVERDUE':
        return <Badge className="bg-red-50 text-red-700 hover:bg-red-50">Overdue</Badge>;
      case 'CANCELLED':
        return <Badge variant="outline">Cancelled</Badge>;
      case 'ACTIVE':
        return <Badge className="bg-emerald-50 text-emerald-700 hover:bg-emerald-50">Active</Badge>;
      case 'EXPIRED':
        return <Badge className="bg-red-50 text-red-700 hover:bg-red-50">Expired</Badge>;
      case 'EXPIRING_SOON':
        return <Badge className="bg-orange-50 text-orange-700 hover:bg-orange-50">Expiring Soon</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const getPriorityBadge = (priority: string) => {
    switch (priority) {
      case 'LOW':
        return <Badge variant="outline">Low</Badge>;
      case 'MEDIUM':
        return <Badge className="bg-blue-50 text-blue-700 hover:bg-blue-50">Medium</Badge>;
      case 'HIGH':
        return <Badge className="bg-orange-50 text-orange-700 hover:bg-orange-50">High</Badge>;
      case 'CRITICAL':
        return <Badge className="bg-red-50 text-red-700 hover:bg-red-50">Critical</Badge>;
      default:
        return <Badge variant="outline">{priority}</Badge>;
    }
  };

  const getTypeBadge = (type: string) => {
    switch (type) {
      case 'PREVENTIVE':
        return <Badge variant="outline">Preventive</Badge>;
      case 'CORRECTIVE':
        return <Badge className="bg-yellow-50 text-yellow-700 hover:bg-yellow-50">Corrective</Badge>;
      case 'EMERGENCY':
        return <Badge className="bg-red-50 text-red-700 hover:bg-red-50">Emergency</Badge>;
      case 'INSPECTION':
        return <Badge className="bg-blue-50 text-blue-700 hover:bg-blue-50">Inspection</Badge>;
      default:
        return <Badge variant="outline">{type}</Badge>;
    }
  };

  const overdueCount = maintenanceRecords.filter(r => r.status === 'OVERDUE').length;
  const scheduledCount = maintenanceRecords.filter(r => r.status === 'SCHEDULED').length;
  const completedCount = maintenanceRecords.filter(r => r.status === 'COMPLETED').length;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Asset Maintenance"
        subtitle="Manage maintenance schedules and AMC contracts"
        actions={
          <Button disabled>
            <Plus className="mr-2 h-4 w-4" />
            Maintenance Workflow Deferred
          </Button>
        }
      />

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Overdue</CardTitle>
            <AlertTriangle className="h-4 w-4 text-red-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{overdueCount}</div>
            <p className="text-xs text-slate-500">Requires immediate attention</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Scheduled</CardTitle>
            <Clock className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">{scheduledCount}</div>
            <p className="text-xs text-slate-500">Upcoming maintenance</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Completed</CardTitle>
            <CheckCircle className="h-4 w-4 text-emerald-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-emerald-600">{completedCount}</div>
            <p className="text-xs text-slate-500">This month</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active AMCs</CardTitle>
            <Settings className="h-4 w-4 text-slate-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {amcContracts.filter(c => c.status === 'ACTIVE' || c.status === 'EXPIRING_SOON').length}
            </div>
            <p className="text-xs text-slate-500">Contracts in force</p>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="maintenance" className="space-y-4">
        <TabsList>
          <TabsTrigger value="maintenance">Maintenance Schedule</TabsTrigger>
          <TabsTrigger value="amc">AMC Contracts</TabsTrigger>
        </TabsList>

        <TabsContent value="maintenance">
          <Card>
            <CardHeader>
              <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <CardTitle>Maintenance Records</CardTitle>
                <div className="flex flex-wrap items-center gap-2">
                  <div className="relative">
                    <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-slate-400" />
                    <Input
                      placeholder="Search..."
                      className="pl-8 w-[180px]"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                    />
                  </div>
                  <Select value={selectedType} onValueChange={setSelectedType}>
                    <SelectTrigger className="w-[140px]">
                      <SelectValue placeholder="All Types" />
                    </SelectTrigger>
                    <SelectContent>
                      {MAINTENANCE_TYPES.map((type) => (
                        <SelectItem key={type.value} value={type.value}>
                          {type.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Select value={selectedStatus} onValueChange={setSelectedStatus}>
                    <SelectTrigger className="w-[140px]">
                      <SelectValue placeholder="All Statuses" />
                    </SelectTrigger>
                    <SelectContent>
                      {STATUSES.map((status) => (
                        <SelectItem key={status.value} value={status.value}>
                          {status.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex items-center justify-center py-8">
                  <p className="text-sm text-slate-500">Loading...</p>
                </div>
              ) : maintenanceRecords.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-8">
                  <Wrench className="mb-4 h-12 w-12 text-slate-300" />
                  <p className="text-sm text-slate-500">No maintenance records found</p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Asset</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead>Scheduled Date</TableHead>
                      <TableHead>Priority</TableHead>
                      <TableHead>Vendor</TableHead>
                      <TableHead className="text-right">Est. Cost</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead className="w-[70px]">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {maintenanceRecords.map((record) => (
                      <TableRow key={record.id}>
                        <TableCell>
                          <div>
                            <p className="font-medium">{record.asset_code}</p>
                            <p className="text-sm text-slate-500">{record.asset_name}</p>
                          </div>
                        </TableCell>
                        <TableCell>{getTypeBadge(record.maintenance_type)}</TableCell>
                        <TableCell>
                          <div className="flex items-center gap-1">
                            <Calendar className="h-3 w-3 text-slate-400" />
                            <DateDisplay date={record.scheduled_date} />
                          </div>
                        </TableCell>
                        <TableCell>{getPriorityBadge(record.priority)}</TableCell>
                        <TableCell>{record.vendor_name || '-'}</TableCell>
                        <TableCell className="text-right">
                          {formatCurrency(record.estimated_cost)}
                        </TableCell>
                        <TableCell>{getStatusBadge(record.status)}</TableCell>
                        <TableCell>
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" size="icon">
                                <MoreHorizontal className="h-4 w-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuItem disabled>View Details</DropdownMenuItem>
                              {record.status === 'SCHEDULED' && (
                                <DropdownMenuItem>Start Maintenance</DropdownMenuItem>
                              )}
                              {record.status === 'IN_PROGRESS' && (
                                <DropdownMenuItem>Complete Maintenance</DropdownMenuItem>
                              )}
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="amc">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>AMC Contracts</CardTitle>
              <Button disabled>
                <Plus className="mr-2 h-4 w-4" />
                AMC Workflow Deferred
              </Button>
            </CardHeader>
            <CardContent>
              {amcContracts.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-8">
                  <Settings className="mb-4 h-12 w-12 text-slate-300" />
                  <p className="text-sm text-slate-500">No AMC contracts found</p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Contract No.</TableHead>
                      <TableHead>Vendor</TableHead>
                      <TableHead>Coverage</TableHead>
                      <TableHead>Period</TableHead>
                      <TableHead>Assets</TableHead>
                      <TableHead className="text-right">Annual Cost</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead className="w-[70px]">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {amcContracts.map((contract) => (
                      <TableRow key={contract.id}>
                        <TableCell className="font-medium">{contract.contract_number}</TableCell>
                        <TableCell>{contract.vendor_name}</TableCell>
                        <TableCell>{contract.coverage_type}</TableCell>
                        <TableCell>
                          <div className="text-sm">
                            <p><DateDisplay date={contract.start_date} /></p>
                            <p className="text-slate-500">to <DateDisplay date={contract.end_date} /></p>
                          </div>
                        </TableCell>
                        <TableCell>{contract.asset_count} assets</TableCell>
                        <TableCell className="text-right font-medium">
                          {formatCurrency(contract.annual_cost)}
                        </TableCell>
                        <TableCell>{getStatusBadge(contract.status)}</TableCell>
                        <TableCell>
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" size="icon">
                                <MoreHorizontal className="h-4 w-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuItem disabled>View Details</DropdownMenuItem>
                              <DropdownMenuItem>View Assets</DropdownMenuItem>
                              {contract.status === 'EXPIRING_SOON' && (
                                <DropdownMenuItem>Renew Contract</DropdownMenuItem>
                              )}
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
