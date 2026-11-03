/**
 * Unit tests for RecoveryCodeDisplay component
 * @module test/components/RecoveryCodeDisplay
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount } from '@vue/test-utils';
import RecoveryCodeDisplay from '../../src/components/auth/RecoveryCodeDisplay.vue';

vi.mock('vue3-gettext', (): Record<string, unknown> => ({
  useGettext: (): { $gettext: (key: string) => string } => ({
    $gettext: (key: string): string => key,
  }),
}));

const mockPush = vi.fn();
vi.mock('vue-router', (): Record<string, unknown> => ({
  useRouter: (): { push: typeof mockPush } => ({ push: mockPush }),
}));

describe('RecoveryCodeDisplay.vue', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders default props (password reset context)', () => {
    const wrapper = mount(RecoveryCodeDisplay, {
      props: { recoveryCode: 'ABCD-EFGH-IJKL-MNOP' }
    });

    const html = wrapper.html();
    expect(html).toContain('Password Reset Successful!');
    expect(html).toContain('Continue to Login');
    expect(html).toContain('ABCD-EFGH-IJKL-MNOP');
    expect(html).toContain('Back to Login');
  });

  it('renders custom props (settings/regeneration context)', () => {
    const wrapper = mount(RecoveryCodeDisplay, {
      props: {
        recoveryCode: 'WXYZ-1234-5678-9012',
        title: 'New Recovery Code Generated',
        instructions: 'Your old recovery code no longer works. Save the new one now.',
        warningText: 'This new recovery code is displayed only once.',
        acknowledgeLabel: 'I have saved my new recovery code in a secure location',
        continueLabel: 'Done',
        showBackLink: false
      }
    });

    const html = wrapper.html();
    expect(html).toContain('New Recovery Code Generated');
    expect(html).toContain('Done');
    expect(html).toContain('WXYZ-1234-5678-9012');
    expect(html).not.toContain('Back to Login');
  });

  it('disables the continue button until acknowledged', async () => {
    const wrapper = mount(RecoveryCodeDisplay, {
      props: { recoveryCode: 'ABCD-EFGH-IJKL-MNOP' }
    });

    const button = wrapper.find('.auth-primary-btn').element as HTMLButtonElement;
    expect(button.disabled).toBe(true);

    await wrapper.find('.auth-acknowledgment input[type="checkbox"]').setValue(true);
    expect(button.disabled).toBe(false);
  });

  it('emits continue when acknowledged and button clicked', async () => {
    const wrapper = mount(RecoveryCodeDisplay, {
      props: { recoveryCode: 'ABCD-EFGH-IJKL-MNOP' }
    });

    await wrapper.find('.auth-acknowledgment input[type="checkbox"]').setValue(true);
    await wrapper.find('.auth-primary-btn').trigger('click');

    expect(wrapper.emitted('continue')).toHaveLength(1);
  });

  it('does not emit continue when not acknowledged', async () => {
    const wrapper = mount(RecoveryCodeDisplay, {
      props: { recoveryCode: 'ABCD-EFGH-IJKL-MNOP' }
    });

    await wrapper.find('.auth-primary-btn').trigger('click');

    expect(wrapper.emitted('continue')).toBeUndefined();
  });
});
