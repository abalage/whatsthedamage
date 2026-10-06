/**
 * Unit tests for Settings page component
 * @module test/pages/Settings
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount, type VueWrapper } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import Settings from '../../src/pages/Settings.vue';
import { useAuthStore } from '../../src/stores/auth.js';

vi.mock('vue3-gettext', (): Record<string, unknown> => ({
  useGettext: (): { $gettext: (key: string) => string } => ({
    $gettext: (key: string): string => key,
  }),
}));

const mockPush = vi.fn();
vi.mock('vue-router', (): Record<string, unknown> => ({
  useRouter: (): { push: typeof mockPush } => ({ push: mockPush }),
}));

const user = {
  id: 1,
  username: 'testuser',
  created_at: null,
  last_login_at: null,
  is_active: true,
  opt_in_sharing: false,
};

describe('Settings.vue', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    setActivePinia(createPinia());
  });

  const mountSettings = (): VueWrapper => {
    const authStore = useAuthStore();
    authStore.user = { ...user };
    return mount(Settings);
  };

  it('renders the sharing section with the permanent retention warning', () => {
    const wrapper = mountSettings();
    const html = wrapper.html();

    expect(html).toContain('Settings');
    expect(html).toContain('Share corrections');
    expect(html).toContain('Contribute my corrections to improve future categorization');
    expect(html).toContain('Shared corrections are retained permanently and remain anonymized even if your account is deleted. They cannot be retracted.');
  });

  it('reflects the opt-out default in the toggle state', () => {
    const wrapper = mountSettings();
    const toggle = wrapper.find('#optInSharingSwitch');

    expect((toggle.element as HTMLInputElement).checked).toBe(false);
  });

  it('reflects an opted-in user in the toggle state', () => {
    const authStore = useAuthStore();
    authStore.user = { ...user, opt_in_sharing: true };
    const wrapper = mount(Settings);

    const toggle = wrapper.find('#optInSharingSwitch');
    expect((toggle.element as HTMLInputElement).checked).toBe(true);
  });

  it('calls the store action when the toggle changes', async () => {
    const wrapper = mountSettings();
    const spy = vi.spyOn(useAuthStore(), 'setOptInSharing');

    await wrapper.find('#optInSharingSwitch').setValue(true);

    expect(spy).toHaveBeenCalledWith(true);
  });

  it('shows the enabled confirmation after a successful opt-in', async () => {
    const wrapper = mountSettings();
    const authStore = useAuthStore();
    vi.spyOn(authStore, 'setOptInSharing').mockImplementation(async (optIn: boolean) => {
      if (authStore.user) {
        authStore.user = { ...authStore.user, opt_in_sharing: optIn };
      }
      return { ...user, opt_in_sharing: optIn };
    });

    await wrapper.find('#optInSharingSwitch').setValue(true);

    expect(wrapper.html()).toContain('Sharing is enabled. Your future corrections will be contributed.');
  });

  it('shows the revoked confirmation after disabling sharing', async () => {
    const authStore = useAuthStore();
    authStore.user = { ...user, opt_in_sharing: true };
    const wrapper = mount(Settings);
    vi.spyOn(authStore, 'setOptInSharing').mockImplementation(async (optIn: boolean) => {
      if (authStore.user) {
        authStore.user = { ...authStore.user, opt_in_sharing: optIn };
      }
      return { ...user, opt_in_sharing: optIn };
    });

    await wrapper.find('#optInSharingSwitch').setValue(false);

    expect(wrapper.html()).toContain('Sharing is disabled. This takes effect immediately for future corrections. Previously shared corrections are retained permanently and cannot be retracted.');
  });

  it('shows an error message when the update fails', async () => {
    const wrapper = mountSettings();
    const authStore = useAuthStore();
    vi.spyOn(authStore, 'setOptInSharing').mockRejectedValue(new Error('Network error'));

    await wrapper.find('#optInSharingSwitch').setValue(true);

    expect(wrapper.html()).toContain('Failed to update the sharing preference:');
    expect(wrapper.html()).toContain('Network error');
  });

  it('renders the account deletion section with the grace period warning', () => {
    const wrapper = mountSettings();
    const html = wrapper.html();

    expect(html).toContain('Delete account');
    expect(html).toContain('Your account and all of your transactions and corrections are deleted after a 7-day grace period.');
    expect(html).toContain('If you log in again before the grace period ends, the deletion is canceled and nothing is lost.');
    expect(html).toContain('Anonymized corrections you shared before deletion are retained permanently and cannot be retracted.');
  });

  it('disables the deletion button until a password is entered', async () => {
    const wrapper = mountSettings();
    const button = wrapper.find('button[type="submit"]');

    expect((button.element as HTMLButtonElement).disabled).toBe(true);

    wrapper.find('#deleteAccountPassword').setValue('password-123456');
    await wrapper.vm.$nextTick();
    expect((button.element as HTMLButtonElement).disabled).toBe(false);
  });

  it('calls the store action when the deletion form is submitted', async () => {
    const wrapper = mountSettings();
    const spy = vi
      .spyOn(useAuthStore(), 'requestAccountDeletion')
      .mockResolvedValue('2026-10-13T00:00:00Z');

    wrapper.find('#deleteAccountPassword').setValue('password-123456');
    await wrapper.vm.$nextTick();
    await wrapper.find('form').trigger('submit.prevent');

    expect(spy).toHaveBeenCalledWith('password-123456');
    expect(mockPush).toHaveBeenCalledWith({ name: 'login' });
  });

  it('shows an error message when the deletion request fails', async () => {
    const wrapper = mountSettings();
    const authStore = useAuthStore();
    vi.spyOn(authStore, 'requestAccountDeletion').mockRejectedValue(
      new Error('Invalid password')
    );

    wrapper.find('#deleteAccountPassword').setValue('wrong-password');
    await wrapper.vm.$nextTick();
    await wrapper.find('form').trigger('submit.prevent');
    await wrapper.vm.$nextTick();

    expect(wrapper.html()).toContain('Failed to schedule the account deletion:');
    expect(wrapper.html()).toContain('Invalid password');
  });
});
