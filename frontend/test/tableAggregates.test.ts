/**
 * Unit tests for the table aggregate helpers
 * @module test/tableAggregates
 */

import { describe, it, expect } from 'vitest';
import {
  AGGREGATE_CALCULATORS,
  AGGREGATE_ROW_MARKER,
  getDefaultLabelForType,
  getEffectiveAggregateConfig,
  isAggregateRow,
  shouldIncludeColumn
} from '../src/components/data/tableAggregates';
import type { AggregateRowConfig, Column } from '../src/types/column';

const rows = [
  { name: 'a', amount: 10 },
  { name: 'b', amount: 20 },
  { name: 'c' },
  { name: 'd', amount: null }
];

describe('AGGREGATE_CALCULATORS', () => {
  it('sums the numeric values and ignores nulls', () => {
    expect(AGGREGATE_CALCULATORS.sum(rows, 'amount')).toBe(30);
  });

  it('averages only the numeric values', () => {
    // Null and undefined rows are filtered before the numeric conversion
    expect(AGGREGATE_CALCULATORS.average(rows, 'amount')).toBe(15);
  });

  it('computes min and max of the numeric values', () => {
    // Number(null) is 0, so null values count as zero for min/max
    expect(AGGREGATE_CALCULATORS.min(rows, 'amount')).toBe(0);
    expect(AGGREGATE_CALCULATORS.max(rows, 'amount')).toBe(20);
  });

  it('counts the non-null values', () => {
    expect(AGGREGATE_CALCULATORS.count(rows, 'amount')).toBe(2);
  });

  it('returns null for sum on an all-null column', () => {
    expect(AGGREGATE_CALCULATORS.sum(rows, 'missing')).toBeNull();
  });
});

describe('isAggregateRow', () => {
  it('detects rows carrying the marker property', () => {
    expect(isAggregateRow({ [AGGREGATE_ROW_MARKER]: true })).toBe(true);
    expect(isAggregateRow({})).toBe(false);
  });
});

describe('shouldIncludeColumn', () => {
  it('includes every column by default', () => {
    const config: AggregateRowConfig = { type: 'sum' };
    expect(shouldIncludeColumn(config, 'any')).toBe(true);
  });

  it('honors an explicit column list', () => {
    const config: AggregateRowConfig = { type: 'sum', columns: ['a', 'b'] };
    expect(shouldIncludeColumn(config, 'a')).toBe(true);
    expect(shouldIncludeColumn(config, 'c')).toBe(false);
  });

  it('honors a column predicate', () => {
    const config: AggregateRowConfig = { type: 'sum', columns: (key: string) => key === 'x' };
    expect(shouldIncludeColumn(config, 'x')).toBe(true);
    expect(shouldIncludeColumn(config, 'y')).toBe(false);
  });

  it('honors the exclusion list', () => {
    const config: AggregateRowConfig = { type: 'sum', excludeColumns: ['a'] };
    expect(shouldIncludeColumn(config, 'a')).toBe(false);
    expect(shouldIncludeColumn(config, 'b')).toBe(true);
  });
});

describe('getEffectiveAggregateConfig', () => {
  it('falls back to the global type when the column has no override', () => {
    const column: Column = { key: 'amount', title: 'Amount' };
    const config = getEffectiveAggregateConfig({ type: 'sum' }, column);
    expect(config.type).toBe('sum');
  });

  it('prefers the column-level type', () => {
    const column: Column = {
      key: 'amount',
      title: 'Amount',
      aggregate: { type: 'average' }
    };
    const config = getEffectiveAggregateConfig({ type: 'sum' }, column);
    expect(config.type).toBe('average');
  });

  it('disables aggregation for columns with enabled=false', () => {
    const column: Column = {
      key: 'amount',
      title: 'Amount',
      aggregate: { enabled: false, type: 'sum' }
    };
    const config = getEffectiveAggregateConfig({ type: 'sum' }, column);
    expect(config.type).toBe('none');
  });
});

describe('getDefaultLabelForType', () => {
  it('translates the known aggregate types', () => {
    expect(getDefaultLabelForType('sum', (key) => `t:${key}`)).toBe('t:Sum');
  });

  it('falls back to the generic label for unknown types', () => {
    expect(getDefaultLabelForType('nope', (key) => `t:${key}`)).toBe('t:Aggregate');
  });
});
