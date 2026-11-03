/**
 * Unit tests for Settings page component
 * @module test/pages/Settings
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount, type VueWrapper } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import Settings from '../../src/pages/Settings.vue';
import { useAuthStore } from '../../src/stores/auth';

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

  it('renders the sharing section with the retention explanation', () => {
    const wrapper = mountSettings();
    const html = wrapper.html();

    expect(html).toContain('Settings');
    expect(html).toContain('Share corrections');
    expect(html).toContain('Contribute my corrections to improve future categorization');
    expect(html).toContain('Shared corrections are anonymized and retained even if you turn sharing off or delete your account. You can ask for their removal when you request account deletion.');
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

    expect(wrapper.html()).toContain('Sharing is disabled. This takes effect immediately for future corrections. Previously shared corrections remain anonymized; you can ask for their removal when you request account deletion.');
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
    expect(html).toContain('Also remove the anonymized corrections I shared');
  });

  it('disables the deletion button until a password is entered', async () => {
    const wrapper = mountSettings();
    const button = wrapper.find('#deleteAccountPassword').element
      .closest('form')?.querySelector('button[type="submit"]') as HTMLButtonElement;

    expect(button.disabled).toBe(true);

    wrapper.find('#deleteAccountPassword').setValue('password-123456');
    await wrapper.vm.$nextTick();
    expect(button.disabled).toBe(false);
  });

  it('calls the store action when the deletion form is submitted', async () => {
    const wrapper = mountSettings();
    const spy = vi
      .spyOn(useAuthStore(), 'requestAccountDeletion')
      .mockResolvedValue('2026-10-13T00:00:00Z');

    wrapper.find('#deleteAccountPassword').setValue('password-123456');
    await wrapper.vm.$nextTick();
    await wrapper.find('[data-testid="delete-account-form"]').trigger('submit.prevent');

    expect(spy).toHaveBeenCalledWith('password-123456', false);
    expect(mockPush).toHaveBeenCalledWith({ name: 'login' });
  });

  it('passes the revocation option to the store action', async () => {
    const wrapper = mountSettings();
    const spy = vi
      .spyOn(useAuthStore(), 'requestAccountDeletion')
      .mockResolvedValue('2026-10-13T00:00:00Z');

    wrapper.find('#deleteAccountPassword').setValue('password-123456');
    await wrapper.find('#revokeSharedCorrections').setValue(true);
    await wrapper.vm.$nextTick();
    await wrapper.find('[data-testid="delete-account-form"]').trigger('submit.prevent');

    expect(spy).toHaveBeenCalledWith('password-123456', true);
  });

  it('shows the machine learning limitation notice when revocation is checked', async () => {
    const wrapper = mountSettings();

    await wrapper.find('#revokeSharedCorrections').setValue(true);

    expect(wrapper.html()).toContain('Machine learning models already trained on your shared corrections cannot be changed.');
  });

  it('shows an error message when the deletion request fails', async () => {
    const wrapper = mountSettings();
    const authStore = useAuthStore();
    vi.spyOn(authStore, 'requestAccountDeletion').mockRejectedValue(
      new Error('Invalid password')
    );

    wrapper.find('#deleteAccountPassword').setValue('wrong-password');
    await wrapper.vm.$nextTick();
    await wrapper.find('[data-testid="delete-account-form"]').trigger('submit.prevent');
    await wrapper.vm.$nextTick();

    expect(wrapper.html()).toContain('Failed to schedule the account deletion:');
    expect(wrapper.html()).toContain('Invalid password');
  });

  it('renders the account and data export sections', () => {
    const wrapper = mountSettings();
    const html = wrapper.html();

    expect(html).toContain('Account');
    expect(html).toContain('Change username');
    expect(html).toContain('Change password');
    expect(html).toContain('Your data');
    expect(html).toContain('Download my data');
  });

  it('calls the store action when the username form is submitted', async () => {
    const wrapper = mountSettings();
    const spy = vi
      .spyOn(useAuthStore(), 'changeUsername')
      .mockResolvedValue({ ...user, username: 'renamed' });

    wrapper.find('#newUsername').setValue('renamed');
    await wrapper.vm.$nextTick();
    await wrapper.find('[data-testid="username-form"]').trigger('submit.prevent');

    expect(spy).toHaveBeenCalledWith('renamed');
  });

  it('calls the store action when the password form is submitted', async () => {
    const wrapper = mountSettings();
    const spy = vi
      .spyOn(useAuthStore(), 'changeUserPassword')
      .mockResolvedValue(undefined);

    wrapper.find('#currentPassword').setValue('password-123456');
    wrapper.find('#newPassword').setValue('new-password-456789');
    await wrapper.vm.$nextTick();
    await wrapper.find('[data-testid="password-form"]').trigger('submit.prevent');

    expect(spy).toHaveBeenCalledWith('password-123456', 'new-password-456789');
  });

  it('calls the store action when the export button is clicked', async () => {
    const wrapper = mountSettings();
    const spy = vi
      .spyOn(useAuthStore(), 'exportData')
      .mockResolvedValue({
        generated_at: '2026-10-07T00:00:00Z',
        account: { ...user },
        processing_results: [],
        transactions: [],
        corrections: []
      });

    await wrapper.find('button.btn.btn-secondary.mb-3').trigger('click');

    expect(spy).toHaveBeenCalled();
  });

  it('renders the recovery code section', () => {
    const wrapper = mountSettings();
    const html = wrapper.html();

    expect(html).toContain('Recovery code');
    expect(html).toContain('Generate new recovery code');
  });

  it('disables the recovery code button until a password is entered', async () => {
    const wrapper = mountSettings();
    const button = wrapper
      .find('[data-testid="recovery-code-form"] button[type="submit"]')
      .element as HTMLButtonElement;

    expect(button.disabled).toBe(true);

    await wrapper.find('#recoveryPassword').setValue('password-123456');
    expect(button.disabled).toBe(false);
  });

  it('calls the store action when the recovery code form is submitted', async () => {
    const wrapper = mountSettings();
    const spy = vi
      .spyOn(useAuthStore(), 'regenerateUserRecoveryCode')
      .mockResolvedValue('ABCD-EFGH-IJKL-MNOP');

    await wrapper.find('#recoveryPassword').setValue('password-123456');
    await wrapper.find('[data-testid="recovery-code-form"]').trigger('submit.prevent');
    await wrapper.vm.$nextTick();

    expect(spy).toHaveBeenCalledWith('password-123456');
  });

  it('shows the new recovery code after successful regeneration', async () => {
    const wrapper = mountSettings();
    vi.spyOn(useAuthStore(), 'regenerateUserRecoveryCode')
      .mockResolvedValue('ABCD-EFGH-IJKL-MNOP');

    await wrapper.find('#recoveryPassword').setValue('password-123456');
    await wrapper.find('[data-testid="recovery-code-form"]').trigger('submit.prevent');
    await wrapper.vm.$nextTick();

    expect(wrapper.html()).toContain('New Recovery Code Generated');
    expect(wrapper.html()).toContain('ABCD-EFGH-IJKL-MNOP');
  });

  it('shows an error when regeneration fails', async () => {
    const wrapper = mountSettings();
    vi.spyOn(useAuthStore(), 'regenerateUserRecoveryCode')
      .mockRejectedValue(new Error('Invalid current password'));

    await wrapper.find('#recoveryPassword').setValue('wrong-password');
    await wrapper.find('[data-testid="recovery-code-form"]').trigger('submit.prevent');
    await wrapper.vm.$nextTick();

    expect(wrapper.html()).toContain('Failed to regenerate the recovery code:');
    expect(wrapper.html()).toContain('Invalid current password');
  });

  it('shows the success message after the recovery code display is acknowledged', async () => {
    const wrapper = mountSettings();
    vi.spyOn(useAuthStore(), 'regenerateUserRecoveryCode')
      .mockResolvedValue('ABCD-EFGH-IJKL-MNOP');

    await wrapper.find('#recoveryPassword').setValue('password-123456');
    await wrapper.find('[data-testid="recovery-code-form"]').trigger('submit.prevent');
    await wrapper.vm.$nextTick();

    // Acknowledge the checkbox in the RecoveryCodeDisplay
    const checkbox = wrapper.find('.auth-acknowledgment input[type="checkbox"]');
    await checkbox.setValue(true);
    await wrapper.find('.auth-primary-btn').trigger('click');
    await wrapper.vm.$nextTick();

    expect(wrapper.html()).toContain('Your recovery code has been regenerated.');
  });
});
