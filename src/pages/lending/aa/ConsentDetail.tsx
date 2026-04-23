/**
 * Account Aggregator Consent Detail Page
 *
 * Full page view for consent details with fetch sessions and logs.
 * No modals - all actions navigate to full pages.
 */

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { format } from 'date-fns';
import {
  ArrowLeft,
  RefreshCw,
  XCircle,
  Download,
  Play,
  Clock,
  CheckCircle,
  AlertCircle,
  FileText,
  Building2,
  Calendar,
  User,
  Shield,
  Database,
  ChevronRight,
} from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { useToast } from '@/hooks/use-toast';
import { Skeleton } from '@/components/ui/skeleton';

// Types
interface FetchSession {
  id: string;
  session_id: string;
  status: string;
  fi_types_requested: string[];
  accounts_count: number;
  transactions_count: number;
  data_from: string;
  data_to: string;
  initiated_at: string;
  completed_at: string | null;
  error_message: string | null;
}

interface ConsentLog {
  id: string;
  event_type: string;
  old_status: string | null;
  new_status: string | null;
  message: string | null;
  raw_payload: Record<string, unknown>;
  created_at: string;
  created_by_name: string | null;
}

interface ConsentDetail {
  id: string;
  organization_id: string;
  entity_id: string | null;
  entity_name: string | null;
  customer_id: string;
  provider: string;
  consent_handle: string;
  consent_id: string | null;
  status: string;
  purpose: string;
  fi_types: string[];
  consent_mode: string;
  fetch_type: string;
  frequency_type: string;
  frequency_value: number;
  date_range_from: string;
  date_range_to: string;
  consent_expiry: string;
  redirect_url: string | null;
  created_at: string;
  updated_at: string;
  created_by_name: string | null;
  fetch_sessions: FetchSession[];
  logs: ConsentLog[];
}

// Status badge styling
const getStatusBadge = (status: string) => {
  const statusStyles: Record<string, { variant: 'default' | 'secondary' | 'destructive' | 'outline'; icon: React.ReactNode }> = {
    PENDING: { variant: 'secondary', icon: <Clock className="h-3 w-3" /> },
    APPROVED: { variant: 'default', icon: <CheckCircle className="h-3 w-3" /> },
    ACTIVE: { variant: 'default', icon: <CheckCircle className="h-3 w-3" /> },
    REJECTED: { variant: 'destructive', icon: <XCircle className="h-3 w-3" /> },
    REVOKED: { variant: 'destructive', icon: <XCircle className="h-3 w-3" /> },
    EXPIRED: { variant: 'outline', icon: <AlertCircle className="h-3 w-3" /> },
    FAILED: { variant: 'destructive', icon: <AlertCircle className="h-3 w-3" /> },
  };

  const style = statusStyles[status] || { variant: 'outline' as const, icon: null };

  return (
    <Badge variant={style.variant} className="gap-1">
      {style.icon}
      {status}
    </Badge>
  );
};

const getSessionStatusBadge = (status: string) => {
  const statusStyles: Record<string, { variant: 'default' | 'secondary' | 'destructive' | 'outline' }> = {
    INITIATED: { variant: 'secondary' },
    PENDING: { variant: 'secondary' },
    READY: { variant: 'default' },
    COMPLETED: { variant: 'default' },
    PARTIAL: { variant: 'outline' },
    FAILED: { variant: 'destructive' },
    EXPIRED: { variant: 'outline' },
  };

  const style = statusStyles[status] || { variant: 'outline' as const };
  return <Badge variant={style.variant}>{status}</Badge>;
};

