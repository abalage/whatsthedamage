/**
 * Plain CSRF token holder shared by the auth store and the API client.
 *
 * The store (and the API client's retry path) writes the token; the
 * API client reads it. This breaks the store -> api.ts -> store
 * cycle without dynamic imports. The token is persisted in
 * localStorage so page reloads and tabs reuse the same token instead
 * of forcing the backend to mint (and rotate) a new one.
 * @module utils/csrfToken
 */

const CSRF_TOKEN_STORAGE_KEY = 'csrfToken';

let csrfToken: string | undefined = localStorage.getItem(CSRF_TOKEN_STORAGE_KEY) ?? undefined;

/**
 * Set the CSRF token and persist it.
 *
 * @param token - New CSRF token, or undefined to clear it
 */
export function setCsrfToken(token: string | undefined): void {
  csrfToken = token;
  if (token) {
    localStorage.setItem(CSRF_TOKEN_STORAGE_KEY, token);
  } else {
    localStorage.removeItem(CSRF_TOKEN_STORAGE_KEY);
  }
}

/**
 * Get the current CSRF token.
 *
 * @returns The CSRF token, or undefined when none is stored
 */
export function getCsrfToken(): string | undefined {
  return csrfToken;
}
