/**
 * Unit tests for the Landing page component
 * @module test/pages/Landing
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { mount } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import Landing from '../../src/pages/Landing.vue';
import { useLocaleStore } from '../../src/stores/locale';

const mockRoute: { query: Record<string, unknown> } = { query: {} };

vi.mock('vue-router', (): Record<string, unknown> => ({
  useRoute: (): { query: Record<string, unknown> } => mockRoute,
  useRouter: (): { push: ReturnType<typeof vi.fn> } => ({ push: vi.fn() })
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

/**
 * Stub window.matchMedia (not implemented in jsdom) with a fixed result
 * @param matches - Whether the reduced-motion media query should match
 */
function stubMatchMedia(matches: boolean): void {
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    configurable: true,
    value: (query: string): unknown => ({
      matches,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn()
    })
  });
}

const mountLanding = (): ReturnType<typeof mount> =>
  mount(Landing, {
    global: {
      plugins: [createPinia()],
      stubs: { RouterLink: RouterLinkStub }
    }
  });

const ctaTargets = (wrapper: ReturnType<typeof mount>): Record<string, unknown>[] =>
  wrapper.findAllComponents(RouterLinkStub)
    .map((link) => link.props('to'))
    .filter((to): to is Record<string, unknown> => typeof to === 'object' && to !== null && 'name' in to);

describe('Landing.vue', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    localStorage.clear();
    mockRoute.query = {};
  });

  afterEach(() => {
    vi.useRealTimers();
    delete (window as unknown as Record<string, unknown>).matchMedia;
  });

  it('renders the trust message, pitch, CTAs, and the slideshow', () => {
    const wrapper = mountLanding();
    const html = wrapper.html();

    expect(html).toContain('Self-hosted. No telemetry. Your data never leaves your machine.');
    expect(html).toContain('Import your bank CSV exports and get them categorized automatically');
    expect(wrapper.find('.feature-slideshow').exists()).toBe(true);

    const names = ctaTargets(wrapper).map((to) => to.name);
    expect(names).toContain('login');
    expect(names).toContain('register');
  });

  it('passes the redirect query through to the Login and Register buttons', () => {
    mockRoute.query = { redirect: '/import' };
    const wrapper = mountLanding();

    for (const name of ['login', 'register']) {
      const target = ctaTargets(wrapper).find((to) => to.name === name);
      expect(target?.query).toEqual({ redirect: '/import' });
    }
  });

  it('omits the redirect query when it is absent or unsafe', () => {
    for (const redirect of [undefined, 'https://evil.example.com', '//evil.example.com']) {
      mockRoute.query = redirect === undefined ? {} : { redirect };
      const wrapper = mountLanding();
      for (const target of ctaTargets(wrapper).filter((to) => to.name === 'login' || to.name === 'register')) {
        expect(target.query).toEqual({});
      }
    }
  });

  it('navigates the slideshow with prev/next buttons and dot indicators', async () => {
    const wrapper = mountLanding();
    const slideshow = wrapper.find('.feature-slideshow');
    expect(slideshow.attributes('data-slide-index')).toBe('0');

    const navButtons = wrapper.findAll('.slideshow-nav');
    await navButtons[1].trigger('click'); // next
    expect(slideshow.attributes('data-slide-index')).toBe('1');

    await navButtons[0].trigger('click'); // prev
    expect(slideshow.attributes('data-slide-index')).toBe('0');

    await navButtons[0].trigger('click'); // prev wraps to the last slide
    expect(slideshow.attributes('data-slide-index')).toBe('5');

    const dots = wrapper.findAll('.slideshow-dot');
    expect(dots).toHaveLength(6);
    await dots[2].trigger('click');
    expect(slideshow.attributes('data-slide-index')).toBe('2');
    expect(dots[2].attributes('aria-current')).toBe('true');
  });

  it('auto-advances the slideshow every 5 seconds', async () => {
    vi.useFakeTimers();
    const wrapper = mountLanding();
    const slideshow = wrapper.find('.feature-slideshow');

    await vi.advanceTimersByTimeAsync(5000);
    expect(slideshow.attributes('data-slide-index')).toBe('1');

    await vi.advanceTimersByTimeAsync(5000);
    expect(slideshow.attributes('data-slide-index')).toBe('2');
  });

  it('pauses auto-advance on hover and resumes on mouse leave', async () => {
    vi.useFakeTimers();
    const wrapper = mountLanding();
    const slideshow = wrapper.find('.feature-slideshow');

    await slideshow.trigger('mouseenter');
    await vi.advanceTimersByTimeAsync(15000);
    expect(slideshow.attributes('data-slide-index')).toBe('0');

    await slideshow.trigger('mouseleave');
    await vi.advanceTimersByTimeAsync(5000);
    expect(slideshow.attributes('data-slide-index')).toBe('1');
  });

  it('does not auto-advance when prefers-reduced-motion is set, but allows manual navigation', async () => {
    stubMatchMedia(true);
    vi.useFakeTimers();
    const wrapper = mountLanding();
    const slideshow = wrapper.find('.feature-slideshow');

    await vi.advanceTimersByTimeAsync(20000);
    expect(slideshow.attributes('data-slide-index')).toBe('0');

    await wrapper.findAll('.slideshow-nav')[1].trigger('click');
    expect(slideshow.attributes('data-slide-index')).toBe('1');
  });

  it('switches the interface language via the locale buttons', async () => {
    const wrapper = mountLanding();
    const localeStore = useLocaleStore();
    const buttons = wrapper.findAll('.landing-locale-switch button');

    expect(buttons).toHaveLength(2);
    await buttons[1].trigger('click');
    expect(localeStore.locale).toBe('hu');
    await buttons[0].trigger('click');
    expect(localeStore.locale).toBe('en');
  });
});
