/**
 * Composable wrapping an async action with loading and error state.
 *
 * Each call clears the previous error, sets the loading flag during
 * the action, and stores the error message while re-throwing it on
 * failure. The rethrow lets callers run their failure handling at
 * the call site; the stored message drives inline error display.
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
  /** Error message of the last failed run, or undefined */
  error: Ref<string | undefined>
  /** Runs the action with loading/error handling */
  run: <T>(action: () => Promise<T>) => Promise<T>
} {
  const isLoading = ref(false)
  const error = ref<string | undefined>(undefined)

  const run = async <T>(action: () => Promise<T>): Promise<T> => {
    isLoading.value = true
    error.value = undefined
    try {
      return await action()
    } catch (err: unknown) {
      error.value = err instanceof Error ? err.message : String(err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  return { isLoading, error, run }
}
