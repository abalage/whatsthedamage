/**
 * CSRF token reader.
 *
 * The backend delivers the token as a readable (not HttpOnly) cookie
 * set by the auth endpoints and /auth/csrf-token; the SPA reads it
 * from document.cookie and echoes it back in the X-CSRF-Token
 * header. The token is not persisted anywhere else: its lifetime is
 * tied to the session, and every tab of the origin sees a rotated
 * token immediately because the browser shares cookies.
 *
 * Trust note: the cookie is not HttpOnly, so XSS can read it - but
 * an XSS payload can already drive requests as the user in-page, so
 * readability adds no new capability.
 * @module utils/csrfToken
 */

const CSRF_COOKIE_NAME = 'csrf_token';

/**
 * Get the current CSRF token from the cookie.
 *
 * @returns The CSRF token, or undefined when the cookie is absent
 */
export function getCsrfToken(): string | undefined {
  const prefix = `${CSRF_COOKIE_NAME}=`;
  for (const part of document.cookie.split(';')) {
    const entry = part.trimStart();
    if (entry.startsWith(prefix)) {
      return entry.slice(prefix.length);
    }
  }
  return undefined;
}
