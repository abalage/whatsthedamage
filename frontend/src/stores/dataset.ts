/**
 * Dataset store: shared, cached fetch of the user's complete transaction
 * dataset and the processing result metadata, keyed by resultId.
 *
 * The Categories, Transactions, and Pivot pages all consume the same
 * dataset; this cache makes navigating between them render-only instead
 * of refetching (potentially tens of thousands of rows) each time.
 *
 * Invalidation:
 * - Corrections that apply to future transactions re-categorize other
 *   rows server-side, so the whole cache is dropped (useTransactionCorrections).
 * - Single-row corrections/undo are patched in place across all cached
 *   entries (replaceTransaction).
 * - New imports, logout, and session expiry drop the cache entirely.
 *
 * The transaction arrays inside the entries are reactive: pages may bind
 * them directly and in-place row updates (splice) propagate everywhere.
 * @module stores/dataset
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'
import { fetchAllTransactions, fetchProcessingResultMetadata } from '../js/api'
import type { ProcessingResultMetadata, TransactionListItem } from '../types/api'

/**
 * Cached dataset for one resultId (or the user's full history)
 */
export interface DatasetEntry {
  /** Complete transaction list of the scope */
  transactions: TransactionListItem[]
  /** Total transaction count reported by the API */
  total_count: number
  /** Processing result metadata, or null when unscoped */
  metadata: ProcessingResultMetadata | null
}

/**
 * Cache key for the unfiltered (all results) dataset
 */
const ALL_KEY = '__all__'

export const useDatasetStore = defineStore('dataset', () => {
  // Cache keyed by resultId ('__all__' when unfiltered)
  const entries = ref(new Map<string, DatasetEntry>())

  // In-flight loads so concurrent callers share a single request
  const inflight = new Map<string, Promise<DatasetEntry>>()

  const keyOf = (resultId?: string): string => resultId ?? ALL_KEY

  /**
   * Fetch and cache the dataset of one result scope.
   *
   * Returns the cached entry when present; concurrent calls with the
   * same scope share one request. Rows and metadata are fetched in
   * parallel.
   *
   * @param resultId - Result ID, or undefined for the user's full history
   * @returns Promise with the cached dataset entry
   */
  async function load(resultId?: string): Promise<DatasetEntry> {
    const key = keyOf(resultId)
    const cached = entries.value.get(key)
    if (cached) {
      return cached
    }
    const pending = inflight.get(key)
    if (pending) {
      return pending
    }

    const promise = (async (): Promise<DatasetEntry> => {
      const [response, metadata] = await Promise.all([
        fetchAllTransactions(resultId),
        fetchProcessingResultMetadata(resultId)
      ])
      const entry: DatasetEntry = {
        transactions: response.transactions,
        total_count: response.total_count,
        metadata
      }
      entries.value.set(key, entry)
      return entry
    })()

    inflight.set(key, promise)
    try {
      return await promise
    } finally {
      inflight.delete(key)
    }
  }

  /**
   * Replace a transaction in every cached dataset, keeping entries in
   * sync after a single-row correction or undo without a refetch
   * @param transaction - The updated transaction from the API
   */
  function replaceTransaction(transaction: TransactionListItem): void {
    for (const entry of entries.value.values()) {
      const index = entry.transactions.findIndex(t => t.id === transaction.id)
      if (index !== -1) {
        entry.transactions.splice(index, 1, transaction)
      }
    }
  }

  /**
   * Drop the cached dataset of one result scope
   * @param resultId - Result ID, or undefined for the full history
   */
  function invalidate(resultId?: string): void {
    entries.value.delete(keyOf(resultId))
  }

  /**
   * Drop all cached datasets
   */
  function invalidateAll(): void {
    entries.value.clear()
  }

  return {
    entries,
    load,
    replaceTransaction,
    invalidate,
    invalidateAll
  }
})
