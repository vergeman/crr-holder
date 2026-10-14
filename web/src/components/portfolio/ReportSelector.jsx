export default function ReportSelector({
  reportMetadata,
  reportId,
  onReportSelect,
}) {
  return (
    <label>
      Report
      <select
        value={reportId ?? ""}
        disabled={!reportMetadata.data}
        onChange={(event) => onReportSelect(event.target.value)}
      >
        {!reportMetadata.data && <option value="">Loading reports...</option>}
        {reportMetadata.data?.reports.map((report) => (
          <option key={report.reportId} value={report.reportId}>
            {report.publicationDate}
          </option>
        ))}
      </select>
    </label>
  );
}
