/**
 * Vendor Portal Login Page
 */

import { Building2, Mail, Lock, Loader2, ArrowLeft, KeyRound } from 'lucide-react';
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/hooks/use-toast';
import { vendorAuthApi } from '@/services/vendorApi';
import { getErrorMessage } from "@/lib/errorMessage";

type LoginStep = 'credentials' | 'otp';
type LoginMethod = 'password' | 'otp';

export default function VendorLogin() {
  const navigate = useNavigate();
  const { toast } = useToast();

  const [loginMethod, setLoginMethod] = useState<LoginMethod>('password');
  const [step, setStep] = useState<LoginStep>('credentials');
  const [loading, setLoading] = useState(false);
  const [countdown, setCountdown] = useState(0);

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [otp, setOtp] = useState('');

  // Check if already logged in
  useEffect(() => {
    const token = localStorage.getItem('vendor_access_token');
    if (token) {
      navigate('/vendor/dashboard');
    }
  }, [navigate]);

  // OTP countdown timer
  useEffect(() => {
    if (countdown > 0) {
      const timer = setTimeout(() => setCountdown(countdown - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [countdown]);

  const handleRequestOtp = async () => {
    if (!email) {
      toast({ variant: 'destructive', title: 'Please enter your email' });
      return;
    }

    setLoading(true);
    try {
      await vendorAuthApi.requestOtp({ email, purpose: 'LOGIN' });
      setStep('otp');
      setCountdown(60);
      toast({ title: 'OTP Sent', description: 'Please check your email for the OTP' });
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } } };
      toast({
        variant: 'destructive',
        title: 'Failed to send OTP',
        description: getErrorMessage(err, 'Please try again'),
      });
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      toast({ variant: 'destructive', title: 'Please enter email and password' });
      return;
    }

    setLoading(true);
    try {
      const response = await vendorAuthApi.login({ email, password });
      const { access_token, refresh_token, user } = response.data;

      localStorage.setItem('vendor_access_token', access_token);
      localStorage.setItem('vendor_refresh_token', refresh_token);
      localStorage.setItem('vendor_user', JSON.stringify(user));

      toast({ title: 'Login Successful', description: `Welcome back, ${user.first_name}!` });
      navigate('/vendor/dashboard');
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } } };
      toast({
        variant: 'destructive',
        title: 'Login Failed',
        description: getErrorMessage(err, 'Invalid credentials'),
      });
    } finally {
      setLoading(false);
    }
  };

  const handleOtpLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !otp) {
      toast({ variant: 'destructive', title: 'Please enter email and OTP' });
      return;
    }

    setLoading(true);
    try {
      const response = await vendorAuthApi.login({ email, otp });
      const { access_token, refresh_token, user } = response.data;

      localStorage.setItem('vendor_access_token', access_token);
      localStorage.setItem('vendor_refresh_token', refresh_token);
      localStorage.setItem('vendor_user', JSON.stringify(user));

      toast({ title: 'Login Successful', description: `Welcome back, ${user.first_name}!` });
      navigate('/vendor/dashboard');
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } } };
      toast({
        variant: 'destructive',
        title: 'Login Failed',
        description: getErrorMessage(err, 'Invalid OTP'),
      });
    } finally {
      setLoading(false);
    }
  };

  const handleResendOtp = async () => {
    if (countdown > 0) return;
    await handleRequestOtp();
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-white flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo/Branding */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-purple-600 text-white mb-4">
            <Building2 className="h-8 w-8" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900">Vendor Portal</h1>
          <p className="text-gray-600 mt-1">Access your vendor dashboard</p>
        </div>

        <Card className="shadow-lg">
          <CardHeader className="space-y-1">
            <CardTitle className="text-xl">Sign In</CardTitle>
            <CardDescription>
              Enter your credentials to access the vendor portal
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Tabs value={loginMethod} onValueChange={(v) => { setLoginMethod(v as LoginMethod); setStep('credentials'); setOtp(''); }}>
              <TabsList className="grid w-full grid-cols-2 mb-4">
                <TabsTrigger value="password">Password</TabsTrigger>
                <TabsTrigger value="otp">OTP</TabsTrigger>
              </TabsList>

              {/* Password Login */}
              <TabsContent value="password">
                <form onSubmit={handlePasswordLogin} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="email">Email</Label>
                    <div className="relative">
                      <Mail className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                      <Input
                        id="email"
                        type="email"
                        placeholder="vendor@example.com"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        className="pl-10"
                        required
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="password">Password</Label>
                    <div className="relative">
                      <Lock className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                      <Input
                        id="password"
                        type="password"
                        placeholder="Enter your password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        className="pl-10"
                        required
                      />
                    </div>
                  </div>

                  <Button type="submit" className="w-full bg-purple-600 hover:bg-purple-700" disabled={loading}>
                    {loading ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Signing in...
                      </>
                    ) : (
                      'Sign In'
                    )}
                  </Button>
                </form>
              </TabsContent>

              {/* OTP Login */}
              <TabsContent value="otp">
                {step === 'credentials' ? (
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="otp-email">Email</Label>
                      <div className="relative">
                        <Mail className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                        <Input
                          id="otp-email"
                          type="email"
                          placeholder="vendor@example.com"
                          value={email}
                          onChange={(e) => setEmail(e.target.value)}
                          className="pl-10"
                          required
                        />
                      </div>
                    </div>

                    <Button
                      type="button"
                      className="w-full bg-purple-600 hover:bg-purple-700"
                      disabled={loading}
                      onClick={handleRequestOtp}
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
                  </div>
                ) : (
                  <form onSubmit={handleOtpLogin} className="space-y-4">
                    <Button
                      type="button"
                      variant="ghost"
                      className="mb-2 -ml-2"
                      onClick={() => { setStep('credentials'); setOtp(''); }}
                    >
                      <ArrowLeft className="mr-2 h-4 w-4" />
                      Change Email
                    </Button>

                    <div className="p-3 bg-gray-50 rounded-lg">
                      <p className="text-sm text-gray-600">OTP sent to:</p>
                      <p className="font-medium">{email}</p>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="otp">Enter OTP</Label>
                      <div className="relative">
                        <KeyRound className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                        <Input
                          id="otp"
                          type="text"
                          placeholder="Enter 6-digit OTP"
                          value={otp}
                          onChange={(e) => setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
                          className="pl-10 text-center text-lg tracking-widest"
                          maxLength={6}
                          required
                        />
                      </div>
                    </div>

                    <Button type="submit" className="w-full bg-purple-600 hover:bg-purple-700" disabled={loading || otp.length !== 6}>
                      {loading ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          Verifying...
                        </>
                      ) : (
                        'Verify & Sign In'
                      )}
                    </Button>

                    <div className="text-center">
                      <Button
                        type="button"
                        variant="link"
                        className="text-purple-600"
                        disabled={countdown > 0}
                        onClick={handleResendOtp}
                      >
                        {countdown > 0 ? `Resend OTP in ${countdown}s` : 'Resend OTP'}
                      </Button>
                    </div>
                  </form>
                )}
              </TabsContent>
            </Tabs>

            <div className="mt-6 text-center text-sm text-gray-600">
              <p>
                New vendor?{' '}
                <a href="/vendor/register" className="text-purple-600 hover:underline font-medium">
                  Register here
                </a>
              </p>
            </div>
          </CardContent>
        </Card>

        <p className="text-center text-sm text-gray-500 mt-6">
          &copy; {new Date().getFullYear()} TalentFino ERP. All rights reserved.
        </p>
      </div>
    </div>
  );
}
