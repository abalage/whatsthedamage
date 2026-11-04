/**
 * Authentication store for managing user authentication state.
 *
 * Uses Pinia for state management. Handles login, logout, registration,
 * and session management. The CSRF token is delivered by the backend as
 * a readable cookie (see js/csrfToken.ts); this store only ensures one
 * exists after login and initialization.
 */

import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { User } from '../types/auth';
import { register, confirmRegistration, login, logout, getMe, fetchCsrfToken, updateSharingPreference, updateUsername, changePassword, exportMyData, deleteAccount, regenerateRecoveryCode } from '../js/api';
import { getCsrfToken } from '../js/csrfToken';
import { useAsyncAction } from '../composables/useAsyncAction';
import { useDatasetStore } from './dataset';
import type { DataExportResponse } from '../types/auth';

// sessionStorage keys for the pending registration. sessionStorage (not
// localStorage) is deliberate: the recovery code must survive a page
// reload while the registration is pending, but must never outlive the
// tab. Both keys are removed as soon as the registration is confirmed,
// fails, or the user logs out.
const PENDING_TOKEN_KEY = 'pending_registration_token';
const PENDING_RECOVERY_CODE_KEY = 'pending_registration_recovery_code';

function readSessionValue(key: string): string | undefined {
  try {
    return sessionStorage.getItem(key) ?? undefined;
  } catch {
    return undefined;
  }
}

function writeSessionValue(key: string, value: string | undefined): void {
  try {
    if (value === undefined) {
      sessionStorage.removeItem(key);
    } else {
      sessionStorage.setItem(key, value);
    }
  } catch {
    // Storage unavailable: pending state lives in memory only
  }
}

/**
 * Use the authentication store.
 *
 * State includes:
 * - user: Current authenticated user
 * - isAuthenticated: Whether user is logged in
 * - isLoading: Loading state for auth operations
 * - error: Current error message
 * - pendingToken: One-time token of the pending registration (phase 1)
 * - recoveryCode: Recovery code shown after registration phase 1
 * - showRecoveryCode: Whether to display recovery code
 */
