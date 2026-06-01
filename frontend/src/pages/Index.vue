<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useFormWithNavigation } from '../stores/form'
import { useFeedbackStore } from '../stores/feedback'
import { useGettext } from 'vue3-gettext'
import CardComponent from '../components/ui/CardComponent.vue'
import ButtonComponent from '../components/ui/ButtonComponent.vue'
import ErrorDisplay from '../components/ErrorDisplay.vue'

const { $gettext } = useGettext()
const formStore = useFormWithNavigation()
const feedback = useFeedbackStore()


const fileInput = ref<HTMLInputElement | null>(null)
const configInput = ref<HTMLInputElement | null>(null)

const handleCsvChange = (event: Event) => {
  formStore.handleFileChange(event, 'csvFile')
}

const handleConfigChange = (event: Event) => {
  formStore.handleFileChange(event, 'configFile')
}

type InputField = 'startDate' | 'endDate' | 'categoryFilter' | 'verbose' | 'mlEnabled'

const handleInputChange = (field: InputField, value: string | boolean) => {
  formStore.handleInputChange(field, value)
}

const handleDateChange = (field: InputField, event: Event) => {
  const target = event.target as HTMLInputElement
  handleInputChange(field, target.value)
}

const handleCheckboxChange = (field: InputField, event: Event) => {
  const target = event.target as HTMLInputElement
  handleInputChange(field, target.checked)
}

const handleTextInput = (field: InputField, event: Event) => {
  const target = event.target as HTMLInputElement
  handleInputChange(field, target.value)
}

const submitForm = async () => {
  await formStore.submitForm()
}

const clearForm = () => {
  if (confirm($gettext('Are you sure you want to clear the form?'))) {
    formStore.resetForm()
    feedback.showInfo($gettext('Form cleared'))
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
          <CardComponent :title="$gettext('File uploads')" type="standard">
            <div class="mb-3">
              <label for="filename" class="form-label">{{ $gettext('CSV file') }}:</label>
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
              <div id="fileHelp" class="form-text">{{ $gettext('Upload your CSV file containing the exported bank account history') }}</div>
            </div>
            <div class="mb-3">
              <label for="config" class="form-label">{{ $gettext('Configuration file') }}:</label>
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
              <div id="configHelp" class="form-text">{{ $gettext('Upload your configuration file here, or the default configuration will be used') }}</div>
            </div>
          </CardComponent>
        </div>
        <div class="col-md-6 mb-3">
          <CardComponent :title="$gettext('Filters')" type="standard">
            <div class="mb-3">
              <label for="start_date" class="form-label">{{ $gettext('Start date') }}:</label>
              <input
                id="start_date"
                v-model="formStore.formData.startDate"
                type="date"
                class="form-control"
                :class="{ 'is-invalid': formStore.getError('startDate') }"
                @change="handleDateChange('startDate', $event)"
              />
              <div v-if="formStore.getError('startDate')" class="invalid-feedback">
                {{ formStore.getError('startDate') }}
              </div>
              <div id="dateStartHelp" class="form-text">{{ $gettext('Filter results starting from this date') }}</div>
            </div>
            <div class="mb-3">
              <label for="end_date" class="form-label">{{ $gettext('End date') }}:</label>
              <input
                id="end_date"
                v-model="formStore.formData.endDate"
                type="date"
                class="form-control"
                :class="{ 'is-invalid': formStore.getError('endDate') }"
                @change="handleDateChange('endDate', $event)"
              />
              <div v-if="formStore.getError('endDate')" class="invalid-feedback">
                {{ formStore.getError('endDate') }}
              </div>
              <div id="dateEndHelp" class="form-text">{{ $gettext('Filter results up until this date') }}</div>
            </div>
            <div class="mb-3">
              <label for="filter" class="form-label">{{ $gettext('Category filter') }}:</label>
              <input
                id="filter"
                v-model="formStore.formData.categoryFilter"
                type="text"
                class="form-control"
                @input="handleTextInput('categoryFilter', $event)"
              />
              <div id="filterHelp" class="form-text">{{ $gettext('Filter by category. (default = "category")') }}</div>
            </div>
            <div v-if="formStore.getError('dateRange')" class="invalid-feedback">
              {{ formStore.getError('dateRange') }}
            </div>
          </CardComponent>
        </div>
      </div>
      <div class="row">
        <div class="col-md-12 mb-3">
          <CardComponent :title="$gettext('Advanced settings')" type="standard">
            <div class="mb-3 form-check">
              <input
                id="verbose"
                v-model="formStore.formData.verbose"
                type="checkbox"
                class="form-check-input"
                @change="handleCheckboxChange('verbose', $event)"
              />
              <label class="form-check-label" for="verbose">{{ $gettext('Enable verbose logging') }}</label>
              <div id="verboseHelp" class="form-text">{{ $gettext('Enable detailed logging in the backend') }}</div>
            </div>
            <div class="mb-3 form-check">
              <input
                id="ml"
                v-model="formStore.formData.mlEnabled"
                type="checkbox"
                class="form-check-input"
                @change="handleCheckboxChange('mlEnabled', $event)"
              />
              <label class="form-check-label" for="ml">
                {{ $gettext('Use Machine Learning model for categorization') }}
              </label>
              <div id="mlHelp" class="form-text">
                {{ $gettext('Uncheck to use regular expressions instead of the ML model') }}
              </div>
            </div>
          </CardComponent>
        </div>
      </div>
      <div class="row">
        <div class="col-md-6">
          <ButtonComponent
            :text="formStore.isLoading ? $gettext('Processing your transactions...') : $gettext('Submit')"
            variant="primary"
            type="submit"
            :disabled="formStore.isLoading"
            size="lg"
          />
        </div>
        <div class="col-md-6 text-end">
          <ButtonComponent
            :text="$gettext('Clear form')"
            variant="secondary"
            type="button"
            size="lg"
            @click="clearForm"
          />
        </div>
      </div>
    </form>
  </div>
</template>
