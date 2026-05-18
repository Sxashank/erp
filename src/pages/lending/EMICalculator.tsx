import { Calculator, ArrowLeft, Download, RefreshCw } from 'lucide-react';
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

import { PageHeader } from '@/components/common/PageHeader';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { formatCurrency } from '@/lib/utils';

interface ScheduleRow {
  installment: number;
  opening_balance: number;
  principal: number;
  interest: number;
  emi: number;
  closing_balance: number;
}

export default function EMICalculator() {
  const navigate = useNavigate();
  const [principal, setPrincipal] = useState(1000000);
  const [interestRate, setInterestRate] = useState(12);
  const [tenure, setTenure] = useState(12);
  const [calculationMethod, setCalculationMethod] = useState('REDUCING');
  const [emi, setEmi] = useState(0);
  const [totalInterest, setTotalInterest] = useState(0);
  const [totalPayment, setTotalPayment] = useState(0);
  const [schedule, setSchedule] = useState<ScheduleRow[]>([]);

  useEffect(() => {
    calculateEMI();
  }, [principal, interestRate, tenure, calculationMethod]);

  const calculateEMI = () => {
    const P = principal;
    const R = interestRate / 12 / 100; // Monthly interest rate
    const N = tenure;

    if (P <= 0 || R <= 0 || N <= 0) {
      setEmi(0);
      setTotalInterest(0);
      setTotalPayment(0);
      setSchedule([]);
      return;
    }

    let monthlyEMI = 0;
    let totalInt = 0;
    const scheduleData: ScheduleRow[] = [];

    if (calculationMethod === 'REDUCING') {
      // EMI = P * R * (1+R)^N / ((1+R)^N - 1)
      const factor = Math.pow(1 + R, N);
      monthlyEMI = (P * R * factor) / (factor - 1);

      let balance = P;
      for (let i = 1; i <= N; i++) {
        const interestComponent = balance * R;
        const principalComponent = monthlyEMI - interestComponent;
        const closingBalance = balance - principalComponent;

        scheduleData.push({
          installment: i,
          opening_balance: balance,
          principal: principalComponent,
          interest: interestComponent,
          emi: monthlyEMI,
          closing_balance: Math.max(0, closingBalance),
        });

        totalInt += interestComponent;
        balance = closingBalance;
      }
    } else if (calculationMethod === 'FLAT') {
      // Flat rate: Interest = P * R * N/12, EMI = (P + Interest) / N
      totalInt = P * (interestRate / 100) * (N / 12);
      monthlyEMI = (P + totalInt) / N;

      const principalPerMonth = P / N;
      const interestPerMonth = totalInt / N;

      let balance = P;
      for (let i = 1; i <= N; i++) {
        scheduleData.push({
          installment: i,
          opening_balance: balance,
          principal: principalPerMonth,
          interest: interestPerMonth,
          emi: monthlyEMI,
          closing_balance: Math.max(0, balance - principalPerMonth),
        });
        balance -= principalPerMonth;
      }
    } else if (calculationMethod === 'RULE_OF_78') {
      // Rule of 78 - interest weighted toward beginning
      totalInt = P * (interestRate / 100) * (N / 12);
      monthlyEMI = (P + totalInt) / N;

      const principalPerMonth = P / N;
      const sumOfDigits = (N * (N + 1)) / 2;

      let balance = P;
      for (let i = 1; i <= N; i++) {
        const interestWeight = (N - i + 1) / sumOfDigits;
        const interestComponent = totalInt * interestWeight;

        scheduleData.push({
          installment: i,
          opening_balance: balance,
          principal: principalPerMonth,
          interest: interestComponent,
          emi: principalPerMonth + interestComponent,
          closing_balance: Math.max(0, balance - principalPerMonth),
        });
        balance -= principalPerMonth;
      }
    }

    setEmi(monthlyEMI);
    setTotalInterest(totalInt);
    setTotalPayment(P + totalInt);
    setSchedule(scheduleData);
  };

  const handleReset = () => {
    setPrincipal(1000000);
    setInterestRate(12);
    setTenure(12);
    setCalculationMethod('REDUCING');
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="EMI Calculator"
        subtitle="Calculate EMI and view amortization schedule"
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Calculator Input */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calculator className="h-5 w-5" />
              Loan Parameters
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-2">
              <div className="flex justify-between">
                <Label>Principal Amount</Label>
                <span className="text-sm font-medium">{formatCurrency(principal)}</span>
              </div>
              <Input
                type="number"
                value={principal}
                onChange={(e) => setPrincipal(parseFloat(e.target.value) || 0)}
              />
              <Slider
                value={[principal]}
                onValueChange={(value) => setPrincipal(value[0])}
                min={100000}
                max={100000000}
                step={100000}
              />
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>1 Lac</span>
                <span>10 Cr</span>
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between">
                <Label>Interest Rate (% p.a.)</Label>
                <span className="text-sm font-medium">{interestRate}%</span>
              </div>
              <Input
                type="number"
                value={interestRate}
                onChange={(e) => setInterestRate(parseFloat(e.target.value) || 0)}
                step={0.25}
              />
              <Slider
                value={[interestRate]}
                onValueChange={(value) => setInterestRate(value[0])}
                min={1}
                max={30}
                step={0.25}
              />
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>1%</span>
                <span>30%</span>
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between">
                <Label>Tenure (Months)</Label>
                <span className="text-sm font-medium">{tenure} months</span>
              </div>
              <Input
                type="number"
                value={tenure}
                onChange={(e) => setTenure(parseInt(e.target.value) || 0)}
              />
              <Slider
                value={[tenure]}
                onValueChange={(value) => setTenure(value[0])}
                min={1}
                max={360}
                step={1}
              />
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>1 month</span>
                <span>30 years</span>
              </div>
            </div>

            <div className="space-y-2">
              <Label>Calculation Method</Label>
              <Select value={calculationMethod} onValueChange={setCalculationMethod}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="REDUCING">Reducing Balance</SelectItem>
                  <SelectItem value="FLAT">Flat Rate</SelectItem>
                  <SelectItem value="RULE_OF_78">Rule of 78</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <Button variant="outline" className="w-full" onClick={handleReset}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Reset
            </Button>
          </CardContent>
        </Card>

        {/* Results */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Calculation Results</CardTitle>
            <CardDescription>Based on {calculationMethod.toLowerCase().replace('_', ' ')} method</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 gap-4 mb-6">
              <div className="text-center p-4 bg-primary/10 rounded-lg">
                <p className="text-sm text-muted-foreground">Monthly EMI</p>
                <p className="text-2xl font-bold text-primary">{formatCurrency(emi)}</p>
              </div>
              <div className="text-center p-4 bg-orange-50 rounded-lg">
                <p className="text-sm text-muted-foreground">Total Interest</p>
                <p className="text-2xl font-bold text-orange-600">{formatCurrency(totalInterest)}</p>
              </div>
              <div className="text-center p-4 bg-green-50 rounded-lg">
                <p className="text-sm text-muted-foreground">Total Payment</p>
                <p className="text-2xl font-bold text-green-600">{formatCurrency(totalPayment)}</p>
              </div>
            </div>

            {/* Break-up Summary */}
            <div className="grid grid-cols-2 gap-4 mb-6">
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">Principal Amount</span>
                  <span className="font-medium">{formatCurrency(principal)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">Interest Amount</span>
                  <span className="font-medium">{formatCurrency(totalInterest)}</span>
                </div>
                <div className="flex justify-between border-t pt-2">
                  <span className="text-sm font-medium">Total Payable</span>
                  <span className="font-bold">{formatCurrency(totalPayment)}</span>
                </div>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">Interest Rate</span>
                  <span className="font-medium">{interestRate}% p.a.</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">Loan Tenure</span>
                  <span className="font-medium">
                    {tenure} months ({(tenure / 12).toFixed(1)} years)
                  </span>
                </div>
                <div className="flex justify-between border-t pt-2">
                  <span className="text-sm font-medium">Interest Ratio</span>
                  <span className="font-bold">
                    {principal > 0 ? ((totalInterest / principal) * 100).toFixed(1) : 0}%
                  </span>
                </div>
              </div>
            </div>

            {/* Amortization Schedule */}
            <Tabs defaultValue="schedule">
              <div className="flex justify-between items-center mb-4">
                <TabsList>
                  <TabsTrigger value="schedule">Amortization Schedule</TabsTrigger>
                  <TabsTrigger value="yearly">Yearly Summary</TabsTrigger>
                </TabsList>
                <Button variant="outline" size="sm">
                  <Download className="h-4 w-4 mr-2" />
                  Export
                </Button>
              </div>

              <TabsContent value="schedule" className="max-h-[400px] overflow-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="text-center">Month</TableHead>
                      <TableHead className="text-right">Opening Balance</TableHead>
                      <TableHead className="text-right">Principal</TableHead>
                      <TableHead className="text-right">Interest</TableHead>
                      <TableHead className="text-right">EMI</TableHead>
                      <TableHead className="text-right">Closing Balance</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {schedule.map((row) => (
                      <TableRow key={row.installment}>
                        <TableCell className="text-center">{row.installment}</TableCell>
                        <TableCell className="text-right">
                          {formatCurrency(row.opening_balance)}
                        </TableCell>
                        <TableCell className="text-right text-green-600">
                          {formatCurrency(row.principal)}
                        </TableCell>
                        <TableCell className="text-right text-orange-600">
                          {formatCurrency(row.interest)}
                        </TableCell>
                        <TableCell className="text-right font-medium">
                          {formatCurrency(row.emi)}
                        </TableCell>
                        <TableCell className="text-right">
                          {formatCurrency(row.closing_balance)}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TabsContent>

              <TabsContent value="yearly">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="text-center">Year</TableHead>
                      <TableHead className="text-right">Principal Paid</TableHead>
                      <TableHead className="text-right">Interest Paid</TableHead>
                      <TableHead className="text-right">Total Paid</TableHead>
                      <TableHead className="text-right">Balance</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {Array.from({ length: Math.ceil(tenure / 12) }, (_, yearIndex) => {
                      const yearStart = yearIndex * 12;
                      const yearEnd = Math.min(yearStart + 12, tenure);
                      const yearSchedule = schedule.slice(yearStart, yearEnd);

                      const principalPaid = yearSchedule.reduce((sum, r) => sum + r.principal, 0);
                      const interestPaid = yearSchedule.reduce((sum, r) => sum + r.interest, 0);
                      const balance = yearSchedule[yearSchedule.length - 1]?.closing_balance || 0;

                      return (
                        <TableRow key={yearIndex + 1}>
                          <TableCell className="text-center">{yearIndex + 1}</TableCell>
                          <TableCell className="text-right text-green-600">
                            {formatCurrency(principalPaid)}
                          </TableCell>
                          <TableCell className="text-right text-orange-600">
                            {formatCurrency(interestPaid)}
                          </TableCell>
                          <TableCell className="text-right font-medium">
                            {formatCurrency(principalPaid + interestPaid)}
                          </TableCell>
                          <TableCell className="text-right">
                            {formatCurrency(balance)}
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
