<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { useStatisticalStore } from '../../stores/statistical'
import { useFeedbackStore } from '../../stores/feedback'
import { useGettext } from 'vue3-gettext'
import { recalculateStatistics } from '../../js/api'
import ButtonComponent from './ButtonComponent.vue'

const { $gettext } = useGettext()

interface StatisticalControlsProps {
  resultId: string
}

const props = defineProps<StatisticalControlsProps>()

const statisticalStore = useStatisticalStore()
const feedback = useFeedbackStore()

// Legend visibility
const legendVisible = ref(false)
const statsControlsVisible = ref(false)

// Algorithm selections - use reactive for proper nested property reactivity
const algorithms = reactive({
  iqr: true,
  pareto: true
})

// Analysis direction
const direction = ref<'rows' | 'columns'>('columns')

// Loading state
const isRecalculating = ref(false)

const toggleLegend = () => {
  legendVisible.value = !legendVisible.value
}

const toggleStatsControls = () => {
  statsControlsVisible.value = !statsControlsVisible.value
}

const handleRecalculate = async () => {
  try {
    isRecalculating.value = true

    const selectedAlgorithms = []
    if (algorithms.iqr) selectedAlgorithms.push('iqr')
    if (algorithms.pareto) selectedAlgorithms.push('pareto')

    const response = await recalculateStatistics(
      props.resultId,
      selectedAlgorithms,
      direction.value
    )

    // Update window.highlights with new highlights from response
    if (response && response.highlights) {
      window.highlights = response.highlights
    }

    // Update store with new settings
    statisticalStore.setAlgorithms(selectedAlgorithms)
    statisticalStore.setDirection(direction.value)

    // Re-apply highlights to cells
    if (typeof window.updateCellHighlights === 'function') {
      window.updateCellHighlights(response.highlights || {})
    }

  } catch (error) {
    const message = error instanceof Error ? error.message : String(error)
    feedback.showError(`${$gettext('Recalculate error')}: ${message}`)
  } finally {
    isRecalculating.value = false
  }
}

const resetToDefaults = async () => {
  algorithms.iqr = true
  algorithms.pareto = true
  direction.value = 'columns'
  statisticalStore.resetToDefaults()

  // Trigger recalculation with defaults
  try {
    isRecalculating.value = true
    const response = await recalculateStatistics(
      props.resultId,
      ['iqr', 'pareto'],
      'columns'
    )

    // Update window.highlights with new highlights from response
    if (response && response.highlights) {
      window.highlights = response.highlights
    }

    // Re-apply highlights to cells
    if (typeof window.updateCellHighlights === 'function') {
      window.updateCellHighlights(response.highlights || {})
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error)
    feedback.showError(`${$gettext('Restore defaults error')}: ${message}`)
  } finally {
    isRecalculating.value = false
  }
}

const legendClasses = computed(() => {
  return legendVisible.value ? 'collapse show' : 'collapse'
})

const statsControlsClasses = computed(() => {
  return statsControlsVisible.value ? 'collapse show' : 'collapse'
})
</script>

<template>
  <div class="row row-cols-auto mb-3">
    <!-- Legend Section -->
    <div class="col">
      <button 
        class="btn btn-outline-info" 
        type="button" 
        data-bs-toggle="collapse" 
        data-bs-target="#legend" 
        aria-expanded="false" 
        aria-controls="legend"
        @click="toggleLegend"
      >
        {{ $gettext('Legend') }}
      </button>
      <div id="legend" :class="legendClasses">
        <div class="card card-body">
          <p><span class="badge highlight-outlier">{{ $gettext('Outlier') }}</span> {{ $gettext('Cells highlighted in red indicate outliers detected by IQR method.') }}</p>
          <p><span class="badge highlight-pareto">{{ $gettext('Pareto') }}</span> {{ $gettext('Cells highlighted in green indicate top contributors per Pareto principle.') }}</p>
          <p><span class="badge highlight-excluded">{{ $gettext('Excluded') }}</span> {{ $gettext('Cells highlighted in light grey are excluded from statistical analysis (calculated rows or excluded categories).') }}</p>
        </div>
      </div>
    </div>

    <!-- Statistical Controls Section -->
    <div class="col">
      <button 
        class="btn btn-outline-primary" 
        type="button" 
        data-bs-toggle="collapse" 
        data-bs-target="#stats-controls" 
        aria-expanded="false" 
        aria-controls="stats-controls"
        @click="toggleStatsControls"
      >
        {{ $gettext('Statistical Analysis Controls') }}
      </button>
      <div id="stats-controls" :class="statsControlsClasses">
        <div class="card card-body">
          <div class="mb-3">
            <h6>{{ $gettext('Algorithms') }}</h6>
            <div class="form-check">
              <input id="algorithm-iqr" v-model="algorithms.iqr" class="form-check-input" type="checkbox" value="iqr">
              <label class="form-check-label" for="algorithm-iqr">
                {{ $gettext('IQR Outlier Detection') }}
              </label>
            </div>
            <div class="form-check">
              <input id="algorithm-pareto" v-model="algorithms.pareto" class="form-check-input" type="checkbox" value="pareto">
              <label class="form-check-label" for="algorithm-pareto">
                {{ $gettext('Pareto analysis') }}
              </label>
            </div>
          </div>

          <div class="mb-3">
            <h6>{{ $gettext('Analysis direction') }}</h6>
            <div class="form-check">
              <input id="direction-rows" v-model="direction" class="form-check-input" type="radio" name="direction" value="rows">
              <label class="form-check-label" for="direction-rows">
                {{ $gettext('rows') }}
              </label>
            </div>
            <div class="form-check">
              <input id="direction-columns" v-model="direction" class="form-check-input" type="radio" name="direction" value="columns">
              <label class="form-check-label" for="direction-columns">
                {{ $gettext('columns') }}
              </label>
            </div>
          </div>

          <div class="d-flex gap-2">
            <ButtonComponent
              :text="$gettext('Recalculate')"
              button-type="primary"
              size="sm"
              :disabled="isRecalculating"
              @click="handleRecalculate"
            >
              <template v-if="isRecalculating">
                <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                <span>{{ $gettext('recalculating') }}...</span>
              </template>
              <template v-else>
                <span>{{ $gettext('Recalculate') }}</span>
              </template>
            </ButtonComponent>
            <ButtonComponent
              :text="$gettext('Reset to defaults')"
              button-type="secondary"
              size="sm"
              @click="resetToDefaults"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.highlight-outlier {
  background-color: #ffe6e6 !important;
  color: black !important;
}

.highlight-pareto {
  background-color: #e6ffe6 !important;
  color: black !important;
}

.highlight-excluded {
  background-color: #f0f0f0 !important;
  color: black !important;
}
</style>
