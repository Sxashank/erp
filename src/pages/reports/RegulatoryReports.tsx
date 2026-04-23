import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { PageHeader } from '@/components/common/PageHeader';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Shield,
  Download,
  FileText,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CheckCircle,
} from 'lucide-react';

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    notation: 'compact',
    maximumFractionDigits: 1,
  }).format(value);
};

// Mock data - ALM Report
const almBuckets = [
  { bucket: '1-7 days', assets: 85000000, liabilities: 72000000, gap: 13000000, cumGap: 13000000 },
  { bucket: '8-14 days', assets: 95000000, liabilities: 88000000, gap: 7000000, cumGap: 20000000 },
  { bucket: '15-30 days', assets: 125000000, liabilities: 115000000, gap: 10000000, cumGap: 30000000 },
  { bucket: '31-60 days', assets: 180000000, liabilities: 165000000, gap: 15000000, cumGap: 45000000 },
  { bucket: '61-90 days', assets: 220000000, liabilities: 195000000, gap: 25000000, cumGap: 70000000 },
  { bucket: '91-180 days', assets: 350000000, liabilities: 320000000, gap: 30000000, cumGap: 100000000 },
  { bucket: '181-365 days', assets: 480000000, liabilities: 420000000, gap: 60000000, cumGap: 160000000 },
  { bucket: '1-3 years', assets: 650000000, liabilities: 580000000, gap: 70000000, cumGap: 230000000 },
  { bucket: '3-5 years', assets: 350000000, liabilities: 300000000, gap: 50000000, cumGap: 280000000 },
  { bucket: 'Over 5 years', assets: 200000000, liabilities: 180000000, gap: 20000000, cumGap: 300000000 },
];

// Mock data - NPA Classification
const npaCategories = [
  { code: 'STD', name: 'Standard Assets', accounts: 14250, outstanding: 2050000000, provision: 8200000, rate: 0.4 },
  { code: 'SMA0', name: 'SMA-0 (1-30 days)', accounts: 450, outstanding: 85000000, provision: 340000, rate: 0.4 },
  { code: 'SMA1', name: 'SMA-1 (31-60 days)', accounts: 180, outstanding: 42000000, provision: 168000, rate: 0.4 },
  { code: 'SMA2', name: 'SMA-2 (61-90 days)', accounts: 120, outstanding: 28000000, provision: 112000, rate: 0.4 },
  { code: 'SUB', name: 'Sub-Standard', accounts: 85, outstanding: 22000000, provision: 3300000, rate: 15.0 },
  { code: 'DBT', name: 'Doubtful 1', accounts: 45, outstanding: 12000000, provision: 3000000, rate: 25.0 },
  { code: 'DBT2', name: 'Doubtful 2', accounts: 18, outstanding: 5500000, provision: 2200000, rate: 40.0 },
  { code: 'LOSS', name: 'Loss Assets', accounts: 8, outstanding: 3200000, provision: 3200000, rate: 100.0 },
];

// Mock data - CRAR
const crarData = {
  tier1Capital: 100000000,
  tier2Capital: 20000000,
  totalCapital: 120000000,
  creditRiskRWA: 425000000,
  marketRiskRWA: 50000000,
  operationalRiskRWA: 25000000,
  totalRWA: 500000000,
  crar: 24.0,
  tier1Ratio: 20.0,
  minimumRequired: 15.0,
};

// Mock data - Liquidity
const liquidityData = {
  level1Assets: 35000000,
  level2aAssets: 10000000,
  level2bAssets: 5000000,
  totalHQLA: 50000000,
  cashOutflows: 40000000,
  cashInflows: 35000000,
  netOutflows: 27500000,
  lcr: 181.8,
  minimumRequired: 100.0,
};

