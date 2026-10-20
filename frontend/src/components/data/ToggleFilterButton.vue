<script setup lang="ts">
/**
 * ToggleFilterButton - Toolbar toggle button for the data table's
 * filter actions slot. Renders the active state with aria-pressed.
 */

interface Props {
  /** Button label */
  label: string
  /** Tooltip explaining what the toggle controls */
  title?: string
  /** Whether the toggle is active */
  modelValue: boolean
}

defineProps<Props>()
defineEmits<{ 'update:modelValue': [value: boolean] }>()
</script>

<template>
  <button
    type="button"
    class="btn px-2 py-1 text-sm rounded-sm"
    :class="modelValue
      ? 'bg-surface-secondary text-on-dark border-secondary'
      : 'bg-surface-base text-secondary border-secondary hover-bg-surface-secondary'"
    :aria-pressed="modelValue"
    :title="title"
    @click="$emit('update:modelValue', !modelValue)"
  >
    {{ label }}
  </button>
</template>
