<!--
  Logout Page Component

  Performs logout on mount and redirects to the login page.
  Registered as a route without a visible layout.
-->

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useGettext } from 'vue3-gettext'
import { useAuthStore } from '../stores/auth'

const { $gettext } = useGettext()
const router = useRouter()
const authStore = useAuthStore()

onMounted(async () => {
  try {
    await authStore.logout()
  } finally {
    await router.push({ name: 'login', query: { loggedOut: 'true' } })
  }
})
</script>

<template>
  <div class="d-flex justify-content-center align-items-center vh-100">
    <div class="spinner-border text-primary" role="status">
      <span class="visually-hidden">{{ $gettext('Logging out...') }}</span>
    </div>
  </div>
</template>
