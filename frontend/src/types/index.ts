/**
 * TypeScript type definitions for What's the Damage frontend
 * @module types
 */

/**
 * Response from statistical analysis API
 */
export interface StatisticalAnalysisResponse {
  status: 'success' | 'error';
  highlights: Record<string, string[]> | {};  // row_id -> array of highlight types
  error?: string;
}

/**
 * Request payload for statistical analysis
 */
export interface StatisticalAnalysisRequest {
  result_id: string;
  algorithms: string[];
  direction: 'columns' | 'rows';
  use_default_directions?: boolean;
}

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
 * API response wrapper
 */
export interface ApiResponse<T> {
  data: T;
  status: number;
  ok: boolean;
  error?: string;
}