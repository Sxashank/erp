import { format, subMonths } from 'date-fns';
import {
  AlertTriangle,
  ArrowRight,
  CheckCircle,
  Clock,
  FileSpreadsheet,
  FileText,
  LogIn,
  RefreshCw,
  Scale,
  Shield,
} from 'lucide-react';
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useGstnSession, useGstnStats } from '@/hooks/tax/useGstn';
import { useGSTRegistrations } from '@/hooks/tax/useTaxation';
import { useActiveOrganizationId } from '@/stores/organizationStore';

export function GstnDashboard() {
  const navigate = useNavigate();
  const activeOrganizationId = useActiveOrganizationId();
  const currentPeriod = format(subMonths(new Date(), 1), 'MMyyyy');

  const registrationsQuery = useGSTRegistrations({
    organizationId: activeOrganizationId ?? undefined,
    includeInactive: false,
    pageSize: 100,
  });

  const registrations = registrationsQuery.data?.items;
  const [selectedGstin, setSelectedGstin] = useState('');
  const selectedRegistration = registrations?.find((registration) => registration.gstin === selectedGstin);

  useEffect(() => {
    if (!selectedGstin && registrations && registrations.length > 0) {
      setSelectedGstin(registrations[0].gstin);
    }
  }, [registrations, selectedGstin]);

  const sessionQuery = useGstnSession(selectedGstin || undefined);
  const statsQuery = useGstnStats(selectedGstin || undefined, currentPeriod);

  if (registrationsQuery.isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <RefreshCw className="h-8 w-8 animate-spin text-blue-500" />
      </div>
    );
  }

  if (!registrations || registrations.length === 0) {
    return (
      <div className="space-y-6">
        <PageHeader title="GSTN Portal Integration" subtitle="File GST returns and reconcile ITC" />
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Shield className="mb-4 h-12 w-12 text-slate-300" />
            <h3 className="mb-2 text-lg font-medium">No GST Registrations Found</h3>
            <p className="mb-4 text-muted-foreground">
              Please add a GST registration before using GSTN features.
            </p>
            <Button onClick={() => navigate('/admin/gst/registrations')}>Manage GST Registrations</Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const sessionStatus = sessionQuery.data;
  const stats = statsQuery.data;

  return (
    <div className="space-y-6">
      <PageHeader
        title="GSTN Portal Integration"
        subtitle="File GST returns and reconcile ITC"
        actions={
          registrations && registrations.length > 1 ? (
            <select
              value={selectedGstin}
              onChange={(event) => setSelectedGstin(event.target.value)}
              className="h-10 rounded-md border border-input bg-background px-3 py-2 text-sm"
            >
              {registrations.map((registration) => (
                <option key={registration.id} value={registration.gstin}>
                  {registration.gstin} - {registration.tradeName || registration.legalName}
                </option>
              ))}
            </select>
          ) : undefined
        }
      />

      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-lg">GSTN Session</CardTitle>
              <CardDescription>
                {selectedRegistration?.tradeName || selectedRegistration?.legalName} ({selectedGstin})
              </CardDescription>
            </div>
            {sessionQuery.isFetching ? (
              <RefreshCw className="h-5 w-5 animate-spin text-muted-foreground" />
            ) : sessionStatus?.isAuthenticated ? (
              <Badge className="bg-green-100 text-green-700">
                <CheckCircle className="mr-1 h-3 w-3" />
                Connected
              </Badge>
            ) : (
              <Badge className="bg-slate-100 text-slate-700">
                <Clock className="mr-1 h-3 w-3" />
                Not Connected
              </Badge>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {sessionStatus?.isAuthenticated ? (
            <div className="flex items-center justify-between">
              <p className="text-sm text-muted-foreground">
                Session expires at:{' '}
                {sessionStatus.expiresAt ? format(new Date(sessionStatus.expiresAt), 'dd MMM yyyy HH:mm') : 'Unknown'}
              </p>
              <Button variant="outline" size="sm" onClick={() => sessionQuery.refetch()}>
                <RefreshCw className="mr-2 h-4 w-4" />
                Refresh
              </Button>
            </div>
          ) : (
            <div className="flex items-center justify-between">
              <p className="text-sm text-muted-foreground">
                Connect to GSTN portal to file returns and fetch data.
              </p>
              <Button onClick={() => navigate(`/admin/gst/gstn/login?gstin=${selectedGstin}`)}>
                <LogIn className="mr-2 h-4 w-4" />
                Connect to GSTN
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending Filings</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.pendingFilings ?? 0}</div>
            <p className="text-xs text-muted-foreground">Returns to be filed</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Submitted</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.submittedFilings ?? 0}</div>
            <p className="text-xs text-muted-foreground">Awaiting filing</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Filed</CardTitle>
            <CheckCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{stats?.filedFilings ?? 0}</div>
            <p className="text-xs text-muted-foreground">Successfully filed</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">ITC Mismatches</CardTitle>
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-amber-600">{stats?.itcMismatches ?? 0}</div>
            <p className="text-xs text-muted-foreground">Require attention</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card
          className="cursor-pointer transition-colors hover:border-blue-300"
          onClick={() => navigate(`/admin/gst/gstn/gstr1?gstin=${selectedGstin}`)}
        >
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-blue-100 p-2">
                <FileSpreadsheet className="h-6 w-6 text-blue-600" />
              </div>
              <div>
                <CardTitle>GSTR-1</CardTitle>
                <CardDescription>Outward Supplies Return</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <p className="mb-4 text-sm text-muted-foreground">
              Generate and file GSTR-1 for your outward supplies (sales invoices).
            </p>
            <Button variant="outline" className="w-full">
              Prepare GSTR-1
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </CardContent>
        </Card>

        <Card
          className="cursor-pointer transition-colors hover:border-green-300"
          onClick={() => navigate(`/admin/gst/gstn/gstr3b?gstin=${selectedGstin}`)}
        >
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-green-100 p-2">
                <FileText className="h-6 w-6 text-green-600" />
              </div>
              <div>
                <CardTitle>GSTR-3B</CardTitle>
                <CardDescription>Summary Return</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <p className="mb-4 text-sm text-muted-foreground">
              Generate and file GSTR-3B summary return with tax payment details.
            </p>
            <Button variant="outline" className="w-full">
              Prepare GSTR-3B
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </CardContent>
        </Card>

        <Card
          className="cursor-pointer transition-colors hover:border-purple-300"
          onClick={() => navigate(`/admin/gst/gstn/itc?gstin=${selectedGstin}`)}
        >
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-purple-100 p-2">
                <Scale className="h-6 w-6 text-purple-600" />
              </div>
              <div>
                <CardTitle>ITC Reconciliation</CardTitle>
                <CardDescription>GSTR-2B Matching</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <p className="mb-4 text-sm text-muted-foreground">
              Reconcile your purchase records with GSTR-2B data from GSTN.
            </p>
            <Button variant="outline" className="w-full">
              Reconcile ITC
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Filing History</CardTitle>
          <CardDescription>Recent GST return filings for {selectedGstin}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="py-8 text-center text-muted-foreground">
            <FileText className="mx-auto mb-4 h-12 w-12 text-slate-300" />
            <p>Filing history will appear here once returns are generated.</p>
            <Button
              variant="link"
              className="mt-2"
              onClick={() => navigate(`/admin/gst/gstn/gstr1?gstin=${selectedGstin}`)}
            >
              Start with GSTR-1
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default GstnDashboard;
