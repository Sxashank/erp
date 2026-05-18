import { Loader2, Mail } from 'lucide-react';
import { useState } from 'react';
import { Link } from 'react-router-dom';

import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  portalAuthApi,
  resolvePortalOrganizationId,
  type PortalForgotPasswordResponse,
} from '@/services/portalApi';
import { getErrorMessage } from "@/lib/errorMessage";

export default function PortalForgotPassword(): JSX.Element {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<PortalForgotPasswordResponse | null>(null);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>): Promise<void> {
    e.preventDefault();
    setError(null);
    setResult(null);

    if (!email.trim()) {
      setError('Email address is required.');
      return;
    }

    setLoading(true);
    try {
      const response = await portalAuthApi.forgotPassword({
        organization_id: resolvePortalOrganizationId(),
        email: email.trim(),
      });
      setResult(response.data);
    } catch (err: unknown) {
      setError(getErrorMessage(err, 'Failed to prepare password reset.'));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-100 via-white to-teal-50 p-4">
      <Card className="w-full max-w-lg shadow-xl">
        <CardHeader className="space-y-3">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-600 text-white">
            <Mail className="h-7 w-7" />
          </div>
          <CardTitle className="text-2xl">Reset internal actor password</CardTitle>
          <CardDescription>
            Use this for lender, SMFCL, ministry, and scheme-admin portal accounts.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {error ? (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          ) : null}

          {result ? (
            <Alert>
              <AlertDescription className="space-y-3">
                <div>{result.message}</div>
                {result.reset_url ? (
                  <div className="break-all text-sm">
                    <span className="font-medium">Reset link:</span> {result.reset_url}
                  </div>
                ) : null}
              </AlertDescription>
            </Alert>
          ) : null}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Official email address</Label>
              <Input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="officer@smfcl.gov.in"
                disabled={loading}
              />
            </div>
            <Button
              type="submit"
              className="w-full bg-emerald-600 hover:bg-emerald-700"
              disabled={loading}
            >
              {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
              Prepare reset link
            </Button>
          </form>

          <div className="text-sm text-slate-600">
            <Link to="/portal/login" className="font-medium text-emerald-700 hover:underline">
              Back to scheme portal sign-in
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
