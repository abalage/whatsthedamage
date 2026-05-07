import { ref } from 'vue'

export const useStatisticalStore = (): StatisticalStore => {
  const algorithms = ref<string[]>(['iqr', 'pareto'])
  const direction = ref<'rows' | 'columns'>('columns')
  const highlights = ref<Record<string, string[]>>({})

  const setAlgorithms = (newAlgorithms: string[]): void => {
    algorithms.value = newAlgorithms
    localStorage.setItem('statisticalAlgorithms', JSON.stringify(newAlgorithms))
  }

  const setDirection = (newDirection: 'rows' | 'columns'): void => {
    direction.value = newDirection
    localStorage.setItem('statisticalDirection', newDirection)
  }

  const setHighlights = (newHighlights: Record<string, string[]>): void => {
    highlights.value = newHighlights
  }

  const resetToDefaults = (): void => {
    algorithms.value = ['iqr', 'pareto']
    direction.value = 'columns'
    highlights.value = {}
    localStorage.removeItem('statisticalAlgorithms')
    localStorage.removeItem('statisticalDirection')
  }

  const loadFromStorage = (): void => {
    const savedAlgorithms = localStorage.getItem('statisticalAlgorithms')
    if (savedAlgorithms) {
      try {
        algorithms.value = JSON.parse(savedAlgorithms)
      } catch (_e: unknown) { // eslint-disable-line @typescript-eslint/no-unused-vars
        // Error parsing saved algorithms - will use defaults
      }
    }

    const savedDirection = localStorage.getItem('statisticalDirection')
    if (savedDirection === 'rows' || savedDirection === 'columns') {
      direction.value = savedDirection
    }
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
}

export type StatisticalStore = ReturnType<typeof useStatisticalStore>