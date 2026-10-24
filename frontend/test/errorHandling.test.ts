/**
 * Unit tests for the global error handlers: Vue errors from a
 * failing component and unhandled promise rejections are captured
 * and routed to the logger
 * @module test/errorHandling
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { createApp, defineComponent } from 'vue';
import { installGlobalErrorHandlers } from '../src/js/errorHandling';
import { logger } from '../src/js/logger';

const loggedMessages = (errorSpy: ReturnType<typeof vi.spyOn>): string =>
  errorSpy.mock.calls.map((call: unknown[]) => String(call[0])).join(' ');

describe('global error handlers', () => {
  let errorSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    errorSpy = vi.spyOn(logger, 'error').mockImplementation((): undefined => undefined);
  });

  afterEach(() => {
    errorSpy.mockRestore();
  });

  it('captures an error thrown by a failing component', () => {
    const host = document.createElement('div');
    document.body.appendChild(host);

    // eslint-disable-next-line vue/one-component-per-file -- test fixture
    const FailingComponent = defineComponent({
      setup: (): unknown => {
        throw new Error('deliberate failure');
      },
      template: '<p>never rendered</p>'
    });

    const app = createApp(FailingComponent);
    installGlobalErrorHandlers(app);
    app.mount(host);

    expect(errorSpy).toHaveBeenCalled();
    const logged = loggedMessages(errorSpy);
    expect(logged).toContain('deliberate failure');
    expect(logged).toContain('Unhandled Vue error');

    app.unmount();
    host.remove();
  });

  it('captures unhandled promise rejections', () => {
    // eslint-disable-next-line vue/one-component-per-file -- test fixture
    const app = createApp(defineComponent({ template: '<p>ok</p>' }));
    installGlobalErrorHandlers(app);

    const event = new Event('unhandledrejection') as PromiseRejectionEvent;
    (event as unknown as { reason: unknown }).reason = new Error('rejected');
    window.dispatchEvent(event);

    expect(errorSpy).toHaveBeenCalled();
    const logged = loggedMessages(errorSpy);
    expect(logged).toContain('rejected');
    expect(logged).toContain('Unhandled promise rejection');
  });
});
