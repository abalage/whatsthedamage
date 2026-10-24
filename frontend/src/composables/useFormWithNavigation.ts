/**
 * Composable for form submission with navigation
 *
 * Runs in the component context: translates user-facing messages,
 * shows feedback, and navigates to the results page. The form store
 * itself owns only form state, validation, and the API call.
 * @module composables/useFormWithNavigation
 */

import { useGettext } from 'vue3-gettext'
import { useRouter } from 'vue-router'
import useFormStore, { type FormErrorCode } from '../stores/form'
import { useFeedbackStore } from '../stores/feedback'
import { useAuthStore } from '../stores/auth'
import { useDatasetStore } from '../stores/dataset'

/**
 * Result of useFormWithNavigation
 */
interface FormWithNavigation {
  /** The backing form store */
  formStore: ReturnType<typeof useFormStore>
  /** Translation of form validation error codes */
  formErrorMessage: (code: FormErrorCode) => string
  /** Submits the form and navigates to the results page */
  submitForm: () => Promise<boolean>
}

/**
 * Form submission with navigation to the results page
 *
 * @returns The form store instance, a translation helper for
 *  validation error codes, and the navigation-capable submit function
 */
export const useFormWithNavigation = (): FormWithNavigation => {
  const { $gettext } = useGettext()
  const formStore = useFormStore()
  const router = useRouter()
  const authStore = useAuthStore()
  const feedback = useFeedbackStore()
  const datasetStore = useDatasetStore()

  /**
   * Translation of form validation error codes
   * @param code - Error code reported by the form store
   * @returns Translated error message
   */
  const formErrorMessage = (code: FormErrorCode): string => {
    switch (code) {
      case 'csvRequired':
        return $gettext('CSV file is required')
      case 'csvInvalid':
        return $gettext('Please upload a valid CSV file')
      case 'configInvalid':
        return $gettext('Please upload a valid YAML configuration file')
      case 'startDateInvalid':
        return $gettext('Please enter a valid start date')
      case 'endDateInvalid':
        return $gettext('Please enter a valid end date')
      case 'dateRangeInvalid':
        return $gettext('End date must be after start date')
    }
  }

  /**
   * Submit form with navigation to results page
   * @returns Promise with success status
   */
  const submitForm = async (): Promise<boolean> => {
    if (!authStore.isAuthenticated) {
      feedback.showError($gettext('Please login to process transactions'))
      return false
    }

    const result = await formStore.prepareSubmit()

    if (!result.success || !result.resultId) {
      switch (result.errorCode) {
        case 'validationFailed':
          feedback.showError($gettext('Please fix the form errors before submitting'))
          break
        case 'noResultId':
          feedback.showError($gettext('Backend error: No result ID returned'))
          break
        case 'processingFailed':
          feedback.showError(`${$gettext('Error processing transactions')}: ${result.errorMessage ?? ''}`)
          break
        default:
          feedback.showError($gettext('Error processing transactions'))
      }
      return false
    }

    feedback.clearMessages()
    feedback.showSuccess($gettext('Transactions processed successfully'))

    // The new import added transactions; drop all cached datasets
    datasetStore.invalidateAll()

    await router.push({
      name: 'results',
      query: { resultId: result.resultId }
    })
    return true
  }

  return {
    formStore,
    formErrorMessage,
    submitForm,
  } as const
}
