<!--
  Login Page Component

  Provides user login functionality with form validation,
  error handling, and rate limit feedback.
-->

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useAuthStore } from '../stores/auth';
import AuthLayout from '../components/AuthLayout.vue';

const router = useRouter();
const route = useRoute();
const authStore = useAuthStore();

// Form state
const username = ref('');
const password = ref('');
const rememberMe = ref(false);
const isSubmitting = ref(false);
const rateLimitRemaining = ref<number | null>(null);
const rateLimitRetryAfter = ref<number | null>(null);

// Computed
const hasRateLimitInfo = () => rateLimitRemaining.value !== null || rateLimitRetryAfter.value !== null;

/**
 * Handle form submission for login.
 */
async function handleLogin() {
  if (!username.value.trim() || !password.value.trim()) {
    authStore.error = 'Username and password are required';
    return;
  }

  isSubmitting.value = true;
  authStore.clearError();

  try {
    await authStore.login(
      username.value.trim(),
      password.value,
      rememberMe.value
    );

    // Redirect based on query parameter or to home
    const redirect = route.query.redirect as string | undefined;
    if (redirect && redirect !== '/login') {
      await router.push(redirect);
    } else {
      await router.push({ name: 'index' });
    }
  } catch (err: unknown) {
    const errorMessage = err instanceof Error ? err.message : String(err);

    // Check for rate limiting in error message
    if (errorMessage.toLowerCase().includes('rate limit') ||
        errorMessage.toLowerCase().includes('too many')) {
      // Extract retry after from error if available
      // This would be better handled with proper error typing
    }
  } finally {
    isSubmitting.value = false;
  }
}

/**
 * Clear error and reset rate limit info.
 */
function clearError() {
  authStore.clearError();
  rateLimitRemaining.value = null;
  rateLimitRetryAfter.value = null;
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
    <h2>Login</h2>

    <form @submit.prevent="handleLogin" class="auth-form">
      <!-- Error message display -->
      <div v-if="authStore.error || hasRateLimitInfo()" class="error-message">
        <p>{{ authStore.error }}</p>
        <p v-if="rateLimitRetryAfter !== null">
          Try again in {{ Math.ceil(rateLimitRetryAfter / 60) }} minutes.
        </p>
        <button
          type="button"
          @click="clearError"
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
          placeholder="Enter your username"
          autocomplete="username"
          @focus="clearError"
        />
      </div>

      <!-- Password field -->
      <div class="form-group">
        <label for="password">Password</label>
        <input
          id="password"
          v-model="password"
          type="password"
          required
          placeholder="Enter your password"
          autocomplete="current-password"
          @focus="clearError"
        />
      </div>

      <!-- Remember me checkbox -->
      <div class="form-group form-checkbox">
        <label>
          <input v-model="rememberMe" type="checkbox" />
          Remember me
        </label>
      </div>

      <!-- Submit button -->
      <button
        type="submit"
        :disabled="isSubmitting || !username.trim() || !password.trim()"
        class="btn btn-primary"
      >
        <span v-if="!isSubmitting">Login</span>
        <span v-else>Logging in...</span>
      </button>

      <!-- Rate limit feedback -->
      <div v-if="rateLimitRemaining !== null" class="rate-limit-info">
        <p>
          {{ rateLimitRemaining }} login attempts remaining
        </p>
      </div>
    </form>

    <!-- Links -->
    <div class="auth-links">
      <p>
        <router-link to="/forgot-password" @click="clearError">Forgot password?</router-link>
      </p>
      <p>
        Don't have an account?
        <router-link to="/register" @click="clearError">Register</router-link>
      </p>
    </div>
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

.rate-limit-info {
  font-size: 0.875rem;
  color: #666;
  text-align: center;
  margin-top: -0.5rem;
  margin-bottom: 1rem;
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
</style>
