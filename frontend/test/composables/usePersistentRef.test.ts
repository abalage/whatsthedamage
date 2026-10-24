/**
 * Unit tests for the localStorage-persisted ref composable
 * @module test/composables/usePersistentRef
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { usePersistentRef, clearPersisted } from '../../src/composables/usePersistentRef';

describe('usePersistentRef', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('uses the default value when nothing is stored', () => {
    const state = usePersistentRef('key', ['a'], (v): v is string[] => Array.isArray(v));
    expect(state.value).toEqual(['a']);
  });

  it('initializes from a stored JSON value', () => {
    localStorage.setItem('key', JSON.stringify(['x', 'y']));
    const state = usePersistentRef('key', ['a'], (v): v is string[] => Array.isArray(v));
    expect(state.value).toEqual(['x', 'y']);
  });

  it('accepts the legacy raw-string storage format', () => {
    localStorage.setItem('key', 'hu');
    const state = usePersistentRef('key', 'en', (v): v is string => typeof v === 'string');
    expect(state.value).toBe('hu');
  });

  it('falls back to the default for values failing validation', () => {
    localStorage.setItem('key', JSON.stringify({ not: 'a string' }));
    const state = usePersistentRef('key', 'en', (v): v is string => typeof v === 'string');
    expect(state.value).toBe('en');
  });

  it('falls back to the default for malformed JSON', () => {
    localStorage.setItem('key', '{broken');
    const state = usePersistentRef('key', true, (v): v is boolean => typeof v === 'boolean');
    expect(state.value).toBe(true);
  });

  it('persists writes as JSON', () => {
    const state = usePersistentRef('key', 1, (v): v is number => typeof v === 'number');
    state.value = 42;
    expect(localStorage.getItem('key')).toBe('42');
  });

  it('reads back persisted writes in a new instance', () => {
    const state = usePersistentRef('key', 1, (v): v is number => typeof v === 'number');
    state.value = 42;

    const second = usePersistentRef('key', 1, (v): v is number => typeof v === 'number');
    expect(second.value).toBe(42);
  });

  it('clearPersisted removes the stored value', () => {
    const state = usePersistentRef('key', 1, (v): v is number => typeof v === 'number');
    state.value = 42;
    clearPersisted('key');
    expect(localStorage.getItem('key')).toBeNull();

    const fresh = usePersistentRef('key', 7, (v): v is number => typeof v === 'number');
    expect(fresh.value).toBe(7);
  });
});
