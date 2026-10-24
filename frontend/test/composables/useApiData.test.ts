/**
 * Unit tests for the useApiData composable: fetching only, with no
 * Pinia or gettext setup required
 * @module test/composables/useApiData
 */

import { describe, it, expect, vi } from 'vitest';
import { useApiData } from '../../src/composables/useApiData';

describe('useApiData', () => {
  it('stores fetched data and reports loading', async () => {
    const { data, isLoading, error, fetchData } = useApiData({ fetchFn: async () => 'payload' });

    const promise = fetchData();
    expect(isLoading.value).toBe(true);
    await promise;

    expect(data.value).toBe('payload');
    expect(isLoading.value).toBe(false);
    expect(error.value).toBeUndefined();
  });

  it('stores the error message without rethrowing', async () => {
    const { data, isLoading, error, fetchData } = useApiData({
      fetchFn: async (): Promise<string> => {
        throw new Error('network down');
      }
    });

    await expect(fetchData()).resolves.toBeUndefined();

    expect(error.value).toBe('network down');
    expect(data.value).toBeUndefined();
    expect(isLoading.value).toBe(false);
  });

  it('runs the onError side effect on failure', async () => {
    const onError = vi.fn();
    const failure = new Error('boom');
    const { fetchData } = useApiData({
      fetchFn: async (): Promise<void> => {
        throw failure;
      },
      onError
    });

    await fetchData();

    expect(onError).toHaveBeenCalledWith(failure);
  });

  it('keeps the previous data when a refetch fails', async () => {
    let shouldFail = false;
    const { data, error, fetchData } = useApiData({
      fetchFn: async (): Promise<string> => {
        if (shouldFail) {
          throw new Error('refetch failed');
        }
        return 'first';
      }
    });

    await fetchData();
    expect(data.value).toBe('first');

    shouldFail = true;
    await fetchData();
    expect(data.value).toBe('first');
    expect(error.value).toBe('refetch failed');
  });

  it('clears the previous error on a successful refetch', async () => {
    let shouldFail = true;
    const { error, fetchData } = useApiData({
      fetchFn: async (): Promise<string> => {
        if (shouldFail) {
          throw new Error('first attempt');
        }
        return 'ok';
      }
    });

    await fetchData();
    expect(error.value).toBe('first attempt');

    shouldFail = false;
    await fetchData();
    expect(error.value).toBeUndefined();
  });
});
