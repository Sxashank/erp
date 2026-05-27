import { Database } from 'lucide-react';
import { Link } from 'react-router-dom';

import { ErrorState, PageHeader, SkeletonTable } from '@/components/common';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useLendingMasterCatalog } from '@/hooks/lending/useLendingMasters';
import type { MasterCatalogItem } from '@/services/lending/masterDataApi';

export default function MastersHub(): JSX.Element {
  const { data, isLoading, isError, error, refetch } = useLendingMasterCatalog();

  if (isLoading) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Lending master data"
          subtitle="Single source of truth for lending, checklist, treasury and borrowing setup"
          breadcrumbs={[{ label: 'Lending', to: '/admin/lending' }, { label: 'Masters' }]}
        />
        <SkeletonTable rows={6} columns={2} />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="Lending master data"
          breadcrumbs={[{ label: 'Lending', to: '/admin/lending' }, { label: 'Masters' }]}
        />
        <ErrorState error={error} onRetry={() => refetch()} />
      </div>
    );
  }

  const grouped = (data?.items ?? []).reduce<Record<string, MasterCatalogItem[]>>((acc, item) => {
    acc[item.group] = [...(acc[item.group] ?? []), item];
    return acc;
  }, {});

  return (
    <div className="space-y-6">
      <PageHeader
        title="Lending master data"
        subtitle="One governed setup command center. Settings links route here; workflows consume these rows."
        breadcrumbs={[{ label: 'Lending', to: '/admin/lending' }, { label: 'Masters' }]}
      />

      {Object.entries(grouped).map(([group, masters]) => (
        <section key={group} className="space-y-3">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
            {group}
          </h2>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {masters
              .slice()
              .sort((a, b) => a.label.localeCompare(b.label))
              .map((master) => (
                <Card key={master.key}>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-base">
                      <Database className="h-4 w-4 text-muted-foreground" />
                      {master.label}
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <p className="min-h-10 text-sm text-muted-foreground">{master.description}</p>
                    <div className="text-xs text-muted-foreground">
                      <div>
                        <span className="font-medium">SSOT:</span> {master.sourceOfTruth}
                      </div>
                      <div>
                        <span className="font-medium">Seed:</span> {master.seedSource}
                      </div>
                    </div>
                    <Link
                      to={`/admin/lending/masters/${master.key}`}
                      className="inline-block text-sm text-primary hover:underline"
                    >
                      Open editor
                    </Link>
                  </CardContent>
                </Card>
              ))}
          </div>
        </section>
      ))}
    </div>
  );
}
