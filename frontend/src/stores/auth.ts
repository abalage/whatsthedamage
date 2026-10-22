/**
 * Authentication store for managing user authentication state.
 *
 * Uses Pinia for state management. Handles login, logout, registration,
 * and session management. The CSRF token lives in the shared
 * js/csrfToken.ts holder (persisted there); this store only refreshes
 * and clears it alongside authentication state.
 */

import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { User } from '../types/auth';
import { register, login, logout, getMe, fetchCsrfToken, updateSharingPreference, updateUsername, changePassword, exportMyData, deleteAccount } from '../js/api';
import { setCsrfToken, getCsrfToken } from '../js/csrfToken';
import { useDatasetStore } from './dataset';
import type { DataExportResponse } from '../types/auth';

/**
 * Use the authentication store.
 *
 * State includes:
 * - user: Current authenticated user
 * - isAuthenticated: Whether user is logged in
 * - isLoading: Loading state for auth operations
 * - error: Current error message
 * - recoveryCode: Recovery code shown after registration
 * - showRecoveryCode: Whether to display recovery code
 * - recoveryCodeAcknowledged: Whether user has acknowledged saving recovery code
 */
export const useAuthStore = defineStore('auth', () => {
  // State
  const user = ref<User | null>(null);
  const isLoading = ref<boolean>(false);
  const isInitialized = ref<boolean>(false);
  const error = ref<string | null>(null);
  const recoveryCode = ref<string | null>(null);
  const showRecoveryCode = ref<boolean>(false);
  const recoveryCodeAcknowledged = ref<boolean>(false);

  // Computed properties
  const isAuthenticated = computed(() => user.value !== null);

  /**
   * Run an action with the shared loading/error wrapper.
   *
   * Sets isLoading during the action; stores the error message and
   * re-throws on failure.
   *
   * @param action - Async action to run
   * @returns Promise with the action's result
   */
  async function withLoading<T>(action: () => Promise<T>): Promise<T> {
    isLoading.value = true;
    error.value = null;

    try {
      return await action();
    } catch (err: unknown) {
      error.value = err instanceof Error ? err.message : String(err);
      throw err;
    } finally {
      isLoading.value = false;
    }
  }

  /**
   * Initialize auth state by checking current session.
   * Called by the router guard before the first navigation; runs the
   * session check only once per app load.
   */
  async function initialize(): Promise<void> {
    if (isInitialized.value || isLoading.value) return;

    isLoading.value = true;
    error.value = null;

    try {
      const response = await getMe();
      user.value = response.user;
      if (response.csrf_token) {
        setCsrfToken(response.csrf_token);
      } else if (!getCsrfToken()) {
        // The session has a token but this client does not (fresh
        // storage); mint one via the explicit token endpoint
        await refreshCsrfToken();
      }
    } catch {
      // Not authenticated - clear any existing state
      user.value = null;
      setCsrfToken(undefined);
      // The session expired or belongs to nobody; cached datasets
      // may belong to a previous user
      useDatasetStore().invalidateAll();
      // Don't set error for 401 (not authenticated)
    } finally {
      isLoading.value = false;
      isInitialized.value = true;
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
    showRecoveryCode.value = false;
    recoveryCodeAcknowledged.value = false;

    return withLoading(async () => {
      const response = await register(username, password);
      user.value = response.user;
      recoveryCode.value = response.recovery_code;
      showRecoveryCode.value = true;
      setCsrfToken(response.csrf_token);

      return { user: response.user, recoveryCode: response.recovery_code };
    });
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
    return withLoading(async () => {
      const response = await login(username, password, rememberMe);
      user.value = response.user;
      setCsrfToken(response.csrf_token);
      // Defensive: a cached dataset could belong to a previous session
      useDatasetStore().invalidateAll();

      return response.user;
    });
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
      setCsrfToken(undefined);
      // Cached datasets belong to the logged-out user
      useDatasetStore().invalidateAll();
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
   * Update the correction sharing opt-in preference.
   *
   * @param optIn - Whether the user opts in to sharing corrections
   * @returns Promise with the updated user
   */
  async function setOptInSharing(optIn: boolean): Promise<User> {
    return withLoading(async () => {
      const response = await updateSharingPreference(optIn);
      if (user.value) {
        user.value = response.user;
      }
      return response.user;
    });
  }

  /**
   * Change the current user's username (right to rectification).
   *
   * @param username - New unique username
   * @returns Promise with the updated user
   */
  async function changeUsername(username: string): Promise<User> {
    return withLoading(async () => {
      const response = await updateUsername(username);
      if (user.value) {
        user.value = response.user;
      }
      return response.user;
    });
  }

  /**
   * Change the current user's password while logged in.
   *
   * All other sessions are revoked server-side; the current session
   * stays valid.
   *
   * @param currentPassword - Current password confirming the change
   * @param newPassword - New password (minimum 12 characters)
   */
  async function changeUserPassword(
    currentPassword: string,
    newPassword: string
  ): Promise<void> {
    return withLoading(async () => {
      await changePassword(currentPassword, newPassword);
    });
  }

  /**
   * Export all personal data of the current user (data portability).
   *
   * @returns Promise with the machine-readable export document
   */
  async function exportData(): Promise<DataExportResponse> {
    return exportMyData();
  }

  /**
   * Schedule deletion of the current account.
   *
   * The backend revokes all sessions and schedules the deletion after
   * a grace period; logging in before that cancels it. Local auth
   * state is cleared regardless.
   *
   * @param password - Current password confirming the deletion request
   * @param revokeSharedCorrections - Whether to also withdraw the
   * user's shared correction contributions when the account is deleted
   * @returns Promise with the scheduled deletion timestamp
   */
  async function requestAccountDeletion(
    password: string,
    revokeSharedCorrections: boolean = false
  ): Promise<string> {
    isLoading.value = true;
    error.value = null;

    try {
      const response = await deleteAccount(password, revokeSharedCorrections);
      return response.scheduled_deletion_at;
    } catch (err: unknown) {
      error.value = err instanceof Error ? err.message : String(err);
      throw err;
    } finally {
      // All sessions are revoked server-side; drop local state too
      user.value = null;
      setCsrfToken(undefined);
      useDatasetStore().invalidateAll();
      isLoading.value = false;
    }
  }

  /**
   * Mint a fresh CSRF token from the backend and persist it.
   * The new token supersedes any previously issued one for this session.
   */
  async function refreshCsrfToken(): Promise<void> {
    try {
      await fetchCsrfToken();
    } catch {
      // If we can't get a new CSRF token, just clear it
      setCsrfToken(undefined);
    }
  }

  // Return the public API
  return {
    // State
    user,
    isAuthenticated,
    isLoading,
    isInitialized,
    error,
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
    setOptInSharing,
    changeUsername,
    changeUserPassword,
    exportData,
    requestAccountDeletion
  };
});
