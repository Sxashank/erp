import { AmountDisplay } from '@/components/common';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { VerificationSchedule } from '@/types/fixed-assets';

export function VerificationProgressCard({
  schedule,
}: {
  schedule: VerificationSchedule;
}): JSX.Element {
  const verifiedPercent =
    schedule.totalAssets > 0
      ? Math.round((schedule.verifiedCount / schedule.totalAssets) * 100)
      : 0;

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-medium">Verification Progress</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div>
          <div className="mb-2 flex items-center justify-between text-sm">
            <span>{schedule.verifiedCount} of {schedule.totalAssets} verified</span>
            <span className="font-medium">{verifiedPercent}%</span>
          </div>
          <div className="h-2 rounded-full bg-muted">
            <div
              className="h-2 rounded-full bg-emerald-500"
              style={{ width: `${verifiedPercent}%` }}
            />
          </div>
        </div>
        <div className="grid gap-3 sm:grid-cols-2">
          <div>
            <div className="text-xs text-muted-foreground">Missing assets</div>
            <div className="text-lg font-semibold text-red-600">{schedule.missingCount}</div>
          </div>
          <div>
            <div className="text-xs text-muted-foreground">Discrepancies</div>
            <div className="text-lg font-semibold text-amber-600">{schedule.discrepancyCount}</div>
          </div>
          <div>
            <div className="text-xs text-muted-foreground">Value verified</div>
            <AmountDisplay amount={schedule.totalValueVerified} className="text-lg font-semibold" />
          </div>
          <div>
            <div className="text-xs text-muted-foreground">Value missing</div>
            <AmountDisplay amount={schedule.totalValueMissing} className="text-lg font-semibold text-red-600" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
