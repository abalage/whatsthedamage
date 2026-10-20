/**
 * Composable wrapping an async action with loading and error state.
 *
 * Each call clears the previous error, sets the loading flag during
 * the action, and stores the error message (re-throwing it) on
 * failure. Pages use it to reduce their handlers to the success path.
 * @module composables/useAsyncAction
 */

import { ref, type Ref } from 'vue'

/**
 * Creates a wrapped async action with loading and error state.
 *
 * @returns Object with isLoading, error refs and the run function
 */
export function useAsyncAction(): {
  /** Whether the wrapped action is running */
  isLoading: Ref<boolean>
  /** Error message of the last failed run, or null */
  error: Ref<string | null>
  /** Runs the action with loading/error handling */
  run: <T>(action: () => Promise<T>) => Promise<T | undefined>
} {
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  const run = async <T>(action: () => Promise<T>): Promise<T | undefined> => {
    isLoading.value = true
    error.value = null
    try {
      return await action()
    } catch (err: unknown) {
      error.value = err instanceof Error ? err.message : String(err)
      return undefined
    } finally {
      isLoading.value = false
    }
  }

  return { isLoading, error, run }
}
