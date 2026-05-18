/**
 * Value-at-Risk (VaR) Report — placeholder.
 *
 * This page requires a market-risk VaR engine which does not yet exist
 * in the backend:
 *   - A portfolio P&L time-series store (daily mark-to-market for
 *     investments, derivatives, foreign-currency exposures, and rate-
 *     sensitive instruments) keyed by `(organization_id, portfolio_id,
 *     business_date)`.
 *   - A VaR computation engine supporting historical-simulation and
 *     parametric methods, configurable horizons (1-day, 10-day) and
 *     confidence levels (95%, 99%), plus a backtesting module that
 *     compares predicted VaR against realised P&L and flags
 *     exceedances per Basel traffic-light test.
 *   - A `trs_var_run` model + `GET /treasury/risk/var/runs` endpoint
 *     that surfaces by-portfolio, by-risk-factor, and trend data.
 *
 * Until those land, the page renders an explicit EmptyState rather than
 * fabricated numbers (CLAUDE.md §1 quality bar: treat as core banking).
 *
 * Routed at /admin/treasury/var-report in src/App.tsx.
 */

import { ArrowLeft, TrendingDown } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

import { EmptyState } from '@/components/common/EmptyState';
import { PageHeader } from '@/components/common/PageHeader';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';

export default function VaRReport() {
  const navigate = useNavigate();

  return (
    <div className="space-y-6">
      <PageHeader
        title="Value-at-Risk (VaR) Report"
        subtitle="Portfolio VaR by method, risk factor, and backtest performance"
        actions={
          <Button variant="ghost" onClick={() => navigate('/admin/treasury')}>
            <ArrowLeft className="mr-2 h-4 w-4" /> Back to Treasury
          </Button>
        }
      />

      <Card>
        <CardContent className="py-12">
          <EmptyState
            icon={TrendingDown}
            title="VaR analytics not yet available"
            subtitle="A VaR engine (historical-simulation / parametric / Monte Carlo), a daily portfolio P&L store, the trs_var_run model, and a backtesting module must ship before this view can render live numbers. Fake VaR on a regulated NBFC platform is unsafe."
          />
        </CardContent>
      </Card>
    </div>
  );
}
