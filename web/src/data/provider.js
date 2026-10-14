// Imports
import { getMetadata, getSummary } from '../generated/client';
import { wasmProvider } from './wasm-provider';

// Transformation: HTTP details stay outside the query hooks and UI.
function unwrap(response) {
  if (response.status !== 200) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.data;
}

const httpProvider = {
  async getMetadata({ reportId, accountHolder }, signal) {
    const response = await getMetadata({
      ...(reportId != null && { report_id: reportId }),
      ...(accountHolder && { account_holder: accountHolder }),
    }, { signal });
    return unwrap(response);
  },
  async getSummary({ reportId, accountHolder, settlementPoint }, signal) {
    const response = await getSummary({
      report_id: reportId,
      ...(accountHolder && { account_holder: accountHolder }),
      ...(settlementPoint && { settlement_point: settlementPoint }),
    }, { signal });
    return unwrap(response);
  },
};

// Output: select browser SQLite at startup; HTTP remains the default baseline.
export const dataProvider = import.meta.env.VITE_DATA_PROVIDER === 'wasm'
  ? wasmProvider : httpProvider;
