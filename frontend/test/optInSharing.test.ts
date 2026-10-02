/**
 * Unit tests for the auth store's sharing opt-in handling
 * @module test/optInSharing
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { createPinia, setActivePinia } from 'pinia';
import { useAuthStore } from '../src/stores/auth.js';

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
  opt_in_sharing: false,
};

beforeEach(() => {
  vi.clearAllMocks();
  localStorage.clear();
  setActivePinia(createPinia());
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('auth store sharing opt-in handling', () => {
  it('setOptInSharing updates the user preference on success', async () => {
    const fetchMock = vi.fn(async (_url?: unknown): Promise<FetchResponse> =>
      makeResponse({ user: { ...user, opt_in_sharing: true } })
    );
    vi.stubGlobal('fetch', fetchMock);

    const authStore = useAuthStore();
    authStore.user = { ...user };

    const updated = await authStore.setOptInSharing(true);

    expect(String(fetchMock.mock.calls[0][0])).toContain('/api/v2/auth/me');
    expect(updated.opt_in_sharing).toBe(true);
    expect(authStore.user?.opt_in_sharing).toBe(true);
  });

  it('setOptInSharing keeps the old value and sets error on failure', async () => {
    const fetchMock = vi.fn(async (_url?: unknown): Promise<FetchResponse> =>
      makeResponse({ error: 'opt_in_sharing must be a boolean' }, false, 400)
    );
    vi.stubGlobal('fetch', fetchMock);

    const authStore = useAuthStore();
    authStore.user = { ...user };

    await expect(authStore.setOptInSharing(true)).rejects.toThrow('opt_in_sharing must be a boolean');

    expect(authStore.user?.opt_in_sharing).toBe(false);
    expect(authStore.error).toBe('opt_in_sharing must be a boolean');
    expect(authStore.isLoading).toBe(false);
  });

  it('setOptInSharing does not overwrite a missing user on failure', async () => {
    const fetchMock = vi.fn(async (_url?: unknown): Promise<FetchResponse> =>
      makeResponse({ user: { ...user, opt_in_sharing: true } })
    );
    vi.stubGlobal('fetch', fetchMock);

    const authStore = useAuthStore();
    authStore.user = null;

    const updated = await authStore.setOptInSharing(true);

    expect(updated.opt_in_sharing).toBe(true);
    expect(authStore.user).toBeNull();
  });
});
