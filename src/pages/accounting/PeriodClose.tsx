import { useState } from 'react';
import { Link, useSearchParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Checkbox } from '@/components/ui/checkbox';
import { PageHeader } from '@/components/common/PageHeader';
import {
  ArrowLeft,
  Lock,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Clock,
  RefreshCw,
  ChevronRight,
  Play,
  FileText,
  Calculator,
  DollarSign,
  Shield,
} from 'lucide-react';

// Mock period data
const periodData = {
  id: 'FY2024-25-Q4-M1',
  name: 'January 2025',
  fiscalYear: 'FY 2024-25',
  quarter: 'Q4',
  startDate: '2025-01-01',
  endDate: '2025-01-31',
  status: 'OPEN',
};

// Pre-close checklist items
const checklistItems = [
  {
    id: 'pending_postings',
    category: 'GL Postings',
    title: 'Pending GL Postings',
    description: 'All GL postings must be approved or rejected',
    status: 'WARNING',
    count: 3,
    actionLabel: 'Review Pending',
    actionLink: '/admin/accounting/gl-postings?status=PENDING_APPROVAL',
  },
  {
    id: 'bank_reconciliation',
    category: 'Bank Reconciliation',
    title: 'Bank Reconciliation Complete',
    description: 'All bank accounts must be reconciled',
    status: 'SUCCESS',
    count: 0,
    actionLabel: 'View BRS',
    actionLink: '/admin/ap-ar/bank-reconciliation',
  },
  {
    id: 'interest_accrual',
    category: 'Accruals',
    title: 'Interest Accrual Posted',
    description: 'Interest accrual entries must be posted',
    status: 'SUCCESS',
    count: 0,
    actionLabel: 'View Postings',
    actionLink: '/admin/accounting/gl-postings?type=interest_accrual',
  },
  {
    id: 'depreciation',
    category: 'Accruals',
    title: 'Depreciation Posted',
    description: 'Fixed asset depreciation must be posted',
    status: 'PENDING',
    count: 1,
    actionLabel: 'Run Depreciation',
    actionLink: '/admin/finance/depreciation',
  },
  {
    id: 'provisions',
    category: 'Provisions',
    title: 'NPA Provisions',
    description: 'NPA provisioning must be calculated and posted',
    status: 'SUCCESS',
    count: 0,
    actionLabel: 'View Provisions',
    actionLink: '/admin/lending/npa',
  },
  {
    id: 'gst_reconciliation',
    category: 'Tax',
    title: 'GST Reconciliation',
    description: 'GST input/output must be reconciled',
    status: 'WARNING',
    count: 5,
    actionLabel: 'Reconcile GST',
    actionLink: '/admin/gst/reconciliation',
  },
  {
    id: 'tds_compliance',
    category: 'Tax',
    title: 'TDS Compliance',
    description: 'TDS deducted must match with challans',
    status: 'SUCCESS',
    count: 0,
    actionLabel: 'View TDS',
    actionLink: '/admin/tds/returns',
  },
  {
    id: 'trial_balance',
    category: 'Reports',
    title: 'Trial Balance Verification',
    description: 'Trial balance must be verified and balanced',
    status: 'SUCCESS',
    count: 0,
    actionLabel: 'View TB',
    actionLink: '/admin/reports/trial-balance',
  },
];

