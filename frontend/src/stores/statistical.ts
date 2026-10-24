import { defineStore } from 'pinia'
import { ref } from 'vue'
import { clearPersisted, usePersistentRef } from '../composables/usePersistentRef'

const ALGORITHMS_KEY = 'statisticalAlgorithms'
const DIRECTION_KEY = 'statisticalDirection'

const DEFAULT_ALGORITHMS = ['iqr', 'pareto']
const DEFAULT_DIRECTION = 'columns'

export const useStatisticalStore = defineStore('statistical', () => {
  const algorithms = usePersistentRef<string[]>(
    ALGORITHMS_KEY,
    [...DEFAULT_ALGORITHMS],
    (value): value is string[] => Array.isArray(value) && value.every(v => typeof v === 'string')
  )
  const direction = usePersistentRef<'rows' | 'columns'>(
    DIRECTION_KEY,
    DEFAULT_DIRECTION,
    (value): value is 'rows' | 'columns' => value === 'rows' || value === 'columns'
  )
  const highlights = ref<Record<string, string[]> | {}>({})

  const setAlgorithms = (newAlgorithms: string[]): void => {
    algorithms.value = newAlgorithms
  }

  const setDirection = (newDirection: 'rows' | 'columns'): void => {
    direction.value = newDirection
  }

  const setHighlights = (newHighlights: Record<string, string[]> | {}): void => {
    highlights.value = newHighlights
  }

  const resetToDefaults = (): void => {
    algorithms.value = [...DEFAULT_ALGORITHMS]
    direction.value = DEFAULT_DIRECTION
    highlights.value = {}
    clearPersisted(ALGORITHMS_KEY)
    clearPersisted(DIRECTION_KEY)
  }

  // Kept for compatibility with pages that call it on mount; the
  // persisted refs already initialize from storage
  const loadFromStorage = (): void => {
    // Values were loaded during store initialization
  }

  return {
    algorithms,
    direction,
    highlights,
    setAlgorithms,
    setDirection,
    setHighlights,
    resetToDefaults,
    loadFromStorage
  }
})
