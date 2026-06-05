<script setup lang="ts">
import { computed } from 'vue'
import { useGettext } from 'vue3-gettext'
import type { AccountData } from '../../types/api.js'

const { $gettext } = useGettext()

interface CardProps {
  title?: string
  classes?: string
  id?: string
  type?: 'standard' | 'simple' | 'account' | 'info'
  account?: AccountData
}

const props = withDefaults(defineProps<CardProps>(), {
  title: '',
  classes: '',
  id: undefined,
  type: 'standard',
  account: undefined
})

const emit = defineEmits(['close'])

const cardClasses = computed(() => {
  const baseClasses = ['card']
  if (props.classes) baseClasses.push(props.classes)
  return baseClasses.join(' ')
})

const headerClasses = computed(() => {
  if (props.type === 'account') {
    return 'account-header bg-light p-3 rounded'
  }
  return 'card-header bg-success text-white'
})

const bodyClasses = computed(() => {
  if (props.type === 'account') {
    return 'account-content mt-3'
  }
  return 'card-body bg-light'
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
</script>

<template>
  <!-- Standard Card -->
  <div v-if="type === 'standard'" :id="id" :class="cardClasses">
    <div v-if="showHeader" :class="headerClasses">
      {{ title }}
    </div>
    <div :class="bodyClasses">
      <slot></slot>
    </div>
  </div>

  <!-- Simple Card (no header) -->
  <div v-else-if="type === 'simple'" :id="id" :class="cardClasses">
    <div class="card-body">
      <slot></slot>
    </div>
  </div>

  <!-- Account Card -->
  <div v-else-if="type === 'account'" class="account-section mb-4">
    <div :class="headerClasses">
      <h2 class="mb-0">
        {{ $gettext('account') }}: {{ formattedAccountId }}
        <span v-if="accountCurrency" class="badge bg-info">({{ accountCurrency }})</span>
      </h2>
    </div>
    <div :class="bodyClasses">
      <slot></slot>
    </div>
  </div>

  <!-- Info Card (Alert-style) -->
  <div v-else-if="type === 'info'" :class="`alert alert-${classes || 'info'} alert-dismissible fade show`" role="alert">
    <strong>{{ title }}:</strong> <slot></slot>
    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close" @click="closeAlert"></button>
  </div>
</template>
