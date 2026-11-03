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

/**
 * One slide of the landing page feature slideshow.
 * Message slides show a title/text; image slides show a screenshot
 * served from frontend/public (CSP img-src 'self').
 */
export interface FeatureSlide {
  type: 'message' | 'image';
  title?: string;
  text?: string;
  src?: string;
  alt?: string;
}

