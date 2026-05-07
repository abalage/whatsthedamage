export interface ApiError {
  error: string
  status: number
  details?: Record<string, unknown>
}

export interface ProcessingResponse {
  result_id: string
  status: string
  message?: string
  accounts?: AccountData[]
  metadata?: ProcessingMetadata
  highlights?: StatisticalHighlights
}

export interface AccountData {
  id: string
  formatted_id: string
  currency: string
  transactions: TransactionData[]
  summary: AccountSummary
}

export interface TransactionData {
  id: string
  date: string
  amount: number
  currency: string
  description: string
  merchant: string
  category: string
  category_confidence: number
  type: string
  account_id: string
}

export interface AccountSummary {
  total_transactions: number
  total_amount: number
  categories: CategorySummary[]
}

export interface CategorySummary {
  category: string
  count: number
  total_amount: number
  percentage: number
}

export interface ProcessingMetadata {
  processing_time: number
  file_name: string
  file_size: number
  start_date?: string
  end_date?: string
  category_filter?: string
  ml_enabled: boolean
}

export interface StatisticalHighlights {
  outliers: Record<string, string[]>
  pareto: Record<string, string[]>
  excluded: Record<string, string[]>
}

export interface ResultsResponse {
  result_id: string
  accounts: AccountData[]
  metadata: ProcessingMetadata
  highlights: StatisticalHighlights
  statistical_analysis: StatisticalAnalysis
}

export interface StatisticalAnalysis {
  algorithms: string[]
  direction: 'rows' | 'columns'
  outliers_detected: number
  pareto_items: number
}

export interface DetailResultsResponse {
  result_id: string
  transactions: TransactionData[]
  metadata: ProcessingMetadata
  highlights: StatisticalHighlights
}

export interface RecalculateResponse {
  result_id: string
  updated_highlights: StatisticalHighlights
  statistical_analysis: StatisticalAnalysis
}