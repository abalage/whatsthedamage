<script setup lang="ts">
import { computed } from 'vue'
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

// Expose current locale to force reactive updates
const currentLocale = computed(() => localeStore.locale)
</script>

<template>
  <Layout :key="currentLocale">
    <RouterView />
  </Layout>
</template>
