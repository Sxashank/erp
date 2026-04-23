import {
  Activity,
  BadgeCheck,
  Bell,
  Building2,
  ClipboardList,
  FileText,
  HelpCircle,
  Landmark,
  LayoutGrid,
  LineChart,
  Search,
  Settings,
  ShieldCheck,
  TrendingUp,
  Users,
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
  DropdownMenuLabel,
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

const modules = [
  {
    name: "Masters and GL",
    summary: "Org, users, COA, vouchers",
    icon: Landmark,
    status: "Live",
  },
  {
    name: "Lending Masters",
    summary: "Borrower, KYC, rating",
    icon: BadgeCheck,
    status: "Live",
  },
  {
    name: "Loan Origination",
    summary: "Application, appraisal, sanction",
    icon: FileText,
    status: "In review",
  },
  {
    name: "Loan Accounting",
    summary: "Disbursement, schedules",
    icon: Activity,
    status: "Live",
  },
  {
    name: "Receipts and NPA",
    summary: "Receipts, NPA, legal",
    icon: ClipboardList,
    status: "Live",
  },
  {
    name: "Treasury and Risk",
    summary: "Borrowings, ALM, risk",
    icon: LineChart,
    status: "Live",
  },
  {
    name: "HRIS and Payroll",
    summary: "Employee, leave, payroll",
    icon: Users,
    status: "Live",
  },
  {
    name: "Fixed Assets and Tax",
    summary: "FA, TDS, GST, BRS",
    icon: Wallet,
    status: "Live",
  },
  {
    name: "Compliance and MIS",
    summary: "Returns, dashboards",
    icon: ShieldCheck,
    status: "Live",
  },
  {
    name: "Portals and Inventory",
    summary: "Borrower, vendor, DMS",
    icon: LayoutGrid,
    status: "Planned",
  },
];

const quickActions = [
  { label: "New voucher", icon: Landmark },
  { label: "Create loan", icon: FileText },
  { label: "Post receipt", icon: ClipboardList },
  { label: "Run payroll", icon: Users },
];

const workQueue = [
  {
    title: "Voucher approvals",
    detail: "12 pending at level 2",
    meta: "Finance",
  },
  {
    title: "Loan sanction memos",
    detail: "5 awaiting committee",
    meta: "Credit",
  },
  {
    title: "KYC document review",
    detail: "8 files expiring",
    meta: "Compliance",
  },
  {
    title: "Treasury drawdown",
    detail: "3 borrowings to confirm",
    meta: "Treasury",
  },
];

export function AdminLanding() {
  return (
    <div className="flex min-h-screen flex-col bg-slate-50 text-slate-900">
      <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/90 backdrop-blur">
        <div className="flex w-full items-center gap-4 px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-600 text-white">
              <Building2 className="h-5 w-5" />
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-500">SMFC ERP</p>
              <p className="text-sm font-semibold">Enterprise Command Center</p>
            </div>
          </div>
          <Separator orientation="vertical" className="h-8" />
          <div className="hidden items-center gap-2 md:flex">
            <Select defaultValue="masters">
              <SelectTrigger className="w-[220px]">
                <SelectValue placeholder="Switch module" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="masters">Masters and GL</SelectItem>
                <SelectItem value="lending">Lending Masters</SelectItem>
                <SelectItem value="origination">Loan Origination</SelectItem>
                <SelectItem value="accounting">Loan Accounting</SelectItem>
                <SelectItem value="npa">Receipts and NPA</SelectItem>
                <SelectItem value="treasury">Treasury and Risk</SelectItem>
                <SelectItem value="hris">HRIS and Payroll</SelectItem>
                <SelectItem value="fa">Fixed Assets and Tax</SelectItem>
                <SelectItem value="compliance">Compliance and MIS</SelectItem>
                <SelectItem value="portals">Portals and Inventory</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="relative ml-auto hidden w-[320px] items-center md:flex">
            <Search className="absolute left-3 h-4 w-4 text-slate-400" />
            <Input className="pl-9" placeholder="Search modules, vouchers, loan IDs" />
          </div>
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="icon">
              <HelpCircle className="h-5 w-5" />
            </Button>
            <Button variant="ghost" size="icon">
              <Bell className="h-5 w-5" />
            </Button>
            <Button variant="ghost" size="icon">
              <Settings className="h-5 w-5" />
            </Button>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="flex items-center gap-2">
                  <Avatar className="h-8 w-8">
                    <AvatarImage src="https://placehold.co/80x80" alt="User" />
                    <AvatarFallback>AV</AvatarFallback>
                  </Avatar>
                  <span className="hidden text-sm font-medium md:inline">A. Verma</span>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-48">
                <DropdownMenuLabel>Account</DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem>Profile</DropdownMenuItem>
                <DropdownMenuItem>Approval limits</DropdownMenuItem>
                <DropdownMenuItem>Preferences</DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem>Sign out</DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </header>

      <div className="flex-1 overflow-hidden">
        <div className="grid h-full w-full grid-cols-1 gap-6 px-6 py-8 lg:grid-cols-[220px_1fr]">
          <aside className="hidden min-h-0 flex-col gap-2 overflow-y-auto rounded-2xl border border-slate-200 bg-white p-4 lg:flex">
          <Button variant="secondary" className="justify-start gap-2">
            <LayoutGrid className="h-4 w-4" />
            Dashboard
          </Button>
          <Button variant="ghost" className="justify-start gap-2">
            <Landmark className="h-4 w-4" />
            GL control
          </Button>
          <Button variant="ghost" className="justify-start gap-2">
            <FileText className="h-4 w-4" />
            Loan pipeline
          </Button>
          <Button variant="ghost" className="justify-start gap-2">
            <ClipboardList className="h-4 w-4" />
            Approvals
          </Button>
          <Button variant="ghost" className="justify-start gap-2">
            <Users className="h-4 w-4" />
            HRIS
          </Button>
          <Button variant="ghost" className="justify-start gap-2">
            <ShieldCheck className="h-4 w-4" />
            Compliance
          </Button>
          <Button variant="ghost" className="justify-start gap-2">
            <Wallet className="h-4 w-4" />
            Treasury
          </Button>
        </aside>

          <main className="min-h-0 space-y-6 overflow-y-auto">
          <section className="grid gap-4 lg:grid-cols-[1.6fr_1fr]">
            <Card className="border-slate-200">
              <CardHeader>
                <CardTitle className="text-xl">Good morning, Ananya</CardTitle>
                <p className="text-sm text-slate-600">
                  Your operations snapshot across finance, lending, and HR.
                </p>
              </CardHeader>
              <CardContent>
                <div className="grid gap-3 sm:grid-cols-3">
                  <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                    <p className="text-xs text-slate-500">Pending approvals</p>
                    <p className="mt-2 text-2xl font-semibold text-slate-900">26</p>
                    <p className="mt-1 text-xs text-slate-500">Across GL, LOS, HR</p>
                  </div>
                  <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                    <p className="text-xs text-slate-500">Active loan book</p>
                    <p className="mt-2 text-2xl font-semibold text-slate-900">INR 1,240 Cr</p>
                    <p className="mt-1 text-xs text-slate-500">4.1% month growth</p>
                  </div>
                  <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                    <p className="text-xs text-slate-500">Next compliance run</p>
                    <p className="mt-2 text-2xl font-semibold text-slate-900">7 days</p>
                    <p className="mt-1 text-xs text-slate-500">RBI return for Q4</p>
                  </div>
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

          <section>
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-lg font-semibold">Module launcher</h2>
              <Button variant="ghost" className="gap-2 text-sm">
                <TrendingUp className="h-4 w-4" />
                View usage analytics
              </Button>
            </div>
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {modules.map((module) => (
                <Card key={module.name} className="border-slate-200">
                  <CardHeader className="flex flex-row items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-50 text-blue-700">
                        <module.icon className="h-5 w-5" />
                      </div>
                      <div>
                        <CardTitle className="text-base">{module.name}</CardTitle>
                        <p className="text-xs text-slate-500">{module.summary}</p>
                      </div>
                    </div>
                    <Badge
                      className={`text-xs ${
                        module.status === "Live"
                          ? "bg-emerald-50 text-emerald-700 hover:bg-emerald-50"
                          : module.status === "In review"
                          ? "bg-amber-50 text-amber-700 hover:bg-amber-50"
                          : "bg-slate-100 text-slate-600 hover:bg-slate-100"
                      }`}
                    >
                      {module.status}
                    </Badge>
                  </CardHeader>
                  <CardContent className="flex items-center justify-between">
                    <span className="text-xs text-slate-500">Last run: 2 hours ago</span>
                    <Button variant="ghost" size="sm">
                      Open
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>
          </section>

          <section className="grid gap-4 lg:grid-cols-[1.4fr_1fr]">
            <Card className="border-slate-200">
              <CardHeader>
                <CardTitle className="text-lg">Work queue</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {workQueue.map((item) => (
                  <div
                    key={item.title}
                    className="flex items-center justify-between rounded-xl border border-slate-200 bg-slate-50 p-4"
                  >
                    <div>
                      <p className="text-sm font-semibold text-slate-900">{item.title}</p>
                      <p className="text-xs text-slate-500">{item.detail}</p>
                    </div>
                    <Badge className="bg-blue-50 text-blue-700 hover:bg-blue-50">
                      {item.meta}
                    </Badge>
                  </div>
                ))}
              </CardContent>
            </Card>

            <Card className="border-slate-200">
              <CardHeader>
                <CardTitle className="text-lg">Compliance pulse</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                  <p className="text-sm font-semibold text-slate-900">RBI return Q4</p>
                  <p className="text-xs text-slate-500">Due in 7 days</p>
                  <div className="mt-3 h-2 w-full rounded-full bg-slate-200">
                    <div className="h-2 w-2/3 rounded-full bg-blue-600" />
                  </div>
                </div>
                <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                  <p className="text-sm font-semibold text-slate-900">GST filing</p>
                  <p className="text-xs text-slate-500">Due in 14 days</p>
                  <div className="mt-3 h-2 w-full rounded-full bg-slate-200">
                    <div className="h-2 w-1/2 rounded-full bg-blue-600" />
                  </div>
                </div>
                <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                  <p className="text-sm font-semibold text-slate-900">TDS certificates</p>
                  <p className="text-xs text-slate-500">Due in 19 days</p>
                  <div className="mt-3 h-2 w-full rounded-full bg-slate-200">
                    <div className="h-2 w-1/3 rounded-full bg-blue-600" />
                  </div>
                </div>
              </CardContent>
            </Card>
          </section>
          </main>
        </div>
      </div>
    </div>
  );
}
