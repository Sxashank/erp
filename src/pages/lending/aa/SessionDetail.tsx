/**
 * Account Aggregator Fetch Session Detail Page
 *
 * Full page view for a specific data fetch session.
 * Shows fetched accounts and allows data pull.
 */

import { format } from 'date-fns';
import {
  RefreshCw,
  Download,
  Loader2,
  Clock,
  CheckCircle,
  AlertCircle,
  XCircle,
  Database,
  CreditCard,
  Building2,
  Calendar,
  ChevronRight,
} from 'lucide-react';
import React, { useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';

import { ErrorState } from '@/components/common/ErrorState';
import { PageHeader } from '@/components/common/PageHeader';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { useAASession, useFetchAASessionData } from '@/hooks/lending/useAASession';
import { useToast } from '@/hooks/use-toast';
import { getErrorEnvelope, showErrorToast } from '@/lib/errorToast';

// Status styling
const getStatusBadge = (status: string) => {
  const statusStyles: Record<
    string,
    { variant: 'default' | 'secondary' | 'destructive' | 'outline'; icon: React.ReactNode }
  > = {
    INITIATED: { variant: 'secondary', icon: <Clock className="h-3 w-3" /> },
    PENDING: { variant: 'secondary', icon: <Clock className="h-3 w-3" /> },
    READY: { variant: 'default', icon: <CheckCircle className="h-3 w-3" /> },
    COMPLETED: { variant: 'default', icon: <CheckCircle className="h-3 w-3" /> },
    PARTIAL: { variant: 'outline', icon: <AlertCircle className="h-3 w-3" /> },
    FAILED: { variant: 'destructive', icon: <XCircle className="h-3 w-3" /> },
    EXPIRED: { variant: 'outline', icon: <AlertCircle className="h-3 w-3" /> },
  };

  const style = statusStyles[status] || { variant: 'outline' as const, icon: null };

  return (
    <Badge variant={style.variant} className="gap-1">
      {style.icon}
      {status}
    </Badge>
  );
};

// Format currency
const formatCurrency = (amount: number, currency = 'INR') => {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: currency,
    maximumFractionDigits: 2,
  }).format(amount);
};

