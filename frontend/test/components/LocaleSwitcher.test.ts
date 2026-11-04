/**
 * Unit tests for the LocaleSwitcher component
 * @module test/components/LocaleSwitcher
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import LocaleSwitcher from '../../src/components/LocaleSwitcher.vue';
import { useLocaleStore } from '../../src/stores/locale';

vi.mock('vue3-gettext', (): Record<string, unknown> => ({
  useGettext: (): Record<string, unknown> => ({
    $gettext: (key: string): string => key,
    current: 'en',
    available: { en: 'English', hu: 'Magyar' }
  })
}));

const mountSwitcher = (): ReturnType<typeof mount> =>
  mount(LocaleSwitcher, {
    global: {
      plugins: [createPinia()]
    }
  });

describe('LocaleSwitcher.vue', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    localStorage.clear();
  });

  it('renders one button per available language with accessible labels', () => {
    const wrapper = mountSwitcher();
    const switcher = wrapper.find('.locale-switch');
    const buttons = wrapper.findAll('.locale-switch button');

    expect(switcher.attributes('role')).toBe('group');
    expect(switcher.attributes('aria-label')).toBe('Languages');
    expect(buttons).toHaveLength(2);
    expect(buttons[0].text()).toBe('EN');
    expect(buttons[0].attributes('aria-label')).toBe('English');
    expect(buttons[1].text()).toBe('HU');
    expect(buttons[1].attributes('aria-label')).toBe('Magyar');
  });

  it('marks the current locale as active and pressed', () => {
    const wrapper = mountSwitcher();
    const buttons = wrapper.findAll('.locale-switch button');

    expect(buttons[0].classes()).toContain('active');
    expect(buttons[0].attributes('aria-pressed')).toBe('true');
    expect(buttons[1].classes()).not.toContain('active');
    expect(buttons[1].attributes('aria-pressed')).toBe('false');
  });

  it('switches the locale and persists it to localStorage on click', async () => {
    const wrapper = mountSwitcher();
    const localeStore = useLocaleStore();
    const buttons = wrapper.findAll('.locale-switch button');

    await buttons[1].trigger('click');
    expect(localeStore.locale).toBe('hu');
    expect(localStorage.getItem('locale')).toBe('"hu"');
    expect(buttons[1].classes()).toContain('active');

    await buttons[0].trigger('click');
    expect(localeStore.locale).toBe('en');
    expect(localStorage.getItem('locale')).toBe('"en"');
    expect(buttons[0].classes()).toContain('active');
  });

  it('restores the persisted locale from localStorage', () => {
    localStorage.setItem('locale', '"hu"');
    const wrapper = mountSwitcher();
    const buttons = wrapper.findAll('.locale-switch button');

    expect(buttons[1].classes()).toContain('active');
  });

  it('ignores an invalid persisted locale and falls back to the default', () => {
    localStorage.setItem('locale', '"fr"');
    const wrapper = mountSwitcher();
    const localeStore = useLocaleStore();
    const buttons = wrapper.findAll('.locale-switch button');

    expect(localeStore.locale).toBe('en');
    expect(buttons[0].classes()).toContain('active');
  });
});
