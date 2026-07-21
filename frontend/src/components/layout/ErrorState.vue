<script setup lang="ts">
defineProps<{
  message: string
}>()
</script>

<template>
  <div class="bg-status-danger text-on-light alert">
    {{ message }}
  </div>
</template>
