<script setup lang="ts">
defineProps<{
  message: string
}>()
</script>

<template>
  <div class="theme-alert theme-alert-danger">
    {{ message }}
  </div>
</template>
