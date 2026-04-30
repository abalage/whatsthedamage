<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useLocaleStore } from '../stores/locale'
import { getTranslation } from '../stores/translations'
import { useFormStore } from '../stores/form'
import { useFeedbackStore } from '../stores/feedback'
import CardComponent from '../components/ui/CardComponent.vue'
import ButtonComponent from '../components/ui/ButtonComponent.vue'
import ErrorDisplay from '../components/ErrorDisplay.vue'

const localeStore = useLocaleStore()
const formStore = useFormStore()
const feedback = useFeedbackStore()

const t = (key: string) => getTranslation(key, localeStore.locale.value)

const fileInput = ref<HTMLInputElement | null>(null)
const configInput = ref<HTMLInputElement | null>(null)

const handleCsvChange = (event: Event) => {
  formStore.handleFileChange(event, 'csvFile')
}

const handleConfigChange = (event: Event) => {
  formStore.handleFileChange(event, 'configFile')
}

const handleInputChange = (field: any, value: any) => {
  formStore.handleInputChange(field, value)
}

const submitForm = async () => {
  await formStore.submitForm()
}

const clearForm = () => {
  if (confirm(t('clearFormConfirmation'))) {
    formStore.resetForm()
    feedback.showInfo(t('formCleared'))
    if (fileInput.value) fileInput.value.value = ''
    if (configInput.value) configInput.value.value = ''
  }
}

onMounted(() => {
  // Initialize form if needed
})
</script>

<template>
  <div class="container">
    <!-- Error Display -->
    <ErrorDisplay />
    
    <form @submit.prevent="submitForm" enctype="multipart/form-data">
      <div class="row">
        <div class="col-md-6 mb-3">
          <CardComponent :title="t('fileUploads')" type="standard">
            <div class="mb-3">
              <label for="filename" class="form-label">{{ t('csvFile') }}:</label>
              <input 
                type="file" 
                class="form-control" 
                id="filename" 
                ref="fileInput"
                @change="handleCsvChange"
                :class="{ 'is-invalid': formStore.getError('csvFile') }"
              />
              <div class="invalid-feedback" v-if="formStore.getError('csvFile')">
                {{ formStore.getError('csvFile') }}
              </div>
              <div id="fileHelp" class="form-text">{{ t('fileHelp') }}</div>
            </div>
            <div class="mb-3">
              <label for="config" class="form-label">{{ t('configFile') }}:</label>
              <input 
                type="file" 
                class="form-control"
                id="config" 
                ref="configInput"
                @change="handleConfigChange"
                :class="{ 'is-invalid': formStore.getError('configFile') }"
              />
              <div class="invalid-feedback" v-if="formStore.getError('configFile')">
                {{ formStore.getError('configFile') }}
              </div>
              <div id="configHelp" class="form-text">{{ t('configHelp') }}</div>
            </div>
          </CardComponent>
        </div>
        <div class="col-md-6 mb-3">
          <CardComponent :title="t('filters')" type="standard">
            <div class="mb-3">
              <label for="start_date" class="form-label">{{ t('startDate') }}:</label>
              <input 
                type="date" 
                class="form-control" 
                id="start_date"
                v-model="formStore.formData.startDate"
                @change="handleInputChange('startDate', $event.target.value)"
                :class="{ 'is-invalid': formStore.getError('startDate') }"
              />
              <div class="invalid-feedback" v-if="formStore.getError('startDate')">
                {{ formStore.getError('startDate') }}
              </div>
              <div id="dateStartHelp" class="form-text">{{ t('dateStartHelp') }}</div>
            </div>
            <div class="mb-3">
              <label for="end_date" class="form-label">{{ t('endDate') }}:</label>
              <input 
                type="date" 
                class="form-control" 
                id="end_date"
                v-model="formStore.formData.endDate"
                @change="handleInputChange('endDate', $event.target.value)"
                :class="{ 'is-invalid': formStore.getError('endDate') }"
              />
              <div class="invalid-feedback" v-if="formStore.getError('endDate')">
                {{ formStore.getError('endDate') }}
              </div>
              <div id="dateEndHelp" class="form-text">{{ t('dateEndHelp') }}</div>
            </div>
            <div class="mb-3">
              <label for="filter" class="form-label">{{ t('categoryFilter') }}:</label>
              <input 
                type="text" 
                class="form-control" 
                id="filter"
                v-model="formStore.formData.categoryFilter"
                @input="handleInputChange('categoryFilter', $event.target.value)"
              />
              <div id="filterHelp" class="form-text">{{ t('filterHelp') }}</div>
            </div>
            <div class="invalid-feedback" v-if="formStore.getError('dateRange')">
              {{ formStore.getError('dateRange') }}
            </div>
          </CardComponent>
        </div>
      </div>
      <div class="row">
        <div class="col-md-12 mb-3">
          <CardComponent :title="t('advancedSettings')" type="standard">
            <div class="mb-3 form-check">
              <input 
                type="checkbox" 
                class="form-check-input" 
                id="verbose"
                v-model="formStore.formData.verbose"
                @change="handleInputChange('verbose', $event.target.checked)"
              />
              <label class="form-check-label" for="verbose">{{ t('verboseLogging') }}</label>
              <div id="verboseHelp" class="form-text">{{ t('verboseHelp') }}</div>
            </div>
            <div class="mb-3 form-check">
              <input 
                type="checkbox" 
                class="form-check-input" 
                id="ml"
                v-model="formStore.formData.mlEnabled"
                @change="handleInputChange('mlEnabled', $event.target.checked)"
              />
              <label class="form-check-label" for="ml">
                {{ t('useML') }}
              </label>
              <div id="mlHelp" class="form-text">
                {{ t('mlHelp') }}
              </div>
            </div>
          </CardComponent>
        </div>
      </div>
      <div class="row">
        <div class="col-md-6">
          <ButtonComponent
            :text="formStore.isLoading.value ? t('processing') : t('submit')"
            buttonType="primary"
            type="submit"
            :disabled="formStore.isLoading.value"
            size="lg"
          />
        </div>
        <div class="col-md-6 text-end">
          <ButtonComponent
            :text="t('clearForm')"
            buttonType="secondary"
            type="button"
            @click="clearForm"
            size="lg"
          />
        </div>
      </div>
    </form>
  </div>
</template>

<style scoped>
/* Add component-specific styles here */
</style>