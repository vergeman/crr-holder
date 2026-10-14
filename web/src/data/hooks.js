// Imports
import { useQuery, useInfiniteQuery } from '@tanstack/react-query';
import { dataProvider } from './provider';

// Output: keys describe the same filters passed to the selected provider.
export function useMetadata(reportId, accountHolder = '') {
  return useQuery({
    queryKey: ['metadata', reportId, accountHolder],
    queryFn: ({ signal }) => dataProvider.getMetadata({ reportId, accountHolder }, signal),
    staleTime: 60_000,
  });
}

export function useSummary(reportId, accountHolder, settlementPoint) {
  return useQuery({
    queryKey: ['summary', reportId, accountHolder, settlementPoint],
    queryFn: ({ signal }) => dataProvider.getSummary(
      { reportId, accountHolder, settlementPoint }, signal),
    enabled: reportId != null,
    staleTime: 60_000,
  });
}

// Output: each portfolio owns its source pages and cancellation signal.
export function useSourceHoldings(reportId, accountHolder, settlementPoint) {
  return useInfiniteQuery({
    queryKey: ['source-holdings', reportId, accountHolder, settlementPoint],
    queryFn: ({ signal, pageParam }) => dataProvider.getSourceHoldings(
      { reportId, accountHolder, settlementPoint, offset: pageParam }, signal),
    initialPageParam: 0,
    getNextPageParam: (page) => page.nextOffset ?? undefined,
    enabled: reportId != null,
    staleTime: 60_000,
  });
}

// Output: mounted expansions fetch only their source under the active portfolio.
export function useSinkHoldings(reportId, accountHolder, settlementPoint, source) {
  return useQuery({
    queryKey: ['sink-holdings', reportId, accountHolder, settlementPoint, source],
    queryFn: ({ signal }) => dataProvider.getSinkHoldings(
      { reportId, accountHolder, settlementPoint, source }, signal),
    enabled: reportId != null,
    staleTime: 60_000,
  });
}

// Output: only an open cell requests details under its full portfolio identity.
export function useContractHoldings(reportId, accountHolder, settlementPoint, selection) {
  return useQuery({
    queryKey: ['contract-holdings', reportId, accountHolder, settlementPoint,
      selection.source, selection.sink, selection.deliveryMonth, selection.hedgeType],
    queryFn: ({ signal }) => dataProvider.getContractHoldings(
      { reportId, accountHolder, settlementPoint, ...selection }, signal),
    enabled: reportId != null,
    staleTime: 60_000,
  });
}
