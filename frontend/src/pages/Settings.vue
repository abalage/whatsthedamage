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

const newUsername = ref('')
const isChangingUsername = ref(false)
const usernameError = ref<string | null>(null)
const usernameChanged = ref(false)

const currentPassword = ref('')
const newPassword = ref('')
const isChangingPassword = ref(false)
const passwordError = ref<string | null>(null)
const passwordChanged = ref(false)

const isExporting = ref(false)
const exportError = ref<string | null>(null)

const deletePassword = ref('')
const revokeSharedCorrections = ref(false)
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

async function handleChangeUsername(): Promise<void> {
  const trimmed = newUsername.value.trim()
  if (trimmed.length === 0 || trimmed === authStore.user?.username) {
    return
  }
  isChangingUsername.value = true
  usernameError.value = null
  usernameChanged.value = false
  try {
    await authStore.changeUsername(trimmed)
    newUsername.value = ''
    usernameChanged.value = true
  } catch (err: unknown) {
    usernameError.value = err instanceof Error ? err.message : String(err)
  } finally {
    isChangingUsername.value = false
  }
}

async function handleChangePassword(): Promise<void> {
  isChangingPassword.value = true
  passwordError.value = null
  passwordChanged.value = false
  try {
    await authStore.changeUserPassword(currentPassword.value, newPassword.value)
    currentPassword.value = ''
    newPassword.value = ''
    passwordChanged.value = true
  } catch (err: unknown) {
    passwordError.value = err instanceof Error ? err.message : String(err)
  } finally {
    isChangingPassword.value = false
  }
}

async function handleExport(): Promise<void> {
  isExporting.value = true
  exportError.value = null
  try {
    const data = await authStore.exportData()
    const blob = new Blob([JSON.stringify(data, null, 2)], {
      type: 'application/json'
    })
    const url = URL.createObjectURL(blob)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = 'whatsthedamage-export.json'
    document.body.appendChild(anchor)
    anchor.click()
    anchor.remove()
    URL.revokeObjectURL(url)
  } catch (err: unknown) {
    exportError.value = err instanceof Error ? err.message : String(err)
  } finally {
    isExporting.value = false
  }
}

async function handleDeleteAccount(): Promise<void> {
  isDeleting.value = true
  deleteError.value = null
  try {
    await authStore.requestAccountDeletion(
      deletePassword.value,
      revokeSharedCorrections.value
    )
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

    <h2>{{ $gettext('Your account') }}</h2>

    <form class="mb-3" @submit.prevent="handleChangeUsername">
      <div class="mb-3">
        <label class="form-label" for="newUsername">
          {{ $gettext('Username') }}
        </label>
        <input
          id="newUsername"
          v-model="newUsername"
          class="form-control"
          type="text"
          :placeholder="authStore.user?.username"
          autocomplete="username"
          :disabled="isChangingUsername"
          maxlength="255"
        >
      </div>
      <button
        type="submit"
        class="btn btn-secondary"
        :disabled="
          isChangingUsername
            || newUsername.trim().length === 0
            || newUsername.trim() === authStore.user?.username
        "
      >
        {{ $gettext('Change username') }}
      </button>
    </form>

    <div v-if="usernameChanged" class="alert alert-success" role="status">
      {{ $gettext('Your username has been updated.') }}
    </div>
    <div v-if="usernameError" class="alert alert-danger" role="alert">
      {{ $gettext('Failed to change the username:') }} {{ usernameError }}
    </div>

    <form class="mb-3" @submit.prevent="handleChangePassword">
      <div class="mb-3">
        <label class="form-label" for="currentPassword">
          {{ $gettext('Current password') }}
        </label>
        <input
          id="currentPassword"
          v-model="currentPassword"
          class="form-control"
          type="password"
          autocomplete="current-password"
          :disabled="isChangingPassword"
          required
        >
      </div>
      <div class="mb-3">
        <label class="form-label" for="newPassword">
          {{ $gettext('New password (minimum 12 characters)') }}
        </label>
        <input
          id="newPassword"
          v-model="newPassword"
          class="form-control"
          type="password"
          autocomplete="new-password"
          minlength="12"
          :disabled="isChangingPassword"
          required
        >
      </div>
      <button
        type="submit"
        class="btn btn-secondary"
        :disabled="
          isChangingPassword
            || currentPassword.length === 0
            || newPassword.length < 12
        "
      >
        {{ $gettext('Change password') }}
      </button>
    </form>

    <p>{{ $gettext('Changing your password logs out all other devices. You stay logged in on this device.') }}</p>

    <div v-if="passwordChanged" class="alert alert-success" role="status">
      {{ $gettext('Your password has been changed.') }}
    </div>
    <div v-if="passwordError" class="alert alert-danger" role="alert">
      {{ $gettext('Failed to change the password:') }} {{ passwordError }}
    </div>

    <h2 class="mt-5">{{ $gettext('Your data') }}</h2>

    <p>{{ $gettext('Download a copy of all personal data stored about you: your account details, processing results, transactions, and corrections, in a machine-readable JSON document.') }}</p>

    <button type="button" class="btn btn-secondary mb-3" :disabled="isExporting" @click="handleExport">
      {{ $gettext('Download my data') }}
    </button>

    <div v-if="exportError" class="alert alert-danger" role="alert">
      {{ $gettext('Failed to export your data:') }} {{ exportError }}
    </div>

    <h2 class="mt-5">{{ $gettext('Share corrections') }}</h2>

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
      {{ $gettext('Shared corrections are anonymized and retained even if you turn sharing off or delete your account. You can ask for their removal when you request account deletion.') }}
    </div>

    <div v-if="justEnabled" class="alert alert-success" role="status">
      {{ $gettext('Sharing is enabled. Your future corrections will be contributed.') }}
    </div>
    <div v-if="justDisabled" class="alert alert-success" role="status">
      {{ $gettext('Sharing is disabled. This takes effect immediately for future corrections. Previously shared corrections remain anonymized; you can ask for their removal when you request account deletion.') }}
    </div>
    <div v-if="updateError" class="alert alert-danger" role="alert">
      {{ $gettext('Failed to update the sharing preference:') }} {{ updateError }}
    </div>

    <h2 class="mt-5">{{ $gettext('Delete account') }}</h2>

    <p>{{ $gettext('Scheduling deletion logs you out everywhere. Your account and all of your transactions and corrections are deleted after a 7-day grace period.') }}</p>
    <p>{{ $gettext('If you log in again before the grace period ends, the deletion is canceled and nothing is lost.') }}</p>

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
      <div class="form-check mb-3">
        <input
          id="revokeSharedCorrections"
          v-model="revokeSharedCorrections"
          class="form-check-input"
          type="checkbox"
          :disabled="isDeleting"
        >
        <label class="form-check-label" for="revokeSharedCorrections">
          {{ $gettext('Also remove the anonymized corrections I shared') }}
        </label>
      </div>
      <button
        type="submit"
        class="btn btn-danger"
        :disabled="isDeleting || deletePassword.length === 0"
      >
        {{ $gettext('Schedule my account for deletion') }}
      </button>
    </form>

    <div v-if="revokeSharedCorrections" class="alert alert-warning" role="alert">
      {{ $gettext('Machine learning models already trained on your shared corrections cannot be changed. New models reflect the absence of withdrawn data once they are made available and older models are deprecated.') }}
    </div>

    <div v-if="deleteError" class="alert alert-danger" role="alert">
      {{ $gettext('Failed to schedule the account deletion:') }} {{ deleteError }}
    </div>
  </div>
</template>
