import { defineStore } from 'pinia'
import { ref, reactive, computed } from 'vue'
import { createTransaction } from '../js/api'
import type { ProcessingResultCreationResponse } from '../types/api'

/**
 * Validation error codes for the transaction processing form.
 * The page maps these codes to translated user-facing messages;
 * the store itself holds no UI strings.
 */
export type FormErrorCode =
  | 'csvRequired'
  | 'csvInvalid'
  | 'configInvalid'
  | 'startDateInvalid'
  | 'endDateInvalid'
  | 'dateRangeInvalid'

/**
 * Submission failure codes returned by prepareSubmit
 */
type SubmitErrorCode =
  | 'notAuthenticated'
  | 'validationFailed'
  | 'noResultId'
  | 'processingFailed'

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
  csvProfileId: string | null
}

/**
 * Form validation errors: field -> error code
 */
type FormErrors = Partial<Record<'csvFile' | 'configFile' | 'startDate' | 'endDate' | 'dateRange', FormErrorCode>>

/**
 * Result of form submission: either a resultId or a failure code
 * with the underlying message for logging/diagnostics
 */
interface SubmitResult {
  success: boolean
  resultId?: string
  errorCode?: SubmitErrorCode
  errorMessage?: string
}

/**
 * Form store using Pinia for state management
 *
 * The store owns form state, validation, and the API call.
 * User-facing feedback and navigation are handled by the
 * useFormWithNavigation composable so messages can be translated
 * in the component context.
 */
const useFormStore = defineStore('form', () => {
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
    mlEnabled: false,
    csvProfileId: null
  })

  /**
   * Validation error codes
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
    formData.csvProfileId = null
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
      newErrors.csvFile = 'csvRequired'
      isValid = false
    } else if (!formData.csvFile.name.endsWith('.csv')) {
      newErrors.csvFile = 'csvInvalid'
      isValid = false
    }

    // Config file validation (if provided)
    if (formData.configFile && !formData.configFile.name.endsWith('.yaml') && !formData.configFile.name.endsWith('.yml')) {
      newErrors.configFile = 'configInvalid'
      isValid = false
    }

    // Date validation
    if (formData.startDate && Number.isNaN(new Date(formData.startDate).getTime())) {
      newErrors.startDate = 'startDateInvalid'
      isValid = false
    }

    if (formData.endDate && Number.isNaN(new Date(formData.endDate).getTime())) {
      newErrors.endDate = 'endDateInvalid'
      isValid = false
    }

    // Date range validation
    if (formData.startDate && formData.endDate) {
      const start = new Date(formData.startDate)
      const end = new Date(formData.endDate)
      if (start > end) {
        newErrors.dateRange = 'dateRangeInvalid'
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
      formData[field] = target.files[0]
      errors.value[field] = undefined
    }
  }

  /**
   * Handle generic input change
   * @param field - Field name (for non-file fields)
   * @param value - New value
   */
  const handleInputChange = (field: Exclude<keyof FormData, 'csvFile' | 'configFile'>, value: string | boolean): void => {
    formData[field] = value as never
    if (field in errors.value) {
      errors.value[field as keyof FormErrors] = undefined
    }
  }

  /**
   * Validate the form and submit it to the processing API.
   *
   * The caller (useFormWithNavigation) is responsible for user-facing
   * feedback and navigation based on the returned code.
   *
   * @returns Promise with the resultId or a failure code
   */
  const prepareSubmit = async (): Promise<SubmitResult> => {
    if (!validateForm()) {
      return { success: false, errorCode: 'validationFailed' }
    }

    isLoading.value = true

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

      // Append CSV profile ID if provided
      if (formData.csvProfileId) {
        formDataObj.append('csv_profile_id', formData.csvProfileId)
      }

      formDataObj.append('verbose', formData.verbose.toString())
      formDataObj.append('ml_enabled', formData.mlEnabled.toString())

      // Call API
      const response: ProcessingResultCreationResponse = await createTransaction(formDataObj)

      // Extract result_id from response (flat structure, not nested in metadata)
      const resultId = response.result_id

      if (!resultId) {
        return { success: false, errorCode: 'noResultId' }
      }

      isSubmitted.value = true

      return { success: true, resultId }
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : String(error)
      return { success: false, errorCode: 'processingFailed', errorMessage: message }
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Check if form has errors
   */
  const hasErrors = computed((): boolean => {
    return Object.keys(errors.value).length > 0
  })

  /**
   * Get the error code for a specific field
   * @param field - Field name
   * @returns Error code or undefined
   */
  const getError = (field: keyof FormErrors): FormErrorCode | undefined => {
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

export default useFormStore
