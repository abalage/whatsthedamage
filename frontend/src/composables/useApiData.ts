/**
 * Composable for API data fetching with loading and error states
 * @module composables/useApiData
 */

import { ref, type Ref } from 'vue'

/**
 * Options for API data fetching
 */
export interface ApiDataOptions<T> {
  /**
   * Function to fetch data
   */
  fetchFn: () => Promise<T>
  /**
   * Optional side effect on failure (e.g. logging); the error
   * message is already stored in the returned error ref
   */
  onError?: (err: unknown) => void
}

/**
 * Result of useApiData composable
 */
export interface ApiDataResult<T> {
  data: Ref<T | undefined>
  isLoading: Ref<boolean>
  error: Ref<string | undefined>
  fetchData: () => Promise<void>
}

/**
 * Handles API data fetching with loading and error states.
 *
 * Fetching only: the caller renders errors (e.g. via ErrorState);
 * errors are stored, not rethrown, so failed refetches leave the
 * previous data in place without crashing the page.
 *
 * @param options - Configuration options
 * @returns Object with data, loading state, error, and fetch function
 */
export function useApiData<T>(options: ApiDataOptions<T>): ApiDataResult<T> {
  const data = ref<T | undefined>(undefined) as Ref<T | undefined>
  const isLoading = ref(false)
  const error = ref<string | undefined>(undefined)

  const fetchData = async (): Promise<void> => {
    isLoading.value = true
    error.value = undefined

    try {
      data.value = await options.fetchFn()
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err)
      error.value = message
      options.onError?.(err)
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
