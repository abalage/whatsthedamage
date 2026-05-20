<script setup lang="ts">
import { useLocaleStore } from '../stores/locale'
import { getTranslation } from '../stores/translations'

const localeStore = useLocaleStore()

const t = (key: string) => getTranslation(key, localeStore.locale)
</script>

<template>
  <div class="container">
    <h1>{{ t('appTitle') }} - Statistical Analysis</h1>
    <p>This page will display statistical analysis of your transactions.</p>
    <div class="alert alert-info">
      Statistical analysis will be shown here after processing your data.
    </div>
  </div>
</template>

<style scoped>
/* Add component-specific styles here */
</style>