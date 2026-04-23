/**
 * Account Aggregator Fetch Session Detail Page
 *
 * Full page view for a specific data fetch session.
 * Shows fetched accounts and allows data pull.
 */

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { format } from 'date-fns';
import {
  ArrowLeft,
  RefreshCw,
  Download,
  Play,
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
import { Skeleton } from '@/components/ui/skeleton';
import { useToast } from '@/hooks/use-toast';
import { Progress } from '@/components/ui/progress';

// Types
interface BankAccount {
  id: string;
  fi_type: string;
  fip_name: string;
  masked_account_number: string;
  account_type: string;
  bank_name: string;
  holder_name: string;
  current_balance: number;
  currency: string;
  transactions_count: number;
}

interface FetchSessionDetail {
  id: string;
  consent_id: string;
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
  bank_accounts: BankAccount[];
}

// Status styling
const getStatusBadge = (status: string) => {
  const statusStyles: Record<string, { variant: 'default' | 'secondary' | 'destructive' | 'outline'; icon: React.ReactNode }> = {
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
const formatCurrency = (amount: number, currency: string = 'INR') => {
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

  const [session, setSession] = useState<FetchSessionDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [fetching, setFetching] = useState(false);

  // Fetch session details
  const fetchSessionDetails = async () => {
    try {
      const response = await fetch(`/api/v1/lending/aa/sessions/${sessionId}`);
      if (!response.ok) {
        if (response.status === 404) {
          toast({
            title: 'Session not found',
            description: 'The requested session does not exist.',
            variant: 'destructive',
          });
          navigate(-1);
          return;
        }
        throw new Error('Failed to fetch session details');
      }
      const data = await response.json();
      setSession(data);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load session details.',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSessionDetails();
  }, [sessionId]);

  // Fetch data for session
  const handleFetchData = async () => {
    setFetching(true);
    try {
      const response = await fetch(`/api/v1/lending/aa/sessions/${sessionId}/fetch-data`, {
        method: 'POST',
      });
      if (!response.ok) throw new Error('Failed to fetch data');

      const data = await response.json();
      setSession(data);

      toast({
        title: 'Data fetched',
        description: `Fetched ${data.accounts_count} accounts with ${data.transactions_count} transactions.`,
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to fetch financial data.',
        variant: 'destructive',
      });
    } finally {
      setFetching(false);
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto py-6 space-y-6">
        <Skeleton className="h-8 w-64" />
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Skeleton className="h-24" />
          <Skeleton className="h-24" />
          <Skeleton className="h-24" />
          <Skeleton className="h-24" />
        </div>
        <Skeleton className="h-64" />
      </div>
    );
  }

  if (!session) {
    return (
      <div className="container mx-auto py-6">
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <AlertCircle className="h-12 w-12 text-muted-foreground mb-4" />
            <p className="text-lg font-medium">Session not found</p>
            <Button
              variant="outline"
              className="mt-4"
              onClick={() => navigate(-1)}
            >
              Go Back
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const canFetch = ['READY', 'PARTIAL', 'INITIATED'].includes(session.status);
  const totalBalance = session.bank_accounts?.reduce((sum, acc) => sum + (acc.current_balance || 0), 0) || 0;

  return (
    <div className="container mx-auto py-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => navigate(-1)}
          >
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold">Fetch Session</h1>
            <p className="text-sm text-muted-foreground font-mono">
              {session.session_id}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={fetchSessionDetails}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>

          {canFetch && (
            <Button size="sm" onClick={handleFetchData} disabled={fetching}>
              {fetching ? (
                <>
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                  Fetching...
                </>
              ) : (
                <>
                  <Download className="h-4 w-4 mr-2" />
                  Fetch Data
                </>
              )}
            </Button>
          )}
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Status</CardDescription>
          </CardHeader>
          <CardContent>
            {getStatusBadge(session.status)}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Accounts Fetched</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <CreditCard className="h-5 w-5 text-muted-foreground" />
              <span className="text-2xl font-bold">{session.accounts_count}</span>
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
              <span className="text-2xl font-bold">{session.transactions_count}</span>
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
      {session.error_message && (
        <Card className="border-destructive">
          <CardHeader>
            <CardTitle className="text-destructive flex items-center gap-2">
              <AlertCircle className="h-5 w-5" />
              Error
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-destructive">{session.error_message}</p>
          </CardContent>
        </Card>
      )}

      {/* Session Details */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Calendar className="h-5 w-5" />
              Session Information
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-muted-foreground">Data From</p>
                <p className="font-medium">
                  {format(new Date(session.data_from), 'dd MMM yyyy')}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Data To</p>
                <p className="font-medium">
                  {format(new Date(session.data_to), 'dd MMM yyyy')}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Initiated</p>
                <p className="font-medium">
                  {format(new Date(session.initiated_at), 'dd MMM yyyy HH:mm')}
                </p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Completed</p>
                <p className="font-medium">
                  {session.completed_at
                    ? format(new Date(session.completed_at), 'dd MMM yyyy HH:mm')
                    : '-'}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Database className="h-5 w-5" />
              FI Types Requested
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {session.fi_types_requested?.map((type) => (
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
          <CardTitle className="text-lg flex items-center gap-2">
            <Building2 className="h-5 w-5" />
            Fetched Bank Accounts
          </CardTitle>
          <CardDescription>
            Financial accounts retrieved in this session
          </CardDescription>
        </CardHeader>
        <CardContent>
          {session.bank_accounts?.length === 0 ? (
            <div className="text-center py-12">
              <CreditCard className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <p className="text-muted-foreground">No accounts fetched yet</p>
              {canFetch && (
                <Button className="mt-4" onClick={handleFetchData} disabled={fetching}>
                  <Download className="h-4 w-4 mr-2" />
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
                {session.bank_accounts?.map((account) => (
                  <TableRow key={account.id}>
                    <TableCell>
                      <div>
                        <p className="font-medium">{account.bank_name}</p>
                        <p className="text-xs text-muted-foreground">{account.fip_name}</p>
                      </div>
                    </TableCell>
                    <TableCell className="font-mono text-sm">
                      {account.masked_account_number}
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">{account.account_type}</Badge>
                    </TableCell>
                    <TableCell>{account.holder_name}</TableCell>
                    <TableCell className="text-right font-medium">
                      {formatCurrency(account.current_balance, account.currency)}
                    </TableCell>
                    <TableCell className="text-right">
                      {account.transactions_count}
                    </TableCell>
                    <TableCell>
                      <Link to={`/lending/aa/fetched-data?account_id=${account.id}`}>
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
