import { Car, Laptop, Monitor, Package, Smartphone } from 'lucide-react';

import { AmountDisplay } from '@/components/common/AmountDisplay';
import { DataTable, type Column } from '@/components/common/DataTable';
import { DateDisplay } from '@/components/common/DateDisplay';
import { PageHeader } from '@/components/common/PageHeader';
import { StatusPill } from '@/components/common/StatusPill';
import { Card, CardContent } from '@/components/ui/card';
import { useAssignedAssets } from '@/hooks/ess/useEssOperations';
import type { ESSAssignedAsset } from '@/services/essApi';

function AssetMetric({
  title,
  value,
  subtitle,
  icon: Icon,
}: {
  title: string;
  value: string | number;
  subtitle: string;
  icon: typeof Package;
}) {
  return (
    <Card>
      <CardContent className="flex items-start justify-between pt-6">
        <div>
          <p className="text-sm text-muted-foreground">{title}</p>
          <p className="mt-2 text-3xl font-semibold">{value}</p>
          <p className="mt-1 text-xs text-muted-foreground">{subtitle}</p>
        </div>
        <div className="rounded-full bg-muted p-3">
          <Icon className="h-5 w-5 text-muted-foreground" />
        </div>
      </CardContent>
    </Card>
  );
}

function assetIconForCategory(category: string) {
  const normalized = category.toLowerCase();
  if (normalized.includes('laptop')) return Laptop;
  if (normalized.includes('monitor')) return Monitor;
  if (normalized.includes('mobile') || normalized.includes('phone')) return Smartphone;
  if (normalized.includes('vehicle') || normalized.includes('car')) return Car;
  return Package;
}

export default function ESSAssetList() {
  const assetsQuery = useAssignedAssets();
  const assets = assetsQuery.data?.items ?? [];

  const columns: Column<ESSAssignedAsset>[] = [
    {
      key: 'assetName',
      header: 'Asset',
      render: (row) => {
        const Icon = assetIconForCategory(row.category);
        return (
          <div className="flex items-center gap-3">
            <div className="rounded-full bg-muted p-2">
              <Icon className="h-4 w-4 text-muted-foreground" />
            </div>
            <div>
              <div className="font-medium">{row.assetName}</div>
              <div className="text-xs text-muted-foreground">{row.category}</div>
            </div>
          </div>
        );
      },
    },
    { key: 'assetCode', header: 'Asset Code' },
    { key: 'serialNumber', header: 'Serial #' },
    {
      key: 'assignedDate',
      header: 'Assigned',
      render: (row) => <DateDisplay date={row.assignedDate} />,
      sortable: true,
      sortValue: (row) => row.assignedDate,
    },
    {
      key: 'status',
      header: 'Status',
      render: (row) => <StatusPill type="application" status={row.status} />,
    },
    {
      key: 'totalCost',
      header: 'Value',
      align: 'right',
      render: (row) => <AmountDisplay amount={row.totalCost} />,
      sortable: true,
      sortValue: (row) => row.totalCost,
    },
  ];

  const itEquipmentCount = assets.filter((asset) =>
    ['laptop', 'monitor', 'mobile', 'phone'].some((needle) =>
      asset.category.toLowerCase().includes(needle),
    ),
  ).length;
  const returnRequiredCount = assets.filter((asset) => asset.returnRequired).length;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Assigned Assets"
        subtitle="View company assets in your custody, assignment dates, and return obligations."
      />

      <div className="grid gap-4 md:grid-cols-4">
        <AssetMetric
          title="Assigned Assets"
          value={assetsQuery.data?.totalAssets ?? 0}
          subtitle="Assets currently assigned"
          icon={Package}
        />
        <AssetMetric
          title="IT Equipment"
          value={itEquipmentCount}
          subtitle="Laptops, monitors, and mobiles"
          icon={Laptop}
        />
        <AssetMetric
          title="Return Required"
          value={returnRequiredCount}
          subtitle="Must be returned on transfer or separation"
          icon={Car}
        />
        <Card>
          <CardContent className="pt-6">
            <p className="text-sm text-muted-foreground">Total Asset Value</p>
            <div className="mt-2 text-3xl font-semibold">
              <AmountDisplay amount={assetsQuery.data?.totalAssetValue ?? 0} compact />
            </div>
            <p className="mt-1 text-xs text-muted-foreground">Original capitalized value</p>
          </CardContent>
        </Card>
      </div>

      <DataTable
        data={assets}
        columns={columns}
        getRowId={(row) => row.id}
        isLoading={assetsQuery.isLoading}
        error={assetsQuery.error}
        onRetry={() => void assetsQuery.refetch()}
        emptyTitle="No assigned assets"
        emptySubtitle="Assets with employee custody will appear here once fixed-asset assignment is recorded."
      />

      <Card className="bg-muted/30">
        <CardContent className="pt-6 text-sm text-muted-foreground">
          Assigned assets are part of the employee custody record. Report damage, loss, or transfer
          requirements through the internal helpdesk so HR and admin teams can update the fixed
          asset register and return obligations.
        </CardContent>
      </Card>
    </div>
  );
}
