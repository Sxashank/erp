import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import {
  Building2,
  KeyRound,
  Loader2,
  LockKeyhole,
} from 'lucide-react';

import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useAuth } from '@/hooks/useAuth';
import type { LoginRequest } from '@/types';

export function Login() {
  const navigate = useNavigate();
  const { login } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [requiresMfa, setRequiresMfa] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginRequest>();

  const onSubmit = async (data: LoginRequest) => {
    try {
      setLoading(true);
      setError('');
      const { requiresMfa: needsMfa } = await login({
        username: data.username,
        password: data.password,
        otp: data.otp,
      });

      if (needsMfa) {
        setRequiresMfa(true);
        return;
      }

      navigate('/admin');
    } catch (err) {
      const message =
        (err as { response?: { data?: { detail?: string; message?: string } } }).response?.data
          ?.detail ||
        (err as { response?: { data?: { message?: string } } }).response?.data?.message ||
        'Login failed. Please try again.';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="grid min-h-screen lg:grid-cols-2">
        {/* Left Panel - Branding */}
        <div className="hidden items-center justify-center border-r border-slate-200 bg-white p-12 lg:flex">
          <div className="max-w-md">
            <div className="flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-blue-600 text-white">
                <Building2 className="h-6 w-6" />
              </div>
              <div>
                <p className="text-sm font-semibold text-slate-500">SMFC Ltd</p>
                <h1 className="text-2xl font-bold">Enterprise Resource Platform</h1>
              </div>
            </div>

            <div className="mt-10 space-y-4">
              <p className="text-slate-600">
                Single console for managing your organization, users, and access control.
              </p>
            </div>

            <div className="mt-10 space-y-4">
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                <p className="text-sm font-semibold">Masters Management</p>
                <p className="text-sm text-slate-500">
                  Organizations, Units, Departments, Designations
                </p>
              </div>
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                <p className="text-sm font-semibold">User Administration</p>
                <p className="text-sm text-slate-500">
                  User accounts, Roles, Permissions
                </p>
              </div>
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                <p className="text-sm font-semibold">Security Features</p>
                <p className="text-sm text-slate-500">
                  MFA, Role-based access, Audit logging
                </p>
              </div>
            </div>

            <div className="mt-10 rounded-xl border border-slate-200 bg-slate-50 p-5">
              <div className="flex items-center justify-between text-sm">
                <span className="text-slate-500">System Status</span>
                <span className="font-medium text-emerald-600">All services operational</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Panel - Login Form */}
        <div className="flex items-center justify-center px-6 py-12">
          <Card className="w-full max-w-md border-slate-200 shadow-sm">
            <CardHeader>
              <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-blue-600 text-white lg:hidden">
                <Building2 className="h-6 w-6" />
              </div>
              <CardTitle className="text-2xl">Sign in</CardTitle>
              <CardDescription>
                Access the admin console with your credentials
              </CardDescription>
            </CardHeader>
            <form onSubmit={handleSubmit(onSubmit)}>
              <CardContent className="space-y-4">
                {error && (
                  <div className="rounded-lg bg-red-50 p-3 text-sm text-red-600">
                    {error}
                  </div>
                )}

                <div className="space-y-2">
                  <Label htmlFor="username">Username</Label>
                  <div className="relative">
                    <Input
                      id="username"
                      {...register('username', { required: 'Username is required' })}
                      placeholder="Enter your username"
                    />
                    <KeyRound className="pointer-events-none absolute right-3 top-2.5 h-4 w-4 text-slate-400" />
                  </div>
                  {errors.username && (
                    <p className="text-sm text-red-500">{errors.username.message}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="password">Password</Label>
                  <div className="relative">
                    <Input
                      id="password"
                      type="password"
                      {...register('password', { required: 'Password is required' })}
                      placeholder="Enter your password"
                    />
                    <LockKeyhole className="pointer-events-none absolute right-3 top-2.5 h-4 w-4 text-slate-400" />
                  </div>
                  {errors.password && (
                    <p className="text-sm text-red-500">{errors.password.message}</p>
                  )}
                </div>

                {requiresMfa && (
                  <div className="space-y-2">
                    <Label htmlFor="otp">One-time code</Label>
                    <Input
                      id="otp"
                      {...register('otp')}
                      placeholder="Enter 6-digit OTP"
                      maxLength={6}
                    />
                  </div>
                )}

                <div className="flex items-center justify-between text-sm">
                  <div className="flex items-center space-x-2">
                    <Checkbox id="remember" />
                    <Label htmlFor="remember" className="text-sm text-slate-600">
                      Remember this device
                    </Label>
                  </div>
                  <Link
                    to="/forgot-password"
                    className="text-sm font-medium text-blue-600 hover:text-blue-700"
                  >
                    Forgot password?
                  </Link>
                </div>
              </CardContent>
              <CardFooter className="flex flex-col gap-3">
                <Button type="submit" className="w-full" disabled={loading}>
                  {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  Sign in
                </Button>
                <p className="text-xs text-slate-500">
                  By continuing, you agree to the SMFC information security policy.
                </p>
              </CardFooter>
            </form>
          </Card>
        </div>
      </div>
    </div>
  );
}
