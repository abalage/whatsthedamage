import { ref } from 'vue'

export const useStatisticalStore = () => {
  const algorithms = ref<string[]>(['iqr', 'pareto'])
  const direction = ref<'rows' | 'columns'>('columns')
  const highlights = ref<Record<string, any>>({})

  const setAlgorithms = (newAlgorithms: string[]) => {
    algorithms.value = newAlgorithms
    localStorage.setItem('statisticalAlgorithms', JSON.stringify(newAlgorithms))
  }

  const setDirection = (newDirection: 'rows' | 'columns') => {
    direction.value = newDirection
    localStorage.setItem('statisticalDirection', newDirection)
  }

  const setHighlights = (newHighlights: Record<string, any>) => {
    highlights.value = newHighlights
  }

  const resetToDefaults = () => {
    algorithms.value = ['iqr', 'pareto']
    direction.value = 'columns'
    highlights.value = {}
    localStorage.removeItem('statisticalAlgorithms')
    localStorage.removeItem('statisticalDirection')
  }

  const loadFromStorage = () => {
    const savedAlgorithms = localStorage.getItem('statisticalAlgorithms')
    if (savedAlgorithms) {
      try {
        algorithms.value = JSON.parse(savedAlgorithms)
      } catch (e) {
        console.error('Error parsing saved algorithms:', e)
      }
    }

    const savedDirection = localStorage.getItem('statisticalDirection')
    if (savedDirection && (savedDirection === 'rows' || savedDirection === 'columns')) {
      direction.value = savedDirection as 'rows' | 'columns'
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