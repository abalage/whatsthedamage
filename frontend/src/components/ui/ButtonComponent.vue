<script setup lang="ts">
import { computed } from 'vue'
import { RouterLink, type RouteLocationRaw } from 'vue-router'

interface ButtonProps {
  text: string
  url?: string
  to?: RouteLocationRaw
  icon?: string
  type?: 'button' | 'submit' | 'reset'
  buttonType?: 'primary' | 'secondary' | 'outline-primary' | 'outline-secondary' | 'back'
  classes?: string
  id?: string
  disabled?: boolean
  size?: 'sm' | 'lg'
}

const props = withDefaults(defineProps<ButtonProps>(), {
  text: '',
  url: undefined,
  to: undefined,
  icon: undefined,
  type: 'button',
  buttonType: 'primary',
  classes: '',
  id: undefined,
  disabled: false,
  size: undefined
})

const emit = defineEmits(['click'])

const buttonClasses = computed(() => {
  const classes = []
  
  // Base button class
  classes.push('btn')
  
  // Button type
  if (props.buttonType === 'back') {
    classes.push('btn-secondary')
  } else if (props.buttonType.startsWith('outline-')) {
    classes.push(`btn-${props.buttonType}`)
  } else {
    classes.push(`btn-${props.buttonType}`)
  }
  
  // Size
  if (props.size) {
    classes.push(`btn-${props.size}`)
  }
  
  // Additional classes
  if (props.classes) {
    classes.push(props.classes)
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

const isAnchor = computed(() => {
  return props.url !== undefined && props.to === undefined
})
</script>

<template>
  <!-- Router Link -->
  <RouterLink
    v-if="isRouterLink"
    :id="id"
    :to="to!"
    :class="buttonClasses"
    @click="handleClick"
  >
    <i v-if="icon" :class="icon" class="me-2"></i>
    {{ text }}
  </RouterLink>

  <!-- Anchor Tag -->
  <a
    v-else-if="isAnchor"
    :id="id"
    :href="url"
    :class="buttonClasses"
    @click="handleClick"
  >
    <i v-if="icon" :class="icon" class="me-2"></i>
    {{ text }}
  </a>

  <!-- Button Tag -->
  <button
    v-else
    :id="id"
    :type="type"
    :class="buttonClasses"
    :disabled="disabled"
    @click="handleClick"
  >
    <i v-if="icon" :class="icon" class="me-2"></i>
    {{ text }}
  </button>
</template>

<style scoped>
/* Button-specific styles can be added here */
</style>