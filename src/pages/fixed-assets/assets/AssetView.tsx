import { ArrowRightLeft, Edit, PackageCheck, ReceiptIndianRupee, ShieldAlert, TrendingDown } from 'lucide-react';
import { useMemo } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

import {
  AmountDisplay,
  DataTable,
  DateDisplay,
  DetailGrid,
  EmptyState,
  ErrorState,
  PageHeader,
  type Column,
} from '@/components/common';
import { FixedAssetStatusPill } from '@/components/fixed-assets/FixedAssetStatusPill';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useFixedAsset, useFixedAssetDepreciationHistory, useFixedAssetDepreciationSchedule } from '@/hooks/fixed-assets/useFixedAssets';
import type { DepreciationEntry } from '@/types/fixed-assets';

export function AssetView(): JSX.Element {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const assetQuery = useFixedAsset(id);
  const historyQuery = useFixedAssetDepreciationHistory(id);
  const scheduleQuery = useFixedAssetDepreciationSchedule(id);

  const historyColumns: Column<DepreciationEntry>[] = useMemo(
    () => [
      {
        key: 'depreciationPeriod',
        header: 'Period',
        render: (row) => row.depreciationPeriod,
      },
      {
        key: 'periodTo',
        header: 'Posted on',
        render: (row) => <DateDisplay date={row.periodTo} />,
      },
      {
        key: 'openingWdv',
        header: 'Opening WDV',
        align: 'right',
        render: (row) => <AmountDisplay amount={row.openingWdv} compact />,
      },
      {
        key: 'depreciationAmount',
        header: 'Depreciation',
        align: 'right',
        render: (row) => <AmountDisplay amount={row.depreciationAmount} compact />,
      },
      {
        key: 'closingWdv',
        header: 'Closing WDV',
        align: 'right',
        render: (row) => <AmountDisplay amount={row.closingWdv} compact />,
      },
    ],
    [],
  );

  if (assetQuery.isLoading) {
    return <Card><CardContent className="py-12 text-sm text-muted-foreground">Loading asset details…</CardContent></Card>;
  }

  if (assetQuery.error) {
    return <ErrorState error={assetQuery.error} onRetry={() => assetQuery.refetch()} />;
  }

  if (!assetQuery.data) {
    return (
      <EmptyState
        title="Asset not found"
        subtitle="The requested asset record is unavailable in the current organization."
        action={
          <Button type="button" onClick={() => navigate('/admin/fixed-assets/assets')}>
            Back to asset register
          </Button>
        }
      />
    );
  }

  const asset = assetQuery.data;
  const canCapitalize = asset.status === 'DRAFT';
  const canLifecycle = asset.status === 'ACTIVE' || asset.status === 'FULLY_DEPRECIATED';

  return (
    <div className="space-y-6">
      <PageHeader
        title={asset.assetName}
        subtitle={asset.assetCode}
        breadcrumbs={[
          { label: 'Fixed Assets' },
          { label: 'Asset Register', to: '/admin/fixed-assets/assets' },
          { label: asset.assetCode },
        ]}
        actions={
          <div className="flex flex-wrap items-center gap-2">
            <FixedAssetStatusPill status={asset.status} />
            {canCapitalize && (
              <Button onClick={() => navigate(`/admin/fixed-assets/assets/${asset.id}/capitalize`)}>
                <PackageCheck className="mr-2 h-4 w-4" />
                Capitalize
              </Button>
            )}
            {asset.status === 'DRAFT' && (
              <Button variant="outline" onClick={() => navigate(`/admin/fixed-assets/assets/${asset.id}/edit`)}>
                <Edit className="mr-2 h-4 w-4" />
                Edit
              </Button>
            )}
            {canLifecycle && (
              <>
                <Button variant="outline" onClick={() => navigate(`/admin/fixed-assets/assets/${asset.id}/transfer`)}>
                  <ArrowRightLeft className="mr-2 h-4 w-4" />
                  Transfer
                </Button>
                <Button variant="outline" onClick={() => navigate(`/admin/fixed-assets/assets/${asset.id}/revalue`)}>
                  <ReceiptIndianRupee className="mr-2 h-4 w-4" />
                  Revalue
                </Button>
                <Button variant="outline" onClick={() => navigate(`/admin/fixed-assets/assets/${asset.id}/impair`)}>
                  <TrendingDown className="mr-2 h-4 w-4" />
                  Impair
                </Button>
                <Button variant="outline" onClick={() => navigate(`/admin/fixed-assets/assets/${asset.id}/dispose`)}>
                  <ShieldAlert className="mr-2 h-4 w-4" />
                  Dispose
                </Button>
              </>
            )}
          </div>
        }
      />

      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total Cost</CardTitle>
          </CardHeader>
          <CardContent>
            <AmountDisplay amount={asset.totalCost} className="text-2xl font-semibold" />
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Accumulated Depreciation</CardTitle>
          </CardHeader>
          <CardContent>
            <AmountDisplay amount={asset.accumulatedDepreciation} className="text-2xl font-semibold text-amber-600" />
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Written Down Value</CardTitle>
          </CardHeader>
          <CardContent>
            <AmountDisplay amount={asset.wdvValue} className="text-2xl font-semibold text-emerald-600" />
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Residual Value</CardTitle>
          </CardHeader>
          <CardContent>
            <AmountDisplay amount={asset.residualValue} className="text-2xl font-semibold" />
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Asset Overview</CardTitle>
        </CardHeader>
        <CardContent>
          <DetailGrid
            columns={3}
            fields={[
              { label: 'Category', value: asset.categoryName ?? '—' },
              { label: 'Location', value: asset.locationName ?? '—' },
              { label: 'Department', value: asset.departmentName ?? '—' },
              { label: 'Acquisition date', value: <DateDisplay date={asset.acquisitionDate} /> },
              { label: 'Put-to-use date', value: <DateDisplay date={asset.putToUseDate} /> },
              { label: 'Vendor', value: asset.vendorName ?? '—' },
              { label: 'Invoice number', value: asset.invoiceNumber ?? '—' },
              { label: 'Invoice date', value: <DateDisplay date={asset.invoiceDate} /> },
              { label: 'PO number', value: asset.poNumber ?? '—' },
              { label: 'Method', value: asset.depreciationMethod.replace(/_/g, ' ') },
              { label: 'Rate', value: `${Number(asset.depreciationRate).toLocaleString('en-IN')}%` },
              { label: 'Useful life', value: `${asset.usefulLifeMonths} months` },
              { label: 'Make', value: asset.make ?? '—' },
              { label: 'Model', value: asset.model ?? '—' },
              { label: 'Serial number', value: asset.serialNumber ?? '—' },
            ]}
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Depreciation Schedule</CardTitle>
        </CardHeader>
        <CardContent>
          {scheduleQuery.isLoading ? (
            <p className="text-sm text-muted-foreground">Loading depreciation schedule…</p>
          ) : scheduleQuery.error ? (
            <ErrorState error={scheduleQuery.error} onRetry={() => scheduleQuery.refetch()} />
          ) : (
            <DataTable
              data={scheduleQuery.data?.schedule ?? []}
              columns={[
                { key: 'period', header: 'Period' },
                {
                  key: 'openingWdv',
                  header: 'Opening WDV',
                  align: 'right',
                  render: (row) => <AmountDisplay amount={row.openingWdv} compact />,
                },
                {
                  key: 'depreciationAmount',
                  header: 'Depreciation',
                  align: 'right',
                  render: (row) => <AmountDisplay amount={row.depreciationAmount} compact />,
                },
                {
                  key: 'closingWdv',
                  header: 'Closing WDV',
                  align: 'right',
                  render: (row) => <AmountDisplay amount={row.closingWdv} compact />,
                },
              ]}
              getRowId={(row) => row.period}
              emptyTitle="No depreciation schedule available"
              emptySubtitle="Capitalize the asset to generate its depreciation timeline."
            />
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Posted Depreciation History</CardTitle>
        </CardHeader>
        <CardContent>
          <DataTable
            data={historyQuery.data?.items ?? []}
            columns={historyColumns}
            getRowId={(row) => row.id}
            isLoading={historyQuery.isLoading}
            error={historyQuery.error}
            onRetry={() => historyQuery.refetch()}
            emptyTitle="No depreciation history yet"
            emptySubtitle="Run monthly depreciation after capitalization to populate this ledger."
          />
        </CardContent>
      </Card>
    </div>
  );
}
