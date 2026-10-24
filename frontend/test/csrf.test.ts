/**
 * Unit tests for CSRF token handling: cookie reading, minting via the
 * explicit endpoint, and transparent retry of state-changing requests
 * after a rejected token
 * @module test/csrf
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { createPinia, setActivePinia } from 'pinia';
import { useAuthStore } from '../src/stores/auth';
import { getCsrfToken } from '../src/js/csrfToken';
import { recalculateStatistics } from '../src/js/api';

type FetchResponse = {
  ok: boolean;
  status: number;
  statusText: string;
  json: () => Promise<unknown>;
};

const makeResponse = (data: unknown, ok = true, status = 200): FetchResponse => ({
  ok,
  status,
  statusText: ok ? 'OK' : 'Error',
  json: async () => data,
});

const fetchCalls = (fetchMock: ReturnType<typeof vi.fn>): Array<{ url: string; init: RequestInit }> =>
  fetchMock.mock.calls.map(([url, init]) => ({ url: String(url), init: (init ?? {}) as RequestInit }));

const setCookie = (value: string | undefined): void => {
  document.cookie = 'csrf_token=; expires=Thu, 01 Jan 1970 00:00:00 GMT';
  if (value) {
    document.cookie = `csrf_token=${value}`;
  }
};

const user = {
  id: 1,
  username: 'testuser',
  created_at: null,
  last_login_at: null,
  is_active: true,
  opt_in_sharing: false
};

beforeEach(() => {
  vi.clearAllMocks();
  setCookie(undefined);
  setActivePinia(createPinia());
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('csrf cookie reader', () => {
  it('reads the token from the csrf_token cookie', () => {
    setCookie('cookie-token');
    expect(getCsrfToken()).toBe('cookie-token');
  });

  it('returns undefined when the cookie is absent', () => {
    expect(getCsrfToken()).toBeUndefined();
  });

  it('finds the token among other cookies', () => {
    document.cookie = 'other=value';
    document.cookie = 'csrf_token=the-token';
    expect(getCsrfToken()).toBe('the-token');
  });
});

describe('auth store CSRF token handling', () => {
  it('login uses the token from the cookie, not localStorage', async () => {
    const fetchMock = vi.fn(async (_url?: unknown): Promise<FetchResponse> => {
      // The login response carries Set-Cookie: csrf_token=login-token;
      // emulate the browser storing it
      setCookie('login-token');
      return makeResponse({ user, session_expires_at: '2026-01-01T00:00:00Z' });
    });
    vi.stubGlobal('fetch', fetchMock);

    const authStore = useAuthStore();
    await authStore.login('testuser', 'password', false);

    expect(authStore.isAuthenticated).toBe(true);
    expect(getCsrfToken()).toBe('login-token');
    expect(localStorage.getItem('csrfToken')).toBeNull();
  });

  it('refreshCsrfToken mints via /auth/csrf-token and reads the cookie', async () => {
    const fetchMock = vi.fn(async (_url?: unknown): Promise<FetchResponse> => {
      setCookie('minted-token');
      return makeResponse({});
    });
    vi.stubGlobal('fetch', fetchMock);

    const authStore = useAuthStore();
    await authStore.refreshCsrfToken();

    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(String(fetchMock.mock.calls[0][0])).toContain('/api/v2/auth/csrf-token');
    expect(getCsrfToken()).toBe('minted-token');
  });

  it('initialize keeps the cookie token when one is present', async () => {
    setCookie('persisted-token');
    const fetchMock = vi.fn(async (_url?: unknown): Promise<FetchResponse> => makeResponse({ user }));
    vi.stubGlobal('fetch', fetchMock);

    const authStore = useAuthStore();
    await authStore.initialize();

    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(String(fetchMock.mock.calls[0][0])).toContain('/api/v2/auth/me');
    expect(getCsrfToken()).toBe('persisted-token');
  });

  it('initialize mints a token when the browser has no cookie', async () => {
    const fetchMock = vi.fn(async (url?: unknown): Promise<FetchResponse> => {
      const urlStr = String(url);
      if (urlStr.includes('/auth/csrf-token')) {
        setCookie('minted-token');
        return makeResponse({});
      }
      return makeResponse({ user });
    });
    vi.stubGlobal('fetch', fetchMock);

    const authStore = useAuthStore();
    await authStore.initialize();

    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(String(fetchMock.mock.calls[1][0])).toContain('/api/v2/auth/csrf-token');
    expect(getCsrfToken()).toBe('minted-token');
  });

  it('initialize stays authenticated when the mint fails', async () => {
    const fetchMock = vi.fn(async (url?: unknown): Promise<FetchResponse> => {
      const urlStr = String(url);
      if (urlStr.includes('/auth/csrf-token')) {
        return makeResponse({ error: 'No session found' }, false, 401);
      }
      return makeResponse({ user });
    });
    vi.stubGlobal('fetch', fetchMock);

    const authStore = useAuthStore();
    await authStore.initialize();

    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(authStore.isAuthenticated).toBe(true);
  });
});

describe('stale CSRF token retry', () => {
  it('retries a request once with a fresh cookie token after a rejected one', async () => {
    setCookie('stale-token');

    const responses: FetchResponse[] = [
      makeResponse({ error: 'Invalid CSRF token', code: 'CSRF_TOKEN_INVALID' }, false, 403),
      makeResponse({}),
      makeResponse({ result_id: null, highlights: {}, algorithms: ['iqr'], direction: 'columns' })
    ];
    const fetchMock = vi.fn(async (_url?: unknown): Promise<FetchResponse> => {
      const response = responses.shift() ?? makeResponse({});
      // The mint response carries Set-Cookie: csrf_token=fresh-token;
      // emulate the browser storing it
      if (responses.length === 1) {
        setCookie('fresh-token');
      }
      return response;
    });
    vi.stubGlobal('fetch', fetchMock);

    const result = await recalculateStatistics(undefined, ['iqr'], 'columns');

    expect(fetchMock).toHaveBeenCalledTimes(3);

    const calls = fetchCalls(fetchMock);
    expect(calls[0].url).toContain('/api/v2/recalculate-statistics');
    const firstHeaders = calls[0].init.headers as Record<string, string>;
    expect(firstHeaders['X-CSRF-Token']).toBe('stale-token');

    expect(calls[1].url).toContain('/api/v2/auth/csrf-token');

    expect(calls[2].url).toContain('/api/v2/recalculate-statistics');
    const retryHeaders = calls[2].init.headers as Record<string, string>;
    expect(retryHeaders['X-CSRF-Token']).toBe('fresh-token');

    expect(result.highlights).toEqual({});
    expect(getCsrfToken()).toBe('fresh-token');
  });

  it('does not retry twice on repeated rejection', async () => {
    setCookie('stale-token');

    const responses: FetchResponse[] = [
      makeResponse({ error: 'Invalid CSRF token', code: 'CSRF_TOKEN_INVALID' }, false, 403),
      makeResponse({}),
      makeResponse({ error: 'Invalid CSRF token', code: 'CSRF_TOKEN_INVALID' }, false, 403)
    ];
    const fetchMock = vi.fn(async (_url?: unknown): Promise<FetchResponse> => {
      const response = responses.shift() ?? makeResponse({});
      if (responses.length === 1) {
        setCookie('fresh-token');
      }
      return response;
    });
    vi.stubGlobal('fetch', fetchMock);

    await expect(
      recalculateStatistics(undefined, ['iqr'], 'columns')
    ).rejects.toThrow('Invalid CSRF token');

    expect(fetchMock).toHaveBeenCalledTimes(3);
  });

  it('does not retry unrelated 403 errors', async () => {
    setCookie('valid-token');

    const fetchMock = vi.fn(async (_url?: unknown): Promise<FetchResponse> =>
      makeResponse({ error: 'Session has no CSRF token', code: 'CSRF_TOKEN_NOT_SET' }, false, 403)
    );
    vi.stubGlobal('fetch', fetchMock);

    await expect(
      recalculateStatistics(undefined, ['iqr'], 'columns')
    ).rejects.toThrow('Session has no CSRF token');

    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it('does not retry a 403 without the CSRF_TOKEN_INVALID code', async () => {
    setCookie('valid-token');

    const fetchMock = vi.fn(async (_url?: unknown): Promise<FetchResponse> =>
      makeResponse({ error: 'Invalid CSRF token' }, false, 403)
    );
    vi.stubGlobal('fetch', fetchMock);

    await expect(
      recalculateStatistics(undefined, ['iqr'], 'columns')
    ).rejects.toThrow('Invalid CSRF token');

    expect(fetchMock).toHaveBeenCalledTimes(1);
  });
});
