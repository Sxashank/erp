import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Shield, KeyRound, CheckCircle, AlertCircle, ArrowLeft, RefreshCw, Loader2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { gstnApi, gstRegistrationsApi } from '@/services/api';
import { useAuth } from '@/contexts/AuthContext';
import { useActiveOrganizationId } from '@/stores/organizationStore';

interface GSTRegistration {
  id: string;
  gstin: string;
  legal_name: string;
  trade_name?: string;
  is_active: boolean;
}

export function GstnLogin() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { user } = useAuth();
  const activeOrganizationId = useActiveOrganizationId();
  const [registrations, setRegistrations] = useState<GSTRegistration[]>([]);
  const [selectedGstin, setSelectedGstin] = useState(searchParams.get('gstin') || '');
  const [step, setStep] = useState<'select' | 'otp' | 'success'>('select');
  const [otp, setOtp] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [otpRequested, setOtpRequested] = useState(false);
  const [countdown, setCountdown] = useState(0);

  useEffect(() => {
    fetchRegistrations();
  }, []);

  useEffect(() => {
    if (countdown > 0) {
      const timer = setTimeout(() => setCountdown(countdown - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [countdown]);

  const fetchRegistrations = async () => {
    try {
      const response = await gstRegistrationsApi.list({
        organization_id: activeOrganizationId ?? undefined,
        include_inactive: false,
      });
      const data = response.data.items || response.data;
      setRegistrations(data);
      if (!selectedGstin && data.length > 0) {
        setSelectedGstin(data[0].gstin);
      }
    } catch (error) {
      console.error('Failed to fetch GST registrations:', error);
    }
  };

  const handleRequestOtp = async () => {
    if (!selectedGstin) {
      setError('Please select a GSTIN');
      return;
    }

    setLoading(true);
    setError('');
    try {
      await gstnApi.requestOtp({ gstin: selectedGstin });
      setOtpRequested(true);
      setStep('otp');
      setCountdown(60);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to request OTP. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOtp = async () => {
    if (!otp || otp.length !== 6) {
      setError('Please enter a valid 6-digit OTP');
      return;
    }

    setLoading(true);
    setError('');
    try {
      await gstnApi.verifyOtp({ gstin: selectedGstin, otp });
      setStep('success');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Invalid OTP. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleResendOtp = async () => {
    if (countdown > 0) return;
    await handleRequestOtp();
  };

  const selectedRegistration = registrations.find(r => r.gstin === selectedGstin);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => navigate('/admin/gst/gstn')}>
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div>
          <h1 className="text-2xl font-semibold">Connect to GSTN Portal</h1>
          <p className="text-muted-foreground">Authenticate using OTP to access GSTN services</p>
        </div>
      </div>

      <div className="max-w-md mx-auto">
        {/* Step: Select GSTIN */}
        {step === 'select' && (
          <Card>
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <Shield className="h-6 w-6 text-blue-600" />
                </div>
                <div>
                  <CardTitle>Select GSTIN</CardTitle>
                  <CardDescription>Choose the GSTIN to connect</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {error && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              <div className="space-y-2">
                <Label htmlFor="gstin">GSTIN</Label>
                <select
                  id="gstin"
                  value={selectedGstin}
                  onChange={(e) => setSelectedGstin(e.target.value)}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                >
                  <option value="">Select GSTIN</option>
                  {registrations.map((reg) => (
                    <option key={reg.id} value={reg.gstin}>
                      {reg.gstin} - {reg.trade_name || reg.legal_name}
                    </option>
                  ))}
                </select>
              </div>

              {selectedRegistration && (
                <div className="p-3 bg-slate-50 rounded-lg space-y-1">
                  <p className="font-medium">{selectedRegistration.trade_name || selectedRegistration.legal_name}</p>
                  <p className="text-sm text-muted-foreground font-mono">{selectedRegistration.gstin}</p>
                </div>
              )}

              <div className="text-sm text-muted-foreground">
                <p>An OTP will be sent to the mobile number registered with GSTN for this GSTIN.</p>
              </div>

              <Button
                className="w-full"
                onClick={handleRequestOtp}
                disabled={!selectedGstin || loading}
              >
                {loading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Requesting OTP...
                  </>
                ) : (
                  <>
                    <KeyRound className="mr-2 h-4 w-4" />
                    Request OTP
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        )}

        {/* Step: Enter OTP */}
        {step === 'otp' && (
          <Card>
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="p-2 bg-amber-100 rounded-lg">
                  <KeyRound className="h-6 w-6 text-amber-600" />
                </div>
                <div>
                  <CardTitle>Enter OTP</CardTitle>
                  <CardDescription>
                    OTP sent to registered mobile for {selectedGstin}
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {error && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              <div className="space-y-2">
                <Label htmlFor="otp">OTP</Label>
                <Input
                  id="otp"
                  type="text"
                  maxLength={6}
                  placeholder="Enter 6-digit OTP"
                  value={otp}
                  onChange={(e) => setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
                  className="text-center text-2xl tracking-widest font-mono"
                />
              </div>

              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">
                  Didn't receive OTP?
                </span>
                <Button
                  variant="link"
                  size="sm"
                  onClick={handleResendOtp}
                  disabled={countdown > 0}
                  className="p-0 h-auto"
                >
                  {countdown > 0 ? (
                    <span>Resend in {countdown}s</span>
                  ) : (
                    <span>Resend OTP</span>
                  )}
                </Button>
              </div>

              <div className="flex gap-3">
                <Button
                  variant="outline"
                  className="flex-1"
                  onClick={() => {
                    setStep('select');
                    setOtp('');
                    setError('');
                  }}
                >
                  Back
                </Button>
                <Button
                  className="flex-1"
                  onClick={handleVerifyOtp}
                  disabled={otp.length !== 6 || loading}
                >
                  {loading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Verifying...
                    </>
                  ) : (
                    'Verify OTP'
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Step: Success */}
        {step === 'success' && (
          <Card>
            <CardContent className="py-12">
              <div className="text-center space-y-4">
                <div className="mx-auto w-16 h-16 bg-green-100 rounded-full flex items-center justify-center">
                  <CheckCircle className="h-8 w-8 text-green-600" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold">Connected Successfully</h3>
                  <p className="text-muted-foreground mt-1">
                    Your GSTN session is now active for {selectedGstin}
                  </p>
                </div>
                <div className="p-3 bg-slate-50 rounded-lg">
                  <p className="text-sm text-muted-foreground">
                    You can now file returns, fetch GSTR-2B data, and perform ITC reconciliation.
                  </p>
                </div>
                <div className="flex gap-3 pt-4">
                  <Button
                    variant="outline"
                    className="flex-1"
                    onClick={() => navigate('/admin/gst/gstn')}
                  >
                    Go to Dashboard
                  </Button>
                  <Button
                    className="flex-1"
                    onClick={() => navigate(`/admin/gst/gstn/gstr1?gstin=${selectedGstin}`)}
                  >
                    Prepare GSTR-1
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Info Card */}
        <Card className="mt-6">
          <CardContent className="pt-6">
            <h4 className="font-medium mb-2">About GSTN Authentication</h4>
            <ul className="text-sm text-muted-foreground space-y-2">
              <li className="flex items-start gap-2">
                <Shield className="h-4 w-4 mt-0.5 text-blue-500" />
                <span>OTP is sent to the mobile number registered with GSTN</span>
              </li>
              <li className="flex items-start gap-2">
                <Shield className="h-4 w-4 mt-0.5 text-blue-500" />
                <span>Session remains active for approximately 6 hours</span>
              </li>
              <li className="flex items-start gap-2">
                <Shield className="h-4 w-4 mt-0.5 text-blue-500" />
                <span>You'll need to re-authenticate after session expiry</span>
              </li>
            </ul>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default GstnLogin;
