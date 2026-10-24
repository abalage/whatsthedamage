/**
 * Processing, category, and CSV profile API functions
 * @module utils/api/processing
 */

import { API_BASE_URL, getApiUrl, postData, request } from './request'
import type {
  CategoryDefinition,
  CsvProfile,
  ProcessingResultCreationResponse,
  ProcessingResultListItem,
  ProcessingResultMetadata,
  RecalculateApiResponse
} from '../../types/api'

/**
 * Process transactions via API (multipart form upload; the browser
 * sets the Content-Type with boundary)
 *
 * @param formData - Form data containing CSV and config files
 * @returns Promise with processing result metadata (flat structure)
 * @throws AppError if processing fails
 */
export async function createTransaction(formData: FormData): Promise<ProcessingResultCreationResponse> {
  // The body is multipart; request() lets the browser set the
  // Content-Type with boundary and attaches the CSRF token
  return request<ProcessingResultCreationResponse>(
    `${API_BASE_URL}/processing-results`,
    { method: 'POST', body: formData }
  )
}

/**
 * Recalculate statistics
 * @param resultId - Result ID, or undefined to use all of the user's transactions
 * @param algorithms - Algorithms to use
 * @param direction - Direction (columns/rows)
 * @returns Promise with statistics result
 */
export async function recalculateStatistics(
  resultId: string | undefined,
  algorithms: string[],
  direction: 'columns' | 'rows'
): Promise<RecalculateApiResponse> {
  return postData<RecalculateApiResponse>(getApiUrl('/recalculate-statistics'), {
    result_id: resultId,
    algorithms,
    direction,
  })
}

/**
 * Fetch all category definitions
 * @returns Promise with array of CategoryDefinition objects
 */
export async function fetchCategories(): Promise<CategoryDefinition[]> {
  return request<CategoryDefinition[]>(getApiUrl('/categories'))
}

/**
 * Fetch cost of living category definition
 * @returns Promise with array of CategoryDefinition objects
 */
export async function fetchCostOfLivingCategories(): Promise<CategoryDefinition[]> {
  return request<CategoryDefinition[]>(getApiUrl('/categories/cost-of-living'))
}

/**
 * Fetch all CSV profiles
 * @returns Promise with array of CsvProfile objects
 */
export async function fetchAllCsvProfiles(): Promise<CsvProfile[]> {
  return request<CsvProfile[]>(getApiUrl('/csv-profiles'))
}

/**
 * Fetch all processing results for the authenticated user
 * @returns Promise with array of ProcessingResultListItem objects
 */
export async function fetchProcessingResults(): Promise<ProcessingResultListItem[]> {
  return request<ProcessingResultListItem[]>(getApiUrl('/processing-results'))
}

/**
 * Fetch processing result metadata
 * @param resultId - Result ID, or undefined to skip the lookup
 * @returns Promise with ProcessingResultMetadata, or undefined when no resultId is given
 */
export async function fetchProcessingResultMetadata(resultId?: string): Promise<ProcessingResultMetadata | undefined> {
  if (!resultId) {
    return undefined
  }
  return request<ProcessingResultMetadata>(getApiUrl(`/processing-results/${encodeURIComponent(resultId)}`))
}
