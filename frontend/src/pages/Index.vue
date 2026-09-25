<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'
import { useFeedbackStore } from '../stores/feedback.js'
import { useGettext } from 'vue3-gettext'
import { fetchProcessingResults, fetchTransactionsByResult } from '../js/api.js'
import { buildResultQuery } from '../js/routeUtils.js'
import type { ProcessingResultListItem } from '../types/api.js'

const { $gettext } = useGettext()
const router = useRouter()
const authStore = useAuthStore()
const feedback = useFeedbackStore()

const isLoading = ref(true)
const processingResults = ref<ProcessingResultListItem[]>([])
const totalTransactionCount = ref(0)

// Empty string means "All Transactions" (no result_id filter)
const selectedResultId = ref('')

const SELECTED_RESULT_STORAGE_KEY = 'selectedResultId'

const hasNoTransactions = computed(() =>
  processingResults.value.length === 0 && totalTransactionCount.value === 0
)

const formatResultLabel = (result: ProcessingResultListItem): string => {
  if (!result.created_at) {
    return result.id
  }
  const date = new Date(result.created_at)
  return Number.isNaN(date.getTime()) ? result.id : date.toLocaleString()
}

const sortResultsByNewest = (results: ProcessingResultListItem[]): ProcessingResultListItem[] => {
  return [...results].sort((a, b) => {
    const dateA = a.created_at ? new Date(a.created_at).getTime() : 0
    const dateB = b.created_at ? new Date(b.created_at).getTime() : 0
    return dateB - dateA
  })
}

const restoreSelectedResult = (): void => {
  const stored = localStorage.getItem(SELECTED_RESULT_STORAGE_KEY)
  selectedResultId.value =
    stored !== null && processingResults.value.some(result => result.id === stored)
      ? stored
      : ''
}

const loadProcessingResults = async (): Promise<void> => {
  if (!authStore.isAuthenticated) {
    isLoading.value = false
    return
  }

  try {
    const [results, transactions] = await Promise.all([
      fetchProcessingResults(),
      fetchTransactionsByResult(undefined, { limit: 1 })
    ])
    processingResults.value = sortResultsByNewest(results)
    totalTransactionCount.value = transactions.total_count
    restoreSelectedResult()
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : String(error)
    feedback.showError(`${$gettext('Failed to load your transactions')}: ${message}`)
    console.error('Failed to load processing results:', error)
  } finally {
    isLoading.value = false
  }
}

const viewResults = (): void => {
  if (selectedResultId.value) {
    localStorage.setItem(SELECTED_RESULT_STORAGE_KEY, selectedResultId.value)
  } else {
    localStorage.removeItem(SELECTED_RESULT_STORAGE_KEY)
  }
  router.push({ name: 'results', query: buildResultQuery(selectedResultId.value) })
}

// Watch for authentication changes and reload results
watch(() => authStore.isAuthenticated, (isAuthenticated) => {
  if (isAuthenticated) {
    loadProcessingResults()
  }
}, { immediate: true })

onMounted(() => {
  loadProcessingResults()
})
</script>

<template>
  <div class="container">
    <div v-if="isLoading" class="text-center my-5">
      <output class="spinner-border text-on-primary">
        <span class="visually-hidden">{{ $gettext('Loading') }}...</span>
      </output>
      <p class="mt-2">{{ $gettext('Loading your transactions') }}...</p>
    </div>

    <div v-else-if="hasNoTransactions" class="text-center my-5">
      <div class="card mx-auto" style="max-width: 600px;">
        <div class="card-header">
          {{ $gettext('Welcome') }}
        </div>
        <div class="card-body">
          <p>{{ $gettext('You have no transactions yet.') }}</p>
          <p>
            <RouterLink to="/import" class="btn bg-surface-primary text-on-primary border-primary">
              {{ $gettext('Import CSV') }}
            </RouterLink>
          </p>
        </div>
      </div>
    </div>

    <div v-else class="text-center my-5">
      <div class="card mx-auto" style="max-width: 600px;">
        <div class="card-header">
          {{ $gettext('Your Transactions') }}
        </div>
        <div class="card-body">
          <label for="result-selector" class="form-label">{{ $gettext('Select Result') }}</label>
          <select
            id="result-selector"
            v-model="selectedResultId"
            class="form-select mb-3"
          >
            <option value="">{{ $gettext('All Transactions') }}</option>
            <option v-for="result in processingResults" :key="result.id" :value="result.id">
              {{ formatResultLabel(result) }}
            </option>
          </select>
          <div class="d-flex justify-content-center gap-2">
            <button
              type="button"
              class="btn bg-surface-primary text-on-primary border-primary"
              @click="viewResults"
            >
              {{ $gettext('View Transactions') }}
            </button>
            <RouterLink
              to="/import"
              class="btn bg-surface-secondary text-on-dark border-secondary"
            >
              {{ $gettext('Import CSV') }}
            </RouterLink>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
