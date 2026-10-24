/**
 * API contract tests: the hand-mirrored frontend types are asserted
 * against the backend's OpenAPI component schemas, checked in as a
 * generated fixture (make api-contract regenerates it; a backend
 * pytest fails when the fixture goes stale).
 *
 * The assertion is one-directional on purpose: every field the
 * frontend type declares must exist in the backend schema, so a
 * backend rename or removal of a consumed field breaks this test at
 * gate time. Backend-only additions (fields the frontend does not
 * model) do not fail.
 * @module test/apiContract
 */

import { describe, it, expect } from 'vitest';
import schemas from './fixtures/api-contract-schemas.json';
import type {
  User,
  RegisterResponse,
  LoginResponse,
  MeResponse,
  DataExportResponse
} from '../src/types/auth';
import type {
  TransactionListItem,
  ProcessingResultListItem,
  ProcessingResultMetadata
} from '../src/types/api';

/** Shape of one OpenAPI component schema in the fixture */
interface BackendSchema {
  required?: string[];
  properties?: Record<string, unknown>;
}

const schemasByName = schemas as Record<string, BackendSchema>;

/**
 * Assert that every frontend-declared field is provided by the
 * backend response schema.
 *
 * @param backendSchemaName - OpenAPI component schema name
 * @param frontendFields - All fields of the mirrored frontend type
 *     (the compiler rejects typos and unknown keys)
 */
function expectBackendProvidesAllFields<FrontendType>(
  backendSchemaName: string,
  frontendFields: Array<keyof FrontendType>
): void {
  const schema = schemasByName[backendSchemaName];
  expect(schema, `missing backend schema ${backendSchemaName}`).toBeDefined();
  const backendProps = Object.keys(schema?.properties ?? {});
  const missing = frontendFields.filter(
    field => !backendProps.includes(field as string)
  );
  expect(
    missing,
    `${backendSchemaName} no longer provides fields the frontend consumes`
  ).toEqual([]);
}

describe('API contract (frontend types vs backend OpenAPI fixture)', () => {
  it('User mirrors UserDetail', () => {
    const fields: Array<keyof User> = [
      'id', 'username', 'created_at', 'last_login_at', 'is_active',
      'opt_in_sharing', 'opted_in_at', 'opted_out_at', 'scheduled_deletion_at'
    ];
    expectBackendProvidesAllFields('UserDetail', fields);
  });

  it('RegisterResponse mirrors RegisterResponse', () => {
    const fields: Array<keyof RegisterResponse> = [
      'user', 'recovery_code', 'session_expires_at'
    ];
    expectBackendProvidesAllFields('RegisterResponse', fields);
  });

  it('LoginResponse mirrors LoginResponse', () => {
    const fields: Array<keyof LoginResponse> = ['user', 'session_expires_at'];
    expectBackendProvidesAllFields('LoginResponse', fields);
  });

  it('MeResponse mirrors MeResponse', () => {
    const fields: Array<keyof MeResponse> = ['user'];
    expectBackendProvidesAllFields('MeResponse', fields);
  });

  it('TransactionListItem mirrors TransactionApiResponse', () => {
    const fields: Array<keyof TransactionListItem> = [
      'id', 'user_id', 'result_id', 'date', 'transaction_type',
      'original_partner', 'amount', 'currency', 'account',
      'deduplication_hash', 'category_id', 'partner', 'notice',
      'original_category_id', 'original_notice', 'confidence',
      'created_at', 'updated_at'
    ];
    expectBackendProvidesAllFields('TransactionApiResponse', fields);
  });

  it('ProcessingResultListItem mirrors ProcessingResultListItem', () => {
    const fields: Array<keyof ProcessingResultListItem> = [
      'id', 'csv_profile_id', 'row_count', 'processing_time', 'ml_enabled',
      'start_date', 'end_date', 'transaction_start_date',
      'transaction_end_date', 'created_at'
    ];
    expectBackendProvidesAllFields('ProcessingResultListItem', fields);
  });

  it('ProcessingResultMetadata mirrors ProcessingResultMetadata', () => {
    const fields: Array<keyof ProcessingResultMetadata> = [
      'result_id', 'user_id', 'csv_profile_id', 'row_count',
      'processing_time', 'ml_enabled', 'start_date', 'end_date',
      'transaction_start_date', 'transaction_end_date', 'created_at',
      'transactions_url'
    ];
    expectBackendProvidesAllFields('ProcessingResultMetadata', fields);
  });

  it('DataExportResponse mirrors DataExportResponse', () => {
    const fields: Array<keyof DataExportResponse> = [
      'generated_at', 'account', 'processing_results', 'transactions',
      'corrections'
    ];
    expectBackendProvidesAllFields('DataExportResponse', fields);
  });
});
