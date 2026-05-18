import type { AxiosError } from 'axios';

interface FastApiValidationError {
  loc?: (string | number)[];
  msg?: string;
}

interface ApiErrorPayload {
  error_code?: string;
  message?: unknown;
  detail?: unknown;
  correlation_id?: string;
}

function describeDetail(detail: unknown): string | undefined {
  if (!detail) return undefined;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => {
        if (!item || typeof item !== 'object') return undefined;
        const validationError = item as FastApiValidationError;
        const field = validationError.loc?.filter((part) => part !== 'body').join('.');
        return validationError.msg
          ? `${field ? `${field}: ` : ''}${validationError.msg}`
          : undefined;
      })
      .filter(Boolean);
    return messages.length > 0 ? messages.join('; ') : undefined;
  }
  if (typeof detail === 'object') {
    return JSON.stringify(detail);
  }
  return String(detail);
}

export function getErrorMessage(error: unknown, fallback = 'Something went wrong.'): string {
  if (!error) return fallback;

  const axiosError = error as AxiosError<ApiErrorPayload>;
  if (axiosError.isAxiosError) {
    const data = axiosError.response?.data;
    const dataMessage =
      describeDetail(data?.message) ??
      describeDetail(data?.detail) ??
      axiosError.message ??
      (axiosError.response?.status ? `HTTP ${axiosError.response.status}` : undefined);
    return dataMessage ?? fallback;
  }

  if (error instanceof Error) return error.message;
  if (typeof error === 'string') return error;
  return fallback;
}

export function getErrorCode(error: unknown): string | undefined {
  if (!error) return undefined;
  const axiosError = error as AxiosError<ApiErrorPayload>;
  return axiosError.isAxiosError ? axiosError.response?.data?.error_code : undefined;
}

export function getCorrelationId(error: unknown): string | undefined {
  if (!error) return undefined;
  const axiosError = error as AxiosError<ApiErrorPayload>;
  return axiosError.isAxiosError ? axiosError.response?.data?.correlation_id : undefined;
}
