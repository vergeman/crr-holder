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
