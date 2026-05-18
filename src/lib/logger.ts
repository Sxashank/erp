/**
 * Frontend logger. See CLAUDE.md §5.12.
 *
 * - Silent in production builds (only `error` survives, because production
 *   errors are real signal and must reach error-reporting telemetry).
 * - Styled console output in development.
 * - Never log PII; never log raw API response bodies.
 *
 * Do NOT use `console.log` directly. If you need a quick dev trace, use
 * `logger.debug(...)`.
 */

type Level = "debug" | "info" | "warn" | "error";

const isProd = import.meta.env.MODE === "production";

const STYLES: Record<Level, string> = {
  debug: "color:#64748b;font-weight:500",
  info: "color:#2563eb;font-weight:500",
  warn: "color:#d97706;font-weight:600",
  error: "color:#dc2626;font-weight:700",
};

function emit(level: Level, args: unknown[]): void {
  if (isProd && level !== "error") return;

  const [first, ...rest] = args;
  const label = `%c[${level.toUpperCase()}]`;


  const sink: (...a: unknown[]) => void =
    level === "error"
      ? console.error
      : level === "warn"
        ? console.warn
        : console.info;

  if (typeof first === "string") {
    sink(label, STYLES[level], first, ...rest);
  } else {
    sink(label, STYLES[level], ...args);
  }
}

export const logger = {
  debug: (...args: unknown[]): void => emit("debug", args),
  info: (...args: unknown[]): void => emit("info", args),
  warn: (...args: unknown[]): void => emit("warn", args),
  error: (...args: unknown[]): void => emit("error", args),
};

export type Logger = typeof logger;