export default function PeriodClose() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const isFinalClose = searchParams.get('final') === 'true';

  const [currentStep, setCurrentStep] = useState(1);
  const [checkedItems, setCheckedItems] = useState<string[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [closeProgress, setCloseProgress] = useState(0);

  const toggleCheck = (id: string) => {
    setCheckedItems(prev =>
      prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]
    );
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'SUCCESS':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'WARNING':
        return <AlertTriangle className="h-5 w-5 text-yellow-500" />;
      case 'ERROR':
        return <XCircle className="h-5 w-5 text-red-500" />;
      case 'PENDING':
        return <Clock className="h-5 w-5 text-gray-400" />;
      default:
        return <Clock className="h-5 w-5 text-gray-400" />;
    }
  };

  const allChecksPass = checklistItems.every(item =>
    item.status === 'SUCCESS' || checkedItems.includes(item.id)
  );

  const runPeriodClose = async () => {
    setIsProcessing(true);
    setCloseProgress(0);

    // Simulate close process
    for (let i = 0; i <= 100; i += 10) {
      await new Promise(resolve => setTimeout(resolve, 500));
      setCloseProgress(i);
    }

    setIsProcessing(false);
    setCurrentStep(3);
  };

  // Statistics
  const successCount = checklistItems.filter(i => i.status === 'SUCCESS').length;
  const warningCount = checklistItems.filter(i => i.status === 'WARNING').length;
  const pendingCount = checklistItems.filter(i => i.status === 'PENDING').length;

  return (
    <div className="container mx-auto py-6 space-y-6">
      <PageHeader
        title={isFinalClose ? 'Final Period Close' : 'Period Close Wizard'}
        subtitle={`${periodData.name} (${periodData.fiscalYear})`}
        breadcrumbs={[
          { label: 'Periods', to: '/admin/accounting/periods' },
          { label: isFinalClose ? 'Final Close' : 'Close Wizard' },
        ]}
      />

      {/* Progress Steps */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            {[
              { step: 1, title: 'Pre-Close Checks' },
              { step: 2, title: 'Execute Close' },
              { step: 3, title: 'Confirmation' },
            ].map((s, index) => (
              <div key={s.step} className="flex items-center flex-1">
                <div className={`flex items-center gap-3 ${currentStep >= s.step ? 'text-primary' : 'text-muted-foreground'}`}>
                  <div className={`h-10 w-10 rounded-full flex items-center justify-center font-bold ${
                    currentStep > s.step ? 'bg-green-500 text-white' :
                    currentStep === s.step ? 'bg-primary text-white' : 'bg-muted'
                  }`}>
                    {currentStep > s.step ? <CheckCircle className="h-5 w-5" /> : s.step}
                  </div>
                  <span className="font-medium">{s.title}</span>
                </div>
                {index < 2 && (
                  <div className={`flex-1 h-1 mx-4 ${currentStep > s.step ? 'bg-green-500' : 'bg-muted'}`} />
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Step 1: Pre-Close Checks */}
      {currentStep === 1 && (
        <>
          {/* Summary */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <CheckCircle className="h-4 w-4 text-green-500" />
                  Passed
                </div>
                <div className="text-2xl font-bold mt-1 text-green-600">{successCount}</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <AlertTriangle className="h-4 w-4 text-yellow-500" />
                  Warnings
                </div>
                <div className="text-2xl font-bold mt-1 text-yellow-600">{warningCount}</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Clock className="h-4 w-4 text-gray-400" />
                  Pending
                </div>
                <div className="text-2xl font-bold mt-1 text-gray-600">{pendingCount}</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="text-sm text-muted-foreground">Acknowledged</div>
                <div className="text-2xl font-bold mt-1">{checkedItems.length}/{checklistItems.length}</div>
              </CardContent>
            </Card>
          </div>

          {/* Checklist */}
          <Card>
            <CardHeader>
              <CardTitle>Pre-Close Checklist</CardTitle>
              <CardDescription>Review and acknowledge all items before proceeding</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {checklistItems.map((item) => (
                  <div key={item.id} className="flex items-start gap-4 p-4 border rounded-lg">
                    <Checkbox
                      checked={item.status === 'SUCCESS' || checkedItems.includes(item.id)}
                      onCheckedChange={() => toggleCheck(item.id)}
                      disabled={item.status === 'SUCCESS'}
                    />
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        {getStatusIcon(item.status)}
                        <span className="font-medium">{item.title}</span>
                        <Badge variant="outline" className="text-xs">{item.category}</Badge>
                      </div>
                      <p className="text-sm text-muted-foreground mt-1">{item.description}</p>
                      {item.count > 0 && (
                        <p className={`text-sm mt-1 ${item.status === 'WARNING' ? 'text-yellow-600' : 'text-red-600'}`}>
                          {item.count} item(s) require attention
                        </p>
                      )}
                    </div>
                    <Link to={item.actionLink}>
                      <Button variant="outline" size="sm">
                        {item.actionLabel}
                        <ChevronRight className="h-4 w-4 ml-1" />
                      </Button>
                    </Link>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Actions */}
          <div className="flex justify-between">
            <Button variant="outline" onClick={() => navigate(-1)}>
              Cancel
            </Button>
            <Button
              disabled={!allChecksPass}
              onClick={() => setCurrentStep(2)}
            >
              Proceed to Close
              <ChevronRight className="h-4 w-4 ml-2" />
            </Button>
          </div>

          {!allChecksPass && (
            <div className="p-4 bg-yellow-50 rounded-lg text-yellow-800 text-sm">
              <AlertTriangle className="h-4 w-4 inline mr-2" />
              Please acknowledge all warnings and resolve pending items before proceeding.
            </div>
          )}
        </>
      )}

      {/* Step 2: Execute Close */}
      {currentStep === 2 && (
        <Card>
          <CardHeader>
            <CardTitle>Execute Period Close</CardTitle>
            <CardDescription>
              {isFinalClose ? 'Final close will permanently lock this period' : 'Soft close will restrict new postings'}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {!isProcessing && closeProgress === 0 && (
              <>
                <div className="p-6 bg-muted rounded-lg text-center">
                  <Lock className="h-16 w-16 mx-auto text-muted-foreground mb-4" />
                  <h3 className="text-lg font-bold">Ready to Close {periodData.name}</h3>
                  <p className="text-muted-foreground mt-2">
                    {isFinalClose
                      ? 'This action is permanent and cannot be undone.'
                      : 'You can reopen a soft-closed period if needed.'}
                  </p>
                </div>

                <div className="space-y-2">
                  <h4 className="font-medium">The following actions will be performed:</h4>
                  <ul className="space-y-2 text-sm">
                    <li className="flex items-center gap-2">
                      <CheckCircle className="h-4 w-4 text-green-500" />
                      Generate closing trial balance
                    </li>
                    <li className="flex items-center gap-2">
                      <CheckCircle className="h-4 w-4 text-green-500" />
                      Lock period for new postings
                    </li>
                    <li className="flex items-center gap-2">
                      <CheckCircle className="h-4 w-4 text-green-500" />
                      Archive period data
                    </li>
                    {isFinalClose && (
                      <li className="flex items-center gap-2">
                        <CheckCircle className="h-4 w-4 text-green-500" />
                        Transfer balances to next period
                      </li>
                    )}
                  </ul>
                </div>

                <div className="flex gap-2">
                  <Button variant="outline" onClick={() => setCurrentStep(1)}>
                    <ArrowLeft className="h-4 w-4 mr-2" />
                    Back
                  </Button>
                  <Button onClick={runPeriodClose}>
                    <Play className="h-4 w-4 mr-2" />
                    Execute Close
                  </Button>
                </div>
              </>
            )}

            {isProcessing && (
              <div className="py-12 text-center">
                <RefreshCw className="h-16 w-16 mx-auto text-primary animate-spin mb-4" />
                <h3 className="text-lg font-bold">Closing Period...</h3>
                <p className="text-muted-foreground mt-2">Please wait while the period is being closed.</p>
                <div className="mt-6 max-w-md mx-auto">
                  <Progress value={closeProgress} className="h-2" />
                  <p className="text-sm text-muted-foreground mt-2">{closeProgress}% complete</p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Step 3: Confirmation */}
      {currentStep === 3 && (
        <Card>
          <CardContent className="py-12 text-center">
            <div className="h-20 w-20 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-6">
              <CheckCircle className="h-10 w-10 text-green-600" />
            </div>
            <h2 className="text-2xl font-bold">Period Closed Successfully</h2>
            <p className="text-muted-foreground mt-2">
              {periodData.name} has been {isFinalClose ? 'permanently' : 'soft'} closed.
            </p>

            <div className="grid grid-cols-3 gap-4 max-w-lg mx-auto mt-8">
              <div className="p-4 bg-muted rounded-lg">
                <FileText className="h-6 w-6 mx-auto text-muted-foreground" />
                <p className="text-sm mt-2">Trial Balance Generated</p>
              </div>
              <div className="p-4 bg-muted rounded-lg">
                <Calculator className="h-6 w-6 mx-auto text-muted-foreground" />
                <p className="text-sm mt-2">45 Postings Archived</p>
              </div>
              <div className="p-4 bg-muted rounded-lg">
                <Shield className="h-6 w-6 mx-auto text-muted-foreground" />
                <p className="text-sm mt-2">Period Locked</p>
              </div>
            </div>

            <div className="flex gap-2 justify-center mt-8">
              <Link to="/admin/accounting/periods">
                <Button variant="outline">
                  View All Periods
                </Button>
              </Link>
              <Link to="/admin/reports/trial-balance">
                <Button>
                  View Trial Balance
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
