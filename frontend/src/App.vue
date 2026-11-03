<script setup lang="ts">
import { computed } from 'vue'
import { RouterView, useRoute } from 'vue-router'
import Layout from './components/Layout.vue'
import { useLocaleStore } from './stores/locale'

const route = useRoute()

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

// Auth pages render without the app chrome (navbar/footer) so that
// .auth-layout's min-height: 100vh fills exactly the viewport (#135)
const isBareRoute = computed(() => route.meta.bare === true)
</script>

<template>
  <!-- Deliberate workaround: :key remounts the page tree on language switch.
       vue3-gettext 4.0.0-beta.1 ships a self-contained bundle with its
       own inlined Vue reactivity, so changing gettext.current does not
       re-render components that used $gettext - the gettext object's
       reactive reads are invisible to the app's render effects. Until
       the library shares the app's reactivity, remounting is
       the only way to update all visible text. Pages must not capture
       translated strings outside render/computed evaluation, so this
       remount stays the single locale-switch mechanism. -->
  <Layout v-if="!isBareRoute" :key="currentLocale">
    <RouterView />
  </Layout>
  <RouterView v-else :key="currentLocale" />
</template>
