import {
  BadgeCheck,
  Building2,
  KeyRound,
  Landmark,
  LayoutGrid,
  LockKeyhole,
  ShieldCheck,
  Users,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

const highlights = [
  {
    title: "Masters and GL",
    detail: "Organization, COA, vouchers",
    icon: Landmark,
  },
  {
    title: "Lending Pipeline",
    detail: "KYC, rating, sanction",
    icon: BadgeCheck,
  },
  {
    title: "Loan Accounting",
    detail: "Disbursements, schedules",
    icon: Building2,
  },
  {
    title: "Treasury and Risk",
    detail: "Borrowings, ALM, risk",
    icon: ShieldCheck,
  },
  {
    title: "HRIS and Payroll",
    detail: "Employees, attendance",
    icon: Users,
  },
  {
    title: "Compliance",
    detail: "Returns, MIS, alerts",
    icon: LayoutGrid,
  },
];

export function AdminLogin() {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <div className="grid min-h-screen lg:grid-cols-[1.1fr_0.9fr]">
        <div className="hidden border-r border-slate-200 bg-white p-12 lg:flex lg:flex-col">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-blue-600 text-white">
              <LockKeyhole className="h-5 w-5" />
            </div>
            <div>
              <p className="text-sm font-semibold text-slate-500">SMFC Ltd</p>
              <h1 className="text-xl font-semibold">Enterprise Resource Platform</h1>
            </div>
          </div>
          <div className="mt-10 space-y-4">
            <Badge className="w-fit bg-blue-50 text-blue-700 hover:bg-blue-50">
              Live modules across lending, treasury, HR, and compliance
            </Badge>
            <p className="text-sm text-slate-600">
              Single console for 10+ operational modules, approvals, and regulatory reporting.
            </p>
          </div>
          <div className="mt-10 grid gap-4">
            {highlights.map((item) => (
              <div
                key={item.title}
                className="flex items-center gap-3 rounded-xl border border-slate-200 bg-slate-50 p-4"
              >
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-white text-blue-700 shadow-sm">
                  <item.icon className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-slate-900">{item.title}</p>
                  <p className="text-xs text-slate-500">{item.detail}</p>
                </div>
              </div>
            ))}
          </div>
          <div className="mt-auto rounded-xl border border-slate-200 bg-slate-50 p-5">
            <div className="flex items-center justify-between text-sm">
              <span className="text-slate-500">System health</span>
              <span className="font-medium text-emerald-600">All services operational</span>
            </div>
            <div className="mt-3 flex items-center justify-between text-sm">
              <span className="text-slate-500">Next payroll cut-off</span>
              <span className="font-medium text-slate-900">25 Jan 2026</span>
            </div>
          </div>
        </div>
        <div className="flex items-center justify-center px-6 py-12">
          <Card className="w-full max-w-md border-slate-200 shadow-sm">
            <CardHeader>
              <CardTitle className="text-2xl">Sign in</CardTitle>
              <CardDescription>
                Access admin and power-user workspaces with approvals.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="org">Organization</Label>
                  <Select>
                    <SelectTrigger id="org">
                      <SelectValue placeholder="SMFC Ltd" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="smfc">SMFC Ltd</SelectItem>
                      <SelectItem value="group">SMFC Group Holdings</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="role">Role</Label>
                  <Select>
                    <SelectTrigger id="role">
                      <SelectValue placeholder="Administrator" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="admin">Administrator</SelectItem>
                      <SelectItem value="finance">Finance Controller</SelectItem>
                      <SelectItem value="ops">Operations User</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="email">Work email or user ID</Label>
                <div className="relative">
                  <Input id="email" placeholder="name@smfc.in" />
                  <KeyRound className="pointer-events-none absolute right-3 top-2.5 h-4 w-4 text-slate-400" />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <div className="relative">
                  <Input id="password" type="password" placeholder="Enter your password" />
                  <LockKeyhole className="pointer-events-none absolute right-3 top-2.5 h-4 w-4 text-slate-400" />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="otp">One-time code</Label>
                <Input id="otp" placeholder="6 digit OTP" />
              </div>
              <div className="flex items-center justify-between text-sm">
                <div className="flex items-center space-x-2">
                  <Checkbox id="remember" />
                  <Label htmlFor="remember" className="text-sm text-slate-600">
                    Remember this device
                  </Label>
                </div>
                <button className="text-sm font-medium text-blue-600 hover:text-blue-700">
                  Forgot password
                </button>
              </div>
            </CardContent>
            <CardFooter className="flex flex-col gap-3">
              <Button className="w-full">Sign in securely</Button>
              <Button variant="outline" className="w-full">
                Use enterprise SSO
              </Button>
              <p className="text-xs text-slate-500">
                By continuing, you agree to the SMFC information security policy.
              </p>
            </CardFooter>
          </Card>
        </div>
      </div>
    </div>
  );
}
