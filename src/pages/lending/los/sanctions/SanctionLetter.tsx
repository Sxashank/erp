import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, Printer, Download } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { AmountDisplay } from '@/components/lending/common/AmountDisplay';
import { PercentageDisplay } from '@/components/lending/common/PercentageDisplay';
import { DateDisplay } from '@/components/lending/common/DateDisplay';
import { PrintButton } from '@/components/lending/common/PrintButton';

// Mock sanction data
const mockSanction = {
  id: '1',
  sanctionNumber: 'SMFC/SAN/2025/00001',
  sanctionDate: '2025-01-10',
  validUntil: '2025-04-10',
  entity: {
    legalName: 'ABC Industries Private Limited',
    registeredAddress: 'Plot 45, Industrial Area, Phase II, Gurgaon, Haryana - 122001',
    pan: 'AABCA1234A',
    cin: 'U72200HR2015PTC123456',
  },
  directors: [
    { name: 'Mr. Rajesh Kumar', designation: 'Managing Director' },
    { name: 'Mrs. Priya Sharma', designation: 'Director' },
  ],
  product: {
    productName: 'Corporate Term Loan',
  },
  sanctionedAmount: 250000000,
  interestType: 'FLOATING',
  baseRate: 'SMFC Base Rate',
  currentBaseRate: 10.5,
  spreadBps: 200,
  effectiveRate: 12.5,
  tenureMonths: 60,
  moratoriumMonths: 6,
  repaymentFrequency: 'MONTHLY',
  repaymentMode: 'EMI',
  processingFee: 2500000,
  processingFeePercent: 1,
  conditions: {
    preDisbursement: [
      'Creation of mortgage on primary security in favor of SMFC',
      'Submission of insurance policy for assets pledged as security',
      'Equity infusion of minimum 20% of project cost before first disbursement',
      'Board resolution authorizing the company to avail the loan facility',
      'Execution of all loan documents including loan agreement, demand promissory note, and personal guarantees',
    ],
    postDisbursement: [
      'Submission of utilization certificate within 30 days of each disbursement',
      'Quarterly progress reports on project implementation',
      'Annual audited financial statements within 180 days of financial year end',
      'Immediate notification of any material adverse change in business',
    ],
  },
  securities: [
    {
      securityType: 'PRIMARY',
      description:
        'Exclusive charge by way of equitable mortgage on Industrial land and building situated at Plot 45, Industrial Area, Phase II, Gurgaon, Haryana admeasuring 2.5 acres with all present and future constructions thereon',
      value: 400000000,
    },
    {
      securityType: 'COLLATERAL',
      description:
        'Lien on Fixed Deposit of Rs. 5,00,00,000 (Rupees Five Crore Only) placed with State Bank of India, Gurgaon Branch',
      value: 50000000,
    },
    {
      securityType: 'GUARANTEE',
      description:
        'Personal guarantee of promoter directors Mr. Rajesh Kumar and Mrs. Priya Sharma',
      value: null,
    },
  ],
  covenants: [
    'The Borrower shall maintain minimum Debt Service Coverage Ratio (DSCR) of 1.5x at all times',
    'The Borrower shall maintain maximum Debt-Equity ratio of 2:1',
    'The Borrower shall not declare/pay any dividend without prior written consent of SMFC',
    'The Borrower shall not create any additional charge/encumbrance on assets without prior consent',
    'The Borrower shall submit monthly stock statements by 7th of following month',
  ],
  specialConditions: [
    'Disbursement shall be milestone-linked as per the project implementation schedule',
    'First disbursement shall be made only after completion of equity infusion by promoters',
    'Interest during construction period (IDCP) to be serviced on monthly basis',
  ],
};

function formatAmountInWords(amount: number): string {
  const crore = Math.floor(amount / 10000000);
  const lakh = Math.floor((amount % 10000000) / 100000);

  let result = '';
  if (crore > 0) {
    result += `${numberToWords(crore)} Crore `;
  }
  if (lakh > 0) {
    result += `${numberToWords(lakh)} Lakh `;
  }
  return result.trim() + ' Only';
}