export const useAuthStore = defineStore('auth', () => {
  // Shared loading/error state for auth actions (useAsyncAction
  // stores the error and rethrows; the store exposes both)
  const { isLoading, error, run } = useAsyncAction();

  // State
  const user = ref<User | null>(null);
  const isInitialized = ref<boolean>(false);
  const pendingToken = ref<string | undefined>(undefined);
  const recoveryCode = ref<string | null>(null);
  const showRecoveryCode = ref<boolean>(false);

  // Computed properties
  const isAuthenticated = computed(() => user.value !== null);

  /**
   * Clear all pending-registration state, including the sessionStorage
   * copies of the pending token and recovery code.
   */
  function clearPendingState(): void {
    pendingToken.value = undefined;
    recoveryCode.value = null;
    showRecoveryCode.value = false;
    writeSessionValue(PENDING_TOKEN_KEY, undefined);
    writeSessionValue(PENDING_RECOVERY_CODE_KEY, undefined);
  }

  /**
   * Initialize auth state by checking current session.
   * Called by the router guard before the first navigation; runs the
   * session check only once per app load.
   */
  async function initialize(): Promise<void> {
    if (isInitialized.value || isLoading.value) return;

    isLoading.value = true;
    error.value = undefined;

    try {
      const response = await getMe();
      user.value = response.user;
      // A confirmed session supersedes any leftover pending registration
      clearPendingState();
      if (!getCsrfToken()) {
        // The session may already have a token the browser does not
        // (fresh cookie store); mint one via the explicit endpoint
        try {
          await refreshCsrfToken();
        } catch {
          // A failed mint does not deauthenticate; the next
          // state-changing request retries via the 403 path
        }
      }
    } catch {
      // Not authenticated - clear any existing state
      user.value = null;
      // The session expired or belongs to nobody; cached datasets
      // may belong to a previous user
      useDatasetStore().invalidateAll();
      // Rehydrate an unfinished pending registration so a page reload
      // on the recovery-code screen shows the code again
      const storedToken = readSessionValue(PENDING_TOKEN_KEY);
      const storedCode = readSessionValue(PENDING_RECOVERY_CODE_KEY);
      if (storedToken !== undefined && storedCode !== undefined) {
        pendingToken.value = storedToken;
        recoveryCode.value = storedCode;
        showRecoveryCode.value = true;
      } else {
        clearPendingState();
      }
      // Don't set error for 401 (not authenticated)
    } finally {
      isLoading.value = false;
      isInitialized.value = true;
    }
  }

  /**
   * Start a two-phase registration (phase 1).
   *
   * Creates a pending registration only; the account is committed by
   * confirmRegistration() after the user acknowledges the recovery code.
   *
   * @param username - User's desired username
   * @param password - User's password
   * @returns Promise with the pending token and recovery code
   */
  async function registerUser(username: string, password: string): Promise<{ pendingToken: string; recoveryCode: string }> {
    showRecoveryCode.value = false;

    return run(async () => {
      const response = await register(username, password);
      pendingToken.value = response.pending_token;
      recoveryCode.value = response.recovery_code;
      showRecoveryCode.value = true;
      writeSessionValue(PENDING_TOKEN_KEY, response.pending_token);
      writeSessionValue(PENDING_RECOVERY_CODE_KEY, response.recovery_code);

      return { pendingToken: response.pending_token, recoveryCode: response.recovery_code };
    });
  }

  /**
   * Confirm the pending registration (phase 2).
   *
   * Echoes the stored recovery code back to the backend; the account is
   * committed and the session started only when the code matches. On
   * success all copies of the recovery code are cleared immediately; on
   * failure the pending state is cleared as well (the token is invalid,
   * expired, or the code mismatched) so the user can register again.
   *
   * @returns Promise with the confirmed user
   */
  async function confirmUserRegistration(): Promise<User> {
    const token = pendingToken.value;
    const code = recoveryCode.value;
    if (token === undefined || code === null) {
      throw new Error('No pending registration to confirm');
    }

    try {
      return await run(async () => {
        const response = await confirmRegistration(token, code);
        user.value = response.user;
        clearPendingState();
        return response.user;
      });
    } catch (e) {
      clearPendingState();
      throw e;
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
    return run(async () => {
      const response = await login(username, password, rememberMe);
      user.value = response.user;
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
    error.value = undefined;

    try {
      await logout();
    } finally {
      // Clear state regardless of success
      user.value = null;
      clearPendingState();
      // Cached datasets belong to the logged-out user
      useDatasetStore().invalidateAll();
      isLoading.value = false;
    }
  }

  /**
   * Clear the current error message.
   */
  function clearError(): void {
    error.value = undefined;
  }

  /**
   * Update the correction sharing opt-in preference.
   *
   * @param optIn - Whether the user opts in to sharing corrections
   * @returns Promise with the updated user
   */
  async function setOptInSharing(optIn: boolean): Promise<User> {
    return run(async () => {
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
    return run(async () => {
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
    return run(async () => {
      await changePassword(currentPassword, newPassword);
    });
  }

  /**
   * Export all personal data of the current user (data portability).
   *
   * @returns Promise with the machine-readable export document
   */
  async function exportData(): Promise<DataExportResponse> {
    return run(() => exportMyData());
  }

  /**
   * Schedule deletion of the current account.
   *
   * The backend revokes all sessions and schedules the deletion after
   * a grace period; logging in before that cancels it. Local auth
   * state is cleared only on success: a failed request (e.g. wrong
   * password) leaves the still-valid session intact.
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
    const response = await run(() => deleteAccount(password, revokeSharedCorrections));

    // All sessions are revoked server-side; drop local state too
    user.value = null;
    useDatasetStore().invalidateAll();
    return response.scheduled_deletion_at;
  }

  /**
   * Regenerate the current user's recovery code while logged in.
   *
   * The old recovery code is invalidated server-side and all other
   * sessions are revoked; the current session stays valid. The new
   * code is returned to the caller for one-time display — it is NOT
   * stored in the shared recoveryCode state (that belongs to the
   * registration flow).
   *
   * @param password - Current password confirming the regeneration
   * @returns Promise with the new formatted recovery code
   */
  async function regenerateUserRecoveryCode(password: string): Promise<string> {
    return run(async () => {
      const response = await regenerateRecoveryCode(password);
      return response.new_recovery_code;
    });
  }

  /**
   * Mint a fresh CSRF token from the backend.
   * The new cookie supersedes any previously issued one for this session.
   */
  async function refreshCsrfToken(): Promise<void> {
    await fetchCsrfToken();
  }

  // Return the public API
  return {
    // State
    user,
    isAuthenticated,
    isLoading,
    isInitialized,
    error,
    pendingToken,
    recoveryCode,
    showRecoveryCode,

    // Actions
    initialize,
    register: registerUser,
    confirmRegistration: confirmUserRegistration,
    login: loginUser,
    logout: logoutUser,
    clearError,
    clearPendingState,
    refreshCsrfToken,
    setOptInSharing,
    changeUsername,
    changeUserPassword,
    exportData,
    requestAccountDeletion,
    regenerateUserRecoveryCode
  };
});
