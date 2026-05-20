import { AlertCircle, CheckCircle, KeyRound, Loader2, Shield } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';

import { PageHeader } from '@/components/common/PageHeader';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { getApiErrorMessage, useRequestGstnOtp, useVerifyGstnOtp } from '@/hooks/tax/useGstn';
import { useGSTRegistrations } from '@/hooks/tax/useTaxation';
import { useActiveOrganizationId } from '@/stores/organizationStore';

export function GstnLogin() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const activeOrganizationId = useActiveOrganizationId();
  const [selectedGstin, setSelectedGstin] = useState(searchParams.get('gstin') || '');
  const [step, setStep] = useState<'select' | 'otp' | 'success'>('select');
  const [otp, setOtp] = useState('');
  const [error, setError] = useState('');
  const [countdown, setCountdown] = useState(0);

  const registrationsQuery = useGSTRegistrations({
    includeInactive: false,
    pageSize: 100,
  });
  const requestOtp = useRequestGstnOtp();
  const verifyOtp = useVerifyGstnOtp();

  const registrations = registrationsQuery.data?.items;
  const selectedRegistration = registrations?.find((registration) => registration.gstin === selectedGstin);

  useEffect(() => {
    if (!selectedGstin && registrations && registrations.length > 0) {
      setSelectedGstin(registrations[0].gstin);
    }
  }, [registrations, selectedGstin]);

  useEffect(() => {
    if (countdown <= 0) {
      return undefined;
    }

    const timer = window.setTimeout(() => setCountdown((current) => current - 1), 1000);
    return () => window.clearTimeout(timer);
  }, [countdown]);

  async function handleRequestOtp() {
    if (!selectedGstin) {
      setError('Please select a GSTIN');
      return;
    }

    setError('');
    try {
      await requestOtp.mutateAsync(selectedGstin);
      setStep('otp');
      setCountdown(60);
    } catch (requestError) {
      setError(getApiErrorMessage(requestError, 'Failed to request OTP. Please try again.'));
    }
  }

  async function handleVerifyOtp() {
    if (otp.length !== 6) {
      setError('Please enter a valid 6-digit OTP');
      return;
    }

    setError('');
    try {
      await verifyOtp.mutateAsync({ gstin: selectedGstin, otp });
      setStep('success');
    } catch (verifyError) {
      setError(getApiErrorMessage(verifyError, 'Invalid OTP. Please try again.'));
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Connect to GSTN Portal"
        subtitle="Authenticate using OTP to access GSTN services"
        breadcrumbs={[{ label: 'GSTN Portal', to: '/admin/gst/gstn' }, { label: 'Connect' }]}
      />

      <div className="mx-auto max-w-md">
        {step === 'select' ? (
          <Card>
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="rounded-lg bg-blue-100 p-2">
                  <Shield className="h-6 w-6 text-blue-600" />
                </div>
                <div>
                  <CardTitle>Select GSTIN</CardTitle>
                  <CardDescription>Choose the GSTIN to connect</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {error ? (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              ) : null}

              <div className="space-y-2">
                <Label htmlFor="gstin">GSTIN</Label>
                <select
                  id="gstin"
                  value={selectedGstin}
                  onChange={(event) => setSelectedGstin(event.target.value)}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                >
                  <option value="">Select GSTIN</option>
                  {registrations?.map((registration) => (
                    <option key={registration.id} value={registration.gstin}>
                      {registration.gstin} - {registration.tradeName || registration.legalName}
                    </option>
                  ))}
                </select>
              </div>

              {selectedRegistration ? (
                <div className="space-y-1 rounded-lg bg-slate-50 p-3">
                  <p className="font-medium">{selectedRegistration.tradeName || selectedRegistration.legalName}</p>
                  <p className="font-mono text-sm text-muted-foreground">{selectedRegistration.gstin}</p>
                </div>
              ) : null}

              <div className="text-sm text-muted-foreground">
                <p>An OTP will be sent to the mobile number registered with GSTN for this GSTIN.</p>
              </div>

                <Button
                  className="w-full"
                  onClick={handleRequestOtp}
                  disabled={!selectedGstin || requestOtp.isPending}
                  data-testid="gstn-request-otp"
                >
                {requestOtp.isPending ? (
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
        ) : null}

        {step === 'otp' ? (
          <Card>
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="rounded-lg bg-amber-100 p-2">
                  <KeyRound className="h-6 w-6 text-amber-600" />
                </div>
                <div>
                  <CardTitle>Enter OTP</CardTitle>
                  <CardDescription>OTP sent to registered mobile for {selectedGstin}</CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {error ? (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              ) : null}

              <div className="space-y-2">
                <Label htmlFor="otp">OTP</Label>
                <Input
                  id="otp"
                  type="text"
                  maxLength={6}
                  placeholder="Enter 6-digit OTP"
                  value={otp}
                  onChange={(event) => setOtp(event.target.value.replace(/\D/g, '').slice(0, 6))}
                  className="text-center font-mono text-2xl tracking-widest"
                  data-testid="gstn-otp-input"
                />
              </div>

              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Did not receive OTP?</span>
                <Button
                  variant="link"
                  size="sm"
                  onClick={handleRequestOtp}
                  disabled={countdown > 0 || requestOtp.isPending}
                  className="h-auto p-0"
                >
                  {countdown > 0 ? `Resend in ${countdown}s` : 'Resend OTP'}
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
                  disabled={otp.length !== 6 || verifyOtp.isPending}
                  data-testid="gstn-verify-otp"
                >
                  {verifyOtp.isPending ? (
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
        ) : null}

        {step === 'success' ? (
          <Card>
            <CardContent className="py-12">
              <div className="space-y-4 text-center">
                <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-green-100">
                  <CheckCircle className="h-8 w-8 text-green-600" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold">Connected Successfully</h3>
                  <p className="mt-1 text-muted-foreground">
                    Your GSTN session is now active for {selectedGstin}
                  </p>
                </div>
                <div className="rounded-lg bg-slate-50 p-3">
                  <p className="text-sm text-muted-foreground">
                    You can now file returns, fetch GSTR-2B data, and perform ITC reconciliation.
                  </p>
                </div>
                <div className="flex gap-3 pt-4">
                  <Button variant="outline" className="flex-1" onClick={() => navigate('/admin/gst/gstn')}>
                    Go to Dashboard
                  </Button>
                  <Button className="flex-1" onClick={() => navigate(`/admin/gst/gstn/gstr1?gstin=${selectedGstin}`)}>
                    Prepare GSTR-1
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ) : null}

        <Card className="mt-6">
          <CardContent className="pt-6">
            <h4 className="mb-2 font-medium">About GSTN Authentication</h4>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li className="flex items-start gap-2">
                <Shield className="mt-0.5 h-4 w-4 text-blue-500" />
                <span>OTP is sent to the mobile number registered with GSTN</span>
              </li>
              <li className="flex items-start gap-2">
                <Shield className="mt-0.5 h-4 w-4 text-blue-500" />
                <span>Session remains active for approximately 6 hours</span>
              </li>
              <li className="flex items-start gap-2">
                <Shield className="mt-0.5 h-4 w-4 text-blue-500" />
                <span>You need to re-authenticate after session expiry</span>
              </li>
            </ul>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default GstnLogin;
