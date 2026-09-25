/**
 * Unit tests for route utility functions
 * @module test/routeUtils
 */

import { describe, it, expect } from 'vitest';
import { buildResultQuery, extractResultId } from '../src/js/routeUtils.js';

describe('buildResultQuery', () => {
  it('returns an empty query for a null resultId', () => {
    expect(buildResultQuery(null)).toEqual({});
  });

  it('returns an empty query for an undefined resultId', () => {
    expect(buildResultQuery(undefined)).toEqual({});
  });

  it('returns an empty query for an empty string resultId', () => {
    expect(buildResultQuery('')).toEqual({});
  });

  it('returns the resultId query for a provided resultId', () => {
    expect(buildResultQuery('r1')).toEqual({ resultId: 'r1' });
  });
});

describe('extractResultId', () => {
  it('returns the string value of resultId', () => {
    expect(extractResultId({ resultId: 'r1' })).toBe('r1');
  });

  it('returns the first element of an array value', () => {
    expect(extractResultId({ resultId: ['r1', 'r2'] })).toBe('r1');
  });

  it('ignores the snake_case result_id key', () => {
    expect(extractResultId({ result_id: 'r1' })).toBe(null);
  });

  it('returns null when resultId is missing', () => {
    expect(extractResultId({})).toBe(null);
  });

  it('returns null for an empty string value', () => {
    expect(extractResultId({ resultId: '' })).toBe(null);
  });

  it('returns null for a null value', () => {
    expect(extractResultId({ resultId: null })).toBe(null);
  });
});
