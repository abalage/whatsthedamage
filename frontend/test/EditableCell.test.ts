/**
 * Unit tests for the EditableCell inline editor component
 * @module test/EditableCell
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount, flushPromises, type VueWrapper } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import EditableCell from '../src/components/data/EditableCell.vue';
import { fetchCategories } from '../src/js/api.js';
import type { CategoryDefinition } from '../src/types/api.js';

vi.mock('vue3-gettext', (): Record<string, unknown> => ({
  useGettext: (): { $gettext: (key: string) => string } => ({
    $gettext: (key: string): string => key,
  }),
}));

vi.mock('../src/js/api.js', () => ({
  fetchCategories: vi.fn(),
  fetchCostOfLivingCategories: vi.fn(),
}));

const categories: CategoryDefinition[] = [
  { id: 'grocery', default_name: 'Grocery', patterns: [] },
  { id: 'housing', default_name: 'Housing', patterns: [] },
];

const mountCell = (
  editor: 'select' | 'text',
  props: Record<string, unknown>
): VueWrapper =>
  mount(EditableCell, {
    props: { editor, maxLength: 255, ...props },
  });

describe('category dropdown', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setActivePinia(createPinia());
    vi.mocked(fetchCategories).mockResolvedValue(categories);
  });

  it('shows the current category and enters edit mode on click', async () => {
    const wrapper = mountCell('select', { value: 'grocery', save: vi.fn() });

    expect(wrapper.text()).toContain('grocery');
    expect(wrapper.find('select').exists()).toBe(false);

    await wrapper.find('button').trigger('click');
    await flushPromises();

    expect(wrapper.find('select').exists()).toBe(true);
    expect((wrapper.find('select').element as HTMLSelectElement).value).toBe('grocery');
  });

  it('offers the backend categories plus an uncategorized option', async () => {
    const wrapper = mountCell('select', { value: 'grocery', save: vi.fn() });

    await wrapper.find('button').trigger('click');
    await flushPromises();

    const options = wrapper.findAll('option');
    const values = options.map(option => option.element as HTMLOptionElement).map(el => el.value);
    expect(values).toEqual(['', 'grocery', 'housing']);
  });

  it('saves the selected category', async () => {
    const save = vi.fn().mockResolvedValue(undefined);
    const wrapper = mountCell('select', { value: 'grocery', save: save });

    await wrapper.find('button').trigger('click');
    await flushPromises();
    await wrapper.find('select').setValue('housing');
    await wrapper.findAll('button')[0].trigger('click');

    expect(save).toHaveBeenCalledWith('housing');
    expect(wrapper.find('select').exists()).toBe(false);
  });

  it('saves null when the uncategorized option is selected', async () => {
    const save = vi.fn().mockResolvedValue(undefined);
    const wrapper = mountCell('select', { value: 'grocery', save: save });

    await wrapper.find('button').trigger('click');
    await flushPromises();
    await wrapper.find('select').setValue('');
    await wrapper.findAll('button')[0].trigger('click');

    expect(save).toHaveBeenCalledWith(null);
  });

  it('starts with the uncategorized option selected for uncategorized transactions', async () => {
    const wrapper = mountCell('select', { value: 'uncategorized', save: vi.fn() });

    await wrapper.find('button').trigger('click');
    await flushPromises();

    expect((wrapper.find('select').element as HTMLSelectElement).value).toBe('');
  });

  it('discards the edit on Cancel and on Esc', async () => {
    const save = vi.fn().mockResolvedValue(undefined);
    const wrapper = mountCell('select', { value: 'grocery', save: save });

    await wrapper.find('button').trigger('click');
    await flushPromises();
    await wrapper.find('select').setValue('housing');
    await wrapper.findAll('button')[1].trigger('click');

    expect(save).not.toHaveBeenCalled();

    await wrapper.find('button').trigger('click');
    await flushPromises();
    await wrapper.find('select').setValue('housing');
    await wrapper.find('select').trigger('keydown.esc');

    expect(save).not.toHaveBeenCalled();
    expect(wrapper.find('select').exists()).toBe(false);
  });

  it('discards the edit when the select loses focus', async () => {
    const save = vi.fn().mockResolvedValue(undefined);
    const wrapper = mountCell('select', { value: 'grocery', save: save });

    await wrapper.find('button').trigger('click');
    await flushPromises();
    await wrapper.find('select').setValue('housing');
    await wrapper.find('select').trigger('blur');

    expect(save).not.toHaveBeenCalled();
    expect(wrapper.find('select').exists()).toBe(false);
  });

  it('does not save when the selection is unchanged', async () => {
    const save = vi.fn().mockResolvedValue(undefined);
    const wrapper = mountCell('select', { value: 'grocery', save: save });

    await wrapper.find('button').trigger('click');
    await flushPromises();
    await wrapper.findAll('button')[0].trigger('click');

    expect(save).not.toHaveBeenCalled();
  });

  it('shows the error and stays in edit mode when saving fails', async () => {
    const save = vi.fn().mockRejectedValue(new Error('Update failed'));
    const wrapper = mountCell('select', { value: 'grocery', save: save });

    await wrapper.find('button').trigger('click');
    await flushPromises();
    await wrapper.find('select').setValue('housing');
    await wrapper.findAll('button')[0].trigger('click');

    expect(wrapper.text()).toContain('Update failed');
    expect(wrapper.find('select').exists()).toBe(true);
  });

  it('passes the apply-to-future state when the toggle is enabled', async () => {
    const save = vi.fn().mockResolvedValue(undefined);
    const wrapper = mountCell('select', { value: 'grocery', save, applyToFuture: true });

    await wrapper.find('button').trigger('click');
    await flushPromises();

    expect(wrapper.find('input[type="checkbox"]').exists()).toBe(true);

    await wrapper.find('select').setValue('housing');
    await wrapper.find('input[type="checkbox"]').setValue(false);
    await wrapper.findAll('button')[0].trigger('click');

    expect(save).toHaveBeenCalledWith('housing', false);
  });

  it('hides the apply-to-future toggle by default', async () => {
    const wrapper = mountCell('select', { value: 'grocery', save: vi.fn() });

    await wrapper.find('button').trigger('click');
    await flushPromises();

    expect(wrapper.find('input[type="checkbox"]').exists()).toBe(false);
  });
});

describe('free-text input', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setActivePinia(createPinia());
  });

  it('shows the value and enters edit mode on click', async () => {
    const wrapper = mountCell('text', { value: 'Store', save: vi.fn() });

    expect(wrapper.text()).toContain('Store');
    expect(wrapper.find('input').exists()).toBe(false);

    await wrapper.find('button').trigger('click');

    expect(wrapper.find('input').exists()).toBe(true);
    expect((wrapper.find('input').element as HTMLInputElement).value).toBe('Store');
  });

  it('saves the edited value', async () => {
    const save = vi.fn().mockResolvedValue(undefined);
    const wrapper = mountCell('text', { value: 'Store', save });

    await wrapper.find('button').trigger('click');
    await wrapper.find('input').setValue('New Store');
    await wrapper.findAll('button')[0].trigger('click');

    expect(save).toHaveBeenCalledWith('New Store');
    expect(wrapper.find('input').exists()).toBe(false);
  });

  it('saves when Enter is pressed', async () => {
    const save = vi.fn().mockResolvedValue(undefined);
    const wrapper = mountCell('text', { value: 'Store', save });

    await wrapper.find('button').trigger('click');
    await wrapper.find('input').setValue('New Store');
    await wrapper.find('input').trigger('keydown.enter');

    expect(save).toHaveBeenCalledWith('New Store');
  });

  it('discards the edit on Cancel and on Esc', async () => {
    const save = vi.fn().mockResolvedValue(undefined);
    const wrapper = mountCell('text', { value: 'Store', save });

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
    const wrapper = mountCell('text', { value: 'Store', save });

    await wrapper.find('button').trigger('click');
    await wrapper.find('input').setValue('New Store');
    await wrapper.find('input').trigger('blur');

    expect(save).not.toHaveBeenCalled();
    expect(wrapper.find('input').exists()).toBe(false);
  });

  it('saves an empty value when allowEmpty is not restricted', async () => {
    const save = vi.fn().mockResolvedValue(undefined);
    const wrapper = mountCell('text', { value: 'Store', save });

    await wrapper.find('button').trigger('click');
    await wrapper.find('input').setValue('');
    await wrapper.findAll('button')[0].trigger('click');

    expect(save).toHaveBeenCalledWith('');
  });

  it('rejects an empty value when allowEmpty is false', async () => {
    const save = vi.fn().mockResolvedValue(undefined);
    const wrapper = mountCell('text', { value: 'Store', allowEmpty: false, save });

    await wrapper.find('button').trigger('click');
    await wrapper.find('input').setValue('');
    await wrapper.findAll('button')[0].trigger('click');

    expect(save).not.toHaveBeenCalled();
    expect(wrapper.text()).toContain('Value must not be empty');
    expect(wrapper.find('input').exists()).toBe(true);
  });

  it('does not save when the value is unchanged', async () => {
    const save = vi.fn().mockResolvedValue(undefined);
    const wrapper = mountCell('text', { value: 'Store', save });

    await wrapper.find('button').trigger('click');
    await wrapper.find('input').setValue('Store');
    await wrapper.findAll('button')[0].trigger('click');

    expect(save).not.toHaveBeenCalled();
  });

  it('rejects values longer than maxLength', async () => {
    const save = vi.fn().mockResolvedValue(undefined);
    const wrapper = mountCell('text', { value: 'Store', maxLength: 5, save });

    await wrapper.find('button').trigger('click');
    await wrapper.find('input').setValue('Too long value');
    await wrapper.findAll('button')[0].trigger('click');

    expect(save).not.toHaveBeenCalled();
    expect(wrapper.text()).toContain('Value is too long');
    expect(wrapper.find('input').exists()).toBe(true);
  });

  it('shows the error and stays in edit mode when saving fails', async () => {
    const save = vi.fn().mockRejectedValue(new Error('Update failed'));
    const wrapper = mountCell('text', { value: 'Store', save });

    await wrapper.find('button').trigger('click');
    await wrapper.find('input').setValue('New Store');
    await wrapper.findAll('button')[0].trigger('click');

    expect(wrapper.text()).toContain('Update failed');
    expect(wrapper.find('input').exists()).toBe(true);
  });

  it('trims whitespace before saving', async () => {
    const save = vi.fn().mockResolvedValue(undefined);
    const wrapper = mountCell('text', { value: 'Store', save });

    await wrapper.find('button').trigger('click');
    await wrapper.find('input').setValue('  New Store  ');
    await wrapper.findAll('button')[0].trigger('click');

    expect(save).toHaveBeenCalledWith('New Store');
  });

  it('passes the apply-to-future state when the toggle is enabled', async () => {
    const save = vi.fn().mockResolvedValue(undefined);
    const wrapper = mountCell('text', { value: 'Store', applyToFuture: true, save });

    await wrapper.find('button').trigger('click');

    expect(wrapper.find('input[type="checkbox"]').exists()).toBe(true);

    await wrapper.find('input[type="text"]').setValue('New Store');
    await wrapper.find('input[type="checkbox"]').setValue(false);
    await wrapper.findAll('button')[0].trigger('click');

    expect(save).toHaveBeenCalledWith('New Store', false);
  });

  it('hides the apply-to-future toggle by default', async () => {
    const save = vi.fn().mockResolvedValue(undefined);
    const wrapper = mountCell('text', { value: 'Store', save });

    await wrapper.find('button').trigger('click');

    expect(wrapper.find('input[type="checkbox"]').exists()).toBe(false);
  });
});
