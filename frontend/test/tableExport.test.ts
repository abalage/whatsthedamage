/**
 * Unit tests for the table export helpers
 * @module test/tableExport
 */

import { describe, it, expect } from 'vitest';
import { buildExportRows } from '../src/js/tableExport';
import type { AggregateRowConfig, Column } from '../src/types/column';

const columns: Column[] = [
  { key: 'name', title: 'Name' },
  { key: 'total', title: 'Total' }
];

const rows = [
  { name: 'plain', total: 10 },
  { name: '<b>bold</b>', total: 20 }
];

const htmlColumns: Column[] = [
  {
    key: 'name',
    title: 'Name',
    renderHtml: (value: unknown) => `<a href="#">${String(value)}</a>`
  },
  { key: 'total', title: 'Total' }
];

describe('buildExportRows', () => {
  it('exports plain values in column order', () => {
    const exported = buildExportRows(columns, rows, [], []);
    expect(exported).toEqual([
      ['plain', '10'],
      ['<b>bold</b>', '20']
    ]);
  });

  it('strips HTML tags from renderHtml columns', () => {
    const exported = buildExportRows(htmlColumns, [{ name: 'link', total: 1 }], [], []);
    expect(exported).toEqual([['link', '1']]);
  });

  it('exports empty strings for null and undefined values', () => {
    const exported = buildExportRows(columns, [{ name: null, total: undefined }], [], []);
    expect(exported).toEqual([['', '']]);
  });

  it('appends exportable aggregate rows after the data rows', () => {
    const aggregateRows: AggregateRowConfig[] = [
      {
        id: 'total-sum',
        type: 'custom',
        includeInExport: true,
        customCalculator: (_data, columnKey) => columnKey === 'name' ? 'Total' : 30
      },
      {
        id: 'hidden',
        type: 'custom',
        includeInExport: false,
        customCalculator: () => 'hidden'
      }
    ];
    const aggregateRowData = [
      { name: 'Total', total: '30' },
      { name: 'hidden', total: 'hidden' }
    ];

    const exported = buildExportRows(columns, rows, aggregateRows, aggregateRowData);
    expect(exported).toEqual([
      ['plain', '10'],
      ['<b>bold</b>', '20'],
      ['Total', '30']
    ]);
  });
});