export default function ConsentDetailPage() {
  const { consentId } = useParams<{ consentId: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();

  const [consent, setConsent] = useState<ConsentDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [revoking, setRevoking] = useState(false);
  const [revokeReason, setRevokeReason] = useState('');
  const [initiatingFetch, setInitiatingFetch] = useState(false);

  // Fetch consent details
  const fetchConsentDetails = async () => {
    try {
      const response = await fetch(`/api/v1/lending/aa/consents/${consentId}`);
      if (!response.ok) {
        if (response.status === 404) {
          toast({
            title: 'Consent not found',
            description: 'The requested consent does not exist.',
            variant: 'destructive',
          });
          navigate('/lending/aa/consents');
          return;
        }
        throw new Error('Failed to fetch consent details');
      }
      const data = await response.json();
      setConsent(data);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load consent details. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchConsentDetails();
  }, [consentId]);

  // Check consent status with provider
  const handleCheckStatus = async () => {
    setRefreshing(true);
    try {
      const response = await fetch(`/api/v1/lending/aa/consents/${consentId}/check-status`, {
        method: 'POST',
      });
      if (!response.ok) throw new Error('Failed to check status');

      const data = await response.json();
      setConsent(prev => prev ? { ...prev, ...data } : null);

      toast({
        title: 'Status updated',
        description: `Consent status: ${data.status}`,
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to check consent status.',
        variant: 'destructive',
      });
    } finally {
      setRefreshing(false);
    }
  };

  // Revoke consent
  const handleRevoke = async () => {
    if (!revokeReason.trim()) {
      toast({
        title: 'Reason required',
        description: 'Please provide a reason for revoking the consent.',
        variant: 'destructive',
      });
      return;
    }

    setRevoking(true);
    try {
      const response = await fetch(`/api/v1/lending/aa/consents/${consentId}/revoke`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reason: revokeReason }),
      });
      if (!response.ok) throw new Error('Failed to revoke consent');

      const data = await response.json();
      setConsent(prev => prev ? { ...prev, ...data } : null);
      setRevokeReason('');

      toast({
        title: 'Consent revoked',
        description: 'The consent has been revoked successfully.',
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to revoke consent.',
        variant: 'destructive',
      });
    } finally {
      setRevoking(false);
    }
  };

  // Initiate data fetch
  const handleInitiateFetch = async () => {
    setInitiatingFetch(true);
    try {
      const response = await fetch(`/api/v1/lending/aa/consents/${consentId}/fetch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          consent_id: consentId,
          fi_types: consent?.fi_types || [],
          date_from: consent?.date_range_from,
          date_to: consent?.date_range_to,
        }),
      });
      if (!response.ok) throw new Error('Failed to initiate fetch');

      const data = await response.json();

      toast({
        title: 'Fetch initiated',
        description: `Session ID: ${data.session_id}`,
      });

      // Refresh to show new session
      fetchConsentDetails();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to initiate data fetch.',
        variant: 'destructive',
      });
    } finally {
      setInitiatingFetch(false);
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto py-6 space-y-6">
        <Skeleton className="h-8 w-64" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Skeleton className="h-32" />
          <Skeleton className="h-32" />
          <Skeleton className="h-32" />
        </div>
        <Skeleton className="h-64" />
      </div>
    );
  }

  if (!consent) {
    return (
      <div className="container mx-auto py-6">
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <AlertCircle className="h-12 w-12 text-muted-foreground mb-4" />
            <p className="text-lg font-medium">Consent not found</p>
            <Button
              variant="outline"
              className="mt-4"
              onClick={() => navigate('/lending/aa/consents')}
            >
              Back to Consents
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const canFetch = ['APPROVED', 'ACTIVE'].includes(consent.status);
  const canRevoke = ['APPROVED', 'ACTIVE', 'PENDING'].includes(consent.status);

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => navigate('/lending/aa/consents')}
          >
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold">Consent Details</h1>
            <p className="text-sm text-muted-foreground">
              {consent.consent_handle || consent.id}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleCheckStatus}
            disabled={refreshing}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            Check Status
          </Button>

          {canFetch && (
            <Button
              size="sm"
              onClick={handleInitiateFetch}
              disabled={initiatingFetch}
            >
              <Play className="h-4 w-4 mr-2" />
              Fetch Data
            </Button>
          )}

          {canRevoke && (
            <AlertDialog>
              <AlertDialogTrigger asChild>
                <Button variant="destructive" size="sm">
                  <XCircle className="h-4 w-4 mr-2" />
                  Revoke
                </Button>
              </AlertDialogTrigger>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle>Revoke Consent</AlertDialogTitle>
                  <AlertDialogDescription>
                    This action cannot be undone. The customer will need to provide
                    a new consent to fetch their financial data.
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <div className="py-4">
                  <Label htmlFor="revoke-reason">Reason for revocation</Label>
                  <Textarea
                    id="revoke-reason"
                    value={revokeReason}
                    onChange={(e) => setRevokeReason(e.target.value)}
                    placeholder="Enter reason for revoking this consent..."
                    className="mt-2"
                  />
                </div>
                <AlertDialogFooter>
                  <AlertDialogCancel>Cancel</AlertDialogCancel>
                  <AlertDialogAction
                    onClick={handleRevoke}
                    disabled={revoking || !revokeReason.trim()}
                    className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                  >
                    {revoking ? 'Revoking...' : 'Revoke Consent'}
                  </AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          )}
        </div>
      </div>

      {/* Status and Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Status</CardDescription>
          </CardHeader>
          <CardContent>
            {getStatusBadge(consent.status)}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Provider</CardDescription>
          </CardHeader>
          <CardContent>
            <Badge variant="outline">{consent.provider}</Badge>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Fetch Sessions</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{consent.fetch_sessions?.length || 0}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Expires</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm font-medium">
              {format(new Date(consent.consent_expiry), 'dd MMM yyyy')}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Detail Tabs */}
      <Tabs defaultValue="details" className="space-y-4">
        <TabsList>
          <TabsTrigger value="details">Details</TabsTrigger>
          <TabsTrigger value="sessions">
            Fetch Sessions ({consent.fetch_sessions?.length || 0})
          </TabsTrigger>
          <TabsTrigger value="logs">
            Activity Log ({consent.logs?.length || 0})
          </TabsTrigger>
        </TabsList>

        {/* Details Tab */}
        <TabsContent value="details" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Consent Information */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <Shield className="h-5 w-5" />
                  Consent Information
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-muted-foreground">Consent Handle</p>
                    <p className="font-mono text-sm">{consent.consent_handle || '-'}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Consent ID</p>
                    <p className="font-mono text-sm">{consent.consent_id || '-'}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Purpose</p>
                    <p className="text-sm">{consent.purpose}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Mode</p>
                    <p className="text-sm">{consent.consent_mode}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Fetch Type</p>
                    <p className="text-sm">{consent.fetch_type}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Frequency</p>
                    <p className="text-sm">
                      {consent.frequency_type} ({consent.frequency_value}x)
                    </p>
                  </div>
                </div>

                <div>
                  <p className="text-sm text-muted-foreground mb-2">FI Types</p>
                  <div className="flex flex-wrap gap-1">
                    {consent.fi_types?.map((type) => (
                      <Badge key={type} variant="secondary" className="text-xs">
                        {type}
                      </Badge>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Customer & Date Information */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <User className="h-5 w-5" />
                  Customer & Timeline
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-muted-foreground">Customer VUA</p>
                    <p className="font-mono text-sm">{consent.customer_id}</p>
                  </div>
                  {consent.entity_name && (
                    <div>
                      <p className="text-sm text-muted-foreground">Entity</p>
                      <p className="text-sm">{consent.entity_name}</p>
                    </div>
                  )}
                  <div>
                    <p className="text-sm text-muted-foreground">Data From</p>
                    <p className="text-sm">
                      {format(new Date(consent.date_range_from), 'dd MMM yyyy')}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Data To</p>
                    <p className="text-sm">
                      {format(new Date(consent.date_range_to), 'dd MMM yyyy')}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Created</p>
                    <p className="text-sm">
                      {format(new Date(consent.created_at), 'dd MMM yyyy HH:mm')}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Last Updated</p>
                    <p className="text-sm">
                      {format(new Date(consent.updated_at), 'dd MMM yyyy HH:mm')}
                    </p>
                  </div>
                </div>

                {consent.redirect_url && (
                  <div>
                    <p className="text-sm text-muted-foreground mb-2">Consent URL</p>
                    <a
                      href={consent.redirect_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm text-blue-600 hover:underline break-all"
                    >
                      {consent.redirect_url}
                    </a>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Fetch Sessions Tab */}
        <TabsContent value="sessions">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Database className="h-5 w-5" />
                Data Fetch Sessions
              </CardTitle>
              <CardDescription>
                History of data fetch requests for this consent
              </CardDescription>
            </CardHeader>
            <CardContent>
              {consent.fetch_sessions?.length === 0 ? (
                <div className="text-center py-8">
                  <Database className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                  <p className="text-muted-foreground">No fetch sessions yet</p>
                  {canFetch && (
                    <Button
                      className="mt-4"
                      onClick={handleInitiateFetch}
                      disabled={initiatingFetch}
                    >
                      <Play className="h-4 w-4 mr-2" />
                      Initiate First Fetch
                    </Button>
                  )}
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Session ID</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>FI Types</TableHead>
                      <TableHead>Accounts</TableHead>
                      <TableHead>Transactions</TableHead>
                      <TableHead>Date Range</TableHead>
                      <TableHead>Initiated</TableHead>
                      <TableHead></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {consent.fetch_sessions?.map((session) => (
                      <TableRow key={session.id}>
                        <TableCell className="font-mono text-xs">
                          {session.session_id?.slice(0, 12)}...
                        </TableCell>
                        <TableCell>{getSessionStatusBadge(session.status)}</TableCell>
                        <TableCell>
                          <div className="flex flex-wrap gap-1">
                            {session.fi_types_requested?.slice(0, 2).map((type) => (
                              <Badge key={type} variant="outline" className="text-xs">
                                {type}
                              </Badge>
                            ))}
                            {session.fi_types_requested?.length > 2 && (
                              <Badge variant="outline" className="text-xs">
                                +{session.fi_types_requested.length - 2}
                              </Badge>
                            )}
                          </div>
                        </TableCell>
                        <TableCell>{session.accounts_count}</TableCell>
                        <TableCell>{session.transactions_count}</TableCell>
                        <TableCell className="text-xs">
                          {format(new Date(session.data_from), 'dd/MM/yy')} -{' '}
                          {format(new Date(session.data_to), 'dd/MM/yy')}
                        </TableCell>
                        <TableCell className="text-xs">
                          {format(new Date(session.initiated_at), 'dd MMM HH:mm')}
                        </TableCell>
                        <TableCell>
                          <Link to={`/lending/aa/sessions/${session.id}`}>
                            <Button variant="ghost" size="icon">
                              <ChevronRight className="h-4 w-4" />
                            </Button>
                          </Link>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Activity Log Tab */}
        <TabsContent value="logs">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <FileText className="h-5 w-5" />
                Activity Log
              </CardTitle>
              <CardDescription>
                Consent status changes and events
              </CardDescription>
            </CardHeader>
            <CardContent>
              {consent.logs?.length === 0 ? (
                <div className="text-center py-8">
                  <FileText className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                  <p className="text-muted-foreground">No activity recorded yet</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {consent.logs?.map((log) => (
                    <div
                      key={log.id}
                      className="flex items-start gap-4 p-4 border rounded-lg"
                    >
                      <div className="flex-shrink-0">
                        <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center">
                          {log.event_type === 'STATUS_CHANGE' ? (
                            <RefreshCw className="h-4 w-4" />
                          ) : log.event_type === 'WEBHOOK_RECEIVED' ? (
                            <Download className="h-4 w-4" />
                          ) : (
                            <FileText className="h-4 w-4" />
                          )}
                        </div>
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-sm">
                            {log.event_type.replace(/_/g, ' ')}
                          </span>
                          {log.old_status && log.new_status && (
                            <span className="text-xs text-muted-foreground">
                              {log.old_status} → {log.new_status}
                            </span>
                          )}
                        </div>
                        {log.message && (
                          <p className="text-sm text-muted-foreground mt-1">
                            {log.message}
                          </p>
                        )}
                        <p className="text-xs text-muted-foreground mt-2">
                          {format(new Date(log.created_at), 'dd MMM yyyy HH:mm:ss')}
                          {log.created_by_name && ` by ${log.created_by_name}`}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
