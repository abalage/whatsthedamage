/**
 * Authentication store for managing user authentication state.
 *
 * Uses Pinia for state management. Handles login, logout, registration,
 * and session management. Manages CSRF tokens and recovery codes.
 */

import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { User, AuthState, RegisterRequest, LoginRequest } from '../types/auth.js';
import { register, login, logout, getMe } from '../js/api.js';

/**
 * Use the authentication store.
 *
 * State includes:
 * - user: Current authenticated user
 * - isAuthenticated: Whether user is logged in
 * - isLoading: Loading state for auth operations
 * - error: Current error message
 * - csrfToken: Current CSRF token
 * - recoveryCode: Recovery code shown after registration
 * - showRecoveryCode: Whether to display recovery code
 * - recoveryCodeAcknowledged: Whether user has acknowledged saving recovery code
 */
export const useAuthStore = defineStore('auth', () => {
  // State
  const user = ref<User | null>(null);
  const isLoading = ref<boolean>(false);
  const error = ref<string | null>(null);
  const csrfToken = ref<string | null>(null);
  const recoveryCode = ref<string | null>(null);
  const showRecoveryCode = ref<boolean>(false);
  const recoveryCodeAcknowledged = ref<boolean>(false);

  // Computed properties
  const isAuthenticated = computed(() => user.value !== null);

  /**
   * Initialize auth state by checking current session.
   * Called on app load to restore session from cookies.
   */
  async function initialize(): Promise<void> {
    if (isLoading.value) return;

    isLoading.value = true;
    error.value = null;

    try {
      const response = await getMe();
      user.value = response.user;
      csrfToken.value = response.csrf_token;
    } catch (err: unknown) {
      // Not authenticated - clear any existing state
      user.value = null;
      csrfToken.value = null;
      // Don't set error for 401 (not authenticated)
    } finally {
      isLoading.value = false;
    }
  }

  /**
   * Register a new user account.
   *
   * @param username - User's desired username
   * @param password - User's password
   * @returns Promise with user and recovery code
   */
  async function registerUser(username: string, password: string): Promise<{ user: User; recoveryCode: string }> {
    isLoading.value = true;
    error.value = null;
    showRecoveryCode.value = false;
    recoveryCodeAcknowledged.value = false;

    try {
      const response = await register(username, password);
      user.value = response.user;
      recoveryCode.value = response.recovery_code;
      showRecoveryCode.value = true;

      // CSRF token is now fetched separately from /auth/me endpoint
      // after the user is authenticated (session cookie is set)
      await refreshCsrfToken();

      return { user: response.user, recoveryCode: response.recovery_code };
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : String(err);
      error.value = errorMessage;
      throw err;
    } finally {
      isLoading.value = false;
    }
  }

  /**
   * Login with username and password.
   *
   * @param username - User's username
   * @param password - User's password
   * @param rememberMe - Whether to remember the session
   * @returns Promise with authenticated user
   */
  async function loginUser(username: string, password: string, rememberMe: boolean = false): Promise<User> {
    isLoading.value = true;
    error.value = null;

    try {
      const response = await login(username, password, rememberMe);
      user.value = response.user;

      // CSRF token is now fetched separately from /auth/me endpoint
      // after the user is authenticated (session cookie is set)
      await refreshCsrfToken();

      return response.user;
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : String(err);
      error.value = errorMessage;
      throw err;
    } finally {
      isLoading.value = false;
    }
  }

  /**
   * Logout the current user.
   */
  async function logoutUser(): Promise<void> {
    isLoading.value = true;
    error.value = null;

    try {
      await logout();
    } finally {
      // Clear state regardless of success
      user.value = null;
      csrfToken.value = null;
      isLoading.value = false;
    }
  }

  /**
   * Clear the current error message.
   */
  function clearError(): void {
    error.value = null;
  }

  /**
   * Acknowledge that the recovery code has been saved.
   *
   * This must be called before allowing the user to proceed after registration.
   */
  function acknowledgeRecoveryCode(): void {
    recoveryCodeAcknowledged.value = true;
    showRecoveryCode.value = false;
  }

  /**
   * Refresh the CSRF token from the backend.
   * Called after login/register to get a fresh CSRF token.
   */
  async function refreshCsrfToken(): Promise<void> {
    try {
      // getMe() returns user info + csrf_token for authenticated users
      const response = await getMe();
      csrfToken.value = response.csrf_token;
    } catch {
      // If we can't get a new CSRF token, just clear it
      csrfToken.value = null;
    }
  }

  // Return the public API
  return {
    // State
    user,
    isAuthenticated,
    isLoading,
    error,
    csrfToken,
    recoveryCode,
    showRecoveryCode,
    recoveryCodeAcknowledged,

    // Actions
    initialize,
    register: registerUser,
    login: loginUser,
    logout: logoutUser,
    clearError,
    acknowledgeRecoveryCode,
    refreshCsrfToken,

    // Getters
    getUser: () => user.value,
    getCsrfToken: () => csrfToken.value
  };
});
