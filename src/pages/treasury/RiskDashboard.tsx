/**
 * Risk Dashboard — placeholder.
 *
 * This page requires a treasury risk-aggregation pipeline which does not
 * yet exist in the backend:
 *   - A `trs_risk_snapshot` table that records daily aggregated risk
 *     metrics (total exposure, VaR, LCR, NSFR, concentration ratios,
 *     CRAR, Tier-1 utilisation) per organisation.
 *   - A scheduled job (`POST /treasury/risk/recompute`) that walks the
 *     loan portfolio + investments + borrowings + derivatives and
 *     materialises the snapshot, plus an alert engine that compares
 *     each metric to its regulatory / internal limit (RBI Scale-Based
 *     Regulation, single-borrower 15% of Tier-1, group 25%, CRAR ≥ 15%).
 *   - A read endpoint `GET /treasury/risk/dashboard` that returns the
 *     latest snapshot + top-N counterparty exposures + open alerts.
 *
 * Until those land, the page renders an explicit EmptyState rather than
 * fabricated numbers (CLAUDE.md §1 quality bar: treat as core banking).
 *
 * Routed at /admin/treasury/risk-dashboard in src/App.tsx.
 */

import { ArrowLeft, Shield } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

import { EmptyState } from '@/components/common/EmptyState';
import { PageHeader } from '@/components/common/PageHeader';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';

export default function RiskDashboard() {
  const navigate = useNavigate();

  return (
    <div className="space-y-6">
      <PageHeader
        title="Risk Dashboard"
        subtitle="Consolidated treasury and credit risk metrics, alerts, and top exposures"
        actions={
          <Button variant="ghost" onClick={() => navigate('/admin/treasury')}>
            <ArrowLeft className="mr-2 h-4 w-4" /> Back to Treasury
          </Button>
        }
      />

      <Card>
        <CardContent className="py-12">
          <EmptyState
            icon={Shield}
            title="Risk dashboard not yet available"
            subtitle="A treasury risk-aggregation pipeline (trs_risk_snapshot + recompute job + alert engine + GET /treasury/risk/dashboard) must ship before this view can render live metrics. Showing fabricated risk numbers on a regulated NBFC platform is unsafe."
          />
        </CardContent>
      </Card>
    </div>
  );
}
