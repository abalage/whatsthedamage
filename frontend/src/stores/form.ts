import { defineStore } from 'pinia'
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { processTransactions } from '../js/api'
import { useFeedbackStore } from './feedback'
import type { ProcessResponse } from '../types/api'

/**
 * Form data interface for transaction processing
 */
interface FormData {
  csvFile: File | null
  configFile: File | null
  startDate: string
  endDate: string
  categoryFilter: string
  verbose: boolean
  mlEnabled: boolean
}

/**
 * Form validation errors interface
 */
interface FormErrors {
  csvFile?: string
  configFile?: string
  startDate?: string
  endDate?: string
  dateRange?: string
}

/**
 * Result of form submission
 */
interface SubmitResult {
  success: boolean
  resultId?: string
  error?: string
}

/**
 * Form store using Pinia for state management
 *
 * Note: Navigation is handled separately via a composable to avoid
 * the limitation of useRouter() not being available in Pinia stores.
 */
const useFormStore = defineStore('form', () => {
  const feedback = useFeedbackStore()

  /**
   * Reactive form data
   */
  const formData = reactive<FormData>({
    csvFile: null,
    configFile: null,
    startDate: '',
    endDate: '',
    categoryFilter: '',
    verbose: false,
    mlEnabled: false
  })

  /**
   * Validation errors
   */
  const errors = ref<FormErrors>({})

  /**
   * Loading state
   */
  const isLoading = ref(false)

  /**
   * Whether form has been submitted
   */
  const isSubmitted = ref(false)

  /**
   * Magic number for array index access (eslint)
   */
  const ARRAY_INDEX = 0

  /**
   * Reset form to initial state
   */
  const resetForm = (): void => {
    formData.csvFile = null
    formData.configFile = null
    formData.startDate = ''
    formData.endDate = ''
    formData.categoryFilter = ''
    formData.verbose = false
    formData.mlEnabled = false
    errors.value = {}
    isSubmitted.value = false
  }

  /**
   * Validate form data
   * @returns Whether the form is valid
   */
  const validateForm = (): boolean => {
    const newErrors: FormErrors = {}
    let isValid = true

    // CSV file validation
    if (!formData.csvFile) {
      newErrors.csvFile = 'CSV file is required'
      isValid = false
    } else if (!formData.csvFile.name.endsWith('.csv')) {
      newErrors.csvFile = 'Please upload a valid CSV file'
      isValid = false
    }

    // Config file validation (if provided)
    if (formData.configFile && !formData.configFile.name.endsWith('.yaml') && !formData.configFile.name.endsWith('.yml')) {
      newErrors.configFile = 'Please upload a valid YAML configuration file'
      isValid = false
    }

    // Date validation
    if (formData.startDate && isNaN(new Date(formData.startDate).getTime())) {
      newErrors.startDate = 'Please enter a valid start date'
      isValid = false
    }

    if (formData.endDate && isNaN(new Date(formData.endDate).getTime())) {
      newErrors.endDate = 'Please enter a valid end date'
      isValid = false
    }

    // Date range validation
    if (formData.startDate && formData.endDate) {
      const start = new Date(formData.startDate)
      const end = new Date(formData.endDate)
      if (start > end) {
        newErrors.dateRange = 'End date must be after start date'
        isValid = false
      }
    }

    errors.value = newErrors
    return isValid
  }

  /**
   * Handle file input change
   * @param event - Input change event
   * @param field - Field name (csvFile or configFile)
   */
  const handleFileChange = (event: Event, field: 'csvFile' | 'configFile'): void => {
    const target = event.target as HTMLInputElement
    if (target.files?.length) {
      formData[field] = target.files[ARRAY_INDEX]
      // Clear validation error for this field
      if (errors.value[field]) {
        errors.value[field] = undefined
      }
    }
  }

  /**
   * Handle generic input change
   * @param field - Field name (for non-file fields)
   * @param value - New value
   */
  const handleInputChange = (field: Exclude<keyof FormData, 'csvFile' | 'configFile'>, value: string | boolean): void => {
    formData[field] = value as never
    // Clear validation error for this field (only for fields that can have errors)
    if (field in errors.value) {
      errors.value[field as keyof FormErrors] = undefined
    }
  }

  /**
   * Prepare form data for submission (without navigation)
   * @returns Promise with result containing resultId or error
   */
  const prepareSubmit = async (): Promise<SubmitResult> => {
    if (!validateForm()) {
      feedback.showError('Please fix the form errors before submitting')
      return { success: false, error: 'Validation failed' }
    }

    isLoading.value = true
    feedback.clearMessages()

    try {
      const formDataObj = new FormData()

      // Append files
      if (formData.csvFile) {
        formDataObj.append('csv_file', formData.csvFile)
      }

      if (formData.configFile) {
        formDataObj.append('config_file', formData.configFile)
      }

      // Append parameters
      if (formData.startDate) {
        formDataObj.append('start_date', formData.startDate)
      }

      if (formData.endDate) {
        formDataObj.append('end_date', formData.endDate)
      }

      if (formData.categoryFilter) {
        formDataObj.append('category_filter', formData.categoryFilter)
      }

      formDataObj.append('verbose', formData.verbose.toString())
      formDataObj.append('ml_enabled', formData.mlEnabled.toString())

      // Call API
      const response: ProcessResponse = await processTransactions(formDataObj)

      // Extract result_id from metadata (new structure)
      const resultId = response.metadata?.result_id ?? response.result_id

      // Debug: Check if we have a valid result ID
      if (!resultId) {
        feedback.showError('Backend error: No result ID returned')
        return { success: false, error: 'No result ID returned' }
      }

      isSubmitted.value = true
      feedback.showSuccess('Transactions processed successfully')

      return { success: true, resultId }

    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : String(error)
      feedback.showError(`Error processing transactions: ${message}`)
      return { success: false, error: message }
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Check if form has errors
   */
  const hasErrors = computed((): boolean => {
    return Object.keys(errors.value).length > ARRAY_INDEX
  })

  /**
   * Get error for a specific field
   * @param field - Field name
   * @returns Error message or undefined
   */
  const getError = (field: keyof FormErrors): string | undefined => {
    return errors.value[field]
  }

  return {
    formData,
    errors,
    isLoading,
    isSubmitted,
    hasErrors,
    validateForm,
    handleFileChange,
    handleInputChange,
    prepareSubmit,
    resetForm,
    getError
  }
})

/**
 * Composable for form submission with navigation
 * This separates the navigation logic from the form state
 *
 * @returns Form store with navigation-capable submit function
 */
export const useFormWithNavigation = (): ReturnType<typeof useFormStore> & { submitForm: () => Promise<boolean> } => {
  const formStore = useFormStore()
  const router = useRouter()

  /**
   * Submit form with navigation to results page
   * @returns Promise with success status
   */
  const submitForm = async (): Promise<boolean> => {
    const result = await formStore.prepareSubmit()

    if (!result.success || !result.resultId) {
      return false
    }

    // Navigate to results page with the result ID
    try {
      await router.push({
        name: 'results',
        query: { resultId: result.resultId }
      })
      return true
    } catch (navError: unknown) {
      const message = navError instanceof Error ? navError.message : String(navError)
      formStore.$patch({ isLoading: false })
      useFeedbackStore().showError(`Navigation error: ${message}`)
      return false
    }
  }

  return {
    ...formStore,
    submitForm
  }
}


