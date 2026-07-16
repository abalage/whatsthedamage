<script setup lang="ts">
defineProps<{
  message: string
}>()
</script>

<template>
  <div class="alert alert-danger">
    {{ message }}
  </div>
</template>
