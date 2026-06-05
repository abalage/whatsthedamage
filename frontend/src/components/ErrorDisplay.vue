<script setup lang="ts">
import { useFeedbackStore } from '../stores/feedback.js'

const feedback = useFeedbackStore()

const getAlertClass = (type: string) => {
  return `alert alert-${type} alert-dismissible fade show`
}

const getIconClass = (type: string) => {
  const icons = {
    success: 'bi-check-circle',
    error: 'bi-exclamation-triangle',
    info: 'bi-info-circle',
    warning: 'bi-exclamation-triangle'
  }
  return icons[type as keyof typeof icons] || 'bi-info-circle'
}
</script>

<template>
  <div class="feedback-container">
    <div 
      v-for="message in feedback.messages" 
      :key="message.id" 
      :class="getAlertClass(message.type)" 
      role="alert"
    >
      <i :class="['bi', getIconClass(message.type), 'me-2']"></i>
      {{ message.message }}
      <button 
        type="button" 
        class="btn-close" 
        aria-label="Close" 
        @click="feedback.dismissMessage(message.id)"
      ></button>
    </div>
  </div>
</template>

<style scoped>
.feedback-container {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 1000;
  max-width: 400px;
  width: 100%;
}

.feedback-container .alert {
  margin-bottom: 10px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

@media (max-width: 768px) {
  .feedback-container {
    left: 20px;
    right: 20px;
    max-width: none;
  }
}
</style>