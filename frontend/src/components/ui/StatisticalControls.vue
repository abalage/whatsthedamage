<script setup lang="ts">
import { ref, computed } from 'vue'
import { useStatisticalStore } from '../../stores/statistical'
import { recalculateStatistics } from '../../js/api'
import ButtonComponent from './ButtonComponent.vue'

interface StatisticalControlsProps {
  resultId: string
}

const props = defineProps<StatisticalControlsProps>()

const statisticalStore = useStatisticalStore()

// Legend visibility
const legendVisible = ref(false)
const statsControlsVisible = ref(false)

// Algorithm selections
const algorithms = ref({
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

const recalculateStatistics = async () => {
  try {
    isRecalculating.value = true
    
    const selectedAlgorithms = []
    if (algorithms.value.iqr) selectedAlgorithms.push('iqr')
    if (algorithms.value.pareto) selectedAlgorithms.push('pareto')
    
    await recalculateStatistics(
      props.resultId,
      selectedAlgorithms,
      direction.value
    )
    
    // Update store with new settings
    statisticalStore.setAlgorithms(selectedAlgorithms)
    statisticalStore.setDirection(direction.value)
    
  } catch (error) {
    console.error('Error recalculating statistics:', error)
    // Could show error message to user
  } finally {
    isRecalculating.value = false
  }
}

const resetToDefaults = () => {
  algorithms.value = {
    iqr: true,
    pareto: true
  }
  direction.value = 'columns'
  statisticalStore.resetToDefaults()
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
        {{ $t('legend') }}
      </button>
      <div :class="legendClasses" id="legend">
        <div class="card card-body">
          <p><span class="badge highlight-outlier">{{ $t('outlier') }}</span> {{ $t('outlierDescription') }}</p>
          <p><span class="badge highlight-pareto">{{ $t('pareto') }}</span> {{ $t('paretoDescription') }}</p>
          <p><span class="badge highlight-excluded">{{ $t('excluded') }}</span> {{ $t('excludedDescription') }}</p>
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
        {{ $t('statisticalAnalysisControls') }}
      </button>
      <div :class="statsControlsClasses" id="stats-controls">
        <div class="card card-body">
          <div class="mb-3">
            <h6>{{ $t('algorithms') }}</h6>
            <div class="form-check">
              <input class="form-check-input" type="checkbox" value="iqr" id="algorithm-iqr" v-model="algorithms.iqr">
              <label class="form-check-label" for="algorithm-iqr">
                {{ $t('iqrOutlierDetection') }}
              </label>
            </div>
            <div class="form-check">
              <input class="form-check-input" type="checkbox" value="pareto" id="algorithm-pareto" v-model="algorithms.pareto">
              <label class="form-check-label" for="algorithm-pareto">
                {{ $t('paretoAnalysis') }}
              </label>
            </div>
          </div>

          <div class="mb-3">
            <h6>{{ $t('analysisDirection') }}</h6>
            <div class="form-check">
              <input class="form-check-input" type="radio" name="direction" id="direction-rows" value="rows" v-model="direction">
              <label class="form-check-label" for="direction-rows">
                {{ $t('rows') }}
              </label>
            </div>
            <div class="form-check">
              <input class="form-check-input" type="radio" name="direction" id="direction-columns" value="columns" v-model="direction">
              <label class="form-check-label" for="direction-columns">
                {{ $t('columns') }}
              </label>
            </div>
          </div>

          <div class="d-flex gap-2">
            <ButtonComponent
              text="{{ $t('recalculate') }}"
              buttonType="primary"
              size="sm"
              :disabled="isRecalculating"
              @click="recalculateStatistics"
            >
              <template v-if="isRecalculating">
                <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                <span>{{ $t('recalculating') }}...</span>
              </template>
              <template v-else>
                <span>{{ $t('recalculate') }}</span>
              </template>
            </ButtonComponent>
            <ButtonComponent
              text="{{ $t('resetToDefaults') }}"
              buttonType="secondary"
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
  background-color: #dc3545;
  color: white;
}

.highlight-pareto {
  background-color: #28a745;
  color: white;
}

.highlight-excluded {
  background-color: #6c757d;
  color: white;
}
</style>