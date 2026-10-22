/**
 * Transaction API functions: listing, filtering, corrections, and
 * aggregations
 * @module utils/api/transactions
 */

import { getApiUrl, request } from './request'
import type {
  AggregatedTransactionsResponse,
  TransactionListItem,
  TransactionListResponse,
  TransactionUpdatePayload
} from '../../types/api'

/**
 * Statistical analysis options for aggregation and recalculation endpoints
 */
export interface StatisticalAnalysisOptions {
  algorithms?: string[]
  direction?: 'columns' | 'rows'
}

/**
 * Fetch transactions, optionally limited to a specific processing result
 * @param resultId - Result ID, or undefined to fetch transactions across all results
 * @param options - Filter and pagination options
 * @returns Promise with TransactionListResponse
 */
export async function fetchTransactionsByResult(
  resultId?: string,
  options: {
    limit?: number
    offset?: number
    account?: string
    categoryId?: string
    month?: string
    sortBy?: string
    sortOrder?: string
  } = {}
): Promise<TransactionListResponse> {
  const params = new URLSearchParams()
  if (resultId) params.append('result_id', resultId)
  if (options.limit !== undefined) params.append('limit', options.limit.toString())
  if (options.offset !== undefined) params.append('offset', options.offset.toString())
  if (options.account) params.append('account', options.account)
  if (options.categoryId) params.append('category_id', options.categoryId)
  if (options.month) params.append('month', options.month)
  if (options.sortBy) params.append('sort_by', options.sortBy)
  if (options.sortOrder) params.append('sort_order', options.sortOrder)

  const query = params.toString()

  return request<TransactionListResponse>(
    getApiUrl(query ? `/transactions?${query}` : '/transactions'))
}

/**
 * Page size used when fetching the complete dataset with paginated requests
 */
const TRANSACTION_PAGE_SIZE = 2000

/**
 * Safety cap for fetch-all queries; the transaction views show a truncation
 * warning when a dataset reaches this size
 */
const MAX_FETCHED_TRANSACTIONS = 50000

/**
 * Fetch the complete transaction dataset, optionally limited to a specific
 * processing result, by paging through the transactions endpoint until
 * total_count rows are collected (or MAX_FETCHED_TRANSACTIONS is reached).
 * Intended for views that aggregate transactions client-side, where a single
 * limited request would silently drop rows.
 * @param resultId - Result ID, or undefined to fetch transactions across all results
 * @param options - Filter options (sorting applies to every page request)
 * @returns Promise with the complete TransactionListResponse
 */
export async function fetchAllTransactions(
  resultId?: string,
  options: {
    account?: string
    categoryId?: string
    month?: string
    sortBy?: string
    sortOrder?: string
  } = {}
): Promise<TransactionListResponse> {
  const firstPage = await fetchTransactionsByResult(resultId, {
    ...options,
    limit: TRANSACTION_PAGE_SIZE,
    offset: 0
  })

  const transactions = [...firstPage.transactions]
  const targetCount = Math.min(firstPage.total_count, MAX_FETCHED_TRANSACTIONS)

  while (transactions.length < targetCount) {
    const page = await fetchTransactionsByResult(resultId, {
      ...options,
      limit: TRANSACTION_PAGE_SIZE,
      offset: transactions.length
    })
    if (page.transactions.length === 0) {
      // The dataset shrank between requests; stop with what we have
      break
    }
    transactions.push(...page.transactions)
  }

  return {
    transactions,
    total_count: firstPage.total_count,
    limit: transactions.length,
    offset: 0
  }
}

/**
 * Update correctable attributes (category, partner, notice) of a transaction
 * @param id - Transaction identifier
 * @param payload - Fields to correct
 * @returns Promise with the updated transaction
 */
export async function updateTransaction(
  id: number,
  payload: TransactionUpdatePayload
): Promise<TransactionListItem> {
  return request<TransactionListItem>(getApiUrl(`/transactions/${id}`), {
    method: 'PUT',
    body: JSON.stringify(payload),
  })
}

/**
 * Undo all corrections of a transaction, restoring the original
 * category, merchant, and notice values
 * @param id - Transaction identifier
 * @returns Promise with the restored transaction
 */
export async function undoTransaction(
  id: number
): Promise<TransactionListItem> {
  return request<TransactionListItem>(getApiUrl(`/transactions/${id}/undo`), {
    method: 'POST',
  })
}

/**
 * Fetch aggregated transaction data for drilldown views
 * @param params - Aggregation parameters
 * @returns Promise with AggregatedTransactionsResponse
 */
export async function fetchAggregatedTransactions(params: {
  result_id?: string
  account?: string
  category_id?: string
  month?: string
  group_by: string
  algorithms?: string[]
  direction?: 'columns' | 'rows'
}): Promise<AggregatedTransactionsResponse> {
  const searchParams = new URLSearchParams()
  if (params.result_id) searchParams.append('result_id', params.result_id)
  if (params.account) searchParams.append('account', params.account)
  if (params.category_id) searchParams.append('category_id', params.category_id)
  if (params.month) searchParams.append('month', params.month)
  searchParams.append('group_by', params.group_by)
  if (params.algorithms) searchParams.append('algorithms', params.algorithms.join(','))
  if (params.direction) searchParams.append('direction', params.direction)

  return request<AggregatedTransactionsResponse>(
    getApiUrl(`/transactions/aggregate?${searchParams.toString()}`))
}

/**
 * Fetch month categories data (drilldown)
 * @param params - Route parameters containing resultId, accountId, monthId
 * @param options - Statistical analysis options (algorithms, direction)
 * @returns Promise with aggregated transactions data
 */
export async function fetchMonthCategories(
  params: Record<string, string | null>,
  options: StatisticalAnalysisOptions = {}
): Promise<AggregatedTransactionsResponse> {
  return fetchAggregatedTransactions({
    result_id: params.resultId ?? undefined,
    account: params.accountId ?? undefined,
    month: params.monthId ?? undefined,
    group_by: 'category',
    ...options
  })
}

/**
 * Fetch category month transactions data (drilldown)
 * @param params - Route parameters containing resultId, accountId, categoryId, monthId
 * @returns Promise with transaction list data
 */
export async function fetchCategoryMonthTransactions(
  params: Record<string, string | null>
): Promise<TransactionListResponse> {
  return fetchAllTransactions(params.resultId ?? undefined, {
    account: params.accountId ?? undefined,
    categoryId: params.categoryId ?? undefined,
    month: params.monthId ?? undefined
  })
}
