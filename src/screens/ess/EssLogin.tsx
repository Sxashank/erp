import {
  BadgeCheck,
  CalendarCheck,
  ClipboardCheck,
  KeyRound,
  ShieldCheck,
  Wallet,
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

const portalHighlights = [
  {
    title: "Leave and attendance",
    detail: "Apply, regularize, track balances",
    icon: CalendarCheck,
  },
  {
    title: "Payslips and tax",
    detail: "Download payslips and Form 16",
    icon: Wallet,
  },
  {
    title: "Requests and approvals",
    detail: "Claims, travel, IT support",
    icon: ClipboardCheck,
  },
];

export function EssLogin() {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <div className="grid min-h-screen lg:grid-cols-[1fr_1fr]">
        <div className="flex flex-col justify-center px-6 py-12 lg:px-12">
          <Badge className="w-fit bg-blue-50 text-blue-700 hover:bg-blue-50">
            Employee self-service portal
          </Badge>
          <h1 className="mt-4 text-3xl font-semibold">
            One place for your daily HR tasks.
          </h1>
          <p className="mt-3 max-w-lg text-sm text-slate-600">
            Access leave, attendance, payroll, reimbursements, and service requests
            without switching tools.
          </p>
          <div className="mt-8 grid gap-4">
            {portalHighlights.map((item) => (
              <div
                key={item.title}
                className="flex items-center gap-3 rounded-xl border border-slate-200 bg-white p-4"
              >
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-50 text-blue-700">
                  <item.icon className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-slate-900">{item.title}</p>
                  <p className="text-xs text-slate-500">{item.detail}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="flex items-center justify-center bg-white px-6 py-12">
          <Card className="w-full max-w-md border-slate-200 shadow-sm">
            <CardHeader>
              <CardTitle className="text-2xl">Sign in to ESS</CardTitle>
              <CardDescription>
                Use your employee ID or registered email.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="employeeId">Employee ID</Label>
                <div className="relative">
                  <Input id="employeeId" placeholder="SMFC-00024" />
                  <BadgeCheck className="pointer-events-none absolute right-3 top-2.5 h-4 w-4 text-slate-400" />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <div className="relative">
                  <Input id="password" type="password" placeholder="Enter password" />
                  <KeyRound className="pointer-events-none absolute right-3 top-2.5 h-4 w-4 text-slate-400" />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="otp">OTP (optional)</Label>
                <Input id="otp" placeholder="6 digit OTP" />
              </div>
              <div className="flex items-center justify-between text-sm">
                <div className="flex items-center space-x-2">
                  <Checkbox id="rememberEss" />
                  <Label htmlFor="rememberEss" className="text-sm text-slate-600">
                    Keep me signed in
                  </Label>
                </div>
                <button className="text-sm font-medium text-blue-600 hover:text-blue-700">
                  Reset password
                </button>
              </div>
            </CardContent>
            <CardFooter className="flex flex-col gap-3">
              <Button className="w-full">Sign in</Button>
              <Button variant="outline" className="w-full">
                Use mobile OTP
              </Button>
              <div className="flex items-center gap-2 text-xs text-slate-500">
                <ShieldCheck className="h-4 w-4 text-blue-600" />
                Protected by SMFC security standards.
              </div>
            </CardFooter>
          </Card>
        </div>
      </div>
    </div>
  );
}
