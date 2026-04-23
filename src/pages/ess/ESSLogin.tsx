/**
 * ESS Portal Login Page
 * OTP-based authentication for employees
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2, Smartphone, Shield, Building2 } from 'lucide-react';
import { essAuthApi } from '@/services/essApi';

type LoginStep = 'mobile' | 'otp';

export default function ESSLogin() {
  const navigate = useNavigate();
  const [step, setStep] = useState<LoginStep>('mobile');
  const [mobile, setMobile] = useState('');
  const [otp, setOtp] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [countdown, setCountdown] = useState(0);

  // Countdown timer for OTP resend
  useEffect(() => {
    if (countdown > 0) {
      const timer = setTimeout(() => setCountdown(countdown - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [countdown]);

  // Check if already logged in
  useEffect(() => {
    const token = localStorage.getItem('ess_access_token');
    if (token) {
      navigate('/ess/dashboard');
    }
  }, [navigate]);

  const handleSendOTP = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Validate mobile number
    const cleanMobile = mobile.replace(/\D/g, '');
    if (cleanMobile.length !== 10) {
      setError('Please enter a valid 10-digit mobile number');
      return;
    }

    setLoading(true);
    try {
      await essAuthApi.sendOtp({ mobile: cleanMobile, purpose: 'LOGIN' });
      setStep('otp');
      setCountdown(60); // 60 seconds cooldown
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to send OTP. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOTP = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (otp.length !== 6) {
      setError('Please enter a valid 6-digit OTP');
      return;
    }

    setLoading(true);
    try {
      const response = await essAuthApi.login({
        mobile: mobile.replace(/\D/g, ''),
        otp,
        device_info: {
          device_type: 'WEB',
          browser: navigator.userAgent,
        },
      });

      // Store tokens
      localStorage.setItem('ess_access_token', response.data.access_token);
      localStorage.setItem('ess_refresh_token', response.data.refresh_token);
      localStorage.setItem('ess_user', JSON.stringify(response.data.user));

      // Navigate to dashboard
      navigate('/ess/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Invalid OTP. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleResendOTP = async () => {
    if (countdown > 0) return;

    setLoading(true);
    setError(null);
    try {
      await essAuthApi.sendOtp({ mobile: mobile.replace(/\D/g, ''), purpose: 'LOGIN' });
      setCountdown(60);
      setOtp('');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to resend OTP');
    } finally {
      setLoading(false);
    }
  };

  const handleBack = () => {
    setStep('mobile');
    setOtp('');
    setError(null);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <div className="w-full max-w-md">
        {/* Logo/Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-600 rounded-2xl mb-4">
            <Building2 className="h-8 w-8 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900">Employee Self Service</h1>
          <p className="text-gray-600 mt-1">Access your HR services anytime, anywhere</p>
        </div>

        <Card className="shadow-xl">
          <CardHeader className="space-y-1">
            <CardTitle className="text-xl">
              {step === 'mobile' ? 'Sign In' : 'Verify OTP'}
            </CardTitle>
            <CardDescription>
              {step === 'mobile'
                ? 'Enter your registered mobile number to receive OTP'
                : `Enter the 6-digit OTP sent to ${mobile.slice(0, 3)}****${mobile.slice(-3)}`}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {error && (
              <Alert variant="destructive" className="mb-4">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            {step === 'mobile' ? (
              <form onSubmit={handleSendOTP} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="mobile">Mobile Number</Label>
                  <div className="relative">
                    <Smartphone className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
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
                <Button type="submit" className="w-full" disabled={loading || !mobile}>
                  {loading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Sending OTP...
                    </>
                  ) : (
                    'Send OTP'
                  )}
                </Button>
              </form>
            ) : (
              <form onSubmit={handleVerifyOTP} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="otp">One-Time Password</Label>
                  <div className="relative">
                    <Shield className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
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
                    onClick={handleBack}
                    className="text-blue-600 hover:underline"
                    disabled={loading}
                  >
                    Change number
                  </button>
                  <button
                    type="button"
                    onClick={handleResendOTP}
                    className={`${
                      countdown > 0 ? 'text-gray-400 cursor-not-allowed' : 'text-blue-600 hover:underline'
                    }`}
                    disabled={countdown > 0 || loading}
                  >
                    {countdown > 0 ? `Resend in ${countdown}s` : 'Resend OTP'}
                  </button>
                </div>

                <Button type="submit" className="w-full" disabled={loading || otp.length !== 6}>
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
            )}
          </CardContent>
        </Card>

        {/* Footer */}
        <div className="text-center mt-6 text-sm text-gray-500">
          <p>
            Having trouble logging in?{' '}
            <a href="#" className="text-blue-600 hover:underline">
              Contact HR
            </a>
          </p>
        </div>
      </div>
    </div>
  );
}
