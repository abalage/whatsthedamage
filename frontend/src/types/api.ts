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

/**
 * Response from transaction processing endpoint
 * This can be either the old format (result_id at root) or new format (result_id in metadata)
 */
export interface ProcessResponse {
  result_id?: string
  metadata?: {
    result_id: string
    processing_time?: number
    file_name?: string
    file_size?: number
    start_date?: string
    end_date?: string
    category_filter?: string
    ml_enabled?: boolean
  }
  status?: string
  message?: string
  accounts?: AccountData[]
  highlights?: StatisticalHighlights
}

// Drilldown response types
export interface DrilldownUrlInfo {
  category_url: string
  category_id: string
}

export interface DrilldownUrls {
  account_id: string | null
  category_urls: Record<string, DrilldownUrlInfo>
  month_urls: Record<string, { month_url: string; month_id: string }>
  cell_urls: Record<string, { cell_url: string; category_id: string; month_id: string }>
}

export interface MonthData {
  month: string
  month_timestamp: number
  total: {
    display: string
    raw: number
  }
  row_id: string
  cell_url: string
}

export interface CategoryMonthsResponse {
  result_id: string
  account_id: string
  account_name: string
  category_id: string
  category_name: string
  data: MonthData[]
  drilldown_urls?: Record<string, DrilldownUrls>
  highlights?: Record<string, string[]>
}

export interface CategoryData {
  category: string
  total: {
    display: string
    raw: number
  }
  row_id: string
  category_url: string
}

export interface MonthCategoriesResponse {
  result_id: string
  account_id: string
  account_name: string
  month_id: string
  month_name: string
  data: CategoryData[]
  drilldown_urls?: Record<string, DrilldownUrls>
  highlights?: Record<string, string[]>
}

export interface TransactionDataDetail {
  date: {
    display: string
  }
  amount: {
    display: string
  }
  merchant: string
  row_id: string
}

export interface CategoryMonthTransactionsResponse {
  result_id: string
  account_id: string
  account_name: string
  category_id: string
  category_name: string
  month_id: string
  month_name: string
  data: TransactionDataDetail[]
  highlights?: Record<string, string[]>
}

export interface ResultsResponseV2 {
  result_id: string
  accounts_data: {
    accounts: Array<{
      id: string
      name: string
      dt_response: {
        data: Array<{
          category: string
          date: {
            display: string
            timestamp: number
          }
          total: {
            display: string
            raw: number
          }
          details: Array<{
            date: { display: string }
            amount: { display: string }
            merchant: string
          }>
          row_id: string
        }>
      }
    }>
    highlights: Record<string, string[]>
  }
  drilldown_urls_by_account: Record<string, DrilldownUrls>
}

export interface AccountResultsResponse {
  result_id: string
  accounts_data: {
    accounts: Array<{
      id: string
      name: string
      dt_response: {
        data: Array<{
          category: string
          date: {
            display: string
            timestamp: number
          }
          total: {
            display: string
            raw: number
          }
          details: Array<{
            date: { display: string }
            amount: { display: string }
            merchant: string
            currency: string
            type: string
            confidence: number | null
            row_id: string
          }>
          row_id: string
        }>
      }
    }>
    highlights: Record<string, string[]>
  }
}