<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink, type RouteLocationRaw } from 'vue-router'

interface ButtonProps {
  text?: string
  to?: RouteLocationRaw
  type?: 'button' | 'submit' | 'reset'
  variant?: 'primary' | 'secondary' | 'outline-primary' | 'outline-secondary' | 'back' | 'success' | 'danger'
  class?: string
  disabled?: boolean
  size?: 'sm' | 'lg'
  icon?: string
}

const props = withDefaults(defineProps<ButtonProps>(), {
  text: '',
  to: undefined,
  type: 'button',
  variant: 'primary',
  class: '',
  disabled: false,
  size: undefined,
  icon: undefined
})

const emit = defineEmits(['click'])

const buttonClasses = computed(() => {
  const classes = ['btn']

  // Button variant - map to semantic utility classes
  switch (props.variant) {
    case 'back':
      classes.push('bg-surface-secondary', 'text-on-dark', 'border-secondary')
      break
    case 'primary':
      classes.push('bg-surface-primary', 'text-on-primary', 'border-primary')
      break
    case 'secondary':
      classes.push('bg-surface-secondary', 'text-on-dark', 'border-secondary')
      break
    case 'outline-primary':
      classes.push('bg-surface-base', 'text-primary', 'border-primary', 'hover-bg-surface-primary-10')
      break
    case 'outline-secondary':
      classes.push('bg-surface-base', 'text-secondary', 'border-secondary', 'hover-bg-surface-secondary')
      break
    case 'success':
      classes.push('bg-surface-base', 'text-success', 'border-success', 'hover-bg-status-success-15')
      break
    case 'danger':
      classes.push('bg-surface-base', 'text-danger', 'border-danger', 'hover-bg-status-danger-15')
      break
  }

  // Size
  if (props.size === 'sm') {
    classes.push('px-2', 'py-1', 'text-sm', 'rounded-sm')
  } else if (props.size === 'lg') {
    classes.push('px-4', 'py-2', 'text-lg', 'rounded-lg')
  }

  // Additional classes
  if (props.class) {
    classes.push(props.class)
  }

  return classes.join(' ')
})

const handleClick = (event: MouseEvent) => {
  if (props.disabled) {
    event.preventDefault()
    event.stopPropagation()
    return
  }
  emit('click', event)
}

const isRouterLink = computed(() => {
  return props.to !== undefined
})
</script>

<template>
  <!-- Router Link -->
  <RouterLink
    v-if="isRouterLink"
    :to="to!"
    :class="buttonClasses"
    @click="handleClick"
  >
    <slot>
      <i v-if="icon" :class="icon" class="me-1"></i>
      {{ text }}
    </slot>
  </RouterLink>

  <!-- Button Tag -->
  <button
    v-else
    :type="type"
    :class="buttonClasses"
    :disabled="disabled"
    @click="handleClick"
  >
    <slot>
      <i v-if="icon" :class="icon" class="me-1"></i>
      {{ text }}
    </slot>
  </button>
</template>
