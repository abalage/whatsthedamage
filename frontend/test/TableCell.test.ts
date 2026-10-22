/**
 * Unit tests for the TableCell component
 * @module test/TableCell
 */

import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import { defineComponent } from 'vue';
import TableCell from '../src/components/data/TableCell.vue';
import type { Column } from '../src/types/column';

const ValueComponent = defineComponent({
  props: { value: { type: null, required: true } },
  template: '<span class="value-component">{{ value }}</span>'
});

describe('TableCell.vue', () => {
  const row = { name: 'row' };

  it('renders plain values as text', () => {
    const column: Column = { key: 'name', title: 'Name' };
    const wrapper = mount(TableCell, {
      props: { column, value: 'hello', row, index: 0 }
    });
    expect(wrapper.text()).toBe('hello');
  });

  it('renders null and undefined values as empty text', () => {
    const column: Column = { key: 'name', title: 'Name' };
    const wrapper = mount(TableCell, {
      props: { column, value: null, row, index: 0 }
    });
    expect(wrapper.text()).toBe('');
  });

  it('renders custom HTML for renderHtml columns', () => {
    const column: Column = {
      key: 'name',
      title: 'Name',
      renderHtml: (value: unknown) => `<strong>${String(value)}</strong>`
    };
    const wrapper = mount(TableCell, {
      props: { column, value: 'bold', row, index: 0 }
    });
    expect(wrapper.html()).toContain('<strong>bold</strong>');
  });

  it('renders the column component with its computed props', () => {
    const column: Column = {
      key: 'name',
      title: 'Name',
      component: ValueComponent,
      componentProps: (value: unknown) => ({ value: String(value) })
    };
    const wrapper = mount(TableCell, {
      props: { column, value: 'comp', row, index: 3 }
    });
    expect(wrapper.find('.value-component').text()).toBe('comp');
  });

  it('renders plain text for aggregate rows when asText is set', () => {
    const column: Column = {
      key: 'name',
      title: 'Name',
      component: ValueComponent,
      componentProps: (value: unknown) => ({ value: String(value) })
    };
    const wrapper = mount(TableCell, {
      props: { column, value: 'aggregate', row, index: 0, asText: true }
    });
    expect(wrapper.find('.value-component').exists()).toBe(false);
    expect(wrapper.text()).toBe('aggregate');
  });
});
