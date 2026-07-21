<script setup lang="ts">
import { computed } from 'vue'
import { useGettext } from 'vue3-gettext'
import type { Account } from '../../types/api.js'

const { $gettext } = useGettext()

interface CardProps {
  title?: string
  classes?: string
  id?: string
  type?: 'standard' | 'simple' | 'account' | 'info'
  account?: Account
  width?: string
}

const props = withDefaults(defineProps<CardProps>(), {
  title: '',
  classes: '',
  id: undefined,
  type: 'standard',
  account: undefined,
  width: '100%'
})

const emit = defineEmits(['close'])

const cardClasses = computed(() => {
  const baseClasses = ['card']
  if (props.classes) baseClasses.push(props.classes)
  return baseClasses.join(' ')
})

const cardStyle = computed(() => {
  return props.width
    ? { width: props.width, margin: '0 auto' }
    : undefined
})

const showHeader = computed(() => {
  return props.type !== 'simple' && (props.title || props.type === 'account')
})

const formattedAccountId = computed(() => {
  if (props.account && props.account.formatted_id) {
    return props.account.formatted_id
  }
  return ''
})

const accountCurrency = computed(() => {
  return props.account && props.account.currency ? props.account.currency : ''
})

const closeAlert = () => {
  emit('close')
}

const infoCardClasses = computed(() => {
  return ['bg-status-info', 'text-on-light', 'alert-dismissible', 'fade', 'show']
})
</script>

<template>
  <div v-if="type === 'standard'" :id="id" :class="cardClasses" :style="cardStyle">
    <div v-if="showHeader" class="card-header">
      {{ title }}
    </div>
    <div class="card-body">
      <slot></slot>
    </div>
  </div>

  <div v-else-if="type === 'simple'" :id="id" :class="cardClasses">
    <div class="card-body">
      <slot></slot>
    </div>
  </div>

  <div v-else-if="type === 'account'" :class="cardClasses">
    <div class="card-header">
      {{ $gettext('Account') }}: {{ formattedAccountId }}
      <span v-if="accountCurrency" class="bg-surface-secondary text-on-dark px-2 py-1 rounded text-xs">{{ accountCurrency }}</span>
    </div>
    <div class="card-body">
      <slot></slot>
    </div>
  </div>

  <div v-else-if="type === 'info'" :class="infoCardClasses" role="alert">
    <strong>{{ title }}:</strong> <slot></slot>
    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close" @click="closeAlert"></button>
  </div>
</template>
