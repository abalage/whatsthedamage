import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { processTransactions } from '../js/api'
import { useFeedbackStore } from './feedback'

interface FormData {
  csvFile: File | null
  configFile: File | null
  startDate: string
  endDate: string
  categoryFilter: string
  verbose: boolean
  mlEnabled: boolean
}

interface FormErrors {
  csvFile?: string
  configFile?: string
  startDate?: string
  endDate?: string
  dateRange?: string
}

export const useFormStore = (): FormStore => {
  const router = useRouter()
  const feedback = useFeedbackStore()

  const formData = reactive<FormData>({
    csvFile: null,
    configFile: null,
    startDate: '',
    endDate: '',
    categoryFilter: '',
    verbose: false,
    mlEnabled: false
  })

  const errors = ref<FormErrors>({})
  const isLoading = ref(false)
  const isSubmitted = ref(false)

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

  const handleFileChange = (event: Event, field: 'csvFile' | 'configFile'): void => {
    const target = event.target as HTMLInputElement
    const MIN_FILES = 0
    const FIRST_FILE_INDEX = 0
    if (target.files && target.files.length > MIN_FILES) {
      formData[field] = target.files[FIRST_FILE_INDEX]
      // Clear validation error for this field
      if (errors.value[field]) {
        errors.value[field] = undefined
      }
    }
  }

  const handleInputChange = (field: keyof FormData, value: string | boolean): void => {
    formData[field] = value
    // Clear validation error for this field
    if (errors.value[field]) {
      errors.value[field] = undefined
    }
  }

  const submitForm = async (): Promise<boolean> => {
    if (!validateForm()) {
      feedback.showError('Please fix the form errors before submitting')
      return false
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
      const response = await processTransactions(formDataObj)

      // Navigate to results page
      isSubmitted.value = true
      
      // Extract result_id from metadata (new structure)
      const resultId = response.metadata?.result_id ?? response.result_id
      
      // Debug: Check if we have a valid result ID
      if (!resultId) {
        feedback.showError('Backend error: No result ID returned')
        return false
      }
      
      // Navigate with query parameters
      try {
        router.push({
          name: 'results',
          query: { resultId: resultId }
        })
      } catch (/* eslint-disable-line @typescript-eslint/no-unused-vars */ _navError: unknown) {
        feedback.showError('Navigation error: Could not redirect to results')
        return false
      }

      feedback.showSuccess('Transactions processed successfully')
      return true

    } catch (_error: unknown) {
      feedback.showError('Error processing transactions: ' + (_error instanceof Error ? _error.message : String(_error)))
      return false
    } finally {
      isLoading.value = false
    }
  }

  const hasErrors = computed((): boolean => {
    const MIN_ERRORS = 0
    return Object.keys(errors.value).length > MIN_ERRORS
  })

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
    submitForm,
    resetForm,
    getError
  }
}

export type FormStore = ReturnType<typeof useFormStore>