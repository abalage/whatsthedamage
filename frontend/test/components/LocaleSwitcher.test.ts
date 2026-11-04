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

const mountSwitcher = (variant?: 'floating' | 'navbar'): ReturnType<typeof mount> =>
  mount(LocaleSwitcher, {
    props: variant === undefined ? {} : { variant },
    global: {
      plugins: [createPinia()]
    }
  });

describe('LocaleSwitcher.vue', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    localStorage.clear();
  });

  describe('floating variant (default)', () => {
    it('renders one button per available language with flag and name', () => {
      const wrapper = mountSwitcher();
      const switcher = wrapper.find('.locale-switch');
      const buttons = wrapper.findAll('.locale-switch button');

      expect(switcher.attributes('role')).toBe('group');
      expect(switcher.attributes('aria-label')).toBe('Languages');
      expect(buttons).toHaveLength(2);
      expect(buttons[0].text()).toBe('🇬🇧 English');
      expect(buttons[0].attributes('aria-label')).toBe('English');
      expect(buttons[1].text()).toBe('🇭🇺 Magyar');
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

  describe('navbar variant', () => {
    it('renders a dropdown with one flag + name item per language', () => {
      const wrapper = mountSwitcher('navbar');
      const toggle = wrapper.find('#langDropdown');
      const items = wrapper.findAll('.dropdown-menu .dropdown-item');

      expect(wrapper.find('li.nav-item.dropdown').exists()).toBe(true);
      expect(toggle.exists()).toBe(true);
      expect(toggle.text()).toBe('Languages');
      expect(items).toHaveLength(2);
      expect(items[0].text()).toBe('🇬🇧 English');
      expect(items[1].text()).toBe('🇭🇺 Magyar');
    });

    it('marks the current locale item as active', () => {
      const wrapper = mountSwitcher('navbar');
      const items = wrapper.findAll('.dropdown-menu .dropdown-item');

      expect(items[0].classes()).toContain('active');
      expect(items[1].classes()).not.toContain('active');
    });

    it('switches the locale on item click', async () => {
      const wrapper = mountSwitcher('navbar');
      const localeStore = useLocaleStore();
      const items = wrapper.findAll('.dropdown-menu .dropdown-item');

      await items[1].trigger('click');
      expect(localeStore.locale).toBe('hu');
      expect(localStorage.getItem('locale')).toBe('"hu"');

      await items[0].trigger('click');
      expect(localeStore.locale).toBe('en');
    });
  });
});
