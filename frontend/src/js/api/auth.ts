/**
 * Authentication and account management API functions
 * @module utils/api/auth
 */

import { getApiUrl, request } from './request'
import type {
  RegisterRequest,
  RegisterResponse,
  RegisterConfirmRequest,
  RegisterConfirmResponse,
  LoginRequest,
  LoginResponse,
  LogoutResponse,
  MeResponse,
  PasswordResetRequest,
  PasswordResetResponse,
  UpdateMeRequest,
  UpdateMeResponse,
  AccountDeletionRequest,
  AccountDeletionResponse,
  ChangePasswordRequest,
  ChangePasswordResponse,
  DataExportResponse,
  RegenerateRecoveryCodeRequest,
  RegenerateRecoveryCodeResponse
} from '../../types/auth'

/**
 * Start a two-phase registration (phase 1)
 *
 * Creates a pending registration and returns the one-time pending
 * token and recovery code. No account and no session exist yet; no
 * cookies are set.
 * @param username - User's username
 * @param password - User's password
 * @returns Promise with the pending registration response
 */
export async function register(username: string, password: string): Promise<RegisterResponse> {
  const requestData: RegisterRequest = { username, password }
  return request<RegisterResponse>(getApiUrl('/auth/register'), {
    method: 'POST',
    body: JSON.stringify(requestData)
  })
}

/**
 * Confirm a pending registration (phase 2)
 *
 * Echoes the recovery code back as proof that it was saved; the backend
 * commits the account and sets the session/CSRF cookies only when the
 * code matches.
 * @param pendingToken - The pending token from phase 1
 * @param recoveryCode - The recovery code echoed back
 * @returns Promise with the confirmed user and session expiry
 */
export async function confirmRegistration(
  pendingToken: string,
  recoveryCode: string
): Promise<RegisterConfirmResponse> {
  const requestData: RegisterConfirmRequest = {
    pending_token: pendingToken,
    recovery_code: recoveryCode
  }
  return request<RegisterConfirmResponse>(getApiUrl('/auth/register/confirm'), {
    method: 'POST',
    body: JSON.stringify(requestData)
  })
}

/**
 * Login a user
 * @param username - User's username
 * @param password - User's password
 * @param rememberMe - Whether to remember the session
 * @returns Promise with login response
 */
export async function login(username: string, password: string, rememberMe: boolean = false): Promise<LoginResponse> {
  const requestData: LoginRequest = { username, password, rememberMe }
  return request<LoginResponse>(getApiUrl('/auth/login'), {
    method: 'POST',
    body: JSON.stringify(requestData)
  })
}

/**
 * Logout the current user
 * @returns Promise with logout response
 */
export async function logout(): Promise<LogoutResponse> {
  return request<LogoutResponse>(getApiUrl('/auth/logout'), {
    method: 'POST',
    body: JSON.stringify({})
  })
}

/**
 * Get current user information
 * @returns Promise with user info
 */
export async function getMe(): Promise<MeResponse> {
  return request<MeResponse>(getApiUrl('/auth/me'))
}

/**
 * Update the current user's correction sharing opt-in preference
 * @param optIn - Whether the user opts in to sharing corrections
 * @returns Promise with the updated user
 */
export async function updateSharingPreference(optIn: boolean): Promise<UpdateMeResponse> {
  const requestData: UpdateMeRequest = { opt_in_sharing: optIn }
  return request<UpdateMeResponse>(getApiUrl('/auth/me'), {
    method: 'PUT',
    body: JSON.stringify(requestData)
  })
}

/**
 * Get a new CSRF token
 *
 * The backend mints a token and sets it as a readable cookie; this
 * function just triggers the refresh. Read the token afterwards via
 * getCsrfToken(). The minted token replaces any previously issued
 * one for the session.
 */
export async function fetchCsrfToken(): Promise<void> {
  await request(getApiUrl('/auth/csrf-token'))
}

/**
 * Reset password using recovery code
 * @param username - User's username
 * @param recoveryCode - Recovery code
 * @param newPassword - New password
 * @returns Promise with password reset response containing user and new recovery code
 */
export async function resetPassword(
  username: string,
  recoveryCode: string,
  newPassword: string
): Promise<PasswordResetResponse> {
  const requestData: PasswordResetRequest = {
    username,
    recoveryCode,
    newPassword
  }
  return request<PasswordResetResponse>(getApiUrl('/auth/reset-password'), {
    method: 'POST',
    body: JSON.stringify(requestData)
  })
}

/**
 * Schedule deletion of the current user's account
 * @param password - Current password confirming the deletion request
 * @param revokeSharedCorrections - Whether to also withdraw the user's
 * shared correction contributions when the account is deleted
 * @returns Promise with the scheduled deletion timestamp
 */
export async function deleteAccount(
  password: string,
  revokeSharedCorrections: boolean = false
): Promise<AccountDeletionResponse> {
  const requestData: AccountDeletionRequest = {
    password,
    revoke_shared_corrections: revokeSharedCorrections
  }
  return request<AccountDeletionResponse>(getApiUrl('/auth/account'), {
    method: 'DELETE',
    body: JSON.stringify(requestData)
  })
}

/**
 * Change the current user's username (right to rectification)
 * @param username - New unique username
 * @returns Promise with the updated user
 */
export async function updateUsername(username: string): Promise<UpdateMeResponse> {
  const requestData: UpdateMeRequest = { username }
  return request<UpdateMeResponse>(getApiUrl('/auth/me'), {
    method: 'PUT',
    body: JSON.stringify(requestData)
  })
}

/**
 * Change the current user's password while logged in
 * @param currentPassword - Current password confirming the change
 * @param newPassword - New password (minimum 12 characters)
 * @returns Promise with a confirmation message
 */
export async function changePassword(
  currentPassword: string,
  newPassword: string
): Promise<ChangePasswordResponse> {
  const requestData: ChangePasswordRequest = {
    current_password: currentPassword,
    new_password: newPassword
  }
  return request<ChangePasswordResponse>(getApiUrl('/auth/me/password'), {
    method: 'PUT',
    body: JSON.stringify(requestData)
  })
}

/**
 * Export all personal data of the current user (data portability)
 * @returns Promise with the machine-readable export document
 */
export async function exportMyData(): Promise<DataExportResponse> {
  return request<DataExportResponse>(getApiUrl('/auth/me/export'))
}

/**
 * Regenerate the current user's recovery code while logged in
 * @param password - Current password confirming the regeneration
 * @returns Promise with the new recovery code (displayed once)
 */
export async function regenerateRecoveryCode(
  password: string
): Promise<RegenerateRecoveryCodeResponse> {
  const requestData: RegenerateRecoveryCodeRequest = { password }
  return request<RegenerateRecoveryCodeResponse>(
    getApiUrl('/auth/me/recovery-code'),
    {
      method: 'POST',
      body: JSON.stringify(requestData)
    }
  )
}