export default function RegulatoryReports() {
  const [asOfDate, setAsOfDate] = useState(new Date().toISOString().split('T')[0]);

  const totalGNPA = npaCategories
    .filter(c => !['STD', 'SMA0', 'SMA1', 'SMA2'].includes(c.code))
    .reduce((sum, c) => sum + c.outstanding, 0);
  const totalOutstanding = npaCategories.reduce((sum, c) => sum + c.outstanding, 0);
  const gnpaRatio = (totalGNPA / totalOutstanding * 100).toFixed(2);
  const totalProvision = npaCategories.reduce((sum, c) => sum + c.provision, 0);
  const nnpaRatio = ((totalGNPA - totalProvision) / (totalOutstanding - totalProvision) * 100).toFixed(2);

  return (
    <div className="container mx-auto py-6 space-y-6">
      <PageHeader
        title="Regulatory Reports"
        subtitle="RBI compliance and regulatory submissions"
        actions={
          <div className="flex items-center gap-4">
            <Input
              type="date"
              value={asOfDate}
              onChange={(e) => setAsOfDate(e.target.value)}
              className="w-40"
            />
            <Button variant="outline">
              <Download className="h-4 w-4 mr-2" />
              Export All
            </Button>
          </div>
        }
      />

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-muted-foreground">CRAR</div>
                <div className="text-2xl font-bold text-green-600">{crarData.crar}%</div>
              </div>
              <div className="text-sm text-muted-foreground">
                Min: {crarData.minimumRequired}%
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-muted-foreground">GNPA Ratio</div>
                <div className="text-2xl font-bold text-orange-600">{gnpaRatio}%</div>
              </div>
              <AlertTriangle className="h-8 w-8 text-orange-200" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-muted-foreground">NNPA Ratio</div>
                <div className="text-2xl font-bold">{nnpaRatio}%</div>
              </div>
              <FileText className="h-8 w-8 text-gray-200" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-muted-foreground">LCR</div>
                <div className="text-2xl font-bold text-green-600">{liquidityData.lcr}%</div>
              </div>
              <div className="text-sm text-muted-foreground">
                Min: {liquidityData.minimumRequired}%
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="alm" className="space-y-4">
        <TabsList>
          <TabsTrigger value="alm">ALM Report</TabsTrigger>
          <TabsTrigger value="npa">NPA Classification</TabsTrigger>
          <TabsTrigger value="crar">CRAR</TabsTrigger>
          <TabsTrigger value="liquidity">Liquidity</TabsTrigger>
        </TabsList>

        {/* ALM Report */}
        <TabsContent value="alm">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Asset Liability Management Report</CardTitle>
              <Button variant="outline" size="sm">
                <Download className="h-4 w-4 mr-2" />
                Export
              </Button>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Time Bucket</TableHead>
                    <TableHead className="text-right">Assets</TableHead>
                    <TableHead className="text-right">Liabilities</TableHead>
                    <TableHead className="text-right">Gap</TableHead>
                    <TableHead className="text-right">Cumulative Gap</TableHead>
                    <TableHead className="text-center">Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {almBuckets.map((bucket) => (
                    <TableRow key={bucket.bucket}>
                      <TableCell className="font-medium">{bucket.bucket}</TableCell>
                      <TableCell className="text-right">{formatCurrency(bucket.assets)}</TableCell>
                      <TableCell className="text-right">{formatCurrency(bucket.liabilities)}</TableCell>
                      <TableCell className={`text-right ${bucket.gap >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {bucket.gap >= 0 ? '+' : ''}{formatCurrency(bucket.gap)}
                      </TableCell>
                      <TableCell className={`text-right ${bucket.cumGap >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {bucket.cumGap >= 0 ? '+' : ''}{formatCurrency(bucket.cumGap)}
                      </TableCell>
                      <TableCell className="text-center">
                        {bucket.gap >= 0 ? (
                          <Badge variant="default" className="bg-green-500">Positive</Badge>
                        ) : (
                          <Badge variant="destructive">Negative</Badge>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        {/* NPA Classification */}
        <TabsContent value="npa">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>NPA Classification as per IRAC Norms</CardTitle>
              <Button variant="outline" size="sm">
                <Download className="h-4 w-4 mr-2" />
                Export
              </Button>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Classification</TableHead>
                    <TableHead className="text-right">Accounts</TableHead>
                    <TableHead className="text-right">Outstanding</TableHead>
                    <TableHead className="text-right">Provision Rate</TableHead>
                    <TableHead className="text-right">Provision Amount</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {npaCategories.map((cat) => (
                    <TableRow key={cat.code}>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Badge variant={
                            cat.code === 'STD' ? 'default' :
                            cat.code.startsWith('SMA') ? 'secondary' :
                            cat.code === 'SUB' ? 'outline' : 'destructive'
                          }>
                            {cat.code}
                          </Badge>
                          <span>{cat.name}</span>
                        </div>
                      </TableCell>
                      <TableCell className="text-right">{cat.accounts.toLocaleString()}</TableCell>
                      <TableCell className="text-right">{formatCurrency(cat.outstanding)}</TableCell>
                      <TableCell className="text-right">{cat.rate}%</TableCell>
                      <TableCell className="text-right">{formatCurrency(cat.provision)}</TableCell>
                    </TableRow>
                  ))}
                  <TableRow className="bg-muted/50 font-bold">
                    <TableCell>Total</TableCell>
                    <TableCell className="text-right">{npaCategories.reduce((s, c) => s + c.accounts, 0).toLocaleString()}</TableCell>
                    <TableCell className="text-right">{formatCurrency(totalOutstanding)}</TableCell>
                    <TableCell className="text-right">-</TableCell>
                    <TableCell className="text-right">{formatCurrency(totalProvision)}</TableCell>
                  </TableRow>
                </TableBody>
              </Table>

              <div className="mt-4 p-4 bg-muted rounded-lg">
                <div className="grid grid-cols-3 gap-4 text-center">
                  <div>
                    <div className="text-sm text-muted-foreground">Gross NPA</div>
                    <div className="text-xl font-bold">{formatCurrency(totalGNPA)}</div>
                    <div className="text-sm text-muted-foreground">({gnpaRatio}%)</div>
                  </div>
                  <div>
                    <div className="text-sm text-muted-foreground">Total Provision</div>
                    <div className="text-xl font-bold">{formatCurrency(totalProvision)}</div>
                  </div>
                  <div>
                    <div className="text-sm text-muted-foreground">Net NPA</div>
                    <div className="text-xl font-bold">{formatCurrency(totalGNPA - totalProvision)}</div>
                    <div className="text-sm text-muted-foreground">({nnpaRatio}%)</div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* CRAR Report */}
        <TabsContent value="crar">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Capital to Risk Assets Ratio (CRAR)</CardTitle>
              <Button variant="outline" size="sm">
                <Download className="h-4 w-4 mr-2" />
                Export
              </Button>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Capital */}
                <div className="space-y-4">
                  <h4 className="font-semibold">Capital Funds</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between p-2 bg-muted rounded">
                      <span>Tier 1 Capital</span>
                      <span className="font-medium">{formatCurrency(crarData.tier1Capital)}</span>
                    </div>
                    <div className="flex justify-between p-2 bg-muted rounded">
                      <span>Tier 2 Capital</span>
                      <span className="font-medium">{formatCurrency(crarData.tier2Capital)}</span>
                    </div>
                    <div className="flex justify-between p-2 bg-primary/10 rounded font-semibold">
                      <span>Total Capital</span>
                      <span>{formatCurrency(crarData.totalCapital)}</span>
                    </div>
                  </div>
                </div>

                {/* RWA */}
                <div className="space-y-4">
                  <h4 className="font-semibold">Risk Weighted Assets</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between p-2 bg-muted rounded">
                      <span>Credit Risk RWA</span>
                      <span className="font-medium">{formatCurrency(crarData.creditRiskRWA)}</span>
                    </div>
                    <div className="flex justify-between p-2 bg-muted rounded">
                      <span>Market Risk RWA</span>
                      <span className="font-medium">{formatCurrency(crarData.marketRiskRWA)}</span>
                    </div>
                    <div className="flex justify-between p-2 bg-muted rounded">
                      <span>Operational Risk RWA</span>
                      <span className="font-medium">{formatCurrency(crarData.operationalRiskRWA)}</span>
                    </div>
                    <div className="flex justify-between p-2 bg-primary/10 rounded font-semibold">
                      <span>Total RWA</span>
                      <span>{formatCurrency(crarData.totalRWA)}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Ratios */}
              <div className="mt-6 p-4 bg-muted rounded-lg">
                <div className="grid grid-cols-3 gap-4 text-center">
                  <div>
                    <div className="text-sm text-muted-foreground">CRAR</div>
                    <div className="text-3xl font-bold text-green-600">{crarData.crar}%</div>
                    <div className="text-sm text-green-600">
                      <CheckCircle className="h-4 w-4 inline mr-1" />
                      Above minimum ({crarData.minimumRequired}%)
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-muted-foreground">Tier 1 Ratio</div>
                    <div className="text-3xl font-bold">{crarData.tier1Ratio}%</div>
                  </div>
                  <div>
                    <div className="text-sm text-muted-foreground">Surplus Capital</div>
                    <div className="text-3xl font-bold text-green-600">
                      {formatCurrency(crarData.totalCapital - (crarData.totalRWA * crarData.minimumRequired / 100))}
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Liquidity Report */}
        <TabsContent value="liquidity">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Liquidity Coverage Ratio (LCR)</CardTitle>
              <Button variant="outline" size="sm">
                <Download className="h-4 w-4 mr-2" />
                Export
              </Button>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* HQLA */}
                <div className="space-y-4">
                  <h4 className="font-semibold">High Quality Liquid Assets (HQLA)</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between p-2 bg-muted rounded">
                      <span>Level 1 Assets</span>
                      <span className="font-medium">{formatCurrency(liquidityData.level1Assets)}</span>
                    </div>
                    <div className="flex justify-between p-2 bg-muted rounded">
                      <span>Level 2A Assets</span>
                      <span className="font-medium">{formatCurrency(liquidityData.level2aAssets)}</span>
                    </div>
                    <div className="flex justify-between p-2 bg-muted rounded">
                      <span>Level 2B Assets</span>
                      <span className="font-medium">{formatCurrency(liquidityData.level2bAssets)}</span>
                    </div>
                    <div className="flex justify-between p-2 bg-primary/10 rounded font-semibold">
                      <span>Total HQLA</span>
                      <span>{formatCurrency(liquidityData.totalHQLA)}</span>
                    </div>
                  </div>
                </div>

                {/* Cash Flows */}
                <div className="space-y-4">
                  <h4 className="font-semibold">Net Cash Outflows (30 days)</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between p-2 bg-muted rounded">
                      <span>Total Cash Outflows</span>
                      <span className="font-medium text-red-600">{formatCurrency(liquidityData.cashOutflows)}</span>
                    </div>
                    <div className="flex justify-between p-2 bg-muted rounded">
                      <span>Total Cash Inflows</span>
                      <span className="font-medium text-green-600">{formatCurrency(liquidityData.cashInflows)}</span>
                    </div>
                    <div className="flex justify-between p-2 bg-primary/10 rounded font-semibold">
                      <span>Net Cash Outflows</span>
                      <span>{formatCurrency(liquidityData.netOutflows)}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* LCR */}
              <div className="mt-6 p-4 bg-muted rounded-lg">
                <div className="grid grid-cols-2 gap-4 text-center">
                  <div>
                    <div className="text-sm text-muted-foreground">Liquidity Coverage Ratio</div>
                    <div className="text-4xl font-bold text-green-600">{liquidityData.lcr}%</div>
                    <div className="text-sm text-green-600">
                      <CheckCircle className="h-4 w-4 inline mr-1" />
                      Above minimum ({liquidityData.minimumRequired}%)
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-muted-foreground">Surplus Liquidity</div>
                    <div className="text-4xl font-bold text-green-600">
                      {formatCurrency(liquidityData.totalHQLA - liquidityData.netOutflows)}
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
