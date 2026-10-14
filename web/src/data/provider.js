// Imports
import {
  getMetadata,
  getSummary,
  getSourceHoldings,
  getSinkHoldings,
  getContractHoldings,
} from "../generated/client";

// Transformation: HTTP details stay outside the query hooks and UI.
function unwrap(response) {
  if (response.status !== 200) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.data;
}

const httpProvider = {
  async getContractHoldings(
    {
      reportId,
      accountHolder,
      settlementPoint,
      source,
      sink,
      deliveryMonth,
      hedgeType,
    },
    signal
  ) {
    return unwrap(
      await getContractHoldings(
        {
          report_id: reportId,
          source,
          sink,
          month: deliveryMonth,
          hedge_type: hedgeType,
          ...(accountHolder && { account_holder: accountHolder }),
          ...(settlementPoint && { settlement_point: settlementPoint }),
        },
        { signal }
      )
    );
  },
  async getSinkHoldings(
    { reportId, accountHolder, settlementPoint, source },
    signal
  ) {
    return unwrap(
      await getSinkHoldings(
        source,
        {
          report_id: reportId,
          ...(accountHolder && { account_holder: accountHolder }),
          ...(settlementPoint && { settlement_point: settlementPoint }),
        },
        { signal }
      )
    );
  },
  async getSourceHoldings(
    { reportId, accountHolder, settlementPoint, offset },
    signal
  ) {
    return unwrap(
      await getSourceHoldings(
        {
          report_id: reportId,
          offset,
          limit: 20,
          ...(accountHolder && { account_holder: accountHolder }),
          ...(settlementPoint && { settlement_point: settlementPoint }),
        },
        { signal }
      )
    );
  },
  async getMetadata({ reportId, accountHolder }, signal) {
    const response = await getMetadata(
      {
        ...(reportId != null && { report_id: reportId }),
        ...(accountHolder && { account_holder: accountHolder }),
      },
      { signal }
    );
    return unwrap(response);
  },
  async getSummary({ reportId, accountHolder, settlementPoint }, signal) {
    const response = await getSummary(
      {
        report_id: reportId,
        ...(accountHolder && { account_holder: accountHolder }),
        ...(settlementPoint && { settlement_point: settlementPoint }),
      },
      { signal }
    );
    return unwrap(response);
  },
};

// Output: swap the HTTP provider here for browser SQLite or VFS in Sprint 5.
export const dataProvider = httpProvider;
