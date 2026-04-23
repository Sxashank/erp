import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Shield,
  FileText,
  AlertTriangle,
  CheckCircle,
  Clock,
  RefreshCw,
  ArrowRight,
  LogIn,
  FileSpreadsheet,
  Scale,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { PageHeader } from '@/components/common/PageHeader';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { gstnApi, gstRegistrationsApi } from '@/services/api';
import { useAuth } from '@/contexts/AuthContext';
import { useActiveOrganizationId } from '@/stores/organizationStore';
import { format, subMonths } from 'date-fns';

interface GSTRegistration {
  id: string;
  gstin: string;
  legal_name: string;
  trade_name?: string;
  state_code: string;
  is_active: boolean;
}

interface SessionStatus {
  is_authenticated: boolean;
  gstin: string;
  expires_at?: string;
}

interface FilingStats {
  pending_filings: number;
  submitted_filings: number;
  filed_filings: number;
  itc_mismatches: number;
}

export function GstnDashboard() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const activeOrganizationId = useActiveOrganizationId();
  const [registrations, setRegistrations] = useState<GSTRegistration[]>([]);
  const [selectedGstin, setSelectedGstin] = useState<string>('');
  const [sessionStatus, setSessionStatus] = useState<SessionStatus | null>(null);
  const [stats, setStats] = useState<FilingStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [checkingSession, setCheckingSession] = useState(false);

  const currentPeriod = format(subMonths(new Date(), 1), 'MMyyyy');

  useEffect(() => {
    fetchRegistrations();
  }, []);

  useEffect(() => {
    if (selectedGstin) {
      checkSessionStatus();
      fetchStats();
    }
  }, [selectedGstin]);

  const fetchRegistrations = async () => {
    try {
      setLoading(true);
      const response = await gstRegistrationsApi.list({
        organization_id: activeOrganizationId ?? undefined,
        include_inactive: false,
      });
      const data = response.data.items || response.data;
      setRegistrations(data);
      if (data.length > 0) {
        setSelectedGstin(data[0].gstin);
      }
    } catch (error) {
      console.error('Failed to fetch GST registrations:', error);
    } finally {
      setLoading(false);
    }
  };

  const checkSessionStatus = async () => {
    if (!selectedGstin) return;
    try {
      setCheckingSession(true);
      const response = await gstnApi.getSession(selectedGstin);
      setSessionStatus(response.data);
    } catch (error) {
      setSessionStatus({ is_authenticated: false, gstin: selectedGstin });
    } finally {
      setCheckingSession(false);
    }
  };

  const fetchStats = async () => {
    if (!selectedGstin) return;
    try {
      const response = await gstnApi.getStats({ gstin: selectedGstin, return_period: currentPeriod });
      setStats(response.data);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  };

  const getStatusBadge = (status: string) => {
    const statusConfig: Record<string, { className: string; label: string }> = {
      DRAFT: { className: 'bg-slate-100 text-slate-700', label: 'Draft' },
      GENERATED: { className: 'bg-blue-100 text-blue-700', label: 'Generated' },
      VALIDATED: { className: 'bg-amber-100 text-amber-700', label: 'Validated' },
      SUBMITTED: { className: 'bg-purple-100 text-purple-700', label: 'Submitted' },
      FILED: { className: 'bg-green-100 text-green-700', label: 'Filed' },
      ERROR: { className: 'bg-red-100 text-red-700', label: 'Error' },
    };
    const config = statusConfig[status] || statusConfig.DRAFT;
    return <Badge className={config.className}>{config.label}</Badge>;
  };

  const selectedRegistration = registrations.find(r => r.gstin === selectedGstin);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin text-blue-500" />
      </div>
    );
  }

  if (registrations.length === 0) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="GSTN Portal Integration"
          subtitle="File GST returns and reconcile ITC"
        />
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Shield className="h-12 w-12 text-slate-300 mb-4" />
            <h3 className="text-lg font-medium mb-2">No GST Registrations Found</h3>
            <p className="text-muted-foreground mb-4">
              Please add a GST registration before using GSTN features.
            </p>
            <Button onClick={() => navigate('/admin/gst/registrations')}>
              Manage GST Registrations
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="GSTN Portal Integration"
        subtitle="File GST returns and reconcile ITC"
        actions={
          registrations.length > 1 ? (
            <select
              value={selectedGstin}
              onChange={(e) => setSelectedGstin(e.target.value)}
              className="h-10 rounded-md border border-input bg-background px-3 py-2 text-sm"
            >
              {registrations.map((reg) => (
                <option key={reg.id} value={reg.gstin}>
                  {reg.gstin} - {reg.trade_name || reg.legal_name}
                </option>
              ))}
            </select>
          ) : undefined
        }
      />

      {/* Session Status Card */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-lg">GSTN Session</CardTitle>
              <CardDescription>
                {selectedRegistration?.trade_name || selectedRegistration?.legal_name} ({selectedGstin})
              </CardDescription>
            </div>
            {checkingSession ? (
              <RefreshCw className="h-5 w-5 animate-spin text-muted-foreground" />
            ) : sessionStatus?.is_authenticated ? (
              <Badge className="bg-green-100 text-green-700">
                <CheckCircle className="h-3 w-3 mr-1" />
                Connected
              </Badge>
            ) : (
              <Badge className="bg-slate-100 text-slate-700">
                <Clock className="h-3 w-3 mr-1" />
                Not Connected
              </Badge>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {sessionStatus?.is_authenticated ? (
            <div className="flex items-center justify-between">
              <p className="text-sm text-muted-foreground">
                Session expires at: {sessionStatus.expires_at ? format(new Date(sessionStatus.expires_at), 'dd MMM yyyy HH:mm') : 'Unknown'}
              </p>
              <Button variant="outline" size="sm" onClick={checkSessionStatus}>
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh
              </Button>
            </div>
          ) : (
            <div className="flex items-center justify-between">
              <p className="text-sm text-muted-foreground">
                Connect to GSTN portal to file returns and fetch data.
              </p>
              <Button onClick={() => navigate(`/admin/gst/gstn/login?gstin=${selectedGstin}`)}>
                <LogIn className="h-4 w-4 mr-2" />
                Connect to GSTN
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Quick Stats */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Pending Filings</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.pending_filings || 0}</div>
            <p className="text-xs text-muted-foreground">Returns to be filed</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Submitted</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.submitted_filings || 0}</div>
            <p className="text-xs text-muted-foreground">Awaiting filing</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Filed</CardTitle>
            <CheckCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{stats?.filed_filings || 0}</div>
            <p className="text-xs text-muted-foreground">Successfully filed</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">ITC Mismatches</CardTitle>
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-amber-600">{stats?.itc_mismatches || 0}</div>
            <p className="text-xs text-muted-foreground">Require attention</p>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {/* GSTR-1 Card */}
        <Card className="hover:border-blue-300 transition-colors cursor-pointer" onClick={() => navigate(`/admin/gst/gstn/gstr1?gstin=${selectedGstin}`)}>
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <FileSpreadsheet className="h-6 w-6 text-blue-600" />
              </div>
              <div>
                <CardTitle>GSTR-1</CardTitle>
                <CardDescription>Outward Supplies Return</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground mb-4">
              Generate and file GSTR-1 for your outward supplies (sales invoices).
            </p>
            <Button variant="outline" className="w-full">
              Prepare GSTR-1
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </CardContent>
        </Card>

        {/* GSTR-3B Card */}
        <Card className="hover:border-green-300 transition-colors cursor-pointer" onClick={() => navigate(`/admin/gst/gstn/gstr3b?gstin=${selectedGstin}`)}>
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 rounded-lg">
                <FileText className="h-6 w-6 text-green-600" />
              </div>
              <div>
                <CardTitle>GSTR-3B</CardTitle>
                <CardDescription>Summary Return</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground mb-4">
              Generate and file GSTR-3B summary return with tax payment details.
            </p>
            <Button variant="outline" className="w-full">
              Prepare GSTR-3B
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </CardContent>
        </Card>

        {/* ITC Reconciliation Card */}
        <Card className="hover:border-purple-300 transition-colors cursor-pointer" onClick={() => navigate(`/admin/gst/gstn/itc?gstin=${selectedGstin}`)}>
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 rounded-lg">
                <Scale className="h-6 w-6 text-purple-600" />
              </div>
              <div>
                <CardTitle>ITC Reconciliation</CardTitle>
                <CardDescription>GSTR-2B Matching</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground mb-4">
              Reconcile your purchase records with GSTR-2B data from GSTN.
            </p>
            <Button variant="outline" className="w-full">
              Reconcile ITC
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Return Period Selection */}
      <Card>
        <CardHeader>
          <CardTitle>Filing History</CardTitle>
          <CardDescription>Recent GST return filings for {selectedGstin}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            <FileText className="h-12 w-12 mx-auto mb-4 text-slate-300" />
            <p>Filing history will appear here once returns are generated.</p>
            <Button variant="link" className="mt-2" onClick={() => navigate(`/admin/gst/gstn/gstr1?gstin=${selectedGstin}`)}>
              Start with GSTR-1
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default GstnDashboard;
