import { Edit, Settings } from 'lucide-react';
import { useNavigate, useParams } from 'react-router-dom';

import { EmptyState } from '@/components/common/EmptyState';
import { ErrorState } from '@/components/common/ErrorState';
import { PageHeader } from '@/components/common/PageHeader';
import { AmountDisplay } from '@/components/lending/common/AmountDisplay';
import { PercentageDisplay } from '@/components/lending/common/PercentageDisplay';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useLoanProduct } from '@/hooks/lending/useLoanProduct';

export default function ProductView() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { data: product, isLoading, isError, error, refetch } = useLoanProduct(id);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <PageHeader title="Loan Product" subtitle="Loading..." />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (isError || !product) {
    return (
      <div className="space-y-6">
        <PageHeader title="Loan Product" />
        <ErrorState title="Could not load product" error={error} onRetry={() => refetch()} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={product.name}
        subtitle={`${product.code} · ${product.category}`}
        breadcrumbs={[
          { label: 'Lending', to: '/admin/lending' },
          { label: 'Products', to: '/admin/lending/products' },
          { label: product.name },
        ]}
        actions={
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={() => navigate(`/admin/lending/products/${id}/checklist`)}
            >
              <Settings className="mr-2 h-4 w-4" />
              Document Checklist
            </Button>
            <Button onClick={() => navigate(`/admin/lending/products/${id}/edit`)}>
              <Edit className="mr-2 h-4 w-4" />
              Edit
            </Button>
          </div>
        }
      />

      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Status</CardTitle>
          </CardHeader>
          <CardContent>
            <Badge
              variant="outline"
              className={
                product.isActive ? 'bg-green-50 text-green-700' : 'bg-gray-50 text-gray-700'
              }
            >
              {product.isActive ? 'ACTIVE' : 'INACTIVE'}
            </Badge>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Amount Range
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-sm">
              <AmountDisplay amount={product.minAmount} abbreviated /> –{' '}
              <AmountDisplay amount={product.maxAmount} abbreviated />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Tenure</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-sm font-medium">
              {product.minTenureMonths}–{product.maxTenureMonths} months
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Interest Type
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Badge variant="outline">{product.interestType}</Badge>
            {product.minEffectiveRate != null && (
              <p className="mt-1 text-xs text-muted-foreground">
                Rate band: <PercentageDisplay value={product.minEffectiveRate} /> –{' '}
                <PercentageDisplay value={product.maxEffectiveRate ?? product.minEffectiveRate} />
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="overview">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="fees">Fees & Charges</TabsTrigger>
          <TabsTrigger value="checklist">Doc Checklist</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4 pt-4">
          <Card>
            <CardHeader>
              <CardTitle>Product Configuration</CardTitle>
            </CardHeader>
            <CardContent>
              <dl className="grid grid-cols-2 gap-4 text-sm md:grid-cols-3">
                <div>
                  <dt className="text-muted-foreground">Code</dt>
                  <dd className="font-mono">{product.code}</dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Category</dt>
                  <dd>{product.category}</dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Sub-category</dt>
                  <dd>{product.subCategory ?? '—'}</dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Min Amount</dt>
                  <dd>
                    <AmountDisplay amount={product.minAmount} />
                  </dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Max Amount</dt>
                  <dd>
                    <AmountDisplay amount={product.maxAmount} />
                  </dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Processing Fee</dt>
                  <dd>{product.defaultSpreadBps} bps default spread</dd>
                </div>
              </dl>
              {product.description && (
                <div className="mt-4 border-t pt-4">
                  <p className="text-sm text-muted-foreground">Description</p>
                  <p className="mt-1 text-sm">{product.description}</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="fees" className="pt-4">
          <Card>
            <CardHeader>
              <CardTitle>Fees & Charges</CardTitle>
              <CardDescription>Product-wise fee schedule</CardDescription>
            </CardHeader>
            <CardContent>
              <EmptyState
                title="Detailed fee list not embedded yet"
                subtitle="Use /lending/products/{id}/details for full fee + checklist data."
              />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="checklist" className="pt-4">
          <Card>
            <CardHeader>
              <CardTitle>Document Checklist</CardTitle>
              <CardDescription>Required documents at each stage</CardDescription>
            </CardHeader>
            <CardContent>
              <EmptyState
                title="Checklist embedded view coming"
                subtitle="Manage checklists at /lending/products/{id}/checklist for now."
                action={
                  <Button
                    variant="outline"
                    onClick={() => navigate(`/admin/lending/products/${id}/checklist`)}
                  >
                    Open Checklist
                  </Button>
                }
              />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
