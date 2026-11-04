/**
 * Unit tests for the Register page component (two-phase registration)
 * @module test/pages/Register
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import Register from '../../src/pages/Register.vue';
import { register, confirmRegistration } from '../../src/js/api';
import { useAuthStore } from '../../src/stores/auth';
import type { RegisterConfirmResponse, User } from '../../src/types/auth';

const mockPush = vi.fn();

vi.mock('vue-router', () => ({
  useRouter: (): { push: (location: unknown) => Promise<unknown> } => ({ push: mockPush }),
  useRoute: (): { query: Record<string, unknown> } => ({ query: {} }),
  RouterLink: { template: '<a><slot /></a>' }
}));

vi.mock('vue3-gettext', (): Record<string, unknown> => ({
  useGettext: (): Record<string, unknown> => ({
    $gettext: (key: string): string => key,
    current: 'en',
    available: { en: 'English', hu: 'Magyar' }
  })
}));

vi.mock('../../src/js/api', () => ({
  register: vi.fn(),
  confirmRegistration: vi.fn()
}));

const testUser: User = {
  id: 1,
  username: 'newuser',
  is_active: true,
  opt_in_sharing: false
};

const pendingResponse = {
  pending_token: 'pending-token-123',
  recovery_code: 'ABCD-EFGH-JKLM-NPQR',
  expires_at: '2026-11-04T14:00:00Z'
};

interface RegisterVm {
  username: string;
  password: string;
  confirmPassword: string;
  termsAccepted: boolean;
  formValid: () => boolean;
  handleRegister: () => Promise<void>;
  handleAcknowledgeAndProceed: () => Promise<void>;
  recoveryCodeAcknowledged: boolean;
  isConfirming: boolean;
}

const mountPage = async (): Promise<{ vm: RegisterVm; authStore: ReturnType<typeof useAuthStore> }> => {
  const wrapper = mount(Register, {
    global: {
      plugins: [createPinia()],
      stubs: { RouterLink: { template: '<a><slot /></a>' } }
    }
  });
  const authStore = useAuthStore();
  return { vm: wrapper.vm as unknown as RegisterVm, authStore };
};

const fillValidForm = (vm: RegisterVm): void => {
  vm.username = 'user';
  vm.password = 'long-enough-password';
  vm.confirmPassword = 'long-enough-password';
  vm.termsAccepted = true;
};

describe('Register.vue', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    sessionStorage.clear();
    setActivePinia(createPinia());
  });

  it('rejects the form when passwords do not match', async () => {
    const { vm, authStore } = await mountPage();
    vm.username = 'user';
    vm.password = 'long-enough-password';
    vm.confirmPassword = 'different-password';
    vm.termsAccepted = true;

    expect(vm.formValid()).toBe(false);

    await vm.handleRegister();
    expect(authStore.error).toBe('Passwords do not match');
    expect(register).not.toHaveBeenCalled();
  });

  it('rejects the form when the password is too short', async () => {
    const { vm, authStore } = await mountPage();
    vm.username = 'user';
    vm.password = 'short';
    vm.confirmPassword = 'short';
    vm.termsAccepted = true;

    await vm.handleRegister();
    expect(authStore.error).toContain('Password must be at least');
    expect(register).not.toHaveBeenCalled();
  });

  it('rejects the form when the terms are not accepted', async () => {
    const { vm, authStore } = await mountPage();
    vm.username = 'user';
    vm.password = 'long-enough-password';
    vm.confirmPassword = 'long-enough-password';
    vm.termsAccepted = false;

    await vm.handleRegister();
    expect(authStore.error).toBe('Please accept the Terms and the Privacy Policy to continue');
  });

  it('phase 1 creates a pending registration and enters the recovery code state', async () => {
    vi.mocked(register).mockResolvedValue(pendingResponse);

    const { vm, authStore } = await mountPage();
    fillValidForm(vm);

    await vm.handleRegister();

    expect(register).toHaveBeenCalledWith('user', 'long-enough-password');
    expect(authStore.showRecoveryCode).toBe(true);
    expect(authStore.pendingToken).toBe('pending-token-123');
    expect(authStore.recoveryCode).toBe('ABCD-EFGH-JKLM-NPQR');
    // The user is NOT authenticated yet: no account, no session
    expect(authStore.isAuthenticated).toBe(false);
    // The pending state survives a reload via sessionStorage
    expect(sessionStorage.getItem('pending_registration_token')).toBe('pending-token-123');
    expect(sessionStorage.getItem('pending_registration_recovery_code')).toBe('ABCD-EFGH-JKLM-NPQR');
  });

  it('phase 2 confirms with the echoed recovery code and navigates to the app', async () => {
    vi.mocked(register).mockResolvedValue(pendingResponse);
    vi.mocked(confirmRegistration).mockResolvedValue({
      user: testUser,
      session_expires_at: '2026-11-04T14:00:00Z'
    });

    const { vm, authStore } = await mountPage();
    fillValidForm(vm);
    await vm.handleRegister();

    vm.recoveryCodeAcknowledged = true;
    await vm.handleAcknowledgeAndProceed();

    expect(confirmRegistration).toHaveBeenCalledWith('pending-token-123', 'ABCD-EFGH-JKLM-NPQR');
    expect(authStore.isAuthenticated).toBe(true);
    expect(mockPush).toHaveBeenCalledWith({ name: 'index', query: {} });
    // All copies of the recovery code are cleared after confirmation
    expect(authStore.recoveryCode).toBeNull();
    expect(authStore.showRecoveryCode).toBe(false);
    expect(authStore.pendingToken).toBeUndefined();
    expect(sessionStorage.getItem('pending_registration_token')).toBeNull();
    expect(sessionStorage.getItem('pending_registration_recovery_code')).toBeNull();
  });

  it('ignores a second confirm click while a confirm is in flight', async () => {
    vi.mocked(register).mockResolvedValue(pendingResponse);
    let resolveConfirm: (value: RegisterConfirmResponse) => void = () => undefined;
    vi.mocked(confirmRegistration).mockImplementation(
      () => new Promise((resolve) => { resolveConfirm = resolve; })
    );

    const { vm } = await mountPage();
    fillValidForm(vm);
    await vm.handleRegister();

    vm.recoveryCodeAcknowledged = true;
    const first = vm.handleAcknowledgeAndProceed();
    expect(vm.isConfirming).toBe(true);
    const second = vm.handleAcknowledgeAndProceed();

    expect(confirmRegistration).toHaveBeenCalledTimes(1);
    resolveConfirm({ user: testUser, session_expires_at: '2026-11-04T14:00:00Z' });
    await Promise.all([first, second]);
    expect(vm.isConfirming).toBe(false);
  });

  it('stays on the form with an error when phase 2 fails', async () => {
    vi.mocked(register).mockResolvedValue(pendingResponse);
    vi.mocked(confirmRegistration).mockRejectedValue(new Error('Invalid or expired registration'));

    const { vm, authStore } = await mountPage();
    fillValidForm(vm);
    await vm.handleRegister();

    vm.recoveryCodeAcknowledged = true;
    await vm.handleAcknowledgeAndProceed();

    expect(mockPush).not.toHaveBeenCalled();
    expect(authStore.error).toBe('Invalid or expired registration');
    // Pending state is cleared so the user can register again
    expect(authStore.showRecoveryCode).toBe(false);
    expect(authStore.pendingToken).toBeUndefined();
    expect(sessionStorage.getItem('pending_registration_token')).toBeNull();
  });

  it('renders the recovery-code screen with all required structural elements', async () => {
    vi.mocked(register).mockResolvedValue(pendingResponse);

    const wrapper = mount(Register, {
      global: {
        plugins: [createPinia()],
        stubs: { RouterLink: { template: '<a><slot /></a>' } }
      }
    });
    const vm = wrapper.vm as unknown as RegisterVm;
    fillValidForm(vm);

    await vm.handleRegister();
    await wrapper.vm.$nextTick();

    const html = wrapper.html();
    expect(html).toContain('recovery-code-container');
    expect(html).toContain('recovery-code-box');
    expect(html).toContain('ABCD-EFGH-JKLM-NPQR');
    expect(html).toContain('auth-status-warning');
    expect(html).toContain('auth-acknowledgment');
    expect(html).toContain('auth-primary-btn');
  });

  it('keeps the recovery-code screen after a remount (locale change) while pending', async () => {
    vi.mocked(register).mockResolvedValue(pendingResponse);

    // One shared Pinia instance: a locale change remounts the page tree
    // (App.vue :key) but the store state survives
    const pinia = createPinia();
    setActivePinia(pinia);
    const mountWith = (): ReturnType<typeof mount> => mount(Register, {
      global: {
        plugins: [pinia],
        stubs: { RouterLink: { template: '<a><slot /></a>' } }
      }
    });

    const wrapper1 = mountWith();
    const vm = wrapper1.vm as unknown as RegisterVm;
    fillValidForm(vm);
    await vm.handleRegister();
    const authStore = useAuthStore();
    expect(authStore.showRecoveryCode).toBe(true);

    // Remount (as the locale switch does) with the same store
    const wrapper2 = mountWith();
    await wrapper2.vm.$nextTick();
    expect(authStore.showRecoveryCode).toBe(true);
    expect(authStore.recoveryCode).toBe('ABCD-EFGH-JKLM-NPQR');
    expect(wrapper2.html()).toContain('recovery-code-container');
    expect(wrapper2.html()).toContain('ABCD-EFGH-JKLM-NPQR');
  });
});
