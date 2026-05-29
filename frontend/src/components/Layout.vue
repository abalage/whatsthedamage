<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useLocaleStore } from '../stores/locale'
import { useStatisticalStore } from '../stores/statistical'
import { useFeedbackStore } from '../stores/feedback'
import { useGettext } from 'vue3-gettext'
import { recalculateStatistics } from '../js/api'
import { RouterLink } from 'vue-router'

const { $gettext } = useGettext()
const route = useRoute()
const localeStore = useLocaleStore()
const statisticalStore = useStatisticalStore()
const feedback = useFeedbackStore()

const isRecalculating = ref(false)

// Get current resultId from route
const resultId = computed(() => {
  const id = route.query.resultId ?? route.query.result_id
  return typeof id === 'string' ? id : null
})

// Show Analytics dropdown only when there's a resultId
const showAnalytics = computed(() => resultId.value !== null)

// Sync with store
const algorithms = computed({
  get: () => statisticalStore.algorithms,
  set: (value: string[]) => statisticalStore.setAlgorithms(value)
})

const direction = computed({
  get: () => statisticalStore.direction,
  set: (value: 'rows' | 'columns') => statisticalStore.setDirection(value)
})

const handleDirectionChange = (event: Event) => {
  const target = event.target as HTMLSelectElement
  direction.value = target.value as 'rows' | 'columns'
  if (resultId.value) {
    triggerRecalculate()
  }
}

const handleAlgorithmChange = (event: Event) => {
  const target = event.target as HTMLSelectElement
  const selected = Array.from(target.selectedOptions).map(opt => opt.value)
  algorithms.value = selected
  if (resultId.value) {
    triggerRecalculate()
  }
}

const triggerRecalculate = async () => {
  if (!resultId.value) return
  
  try {
    isRecalculating.value = true
    const response = await recalculateStatistics(
      resultId.value,
      algorithms.value,
      direction.value
    )
    
    // Update window highlights
    if (response?.highlights) {
      window.highlights = response.highlights
      if (typeof window.updateCellHighlights === 'function') {
        window.updateCellHighlights(response.highlights)
      }
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error)
    feedback.showError(`${$gettext('Recalculate error')}: ${message}`)
  } finally {
    isRecalculating.value = false
  }
}

const resetToDefaults = async () => {
  statisticalStore.resetToDefaults()
  if (resultId.value) {
    try {
      isRecalculating.value = true
      const response = await recalculateStatistics(
        resultId.value,
        ['iqr', 'pareto'],
        'columns'
      )
      
      if (response?.highlights) {
        window.highlights = response.highlights
        if (typeof window.updateCellHighlights === 'function') {
          window.updateCellHighlights(response.highlights)
        }
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error)
      feedback.showError(`${$gettext('Restore defaults error')}: ${message}`)
    } finally {
      isRecalculating.value = false
    }
  }
}

const setLocale = (locale: string) => {
  localeStore.setLocale(locale)
}
</script>

