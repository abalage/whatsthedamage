<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useFormWithNavigation } from '../stores/form.js'
import { useFeedbackStore } from '../stores/feedback.js'
import { useGettext } from 'vue3-gettext'
import CardComponent from '../components/ui/CardComponent.vue'
import ButtonComponent from '../components/ui/ButtonComponent.vue'
import ErrorDisplay from '../components/ErrorDisplay.vue'

const { $gettext } = useGettext()
const { formStore, submitForm: submitFormFn } = useFormWithNavigation()
const feedback = useFeedbackStore()


const fileInput = ref<HTMLInputElement | null>(null)
const configInput = ref<HTMLInputElement | null>(null)

const handleCsvChange = (event: Event) => {
  formStore.handleFileChange(event, 'csvFile')
}

const handleConfigChange = (event: Event) => {
  formStore.handleFileChange(event, 'configFile')
}

type InputField = 'mlEnabled' | 'cacheEnabled'

const handleInputChange = (field: InputField, value: string | boolean) => {
  formStore.handleInputChange(field, value)
}

const handleCheckboxChange = (field: InputField, event: Event) => {
  const target = event.target as HTMLInputElement
  handleInputChange(field, target.checked)
}

const submitForm = async () => {
  await submitFormFn()
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
      <CardComponent :title="$gettext('File uploads')" type="standard" width="75%">
      <div class="row">
          <div class="col-md-12 mb-3">
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
            <label for="ml" class="form-label">{{ $gettext('Advanced settings') }}:</label>
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
            <div class="mb-3 form-check">
              <input
                id="cacheData"
                v-model="formStore.formData.cacheEnabled"
                type="checkbox"
                class="form-check-input"
                @change="handleCheckboxChange('cacheEnabled', $event)"
              />
              <label class="form-check-label" for="cacheData">
                {{ $gettext('Cache data with TTL') }}
              </label>
              <div id="cacheHelp" class="form-text">
                {{ $gettext('Checked: cache with default TTL (30 min). Unchecked: cache never expires.') }}
              </div>
            </div>
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
      </CardComponent>
    </form>
  </div>
</template>
