<script setup lang="ts">
import { RouterView } from 'vue-router'
import Layout from './components/Layout.vue'
import { useLocaleStore } from './stores/locale'
import { loadTranslations } from './stores/translations'

// Initialize locale store
const localeStore = useLocaleStore()

// Load translations on app initialization
loadTranslations()

// Set default locale (could be detected from browser or URL)
localeStore.setLocale('en')
</script>

<template>
  <Layout>
    <RouterView />
  </Layout>
</template>

<style>
body {
  margin: 0;
  padding: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}
</style>