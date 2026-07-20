<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink, type RouteLocationRaw } from 'vue-router'

interface ButtonProps {
  text?: string
  to?: RouteLocationRaw
  type?: 'button' | 'submit' | 'reset'
  variant?: 'primary' | 'secondary' | 'outline-primary' | 'outline-secondary' | 'back'
  class?: string
  disabled?: boolean
  size?: 'sm' | 'lg'
}

const props = withDefaults(defineProps<ButtonProps>(), {
  text: '',
  to: undefined,
  type: 'button',
  variant: 'primary',
  class: '',
  disabled: false,
  size: undefined
})

const emit = defineEmits(['click'])

const buttonClasses = computed(() => {
  const classes = ['theme-btn']

  // Button variant - directly map typed variants to theme classes
  switch (props.variant) {
    case 'back':
      classes.push('theme-btn-secondary')
      break
    case 'primary':
      classes.push('theme-btn-primary')
      break
    case 'secondary':
      classes.push('theme-btn-secondary')
      break
    case 'outline-primary':
      classes.push('theme-btn-outline-primary')
      break
    case 'outline-secondary':
      classes.push('theme-btn-outline-secondary')
      break
  }

  // Size
  if (props.size) {
    classes.push(`theme-btn-${props.size}`)
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
    {{ text }}
  </RouterLink>

  <!-- Button Tag -->
  <button
    v-else
    :type="type"
    :class="buttonClasses"
    :disabled="disabled"
    @click="handleClick"
  >
    {{ text }}
  </button>
</template>