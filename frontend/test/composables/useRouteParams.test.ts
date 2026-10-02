/**
 * Unit tests for useRouteParams composable
 * @module test/composables/useRouteParams
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount } from '@vue/test-utils';
import { defineComponent, reactive, nextTick } from 'vue';
import { useRouteParams } from '../../src/composables/useRouteParams.js';

const mockRoute = reactive<{ params: Record<string, unknown>; query: Record<string, unknown> }>({
  params: {},
  query: {},
});

vi.mock('vue-router', (): Record<string, unknown> => ({
  useRoute: () => mockRoute,
}));

const Harness = defineComponent({
  setup() {
    const { resultId, stringParams } = useRouteParams();
    return { resultId, stringParams };
  },
  template: '<div />',
});

const mountHarness = (): { resultId: () => string | null; stringParams: () => Record<string, string | null> } => {
  const wrapper = mount(Harness);
  const vm = wrapper.vm as unknown as {
    resultId: string | null;
    stringParams: Record<string, string | null>;
  };
  return {
    resultId: () => vm.resultId,
    stringParams: () => vm.stringParams,
  };
};

describe('useRouteParams', () => {
  beforeEach(() => {
    mockRoute.params = {};
    mockRoute.query = {};
  });

  it('reads resultId from the query string', () => {
    mockRoute.query = { resultId: 'from-query' };
    const harness = mountHarness();
    expect(harness.resultId()).toBe('from-query');
  });

  it('returns null when no resultId is present', () => {
    const harness = mountHarness();
    expect(harness.resultId()).toBe(null);
  });

  it('includes the query resultId in stringParams for API calls', () => {
    mockRoute.params = { accountId: 'a1', categoryId: 'c1' };
    mockRoute.query = { resultId: 'r1' };
    const harness = mountHarness();
    expect(harness.stringParams()).toEqual({
      accountId: 'a1',
      categoryId: 'c1',
      resultId: 'r1',
    });
  });

  it('keeps resultId null in stringParams when absent', () => {
    mockRoute.params = { accountId: 'a1' };
    const harness = mountHarness();
    expect(harness.stringParams()).toEqual({
      accountId: 'a1',
      resultId: null,
    });
  });

  it('reacts to query changes', async () => {
    mockRoute.query = { resultId: 'r1' };
    const harness = mountHarness();
    expect(harness.resultId()).toBe('r1');

    mockRoute.query = {};
    await nextTick();
    expect(harness.resultId()).toBe(null);
  });
});
