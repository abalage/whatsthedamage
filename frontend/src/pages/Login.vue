<!--
  Login Page Component

  Provides user login functionality with form validation,
  error handling, and rate limit feedback.
-->

<script setup lang="ts">
import { ref } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useGettext } from 'vue3-gettext';
import { useAuthStore } from '../stores/auth';
import AuthLayout from '../components/AuthLayout.vue';

const { $gettext } = useGettext();
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
    authStore.error = $gettext('Username and password are required');
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
  } catch {
    // Error message is already set in the store
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
</script>

<template>
  <AuthLayout>
    <h2>{{ $gettext('Login') }}</h2>

    <form class="auth-form" @submit.prevent="handleLogin">
      <!-- Error message display -->
      <div v-if="authStore.error || hasRateLimitInfo()" class="auth-error">
        <p>{{ authStore.error }}</p>
        <p v-if="rateLimitRetryAfter !== null">
          {{ $gettext('Try again in') }} {{ Math.ceil(rateLimitRetryAfter / 60) }} {{ $gettext('minutes') }}.
        </p>
        <button
          type="button"
          class="auth-error-close"
          :aria-label="$gettext('Clear error')"
          @click="clearError"
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
          @focus="clearError"
        />
      </div>

      <!-- Password field -->
      <div class="form-group">
        <label for="password">{{ $gettext('Password') }}</label>
        <input
          id="password"
          v-model="password"
          type="password"
          class="form-control"
          required
          :placeholder="$gettext('Enter your password')"
          autocomplete="current-password"
          @focus="clearError"
        />
      </div>

      <!-- Remember me checkbox -->
      <div class="auth-checkbox">
        <label>
          <input v-model="rememberMe" type="checkbox" />
          {{ $gettext('Remember me') }}
        </label>
      </div>

      <!-- Submit button -->
      <button
        type="submit"
        class="auth-primary-btn"
        :disabled="isSubmitting || !username.trim() || !password.trim()"
      >
        <span v-if="!isSubmitting">{{ $gettext('Login') }}</span>
        <span v-else>{{ $gettext('Logging in...') }}</span>
      </button>

      <!-- Rate limit feedback -->
      <div v-if="rateLimitRemaining !== null" class="rate-limit-info">
        <p>
          {{ rateLimitRemaining }} {{ $gettext('login attempts remaining') }}
        </p>
      </div>
    </form>

    <!-- Links -->
    <div class="auth-links">
      <p>
        <router-link to="/forgot-password" @click="clearError">{{ $gettext('Forgot password?') }}</router-link>
      </p>
      <p>
        {{ $gettext("Don't have an account?") }}
        <router-link to="/register" @click="clearError">{{ $gettext('Register') }}</router-link>
      </p>
    </div>
  </AuthLayout>
</template>

<style scoped>
.rate-limit-info {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  text-align: center;
  margin-top: -0.5rem;
  margin-bottom: 1rem;
}
</style>
