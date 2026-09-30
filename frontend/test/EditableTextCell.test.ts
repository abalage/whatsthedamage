/**
 * Unit tests for the EditableTextCell inline editor component
 * @module test/EditableTextCell
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount, type VueWrapper } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import EditableTextCell from '../src/components/data/EditableTextCell.vue';

vi.mock('vue3-gettext', (): Record<string, unknown> => ({
  useGettext: (): { $gettext: (key: string) => string } => ({
    $gettext: (key: string): string => key,
  }),
}));

interface CellProps {
  value: string;
  maxLength?: number;
  allowEmpty?: boolean;
  save: (value: string) => Promise<unknown>;
}

const mountCell = (props: CellProps): VueWrapper =>
  mount(EditableTextCell, {
    props: {
      maxLength: 255,
      ...props,
    },
  });

describe('EditableTextCell', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setActivePinia(createPinia());
  });

  it('shows the value and enters edit mode on click', async () => {
    const wrapper = mountCell({ value: 'Store', save: vi.fn() });

    expect(wrapper.text()).toContain('Store');
    expect(wrapper.find('input').exists()).toBe(false);

    await wrapper.find('button').trigger('click');

    expect(wrapper.find('input').exists()).toBe(true);
    expect((wrapper.find('input').element as HTMLInputElement).value).toBe('Store');
  });

  it('saves the edited value', async () => {
    const save = vi.fn().mockResolvedValue(undefined);
    const wrapper = mountCell({ value: 'Store', save });

    await wrapper.find('button').trigger('click');
    await wrapper.find('input').setValue('New Store');
    await wrapper.findAll('button')[0].trigger('click');

    expect(save).toHaveBeenCalledWith('New Store');
    expect(wrapper.find('input').exists()).toBe(false);
  });

  it('saves when Enter is pressed', async () => {
    const save = vi.fn().mockResolvedValue(undefined);
    const wrapper = mountCell({ value: 'Store', save });

    await wrapper.find('button').trigger('click');
    await wrapper.find('input').setValue('New Store');
    await wrapper.find('input').trigger('keydown.enter');

    expect(save).toHaveBeenCalledWith('New Store');
  });

  it('discards the edit on Cancel and on Esc', async () => {
    const save = vi.fn().mockResolvedValue(undefined);
    const wrapper = mountCell({ value: 'Store', save });

    await wrapper.find('button').trigger('click');
    await wrapper.find('input').setValue('New Store');
    await wrapper.findAll('button')[1].trigger('click');

    expect(save).not.toHaveBeenCalled();
    expect(wrapper.find('input').exists()).toBe(false);

    await wrapper.find('button').trigger('click');
    await wrapper.find('input').setValue('New Store');
    await wrapper.find('input').trigger('keydown.esc');

    expect(save).not.toHaveBeenCalled();
    expect(wrapper.find('input').exists()).toBe(false);
  });

  it('discards the edit when the input loses focus', async () => {
    const save = vi.fn().mockResolvedValue(undefined);
    const wrapper = mountCell({ value: 'Store', save });

    await wrapper.find('button').trigger('click');
    await wrapper.find('input').setValue('New Store');
    await wrapper.find('input').trigger('blur');

    expect(save).not.toHaveBeenCalled();
    expect(wrapper.find('input').exists()).toBe(false);
  });

  it('saves an empty value when allowEmpty is not restricted', async () => {
    const save = vi.fn().mockResolvedValue(undefined);
    const wrapper = mountCell({ value: 'Store', save });

    await wrapper.find('button').trigger('click');
    await wrapper.find('input').setValue('');
    await wrapper.findAll('button')[0].trigger('click');

    expect(save).toHaveBeenCalledWith('');
  });

  it('rejects an empty value when allowEmpty is false', async () => {
    const save = vi.fn().mockResolvedValue(undefined);
    const wrapper = mountCell({ value: 'Store', allowEmpty: false, save });

    await wrapper.find('button').trigger('click');
    await wrapper.find('input').setValue('');
    await wrapper.findAll('button')[0].trigger('click');

    expect(save).not.toHaveBeenCalled();
    expect(wrapper.text()).toContain('Value must not be empty');
    expect(wrapper.find('input').exists()).toBe(true);
  });

  it('does not save when the value is unchanged', async () => {
    const save = vi.fn().mockResolvedValue(undefined);
    const wrapper = mountCell({ value: 'Store', save });

    await wrapper.find('button').trigger('click');
    await wrapper.find('input').setValue('Store');
    await wrapper.findAll('button')[0].trigger('click');

    expect(save).not.toHaveBeenCalled();
  });

  it('rejects values longer than maxLength', async () => {
    const save = vi.fn().mockResolvedValue(undefined);
    const wrapper = mountCell({ value: 'Store', maxLength: 5, save });

    await wrapper.find('button').trigger('click');
    await wrapper.find('input').setValue('Too long value');
    await wrapper.findAll('button')[0].trigger('click');

    expect(save).not.toHaveBeenCalled();
    expect(wrapper.text()).toContain('Value is too long');
    expect(wrapper.find('input').exists()).toBe(true);
  });

  it('shows the error and stays in edit mode when saving fails', async () => {
    const save = vi.fn().mockRejectedValue(new Error('Update failed'));
    const wrapper = mountCell({ value: 'Store', save });

    await wrapper.find('button').trigger('click');
    await wrapper.find('input').setValue('New Store');
    await wrapper.findAll('button')[0].trigger('click');

    expect(wrapper.text()).toContain('Update failed');
    expect(wrapper.find('input').exists()).toBe(true);
  });

  it('trims whitespace before saving', async () => {
    const save = vi.fn().mockResolvedValue(undefined);
    const wrapper = mountCell({ value: 'Store', save });

    await wrapper.find('button').trigger('click');
    await wrapper.find('input').setValue('  New Store  ');
    await wrapper.findAll('button')[0].trigger('click');

    expect(save).toHaveBeenCalledWith('New Store');
  });
});
