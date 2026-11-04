/**
 * Unit tests for the theme registry and theme store: the application has
 * exactly one theme (Baltic Blue) and the engine still applies it
 * @module test/theme
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { createPinia, setActivePinia } from 'pinia';
import { THEMES, getThemeById, getDefaultTheme } from '../src/js/themes/index';
import { useThemeStore } from '../src/stores/theme';

const STORAGE_KEY = 'wtb-theme-preference';

describe('theme registry', () => {
  it('contains exactly one theme: Baltic Blue', () => {
    expect(THEMES).toHaveLength(1);
    expect(THEMES[0].id).toBe('baltic-blue');
    expect(THEMES[0].name).toBe('Baltic Blue');
  });

  it('returns Baltic Blue as the default theme', () => {
    expect(getDefaultTheme().id).toBe('baltic-blue');
  });

  it('resolves baltic-blue by id and rejects removed theme ids', () => {
    expect(getThemeById('baltic-blue')?.id).toBe('baltic-blue');
    expect(getThemeById('corporate')).toBeUndefined();
    expect(getThemeById('earth-tones')).toBeUndefined();
    expect(getThemeById('green-dream')).toBeUndefined();
    expect(getThemeById('soft-pastel')).toBeUndefined();
    expect(getThemeById('picker')).toBeUndefined();
  });
});

describe('theme store', () => {
  beforeEach(() => {
    localStorage.clear();
    setActivePinia(createPinia());
  });

  it('exposes exactly one theme and applies it as the current theme', () => {
    const store = useThemeStore();

    expect(store.allThemes).toHaveLength(1);
    expect(store.currentThemeId).toBe('baltic-blue');
    expect(store.currentTheme.id).toBe('baltic-blue');
  });

  it('writes the theme semantic CSS variables to the document root', () => {
    useThemeStore();

    expect(document.documentElement.style.getPropertyValue('--color-surface-primary')).toBe('#05668d');
    expect(document.documentElement.style.getPropertyValue('--color-text-primary')).toBe('#05668d');
    expect(document.documentElement.style.getPropertyValue('--chart-color-1')).toBe('#05668d');
  });

  it('ignores setTheme calls with unknown theme ids', () => {
    const store = useThemeStore();

    store.setTheme('corporate');

    expect(store.currentThemeId).toBe('baltic-blue');
    expect(store.currentTheme.id).toBe('baltic-blue');
  });

  it('persists the theme id to localStorage on setTheme', () => {
    const store = useThemeStore();

    store.setTheme('baltic-blue');

    expect(localStorage.getItem(STORAGE_KEY)).toBe('"baltic-blue"');
  });

  it('falls back to the default theme when the persisted id is unknown', () => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify('corporate'));
    setActivePinia(createPinia());

    const store = useThemeStore();

    expect(store.currentThemeId).toBe('baltic-blue');
    expect(store.currentTheme.id).toBe('baltic-blue');
  });
});
