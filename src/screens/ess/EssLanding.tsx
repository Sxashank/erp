import {
  Bell,
  CalendarCheck,
  ClipboardCheck,
  Clock,
  FileText,
  HelpCircle,
  MapPin,
  ShieldCheck,
  User,
  Wallet,
} from "lucide-react";

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";

const quickActions = [
  { label: "Apply leave", icon: CalendarCheck },
  { label: "Regularize attendance", icon: Clock },
  { label: "Download payslip", icon: Wallet },
  { label: "Submit reimbursement", icon: ClipboardCheck },
];

const tasks = [
  {
    title: "Upload investment proof",
    due: "Due in 5 days",
    status: "Pending",
  },
  {
    title: "Confirm January attendance",
    due: "Due tomorrow",
    status: "Urgent",
  },
  {
    title: "Complete performance check-in",
    due: "Due in 12 days",
    status: "Scheduled",
  },
];

const announcements = [
  {
    title: "Policy update: hybrid work",
    detail: "New rules effective from Feb 1",
  },
  {
    title: "Medical insurance renewal",
    detail: "Nominee updates open till Jan 30",
  },
  {
    title: "New wellness reimbursement",
    detail: "Up to INR 15,000 annually",
  },
];

export function EssLanding() {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/90 backdrop-blur">
        <div className="flex w-full items-center gap-4 px-6 py-4">
          <div>
            <p className="text-xs font-semibold text-slate-500">Employee self service</p>
            <p className="text-base font-semibold">My HR Workspace</p>
          </div>
          <Separator orientation="vertical" className="h-8" />
          <Select defaultValue="employee">
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Switch portal" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="employee">Employee portal</SelectItem>
              <SelectItem value="borrower">Borrower portal</SelectItem>
              <SelectItem value="vendor">Vendor portal</SelectItem>
            </SelectContent>
          </Select>
          <div className="relative ml-auto hidden w-[220px] items-center md:flex">
            <Input className="pl-3" placeholder="Search requests" />
          </div>
          <Button variant="ghost" size="icon">
            <HelpCircle className="h-5 w-5" />
          </Button>
          <Button variant="ghost" size="icon">
            <Bell className="h-5 w-5" />
          </Button>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="flex items-center gap-2">
                <Avatar className="h-8 w-8">
                  <AvatarImage src="https://placehold.co/80x80" alt="User" />
                  <AvatarFallback>RK</AvatarFallback>
                </Avatar>
                <span className="hidden text-sm font-medium md:inline">R. Kapoor</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-44">
              <DropdownMenuItem>My profile</DropdownMenuItem>
              <DropdownMenuItem>Settings</DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem>Sign out</DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </header>

      <main className="w-full space-y-6 px-6 py-8">
        <section className="grid gap-4 lg:grid-cols-[1.5fr_1fr]">
          <Card className="border-slate-200">
            <CardHeader>
              <CardTitle className="text-xl">Welcome back, Riya</CardTitle>
              <p className="text-sm text-slate-600">
                Your HR essentials at a glance.
              </p>
            </CardHeader>
            <CardContent className="grid gap-3 sm:grid-cols-3">
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                <p className="text-xs text-slate-500">Leave balance</p>
                <p className="mt-2 text-2xl font-semibold text-slate-900">12.5 days</p>
                <p className="mt-1 text-xs text-slate-500">Next holiday Feb 2</p>
              </div>
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                <p className="text-xs text-slate-500">Attendance</p>
                <p className="mt-2 text-2xl font-semibold text-slate-900">94%</p>
                <p className="mt-1 text-xs text-slate-500">1 regularization pending</p>
              </div>
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                <p className="text-xs text-slate-500">Payslip</p>
                <p className="mt-2 text-2xl font-semibold text-slate-900">Jan 2026</p>
                <p className="mt-1 text-xs text-slate-500">Released on Jan 31</p>
              </div>
            </CardContent>
          </Card>

          <Card className="border-slate-200">
            <CardHeader>
              <CardTitle className="text-lg">Quick actions</CardTitle>
            </CardHeader>
            <CardContent className="grid gap-3">
              {quickActions.map((action) => (
                <Button
                  key={action.label}
                  variant="outline"
                  className="justify-start gap-3"
                >
                  <action.icon className="h-4 w-4 text-blue-600" />
                  {action.label}
                </Button>
              ))}
            </CardContent>
          </Card>
        </section>

        <section className="grid gap-4 lg:grid-cols-[1.2fr_1fr]">
          <Card className="border-slate-200">
            <CardHeader>
              <CardTitle className="text-lg">My tasks</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {tasks.map((task) => (
                <div
                  key={task.title}
                  className="flex items-center justify-between rounded-xl border border-slate-200 bg-slate-50 p-4"
                >
                  <div>
                    <p className="text-sm font-semibold text-slate-900">{task.title}</p>
                    <p className="text-xs text-slate-500">{task.due}</p>
                  </div>
                  <Badge
                    className={`text-xs ${
                      task.status === "Urgent"
                        ? "bg-rose-50 text-rose-700 hover:bg-rose-50"
                        : task.status === "Pending"
                        ? "bg-amber-50 text-amber-700 hover:bg-amber-50"
                        : "bg-slate-100 text-slate-600 hover:bg-slate-100"
                    }`}
                  >
                    {task.status}
                  </Badge>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card className="border-slate-200">
            <CardHeader>
              <CardTitle className="text-lg">Today at work</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                <div className="flex items-center gap-2 text-sm font-semibold text-slate-900">
                  <MapPin className="h-4 w-4 text-blue-600" />
                  Bangalore HQ
                </div>
                <p className="mt-1 text-xs text-slate-500">Check-in 9:42 AM</p>
              </div>
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                <div className="flex items-center gap-2 text-sm font-semibold text-slate-900">
                  <Clock className="h-4 w-4 text-blue-600" />
                  Focus hours
                </div>
                <p className="mt-1 text-xs text-slate-500">10:00 AM - 1:00 PM</p>
              </div>
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                <div className="flex items-center gap-2 text-sm font-semibold text-slate-900">
                  <FileText className="h-4 w-4 text-blue-600" />
                  Upcoming review
                </div>
                <p className="mt-1 text-xs text-slate-500">Quarterly check-in on Feb 6</p>
              </div>
            </CardContent>
          </Card>
        </section>

        <section className="grid gap-4 lg:grid-cols-[1.3fr_1fr]">
          <Card className="border-slate-200">
            <CardHeader>
              <CardTitle className="text-lg">Announcements</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {announcements.map((item) => (
                <div
                  key={item.title}
                  className="flex items-start justify-between rounded-xl border border-slate-200 bg-slate-50 p-4"
                >
                  <div>
                    <p className="text-sm font-semibold text-slate-900">{item.title}</p>
                    <p className="text-xs text-slate-500">{item.detail}</p>
                  </div>
                  <Button variant="ghost" size="sm">
                    View
                  </Button>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card className="border-slate-200">
            <CardHeader>
              <CardTitle className="text-lg">Help and compliance</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                <div className="flex items-center gap-2 text-sm font-semibold text-slate-900">
                  <ShieldCheck className="h-4 w-4 text-blue-600" />
                  Security training
                </div>
                <p className="mt-1 text-xs text-slate-500">Complete by Feb 15</p>
              </div>
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                <div className="flex items-center gap-2 text-sm font-semibold text-slate-900">
                  <User className="h-4 w-4 text-blue-600" />
                  HR helpdesk
                </div>
                <p className="mt-1 text-xs text-slate-500">Avg response time 2 hrs</p>
              </div>
            </CardContent>
          </Card>
        </section>
      </main>
    </div>
  );
}
