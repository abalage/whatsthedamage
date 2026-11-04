/**
 * Unit tests for the AuthLayout component
 * @module test/components/AuthLayout
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import AuthLayout from '../../src/components/AuthLayout.vue';
import { useLocaleStore } from '../../src/stores/locale';

const mockRoute: { query: Record<string, unknown> } = { query: {} };

vi.mock('vue-router', (): Record<string, unknown> => ({
  useRoute: (): { query: Record<string, unknown> } => mockRoute
}));

vi.mock('vue3-gettext', (): Record<string, unknown> => ({
  useGettext: (): Record<string, unknown> => ({
    $gettext: (key: string): string => key,
    current: 'en',
    available: { en: 'English', hu: 'Magyar' }
  })
}));

const RouterLinkStub = {
  name: 'RouterLink',
  props: ['to'],
  template: '<a><slot /></a>'
};

const mountLayout = (): ReturnType<typeof mount> =>
  mount(AuthLayout, {
    slots: { default: '<p>content</p>' },
    global: {
      plugins: [createPinia()],
      stubs: { RouterLink: RouterLinkStub }
    }
  });

describe('AuthLayout.vue', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    localStorage.clear();
    mockRoute.query = {};
  });

  it('renders the app title as a link to the landing page', () => {
    const wrapper = mountLayout();
    const link = wrapper.findComponent(RouterLinkStub);

    expect(wrapper.find('h1.app-title').text()).toContain("What's the Damage");
    expect(link.exists()).toBe(true);
    expect(link.props('to')).toEqual({ name: 'landing', query: {} });
  });

  it('preserves a pending redirect target on the landing link', () => {
    mockRoute.query = { redirect: '/import' };
    const wrapper = mountLayout();

    expect(wrapper.findComponent(RouterLinkStub).props('to')).toEqual({
      name: 'landing',
      query: { redirect: '/import' }
    });
  });

  it('drops an unsafe redirect target from the landing link', () => {
    mockRoute.query = { redirect: 'https://evil.example.com' };
    const wrapper = mountLayout();

    expect(wrapper.findComponent(RouterLinkStub).props('to')).toEqual({ name: 'landing', query: {} });
  });

  it('renders the language switcher', () => {
    const wrapper = mountLayout();

    expect(wrapper.find('.locale-switch').exists()).toBe(true);
    expect(wrapper.findAll('.locale-switch button')).toHaveLength(2);
  });

  it('switches the interface language from the auth layout', async () => {
    const wrapper = mountLayout();
    const localeStore = useLocaleStore();
    const buttons = wrapper.findAll('.locale-switch button');

    await buttons[1].trigger('click');
    expect(localeStore.locale).toBe('hu');
    await buttons[0].trigger('click');
    expect(localeStore.locale).toBe('en');
  });
});
