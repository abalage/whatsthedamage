/**
 * Composable for refs persisted to localStorage.
 *
 * Wraps a ref whose value survives page reloads: writes serialize to
 * JSON under the given key, and initialization reads and validates the
 * stored value, falling back to the default when it is missing or
 * malformed.
 * @module composables/usePersistentRef
 */

import { computed, ref, type Ref } from 'vue'

/**
 * Read and parse a persisted value from localStorage
 *
 * Accepts both JSON-serialized values and the legacy raw-string format
 * used by earlier versions of the stores.
 *
 * @param key - Storage key
 * @param validate - Type guard accepting the parsed value when valid
 * @returns The stored value, or undefined when missing or invalid
 */
function readPersisted<T>(key: string, validate: (value: unknown) => value is T): T | undefined {
  const saved = localStorage.getItem(key)
  if (saved === null) return undefined
  try {
    const parsed: unknown = JSON.parse(saved)
    if (validate(parsed)) {
      return parsed
    }
  } catch {
    // Legacy raw-string format (pre-JSON persistence)
    if (validate(saved)) {
      return saved as T
    }
  }
  return undefined
}

/**
 * Create a ref persisted to localStorage.
 *
 * The ref initializes from the stored value when it passes `validate`;
 * otherwise the default is used. Every subsequent set serializes to
 * storage.
 *
 * @param key - localStorage key
 * @param defaultValue - Value used when nothing valid is stored
 * @param validate - Runtime check for the parsed stored value
 * @returns The persisted ref
 */
export function usePersistentRef<T>(
  key: string,
  defaultValue: T,
  validate: (value: unknown) => value is T
): Ref<T> {
  const stored = readPersisted<T>(key, validate)
  const state = ref<T>(stored ?? defaultValue) as Ref<T>

  // Writable computed: same ref interface, persists on set
  return computed<T>({
    get: () => state.value,
    set: (value: T) => {
      state.value = value
      localStorage.setItem(key, JSON.stringify(value))
    }
  }) as Ref<T>
}

/**
 * Remove the persisted value for a key (used by reset actions)
 * @param key - Storage key
 */
export function clearPersisted(key: string): void {
  localStorage.removeItem(key)
}
