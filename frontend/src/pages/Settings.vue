<script setup lang="ts">
import { ref } from 'vue'
import { useGettext } from 'vue3-gettext'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'

const { $gettext } = useGettext()
const router = useRouter()
const authStore = useAuthStore()

const isUpdating = ref(false)
const updateError = ref<string | null>(null)
const justEnabled = ref(false)
const justDisabled = ref(false)

const deletePassword = ref('')
const isDeleting = ref(false)
const deleteError = ref<string | null>(null)

async function handleToggle(event: Event): Promise<void> {
  const target = event.target as HTMLInputElement
  const newValue = target.checked
  isUpdating.value = true
  updateError.value = null
  justEnabled.value = false
  justDisabled.value = false
  try {
    await authStore.setOptInSharing(newValue)
    justEnabled.value = newValue
    justDisabled.value = !newValue
  } catch (err: unknown) {
    updateError.value = err instanceof Error ? err.message : String(err)
    target.checked = !newValue
  } finally {
    isUpdating.value = false
  }
}

async function handleDeleteAccount(): Promise<void> {
  isDeleting.value = true
  deleteError.value = null
  try {
    await authStore.requestAccountDeletion(deletePassword.value)
    deletePassword.value = ''
    await router.push({ name: 'login' })
  } catch (err: unknown) {
    deleteError.value = err instanceof Error ? err.message : String(err)
  } finally {
    isDeleting.value = false
  }
}
</script>

<template>
  <div class="container">
    <h1>{{ $gettext('Settings') }}</h1>

    <h2>{{ $gettext('Share corrections') }}</h2>

    <div class="form-check form-switch mb-3">
      <input
        id="optInSharingSwitch"
        class="form-check-input"
        type="checkbox"
        role="switch"
        :checked="authStore.user?.opt_in_sharing ?? false"
        :disabled="isUpdating"
        @change="handleToggle"
      >
      <label class="form-check-label" for="optInSharingSwitch">
        {{ $gettext('Contribute my corrections to improve future categorization') }}
      </label>
    </div>

    <p>{{ $gettext('When enabled, the merchant names and categories of your corrections are shared anonymously to help improve future categorization for everyone.') }}</p>
    <p>{{ $gettext('Shared corrections contain no amounts, dates, or user information. You can change this setting at any time.') }}</p>

    <div class="alert alert-warning" role="alert">
      {{ $gettext('Shared corrections are retained permanently and remain anonymized even if your account is deleted. They cannot be retracted.') }}
    </div>

    <div v-if="justEnabled" class="alert alert-success" role="status">
      {{ $gettext('Sharing is enabled. Your future corrections will be contributed.') }}
    </div>
    <div v-if="justDisabled" class="alert alert-success" role="status">
      {{ $gettext('Sharing is disabled. This takes effect immediately for future corrections. Previously shared corrections are retained permanently and cannot be retracted.') }}
    </div>
    <div v-if="updateError" class="alert alert-danger" role="alert">
      {{ $gettext('Failed to update the sharing preference:') }} {{ updateError }}
    </div>

    <h2 class="mt-5">{{ $gettext('Delete account') }}</h2>

    <p>{{ $gettext('Scheduling deletion logs you out everywhere. Your account and all of your transactions and corrections are deleted after a 7-day grace period.') }}</p>
    <p>{{ $gettext('If you log in again before the grace period ends, the deletion is canceled and nothing is lost.') }}</p>

    <div class="alert alert-warning" role="alert">
      {{ $gettext('Anonymized corrections you shared before deletion are retained permanently and cannot be retracted.') }}
    </div>

    <form class="mb-3" @submit.prevent="handleDeleteAccount">
      <div class="mb-3">
        <label class="form-label" for="deleteAccountPassword">
          {{ $gettext('Confirm with your password') }}
        </label>
        <input
          id="deleteAccountPassword"
          v-model="deletePassword"
          class="form-control"
          type="password"
          autocomplete="current-password"
          :disabled="isDeleting"
          required
        >
      </div>
      <button
        type="submit"
        class="btn btn-danger"
        :disabled="isDeleting || deletePassword.length === 0"
      >
        {{ $gettext('Schedule my account for deletion') }}
      </button>
    </form>

    <div v-if="deleteError" class="alert alert-danger" role="alert">
      {{ $gettext('Failed to schedule the account deletion:') }} {{ deleteError }}
    </div>
  </div>
</template>
