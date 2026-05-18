import { useState } from 'react';

import {
  AmountDisplay,
  DataTable,
  DateDisplay,
  PageHeader,
} from '@/components/common';
import { Button } from '@/components/ui/button';
import { DatePicker } from '@/components/ui/date-picker';
import { Input } from '@/components/ui/input';
import { useAssetRegisterReport, useDepreciationSummaryReport } from '@/hooks/fixed-assets/useReports';
import { useRequiredActiveOrganizationId } from '@/hooks/useOrganization';

function downloadCsv(filename: string, headers: string[], rows: (string | number)[][]): void {
  const content = [
    headers.join(','),
    ...rows.map((row) =>
      row.map((cell) => `"${String(cell ?? '').replace(/"/g, '""')}"`).join(','),
    ),
  ].join('\n');
  const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

export default function FixedAssetReports(): JSX.Element {
  const organizationId = useRequiredActiveOrganizationId();
  const [asOnDate, setAsOnDate] = useState<Date | null>(new Date());
  const [depreciationPeriod, setDepreciationPeriod] = useState(
    new Date().toISOString().slice(0, 7),
  );

  const assetRegisterQuery = useAssetRegisterReport({
    organizationId,
    asOnDate: asOnDate ? asOnDate.toISOString().slice(0, 10) : undefined,
  });
  const depreciationSummaryQuery = useDepreciationSummaryReport(organizationId, depreciationPeriod);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Fixed Asset Reports"
        subtitle="Review the asset register and monthly depreciation summary without leaving the fixed-assets module."
        breadcrumbs={[{ label: 'Fixed Assets' }, { label: 'Reports' }]}
      />

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-lg border bg-background p-4">
          <div className="mb-4 flex items-center justify-between gap-4">
            <div>
              <h2 className="text-base font-semibold">Asset Register</h2>
              <p className="text-sm text-muted-foreground">As-on reporting for active fixed assets.</p>
            </div>
            <Button
              type="button"
              variant="outline"
              onClick={() =>
                downloadCsv(
                  'fixed-asset-register.csv',
                  ['Asset Code', 'Asset Name', 'Category', 'Location', 'Acquisition Date', 'Cost', 'Accumulated Depreciation', 'WDV'],
                  (assetRegisterQuery.data?.assets ?? []).map((asset) => [
                    asset.assetCode,
                    asset.assetName,
                    asset.categoryName,
                    asset.locationName ?? '',
                    asset.acquisitionDate,
                    asset.acquisitionCost,
                    asset.accumulatedDepreciation,
                    asset.wdvValue,
                  ]),
                )
              }
            >
              Export CSV
            </Button>
          </div>
          <div className="mb-4 max-w-[220px]">
            <DatePicker date={asOnDate} onSelect={(value) => setAsOnDate(value ?? null)} />
          </div>
          <div className="grid gap-4 md:grid-cols-3">
            <MetricCard label="Total Cost" value={<AmountDisplay amount={assetRegisterQuery.data?.totalCost} abbreviated />} />
            <MetricCard label="Accumulated Depreciation" value={<AmountDisplay amount={assetRegisterQuery.data?.totalAccumulatedDepreciation} abbreviated />} />
            <MetricCard label="Total WDV" value={<AmountDisplay amount={assetRegisterQuery.data?.totalWdv} abbreviated />} />
          </div>
          <div className="mt-4">
            <DataTable
              data={assetRegisterQuery.data?.assets ?? []}
              columns={[
                { key: 'assetCode', header: 'Asset code' },
                { key: 'assetName', header: 'Asset name' },
                { key: 'categoryName', header: 'Category' },
                { key: 'locationName', header: 'Location' },
                {
                  key: 'acquisitionDate',
                  header: 'Acquired',
                  render: (row) => <DateDisplay date={row.acquisitionDate} />,
                },
                {
                  key: 'wdvValue',
                  header: 'WDV',
                  align: 'right',
                  render: (row) => <AmountDisplay amount={row.wdvValue} compact />,
                },
              ]}
              getRowId={(row) => row.id}
              isLoading={assetRegisterQuery.isLoading}
              error={assetRegisterQuery.error}
              onRetry={() => assetRegisterQuery.refetch()}
              emptyTitle="No assets available for this as-on date"
            />
          </div>
        </div>

        <div className="rounded-lg border bg-background p-4">
          <div className="mb-4 flex items-center justify-between gap-4">
            <div>
              <h2 className="text-base font-semibold">Depreciation Summary</h2>
              <p className="text-sm text-muted-foreground">Category-wise depreciation for the selected period.</p>
            </div>
            <Button
              type="button"
              variant="outline"
              onClick={() =>
                downloadCsv(
                  'fixed-asset-depreciation-summary.csv',
                  ['Category Code', 'Category Name', 'Asset Count', 'Depreciation', 'Closing WDV'],
                  (depreciationSummaryQuery.data?.byCategory ?? []).map((category) => [
                    category.categoryCode,
                    category.categoryName,
                    category.assetCount,
                    category.totalDepreciation,
                    category.closingWdv,
                  ]),
                )
              }
            >
              Export CSV
            </Button>
          </div>
          <div className="mb-4 max-w-[220px]">
            <Input
              type="month"
              value={depreciationPeriod}
              onChange={(event) => setDepreciationPeriod(event.target.value)}
            />
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <MetricCard label="Assets Included" value={String(depreciationSummaryQuery.data?.totalAssets ?? 0)} />
            <MetricCard label="Period Depreciation" value={<AmountDisplay amount={depreciationSummaryQuery.data?.totalDepreciation} abbreviated />} />
          </div>
          <div className="mt-4">
            <DataTable
              data={depreciationSummaryQuery.data?.byCategory ?? []}
              columns={[
                { key: 'categoryCode', header: 'Category code' },
                { key: 'categoryName', header: 'Category name' },
                {
                  key: 'assetCount',
                  header: 'Assets',
                  align: 'right',
                  render: (row) => row.assetCount.toLocaleString('en-IN'),
                },
                {
                  key: 'totalDepreciation',
                  header: 'Depreciation',
                  align: 'right',
                  render: (row) => <AmountDisplay amount={row.totalDepreciation} compact />,
                },
                {
                  key: 'closingWdv',
                  header: 'Closing WDV',
                  align: 'right',
                  render: (row) => <AmountDisplay amount={row.closingWdv} compact />,
                },
              ]}
              getRowId={(row) => row.categoryId}
              isLoading={depreciationSummaryQuery.isLoading}
              error={depreciationSummaryQuery.error}
              onRetry={() => depreciationSummaryQuery.refetch()}
              emptyTitle="No depreciation data found for this period"
            />
          </div>
        </div>
      </div>
    </div>
  );
}

function MetricCard({
  label,
  value,
}: {
  label: string;
  value: React.ReactNode;
}): JSX.Element {
  return (
    <div className="rounded-lg border p-4">
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className="mt-1 text-xl font-semibold">{value}</div>
    </div>
  );
}
