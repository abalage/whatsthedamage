<!--
  Password Reset Form Component
  
  Form for resetting password using recovery code.
  Handles form state, validation, and submission.
-->

<script setup lang="ts">
import { ref, computed } from 'vue';
import { getPasswordMinLength } from '../../config/auth-config';

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
    <div v-if="props.error" class="error-message">
      <p>{{ props.error }}</p>
      <button
        type="button"
        class="error-close"
        aria-label="Clear error"
        @click="handleClearError"
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
        placeholder="Enter your username"
        autocomplete="username"
        @focus="handleClearError"
      />
    </div>

    <!-- Recovery Code field -->
    <div class="form-group">
      <label for="recoveryCode">Recovery Code</label>
      <input
        id="recoveryCode"
        v-model="recoveryCode"
        type="text"
        required
        placeholder="e.g., ABCD-EFGH-IJKL-MNOP"
        autocomplete="off"
        @focus="handleClearError"
      />
      <p class="hint">
        Enter the recovery code you saved (with or without hyphens)
      </p>
    </div>

    <!-- New Password field -->
    <div class="form-group">
      <label for="newPassword">New Password</label>
      <input
        id="newPassword"
        v-model="newPassword"
        type="password"
        required
        placeholder="Enter new password"
        autocomplete="new-password"
        @focus="handleClearError"
      />
      <div class="password-strength" :class="passwordStrength">
        <span v-if="newPassword.length > 0">
          {{ newPassword.length }}/{{ minPasswordLength }} characters
        </span>
      </div>
    </div>

    <!-- Confirm Password field -->
    <div class="form-group">
      <label for="confirmPassword">Confirm New Password</label>
      <input
        id="confirmPassword"
        v-model="confirmPassword"
        type="password"
        required
        placeholder="Confirm new password"
        autocomplete="new-password"
        @focus="handleClearError"
      />
      <div v-if="confirmPassword.length > 0" class="validation-message">
        <span v-if="passwordsMatch" class="valid">Passwords match</span>
        <span v-else class="invalid">Passwords do not match</span>
      </div>
    </div>

    <!-- Submit button -->
    <button
      type="submit"
      :disabled="!isFormValid || props.isLoading"
      class="btn btn-primary"
    >
      <span v-if="!props.isLoading">Reset Password</span>
      <span v-else>Resetting...</span>
    </button>

    <!-- Requirements notice -->
    <div class="requirements-notice">
      <p>
        <strong>Note:</strong> Password must be at least {{ minPasswordLength }} characters long.
      </p>
    </div>
  </form>
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
  font-family: monospace;
}

.form-group input[type="text"]:focus,
.form-group input[type="password"]:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
}

.hint {
  font-size: 0.875rem;
  color: #666;
  margin-top: 0.25rem;
}

.password-strength {
  font-size: 0.75rem;
  height: 1rem;
  display: flex;
  align-items: center;
}

.password-strength.empty {
  color: #666;
}

.password-strength.weak {
  color: #dc3545;
}

.password-strength.medium {
  color: #ffc107;
}

.password-strength.strong {
  color: #28a745;
}

.validation-message {
  font-size: 0.875rem;
}

.valid {
  color: #28a745;
}

.invalid {
  color: #dc3545;
}

.requirements-notice {
  font-size: 0.875rem;
  color: #666;
  margin-top: -0.5rem;
}

.btn {
  padding: 0.75rem 1rem;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  cursor: pointer;
  transition: background-color 0.2s, opacity 0.2s;
  width: 100%;
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
</style>
