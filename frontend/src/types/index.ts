/**
 * TypeScript type definitions for What's the Damage frontend
 * @module types
 */

/**
 * Error with additional context
 */
export class AppError extends Error {
  constructor(message: string, public context?: unknown) {
    super(message);
    this.name = 'AppError';
  }
}

/**
 * Error body returned by API v2 endpoints on failures.
 * `error` is the human-readable message; `code` is the
 * machine-readable error code the frontend can branch on
 * (e.g. CSRF_TOKEN_INVALID for the automatic CSRF retry).
 */
export interface ApiErrorBody {
  error?: string;
  message?: string;
  detail?: string;
  code?: string;
  retry_after?: string;
}

