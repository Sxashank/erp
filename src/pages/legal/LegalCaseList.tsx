/**
 * Legal Case List Page
 * View and manage all legal cases
 */

import {
  Briefcase,
  Plus,
  Search,
  Loader2,
  Calendar,
  IndianRupee,
  ChevronRight,
  Scale,
  Filter,
} from 'lucide-react';
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

import { DateDisplay } from '@/components/common/DateDisplay';
import { PageHeader } from '@/components/common/PageHeader';
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { legalCaseApi } from '@/services/legalApi';
import type { LegalCase } from '@/types/legal';

import { logger } from "@/lib/logger";
const forumTypes = [
  { value: 'DRT', label: 'DRT' },
  { value: 'DRAT', label: 'DRAT' },
  { value: 'NCLT', label: 'NCLT' },
  { value: 'CIVIL_COURT', label: 'Civil Court' },
  { value: 'HIGH_COURT', label: 'High Court' },
  { value: 'ARBITRATION', label: 'Arbitration' },
  { value: 'LOK_ADALAT', label: 'Lok Adalat' },
];

const caseTypes = [
  { value: 'SARFAESI', label: 'SARFAESI' },
  { value: 'DRT_APPLICATION', label: 'DRT Application' },
  { value: 'DRT_APPEAL', label: 'DRT Appeal' },
  { value: 'RECOVERY_SUIT', label: 'Recovery Suit' },
  { value: 'EXECUTION_PETITION', label: 'Execution Petition' },
  { value: 'IBC', label: 'IBC' },
  { value: 'SECTION_138', label: 'Section 138 NI Act' },
];

const forumColors: Record<string, string> = {
  DRT: 'bg-blue-100 text-blue-700',
  DRAT: 'bg-indigo-100 text-indigo-700',
  NCLT: 'bg-purple-100 text-purple-700',
  CIVIL_COURT: 'bg-green-100 text-green-700',
  HIGH_COURT: 'bg-orange-100 text-orange-700',
  ARBITRATION: 'bg-yellow-100 text-yellow-700',
  LOK_ADALAT: 'bg-teal-100 text-teal-700',
};

