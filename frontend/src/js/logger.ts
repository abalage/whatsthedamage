/* eslint-disable no-console -- the logger is the single console wrapper */
/**
 * Minimal logger that suppresses non-error output in production builds.
 *
 * Use instead of the console directly so diagnostics never leak to
 * end users; errors are still reported in production because they
 * indicate bugs worth surfacing in the browser console.
 * @module utils/logger
 */

const isDev = import.meta.env.DEV

export const logger = {
  /** Diagnostic output, suppressed in production builds */
  debug(...args: unknown[]): void {
    if (isDev) {
      console.debug(...args)
    }
  },
  /** Warnings, suppressed in production builds */
  warn(...args: unknown[]): void {
    if (isDev) {
      console.warn(...args)
    }
  },
  /** Errors, always reported */
  error(...args: unknown[]): void {
    console.error(...args)
  }
}
