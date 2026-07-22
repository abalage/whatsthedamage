/**
 * Composable for API data fetching with loading and error states
 * @module composables/useApiData
 */

import { ref, type Ref } from 'vue'
import { useFeedbackStore } from '../stores/feedback.js'

/**
 * Options for API data fetching
 */
export interface ApiDataOptions<T> {
  /**
   * Function to fetch data
   */
  fetchFn: () => Promise<T>
  /**
   * i18n translation function
   */
  t: (key: string) => string
  /**
   * i18n key for error messages
   */
  errorMessageKey?: string
}

/**
 * Result of useApiData composable
 */
export interface ApiDataResult<T> {
  data: Ref<T | null>
  isLoading: Ref<boolean>
  error: Ref<string | null>
  fetchData: () => Promise<void>
}

/**
 * Handles API data fetching with loading state, error handling, and feedback
 * @param options - Configuration options
 * @returns Object with data, loading state, error, and fetch function
 */
export function useApiData<T>(options: ApiDataOptions<T>): ApiDataResult<T> {
  const data = ref<T | null>(null) as Ref<T | null>
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const feedback = useFeedbackStore()

  const fetchData = async (): Promise<void> => {
    isLoading.value = true
    error.value = null

    try {
      data.value = await options.fetchFn()
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err)
      error.value = message
      const errorKey = options.errorMessageKey ?? 'loadError'
      feedback.showError(`${options.t(errorKey)}: ${message}`)
    } finally {
      isLoading.value = false
    }
  }

  return {
    data,
    isLoading,
    error,
    fetchData
  }
}
