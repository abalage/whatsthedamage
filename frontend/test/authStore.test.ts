/**
 * Unit tests for the auth store's account deletion handling: local
 * state is cleared only when the backend confirms the deletion
 * @module test/authStore
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { createPinia, setActivePinia } from 'pinia';
import { useAuthStore } from '../src/stores/auth';
import { useDatasetStore } from '../src/stores/dataset';

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
  setActivePinia(createPinia());
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('auth store account deletion', () => {
  it('keeps the user and cached datasets when the deletion request fails', async () => {
    const fetchMock = vi.fn(async (): Promise<FetchResponse> =>
      makeResponse({ error: 'Invalid password', code: 'INVALID_CREDENTIALS' }, false, 403)
    );
    vi.stubGlobal('fetch', fetchMock);

    const authStore = useAuthStore();
    authStore.user = user;
    const invalidateAll = vi.spyOn(useDatasetStore(), 'invalidateAll');

    await expect(authStore.requestAccountDeletion('wrong-password')).rejects.toThrow('Invalid password');

    expect(authStore.isAuthenticated).toBe(true);
    expect(authStore.error).toBe('Invalid password');
    expect(invalidateAll).not.toHaveBeenCalled();
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it('clears the user and cached datasets when the deletion succeeds', async () => {
    const fetchMock = vi.fn(async (_url?: unknown, _init?: RequestInit): Promise<FetchResponse> =>
      makeResponse({ scheduled_deletion_at: '2026-11-01T00:00:00Z' })
    );
    vi.stubGlobal('fetch', fetchMock);

    const authStore = useAuthStore();
    authStore.user = user;
    const invalidateAll = vi.spyOn(useDatasetStore(), 'invalidateAll');

    const scheduledAt = await authStore.requestAccountDeletion('correct-password');

    expect(scheduledAt).toBe('2026-11-01T00:00:00Z');
    expect(authStore.isAuthenticated).toBe(false);
    expect(invalidateAll).toHaveBeenCalledTimes(1);
    expect(String(fetchMock.mock.calls[0][0])).toContain('/api/v2/auth/account');
    expect((fetchMock.mock.calls[0][1] as RequestInit).method).toBe('DELETE');
  });
});

describe('auth store recovery code regeneration', () => {
  it('returns the new code and does not touch the registration recovery state', async () => {
    const fetchMock = vi.fn(async (_url?: unknown, _init?: RequestInit): Promise<FetchResponse> =>
      makeResponse({ new_recovery_code: 'ABCD-EFGH-IJKL-MNOP' })
    );
    vi.stubGlobal('fetch', fetchMock);

    const authStore = useAuthStore();
    authStore.user = user;

    const code = await authStore.regenerateUserRecoveryCode('correct-password');

    expect(code).toBe('ABCD-EFGH-IJKL-MNOP');
    // The registration-specific state must remain untouched
    expect(authStore.recoveryCode).toBeNull();
    expect(authStore.showRecoveryCode).toBe(false);
    expect(String(fetchMock.mock.calls[0][0])).toContain('/api/v2/auth/me/recovery-code');
    expect((fetchMock.mock.calls[0][1] as RequestInit).method).toBe('POST');
    const body = JSON.parse((fetchMock.mock.calls[0][1] as RequestInit).body as string);
    expect(body).toEqual({ password: 'correct-password' });
  });

  it('propagates errors from the API', async () => {
    const fetchMock = vi.fn(async (): Promise<FetchResponse> =>
      makeResponse({ message: 'Invalid current password', code: 'INVALID_CREDENTIALS' }, false, 401)
    );
    vi.stubGlobal('fetch', fetchMock);

    const authStore = useAuthStore();
    authStore.user = user;

    await expect(authStore.regenerateUserRecoveryCode('wrong-password')).rejects.toThrow('Invalid current password');
    expect(authStore.error).toBe('Invalid current password');
  });
});

describe('auth store two-phase registration', () => {
  const pendingResponse = {
    pending_token: 'pending-token-123',
    recovery_code: 'ABCD-EFGH-JKLM-NPQR',
    expires_at: '2026-11-04T14:00:00Z'
  };

  beforeEach(() => {
    sessionStorage.clear();
  });

  it('phase 1 stores pending state without authenticating and persists it to sessionStorage', async () => {
    const fetchMock = vi.fn(async (_url?: unknown, _init?: RequestInit): Promise<FetchResponse> => makeResponse(pendingResponse));
    vi.stubGlobal('fetch', fetchMock);

    const authStore = useAuthStore();
    const result = await authStore.register('newuser', 'long-enough-password');

    expect(result).toEqual({ pendingToken: 'pending-token-123', recoveryCode: 'ABCD-EFGH-JKLM-NPQR' });
    expect(authStore.isAuthenticated).toBe(false);
    expect(authStore.user).toBeNull();
    expect(authStore.showRecoveryCode).toBe(true);
    expect(authStore.pendingToken).toBe('pending-token-123');
    expect(authStore.recoveryCode).toBe('ABCD-EFGH-JKLM-NPQR');
    expect(sessionStorage.getItem('pending_registration_token')).toBe('pending-token-123');
    expect(sessionStorage.getItem('pending_registration_recovery_code')).toBe('ABCD-EFGH-JKLM-NPQR');
    expect(String(fetchMock.mock.calls[0][0])).toContain('/api/v2/auth/register');
    const body = JSON.parse((fetchMock.mock.calls[0][1] as RequestInit).body as string);
    expect(body).toEqual({ username: 'newuser', password: 'long-enough-password' });
  });

  it('phase 2 confirms with the echoed code, authenticates, and clears all copies of the code', async () => {
    let confirmBody: string | undefined;
    const fetchMock = vi.fn(async (_url?: unknown, init?: RequestInit): Promise<FetchResponse> => {
      const url = String(_url);
      if (url.includes('/auth/register/confirm')) {
        confirmBody = init?.body as string;
        return makeResponse({ user, session_expires_at: '2026-11-04T14:00:00Z' });
      }
      return makeResponse(pendingResponse);
    });
    vi.stubGlobal('fetch', fetchMock);

    const authStore = useAuthStore();
    await authStore.register('newuser', 'long-enough-password');
    const confirmed = await authStore.confirmRegistration();

    expect(confirmed.username).toBe('testuser');
    expect(authStore.isAuthenticated).toBe(true);
    expect(authStore.recoveryCode).toBeNull();
    expect(authStore.showRecoveryCode).toBe(false);
    expect(authStore.pendingToken).toBeUndefined();
    expect(sessionStorage.getItem('pending_registration_token')).toBeNull();
    expect(sessionStorage.getItem('pending_registration_recovery_code')).toBeNull();

    expect(JSON.parse(confirmBody ?? '')).toEqual({
      pending_token: 'pending-token-123',
      recovery_code: 'ABCD-EFGH-JKLM-NPQR'
    });
  });

  it('phase 2 failure clears the pending state so the user can register again', async () => {
    const fetchMock = vi.fn(async (_url?: unknown): Promise<FetchResponse> => {
      const url = String(_url);
      if (url.includes('/auth/register/confirm')) {
        return makeResponse({ error: 'Invalid or expired registration', code: 'REGISTRATION_INVALID' }, false, 401);
      }
      return makeResponse(pendingResponse);
    });
    vi.stubGlobal('fetch', fetchMock);

    const authStore = useAuthStore();
    await authStore.register('newuser', 'long-enough-password');

    await expect(authStore.confirmRegistration()).rejects.toThrow();
    expect(authStore.error).toBeTruthy();
    expect(authStore.showRecoveryCode).toBe(false);
    expect(authStore.pendingToken).toBeUndefined();
    expect(authStore.recoveryCode).toBeNull();
    expect(sessionStorage.getItem('pending_registration_token')).toBeNull();
  });

  it('initialize rehydrates a pending registration from sessionStorage when not authenticated', async () => {
    sessionStorage.setItem('pending_registration_token', 'stored-token');
    sessionStorage.setItem('pending_registration_recovery_code', 'STORED-CODE-1234-ABCD');
    const fetchMock = vi.fn(async (): Promise<FetchResponse> =>
      makeResponse({ error: 'No session found', code: 'NOT_AUTHENTICATED' }, false, 401)
    );
    vi.stubGlobal('fetch', fetchMock);

    const authStore = useAuthStore();
    await authStore.initialize();

    expect(authStore.isAuthenticated).toBe(false);
    expect(authStore.showRecoveryCode).toBe(true);
    expect(authStore.pendingToken).toBe('stored-token');
    expect(authStore.recoveryCode).toBe('STORED-CODE-1234-ABCD');
  });

  it('initialize clears stale pending state when a confirmed session exists', async () => {
    sessionStorage.setItem('pending_registration_token', 'stored-token');
    sessionStorage.setItem('pending_registration_recovery_code', 'STORED-CODE-1234-ABCD');
    const fetchMock = vi.fn(async (): Promise<FetchResponse> => makeResponse({ user }));
    vi.stubGlobal('fetch', fetchMock);

    const authStore = useAuthStore();
    await authStore.initialize();

    expect(authStore.isAuthenticated).toBe(true);
    expect(authStore.showRecoveryCode).toBe(false);
    expect(authStore.pendingToken).toBeUndefined();
    expect(authStore.recoveryCode).toBeNull();
    expect(sessionStorage.getItem('pending_registration_token')).toBeNull();
  });

  it('logout clears the pending registration state', async () => {
    const fetchMock = vi.fn(async (_url?: unknown): Promise<FetchResponse> => {
      const url = String(_url);
      if (url.includes('/auth/logout')) {
        return makeResponse({ message: 'Successfully logged out' });
      }
      return makeResponse(pendingResponse);
    });
    vi.stubGlobal('fetch', fetchMock);

    const authStore = useAuthStore();
    await authStore.register('newuser', 'long-enough-password');
    expect(authStore.showRecoveryCode).toBe(true);

    await authStore.logout();

    expect(authStore.showRecoveryCode).toBe(false);
    expect(authStore.pendingToken).toBeUndefined();
    expect(authStore.recoveryCode).toBeNull();
    expect(sessionStorage.getItem('pending_registration_token')).toBeNull();
    expect(sessionStorage.getItem('pending_registration_recovery_code')).toBeNull();
  });
});
