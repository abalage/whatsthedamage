<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRouter, RouterLink } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'
import { useFeedbackStore } from '../stores/feedback.js'
import { useGettext } from 'vue3-gettext'
import { fetchProcessingResults } from '../js/api.js'
import type { ProcessingResultListItem } from '../types/api.js'

const { $gettext } = useGettext()
const router = useRouter()
const authStore = useAuthStore()
const feedback = useFeedbackStore()

const isLoading = ref(true)
const processingResults = ref<ProcessingResultListItem[]>([])

const loadProcessingResults = async (): Promise<void> => {
  if (!authStore.isAuthenticated) {
    isLoading.value = false
    return
  }

  try {
    processingResults.value = await fetchProcessingResults()
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : String(error)
    feedback.showError(`${$gettext('Failed to load your transactions')}: ${message}`)
    console.error('Failed to load processing results:', error)
  } finally {
    isLoading.value = false
  }
}

// Watch for authentication changes and reload results
watch(() => authStore.isAuthenticated, (isAuthenticated) => {
  if (isAuthenticated) {
    loadProcessingResults()
  }
}, { immediate: true })

// Redirect to latest result when results are loaded
watch(processingResults, (results) => {
  if (results.length > 0) {
    // Sort by created_at descending and get the most recent
    const sortedResults = [...results].sort((a, b) => {
      const dateA = a.created_at ? new Date(a.created_at).getTime() : 0
      const dateB = b.created_at ? new Date(b.created_at).getTime() : 0
      return dateB - dateA
    })
    router.push({ name: 'results', query: { resultId: sortedResults[0].id } })
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

    <div v-else-if="!isLoading && processingResults.length === 0" class="text-center my-5">
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
  </div>
</template>
