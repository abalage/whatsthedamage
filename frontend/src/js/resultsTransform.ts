/**
 * Transform helpers converting flat transaction lists into the
 * account-grouped ResultsApiResponse shape consumed by the pivot
 * store and the chart views.
 * @module utils/resultsTransform
 */

import type {
  Account,
  ResultsApiResponse,
  TransactionListItem
} from '../types/api'
import { createMonthDate, getMonthKey } from './dateUtils'

/**
 * Row shape produced by the aggregation: category-month cell with
 * its member transactions attached as details
 */
interface AggregatedRow {
  row_id: string
  category_id: string
  total: { display: string; raw: number }
  date: string
  details: Array<{
    row_id: string
    date: string
    amount: { display: string; raw: number }
    merchant: string
    currency: string
    account: string
    type: string | null
    confidence: number | null
    notice: string | null
    category_id: string | null
    month_id: string
  }>
  is_calculated: boolean
}

/**
 * Build the aggregated data rows of one account: transactions grouped
 * by category and month (YYYY-MM), with per-group totals.
 */
function aggregateAccountData(accountId: string, accountTransactions: TransactionListItem[]): AggregatedRow[] {
  // Group transactions by category_id and month (YYYY-MM)
  const categoryMonthMap = new Map<string, Map<string, TransactionListItem[]>>()
  for (const txn of accountTransactions) {
    const categoryId = txn.category_id ?? 'uncategorized'
    const monthKey = getMonthKey(txn.date)

    let monthMap = categoryMonthMap.get(categoryId)
    if (!monthMap) {
      monthMap = new Map()
      categoryMonthMap.set(categoryId, monthMap)
    }
    let monthTransactions = monthMap.get(monthKey)
    if (!monthTransactions) {
      monthTransactions = []
      monthMap.set(monthKey, monthTransactions)
    }
    monthTransactions.push(txn)
  }

  // Build aggregated rows
  const rows: AggregatedRow[] = []
  for (const [categoryId, monthMap] of categoryMonthMap) {
    for (const [monthKey, monthTransactions] of monthMap) {
      const totalAmount = monthTransactions.reduce((sum, txn) => sum + (txn.amount || 0), 0)
      const monthDate = createMonthDate(monthKey)

      if (!monthDate) {
        continue // Skip invalid dates
      }

      rows.push({
        row_id: `${accountId}-${categoryId}-${monthKey}`,
        category_id: categoryId,
        total: {
          display: totalAmount.toFixed(2),
          raw: totalAmount
        },
        date: monthKey, // ISO date string (YYYY-MM-DD)
        details: monthTransactions.map(txn => ({
          row_id: String(txn.id),
          date: txn.date || '', // ISO date string from API
          amount: {
            display: (txn.amount ?? 0).toFixed(2),
            raw: txn.amount ?? 0
          },
          merchant: txn.original_partner || (txn.partner ?? ''),
          currency: txn.currency || '',
          account: txn.account,
          type: txn.transaction_type || null,
          confidence: txn.confidence ?? null,
          notice: txn.notice ?? null,
          category_id: txn.category_id ?? null,
          month_id: monthKey
        })),
        is_calculated: false
      })
    }
  }

  return rows
}

/**
 * Transform a flat transaction list into the ResultsApiResponse format
 * used by the pivot store, grouping transactions by account, then by
 * category and month.
 *
 * @param transactions - Flat transaction list from the API
 * @returns ResultsApiResponse with one account entry per account id
 */
export function transformToResultsApiResponse(
  transactions: TransactionListItem[]
): ResultsApiResponse {
  // Group transactions by account
  const accountsMap = new Map<string, TransactionListItem[]>()
  for (const txn of transactions) {
    const accountId = txn.account
    let accountTransactions = accountsMap.get(accountId)
    if (!accountTransactions) {
      accountTransactions = []
      accountsMap.set(accountId, accountTransactions)
    }
    accountTransactions.push(txn)
  }

  // Build accounts array
  const accounts: Account[] = []
  for (const [accountId, accountTransactions] of accountsMap) {
    // Get account info from first transaction
    const firstTxn = accountTransactions[0]
    const account: Account = {
      id: accountId,
      name: accountId,
      formatted_id: accountId,
      currency: firstTxn.currency || '',
      data: [],
      metadata: null
    }

    account.data = aggregateAccountData(accountId, accountTransactions)
    accounts.push(account)
  }

  return {
    accounts,
    highlights: {}
  }
}
