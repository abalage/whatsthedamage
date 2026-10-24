/**
 * Unit tests for the v-popover directive: text-only default and
 * opt-in HTML handling
 * @module test/popover
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { mount } from '@vue/test-utils';
import { defineComponent } from 'vue';
import { popoverDirective } from '../src/directives/popover';

class PopoverMock {
  static instances = new Map<Element, PopoverMock>()
  static ctorSpy = vi.fn()

  static getInstance(el: Element): PopoverMock | undefined {
    return PopoverMock.instances.get(el)
  }

  constructor(el: Element, opts: unknown) {
    PopoverMock.ctorSpy(el, opts)
    PopoverMock.instances.set(el, this)
  }

  dispose(): void {
    // no-op; instance cleanup is Bootstrap's own behavior
  }
}

const mountWithPopover = (options: Record<string, unknown>): ReturnType<typeof mount> => {
  const component = defineComponent({
    props: { options: { type: Object, required: true } },
    template: '<span v-popover="options">Hover me</span>'
  })
  return mount(component, {
    props: { options },
    global: {
      directives: { popover: popoverDirective }
    }
  })
}

describe('popover directive', () => {
  beforeEach(() => {
    PopoverMock.ctorSpy.mockClear()
    PopoverMock.instances.clear()
    ;(globalThis as unknown as Window).bootstrap = { Popover: PopoverMock }
  })

  afterEach(() => {
    delete (globalThis as unknown as { bootstrap?: unknown }).bootstrap
  })

  it('initializes the popover as text-only by default', () => {
    mountWithPopover({ content: 'line one\nline two' })

    expect(PopoverMock.ctorSpy).toHaveBeenCalledTimes(1)
    const [, opts] = PopoverMock.ctorSpy.mock.calls[0] as [Element, Record<string, unknown>]
    expect(opts.html).toBe(false)
    expect(opts.content).toBe('line one\nline two')
  })

  it('allows HTML only when explicitly opted in', () => {
    mountWithPopover({ content: '<strong>trusted</strong>', html: true })

    const [, opts] = PopoverMock.ctorSpy.mock.calls[0] as [Element, Record<string, unknown>]
    expect(opts.html).toBe(true)
  })

  it('does not initialize without content', () => {
    mountWithPopover({})

    expect(PopoverMock.ctorSpy).not.toHaveBeenCalled()
  })
})
