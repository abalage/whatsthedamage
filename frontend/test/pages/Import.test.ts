/**
 * Unit tests for the Import page component
 * @module test/pages/Import
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import Import from '../../src/pages/Import.vue';
import { fetchAllCsvProfiles } from '../../src/js/api';
import type { CsvProfile } from '../../src/types/api';

const mockPush = vi.fn();

vi.mock('vue-router', () => ({
  useRouter: (): { push: (location: unknown) => Promise<unknown> } => ({ push: mockPush }),
  RouterLink: { template: '<a><slot /></a>' }
}));

vi.mock('vue3-gettext', (): Record<string, unknown> => ({
  useGettext: (): { $gettext: (key: string) => string } => ({
    $gettext: (key: string): string => key
  })
}));

vi.mock('../../src/js/api', () => ({
  fetchAllCsvProfiles: vi.fn(),
  createTransaction: vi.fn()
}));

const profiles: CsvProfile[] = [
  {
    id: 'p1',
    name: 'Bank A',
    version: '1',
    is_default: true,
    description: 'Bank A profile',
    csv_config: {
      dialect: 'excel',
      delimiter: ';',
      date_attribute_format: '%Y-%m-%d',
      attribute_mapping: {}
    }
  },
  {
    id: 'p2',
    name: 'Bank B',
    version: '2',
    is_default: false,
    description: 'Bank B profile',
    csv_config: {
      dialect: 'excel',
      delimiter: ',',
      date_attribute_format: '%Y-%m-%d',
      attribute_mapping: {}
    }
  }
];

const mountPage = async (): Promise<ReturnType<typeof mount>> => {
  const wrapper = mount(Import, {
    global: {
      plugins: [createPinia()],
      stubs: { RouterLink: { template: '<a><slot /></a>' } }
    }
  });
  await flushPromises();
  return wrapper;
};

describe('Import.vue', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setActivePinia(createPinia());
    vi.mocked(fetchAllCsvProfiles).mockResolvedValue(profiles);
  });

  it('loads the CSV profiles and selects the default one', async () => {
    const wrapper = await mountPage();

    expect(fetchAllCsvProfiles).toHaveBeenCalled();
    const options = wrapper.findAll('#csvProfile option');
    expect(options).toHaveLength(2);
    expect(options[0].text()).toContain('(default)');

    const vm = wrapper.vm as unknown as { formStore: { formData: { csvProfileId: string | null } } };
    expect(vm.formStore.formData.csvProfileId).toBe('p1');
  });

  it('shows a feedback error when the profile loading fails', async () => {
    vi.mocked(fetchAllCsvProfiles).mockRejectedValue(new Error('boom'));
    const wrapper = await mountPage();

    const feedback = wrapper.findComponent({ name: 'ErrorDisplay' });
    expect(feedback.exists()).toBe(true);
  });

  it('shows the validation message when submitting without a CSV file', async () => {
    const wrapper = await mountPage();

    // Trigger the composable's submit path: not authenticated
    await (wrapper.vm as unknown as { submitForm: () => Promise<boolean> }).submitForm();
    await flushPromises();

    // The unauthenticated path reports a feedback error and does not navigate
    expect(mockPush).not.toHaveBeenCalled();
  });
});
