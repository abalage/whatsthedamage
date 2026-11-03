/**
 * Unit tests for the AuthLayout component
 * @module test/components/AuthLayout
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount } from '@vue/test-utils';
import AuthLayout from '../../src/components/AuthLayout.vue';

const mockRoute: { query: Record<string, unknown> } = { query: {} };

vi.mock('vue-router', (): Record<string, unknown> => ({
  useRoute: (): { query: Record<string, unknown> } => mockRoute
}));

const RouterLinkStub = {
  name: 'RouterLink',
  props: ['to'],
  template: '<a><slot /></a>'
};

const mountLayout = (): ReturnType<typeof mount> =>
  mount(AuthLayout, {
    slots: { default: '<p>content</p>' },
    global: { stubs: { RouterLink: RouterLinkStub } }
  });

describe('AuthLayout.vue', () => {
  beforeEach(() => {
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
});
