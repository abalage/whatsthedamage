<script setup lang="ts">
import ButtonComponent from '../ui/ButtonComponent.vue'
import type { NavButton } from '../../composables/useDrilldownData.js'

withDefaults(defineProps<{
  title: string
  buttons?: NavButton[]
}>(), {
  buttons: () => []
})
</script>

<template>
  <div class="d-flex justify-content-between align-items-center mb-3">
    <h1 class="mb-0">{{ title }}</h1>
    <div v-if="buttons.length" class="d-flex gap-2">
      <ButtonComponent
        v-for="(button, index) in buttons"
        :key="index"
        v-bind="button"
        class="mt-3 mb-3"
      />
    </div>
  </div>
</template>
