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
 * Contains user data, recovery code (displayed once), and session info.
 * Note: sessionToken removed for security - only available in HttpOnly cookie
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
 * Contains user data and session info.
 * Note: sessionToken removed for security - only available in HttpOnly cookie
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
 * Contains current user info and a CSRF token.
 */
export interface MeResponse {
  user: User;
  csrf_token: string;
}

/**
 * Response from /auth/csrf-token endpoint.
 * Contains only a CSRF token.
 */
export interface CsrfTokenResponse {
  csrf_token: string;
}

/**
 * Authentication state stored in Pinia.
 */
export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  csrfToken: string | null;
  recoveryCode: string | null;
  showRecoveryCode: boolean;
  recoveryCodeAcknowledged: boolean;
}

/**
 * API error response structure.
 */
interface AuthError {
  error: string;
  code?: string;
  retryAfter?: number;
}

/**
 * Combined API response wrapper.
 */
interface ApiAuthResponse<T> {
  data?: T;
  error?: string;
  code?: string;
  retryAfter?: number;
}

/**
 * Credentials for login/register forms.
 */
interface Credentials {
  username: string;
  password: string;
}

/**
 * Form data for registration with password confirmation.
 */
interface RegistrationForm {
  username: string;
  password: string;
  confirmPassword: string;
}

/**
 * Form data for login with remember me option.
 */
interface LoginForm {
  username: string;
  password: string;
  rememberMe: boolean;
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
