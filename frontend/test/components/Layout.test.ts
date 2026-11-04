/**
 * Unit tests for the Layout component's navbar: with a single default theme
 * there is no theme switcher dropdown
 * @module test/components/Layout
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount, type VueWrapper } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import Layout from '../../src/components/Layout.vue';

const mockRoute: { name: string; query: Record<string, unknown>; meta: Record<string, unknown> } = {
  name: 'index',
  query: {},
  meta: {},
};

vi.mock('vue-router', (): Record<string, unknown> => ({
  useRoute: (): typeof mockRoute => mockRoute,
  RouterLink: { props: ['to'], template: '<a><slot /></a>' },
}));

vi.mock('vue3-gettext', (): Record<string, unknown> => ({
  useGettext: (): Record<string, unknown> => ({
    $gettext: (key: string): string => key,
  }),
}));

vi.mock('../../src/js/api.js', (): Record<string, unknown> => ({
  recalculateStatistics: vi.fn(),
}));

const mountLayout = (): VueWrapper =>
  mount(Layout, {
    global: {
      plugins: [createPinia()],
      mocks: { $gettext: (key: string): string => key },
      stubs: { LocaleSwitcher: true },
    },
  });

describe('Layout.vue', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    setActivePinia(createPinia());
    mockRoute.name = 'index';
    mockRoute.query = {};
    mockRoute.meta = {};
  });

  it('renders the navbar without a theme switcher dropdown', () => {
    const wrapper = mountLayout();

    expect(wrapper.find('#themeDropdown').exists()).toBe(false);
    expect(wrapper.find('.theme-preview').exists()).toBe(false);
    expect(wrapper.text()).not.toContain('Themes');
  });

  it('still renders the main navigation links', () => {
    const wrapper = mountLayout();

    expect(wrapper.find('nav.navbar').exists()).toBe(true);
    expect(wrapper.text()).toContain("What's the Damage?");
    expect(wrapper.text()).toContain('Home');
  });
});
