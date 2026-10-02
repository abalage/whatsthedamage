/**
 * Unit tests for useResultQuery composable
 * @module test/composables/useResultQuery
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount } from '@vue/test-utils';
import { defineComponent, reactive, nextTick } from 'vue';
import { useResultQuery } from '../../src/composables/useResultQuery.js';

const mockRoute = reactive<{ query: Record<string, unknown> }>({ query: {} });

vi.mock('vue-router', (): Record<string, unknown> => ({
  useRoute: (): { query: Record<string, unknown> } => mockRoute,
}));

const Harness = defineComponent({
  setup() {
    const resultQuery = useResultQuery();
    return { resultQuery };
  },
  template: '<div />',
});

const mountHarness = (): (() => { resultId?: string }) => {
  const wrapper = mount(Harness);
  const vm = wrapper.vm as unknown as { resultQuery: () => { resultId?: string } };
  return () => vm.resultQuery();
};

describe('useResultQuery', () => {
  beforeEach(() => {
    mockRoute.query = {};
  });

  it('builds an empty query when no resultId is present', () => {
    const resultQuery = mountHarness();
    expect(resultQuery()).toEqual({});
  });

  it('carries the resultId from the query string', () => {
    mockRoute.query = { resultId: 'r1' };
    const resultQuery = mountHarness();
    expect(resultQuery()).toEqual({ resultId: 'r1' });
  });

  it('reacts to query changes', async () => {
    mockRoute.query = { resultId: 'r1' };
    const resultQuery = mountHarness();
    expect(resultQuery()).toEqual({ resultId: 'r1' });

    mockRoute.query = {};
    await nextTick();
    expect(resultQuery()).toEqual({});
  });
});
