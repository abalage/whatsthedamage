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
  <!-- Deliberate workaround: :key remounts Layout on language switch.
       vue3-gettext 4.0.0-beta.1 ships a self-contained bundle with its
       own inlined Vue reactivity, so changing gettext.current does not
       re-render components that used $gettext - the gettext object's
       reactive reads are invisible to the app's render effects. Until
       the library shares the app's reactivity, remounting Layout is
       the only way to update all visible text. Pages must not capture
       translated strings outside render/computed evaluation, so this
       remount stays the single locale-switch mechanism. -->
  <Layout :key="currentLocale">
    <RouterView />
  </Layout>
</template>