function numberToWords(num: number): string {
  const ones = ['', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine'];
  const tens = ['', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety'];
  const teens = ['Ten', 'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen', 'Seventeen', 'Eighteen', 'Nineteen'];

  if (num === 0) return 'Zero';
  if (num < 10) return ones[num];
  if (num < 20) return teens[num - 10];
  if (num < 100) return tens[Math.floor(num / 10)] + (num % 10 ? ' ' + ones[num % 10] : '');
  if (num < 1000) return ones[Math.floor(num / 100)] + ' Hundred' + (num % 100 ? ' ' + numberToWords(num % 100) : '');
  return num.toString();
}

export default function SanctionLetter() {
  const navigate = useNavigate();
  const { id } = useParams();
  const sanction = mockSanction;

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="space-y-6">
      {/* Header - Hidden in print */}
      <div className="flex items-center gap-4 print:hidden">
        <Button variant="ghost" size="icon" onClick={() => navigate(`/admin/lending/sanctions/${id}`)}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div className="flex-1">
          <h1 className="text-2xl font-semibold">Sanction Letter</h1>
          <p className="text-muted-foreground font-mono">{sanction.sanctionNumber}</p>
        </div>
        <div className="flex gap-2">
          <PrintButton />
          <Button variant="outline">
            <Download className="mr-2 h-4 w-4" />
            Download PDF
          </Button>
        </div>
      </div>

      {/* Letter Content */}
      <Card className="max-w-4xl mx-auto print:shadow-none print:border-none">
        <CardContent className="p-8 print:p-0">
          {/* Letterhead */}
          <div className="text-center border-b-2 border-primary pb-4 mb-6">
            <h1 className="text-2xl font-bold text-primary">SMFC FINANCE LIMITED</h1>
            <p className="text-sm text-muted-foreground">
              CIN: U65910DL2020PLC123456 | RBI Reg. No.: N-14.00123
            </p>
            <p className="text-sm text-muted-foreground">
              Corporate Office: 123, Finance Tower, Connaught Place, New Delhi - 110001
            </p>
            <p className="text-sm text-muted-foreground">
              Tel: +91-11-23456789 | Email: loans@smfc.co.in | Web: www.smfc.co.in
            </p>
          </div>

          {/* Reference & Date */}
          <div className="flex justify-between mb-6">
            <div>
              <p className="font-medium">Ref: {sanction.sanctionNumber}</p>
            </div>
            <div>
              <p>
                Date: <DateDisplay date={sanction.sanctionDate} />
              </p>
            </div>
          </div>

          {/* Addressee */}
          <div className="mb-6">
            <p className="font-medium">To,</p>
            <p className="font-medium">{sanction.entity.legalName}</p>
            <p>{sanction.entity.registeredAddress}</p>
            <p className="mt-2">PAN: {sanction.entity.pan}</p>
            <p>CIN: {sanction.entity.cin}</p>
          </div>

          {/* Salutation */}
          <div className="mb-6">
            <p>Dear Sir/Madam,</p>
          </div>

          {/* Subject */}
          <div className="mb-6">
            <p className="font-medium underline">
              Sub: Sanction of {sanction.product.productName} Facility of Rs.{' '}
              {(sanction.sanctionedAmount / 10000000).toFixed(2)} Crore
            </p>
          </div>

          {/* Body */}
          <div className="space-y-4 text-justify">
            <p>
              We are pleased to inform you that the Credit Committee of SMFC Finance Limited has
              approved the following credit facility to your company, subject to terms and conditions
              mentioned herein:
            </p>

            {/* Facility Details Table */}
            <div className="my-6 border rounded-lg overflow-hidden">
              <table className="w-full text-sm">
                <tbody>
                  <tr className="border-b bg-muted/50">
                    <td className="p-3 font-medium w-1/3">Borrower</td>
                    <td className="p-3">{sanction.entity.legalName}</td>
                  </tr>
                  <tr className="border-b">
                    <td className="p-3 font-medium">Nature of Facility</td>
                    <td className="p-3">{sanction.product.productName}</td>
                  </tr>
                  <tr className="border-b bg-muted/50">
                    <td className="p-3 font-medium">Sanctioned Amount</td>
                    <td className="p-3">
                      Rs. <AmountDisplay amount={sanction.sanctionedAmount} showFull /> (Rupees{' '}
                      {formatAmountInWords(sanction.sanctionedAmount)})
                    </td>
                  </tr>
                  <tr className="border-b">
                    <td className="p-3 font-medium">Interest Rate</td>
                    <td className="p-3">
                      {sanction.interestType === 'FLOATING' ? (
                        <>
                          {sanction.baseRate} (presently{' '}
                          <PercentageDisplay value={sanction.currentBaseRate} /> p.a.) +{' '}
                          {sanction.spreadBps / 100}% spread = Effective{' '}
                          <PercentageDisplay value={sanction.effectiveRate} /> p.a. (Floating)
                        </>
                      ) : (
                        <>
                          <PercentageDisplay value={sanction.effectiveRate} /> p.a. (Fixed)
                        </>
                      )}
                    </td>
                  </tr>
                  <tr className="border-b bg-muted/50">
                    <td className="p-3 font-medium">Tenure</td>
                    <td className="p-3">
                      {sanction.tenureMonths} months including moratorium period of{' '}
                      {sanction.moratoriumMonths} months
                    </td>
                  </tr>
                  <tr className="border-b">
                    <td className="p-3 font-medium">Repayment</td>
                    <td className="p-3">
                      {sanction.repaymentMode} ({sanction.repaymentFrequency})
                    </td>
                  </tr>
                  <tr className="border-b bg-muted/50">
                    <td className="p-3 font-medium">Processing Fee</td>
                    <td className="p-3">
                      <PercentageDisplay value={sanction.processingFeePercent} /> of sanctioned
                      amount i.e. Rs. <AmountDisplay amount={sanction.processingFee} /> + applicable
                      GST (payable upfront)
                    </td>
                  </tr>
                  <tr className="border-b">
                    <td className="p-3 font-medium">Validity</td>
                    <td className="p-3">
                      This sanction is valid till <DateDisplay date={sanction.validUntil} />
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            {/* Security */}
            <div className="my-6">
              <h3 className="font-bold mb-2">SECURITY:</h3>
              <ol className="list-decimal list-inside space-y-2 pl-4">
                {sanction.securities.map((sec, index) => (
                  <li key={index}>
                    <span className="font-medium">{sec.securityType}: </span>
                    {sec.description}
                    {sec.value && (
                      <span>
                        {' '}
                        (Valued at Rs. <AmountDisplay amount={sec.value} />)
                      </span>
                    )}
                  </li>
                ))}
              </ol>
            </div>

            {/* Pre-Disbursement Conditions */}
            <div className="my-6">
              <h3 className="font-bold mb-2">PRE-DISBURSEMENT CONDITIONS:</h3>
              <ol className="list-decimal list-inside space-y-2 pl-4">
                {sanction.conditions.preDisbursement.map((cond, index) => (
                  <li key={index}>{cond}</li>
                ))}
              </ol>
            </div>

            {/* Post-Disbursement Conditions */}
            <div className="my-6">
              <h3 className="font-bold mb-2">POST-DISBURSEMENT CONDITIONS:</h3>
              <ol className="list-decimal list-inside space-y-2 pl-4">
                {sanction.conditions.postDisbursement.map((cond, index) => (
                  <li key={index}>{cond}</li>
                ))}
              </ol>
            </div>

            {/* Covenants */}
            <div className="my-6">
              <h3 className="font-bold mb-2">COVENANTS:</h3>
              <ol className="list-decimal list-inside space-y-2 pl-4">
                {sanction.covenants.map((cov, index) => (
                  <li key={index}>{cov}</li>
                ))}
              </ol>
            </div>

            {/* Special Conditions */}
            <div className="my-6">
              <h3 className="font-bold mb-2">SPECIAL CONDITIONS:</h3>
              <ol className="list-decimal list-inside space-y-2 pl-4">
                {sanction.specialConditions.map((cond, index) => (
                  <li key={index}>{cond}</li>
                ))}
              </ol>
            </div>

            {/* General Terms */}
            <div className="my-6">
              <h3 className="font-bold mb-2">GENERAL TERMS:</h3>
              <ol className="list-decimal list-inside space-y-2 pl-4">
                <li>
                  This sanction letter is subject to the detailed terms and conditions of the Loan
                  Agreement to be executed at the time of disbursement.
                </li>
                <li>
                  SMFC reserves the right to recall/cancel the facility at any time without assigning
                  any reason.
                </li>
                <li>
                  Any changes in the constitution of the Borrower shall be intimated to SMFC
                  immediately.
                </li>
                <li>
                  The Borrower shall not avail any additional credit facility from any other
                  lender/institution without prior written consent of SMFC.
                </li>
                <li>
                  SMFC shall have the right to inspect the assets, books of accounts, and other
                  records of the Borrower at any time.
                </li>
              </ol>
            </div>

            {/* Acceptance */}
            <p className="mt-6">
              Please return a copy of this letter duly signed and stamped as a token of your
              acceptance of the above terms and conditions within 15 days from the date of this
              letter, failing which this sanction shall stand withdrawn automatically without any
              further notice.
            </p>

            <p className="mt-4">
              We look forward to a long and mutually beneficial relationship.
            </p>
          </div>

          {/* Signature Block */}
          <div className="mt-12">
            <p>Yours faithfully,</p>
            <p className="font-bold mt-8">For SMFC Finance Limited</p>
            <div className="mt-16">
              <p className="border-t border-black pt-2 w-48">Authorized Signatory</p>
            </div>
          </div>

          {/* Acceptance Block */}
          <div className="mt-12 pt-6 border-t-2 border-dashed">
            <h3 className="font-bold mb-4">BORROWER'S ACCEPTANCE</h3>
            <p className="text-sm">
              We have read and understood all the terms and conditions mentioned in this sanction
              letter. We hereby accept the same unconditionally and agree to abide by all the terms
              and conditions mentioned herein and in the loan agreement to be executed.
            </p>
            <div className="mt-8 grid grid-cols-2 gap-8">
              <div>
                <p className="font-medium">For {sanction.entity.legalName}</p>
                <div className="mt-16 border-t border-black pt-2">
                  <p>Authorized Signatory</p>
                  <p className="text-sm text-muted-foreground">Name:</p>
                  <p className="text-sm text-muted-foreground">Designation:</p>
                </div>
              </div>
              <div>
                <p className="font-medium">Date of Acceptance:</p>
                <div className="mt-16 border-t border-black pt-2">
                  <p>Company Seal</p>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
