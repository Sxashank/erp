/**
 * Borrower Portal - Borrower Registration
 *
 * 2-step wizard:
 *   1. Borrower verification via organisation ID or existing loan
 *   2. OTP verification
 *
 * After verification a status panel polls /portal/auth/registration-status
 * (CLAUDE.md §5.1 / §5.3: shadcn `<Form>` + RHF + zod, no inline tables /
 * status badges / form elements; per CLAUDE.md §1 we onboard ORGANISATIONS
 * — never individuals — so no AADHAAR field exists here).
 */

import { zodResolver } from '@hookform/resolvers/zod';
import { Building2, CheckCircle2, Clock, Loader2, ShieldAlert, Wallet } from 'lucide-react';
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { Link } from 'react-router-dom';

import { PageHeader } from '@/components/common/PageHeader';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import {
  useRegistrationStatus,
  useStartRegistration,
  useVerifyRegistrationOtp,
} from '@/hooks/portal/useRegistration';
import { useToast } from '@/hooks/use-toast';
import { showErrorToast } from '@/lib/errorToast';
import {
  type RegistrationStartInput,
  type OtpVerifyInput,
  registrationStartSchema,
  otpVerifySchema,
} from '@/schemas/portal/registrationSchema';

type RegistrationStage = 'details' | 'otp' | 'status';

const ID_OPTIONS: { value: RegistrationStartInput['idType']; label: string; placeholder: string }[] = [
  { value: 'cin', label: 'CIN', placeholder: 'L12345AB6789CDE123456' },
  { value: 'gstin', label: 'GSTIN', placeholder: '22ABCDE1234F1Z5' },
  { value: 'llpin', label: 'LLPIN', placeholder: 'AAB-1234' },
  { value: 'pan', label: 'PAN (Org)', placeholder: 'ABCDE1234F' },
];

