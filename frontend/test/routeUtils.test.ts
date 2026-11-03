/**
 * Unit tests for route utility functions
 * @module test/routeUtils
 */

import { describe, it, expect } from 'vitest';
import { buildRedirectQuery, buildResultQuery, extractResultId, safeRedirectParam } from '../src/js/routeUtils';

describe('buildResultQuery', () => {
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
    expect(extractResultId({ result_id: 'r1' })).toBe(undefined);
  });

  it('returns undefined when resultId is missing', () => {
    expect(extractResultId({})).toBe(undefined);
  });

  it('returns undefined for an empty string value', () => {
    expect(extractResultId({ resultId: '' })).toBe(undefined);
  });

  it('returns undefined for a null value', () => {
    expect(extractResultId({ resultId: null })).toBe(undefined);
  });
});

describe('safeRedirectParam', () => {
  it('returns the redirect path for a same-app path', () => {
    expect(safeRedirectParam({ redirect: '/import' })).toBe('/import');
  });

  it('returns undefined when redirect is missing, empty, or not a string', () => {
    expect(safeRedirectParam({})).toBe(undefined);
    expect(safeRedirectParam({ redirect: '' })).toBe(undefined);
    expect(safeRedirectParam({ redirect: null })).toBe(undefined);
    expect(safeRedirectParam({ redirect: ['/import'] })).toBe(undefined);
    expect(safeRedirectParam({ redirect: 42 })).toBe(undefined);
  });

  it('rejects external and protocol-relative URLs', () => {
    expect(safeRedirectParam({ redirect: 'https://evil.example.com' })).toBe(undefined);
    expect(safeRedirectParam({ redirect: '//evil.example.com' })).toBe(undefined);
    expect(safeRedirectParam({ redirect: 'evil.example.com' })).toBe(undefined);
  });
});

describe('buildRedirectQuery', () => {
  it('returns an empty query for an undefined redirect', () => {
    expect(buildRedirectQuery(undefined)).toEqual({});
  });

  it('returns the redirect query for a provided redirect', () => {
    expect(buildRedirectQuery('/import')).toEqual({ redirect: '/import' });
  });
});
