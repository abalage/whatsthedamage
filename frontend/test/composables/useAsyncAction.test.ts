/**
 * Unit tests for the useAsyncAction composable: loading and error
 * state, rethrow semantics, and loading reset in the finally path
 * @module test/composables/useAsyncAction
 */

import { describe, it, expect } from 'vitest';
import { useAsyncAction } from '../../src/composables/useAsyncAction';

describe('useAsyncAction', () => {
  it('returns the action result and reports loading', async () => {
    const { isLoading, error, run } = useAsyncAction();

    const promise = run(async (): Promise<string> => {
      expect(isLoading.value).toBe(true);
      return 'ok';
    });

    expect(await promise).toBe('ok');
    expect(isLoading.value).toBe(false);
    expect(error.value).toBeUndefined();
  });

  it('stores the error message and rethrows it', async () => {
    const { isLoading, error, run } = useAsyncAction();
    const failure = new Error('boom');

    await expect(run(async (): Promise<string> => {
      throw failure;
    })).rejects.toThrow('boom');

    expect(error.value).toBe('boom');
    expect(isLoading.value).toBe(false);
  });

  it('resets the loading flag in the finally path on failure', async () => {
    const { isLoading, run } = useAsyncAction();

    try {
      await run(async (): Promise<void> => {
        throw new Error('boom');
      });
    } catch {
      // expected
    }

    expect(isLoading.value).toBe(false);
  });

  it('clears the previous error on the next run', async () => {
    const { error, run } = useAsyncAction();

    try {
      await run(async (): Promise<void> => {
        throw new Error('first');
      });
    } catch {
      // expected
    }

    await run(async (): Promise<string> => 'second');
    expect(error.value).toBeUndefined();
  });

  it('stringifies non-Error rejections into the error message', async () => {
    const { error, run } = useAsyncAction();

    await expect(run(async (): Promise<void> => {
      throw 'plain failure';
    })).rejects.toBe('plain failure');

    expect(error.value).toBe('plain failure');
  });
});
