/**
 * Composable for transaction corrections (category, merchant, notice)
 * shared by the transaction table pages
 * @module composables/useTransactionCorrections
 */

import { computed, type ComputedRef } from 'vue'
import { useGettext } from 'vue3-gettext'
import { useFeedbackStore } from '../stores/feedback.js'
import { updateTransaction, undoTransaction } from '../js/api.js'
import type {
  TransactionListItem,
  TransactionUpdatePayload
} from '../types/api.js'

/** Maximum length of the partner (merchant) field, matches the backend */
export const PARTNER_MAX_LENGTH = 255

/** Maximum length of the notice field, matches the backend */
export const NOTICE_MAX_LENGTH = 500

/** Category id marker used by the frontend for uncategorized transactions */
export const UNCATEGORIZED = 'uncategorized'

// Correctable column keys whose cells are highlighted when corrected
const CORRECTED_COLUMNS = ['category_id', 'merchant', 'notice'] as const

// A field is corrected when its applied value differs from its original;
// rows created by the current API always carry the original values
export function isCategoryCorrected(txn: TransactionListItem): boolean {
  return txn.category_id !== txn.original_category_id
}

export function isMerchantCorrected(txn: TransactionListItem): boolean {
  return txn.partner !== null && txn.partner !== txn.original_partner
}

export function isNoticeCorrected(txn: TransactionListItem): boolean {
  return txn.notice !== txn.original_notice
}

export function isCorrected(txn: TransactionListItem): boolean {
  return (
    isCategoryCorrected(txn) ||
    isMerchantCorrected(txn) ||
    isNoticeCorrected(txn)
  )
}

/**
 * Applied merchant value shown in the table, falling back to the
 * original partner when no correction exists
 */
export function merchantOf(txn: TransactionListItem): string {
  return txn.partner ?? txn.original_partner ?? ''
}

/**
 * Per-cell row ids used by the cell highlight lookup of the data table
 */
export function correctedRowIds(
  txn: TransactionListItem
): Record<string, string> {
  return {
    category_id: `${txn.id}|category_id`,
    merchant: `${txn.id}|merchant`,
    notice: `${txn.id}|notice`
  }
}

/**
 * Result of the useTransactionCorrections composable
 */
export interface TransactionCorrections {
  /** Persists a correction and refreshes the local row */
  saveCorrection: (
    transactionId: number,
    payload: TransactionUpdatePayload
  ) => Promise<void>
  /** Undoes all corrections of a transaction and refreshes the local row */
  undoCorrection: (transactionId: number) => Promise<void>
  /** Cell highlight map keyed by row id for the data table */
  correctedCellHighlights: ComputedRef<Record<string, string[]>>
}

/**
 * Creates correction persistence and corrected-state helpers for a
 * transaction table.
 *
 * The caller passes a getter to the mutable transaction list so saved
 * and undone transactions replace their row in place. Errors from the
 * API are rethrown so the editing cell can display them inline;
 * successful operations are confirmed through the feedback store.
 *
 * @param transactions - Getter returning the current transaction list
 * @returns Correction persistence functions and the highlight map
 */
export function useTransactionCorrections(
  transactions: () => TransactionListItem[]
): TransactionCorrections {
  const { $gettext } = useGettext()
  const feedbackStore = useFeedbackStore()

  // Replace the row of the same id so the table refreshes in place
  const replaceTransaction = (transaction: TransactionListItem): void => {
    const list = transactions()
    const index = list.findIndex(t => t.id === transaction.id)
    if (index !== -1) {
      list.splice(index, 1, transaction)
    }
  }

  // Persist a correction, refresh the local row, and confirm the outcome.
  // Errors are rethrown so the editing cell can display them inline.
  const saveCorrection = async (
    transactionId: number,
    payload: TransactionUpdatePayload
  ): Promise<void> => {
    const transaction = await updateTransaction(transactionId, payload)
    replaceTransaction(transaction)
    feedbackStore.showSuccess($gettext('Transaction updated'))
  }

  // Undo all corrections of a transaction and refresh the local row.
  // Errors are rethrown so the undo cell can display them inline.
  const undoCorrection = async (
    transactionId: number
  ): Promise<void> => {
    const transaction = await undoTransaction(transactionId)
    replaceTransaction(transaction)
    feedbackStore.showSuccess($gettext('Corrections undone'))
  }

  // Cell highlight map for the data table: corrected cells resolve to
  // the 'corrected' semantic type via the highlight config
  const correctedCellHighlights = computed<Record<string, string[]>>(() => {
    const highlights: Record<string, string[]> = {}
    for (const txn of transactions()) {
      for (const column of CORRECTED_COLUMNS) {
        const corrected = column === 'category_id'
          ? isCategoryCorrected(txn)
          : column === 'merchant'
            ? isMerchantCorrected(txn)
            : isNoticeCorrected(txn)
        if (corrected) {
          highlights[`${txn.id}|${column}`] = ['corrected']
        }
      }
    }
    return highlights
  })

  return { saveCorrection, undoCorrection, correctedCellHighlights }
}
