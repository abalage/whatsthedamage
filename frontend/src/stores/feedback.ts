import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

interface FeedbackMessage {
  id: number
  type: 'success' | 'error' | 'info' | 'warning'
  message: string
  timestamp: number
  autoDismiss?: boolean
}

export const useFeedbackStore = defineStore('feedback', () => {
  const messages = ref<FeedbackMessage[]>([])
  const nextId = ref(1) // eslint-disable-line no-magic-numbers

  const AUTO_DISMISS_TIMEOUT = 5000 // ms

  const showMessage = (message: string, type: FeedbackMessage['type'] = 'info', autoDismiss: boolean = true): void => {
    const id = nextId.value++
    const timestamp = Date.now()
    
    messages.value.push({
      id,
      type,
      message,
      timestamp,
      autoDismiss
    })
    
    // Auto-dismiss after 5 seconds if enabled
    if (autoDismiss) {
      setTimeout(() => {
        dismissMessage(id)
      }, AUTO_DISMISS_TIMEOUT)
    }
  }

  const showSuccess = (message: string, autoDismiss: boolean = true): void => {
    showMessage(message, 'success', autoDismiss)
  }

  const showError = (message: string, autoDismiss: boolean = true): void => {
    showMessage(message, 'error', autoDismiss)
  }

  const showInfo = (message: string, autoDismiss: boolean = true): void => {
    showMessage(message, 'info', autoDismiss)
  }

  const showWarning = (message: string, autoDismiss: boolean = true): void => {
    showMessage(message, 'warning', autoDismiss)
  }

  const dismissMessage = (id: number): void => {
    messages.value = messages.value.filter(msg => msg.id !== id)
  }

  const dismissAll = (): void => {
    messages.value = []
  }

  const clearMessages = (): void => {
    messages.value = []
    nextId.value = 1
  }

  const hasMessages = computed((): boolean => {
    return messages.value.length > 0 // eslint-disable-line no-magic-numbers
  })

  const hasErrors = computed((): boolean => {
    return messages.value.some(msg => msg.type === 'error')
  })

  const getMessagesByType = (type: FeedbackMessage['type']): FeedbackMessage[] => {
    return messages.value.filter(msg => msg.type === type)
  }

  return {
    messages,
    nextId,
    hasMessages,
    hasErrors,
    showMessage,
    showSuccess,
    showError,
    showInfo,
    showWarning,
    dismissMessage,
    dismissAll,
    clearMessages,
    getMessagesByType
  }
})