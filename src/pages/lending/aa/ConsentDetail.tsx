/**
 * Account Aggregator Consent Detail Page
 *
 * Full page view for consent details with fetch sessions and logs.
 * No modals - all actions navigate to full pages.
 */

import { format } from 'date-fns';
import {
  RefreshCw,
  XCircle,
  Download,
  Play,
  Clock,
  CheckCircle,
  AlertCircle,
  FileText,
  User,
  Shield,
  Database,
  ChevronRight,
  Loader2,
} from 'lucide-react';
import React, { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';

import { ErrorState } from '@/components/common/ErrorState';
import { PageHeader } from '@/components/common/PageHeader';
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
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Textarea } from '@/components/ui/textarea';
import {
  useAAConsent,
  useCheckAAConsentStatus,
  useInitiateAAFetch,
  useRevokeAAConsent,
} from '@/hooks/lending/useAAConsent';
import { useToast } from '@/hooks/use-toast';
import { getErrorEnvelope, showErrorToast } from '@/lib/errorToast';

// Status badge styling
const getStatusBadge = (status: string) => {
  const statusStyles: Record<
    string,
    { variant: 'default' | 'secondary' | 'destructive' | 'outline'; icon: React.ReactNode }
  > = {
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
  const statusStyles: Record<
    string,
    { variant: 'default' | 'secondary' | 'destructive' | 'outline' }
  > = {
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

  const consentQuery = useAAConsent(consentId);
  const checkStatus = useCheckAAConsentStatus(consentId);
  const revoke = useRevokeAAConsent(consentId);
  const initiateFetch = useInitiateAAFetch(consentId);

  const [revokeReason, setRevokeReason] = useState('');

  // Redirect to list when the consent genuinely doesn't exist (404), so
  // users don't get stuck on an empty page after a bookmark goes stale.
  useEffect(() => {
    if (!consentQuery.isError) return;
    const envelope = getErrorEnvelope(consentQuery.error);
    const status = (consentQuery.error as { response?: { status?: number } } | undefined)?.response
      ?.status;
    if (status === 404 || envelope?.error_code === 'NOT_FOUND') {
      toast({
        title: 'Consent not found',
        description: 'The requested consent does not exist.',
        variant: 'destructive',
      });
      navigate('/admin/lending/aa/consents');
    }
  }, [consentQuery.isError, consentQuery.error, navigate, toast]);

  const handleCheckStatus = () => {
    checkStatus.mutate(undefined, {
      onSuccess: (data) => {
        toast({
          title: 'Status updated',
          description: `Consent status: ${data.status}`,
        });
      },
      onError: (err) => showErrorToast(err, toast),
    });
  };

  const handleRevoke = () => {
    if (!revokeReason.trim()) {
      toast({
        title: 'Reason required',
        description: 'Please provide a reason for revoking the consent.',
        variant: 'destructive',
      });
      return;
    }
    revoke.mutate(
      { reason: revokeReason },
      {
        onSuccess: () => {
          setRevokeReason('');
          toast({
            title: 'Consent revoked',
            description: 'The consent has been revoked successfully.',
          });
        },
        onError: (err) => showErrorToast(err, toast),
      },
    );
  };

  const handleInitiateFetch = () => {
    const consent = consentQuery.data;
    if (!consent || !consentId) return;
    initiateFetch.mutate(
      {
        consentId,
        fiTypes: consent.fiTypes ?? [],
        dateFrom: consent.dateRangeFrom,
        dateTo: consent.dateRangeTo,
      },
      {
        onSuccess: (data) => {
          toast({
            title: 'Fetch initiated',
            description: `Session ID: ${data.sessionId}`,
          });
        },
        onError: (err) => showErrorToast(err, toast),
      },
    );
  };

  if (consentQuery.isLoading) {
    return (
      <div className="container mx-auto space-y-6 py-6">
        <Skeleton className="h-8 w-64" />
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          <Skeleton className="h-32" />
          <Skeleton className="h-32" />
          <Skeleton className="h-32" />
        </div>
        <Skeleton className="h-64" />
      </div>
    );
  }

  if (consentQuery.isError && !consentQuery.data) {
    return (
      <div className="container mx-auto space-y-6 py-6">
        <ErrorState
          title="Could not load consent"
          error={consentQuery.error}
          onRetry={() => consentQuery.refetch()}
        />
      </div>
    );
  }

  const consent = consentQuery.data;
  if (!consent) {
    return (
      <div className="container mx-auto py-6">
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <AlertCircle className="mb-4 h-12 w-12 text-muted-foreground" />
            <p className="text-lg font-medium">Consent not found</p>
            <Button
              variant="outline"
              className="mt-4"
              onClick={() => navigate('/admin/lending/aa/consents')}
            >
              Back to Consents
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const refreshing = checkStatus.isPending;
  const revoking = revoke.isPending;
  const initiatingFetch = initiateFetch.isPending;

  const canFetch = ['APPROVED', 'ACTIVE'].includes(consent.status);
  const canRevoke = ['APPROVED', 'ACTIVE', 'PENDING'].includes(consent.status);

  return (
    <div className="container mx-auto space-y-6 py-6">
      <PageHeader
        title="Consent Details"
        subtitle={consent.consentHandle || consent.id}
        breadcrumbs={[
          { label: 'AA Consents', to: '/admin/lending/aa/consents' },
          { label: consent.consentHandle || consent.id },
        ]}
        actions={
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={handleCheckStatus} disabled={refreshing}>
              {refreshing ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <RefreshCw className="mr-2 h-4 w-4" />
              )}
              Check Status
            </Button>

            {canFetch && (
              <Button size="sm" onClick={handleInitiateFetch} disabled={initiatingFetch}>
                {initiatingFetch ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Play className="mr-2 h-4 w-4" />
                )}
                Fetch Data
              </Button>
            )}

            {canRevoke && (
              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <Button variant="destructive" size="sm">
                    <XCircle className="mr-2 h-4 w-4" />
                    Revoke
                  </Button>
                </AlertDialogTrigger>
                <AlertDialogContent>
                  <AlertDialogHeader>
                    <AlertDialogTitle>Revoke Consent</AlertDialogTitle>
                    <AlertDialogDescription>
                      This action cannot be undone. The customer will need to provide a new consent
                      to fetch their financial data.
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
        }
      />

      {/* Status and Summary Cards */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Status</CardDescription>
          </CardHeader>
          <CardContent>{getStatusBadge(consent.status)}</CardContent>
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
            <p className="text-2xl font-bold">{consent.fetchSessions?.length || 0}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Expires</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm font-medium">
              {format(new Date(consent.consentExpiry), 'dd MMM yyyy')}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Detail Tabs */}
      <Tabs defaultValue="details" className="space-y-4">
        <TabsList>
          <TabsTrigger value="details">Details</TabsTrigger>
          <TabsTrigger value="sessions">
            Fetch Sessions ({consent.fetchSessions?.length || 0})
          </TabsTrigger>
          <TabsTrigger value="logs">Activity Log ({consent.logs?.length || 0})</TabsTrigger>
        </TabsList>

        {/* Details Tab */}
        <TabsContent value="details" className="space-y-4">
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
            {/* Consent Information */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-lg">
                  <Shield className="h-5 w-5" />
                  Consent Information
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-muted-foreground">Consent Handle</p>
                    <p className="font-mono text-sm">{consent.consentHandle || '-'}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Consent ID</p>
                    <p className="font-mono text-sm">{consent.consentId || '-'}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Purpose</p>
                    <p className="text-sm">{consent.purpose}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Mode</p>
                    <p className="text-sm">{consent.consentMode}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Fetch Type</p>
                    <p className="text-sm">{consent.fetchType}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Frequency</p>
                    <p className="text-sm">
                      {consent.frequencyType} ({consent.frequencyValue}x)
                    </p>
                  </div>
                </div>

                <div>
                  <p className="mb-2 text-sm text-muted-foreground">FI Types</p>
                  <div className="flex flex-wrap gap-1">
                    {consent.fiTypes?.map((type) => (
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
                <CardTitle className="flex items-center gap-2 text-lg">
                  <User className="h-5 w-5" />
                  Customer & Timeline
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-muted-foreground">Customer VUA</p>
                    <p className="font-mono text-sm">{consent.customerId}</p>
                  </div>
                  {consent.entityName && (
                    <div>
                      <p className="text-sm text-muted-foreground">Entity</p>
                      <p className="text-sm">{consent.entityName}</p>
                    </div>
                  )}
                  <div>
                    <p className="text-sm text-muted-foreground">Data From</p>
                    <p className="text-sm">
                      {format(new Date(consent.dateRangeFrom), 'dd MMM yyyy')}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Data To</p>
                    <p className="text-sm">
                      {format(new Date(consent.dateRangeTo), 'dd MMM yyyy')}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Created</p>
                    <p className="text-sm">
                      {format(new Date(consent.createdAt), 'dd MMM yyyy HH:mm')}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Last Updated</p>
                    <p className="text-sm">
                      {format(new Date(consent.updatedAt), 'dd MMM yyyy HH:mm')}
                    </p>
                  </div>
                </div>

                {consent.redirectUrl && (
                  <div>
                    <p className="mb-2 text-sm text-muted-foreground">Consent URL</p>
                    <a
                      href={consent.redirectUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="break-all text-sm text-blue-600 hover:underline"
                    >
                      {consent.redirectUrl}
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
              <CardTitle className="flex items-center gap-2 text-lg">
                <Database className="h-5 w-5" />
                Data Fetch Sessions
              </CardTitle>
              <CardDescription>History of data fetch requests for this consent</CardDescription>
            </CardHeader>
            <CardContent>
              {consent.fetchSessions?.length === 0 ? (
                <div className="py-8 text-center">
                  <Database className="mx-auto mb-4 h-12 w-12 text-muted-foreground" />
                  <p className="text-muted-foreground">No fetch sessions yet</p>
                  {canFetch && (
                    <Button
                      className="mt-4"
                      onClick={handleInitiateFetch}
                      disabled={initiatingFetch}
                    >
                      {initiatingFetch ? (
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      ) : (
                        <Play className="mr-2 h-4 w-4" />
                      )}
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
                    {consent.fetchSessions?.map((session) => (
                      <TableRow key={session.id}>
                        <TableCell className="font-mono text-xs">
                          {session.sessionId?.slice(0, 12)}...
                        </TableCell>
                        <TableCell>{getSessionStatusBadge(session.status)}</TableCell>
                        <TableCell>
                          <div className="flex flex-wrap gap-1">
                            {session.fiTypesRequested?.slice(0, 2).map((type) => (
                              <Badge key={type} variant="outline" className="text-xs">
                                {type}
                              </Badge>
                            ))}
                            {session.fiTypesRequested?.length > 2 && (
                              <Badge variant="outline" className="text-xs">
                                +{session.fiTypesRequested.length - 2}
                              </Badge>
                            )}
                          </div>
                        </TableCell>
                        <TableCell>{session.accountsCount}</TableCell>
                        <TableCell>{session.transactionsCount}</TableCell>
                        <TableCell className="text-xs">
                          {format(new Date(session.dataFrom), 'dd/MM/yy')} -{' '}
                          {format(new Date(session.dataTo), 'dd/MM/yy')}
                        </TableCell>
                        <TableCell className="text-xs">
                          {format(new Date(session.initiatedAt), 'dd MMM HH:mm')}
                        </TableCell>
                        <TableCell>
                          <Link to={`/admin/lending/aa/sessions/${session.id}`}>
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
              <CardTitle className="flex items-center gap-2 text-lg">
                <FileText className="h-5 w-5" />
                Activity Log
              </CardTitle>
              <CardDescription>Consent status changes and events</CardDescription>
            </CardHeader>
            <CardContent>
              {consent.logs?.length === 0 ? (
                <div className="py-8 text-center">
                  <FileText className="mx-auto mb-4 h-12 w-12 text-muted-foreground" />
                  <p className="text-muted-foreground">No activity recorded yet</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {consent.logs?.map((log) => (
                    <div key={log.id} className="flex items-start gap-4 rounded-lg border p-4">
                      <div className="flex-shrink-0">
                        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-muted">
                          {log.eventType === 'STATUS_CHANGE' ? (
                            <RefreshCw className="h-4 w-4" />
                          ) : log.eventType === 'WEBHOOK_RECEIVED' ? (
                            <Download className="h-4 w-4" />
                          ) : (
                            <FileText className="h-4 w-4" />
                          )}
                        </div>
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-medium">
                            {log.eventType.replace(/_/g, ' ')}
                          </span>
                          {log.oldStatus && log.newStatus && (
                            <span className="text-xs text-muted-foreground">
                              {log.oldStatus} → {log.newStatus}
                            </span>
                          )}
                        </div>
                        {log.message && (
                          <p className="mt-1 text-sm text-muted-foreground">{log.message}</p>
                        )}
                        <p className="mt-2 text-xs text-muted-foreground">
                          {format(new Date(log.createdAt), 'dd MMM yyyy HH:mm:ss')}
                          {log.createdByName && ` by ${log.createdByName}`}
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
