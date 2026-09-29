/**
 * Authentication store for managing user authentication state.
 *
 * Uses Pinia for state management. Handles login, logout, registration,
 * and session management. Manages CSRF tokens and recovery codes.
 */

import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { User } from '../types/auth.js';
import { register, login, logout, getMe, fetchCsrfToken } from '../js/api.js';

/**
 * localStorage key for the persisted CSRF token.
 * Persisting it lets page reloads and tabs reuse the same token instead
 * of forcing the backend to mint (and rotate) a new one.
 */
const CSRF_TOKEN_STORAGE_KEY = 'csrfToken';

/**
 * Use the authentication store.
 *
 * State includes:
 * - user: Current authenticated user
 * - isAuthenticated: Whether user is logged in
 * - isLoading: Loading state for auth operations
 * - error: Current error message
 * - csrfToken: Current CSRF token (persisted in localStorage)
 * - recoveryCode: Recovery code shown after registration
 * - showRecoveryCode: Whether to display recovery code
 * - recoveryCodeAcknowledged: Whether user has acknowledged saving recovery code
 */
export const useAuthStore = defineStore('auth', () => {
  // State
  const user = ref<User | null>(null);
  const isLoading = ref<boolean>(false);
  const error = ref<string | null>(null);
  const csrfToken = ref<string | null>(localStorage.getItem(CSRF_TOKEN_STORAGE_KEY));
  const recoveryCode = ref<string | null>(null);
  const showRecoveryCode = ref<boolean>(false);
  const recoveryCodeAcknowledged = ref<boolean>(false);

  // Computed properties
  const isAuthenticated = computed(() => user.value !== null);

  /**
   * Set the CSRF token in state and persist it.
   *
   * @param token - New CSRF token, or null to clear it
   */
  function setCsrfToken(token: string | null): void {
    csrfToken.value = token;
    if (token) {
      localStorage.setItem(CSRF_TOKEN_STORAGE_KEY, token);
    } else {
      localStorage.removeItem(CSRF_TOKEN_STORAGE_KEY);
    }
  }

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
      if (response.csrf_token) {
        setCsrfToken(response.csrf_token);
      } else if (!csrfToken.value) {
        // The session has a token but this client does not (fresh
        // storage); mint one via the explicit token endpoint
        await refreshCsrfToken();
      }
    } catch {
      // Not authenticated - clear any existing state
      user.value = null;
      setCsrfToken(null);
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
      setCsrfToken(response.csrf_token);

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
      setCsrfToken(response.csrf_token);

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
      setCsrfToken(null);
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
   * Mint a fresh CSRF token from the backend and persist it.
   * The new token supersedes any previously issued one for this session.
   */
  async function refreshCsrfToken(): Promise<void> {
    try {
      const response = await fetchCsrfToken();
      setCsrfToken(response.csrf_token);
    } catch {
      // If we can't get a new CSRF token, just clear it
      setCsrfToken(null);
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
    getUser: (): User | null => user.value,
    getCsrfToken: (): string | null => csrfToken.value
  };
});
