/**
 * Error-code → user-facing toast title/description mapping.
 *
 * The backend error envelope (see CLAUDE.md §7) is:
 *
 *     { error_code: "STRING_CODE", message: "Human-readable",
 *       details?: {...}, correlation_id: "uuid" }
 *
 * Mutations that fail should call `showErrorToast(err, toast)` with the
 * AxiosError they caught. Known error codes map to a tuned message; unknown
 * codes fall through to the backend's `message` string + a correlation-id
 * affordance so on-call can trace the incident.
 *
 * See CLAUDE.md §9.5 (mutating button UX) and STAGE-4-004 (maker-checker).
 */

import type { AxiosError } from 'axios';

export interface AppErrorEnvelope {
  error_code?: string;
  message?: string;
  details?: unknown;
  correlation_id?: string;
}

/** Shape of the `toast` helper from `@/hooks/use-toast`. */
export type ToastFn = (args: {
  title?: string;
  description?: string;
  variant?: 'default' | 'destructive';
}) => void;

interface Mapped {
  title: string;
  description: string;
}

/**
 * Tuned error-code → title/description mapping.
 *
 * Add an entry here whenever the backend adds a code that has a better
 * user-facing story than the raw message (e.g. turning the generic "Maker
 * cannot approve their own submission" into something that tells the user
 * who SHOULD approve it instead).
 */
const ERROR_CODE_MAP: Readonly<Record<string, Mapped>> = {
  MAKER_EQUALS_CHECKER: {
    title: 'Approval blocked — maker-checker',
    description:
      'You submitted this record, so you cannot also approve it. Ask a different authorised user to approve.',
  },
  WEBHOOK_NOT_CONFIGURED: {
    title: 'Integration not configured',
    description:
      'The vendor credentials for this organisation have not been provisioned yet. Admin: set them in Admin → Integrations.',
  },
  INVALID_WEBHOOK_SIGNATURE: {
    title: 'Webhook rejected',
    description: 'Signature did not match. The vendor may have rotated their secret.',
  },
  WEBHOOK_TIMESTAMP_EXPIRED: {
    title: 'Webhook rejected',
    description: 'Timestamp is outside the accepted window. Possible replay attempt.',
  },
  UPLOAD_INFECTED: {
    title: 'Upload rejected — virus detected',
    description:
      'The antivirus scanner flagged this file. Upload a clean version or contact security.',
  },
  UPLOAD_TOO_LARGE: {
    title: 'Upload too large',
    description: 'File exceeds the 50 MB limit.',
  },
  CONTENT_TYPE_DENIED: {
    title: 'File type not permitted',
    description: 'This content type is on the deny list. Try a PDF or an image.',
  },
  CONTENT_TYPE_MISMATCH: {
    title: 'Upload rejected',
    description:
      'The file contents do not match the declared type. Do not rename files with a different extension.',
  },
  CONCURRENCY_CONFLICT: {
    title: 'Update conflict',
    description:
      'Someone else updated this record while you were working on it. Refresh and try again.',
  },
  CLOSED_PERIOD: {
    title: 'Cannot post',
    description: 'This financial period is closed. Reversals go to the next open period.',
  },
  GL_UNBALANCED: {
    title: 'Voucher rejected',
    description: 'Debit and credit totals do not balance.',
  },
};

/**
 * Extract the typed envelope from an AxiosError. Returns `undefined` if the
 * response wasn't shaped like our error envelope (e.g. a network failure or
 * a non-JSON error page from a reverse proxy).
 */
export function getErrorEnvelope(err: unknown): AppErrorEnvelope | undefined {
  const axiosErr = err as AxiosError<AppErrorEnvelope> | undefined;
  const data = axiosErr?.response?.data;
  if (!data || typeof data !== 'object') return undefined;
  // FastAPI's default `{detail: "..."}` isn't our envelope — skip.
  if (!('error_code' in data) && !('message' in data)) return undefined;
  return data;
}

/**
 * Map an AxiosError / thrown value to a toast payload. Exported separately
 * from {@link showErrorToast} so tests can assert on the mapping without
 * mounting a toast provider.
 */
export function mapErrorToToast(err: unknown): {
  title: string;
  description: string;
  variant: 'destructive';
} {
  const envelope = getErrorEnvelope(err);
  const code = envelope?.error_code;

  if (code && ERROR_CODE_MAP[code]) {
    const mapped = ERROR_CODE_MAP[code];
    // Suffix the correlation id so support can trace the request without
    // the user needing to copy-paste a stack trace.
    const trace = envelope?.correlation_id ? ` (ref: ${envelope.correlation_id.slice(0, 8)})` : '';
    return {
      title: mapped.title,
      description: mapped.description + trace,
      variant: 'destructive',
    };
  }

  // Unknown code — show the backend's message verbatim if we have one, else
  // fall through to a generic message. Either way include the correlation id.
  const description =
    envelope?.message ?? (err as { message?: string })?.message ?? 'An unexpected error occurred.';
  const trace = envelope?.correlation_id ? ` (ref: ${envelope.correlation_id.slice(0, 8)})` : '';
  return {
    title: 'Something went wrong',
    description: description + trace,
    variant: 'destructive',
  };
}

/**
 * One-call convenience for mutation `onError` handlers:
 *
 *     const toast = useToast();
 *     const mutation = useMutation({
 *       mutationFn: ...,
 *       onError: (err) => showErrorToast(err, toast),
 *     });
 */
export function showErrorToast(err: unknown, toast: ToastFn): void {
  toast(mapErrorToToast(err));
}
