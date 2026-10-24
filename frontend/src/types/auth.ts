/**
 * Authentication-related TypeScript types and interfaces.
 *
 * Defines the data structures used for authentication API requests and responses.
 */

/**
 * User data structure returned from the API.
 */
export interface User {
  id: number;
  username: string;
  created_at?: string | null;
  last_login_at?: string | null;
  is_active: boolean;
  opt_in_sharing: boolean;
  opted_in_at?: string | null;
  opted_out_at?: string | null;
  scheduled_deletion_at?: string | null;
}

/**
 * Request body for user registration.
 */
export interface RegisterRequest {
  username: string;
  password: string;
}

/**
 * Response from successful registration.
 * Contains user data and recovery code (displayed once). The session
 * and CSRF tokens are only available in cookies set by the backend.
 */
export interface RegisterResponse {
  user: User;
  recovery_code: string;
  session_expires_at: string;
}

/**
 * Request body for user login.
 */
export interface LoginRequest {
  username: string;
  password: string;
  rememberMe?: boolean;
}

/**
 * Response from successful login.
 * Contains user data. The session and CSRF tokens are only available
 * in cookies set by the backend.
 */
export interface LoginResponse {
  user: User;
  session_expires_at: string;
}

/**
 * Response from successful logout.
 */
export interface LogoutResponse {
  message: string;
}

/**
 * Response from /auth/me endpoint.
 * Contains current user info. A fresh CSRF cookie is set when the
 * session does not have a token yet.
 */
export interface MeResponse {
  user: User;
}

/**
 * Request body for updating user settings via PUT /auth/me.
 * At least one field must be present.
 */
export interface UpdateMeRequest {
  opt_in_sharing?: boolean;
  username?: string;
}

/**
 * Response from successful settings update.
 * Contains the updated user data.
 */
export interface UpdateMeResponse {
  user: User;
}

/**
 * Request body for password reset using recovery code.
 */
export interface PasswordResetRequest {
  username: string;
  recoveryCode: string;
  newPassword: string;
}

/**
 * Response from successful password reset.
 * Contains user data and the new recovery code (displayed once).
 */
export interface PasswordResetResponse {
  user: User;
  new_recovery_code: string;
}

/**
 * Request body for scheduling account deletion via DELETE /auth/account.
 */
export interface AccountDeletionRequest {
  password: string;
  revoke_shared_corrections?: boolean;
}

/**
 * Response from scheduling account deletion.
 * Contains the UTC timestamp after which the account is deleted.
 */
export interface AccountDeletionResponse {
  message: string;
  scheduled_deletion_at: string;
}

/**
 * Request body for changing the password while logged in
 * via PUT /auth/me/password.
 */
export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
}

/**
 * Response from a successful password change.
 */
export interface ChangePasswordResponse {
  message: string;
}

/**
 * A processing result as included in the data export.
 */
interface ExportedProcessingResult {
  result_id: string | null;
  csv_profile_id: string;
  row_count: number;
  processing_time: number;
  ml_enabled: boolean;
  start_date: string | null;
  end_date: string | null;
  created_at: string | null;
}

/**
 * A transaction as included in the data export.
 */
interface ExportedTransaction {
  id: number | null;
  result_id: string | null;
  date: string | null;
  transaction_type: string | null;
  original_partner: string | null;
  amount: number | null;
  currency: string | null;
  account: string | null;
  category_id: string | null;
  partner: string | null;
  notice: string | null;
  confidence: number | null;
  original_category_id: string | null;
  original_notice: string | null;
  created_at: string | null;
  updated_at: string | null;
}

/**
 * A correction as included in the data export.
 */
interface ExportedCorrection {
  id: number | null;
  original_partner: string;
  corrected_partner: string | null;
  corrected_category_id: string;
  created_at: string | null;
  updated_at: string | null;
}

/**
 * Response from GET /auth/me/export (data portability).
 */
export interface DataExportResponse {
  generated_at: string;
  account: User;
  processing_results: ExportedProcessingResult[];
  transactions: ExportedTransaction[];
  corrections: ExportedCorrection[];
}
