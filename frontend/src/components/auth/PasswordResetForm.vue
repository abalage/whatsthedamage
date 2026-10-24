<!--
  Password Reset Form Component

  Form for resetting password using recovery code.
  Handles form state, validation, and submission.
-->

<script setup lang="ts">
import { ref, computed } from 'vue';
import { useGettext } from 'vue3-gettext';
import { getPasswordMinLength } from '../../config/auth-config';

const { $gettext } = useGettext();

// Props
interface Props {
  isLoading: boolean;
  error: string | null;
}

const props = defineProps<Props>();

// Emits
interface Emits {
  (e: 'submit', username: string, recoveryCode: string, newPassword: string): void;
  (e: 'clear-error'): void;
}

const emit = defineEmits<Emits>();

// Form state
const username = ref('');
const recoveryCode = ref('');
const newPassword = ref('');
const confirmPassword = ref('');

// Computed properties
const minPasswordLength = getPasswordMinLength();
const passwordsMatch = computed(() => newPassword.value === confirmPassword.value);
const isFormValid = computed(() => (
  username.value.trim() &&
  recoveryCode.value.trim() &&
  newPassword.value &&
  confirmPassword.value &&
  passwordsMatch.value &&
  newPassword.value.length >= minPasswordLength
));

const passwordStrength = computed(() => {
  const length = newPassword.value.length;
  if (length === 0) return 'empty';
  if (length < 8) return 'weak';
  if (length < minPasswordLength) return 'medium';
  return 'strong';
});

/**
 * Handle form submission.
 */
function handleSubmit() {
  if (!isFormValid.value) {
    return;
  }
  emit('submit', username.value.trim(), recoveryCode.value.trim(), newPassword.value);
}

/**
 * Clear error and reset form focus.
 */
function handleClearError() {
  emit('clear-error');
}
</script>

<template>
  <form class="auth-form" @submit.prevent="handleSubmit">
    <!-- Error message display -->
    <div v-if="props.error" class="auth-error">
      <p>{{ props.error }}</p>
      <button
        type="button"
        class="auth-error-close"
        :aria-label="$gettext('Clear error')"
        @click="handleClearError"
      >
        &times;
      </button>
    </div>

    <!-- Username field -->
    <div class="form-group">
      <label for="username">{{ $gettext('Username') }}</label>
      <input
        id="username"
        v-model="username"
        type="text"
        class="form-control"
        required
        :placeholder="$gettext('Enter your username')"
        autocomplete="username"
        @focus="handleClearError"
      />
    </div>

    <!-- Recovery Code field -->
    <div class="form-group">
      <label for="recoveryCode">{{ $gettext('Recovery Code') }}</label>
      <input
        id="recoveryCode"
        v-model="recoveryCode"
        type="text"
        class="form-control"
        required
        :placeholder="$gettext('e.g., ABCD-EFGH-IJKL-MNOP')"
        autocomplete="off"
        @focus="handleClearError"
      />
      <p class="auth-hint">
        {{ $gettext('Enter the recovery code you saved (with or without hyphens)') }}
      </p>
    </div>

    <!-- New Password field -->
    <div class="form-group">
      <label for="newPassword">{{ $gettext('New Password') }}</label>
      <input
        id="newPassword"
        v-model="newPassword"
        type="password"
        class="form-control"
        required
        :placeholder="$gettext('Enter new password')"
        autocomplete="new-password"
        @focus="handleClearError"
      />
      <div class="password-strength" :class="passwordStrength">
        <span v-if="newPassword.length > 0">
          {{ newPassword.length }}/{{ minPasswordLength }} {{ $gettext('characters') }}
        </span>
      </div>
    </div>

    <!-- Confirm Password field -->
    <div class="form-group">
      <label for="confirmPassword">{{ $gettext('Confirm New Password') }}</label>
      <input
        id="confirmPassword"
        v-model="confirmPassword"
        type="password"
        class="form-control"
        required
        :placeholder="$gettext('Confirm new password')"
        autocomplete="new-password"
        @focus="handleClearError"
      />
      <div v-if="confirmPassword.length > 0" class="auth-hint">
        <span v-if="passwordsMatch" class="auth-valid">{{ $gettext('Passwords match') }}</span>
        <span v-else class="auth-invalid">{{ $gettext('Passwords do not match') }}</span>
      </div>
    </div>

    <!-- Submit button -->
    <button
      type="submit"
      class="auth-primary-btn"
      :disabled="!isFormValid || props.isLoading"
    >
      <span v-if="!props.isLoading">{{ $gettext('Reset Password') }}</span>
      <span v-else>{{ $gettext('Resetting...') }}</span>
    </button>

    <!-- Requirements notice -->
    <div class="auth-hint">
      <p>
        <strong>{{ $gettext('Note:') }}</strong>
        {{ $gettext('Password must be at least {minLength} characters long.').replace('{minLength}', String(minPasswordLength)) }}
      </p>
    </div>
  </form>
</template>

<style scoped>
.form-group input[type="text"],
.form-group input[type="password"] {
  font-family: monospace;
}

.password-strength {
  font-size: 0.75rem;
  height: 1rem;
  display: flex;
  align-items: center;
}

.password-strength.empty {
  color: var(--color-text-secondary);
}

.password-strength.weak {
  color: var(--color-status-danger);
}

.password-strength.medium {
  color: var(--color-status-warning);
}

.password-strength.strong {
  color: var(--color-status-success);
}
</style>
