/**
 * Application version information
 * @module utils/version
 */

/**
 * The current application version, sourced from build-time environment variable.
 * Falls back to '1.0.0' if not provided.
 */
export const APP_VERSION = import.meta.env.VITE_APP_VERSION ?? '1.0.0';
