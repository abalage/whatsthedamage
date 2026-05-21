<script setup lang="ts">
import { RouterView } from 'vue-router'
import Layout from './components/Layout.vue'
import { useLocaleStore } from './stores/locale'

// Initialize locale store
const localeStore = useLocaleStore()

// Load locale from localStorage
localeStore.loadLocale()

// Set default locale if not loaded (could be detected from browser or URL)
if (!localeStore.locale) {
  localeStore.setLocale('en')
}
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