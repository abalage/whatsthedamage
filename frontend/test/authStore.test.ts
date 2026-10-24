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
