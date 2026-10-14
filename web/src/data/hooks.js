// Imports
import { useQuery } from '@tanstack/react-query';
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
