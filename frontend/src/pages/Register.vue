<!--
  Register Page Component

  Provides user registration with form validation,
  password strength checking, and recovery code display.
-->

<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useGettext } from 'vue3-gettext';
import { useAuthStore } from '../stores/auth';
import AuthLayout from '../components/AuthLayout.vue';
import { getPasswordMinLength } from '../config/auth-config';

const { $gettext } = useGettext();
const router = useRouter();
const authStore = useAuthStore();

const minPasswordLength = getPasswordMinLength();

// Form state
const username = ref('');
const password = ref('');
const confirmPassword = ref('');
const termsAccepted = ref(false);
const isSubmitting = ref(false);
const showRecoveryCode = ref(false);
const recoveryCodeAcknowledged = ref(false);

// Computed properties
const passwordsMatch = () => password.value === confirmPassword.value;
const passwordValid = () => password.value.length >= minPasswordLength;
const formValid = () => (
  username.value.trim().length > 0 &&
  passwordValid() &&
  passwordsMatch() &&
  termsAccepted.value
);

/**
 * Handle form submission for registration.
 */
async function handleRegister() {
  if (!formValid()) {
    if (!passwordsMatch()) {
      authStore.error = $gettext('Passwords do not match');
    } else if (!passwordValid()) {
      authStore.error = $gettext('Password must be at least {minLength} characters').replace('{minLength}', String(minPasswordLength));
    } else if (!termsAccepted.value) {
      authStore.error = $gettext('Please accept the Terms and the Privacy Policy to continue');
    } else {
      authStore.error = $gettext('Please fill in all fields');
    }
    return;
  }

  isSubmitting.value = true;
  authStore.clearError();

  try {
    await authStore.register(username.value.trim(), password.value);

    // Show recovery code
    showRecoveryCode.value = true;
    recoveryCodeAcknowledged.value = false;
  } catch {
    // Error is already set in the store
  } finally {
    isSubmitting.value = false;
  }
}

/**
 * Acknowledge recovery code and proceed to login.
 */
function handleAcknowledgeAndProceed() {
  recoveryCodeAcknowledged.value = true;
  authStore.acknowledgeRecoveryCode();

  // Redirect to login
  router.push({ name: 'login', query: { registered: 'true' } });
}

/**
 * Copy recovery code to clipboard.
 */
async function copyRecoveryCode() {
  try {
    if (authStore.recoveryCode) {
      await navigator.clipboard.writeText(authStore.recoveryCode);
    }
  } catch {
    // Clipboard write failed; the user can still read and copy the code manually
  }
}
</script>

<template>
  <AuthLayout>
    <!-- Registration form -->
    <template v-if="!showRecoveryCode">
      <h2>{{ $gettext('Create Account') }}</h2>

      <form class="auth-form" @submit.prevent="handleRegister">
        <!-- Error message display -->
        <div v-if="authStore.error" class="auth-error">
          <p>{{ authStore.error }}</p>
          <button
            type="button"
            class="auth-error-close"
            :aria-label="$gettext('Clear error')"
            @click="authStore.clearError"
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
            :placeholder="$gettext('Choose a username')"
            autocomplete="username"
            @focus="authStore.clearError"
          />
        </div>

        <!-- Password field -->
        <div class="form-group">
          <label for="password">{{ $gettext('Password (minimum {minLength} characters)').replace('{minLength}', String(minPasswordLength)) }}</label>
          <input
            id="password"
            v-model="password"
            type="password"
            class="form-control"
            required
            :minlength="minPasswordLength"
            :placeholder="$gettext('Create a password')"
            autocomplete="new-password"
            @focus="authStore.clearError"
          />
          <div class="auth-hint">
            <span :class="password.length >= minPasswordLength ? 'auth-valid' : 'auth-invalid'">
              {{ password.length }}/{{ minPasswordLength }} {{ $gettext('characters') }}
            </span>
          </div>
        </div>

        <!-- Confirm password field -->
        <div class="form-group">
          <label for="confirmPassword">{{ $gettext('Confirm Password') }}</label>
          <input
            id="confirmPassword"
            v-model="confirmPassword"
            type="password"
            class="form-control"
            required
            :placeholder="$gettext('Confirm your password')"
            autocomplete="new-password"
            @focus="authStore.clearError"
          />
          <div class="auth-hint">
            <span :class="passwordsMatch() ? 'auth-valid' : 'auth-invalid'">
              {{ passwordsMatch() ? $gettext('Passwords match') : $gettext('Passwords do not match') }}
            </span>
          </div>
        </div>

        <!-- Terms and privacy policy acceptance -->
        <div class="auth-checkbox">
          <label>
            <input
              v-model="termsAccepted"
              type="checkbox"
              required
            />
            {{ $gettext('I have read and accept the') }}
            <router-link to="/legal">{{ $gettext('Terms (Legal Notice)') }}</router-link>
            {{ $gettext('and the') }}
            <router-link to="/privacy">{{ $gettext('Privacy Policy') }}</router-link>
          </label>
        </div>

        <!-- Submit button -->
        <button
          type="submit"
          class="auth-primary-btn"
          :disabled="isSubmitting || !formValid()"
        >
          <span v-if="!isSubmitting">{{ $gettext('Create Account') }}</span>
          <span v-else>{{ $gettext('Creating...') }}</span>
        </button>
      </form>

      <!-- Links -->
      <div class="auth-links">
        <p>
          {{ $gettext('Already have an account?') }}
          <router-link to="/login" @click="authStore.clearError">{{ $gettext('Login') }}</router-link>
        </p>
      </div>
    </template>

    <!-- Recovery code display -->
    <template v-else>
      <div class="recovery-code-container">
        <h2>{{ $gettext('Save Your Recovery Code') }}</h2>

        <p class="auth-instructions">
          {{ $gettext('This code is displayed only once. Save it securely to reset your password if you forget it. You will not be able to retrieve it later.') }}
        </p>

        <div class="recovery-code-box">
          <code>{{ authStore.recoveryCode }}</code>
          <button
            class="recovery-copy-btn"
            type="button"
            :title="$gettext('Copy to clipboard')"
            @click="copyRecoveryCode"
          >
            {{ $gettext('Copy') }}
          </button>
        </div>

        <div class="auth-status-warning">
          <p>
            <strong>{{ $gettext('Important:') }}</strong>
            {{ $gettext('Store this code in a safe place. Without it, you will not be able to recover your account.') }}
          </p>
        </div>

        <div class="auth-acknowledgment">
          <label>
            <input
              v-model="recoveryCodeAcknowledged"
              type="checkbox"
              :disabled="!authStore.recoveryCode"
            />
            {{ $gettext('I have saved my recovery code') }}
          </label>
        </div>

        <button
          class="auth-primary-btn"
          :disabled="!recoveryCodeAcknowledged || !authStore.recoveryCode"
          @click="handleAcknowledgeAndProceed"
        >
          {{ $gettext('Continue to Login') }}
        </button>
      </div>
    </template>
  </AuthLayout>
</template>
