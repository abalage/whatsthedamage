/**
 * Unit tests for the UndoCorrectionCell undo button component
 * @module test/UndoCorrectionCell
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount, type VueWrapper } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import UndoCorrectionCell from '../src/components/data/UndoCorrectionCell.vue';

vi.mock('vue3-gettext', (): Record<string, unknown> => ({
  useGettext: (): { $gettext: (key: string) => string } => ({
    $gettext: (key: string): string => key,
  }),
}));

interface CellProps {
  corrected: boolean;
  undo: () => Promise<unknown>;
}

const mountCell = (props: CellProps): VueWrapper =>
  mount(UndoCorrectionCell, { props });

describe('UndoCorrectionCell', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setActivePinia(createPinia());
  });

  it('renders nothing for an uncorrected transaction', () => {
    const wrapper = mountCell({ corrected: false, undo: vi.fn() });

    expect(wrapper.find('button').exists()).toBe(false);
  });

  it('renders a labelled button for a corrected transaction', () => {
    const wrapper = mountCell({ corrected: true, undo: vi.fn() });

    const button = wrapper.find('button');
    expect(button.exists()).toBe(true);
    expect(button.text()).toContain('Undo');
    expect(button.attributes('title')).toBe('Undo corrections');
    expect(button.find('i.bi-arrow-counterclockwise').exists()).toBe(true);
  });

  it('calls undo on click', async () => {
    const undo = vi.fn().mockResolvedValue(undefined);
    const wrapper = mountCell({ corrected: true, undo });

    await wrapper.find('button').trigger('click');

    expect(undo).toHaveBeenCalledTimes(1);
  });

  it('shows the error when undo fails', async () => {
    const undo = vi.fn().mockRejectedValue(new Error('Undo failed'));
    const wrapper = mountCell({ corrected: true, undo });

    await wrapper.find('button').trigger('click');

    expect(wrapper.text()).toContain('Undo failed');
  });
});
