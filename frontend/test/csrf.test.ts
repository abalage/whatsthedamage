/**
 * Unit tests for CSRF token handling: persistence in the auth store and
 * transparent retry of state-changing requests after a rejected token
 * @module test/csrf
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { createPinia, setActivePinia } from 'pinia';
import { useAuthStore } from '../src/stores/auth.js';
import { login, getMe, fetchCsrfToken } from '../src/js/api.js';
import { recalculateStatistics } from '../src/js/api.js';

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
  fetchMock.mock.calls.map(([url, init]) => ({
    url: String(url),
    init: (init ?? {}) as RequestInit
  }));

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
  localStorage.clear();
  setActivePinia(createPinia());
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('auth store CSRF token handling', () => {
  it('persists the csrf_token from the login response', async () => {
    const fetchMock = vi.fn(async (_url?: unknown): Promise<FetchResponse> =>
      makeResponse({ user, csrf_token: 'login-token', session_expires_at: '2026-01-01T00:00:00Z' })
    );
    vi.stubGlobal('fetch', fetchMock);

    const authStore = useAuthStore();
    await authStore.login('testuser', 'password', false);

    expect(authStore.getCsrfToken()).toBe('login-token');
    expect(localStorage.getItem('csrfToken')).toBe('login-token');
  });

  it('persists the csrf_token from the register response', async () => {
    const fetchMock = vi.fn(async (_url?: unknown): Promise<FetchResponse> =>
      makeResponse({
        user,
        recovery_code: 'abcd-efgh-ijkl-mnop',
        csrf_token: 'register-token',
        session_expires_at: '2026-01-01T00:00:00Z'
      }, true, 200)
    );
    vi.stubGlobal('fetch', fetchMock);

    const authStore = useAuthStore();
    await authStore.register('newuser', 'secure_password_1');

    expect(authStore.getCsrfToken()).toBe('register-token');
    expect(localStorage.getItem('csrfToken')).toBe('register-token');
  });

  it('refreshCsrfToken mints via /auth/csrf-token and persists', async () => {
    const fetchMock = vi.fn(async (_url?: unknown): Promise<FetchResponse> => makeResponse({ csrf_token: 'minted-token' }));
    vi.stubGlobal('fetch', fetchMock);

    const authStore = useAuthStore();
    await authStore.refreshCsrfToken();

    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(String(fetchMock.mock.calls[0][0])).toContain('/api/v2/auth/csrf-token');
    expect(authStore.getCsrfToken()).toBe('minted-token');
    expect(localStorage.getItem('csrfToken')).toBe('minted-token');
  });

  it('initialize keeps the persisted token when /auth/me returns none', async () => {
    localStorage.setItem('csrfToken', 'persisted-token');
    const fetchMock = vi.fn(async (_url?: unknown): Promise<FetchResponse> => makeResponse({ user, csrf_token: null }));
    vi.stubGlobal('fetch', fetchMock);

    const authStore = useAuthStore();
    await authStore.initialize();

    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(String(fetchMock.mock.calls[0][0])).toContain('/api/v2/auth/me');
    expect(authStore.getCsrfToken()).toBe('persisted-token');
  });

  it('initialize mints a token when the session has one but the client does not', async () => {
    const fetchMock = vi.fn(async (url?: unknown): Promise<FetchResponse> => {
      const urlStr = String(url);
      if (urlStr.includes('/auth/csrf-token')) {
        return makeResponse({ csrf_token: 'minted-token' });
      }
      return makeResponse({ user, csrf_token: null });
    });
    vi.stubGlobal('fetch', fetchMock);

    const authStore = useAuthStore();
    await authStore.initialize();

    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(String(fetchMock.mock.calls[1][0])).toContain('/api/v2/auth/csrf-token');
    expect(authStore.getCsrfToken()).toBe('minted-token');
    expect(localStorage.getItem('csrfToken')).toBe('minted-token');
  });

  it('logout clears the persisted token', async () => {
    localStorage.setItem('csrfToken', 'persisted-token');
    const fetchMock = vi.fn(async (_url?: unknown): Promise<FetchResponse> => makeResponse({ message: 'Successfully logged out' }));
    vi.stubGlobal('fetch', fetchMock);

    const authStore = useAuthStore();
    await authStore.logout();

    expect(authStore.getCsrfToken()).toBeNull();
    expect(localStorage.getItem('csrfToken')).toBeNull();
  });
});

describe('fetchWithCsrf stale token retry', () => {
  it('retries a request once with a fresh token after a rejected one', async () => {
    const authStore = useAuthStore();
    authStore.csrfToken = 'stale-token';

    const responses: FetchResponse[] = [
      makeResponse({ error: 'Invalid CSRF token' }, false, 403),
      makeResponse({ csrf_token: 'fresh-token' }),
      makeResponse({ result_id: null, highlights: {}, algorithms: ['iqr'], direction: 'columns' })
    ];
    const fetchMock = vi.fn(async (_url?: unknown): Promise<FetchResponse> => responses.shift() ?? makeResponse({}));
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
    expect(authStore.getCsrfToken()).toBe('fresh-token');
  });

  it('does not retry twice on repeated rejection', async () => {
    const authStore = useAuthStore();
    authStore.csrfToken = 'stale-token';

    const responses: FetchResponse[] = [
      makeResponse({ error: 'Invalid CSRF token' }, false, 403),
      makeResponse({ csrf_token: 'fresh-token' }),
      makeResponse({ error: 'Invalid CSRF token' }, false, 403),
      makeResponse({ csrf_token: 'another-token' })
    ];
    const fetchMock = vi.fn(async (_url?: unknown): Promise<FetchResponse> => responses.shift() ?? makeResponse({}));
    vi.stubGlobal('fetch', fetchMock);

    await expect(
      recalculateStatistics(undefined, ['iqr'], 'columns')
    ).rejects.toThrow('Invalid CSRF token');

    expect(fetchMock).toHaveBeenCalledTimes(3);
  });

  it('does not retry unrelated 403 errors', async () => {
    const authStore = useAuthStore();
    authStore.csrfToken = 'valid-token';

    const fetchMock = vi.fn(async (_url?: unknown): Promise<FetchResponse> =>
      makeResponse({ error: 'Session has no CSRF token' }, false, 403)
    );
    vi.stubGlobal('fetch', fetchMock);

    await expect(
      recalculateStatistics(undefined, ['iqr'], 'columns')
    ).rejects.toThrow('Session has no CSRF token');

    expect(fetchMock).toHaveBeenCalledTimes(1);
  });
});

describe('api csrf functions', () => {
  it('fetchCsrfToken calls the explicit mint endpoint', async () => {
    const fetchMock = vi.fn(async (_url?: unknown): Promise<FetchResponse> => makeResponse({ csrf_token: 'minted-token' }));
    vi.stubGlobal('fetch', fetchMock);

    const response = await fetchCsrfToken();

    expect(String(fetchMock.mock.calls[0][0])).toContain('/api/v2/auth/csrf-token');
    expect(response.csrf_token).toBe('minted-token');
  });

  it('getMe returns a nullable csrf_token', async () => {
    const fetchMock = vi.fn(async (_url?: unknown): Promise<FetchResponse> => makeResponse({ user, csrf_token: null }));
    vi.stubGlobal('fetch', fetchMock);

    const response = await getMe();

    expect(response.csrf_token).toBeNull();
    expect(response.user.username).toBe('testuser');
  });

  it('login response carries the csrf_token', async () => {
    const fetchMock = vi.fn(async (_url?: unknown): Promise<FetchResponse> =>
      makeResponse({ user, csrf_token: 'login-token', session_expires_at: '2026-01-01T00:00:00Z' })
    );
    vi.stubGlobal('fetch', fetchMock);

    const response = await login('testuser', 'password', false);

    expect(response.csrf_token).toBe('login-token');
  });
});
