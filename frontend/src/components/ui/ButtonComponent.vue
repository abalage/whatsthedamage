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
  const classes = []

  // Base button class
  classes.push('btn')

  // Button variant
  if (props.variant === 'back') {
    classes.push('btn-secondary')
  } else {
    classes.push(`btn-${props.variant}`)
  }

  // Size
  if (props.size) {
    classes.push(`btn-${props.size}`)
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

<style scoped>
/* Button-specific styles can be added here */
</style>