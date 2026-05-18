/**
 * Scheme Portal Login Page
 * Supports borrower OTP login and invited internal-actor password login.
 */

import { Loader2, Mail, Shield, Smartphone, Wallet } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  persistPortalSession,
  portalAuthApi,
  resolvePortalOrganizationId,
} from '@/services/portalApi';
import { getErrorMessage } from "@/lib/errorMessage";

type LoginMode = 'borrower' | 'internal';
type LoginStep = 'mobile' | 'otp';

export default function PortalLogin(): JSX.Element {
  const navigate = useNavigate();
  const [mode, setMode] = useState<LoginMode>('borrower');
  const [step, setStep] = useState<LoginStep>('mobile');
  const [mobile, setMobile] = useState('');
  const [otp, setOtp] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [internalOtp, setInternalOtp] = useState('');
  const [requiresInternalMfa, setRequiresInternalMfa] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [countdown, setCountdown] = useState(0);

  useEffect(() => {
    if (countdown <= 0) return undefined;
    const timer = setTimeout(() => setCountdown(countdown - 1), 1000);
    return () => clearTimeout(timer);
  }, [countdown]);

  useEffect(() => {
    const token = localStorage.getItem('portal_access_token');
    if (token) {
      navigate('/portal/workbench');
    }
  }, [navigate]);

  function resetMessages(): void {
    setError(null);
  }

  function switchMode(nextMode: LoginMode): void {
    setMode(nextMode);
    setError(null);
    setRequiresInternalMfa(false);
    setInternalOtp('');
  }

  async function handleSendOTP(e: React.FormEvent<HTMLFormElement>): Promise<void> {
    e.preventDefault();
    resetMessages();

    const cleanMobile = mobile.replace(/\D/g, '');
    if (cleanMobile.length !== 10) {
      setError('Please enter a valid 10-digit mobile number');
      return;
    }

    setLoading(true);
    try {
      await portalAuthApi.sendOtp({
        organization_id: resolvePortalOrganizationId(),
        mobile: cleanMobile,
        purpose: 'LOGIN',
      });
      setStep('otp');
      setCountdown(60);
    } catch (err: unknown) {
      setError(getErrorMessage(err, 'Failed to send OTP. Please try again.'));
    } finally {
      setLoading(false);
    }
  }

  async function handleVerifyOTP(e: React.FormEvent<HTMLFormElement>): Promise<void> {
    e.preventDefault();
    resetMessages();

    if (otp.length !== 6) {
      setError('Please enter a valid 6-digit OTP');
      return;
    }

    setLoading(true);
    try {
      const response = await portalAuthApi.login({
        organization_id: resolvePortalOrganizationId(),
        mobile: mobile.replace(/\D/g, ''),
        otp,
        device_info: {
          device_type: 'WEB',
          browser: navigator.userAgent,
        },
      });
      persistPortalSession(response.data);
      navigate('/portal/workbench');
    } catch (err: unknown) {
      setError(getErrorMessage(err, 'Invalid OTP. Please try again.'));
    } finally {
      setLoading(false);
    }
  }

  async function handleResendOTP(): Promise<void> {
    if (countdown > 0) return;

    setLoading(true);
    resetMessages();
    try {
      await portalAuthApi.sendOtp({
        organization_id: resolvePortalOrganizationId(),
        mobile: mobile.replace(/\D/g, ''),
        purpose: 'LOGIN',
      });
      setCountdown(60);
      setOtp('');
    } catch (err: unknown) {
      setError(getErrorMessage(err, 'Failed to resend OTP'));
    } finally {
      setLoading(false);
    }
  }

  async function handleInternalLogin(e: React.FormEvent<HTMLFormElement>): Promise<void> {
    e.preventDefault();
    resetMessages();

    if (!email.trim() || !password) {
      setError('Email and password are required.');
      return;
    }

    setLoading(true);
    try {
      const response = await portalAuthApi.loginWithPassword({
        organization_id: resolvePortalOrganizationId(),
        email: email.trim(),
        password,
        otp: requiresInternalMfa ? internalOtp : undefined,
        device_info: {
          device_type: 'WEB',
          device_name: 'Scheme Portal',
        },
      });

      if (response.data.requires_mfa) {
        setRequiresInternalMfa(true);
        return;
      }

      persistPortalSession(response.data);
      navigate('/portal/workbench');
    } catch (err: unknown) {
      setError(getErrorMessage(err, 'Invalid email or password.'));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-emerald-50 to-teal-100 p-4">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <div className="mb-4 inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-emerald-600">
            <Wallet className="h-8 w-8 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900">Scheme Portal</h1>
          <p className="mt-1 text-gray-600">
            Track institutional maritime and shipyard applications
          </p>
        </div>

        <Card className="shadow-xl">
          <CardHeader className="space-y-3">
            <div className="grid grid-cols-2 gap-2 rounded-xl bg-slate-100 p-1">
              <button
                type="button"
                className={`rounded-lg px-3 py-2 text-sm font-medium transition ${
                  mode === 'borrower' ? 'bg-white text-emerald-700 shadow-sm' : 'text-slate-600'
                }`}
                onClick={() => switchMode('borrower')}
              >
                Borrower OTP
              </button>
              <button
                type="button"
                className={`rounded-lg px-3 py-2 text-sm font-medium transition ${
                  mode === 'internal' ? 'bg-white text-emerald-700 shadow-sm' : 'text-slate-600'
                }`}
                onClick={() => switchMode('internal')}
              >
                Internal user
              </button>
            </div>
            <CardTitle className="text-xl">
              {mode === 'borrower'
                ? step === 'mobile'
                  ? 'Sign In'
                  : 'Verify OTP'
                : 'Sign in to workbench'}
            </CardTitle>
            <CardDescription>
              {mode === 'borrower'
                ? step === 'mobile'
                  ? 'Enter your authorised mobile number to receive an OTP'
                  : `Enter the 6-digit OTP sent to ${mobile.slice(0, 3)}****${mobile.slice(-3)}`
                : 'Use your invited email address and password to access lender, SMFCL, ministry, or scheme-admin queues.'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {error ? (
              <Alert variant="destructive" className="mb-4">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            ) : null}

            {mode === 'borrower' && step === 'mobile' ? (
              <form onSubmit={handleSendOTP} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="mobile">Mobile Number</Label>
                  <div className="relative">
                    <Smartphone className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
                    <Input
                      id="mobile"
                      type="tel"
                      placeholder="Enter 10-digit mobile number"
                      value={mobile}
                      onChange={(e) => setMobile(e.target.value)}
                      className="pl-10"
                      maxLength={10}
                      disabled={loading}
                      autoFocus
                    />
                  </div>
                </div>
                <Button
                  type="submit"
                  className="w-full bg-emerald-600 hover:bg-emerald-700"
                  disabled={loading || !mobile}
                >
                  {loading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Sending OTP...
                    </>
                  ) : (
                    'Send OTP'
                  )}
                </Button>
                <div className="pt-2 text-center text-sm">
                  <span className="text-gray-500">New to the scheme? </span>
                  <Link
                    to="/portal/register"
                    className="font-medium text-emerald-600 hover:underline"
                  >
                    Register your organisation
                  </Link>
                </div>
              </form>
            ) : null}

            {mode === 'borrower' && step === 'otp' ? (
              <form onSubmit={handleVerifyOTP} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="otp">One-Time Password</Label>
                  <div className="relative">
                    <Shield className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
                    <Input
                      id="otp"
                      type="text"
                      placeholder="Enter 6-digit OTP"
                      value={otp}
                      onChange={(e) => setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
                      className="pl-10 text-center text-lg tracking-widest"
                      maxLength={6}
                      disabled={loading}
                      autoFocus
                    />
                  </div>
                </div>

                <div className="flex items-center justify-between text-sm">
                  <button
                    type="button"
                    onClick={() => {
                      setStep('mobile');
                      setOtp('');
                      setError(null);
                    }}
                    className="text-emerald-600 hover:underline"
                    disabled={loading}
                  >
                    Change number
                  </button>
                  <button
                    type="button"
                    onClick={() => void handleResendOTP()}
                    className={
                      countdown > 0
                        ? 'cursor-not-allowed text-gray-400'
                        : 'text-emerald-600 hover:underline'
                    }
                    disabled={countdown > 0 || loading}
                  >
                    {countdown > 0 ? `Resend in ${countdown}s` : 'Resend OTP'}
                  </button>
                </div>

                <Button
                  type="submit"
                  className="w-full bg-emerald-600 hover:bg-emerald-700"
                  disabled={loading || otp.length !== 6}
                >
                  {loading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Verifying...
                    </>
                  ) : (
                    'Verify & Login'
                  )}
                </Button>
              </form>
            ) : null}

            {mode === 'internal' ? (
              <form onSubmit={handleInternalLogin} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="email">Official email address</Label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
                    <Input
                      id="email"
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="officer@smfcl.gov.in"
                      className="pl-10"
                      disabled={loading}
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="password">Password</Label>
                  <Input
                    id="password"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Enter your password"
                    disabled={loading}
                  />
                </div>

                {requiresInternalMfa ? (
                  <div className="space-y-2">
                    <Label htmlFor="internal-otp">Authenticator code</Label>
                    <div className="relative">
                      <Shield className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
                      <Input
                        id="internal-otp"
                        type="text"
                        value={internalOtp}
                        onChange={(e) =>
                          setInternalOtp(e.target.value.replace(/\D/g, '').slice(0, 6))
                        }
                        className="pl-10"
                        placeholder="Enter 6-digit code"
                        maxLength={6}
                        disabled={loading}
                      />
                    </div>
                  </div>
                ) : null}

                <Button
                  type="submit"
                  className="w-full bg-emerald-600 hover:bg-emerald-700"
                  disabled={loading}
                >
                  {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                  {requiresInternalMfa ? 'Verify & sign in' : 'Sign in'}
                </Button>

                <div className="space-y-2 pt-2 text-sm">
                  <div>
                    <Link
                      to="/portal/forgot-password"
                      className="font-medium text-emerald-700 hover:underline"
                    >
                      Forgot password?
                    </Link>
                  </div>
                  <div>
                    <Link
                      to="/portal/activate"
                      className="font-medium text-emerald-700 hover:underline"
                    >
                      Activate invited account
                    </Link>
                  </div>
                </div>
              </form>
            ) : null}
          </CardContent>
        </Card>

        <div className="mt-6 text-center text-sm text-gray-500">
          <p>Use your registered institutional contact to access the scheme workbench.</p>
        </div>
      </div>
    </div>
  );
}