<template>
  <div>
    <header>
      <nav class="navbar navbar-expand-lg navbar-dark bg-success mb-3">
        <div class="container-fluid">
          <RouterLink to="/" class="navbar-brand">What's the Damage?</RouterLink>
          <span class="text-white align-middle">{{ $gettext('Generate reports from your bank account CSV history') }}</span>
          <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
            <span class="navbar-toggler-icon"></span>
          </button>
          <div id="navbarNav" class="collapse navbar-collapse">
            <ul class="navbar-nav ms-auto">
              <li class="nav-item">
                <RouterLink to="/" class="nav-link">{{ $gettext('Home') }}</RouterLink>
              </li>
              <li class="nav-item">
                <RouterLink to="/privacy" class="nav-link">{{ $gettext('Privacy') }}</RouterLink>
              </li>
              <li class="nav-item">
                <RouterLink to="/legal" class="nav-link">{{ $gettext('Legal') }}</RouterLink>
              </li>
              <li class="nav-item">
                <RouterLink to="/about" class="nav-link">{{ $gettext('About') }}</RouterLink>
              </li>
              <li v-if="showAnalytics" class="nav-item dropdown">
                <a id="analyticsDropdown" class="nav-link dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown" aria-expanded="false">
                  {{ $gettext('Analytics') }}
                </a>
                <ul class="dropdown-menu dropdown-menu-end" aria-labelledby="analyticsDropdown">
                  <li>
                    <div class="dropdown-item-text">{{ $gettext('Analysis direction') }}</div>
                  </li>
                  <li>
                    <select 
                      v-model="direction" 
                      class="form-select form-select-sm mx-2 mb-1"
                      :disabled="isRecalculating"
                      @change="handleDirectionChange"
                    >
                      <option value="columns">{{ $gettext('columns') }}</option>
                      <option value="rows">{{ $gettext('rows') }}</option>
                    </select>
                  </li>
                  <li>
                    <div class="dropdown-item-text">{{ $gettext('Algorithms') }}</div>
                  </li>
                  <li>
                    <select 
                      v-model="algorithms" 
                      class="form-select form-select-sm mx-2 mb-1"
                      multiple
                      size="2"
                      :disabled="isRecalculating"
                      @change="handleAlgorithmChange"
                    >
                      <option value="iqr">{{ $gettext('IQR Outlier Detection') }}</option>
                      <option value="pareto">{{ $gettext('Pareto analysis') }}</option>
                    </select>
                  </li>
                  <li>
                    <div class="dropdown-item-text">{{ $gettext('Legend') }}</div>
                  </li>
                  <li>
                    <div class="dropdown-item">
                      <div class="d-flex flex-wrap gap-2 justify-content-center">
                        <span class="badge highlight-outlier">{{ $gettext('Marked outlier by IQR') }}</span>
                        <span class="badge highlight-pareto">{{ $gettext('Marked outlier by Pareto principle') }}</span>
                        <span class="badge highlight-excluded">{{ $gettext('Excluded from statistics') }}</span>
                        <span class="badge highlight-multiple">{{ $gettext('Matched by multiple algorithms') }}</span>
                      </div>
                    </div>
                  </li>
                  <li><hr class="dropdown-divider"></li>
                  <li>
                    <a 
                      class="dropdown-item" 
                      href="#" 
                      :class="{ disabled: isRecalculating }"
                      @click.prevent="resetToDefaults"
                    >
                      {{ $gettext('Reset to defaults') }}
                    </a>
                  </li>
                </ul>
              </li>
              <li class="nav-item dropdown">
                <a id="langDropdown" class="nav-link dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown" aria-expanded="false">
                  {{ $gettext('Languages') }}
                </a>
                <ul class="dropdown-menu dropdown-menu-end" aria-labelledby="langDropdown">
                  <li>
                    <a class="dropdown-item" href="#" @click.prevent="setLocale('en')">🇬🇧 English</a>
                  </li>
                  <li>
                    <a class="dropdown-item" href="#" @click.prevent="setLocale('hu')">🇭🇺 Magyar</a>
                  </li>
                </ul>
              </li>
            </ul>
          </div>
        </div>
      </nav>
    </header>

    <main id="main-content" class="container-fluid" tabindex="-1">
      <a class="sr-only sr-only-focusable" href="#main-content">{{ $gettext('Skip to main content') }}</a>
      <slot></slot>
    </main>

    <footer class="bg-success text-white text-center py-3 mt-3">
      <div class="container">
        <a href="https://balagetech.com" class="text-white me-3">@ 2025 Balagetech</a>
        <span class="text-white me-3">v1.0.0</span>
      </div>
    </footer>
  </div>
</template>

<style scoped>
header, footer {
  padding: 15px 0;
}

.navbar {
  padding: 0;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.sr-only-focusable:focus {
  position: static;
  width: auto;
  height: auto;
  padding: 0.5rem;
  margin: 0;
  overflow: visible;
  clip: auto;
  white-space: normal;
}
</style>