export default function LegalCaseList() {
  const [loading, setLoading] = useState(true);
  const [cases, setCases] = useState<LegalCase[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterForum, setFilterForum] = useState('all');
  const [filterType, setFilterType] = useState('all');
  const [activeTab, setActiveTab] = useState('all');

  useEffect(() => {
    fetchCases();
  }, [searchQuery, filterForum, filterType]);

  const fetchCases = async () => {
    try {
      const response = await legalCaseApi.getList({
        forum_type: filterForum !== 'all' ? filterForum : undefined,
        case_type: filterType !== 'all' ? filterType : undefined,
      });
      const body = response.data as LegalCase[] | { items?: LegalCase[] } | undefined;
      setCases(Array.isArray(body) ? body : (body?.items ?? []));
    } catch (error) {
      logger.error('Failed to fetch cases:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const filteredCases = cases.filter((c) => {
    const matchesSearch =
      !searchQuery ||
      c.case_number.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.borrower_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.loan_account_number.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesTab =
      activeTab === 'all' ||
      (activeTab === 'active' && c.is_active) ||
      (activeTab === 'sarfaesi' && c.case_type === 'SARFAESI');

    return matchesSearch && matchesTab;
  });

  const stats = {
    total: cases.length,
    active: cases.filter((c) => c.is_active).length,
    sarfaesi: cases.filter((c) => c.case_type === 'SARFAESI').length,
    hearingDue: cases.filter(
      (c) =>
        c.next_hearing_date &&
        new Date(c.next_hearing_date) <= new Date(Date.now() + 7 * 24 * 60 * 60 * 1000),
    ).length,
  };

  if (loading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Legal Cases"
        subtitle="Manage all legal cases and proceedings"
        actions={
          <Link to="/admin/legal/cases/new">
            <Button>
              <Plus className="mr-2 h-4 w-4" />
              New Case
            </Button>
          </Link>
        }
      />

      {/* Stats Cards */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-blue-100 p-2">
                <Briefcase className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Total Cases</p>
                <p className="text-xl font-bold">{stats.total}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-green-100 p-2">
                <Scale className="h-5 w-5 text-green-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Active Cases</p>
                <p className="text-xl font-bold">{stats.active}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-purple-100 p-2">
                <Briefcase className="h-5 w-5 text-purple-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">SARFAESI</p>
                <p className="text-xl font-bold">{stats.sarfaesi}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-yellow-100 p-2">
                <Calendar className="h-5 w-5 text-yellow-600" />
              </div>
              <div>
                <p className="text-sm text-gray-500">Hearings This Week</p>
                <p className="text-xl font-bold">{stats.hearingDue}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col gap-4 md:flex-row">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
              <Input
                placeholder="Search by case number, borrower, or loan account..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
            <Select value={filterForum} onValueChange={setFilterForum}>
              <SelectTrigger className="w-[150px]">
                <SelectValue placeholder="Forum" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Forums</SelectItem>
                {forumTypes.map((forum) => (
                  <SelectItem key={forum.value} value={forum.value}>
                    {forum.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={filterType} onValueChange={setFilterType}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Case Type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                {caseTypes.map((type) => (
                  <SelectItem key={type.value} value={type.value}>
                    {type.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Cases Table with Tabs */}
      <Card>
        <CardHeader>
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList>
              <TabsTrigger value="all">All Cases</TabsTrigger>
              <TabsTrigger value="active">Active</TabsTrigger>
              <TabsTrigger value="sarfaesi">SARFAESI</TabsTrigger>
            </TabsList>
          </Tabs>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Case Number</TableHead>
                <TableHead>Borrower</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Forum</TableHead>
                <TableHead className="text-right">Claim Amount</TableHead>
                <TableHead>Next Hearing</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="w-[50px]"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredCases.map((legalCase) => (
                <TableRow key={legalCase.id}>
                  <TableCell>
                    <Link
                      to={`/admin/legal/cases/${legalCase.id}`}
                      className="font-medium text-blue-600 hover:underline"
                    >
                      {legalCase.case_number}
                    </Link>
                    <p className="text-sm text-gray-500">{legalCase.loan_account_number}</p>
                  </TableCell>
                  <TableCell>{legalCase.borrower_name}</TableCell>
                  <TableCell>
                    <Badge variant="secondary">{legalCase.case_type.replace(/_/g, ' ')}</Badge>
                  </TableCell>
                  <TableCell>
                    <Badge className={forumColors[legalCase.forum_type] || 'bg-gray-100'}>
                      {legalCase.forum_type}
                    </Badge>
                    {legalCase.court_name && (
                      <p className="mt-1 text-xs text-gray-500">{legalCase.court_name}</p>
                    )}
                  </TableCell>
                  <TableCell className="text-right">
                    {formatCurrency(legalCase.claim_amount)}
                  </TableCell>
                  <TableCell>
                    {legalCase.next_hearing_date ? (
                      <div className="flex items-center gap-1">
                        <Calendar className="h-4 w-4 text-gray-400" />
                        <DateDisplay date={legalCase.next_hearing_date} />
                      </div>
                    ) : (
                      '-'
                    )}
                  </TableCell>
                  <TableCell>
                    <Badge
                      className={
                        legalCase.is_active
                          ? 'bg-green-100 text-green-700'
                          : 'bg-gray-100 text-gray-700'
                      }
                    >
                      {legalCase.current_status || (legalCase.is_active ? 'Active' : 'Closed')}
                    </Badge>
                    {legalCase.sarfaesi_stage && (
                      <p className="mt-1 text-xs text-gray-500">
                        {legalCase.sarfaesi_stage.replace(/_/g, ' ')}
                      </p>
                    )}
                  </TableCell>
                  <TableCell>
                    <Link to={`/admin/legal/cases/${legalCase.id}`}>
                      <Button variant="ghost" size="icon">
                        <ChevronRight className="h-4 w-4" />
                      </Button>
                    </Link>
                  </TableCell>
                </TableRow>
              ))}
              {filteredCases.length === 0 && (
                <TableRow>
                  <TableCell colSpan={8} className="py-8 text-center text-gray-500">
                    <Briefcase className="mx-auto mb-4 h-12 w-12 opacity-50" />
                    <p>No cases found</p>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
