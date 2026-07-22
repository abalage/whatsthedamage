<script setup lang="ts">
withDefaults(defineProps<{
  title: string
}>(), {})
</script>

<template>
  <div class="d-flex justify-content-between align-items-center mb-3">
    <h1 class="mb-0">{{ title }}</h1>
    <slot name="actions" />
  </div>
</template>
