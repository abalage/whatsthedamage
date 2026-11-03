/**
 * Unit tests for the Register page component
 * @module test/pages/Register
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import Register from '../../src/pages/Register.vue';
import { register } from '../../src/js/api';
import { useAuthStore } from '../../src/stores/auth';
import type { User } from '../../src/types/auth';

const mockPush = vi.fn();

vi.mock('vue-router', () => ({
  useRouter: (): { push: (location: unknown) => Promise<unknown> } => ({ push: mockPush }),
  useRoute: (): { query: Record<string, unknown> } => ({ query: {} }),
  RouterLink: { template: '<a><slot /></a>' }
}));

vi.mock('vue3-gettext', (): Record<string, unknown> => ({
  useGettext: (): { $gettext: (key: string) => string } => ({
    $gettext: (key: string): string => key
  })
}));

vi.mock('../../src/js/api', () => ({
  register: vi.fn()
}));

const testUser: User = {
  id: 1,
  username: 'newuser',
  is_active: true,
  opt_in_sharing: false
};

interface RegisterVm {
  username: string;
  password: string;
  confirmPassword: string;
  termsAccepted: boolean;
  formValid: () => boolean;
  handleRegister: () => Promise<void>;
  handleAcknowledgeAndProceed: () => void;
  recoveryCodeAcknowledged: boolean;
  showRecoveryCode: boolean;
}

const mountPage = async (): Promise<{ vm: RegisterVm; authStore: ReturnType<typeof useAuthStore> }> => {
  const wrapper = mount(Register, {
    global: {
      plugins: [createPinia()],
      stubs: { RouterLink: { template: '<a><slot /></a>' } }
    }
  });
  // Skip the initial navigation redirect watcher by not authenticating
  const authStore = useAuthStore();
  return { vm: wrapper.vm as unknown as RegisterVm, authStore };
};

describe('Register.vue', () => {
  beforeEach(() => {
    vi.clearAllMocks();
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

  it('registers successfully and enters the recovery code state', async () => {
    vi.mocked(register).mockResolvedValue({
      user: testUser,
      recovery_code: 'ABCD-EFGH-IJKL-MNOP',
      session_expires_at: '2026-10-20T12:00:00Z'
    });

    const { vm } = await mountPage();
    vm.username = 'user';
    vm.password = 'long-enough-password';
    vm.confirmPassword = 'long-enough-password';
    vm.termsAccepted = true;

    await vm.handleRegister();

    expect(register).toHaveBeenCalledWith('user', 'long-enough-password');
    expect(vm.showRecoveryCode).toBe(true);
  });

  it('navigates to login after acknowledging the recovery code', async () => {
    const { vm } = await mountPage();
    vm.recoveryCodeAcknowledged = true;
    vm.handleAcknowledgeAndProceed();

    expect(mockPush).toHaveBeenCalledWith({ name: 'login', query: { registered: 'true' } });
  });

  it('renders the recovery-code screen with all required structural elements', async () => {
    vi.mocked(register).mockResolvedValue({
      user: testUser,
      recovery_code: 'ABCD-EFGH-IJKL-MNOP',
      session_expires_at: '2026-10-20T12:00:00Z'
    });

    const wrapper = mount(Register, {
      global: {
        plugins: [createPinia()],
        stubs: { RouterLink: { template: '<a><slot /></a>' } }
      }
    });
    const vm = wrapper.vm as unknown as RegisterVm;
    vm.username = 'user';
    vm.password = 'long-enough-password';
    vm.confirmPassword = 'long-enough-password';
    vm.termsAccepted = true;

    await vm.handleRegister();
    await wrapper.vm.$nextTick();

    const html = wrapper.html();
    expect(html).toContain('recovery-code-container');
    expect(html).toContain('recovery-code-box');
    expect(html).toContain('ABCD-EFGH-IJKL-MNOP');
    expect(html).toContain('auth-status-warning');
    expect(html).toContain('auth-acknowledgment');
    expect(html).toContain('auth-primary-btn');
  });
});
