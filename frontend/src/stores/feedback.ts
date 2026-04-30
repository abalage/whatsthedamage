import { ref, computed } from 'vue'

interface FeedbackMessage {
  id: number
  type: 'success' | 'error' | 'info' | 'warning'
  message: string
  timestamp: number
  autoDismiss?: boolean
}

export const useFeedbackStore = () => {
  const messages = ref<FeedbackMessage[]>([])
  const nextId = ref(1)

  const showMessage = (message: string, type: FeedbackMessage['type'] = 'info', autoDismiss: boolean = true) => {
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
      }, 5000)
    }
  }

  const showSuccess = (message: string, autoDismiss: boolean = true) => {
    showMessage(message, 'success', autoDismiss)
  }

  const showError = (message: string, autoDismiss: boolean = true) => {
    showMessage(message, 'error', autoDismiss)
  }

  const showInfo = (message: string, autoDismiss: boolean = true) => {
    showMessage(message, 'info', autoDismiss)
  }

  const showWarning = (message: string, autoDismiss: boolean = true) => {
    showMessage(message, 'warning', autoDismiss)
  }

  const dismissMessage = (id: number) => {
    messages.value = messages.value.filter(msg => msg.id !== id)
  }

  const dismissAll = () => {
    messages.value = []
  }

  const clearMessages = () => {
    messages.value = []
    nextId.value = 1
  }

  const hasMessages = computed(() => {
    return messages.value.length > 0
  })

  const hasErrors = computed(() => {
    return messages.value.some(msg => msg.type === 'error')
  })

  const getMessagesByType = (type: FeedbackMessage['type']) => {
    return messages.value.filter(msg => msg.type === type)
  }

  return {
    messages,
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
}

export type FeedbackStore = ReturnType<typeof useFeedbackStore>