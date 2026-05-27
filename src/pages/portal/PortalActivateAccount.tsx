import { KeyRound, Loader2, LockKeyhole, ShieldCheck } from 'lucide-react';
import { useMemo, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';

import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { persistPortalSession, portalAuthApi } from '@/services/portalApi';
import { getErrorMessage } from '@/lib/errorMessage';

export default function PortalActivateAccount(): JSX.Element {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const token = useMemo(() => searchParams.get('token') ?? '', [searchParams]);
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleActivate(e: React.FormEvent<HTMLFormElement>): Promise<void> {
    e.preventDefault();
    setError(null);

    if (!token) {
      setError('Activation token is missing from this link.');
      return;
    }
    if (password.length < 8) {
      setError('Password must be at least 8 characters long.');
      return;
    }
    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    setLoading(true);
    try {
      const response = await portalAuthApi.activateInvite({
        token,
        password,
        device_info: {
          device_type: 'WEB',
          device_name: 'Borrower Portal',
        },
      });
      persistPortalSession(response.data);
      navigate('/portal/workbench');
    } catch (err: unknown) {
      setError(getErrorMessage(err, 'Failed to activate account.'));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-100 via-white to-emerald-50 p-4">
      <Card className="w-full max-w-lg shadow-xl">
        <CardHeader className="space-y-3">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-600 text-white">
            <ShieldCheck className="h-7 w-7" />
          </div>
          <CardTitle className="text-2xl">Activate portal account</CardTitle>
          <CardDescription>Set the password for your authorised SFC portal access.</CardDescription>
        </CardHeader>
        <CardContent>
          {error ? (
            <Alert variant="destructive" className="mb-4">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          ) : null}

          <form onSubmit={handleActivate} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="new-password">New password</Label>
              <div className="relative">
                <Input
                  id="new-password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Create a strong password"
                  className="pr-10"
                  disabled={loading}
                />
                <LockKeyhole className="pointer-events-none absolute right-3 top-2.5 h-4 w-4 text-slate-400" />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="confirm-password">Confirm password</Label>
              <div className="relative">
                <Input
                  id="confirm-password"
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Re-enter the password"
                  className="pr-10"
                  disabled={loading}
                />
                <KeyRound className="pointer-events-none absolute right-3 top-2.5 h-4 w-4 text-slate-400" />
              </div>
            </div>

            <Button
              type="submit"
              className="w-full bg-emerald-600 hover:bg-emerald-700"
              disabled={loading}
            >
              {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
              Activate account
            </Button>
          </form>

          <div className="mt-6 text-sm text-slate-600">
            Already activated?{' '}
            <Link to="/portal/login" className="font-medium text-emerald-700 hover:underline">
              Sign in
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
