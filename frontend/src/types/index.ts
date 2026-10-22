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