export default function PortalRegister(): JSX.Element {
  const { toast } = useToast();
  const [stage, setStage] = useState<RegistrationStage>('details');
  const [registrationReference, setRegistrationReference] = useState<string | null>(null);
  const [maskedMobile, setMaskedMobile] = useState<string | null>(null);
  const [mobileForStatus, setMobileForStatus] = useState<string | null>(null);
  const [verifyResult, setVerifyResult] = useState<{
    autoApproved: boolean;
    registrationStatus: 'PENDING_APPROVAL' | 'ACTIVE';
  } | null>(null);

  const detailsForm = useForm<RegistrationStartInput>({
    resolver: zodResolver(registrationStartSchema),
    defaultValues: {
      registrationMode: 'organizationIdentity',
      idType: 'cin',
      idValue: '',
      loanAccountNumber: '',
      sanctionedAmount: '',
      authorizedSignatoryName: '',
      mobile: '+91',
      email: '',
    },
    mode: 'onBlur',
  });

  const otpForm = useForm<OtpVerifyInput>({
    resolver: zodResolver(otpVerifySchema),
    defaultValues: { otp: '' },
    mode: 'onBlur',
  });

  const startRegistration = useStartRegistration();
  const verifyOtp = useVerifyRegistrationOtp();
  const statusQuery = useRegistrationStatus(
    stage === 'status' ? registrationReference : null,
    stage === 'status' ? mobileForStatus : null,
  );

  const onSubmitDetails = detailsForm.handleSubmit(async (values) => {
    try {
      const idValue = (values.idValue ?? '').toUpperCase();
      const body = {
        authorizedSignatoryName: values.authorizedSignatoryName,
        mobile: values.mobile,
        email: values.email,
        ...(values.registrationMode === 'organizationIdentity'
          ? {
              ...(values.idType === 'cin' ? { cin: idValue } : {}),
              ...(values.idType === 'gstin' ? { gstin: idValue } : {}),
              ...(values.idType === 'llpin' ? { llpin: idValue } : {}),
              ...(values.idType === 'pan' ? { pan: idValue } : {}),
            }
          : {
              loanAccountNumber: (values.loanAccountNumber ?? '').trim().toUpperCase(),
              sanctionedAmount: (values.sanctionedAmount ?? '').trim(),
            }),
      };
      const res = await startRegistration.mutateAsync(body);
      setRegistrationReference(res.registrationReference);
      setMaskedMobile(res.maskedMobile);
      setMobileForStatus(values.mobile);
      setStage('otp');
      toast({
        title: 'OTP sent',
        description: `We have sent a 6-digit OTP to ${res.maskedMobile}.`,
      });
    } catch (err) {
      showErrorToast(err, toast);
    }
  });

  const onSubmitOtp = otpForm.handleSubmit(async (values) => {
    if (!registrationReference) return;
    try {
      const res = await verifyOtp.mutateAsync({
        registrationReference,
        otp: values.otp,
      });
      setVerifyResult({
        autoApproved: res.autoApproved,
        registrationStatus: res.registrationStatus,
      });
      setStage('status');
    } catch (err) {
      showErrorToast(err, toast);
    }
  });

  const currentStatus =
    statusQuery.data?.registrationStatus ?? verifyResult?.registrationStatus ?? 'PENDING_APPROVAL';

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-emerald-50 to-teal-100 p-4">
      <div className="w-full max-w-2xl">
        <div className="mb-6 text-center">
          <div className="mb-3 inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-600">
            <Wallet className="h-7 w-7 text-white" />
          </div>
          <PageHeader
            title="Register your organisation"
            subtitle="Onboard your institutional organisation to apply for SFC maritime and shipyard funding."
            className="items-center text-center"
          />
        </div>

        {stage === 'details' && (
          <Card className="shadow-xl">
            <CardHeader>
              <CardTitle>Borrower verification</CardTitle>
              <CardDescription>
                Register using your organisation identifier or validate against an existing loan
                account already seeded by SFC. We will send an OTP to the registered mobile number.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Form {...detailsForm}>
                <form className="space-y-6" onSubmit={onSubmitDetails}>
                  <FormField
                    control={detailsForm.control}
                    name="registrationMode"
                    render={({ field }) => (
                      <FormItem className="space-y-3">
                        <FormLabel>Registration path</FormLabel>
                        <FormControl>
                          <RadioGroup
                            value={field.value}
                            onValueChange={(value) =>
                              field.onChange(value as RegistrationStartInput['registrationMode'])
                            }
                            className="grid gap-3 md:grid-cols-2"
                          >
                            <label
                              htmlFor="mode-organization-identity"
                              className="flex cursor-pointer items-start gap-3 rounded-md border p-3 hover:bg-muted"
                            >
                              <RadioGroupItem
                                value="organizationIdentity"
                                id="mode-organization-identity"
                              />
                              <span className="space-y-1">
                                <span className="block text-sm font-medium">
                                  Organisation identifier
                                </span>
                                <span className="block text-xs text-muted-foreground">
                                  Use CIN, GSTIN, LLPIN, or organisation PAN.
                                </span>
                              </span>
                            </label>
                            <label
                              htmlFor="mode-existing-loan"
                              className="flex cursor-pointer items-start gap-3 rounded-md border p-3 hover:bg-muted"
                            >
                              <RadioGroupItem value="existingLoan" id="mode-existing-loan" />
                              <span className="space-y-1">
                                <span className="block text-sm font-medium">Existing loan</span>
                                <span className="block text-xs text-muted-foreground">
                                  Validate with loan account number and sanctioned amount.
                                </span>
                              </span>
                            </label>
                          </RadioGroup>
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  {detailsForm.watch('registrationMode') === 'organizationIdentity' ? (
                    <>
                  <FormField
                    control={detailsForm.control}
                    name="idType"
                    render={({ field }) => (
                      <FormItem className="space-y-3">
                        <FormLabel>Identifier type</FormLabel>
                        <FormControl>
                          <RadioGroup
                            value={field.value}
                            onValueChange={(v) =>
                              field.onChange(v as RegistrationStartInput['idType'])
                            }
                            className="grid grid-cols-2 gap-2 md:grid-cols-4"
                          >
                            {ID_OPTIONS.map((opt) => (
                              <label
                                key={opt.value}
                                htmlFor={`id-${opt.value}`}
                                className="flex cursor-pointer items-center gap-2 rounded-md border p-2 hover:bg-muted"
                              >
                                <RadioGroupItem value={opt.value} id={`id-${opt.value}`} />
                                <span className="text-sm font-medium">{opt.label}</span>
                              </label>
                            ))}
                          </RadioGroup>
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={detailsForm.control}
                    name="idValue"
                    render={({ field }) => {
                      const selected = detailsForm.watch('idType');
                      const placeholder =
                        ID_OPTIONS.find((o) => o.value === selected)?.placeholder ?? '';
                      return (
                        <FormItem>
                          <FormLabel>Identifier value</FormLabel>
                          <FormControl>
                            <Input
                              {...field}
                              placeholder={placeholder}
                              autoCapitalize="characters"
                              spellCheck={false}
                            />
                          </FormControl>
                          <FormDescription>
                            We accept only organisation-level identifiers issued by Indian
                            regulators.
                          </FormDescription>
                          <FormMessage />
                        </FormItem>
                      );
                    }}
                  />
                    </>
                  ) : (
                    <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                      <FormField
                        control={detailsForm.control}
                        name="loanAccountNumber"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Loan account number</FormLabel>
                            <FormControl>
                              <Input
                                {...field}
                                placeholder="SMFC/LA/2026/00001"
                                autoCapitalize="characters"
                                spellCheck={false}
                              />
                            </FormControl>
                            <FormDescription>
                              Use the exact loan account number issued by SFC.
                            </FormDescription>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                      <FormField
                        control={detailsForm.control}
                        name="sanctionedAmount"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Sanctioned amount</FormLabel>
                            <FormControl>
                              <Input
                                {...field}
                                inputMode="decimal"
                                placeholder="2500000.00"
                                onChange={(e) =>
                                  field.onChange(
                                    e.target.value.replace(/[^0-9.]/g, '').replace(/(\..*)\./g, '$1'),
                                  )
                                }
                              />
                            </FormControl>
                            <FormDescription>
                              Enter the sanctioned loan amount exactly as per sanction/loan advice.
                            </FormDescription>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                    </div>
                  )}

                  <FormField
                    control={detailsForm.control}
                    name="authorizedSignatoryName"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Authorised signatory name</FormLabel>
                        <FormControl>
                          <Input {...field} placeholder="As per board resolution" />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                    <FormField
                      control={detailsForm.control}
                      name="mobile"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Authorised mobile</FormLabel>
                          <FormControl>
                            <Input
                              {...field}
                              type="tel"
                              inputMode="tel"
                              placeholder="+91XXXXXXXXXX"
                              onChange={(e) => {
                                const v = e.target.value;
                                field.onChange(
                                  v.startsWith('+91')
                                    ? v
                                    : `+91${v.replace(/\+91/, '').replace(/[^\d]/g, '')}`,
                                );
                              }}
                            />
                          </FormControl>
                          <FormDescription>
                            We send the OTP to this number; the +91 prefix is locked.
                          </FormDescription>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                    <FormField
                      control={detailsForm.control}
                      name="email"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Corporate email</FormLabel>
                          <FormControl>
                            <Input {...field} type="email" placeholder="signatory@example.com" />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                  </div>

                  <div className="flex flex-col-reverse gap-3 pt-2 sm:flex-row sm:items-center sm:justify-between">
                    <Link to="/portal/login" className="text-sm text-emerald-700 hover:underline">
                      Already registered? Sign in
                    </Link>
                    <Button
                      type="submit"
                      className="bg-emerald-600 hover:bg-emerald-700"
                      disabled={startRegistration.isPending}
                    >
                      {startRegistration.isPending ? (
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      ) : (
                        <Building2 className="mr-2 h-4 w-4" />
                      )}
                      Send OTP
                    </Button>
                  </div>
                </form>
              </Form>
            </CardContent>
          </Card>
        )}

        {stage === 'otp' && (
          <Card className="shadow-xl">
            <CardHeader>
              <CardTitle>Verify OTP</CardTitle>
              <CardDescription>
                Enter the 6-digit OTP sent to <span className="font-medium">{maskedMobile}</span>.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Form {...otpForm}>
                <form className="space-y-6" onSubmit={onSubmitOtp}>
                  <FormField
                    control={otpForm.control}
                    name="otp"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>One-time password</FormLabel>
                        <FormControl>
                          <Input
                            {...field}
                            inputMode="numeric"
                            maxLength={6}
                            placeholder="6-digit OTP"
                            onChange={(e) =>
                              field.onChange(e.target.value.replace(/[^\d]/g, '').slice(0, 6))
                            }
                          />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <div className="flex flex-col-reverse gap-3 pt-2 sm:flex-row sm:items-center sm:justify-between">
                    <Button
                      type="button"
                      variant="ghost"
                      onClick={() => setStage('details')}
                      disabled={verifyOtp.isPending}
                    >
                      Change details
                    </Button>
                    <Button
                      type="submit"
                      className="bg-emerald-600 hover:bg-emerald-700"
                      disabled={verifyOtp.isPending}
                    >
                      {verifyOtp.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                      Verify
                    </Button>
                  </div>
                </form>
              </Form>
            </CardContent>
          </Card>
        )}

        {stage === 'status' && (
          <Card className="shadow-xl">
            <CardHeader>
              <CardTitle>Registration status</CardTitle>
              <CardDescription>
                Reference <span className="font-mono">{registrationReference ?? '—'}</span>
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {currentStatus === 'ACTIVE' && (
                <Alert>
                  <CheckCircle2 className="h-4 w-4" />
                  <AlertTitle>Your organisation is approved</AlertTitle>
                  <AlertDescription>
                    You can now sign in and start a loan application.
                  </AlertDescription>
                </Alert>
              )}
              {currentStatus === 'PENDING_APPROVAL' && (
                <Alert>
                  <Clock className="h-4 w-4" />
                  <AlertTitle>Awaiting approval</AlertTitle>
                  <AlertDescription>
                    Our operations team is reviewing your registration. This page refreshes
                    automatically every 30 seconds; you can safely close this window. We will
                    notify the registered mobile number and email address once you are approved.
                  </AlertDescription>
                </Alert>
              )}
              {currentStatus === 'REJECTED' && (
                <Alert variant="destructive">
                  <ShieldAlert className="h-4 w-4" />
                  <AlertTitle>Registration rejected</AlertTitle>
                  <AlertDescription>
                    {statusQuery.data?.rejectionReason ?? 'Please contact support for assistance.'}
                  </AlertDescription>
                </Alert>
              )}

              <div className="flex justify-end gap-2">
                <Link to="/portal/login">
                  <Button
                    variant={currentStatus === 'ACTIVE' ? 'default' : 'outline'}
                    className={
                      currentStatus === 'ACTIVE' ? 'bg-emerald-600 hover:bg-emerald-700' : undefined
                    }
                  >
                    {currentStatus === 'ACTIVE' ? 'Sign in' : 'Back to sign in'}
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
