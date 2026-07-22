<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import { useLocaleStore } from '../stores/locale.js'
import { useStatisticalStore } from '../stores/statistical.js'
import { useFeedbackStore } from '../stores/feedback.js'
import { useThemeStore } from '../stores/theme.js'
import { useGettext } from 'vue3-gettext'
import { recalculateStatistics } from '../js/api.js'

const { $gettext } = useGettext()
const route = useRoute()
const localeStore = useLocaleStore()
const statisticalStore = useStatisticalStore()
const feedback = useFeedbackStore()
const themeStore = useThemeStore()

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

    // Store highlights in Pinia
    if (response?.highlights) {
      statisticalStore.setHighlights(response.highlights)
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
        statisticalStore.setHighlights(response.highlights)
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
      <nav class="navbar navbar-expand-lg navbar-dark mb-3">
        <div class="container-fluid">
          <RouterLink to="/" class="navbar-brand text-on-primary">What's the Damage?</RouterLink>
          <span class="align-middle text-on-primary">{{ $gettext('Tell me I didn\'t spend that much…') }}</span>
          <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
            <span class="navbar-toggler-icon"></span>
          </button>
          <div id="navbarNav" class="collapse navbar-collapse">
            <ul class="navbar-nav ms-auto">
              <li class="nav-item">
                <RouterLink to="/" class="nav-link">{{ $gettext('Home') }}</RouterLink>
              </li>
              <li class="nav-item dropdown">
                <button id="aboutDropdown" class="nav-link dropdown-toggle" type="button" data-bs-toggle="dropdown" aria-expanded="false" @keydown.enter.prevent="($event.currentTarget as HTMLButtonElement).click()" @keydown.space.prevent="($event.currentTarget as HTMLButtonElement).click()">
                  {{ $gettext('About') }}
                </button>
                <ul class="dropdown-menu dropdown-menu-end" aria-labelledby="aboutDropdown">
                  <li>
                    <RouterLink to="privacy" class="dropdown-item">{{ $gettext('Privacy') }}</RouterLink>
                  </li>
                  <li>
                     <RouterLink to="legal" class="dropdown-item">{{ $gettext('Legal') }}</RouterLink>
                  </li>
                  <li>
                     <RouterLink to="about" class="dropdown-item">{{ $gettext('About') }}</RouterLink>
                  </li>
                </ul>
              </li>
              <li v-if="showAnalytics" class="nav-item dropdown">
                <button id="analyticsDropdown" class="nav-link dropdown-toggle" type="button" data-bs-toggle="dropdown" aria-expanded="false" @keydown.enter.prevent="($event.currentTarget as HTMLButtonElement).click()" @keydown.space.prevent="($event.currentTarget as HTMLButtonElement).click()">
                  {{ $gettext('Analytics') }}
                </button>
                <ul class="dropdown-menu dropdown-menu-end" aria-labelledby="analyticsDropdown">
                  <li>
                    <label for="directionSelect" class="dropdown-item-text">{{ $gettext('Analysis direction') }}:</label>
                  </li>
                  <li>
                    <select
                      id="directionSelect"
                      v-model="direction"
                      class="form-select form-select-sm mx-4 mb-1 w-75"
                      :disabled="isRecalculating"
                      aria-label="Analysis direction"
                      @change="handleDirectionChange"
                    >
                      <option value="columns">{{ $gettext('columns') }}</option>
                      <option value="rows">{{ $gettext('rows') }}</option>
                    </select>
                  </li>
                  <li>
                    <label for="algorithmsSelect" class="dropdown-item-text">{{ $gettext('Algorithms') }}:</label>
                  </li>
                  <li>
                    <select
                      id="algorithmsSelect"
                      v-model="algorithms"
                      class="form-select form-select-sm mx-4 mb-1 w-75"
                      multiple
                      size="2"
                      :disabled="isRecalculating"
                      aria-label="Algorithms"
                      @change="handleAlgorithmChange"
                    >
                      <option value="iqr">{{ $gettext('IQR Outlier Detection') }}</option>
                      <option value="pareto">{{ $gettext('Pareto analysis') }}</option>
                    </select>
                  </li>
                  <li>
                    <div class="dropdown-item-text">{{ $gettext('Legend') }}:</div>
                  </li>
                  <li>
                    <div class="dropdown-item">
                      <div class="legend-display d-flex flex-wrap gap-2 justify-content-left">
                        <span class="badge highlight-outlier">{{ $gettext('Marked outlier by IQR') }}</span>
                        <span class="badge highlight-pareto">{{ $gettext('Marked outlier by Pareto principle') }}</span>
                        <span class="badge highlight-excluded">{{ $gettext('Excluded from statistics') }}</span>
                        <span class="badge highlight-multiple">{{ $gettext('Matched by multiple algorithms') }}</span>
                      </div>
                    </div>
                  </li>
                  <li><hr class="dropdown-divider"></li>
                  <li>
                    <button
                      class="dropdown-item"
                      type="button"
                      :class="{ disabled: isRecalculating }"
                      @click.prevent="resetToDefaults"
                      @keydown.enter.prevent="resetToDefaults"
                      @keydown.space.prevent="resetToDefaults"
                    >
                      {{ $gettext('Reset to defaults') }}
                    </button>
                  </li>
                </ul>
              </li>
              <li class="nav-item dropdown">
                <button id="langDropdown" class="nav-link dropdown-toggle" type="button" data-bs-toggle="dropdown" aria-expanded="false" @keydown.enter.prevent="($event.currentTarget as HTMLButtonElement).click()" @keydown.space.prevent="($event.currentTarget as HTMLButtonElement).click()">
                  {{ $gettext('Languages') }}
                </button>
                <ul class="dropdown-menu dropdown-menu-end" aria-labelledby="langDropdown">
                  <li>
                    <button class="dropdown-item" type="button" @click.prevent="setLocale('en')" @keydown.enter.prevent="setLocale('en')" @keydown.space.prevent="setLocale('en')">🇬🇧 English</button>
                  </li>
                  <li>
                    <button class="dropdown-item" type="button" @click.prevent="setLocale('hu')" @keydown.enter.prevent="setLocale('hu')" @keydown.space.prevent="setLocale('hu')">🇭🇺 Magyar</button>
                  </li>
                </ul>
              </li>
              <li class="nav-item dropdown">
                <button
                  id="themeDropdown"
                  class="nav-link dropdown-toggle"
                  type="button"
                  data-bs-toggle="dropdown"
                  aria-expanded="false"
                  @keydown.enter.prevent="($event.currentTarget as HTMLButtonElement).click()"
                  @keydown.space.prevent="($event.currentTarget as HTMLButtonElement).click()"
                >
                  {{ $gettext('Themes') }}
                </button>
                <ul class="dropdown-menu dropdown-menu-end" aria-labelledby="themeDropdown">
                  <li v-for="theme in themeStore.allThemes" :key="theme.id">
                    <button
                      :class="{ 'active': themeStore.currentThemeId === theme.id }"
                      class="dropdown-item"
                      type="button"
                      @click.prevent="themeStore.setTheme(theme.id)"
                      @keydown.enter.prevent="themeStore.setTheme(theme.id)"
                      @keydown.space.prevent="themeStore.setTheme(theme.id)"
                    >
                      <span class="theme-preview" :style="{ backgroundColor: theme.colors.surface.primary, color: theme.colors.text.onPrimary }">
                        &nbsp;&nbsp;&nbsp;
                      </span>
                      {{ theme.name }}
                    </button>
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

    <footer class="text-center py-3 mt-3">
      <div class="container-fluid">
        <a href="https://balagetech.com" class="text-on-primary me-3">@ 2026 Balagetech</a>
        <span class="me-3">v1.0.0</span>
      </div>
    </footer>
  </div>
</template>