export default function SessionDetailPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();

  const sessionQuery = useAASession(sessionId);
  const fetchData = useFetchAASessionData(sessionId);

  // Bounce back to the previous page on a true 404, mirroring the legacy
  // behaviour of the old fetch-based handler.
  useEffect(() => {
    if (!sessionQuery.isError) return;
    const envelope = getErrorEnvelope(sessionQuery.error);
    const status = (sessionQuery.error as { response?: { status?: number } } | undefined)?.response
      ?.status;
    if (status === 404 || envelope?.error_code === 'NOT_FOUND') {
      toast({
        title: 'Session not found',
        description: 'The requested session does not exist.',
        variant: 'destructive',
      });
      navigate('/admin/lending/aa/sessions', { replace: true });
    }
  }, [sessionQuery.isError, sessionQuery.error, navigate, toast]);

  const handleFetchData = () => {
    fetchData.mutate(undefined, {
      onSuccess: (data) => {
        toast({
          title: 'Data fetched',
          description: `Fetched ${data.accountsCount} accounts with ${data.transactionsCount} transactions.`,
        });
      },
      onError: (err) => showErrorToast(err, toast),
    });
  };

  const fetching = fetchData.isPending;

  if (sessionQuery.isLoading) {
    return (
      <div className="container mx-auto space-y-6 py-6">
        <Skeleton className="h-8 w-64" />
        <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
          <Skeleton className="h-24" />
          <Skeleton className="h-24" />
          <Skeleton className="h-24" />
          <Skeleton className="h-24" />
        </div>
        <Skeleton className="h-64" />
      </div>
    );
  }

  if (sessionQuery.isError && !sessionQuery.data) {
    return (
      <div className="container mx-auto space-y-6 py-6">
        <ErrorState
          title="Could not load session"
          error={sessionQuery.error}
          onRetry={() => sessionQuery.refetch()}
        />
      </div>
    );
  }

  const session = sessionQuery.data;
  if (!session) {
    return (
      <div className="container mx-auto py-6">
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <AlertCircle className="mb-4 h-12 w-12 text-muted-foreground" />
            <p className="text-lg font-medium">Session not found</p>
            <Button variant="outline" className="mt-4" onClick={() => navigate(-1)}>
              Go Back
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const canFetch = ['READY', 'PARTIAL', 'INITIATED'].includes(session.status);
  const totalBalance =
    session.bankAccounts?.reduce((sum, acc) => sum + (acc.currentBalance || 0), 0) || 0;

  return (
    <div className="container mx-auto space-y-6 py-6">
      <PageHeader
        title="Fetch Session"
        subtitle={session.sessionId}
        breadcrumbs={[
          { label: 'AA Consents', to: '/admin/lending/aa/consents' },
          { label: session.sessionId },
        ]}
        actions={
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => sessionQuery.refetch()}
              disabled={sessionQuery.isFetching}
            >
              {sessionQuery.isFetching ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <RefreshCw className="mr-2 h-4 w-4" />
              )}
              Refresh
            </Button>

            {canFetch && (
              <Button size="sm" onClick={handleFetchData} disabled={fetching}>
                {fetching ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Fetching...
                  </>
                ) : (
                  <>
                    <Download className="mr-2 h-4 w-4" />
                    Fetch Data
                  </>
                )}
              </Button>
            )}
          </div>
        }
      />

      {/* Stats Cards */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Status</CardDescription>
          </CardHeader>
          <CardContent>{getStatusBadge(session.status)}</CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Accounts Fetched</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <CreditCard className="h-5 w-5 text-muted-foreground" />
              <span className="text-2xl font-bold">{session.accountsCount}</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Transactions</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <Database className="h-5 w-5 text-muted-foreground" />
              <span className="text-2xl font-bold">{session.transactionsCount}</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Total Balance</CardDescription>
          </CardHeader>
          <CardContent>
            <span className="text-2xl font-bold">{formatCurrency(totalBalance)}</span>
          </CardContent>
        </Card>
      </div>

      {/* Error Message */}
      {session.errorMessage && (
        <Card className="border-destructive">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-destructive">
              <AlertCircle className="h-5 w-5" />
              Error
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-destructive">{session.errorMessage}</p>
          </CardContent>
        </Card>
      )}

      {/* Session Details */}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Calendar className="h-5 w-5" />
              Session Information
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-muted-foreground">Data From</p>
                <p className="font-medium">{format(new Date(session.dataFrom), 'dd MMM yyyy')}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Data To</p>
                <p className="font-medium">{format(new Date(session.dataTo), 'dd MMM yyyy')}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Initiated</p>
                <p className="font-medium">
                  {format(new Date(session.initiatedAt), 'dd MMM yyyy HH:mm')}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Completed</p>
                <p className="font-medium">
                  {session.completedAt
                    ? format(new Date(session.completedAt), 'dd MMM yyyy HH:mm')
                    : '-'}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Database className="h-5 w-5" />
              FI Types Requested
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {session.fiTypesRequested?.map((type) => (
                <Badge key={type} variant="secondary">
                  {type.replace(/_/g, ' ')}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Bank Accounts */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <Building2 className="h-5 w-5" />
            Fetched Bank Accounts
          </CardTitle>
          <CardDescription>Financial accounts retrieved in this session</CardDescription>
        </CardHeader>
        <CardContent>
          {session.bankAccounts?.length === 0 ? (
            <div className="py-12 text-center">
              <CreditCard className="mx-auto mb-4 h-12 w-12 text-muted-foreground" />
              <p className="text-muted-foreground">No accounts fetched yet</p>
              {canFetch && (
                <Button className="mt-4" onClick={handleFetchData} disabled={fetching}>
                  {fetching ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <Download className="mr-2 h-4 w-4" />
                  )}
                  Fetch Data Now
                </Button>
              )}
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Bank</TableHead>
                  <TableHead>Account</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Holder</TableHead>
                  <TableHead className="text-right">Balance</TableHead>
                  <TableHead className="text-right">Transactions</TableHead>
                  <TableHead></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {session.bankAccounts?.map((account) => (
                  <TableRow key={account.id}>
                    <TableCell>
                      <div>
                        <p className="font-medium">{account.bankName}</p>
                        <p className="text-xs text-muted-foreground">{account.fipName}</p>
                      </div>
                    </TableCell>
                    <TableCell className="font-mono text-sm">
                      {account.maskedAccountNumber}
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">{account.accountType}</Badge>
                    </TableCell>
                    <TableCell>{account.holderName}</TableCell>
                    <TableCell className="text-right font-medium">
                      {formatCurrency(account.currentBalance, account.currency)}
                    </TableCell>
                    <TableCell className="text-right">{account.transactionsCount}</TableCell>
                    <TableCell>
                      <Link to={`/admin/lending/aa/fetched-data?account_id=${account.id}`}>
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
    </div>
  );
}
