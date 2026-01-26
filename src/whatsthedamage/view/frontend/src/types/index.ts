/**
 * TypeScript type definitions for What's the Damage frontend
 * @module types
 */

/**
 * Configuration for DataTables
 */
export interface DataTableConfig {
  responsive: boolean;
  fixedHeader: boolean;
  ordering: boolean;
  pageLength: number;
  scrollX: boolean;
  autoWidth: boolean;
  dom: string;
  buttons: {
    extend: 'csv' | 'excel';
    text: string;
    title: string;
  }[];
}

/**
 * Response from statistical analysis API
 */
export interface StatisticalAnalysisResponse {
  status: 'success' | 'error';
  highlights: Record<string, 'outlier' | 'pareto' | 'excluded'>;
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
 * Extended Window interface for global variables
 */
export interface WindowExtensions {
  exportCsvText?: string;
  exportExcelText?: string;
  bootstrap: any;
  resultId?: string;
}

/**
 * Notification type
 */
export type NotificationType = 'success' | 'danger' | 'warning' | 'info';

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