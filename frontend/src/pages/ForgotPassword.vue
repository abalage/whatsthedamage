<!--
  Forgot Password Page Component

  Provides password reset functionality using recovery codes.
  Users can reset their password using the recovery code they saved during registration.

  This component orchestrates between the password reset form and the recovery code display.
-->

<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { resetPassword } from '../js/api';
import type { PasswordResetResponse } from '../types/auth';
import AuthLayout from '../components/AuthLayout.vue';
import { PasswordResetForm, RecoveryCodeDisplay } from '../components/auth';

const router = useRouter();

// Page state
const newRecoveryCode = ref<string | null>(null);
const showSuccessState = ref(false);
const error = ref<string | null>(null);
const isLoading = ref(false);

/**
 * Handle password reset form submission.
 */
async function handleResetPassword(
  username: string,
  recoveryCode: string,
  newPassword: string
) {
  isLoading.value = true;
  error.value = null;

  try {
    const response: PasswordResetResponse = await resetPassword(
      username,
      recoveryCode,
      newPassword
    );

    // Success - show new recovery code
    newRecoveryCode.value = response.new_recovery_code;
    showSuccessState.value = true;

  } catch (err: unknown) {
    const errorMessage = err instanceof Error ? err.message : String(err);

    // Handle specific error cases
    if (errorMessage.toLowerCase().includes('password must be at least')) {
      error.value = errorMessage;
    } else if (errorMessage.toLowerCase().includes('rate limit') ||
               errorMessage.toLowerCase().includes('too many')) {
      error.value = 'Too many attempts. Please try again later.';
    } else {
      // Generic error for invalid username or recovery code
      error.value = 'Invalid username or recovery code';
    }
    showSuccessState.value = false;
  } finally {
    isLoading.value = false;
  }
}

/**
 * Clear error message.
 */
function clearError() {
  error.value = null;
}

/**
 * Handle acknowledgment and navigation to login.
 */
function handleContinue() {
  router.push({ name: 'login' });
}
</script>

<template>
  <AuthLayout>
    <!-- Password Reset Form -->
    <template v-if="!showSuccessState">
      <h2>Reset Password</h2>

      <p class="instructions">
        Enter your username and the recovery code you saved during registration
        to reset your password.
      </p>

      <PasswordResetForm
        :is-loading="isLoading"
        :error="error"
        @submit="handleResetPassword"
        @clear-error="clearError"
      />

      <!-- Links -->
      <div class="auth-links">
        <p>
          Remember your password?
          <router-link to="/login" @click="clearError">Login</router-link>
        </p>
        <p>
          Don't have an account?
          <router-link to="/register" @click="clearError">Register</router-link>
        </p>
      </div>
    </template>

    <!-- Success State - Show new recovery code -->
    <template v-if="showSuccessState && newRecoveryCode">
      <RecoveryCodeDisplay
        :recovery-code="newRecoveryCode"
        @continue="handleContinue"
      />
    </template>
  </AuthLayout>
</template>

<style scoped>
.instructions {
  color: #666;
  margin-bottom: 1rem;
  line-height: 1.5;
}

.auth-links {
  text-align: center;
  margin-top: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.auth-links a {
  color: #007bff;
  text-decoration: none;
}

.auth-links a:hover {
  text-decoration: underline;
}
</style>
