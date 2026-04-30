<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useLocaleStore } from '../stores/locale'
import { getTranslation } from '../stores/translations'
import { fetchWithErrorHandling } from '../js/api'
import CardComponent from '../components/ui/CardComponent.vue'
import ButtonComponent from '../components/ui/ButtonComponent.vue'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

const localeStore = useLocaleStore()
const route = useRoute()
const router = useRouter()

const t = (key: string) => getTranslation(key, localeStore.locale)

interface CategoryData {
  category: string
  total: {
    display: string
    raw: number
  }
  row_id: string
  category_url: string
}

interface MonthCategoriesResponse {
  result_id: string
  account_id: string
  account_name: string
  month_id: string
  month_name: string
  data: CategoryData[]
}

const resultId = computed(() => route.params.resultId as string)
const accountId = computed(() => route.params.accountId as string)
const monthId = computed(() => route.params.monthId as string)

const monthCategoriesData = ref<MonthCategoriesResponse | null>(null)
const isLoading = ref(true)
const error = ref<string | null>(null)

const fetchMonthCategories = async () => {
  if (!resultId.value || !accountId.value || !monthId.value) {
    error.value = 'Missing required parameters'
    isLoading.value = false
    return
  }

  try {
    isLoading.value = true
    error.value = null
    
    const response = await fetchWithErrorHandling<MonthCategoriesResponse>(
      `${API_BASE_URL}/results/${resultId.value}/accounts/${accountId.value}/months/${monthId.value}/categories`
    )
    
    monthCategoriesData.value = response
  } catch (err) {
    console.error('Failed to fetch month categories:', err)
    error.value = err instanceof Error ? err.message : 'Failed to load month categories'
  } finally {
    isLoading.value = false
  }
}

const navigateToTransactions = (categoryData: CategoryData) => {
  // Navigate to the transactions view for this specific category
  router.push({
    name: 'category-month-transactions',
    params: {
      resultId: resultId.value,
      accountId: accountId.value,
      categoryId: categoryData.category,
      monthId: monthId.value
    }
  })
}

onMounted(() => {
  fetchMonthCategories()
})
</script>

<template>
  <div class="container">
    <!-- Breadcrumb Navigation -->
    <nav aria-label="breadcrumb">
      <ol class="breadcrumb">
        <li class="breadcrumb-item"><router-link to="/">{{ t('Home') }}</router-link></li>
        <li class="breadcrumb-item"><router-link :to="{ name: 'results', query: { resultId: resultId } }">{{ t('Results') }}</router-link></li>
        <li class="breadcrumb-item active" aria-current="page">{{ t('Month Details') }}</li>
      </ol>
    </nav>

    <!-- Loading State -->
    <div v-if="isLoading" class="text-center my-5">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">{{ t('loading') }}...</span>
      </div>
      <p class="mt-2">{{ t('loadingData') }}...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="alert alert-danger">
      {{ error }}
    </div>

    <!-- Main Content -->
    <div v-else-if="monthCategoriesData">
      <div class="d-flex justify-content-between align-items-center mb-3">
        <h1 class="mb-0">{{ t('Details for Month') }}: {{ monthCategoriesData.month_name }}</h1>
      </div>

      <!-- Account Card -->
      <CardComponent :title="monthCategoriesData.account_name" class="mb-4">
        <div class="row">
          <div class="col-md-6 mb-3">
            <div class="table-responsive">
              <table id="datatable-month" class="table table-bordered" data-datatable="true">
                <thead>
                  <tr>
                    <th>{{ t('Category') }}</th>
                    <th>{{ t('Total') }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="category in monthCategoriesData.data" :key="category.row_id">
                    <td>
                      <a href="#" class="clickable" @click.prevent="navigateToTransactions(category)">
                        {{ category.category }}
                      </a>
                    </td>
                    <td :data-row-id="category.row_id" class="">
                      {{ category.total.display }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </CardComponent>

      <!-- Navigation -->
      <div class="row">
        <div class="col-md-6">
          <ButtonComponent 
            :text="t('Back to Results')" 
            variant="secondary" 
            :to="{ name: 'results', query: { resultId: resultId } }" 
            class="mt-3 mb-3"
          />
        </div>
      </div>
    </div>

    <!-- No Data State -->
    <div v-else class="alert alert-info">
      {{ t('noDataFound') }}
    </div>
  </div>
</template>

<style scoped>
.clickable {
  cursor: pointer;
  text-decoration: underline;
}

.clickable:hover {
  color: #0d6efd;
}
</style>