/**
 * Unit tests for ForgotPassword page component
 * @module test/pages/ForgotPassword
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount } from '@vue/test-utils';
import ForgotPassword from '../../src/pages/ForgotPassword.vue';
import { resetPassword } from '../../src/js/api.js';

// Mock the router
const mockPush = vi.fn();
const mockRouter = {
  push: mockPush
};

// Mock the API
vi.mock('../../src/js/api.js', () => ({
  resetPassword: vi.fn()
}));

// Mock useRouter from vue-router
vi.mock('vue-router', () => ({
  useRouter: () => mockRouter,
  useRoute: () => ({ query: {} })
}));

describe('ForgotPassword.vue', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(resetPassword).mockReset();
    mockPush.mockClear();
  });

  const mountOptions = {
    attachTo: document.body,
    global: {
      stubs: {
        RouterLink: { template: '<a><slot /></a>' }
      }
    }
  };

  it('renders correctly with title and instructions', () => {
    const wrapper = mount(ForgotPassword, mountOptions);
    const html = wrapper.html();

    expect(html.includes('Reset Password')).toBe(true);
    expect(html.includes('class="instructions"')).toBe(true);
    expect(html).toContain('Enter your username and the recovery code');
  });

  it('shows login and register links', () => {
    const wrapper = mount(ForgotPassword, mountOptions);
    const html = wrapper.html();

    expect(html).toContain('Login');
    expect(html).toContain('Register');
  });

  it('calls resetPassword API when form submits', async () => {
    vi.mocked(resetPassword).mockResolvedValue({
      user: { id: 1, username: 'testuser', is_active: true, opt_in_sharing: false },
      new_recovery_code: 'NEW-ABCD-EFGH-IJKL-MN'
    });

    const wrapper = mount(ForgotPassword, mountOptions);
    const vm = wrapper.vm as any;

    await vm.handleResetPassword('testuser', 'ABCD-EFGH-IJKL-MNOP', 'new_secure_password_1234');
    await new Promise(setImmediate);

    expect(resetPassword).toHaveBeenCalledWith(
      'testuser',
      'ABCD-EFGH-IJKL-MNOP',
      'new_secure_password_1234'
    );
  });

  it('shows success state with new recovery code after successful submission', async () => {
    vi.mocked(resetPassword).mockResolvedValue({
      user: { id: 1, username: 'testuser', is_active: true, opt_in_sharing: false },
      new_recovery_code: 'NEW-ABCD-EFGH-IJKL-MN'
    });

    const wrapper = mount(ForgotPassword, mountOptions);
    const vm = wrapper.vm as any;

    await vm.handleResetPassword('testuser', 'ABCD-EFGH-IJKL-MNOP', 'new_secure_password_1234');
    await new Promise(setImmediate);
    await wrapper.vm.$nextTick();

    expect(vm.showSuccessState).toBe(true);
    expect(vm.newRecoveryCode).toBe('NEW-ABCD-EFGH-IJKL-MN');
  });

  it('handles API errors with generic message', async () => {
    vi.mocked(resetPassword).mockRejectedValue(new Error('Invalid username or recovery code'));

    const wrapper = mount(ForgotPassword, mountOptions);
    const vm = wrapper.vm as any;

    await vm.handleResetPassword('testuser', 'WRONG-CODE', 'new_secure_password_1234');
    await new Promise(setImmediate);
    await wrapper.vm.$nextTick();

    expect(vm.error).toContain('Invalid username or recovery code');
    expect(vm.showSuccessState).toBe(false);
  });

  it('handles password too weak error', async () => {
    vi.mocked(resetPassword).mockRejectedValue(new Error('Password must be at least 12 characters'));

    const wrapper = mount(ForgotPassword, mountOptions);
    const vm = wrapper.vm as any;

    await vm.handleResetPassword('testuser', 'ABCD-EFGH-IJKL-MNOP', 'short');
    await new Promise(setImmediate);
    await wrapper.vm.$nextTick();

    expect(vm.error).toContain('Password must be at least 12 characters');
  });

  it('navigates to login when continue is called', async () => {
    vi.mocked(resetPassword).mockResolvedValue({
      user: { id: 1, username: 'testuser', is_active: true, opt_in_sharing: false },
      new_recovery_code: 'NEW-ABCD-EFGH-IJKL-MN'
    });

    const wrapper = mount(ForgotPassword, mountOptions);
    const vm = wrapper.vm as any;

    await vm.handleResetPassword('testuser', 'ABCD-EFGH-IJKL-MNOP', 'new_secure_password_1234');
    await new Promise(setImmediate);
    await wrapper.vm.$nextTick();

    vm.handleContinue();

    expect(mockPush).toHaveBeenCalledWith({ name: 'login' });
  });

  it('clears error when clearError is called', async () => {
    vi.mocked(resetPassword).mockRejectedValue(new Error('Invalid username or recovery code'));

    const wrapper = mount(ForgotPassword, mountOptions);
    const vm = wrapper.vm as any;

    await vm.handleResetPassword('testuser', 'WRONG-CODE', 'new_secure_password_1234');
    await new Promise(setImmediate);
    await wrapper.vm.$nextTick();

    expect(vm.error).toBeTruthy();

    vm.clearError();

    expect(vm.error).toBe(null);
  });

  it('passes isLoading and error props to child form', () => {
    const wrapper = mount(ForgotPassword, mountOptions);
    const vm = wrapper.vm as any;

    expect(vm.isLoading).toBe(false);
    expect(vm.error).toBe(null);
  });
});
