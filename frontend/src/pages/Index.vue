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

    <form enctype="multipart/form-data" @submit.prevent="submitForm">
      <div class="row">
        <div class="col-md-6 mb-3">
          <CardComponent :title="t('fileUploads')" type="standard">
            <div class="mb-3">
              <label for="filename" class="form-label">{{ t('csvFile') }}:</label>
              <input
                id="filename"
                ref="fileInput"
                type="file"
                class="form-control"
                :class="{ 'is-invalid': formStore.getError('csvFile') }"
                @change="handleCsvChange"
              />
              <div v-if="formStore.getError('csvFile')" class="invalid-feedback">
                {{ formStore.getError('csvFile') }}
              </div>
              <div id="fileHelp" class="form-text">{{ t('fileHelp') }}</div>
            </div>
            <div class="mb-3">
              <label for="config" class="form-label">{{ t('configFile') }}:</label>
              <input
                id="config"
                ref="configInput"
                type="file"
                class="form-control"
                :class="{ 'is-invalid': formStore.getError('configFile') }"
                @change="handleConfigChange"
              />
              <div v-if="formStore.getError('configFile')" class="invalid-feedback">
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
                id="start_date"
                v-model="formStore.formData.startDate"
                type="date"
                class="form-control"
                :class="{ 'is-invalid': formStore.getError('startDate') }"
                @change="handleInputChange('startDate', $event.target.value)"
              />
              <div v-if="formStore.getError('startDate')" class="invalid-feedback">
                {{ formStore.getError('startDate') }}
              </div>
              <div id="dateStartHelp" class="form-text">{{ t('dateStartHelp') }}</div>
            </div>
            <div class="mb-3">
              <label for="end_date" class="form-label">{{ t('endDate') }}:</label>
              <input
                id="end_date"
                v-model="formStore.formData.endDate"
                type="date"
                class="form-control"
                :class="{ 'is-invalid': formStore.getError('endDate') }"
                @change="handleInputChange('endDate', $event.target.value)"
              />
              <div v-if="formStore.getError('endDate')" class="invalid-feedback">
                {{ formStore.getError('endDate') }}
              </div>
              <div id="dateEndHelp" class="form-text">{{ t('dateEndHelp') }}</div>
            </div>
            <div class="mb-3">
              <label for="filter" class="form-label">{{ t('categoryFilter') }}:</label>
              <input
                id="filter"
                v-model="formStore.formData.categoryFilter"
                type="text"
                class="form-control"
                @input="handleInputChange('categoryFilter', $event.target.value)"
              />
              <div id="filterHelp" class="form-text">{{ t('filterHelp') }}</div>
            </div>
            <div v-if="formStore.getError('dateRange')" class="invalid-feedback">
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
                id="verbose"
                v-model="formStore.formData.verbose"
                type="checkbox"
                class="form-check-input"
                @change="handleInputChange('verbose', $event.target.checked)"
              />
              <label class="form-check-label" for="verbose">{{ t('verboseLogging') }}</label>
              <div id="verboseHelp" class="form-text">{{ t('verboseHelp') }}</div>
            </div>
            <div class="mb-3 form-check">
              <input
                id="ml"
                v-model="formStore.formData.mlEnabled"
                type="checkbox"
                class="form-check-input"
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
            button-type="primary"
            type="submit"
            :disabled="formStore.isLoading.value"
            size="lg"
          />
        </div>
        <div class="col-md-6 text-end">
          <ButtonComponent
            :text="t('clearForm')"
            button-type="secondary"
            type="button"
            size="lg"
            @click="clearForm"
          />
        </div>
      </div>
    </form>
  </div>
</template>

<style scoped>
/* Add component-specific styles here */
</style>