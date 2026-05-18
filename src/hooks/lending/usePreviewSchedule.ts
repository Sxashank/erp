/**
 * usePreviewSchedule — wraps POST /lending/schedules/preview.
 *
 * Preview is a pure computation: no Idempotency-Key (nothing is persisted),
 * no permission gate, no organization scoping. Returns the full row set +
 * summary keyed for the calculator UI.
 */

import { useMutation } from '@tanstack/react-query';

import {
  previewSchedule,
  type SchedulePreviewRequest,
  type SchedulePreviewResponse,
} from '@/services/lending/scheduleApi';

export function usePreviewSchedule() {
  return useMutation<SchedulePreviewResponse, Error, SchedulePreviewRequest>({
    mutationFn: previewSchedule,
  });
}
