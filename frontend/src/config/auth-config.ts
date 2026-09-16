/**
 * Authentication configuration for frontend.
 *
 * Centralized configuration values for authentication-related settings.
 * These should match the backend configuration values.
 */

/**
 * Authentication configuration.
 */
interface AuthConfig {
  passwordMinLength: number;
  recoveryCodeLength: number;
  usernameMaxLength: number;
}

/**
 * Default authentication configuration.
 * Can be overridden by importing and modifying.
 */
const authConfig: AuthConfig = {
  // Minimum password length - should match backend PASSWORD_MIN_LENGTH
  passwordMinLength: 12,

  // Recovery code length - should match backend RECOVERY_CODE_LENGTH
  recoveryCodeLength: 16,

  // Maximum username length
  usernameMaxLength: 255,
};

/**
 * Get password minimum length from environment or use default.
 * This allows the frontend to use the same minimum length as the backend.
 */
export function getPasswordMinLength(): number {
  const envValue = import.meta.env.VITE_PASSWORD_MIN_LENGTH;
  if (envValue) {
    const parsed = parseInt(envValue, 10);
    if (!isNaN(parsed) && parsed > 0) {
      return parsed;
    }
  }
  return authConfig.passwordMinLength;
}

/**
 * Get recovery code length from environment or use default.
 */
function getRecoveryCodeLength(): number {
  const envValue = import.meta.env.VITE_RECOVERY_CODE_LENGTH;
  if (envValue) {
    const parsed = parseInt(envValue, 10);
    if (!isNaN(parsed) && parsed > 0) {
      return parsed;
    }
  }
  return authConfig.recoveryCodeLength;
}
