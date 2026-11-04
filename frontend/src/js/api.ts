/**
 * API utility functions for What's the Damage frontend.
 *
 * Barrel module: the implementation lives in js/api/ (transport, auth,
 * transactions, processing); this file preserves the single import path
 * (`../js/api`) used across the app and tests.
 * @module utils/api
 */

export {
  register,
  confirmRegistration,
  login,
  logout,
  getMe,
  updateSharingPreference,
  fetchCsrfToken,
  resetPassword,
  deleteAccount,
  updateUsername,
  changePassword,
  exportMyData,
  regenerateRecoveryCode
} from './api/auth'
export {
  fetchTransactionsByResult,
  fetchAllTransactions,
  updateTransaction,
  undoTransaction,
  fetchAggregatedTransactions,
  fetchMonthCategories,
  fetchCategoryMonthTransactions
} from './api/transactions'
export {
  createTransaction,
  recalculateStatistics,
  fetchCategories,
  fetchCostOfLivingCategories,
  fetchAllCsvProfiles,
  fetchProcessingResults,
  fetchProcessingResultMetadata
} from './api/processing'
