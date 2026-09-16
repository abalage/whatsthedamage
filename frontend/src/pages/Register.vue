<!--
  Register Page Component

  Provides user registration with form validation,
  password strength checking, and recovery code display.
-->

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../stores/auth';
import AuthLayout from '../components/AuthLayout.vue';

const router = useRouter();
const authStore = useAuthStore();

// Form state
const username = ref('');
const password = ref('');
const confirmPassword = ref('');
const isSubmitting = ref(false);
const showRecoveryCode = ref(false);
const recoveryCodeAcknowledged = ref(false);

// Computed properties
const passwordsMatch = () => password.value === confirmPassword.value;
const passwordValid = () => password.value.length >= 12;
const formValid = () => (
  username.value.trim().length > 0 &&
  password.value.length >= 12 &&
  passwordsMatch()
);

/**
 * Handle form submission for registration.
 */
async function handleRegister() {
  if (!formValid()) {
    if (!passwordsMatch()) {
      authStore.error = 'Passwords do not match';
    } else if (!passwordValid()) {
      authStore.error = 'Password must be at least 12 characters';
    } else {
      authStore.error = 'Please fill in all fields';
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
      // Could show a toast/snackbar here
    }
  } catch (err) {
    // Clipboard write failed
    console.error('Failed to copy recovery code:', err);
  }
}

// Initialize - check if already authenticated
onMounted(async () => {
  await authStore.initialize();

  // If already authenticated, redirect to home
  if (authStore.isAuthenticated) {
    await router.push({ name: 'index' });
  }
});
</script>

<template>
  <AuthLayout>
    <!-- Registration form -->
    <template v-if="!showRecoveryCode">
      <h2>Create Account</h2>

      <form @submit.prevent="handleRegister" class="auth-form">
        <!-- Error message display -->
        <div v-if="authStore.error" class="error-message">
          <p>{{ authStore.error }}</p>
          <button
            type="button"
            @click="authStore.clearError"
            class="error-close"
            aria-label="Clear error"
          >
            &times;
          </button>
        </div>

        <!-- Username field -->
        <div class="form-group">
          <label for="username">Username</label>
          <input
            id="username"
            v-model="username"
            type="text"
            required
            placeholder="Choose a username"
            autocomplete="username"
            @focus="authStore.clearError"
          />
        </div>

        <!-- Password field -->
        <div class="form-group">
          <label for="password">Password (minimum 12 characters)</label>
          <input
            id="password"
            v-model="password"
            type="password"
            required
            minlength="12"
            placeholder="Create a password"
            autocomplete="new-password"
            @focus="authStore.clearError"
          />
          <div class="password-hint">
            <span
              :class="password.length >= 12 ? 'valid' : 'invalid'"
            >
              {{ password.length }}/12 characters
            </span>
          </div>
        </div>

        <!-- Confirm password field -->
        <div class="form-group">
          <label for="confirmPassword">Confirm Password</label>
          <input
            id="confirmPassword"
            v-model="confirmPassword"
            type="password"
            required
            placeholder="Confirm your password"
            autocomplete="new-password"
            @focus="authStore.clearError"
          />
          <div class="password-hint">
            <span
              :class="passwordsMatch() ? 'valid' : 'invalid'"
            >
              {{ passwordsMatch() ? 'Passwords match' : 'Passwords do not match' }}
            </span>
          </div>
        </div>

        <!-- Submit button -->
        <button
          type="submit"
          :disabled="isSubmitting || !formValid()"
          class="btn btn-primary"
        >
          <span v-if="!isSubmitting">Create Account</span>
          <span v-else>Creating...</span>
        </button>
      </form>

      <!-- Links -->
      <div class="auth-links">
        <p>
          Already have an account?
          <router-link to="/login" @click="authStore.clearError">Login</router-link>
        </p>
      </div>
    </template>

    <!-- Recovery code display -->
    <template v-else>
      <h2>Save Your Recovery Code</h2>

      <div class="recovery-code-container">
        <p class="recovery-instructions">
          This code is displayed only once. Save it securely to reset your
          password if you forget it. You will not be able to retrieve it later.
        </p>

        <div class="recovery-code-display">
          <code class="recovery-code">{{ authStore.recoveryCode }}</code>
          <button
            @click="copyRecoveryCode"
            class="copy-btn"
            type="button"
            title="Copy to clipboard"
          >
            Copy
          </button>
        </div>

        <div class="recovery-warning">
          <p>
            <strong>Important:</strong> Store this code in a safe place.
            Without it, you will not be able to recover your account.
          </p>
        </div>

        <div class="form-group form-checkbox">
          <label>
            <input
              v-model="recoveryCodeAcknowledged"
              type="checkbox"
              :disabled="!authStore.recoveryCode"
            />
            I have saved my recovery code
          </label>
        </div>

        <button
          @click="handleAcknowledgeAndProceed"
          :disabled="!recoveryCodeAcknowledged || !authStore.recoveryCode"
          class="btn btn-primary"
        >
          Continue to Login
        </button>
      </div>
    </template>
  </AuthLayout>
</template>

<style scoped>
.auth-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  font-weight: 500;
  color: #333;
}

.form-group input[type="text"],
.form-group input[type="password"] {
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.form-group input[type="text"]:focus,
.form-group input[type="password"]:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
}

.password-hint {
  font-size: 0.875rem;
}

.password-hint .valid {
  color: #28a745;
}

.password-hint .invalid {
  color: #dc3545;
}

.form-checkbox {
  flex-direction: row;
  align-items: center;
  gap: 0.5rem;
}

.form-checkbox label {
  font-weight: normal;
  cursor: pointer;
}

.btn {
  padding: 0.75rem 1rem;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  cursor: pointer;
  transition: background-color 0.2s, opacity 0.2s;
}

.btn-primary {
  background-color: #007bff;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background-color: #0069d9;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.error-message {
  background-color: #f8d7da;
  color: #721c24;
  padding: 0.75rem;
  border-radius: 4px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
}

.error-close {
  background: none;
  border: none;
  font-size: 1.25rem;
  cursor: pointer;
  color: #721c24;
  padding: 0;
  line-height: 1;
}

.error-close:hover {
  opacity: 0.7;
}

.auth-links {
  text-align: center;
  margin-top: 1rem;
}

.auth-links a {
  color: #007bff;
  text-decoration: none;
}

.auth-links a:hover {
  text-decoration: underline;
}

/* Recovery code display */
.recovery-code-container {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.recovery-instructions {
  background-color: #fff3cd;
  padding: 1rem;
  border-radius: 4px;
  margin: 0;
  font-size: 0.9rem;
  line-height: 1.4;
}

.recovery-code-display {
  display: flex;
  align-items: center;
  gap: 1rem;
  background-color: #f8f9fa;
  padding: 1rem;
  border-radius: 4px;
  font-size: 1.125rem;
}

.recovery-code {
  font-family: monospace;
  letter-spacing: 0.1em;
  background: none;
  padding: 0.5rem;
  border: none;
  color: #333;
}

.copy-btn {
  background-color: #6c757d;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.875rem;
  white-space: nowrap;
}

.copy-btn:hover {
  background-color: #5a6268;
}

.recovery-warning {
  background-color: #f8d7da;
  padding: 1rem;
  border-radius: 4px;
  font-size: 0.9rem;
}

.recovery-warning strong {
  color: #721c24;
}
</style>
