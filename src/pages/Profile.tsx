import {
  User,
  Mail,
  Phone,
  Building2,
  Shield,
  Clock,
  Loader2,
  Save,
  Key,
  CheckCircle,
} from 'lucide-react';
import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';

import { PageHeader } from '@/components/common/PageHeader';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { authApi } from '@/services/api';

import { logger } from "@/lib/logger";
import { getErrorMessage } from "@/lib/errorMessage";
interface UserProfile {
  id: string;
  username: string;
  email: string;
  full_name: string;
  employee_code?: string;
  phone?: string;
  timezone?: string;
  organization_name?: string;
  default_unit_name?: string;
  roles: { code: string; name: string }[];
  permissions: string[];
  last_login_at?: string;
  mfa_enabled: boolean;
}

interface ChangePasswordForm {
  current_password: string;
  new_password: string;
  confirm_password: string;
}

export function Profile() {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [passwordDialogOpen, setPasswordDialogOpen] = useState(false);
  const [changingPassword, setChangingPassword] = useState(false);
  const [passwordChanged, setPasswordChanged] = useState(false);
  const [passwordError, setPasswordError] = useState('');

  const {
    register,
    handleSubmit,
    watch,
    reset,
    formState: { errors },
  } = useForm<ChangePasswordForm>();

  const newPassword = watch('new_password');

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      setLoading(true);
      const response = await authApi.me();
      setProfile(response.data);
    } catch (error) {
      logger.error('Failed to fetch profile:', error);
    } finally {
      setLoading(false);
    }
  };

  const onChangePassword = async (data: ChangePasswordForm) => {
    try {
      setChangingPassword(true);
      setPasswordError('');
      await authApi.changePassword(data);
      setPasswordChanged(true);
      reset();
      setTimeout(() => {
        setPasswordDialogOpen(false);
        setPasswordChanged(false);
      }, 2000);
    } catch (err: unknown) {
      setPasswordError(getErrorMessage(err, 'Failed to change password'));
    } finally {
      setChangingPassword(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="text-center py-12 text-slate-500">
        Failed to load profile
      </div>
    );
  }

  const changePasswordDialog = (
    <Dialog open={passwordDialogOpen} onOpenChange={setPasswordDialogOpen}>
      <DialogTrigger asChild>
        <Button variant="outline">
          <Key className="mr-2 h-4 w-4" />
          Change Password
        </Button>
      </DialogTrigger>
      <DialogContent>
            <DialogHeader>
              <DialogTitle>Change Password</DialogTitle>
              <DialogDescription>
                Enter your current password and choose a new password
              </DialogDescription>
            </DialogHeader>

            {passwordChanged ? (
              <div className="flex flex-col items-center gap-4 py-6">
                <CheckCircle className="h-12 w-12 text-green-500" />
                <p className="font-medium">Password changed successfully!</p>
              </div>
            ) : (
              <form onSubmit={handleSubmit(onChangePassword)}>
                <div className="space-y-4 py-4">
                  {passwordError && (
                    <div className="rounded-lg bg-red-50 p-3 text-sm text-red-600">
                      {passwordError}
                    </div>
                  )}

                  <div className="space-y-2">
                    <Label htmlFor="current_password">Current Password</Label>
                    <Input
                      id="current_password"
                      type="password"
                      {...register('current_password', {
                        required: 'Current password is required',
                      })}
                      placeholder="Enter current password"
                    />
                    {errors.current_password && (
                      <p className="text-sm text-red-500">{errors.current_password.message}</p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="new_password">New Password</Label>
                    <Input
                      id="new_password"
                      type="password"
                      {...register('new_password', {
                        required: 'New password is required',
                        minLength: {
                          value: 8,
                          message: 'Password must be at least 8 characters',
                        },
                      })}
                      placeholder="Enter new password"
                    />
                    {errors.new_password && (
                      <p className="text-sm text-red-500">{errors.new_password.message}</p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="confirm_password">Confirm New Password</Label>
                    <Input
                      id="confirm_password"
                      type="password"
                      {...register('confirm_password', {
                        required: 'Please confirm your password',
                        validate: (value) =>
                          value === newPassword || 'Passwords do not match',
                      })}
                      placeholder="Confirm new password"
                    />
                    {errors.confirm_password && (
                      <p className="text-sm text-red-500">{errors.confirm_password.message}</p>
                    )}
                  </div>
                </div>
                <DialogFooter>
                  <Button type="button" variant="outline" onClick={() => setPasswordDialogOpen(false)}>
                    Cancel
                  </Button>
                  <Button type="submit" disabled={changingPassword}>
                    {changingPassword && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                    Change Password
                  </Button>
                </DialogFooter>
              </form>
            )}
          </DialogContent>
        </Dialog>
  );

  return (
    <div className="space-y-6">
      <PageHeader
        title="My Profile"
        subtitle="View and manage your account settings"
        actions={changePasswordDialog}
      />

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Personal Information */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <User className="h-5 w-5 text-blue-600" />
              Personal Information
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center gap-3 rounded-lg border border-slate-200 p-4">
              <User className="h-5 w-5 text-slate-400" />
              <div>
                <p className="text-sm text-slate-500">Full Name</p>
                <p className="font-medium">{profile.full_name}</p>
              </div>
            </div>
            <div className="flex items-center gap-3 rounded-lg border border-slate-200 p-4">
              <Mail className="h-5 w-5 text-slate-400" />
              <div>
                <p className="text-sm text-slate-500">Email</p>
                <p className="font-medium">{profile.email}</p>
              </div>
            </div>
            {profile.phone && (
              <div className="flex items-center gap-3 rounded-lg border border-slate-200 p-4">
                <Phone className="h-5 w-5 text-slate-400" />
                <div>
                  <p className="text-sm text-slate-500">Phone</p>
                  <p className="font-medium">{profile.phone}</p>
                </div>
              </div>
            )}
            {profile.employee_code && (
              <div className="flex items-center gap-3 rounded-lg border border-slate-200 p-4">
                <User className="h-5 w-5 text-slate-400" />
                <div>
                  <p className="text-sm text-slate-500">Employee Code</p>
                  <p className="font-medium">{profile.employee_code}</p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Account Information */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="h-5 w-5 text-blue-600" />
              Account Information
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center gap-3 rounded-lg border border-slate-200 p-4">
              <User className="h-5 w-5 text-slate-400" />
              <div>
                <p className="text-sm text-slate-500">Username</p>
                <p className="font-medium">{profile.username}</p>
              </div>
            </div>
            {profile.organization_name && (
              <div className="flex items-center gap-3 rounded-lg border border-slate-200 p-4">
                <Building2 className="h-5 w-5 text-slate-400" />
                <div>
                  <p className="text-sm text-slate-500">Organization</p>
                  <p className="font-medium">{profile.organization_name}</p>
                </div>
              </div>
            )}
            {profile.default_unit_name && (
              <div className="flex items-center gap-3 rounded-lg border border-slate-200 p-4">
                <Building2 className="h-5 w-5 text-slate-400" />
                <div>
                  <p className="text-sm text-slate-500">Default Unit</p>
                  <p className="font-medium">{profile.default_unit_name}</p>
                </div>
              </div>
            )}
            {profile.last_login_at && (
              <div className="flex items-center gap-3 rounded-lg border border-slate-200 p-4">
                <Clock className="h-5 w-5 text-slate-400" />
                <div>
                  <p className="text-sm text-slate-500">Last Login</p>
                  <p className="font-medium">
                    {new Date(profile.last_login_at).toLocaleString()}
                  </p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Roles & Permissions */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="h-5 w-5 text-blue-600" />
              Roles & Permissions
            </CardTitle>
            <CardDescription>Your assigned roles and access permissions</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <p className="text-sm font-medium text-slate-500 mb-2">Assigned Roles</p>
                <div className="flex flex-wrap gap-2">
                  {profile.roles.map((role) => (
                    <span
                      key={role.code}
                      className="inline-flex items-center rounded-full bg-blue-50 px-3 py-1 text-sm font-medium text-blue-700"
                    >
                      {role.name || role.code}
                    </span>
                  ))}
                </div>
              </div>
              <div>
                <p className="text-sm font-medium text-slate-500 mb-2">Permissions</p>
                <div className="flex flex-wrap gap-2">
                  {profile.permissions.slice(0, 20).map((perm) => (
                    <span
                      key={perm}
                      className="inline-flex items-center rounded-full bg-slate-100 px-2 py-1 text-xs font-medium text-slate-600"
                    >
                      {perm}
                    </span>
                  ))}
                  {profile.permissions.length > 20 && (
                    <span className="inline-flex items-center rounded-full bg-slate-100 px-2 py-1 text-xs font-medium text-slate-600">
                      +{profile.permissions.length - 20} more
                    </span>
                  )}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
