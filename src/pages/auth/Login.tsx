import { Building2, KeyRound, Loader2, LockKeyhole, Palette } from 'lucide-react';
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate, Link } from 'react-router-dom';

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
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useAppTheme } from '@/contexts/AppThemeContext';
import { useAuth } from '@/hooks/useAuth';
import type { LoginRequest } from '@/types';

export function Login() {
  const navigate = useNavigate();
  const { theme, setTheme, themes } = useAppTheme();
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
    <div className="auth-shell min-h-screen">
      <div className="grid min-h-screen lg:grid-cols-2">
        {/* Left Panel - Branding */}
        <div className="auth-hero hidden items-center justify-center border-r border-white/10 p-12 lg:flex">
          <div className="max-w-md">
            <div className="flex items-center gap-3">
              <div className="app-brand-mark flex h-12 w-12 items-center justify-center rounded-xl">
                <Building2 className="h-6 w-6" />
              </div>
              <div>
                <p className="text-sm font-semibold text-white/70">SMFC Ltd</p>
                <h1 className="text-2xl font-bold text-white">Enterprise Resource Platform</h1>
              </div>
            </div>

            <div className="mt-10 space-y-4">
              <p className="text-white/78">
                A single operating console for lending, finance, tax, compliance, HR, and internal controls.
              </p>
            </div>

            <div className="mt-10 space-y-4">
              <div className="auth-hero-card rounded-xl p-4">
                <p className="text-sm font-semibold text-white">Operations Backbone</p>
                <p className="text-sm text-white/68">
                  Loans, AP/AR, banking, tax, workflow, and audit surfaces in one place.
                </p>
              </div>
              <div className="auth-hero-card rounded-xl p-4">
                <p className="text-sm font-semibold text-white">Structured Control</p>
                <p className="text-sm text-white/68">
                  Role-based access, maker-checker, approval routing, and full traceability.
                </p>
              </div>
              <div className="auth-hero-card rounded-xl p-4">
                <p className="text-sm font-semibold text-white">India-First ERP</p>
                <p className="text-sm text-white/68">
                  Built for NBFC operations with statutory flows, reports, and manual-first control.
                </p>
              </div>
            </div>

            <div className="auth-hero-card mt-10 rounded-xl p-5">
              <div className="flex items-center justify-between text-sm">
                <span className="text-white/62">System Status</span>
                <span className="font-medium text-emerald-200">All services operational</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Panel - Login Form */}
        <div className="auth-form-side relative flex items-center justify-center px-6 py-12">
          <div className="absolute right-6 top-6">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" className="gap-2 bg-white/80 backdrop-blur">
                  <Palette className="h-4 w-4" />
                  Theme
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-72">
                <DropdownMenuLabel>Appearance</DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuRadioGroup
                  value={theme}
                  onValueChange={(value) => setTheme(value as typeof theme)}
                >
                  {themes.map((themeOption) => (
                    <DropdownMenuRadioItem
                      key={themeOption.id}
                      value={themeOption.id}
                      className="items-start gap-3 py-2"
                    >
                      <div className="mt-0.5 flex gap-1.5">
                        {themeOption.swatches.map((swatch, index) => (
                          <span
                            key={`${themeOption.id}-${index}`}
                            className="app-theme-swatch h-3.5 w-3.5 rounded-full"
                            style={{ backgroundColor: swatch }}
                          />
                        ))}
                      </div>
                      <div className="min-w-0">
                        <div className="font-medium text-slate-900">{themeOption.label}</div>
                        <div className="text-xs leading-5 text-slate-500">
                          {themeOption.description}
                        </div>
                      </div>
                    </DropdownMenuRadioItem>
                  ))}
                </DropdownMenuRadioGroup>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>

          <Card className="auth-form-card w-full max-w-md shadow-none">
            <CardHeader>
              <div className="app-brand-mark mb-4 flex h-12 w-12 items-center justify-center rounded-xl lg:hidden">
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
                  <div className="rounded-lg bg-red-50 p-3 text-sm text-red-600">{error}</div>
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
                    className="auth-link text-sm font-medium"
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
