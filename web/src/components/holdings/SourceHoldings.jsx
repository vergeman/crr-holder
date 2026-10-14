// Imports
import { Fragment, useEffect, useRef, useState } from "react";
import { useSourceHoldings } from "../../data/hooks";
import SinkHoldings from "./SinkHoldings";

// Preparation: month-only formatting avoids timezone changes to delivery dates.
const monthLabel = (month) =>
  new Date(`${month}T00:00:00Z`).toLocaleDateString("en-US", {
    month: "short",
    year: "numeric",
    timeZone: "UTC",
  });

export default function SourceHoldings({
  reportId,
  accountHolder,
  settlementPoint,
  mwhNumber,
  onCellSelect,
  onSourceCollapse,
  visible,
  selection,
}) {
  const query = useSourceHoldings(reportId, accountHolder, settlementPoint);
  const [expanded, setExpanded] = useState(new Set());
  const scroll = useRef(null);
  const firstMonth = useRef(null);
  const positioned = useRef(false);
  const page = query.data?.pages[0];

  function toggle(source) {
    if (expanded.has(source)) onSourceCollapse(source);
    setExpanded((previous) => {
      const next = new Set(previous);
      if (next.has(source)) next.delete(source);
      else next.add(source);
      return next;
    });
  }

  function jump() {
    if (scroll.current && firstMonth.current) {
      const timelineStart = scroll.current.querySelector(
        "[data-delivery-month]"
      ).offsetLeft;
      scroll.current.scrollLeft = firstMonth.current.offsetLeft - timelineStart;
    }
  }

  // Transformation: position once per selection; appended pages retain scrolling.
  useEffect(() => {
    if (page && visible && !positioned.current) {
      jump();
      positioned.current = true;
    }
  }, [page, visible]);

  // Output: an additional-page error keeps the successful pages visible.
  return (
    <div className="source-holdings">
      {!page ? (
        query.isError ? (
          <p role="alert">Unable to load holdings.</p>
        ) : (
          <p role="status">Loading holdings...</p>
        )
      ) : (
        <>
          {page.holdingsRange && (
            <div className="holdings-range">
              <span>
                Holdings: {monthLabel(page.holdingsRange.firstMonth)}–
                {monthLabel(page.holdingsRange.lastMonth)}
              </span>
              <button type="button" onClick={jump}>
                Jump to first holdings
              </button>
            </div>
          )}
          {page.sources.length === 0 ? (
            <p>No holdings match these filters.</p>
          ) : (
            <div
              className="holdings-scroll"
              ref={scroll}
              tabIndex={0}
              role="region"
              aria-label="Source holdings by delivery month"
            >
              <table>
                <thead>
                  <tr>
                    <th rowSpan={2} scope="col">
                      Source
                    </th>
                    <th colSpan={2} scope="colgroup">
                      Total MWh
                    </th>
                    {page.deliveryMonths.map((month) => (
                      <th
                        key={month}
                        colSpan={2}
                        scope="colgroup"
                        data-delivery-month={month}
                        ref={
                          month === page.holdingsRange?.firstMonth
                            ? firstMonth
                            : null
                        }
                      >
                        {monthLabel(month)}
                      </th>
                    ))}
                  </tr>
                  <tr>
                    <th scope="col">OPT</th>
                    <th scope="col">OBL</th>
                    {page.deliveryMonths.flatMap((month) =>
                      ["OPT", "OBL"].map((type) => (
                        <th key={`${month}/${type}`} scope="col">
                          {type}
                        </th>
                      ))
                    )}
                  </tr>
                </thead>
                <tbody>
                  {query.data.pages
                    .flatMap((part) => part.sources)
                    .map((row) => (
                      <Fragment key={row.source}>
                        <tr>
                          <th scope="row">
                            <button
                              type="button"
                              className="source-expand control-icon"
                              aria-expanded={expanded.has(row.source)}
                              aria-label={`${
                                expanded.has(row.source) ? "Collapse" : "Expand"
                              } ${row.source}`}
                              title={`${
                                expanded.has(row.source) ? "Collapse" : "Expand"
                              } ${row.source}`}
                              onClick={() => toggle(row.source)}
                            >
                              <svg
                                className="control-caret"
                                viewBox="0 0 16 16"
                                aria-hidden="true"
                                fill="none"
                                stroke="currentColor"
                                strokeWidth="1.6"
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                style={{
                                  transform: expanded.has(row.source)
                                    ? "rotate(0deg)"
                                    : "rotate(-90deg)",
                                }}
                              >
                                <path d="m4 6 4 4 4-4" />
                              </svg>
                            </button>
                            {row.source}
                          </th>
                          <td>{mwhNumber.format(row.totalOptMwh)}</td>
                          <td>{mwhNumber.format(row.totalOblMwh)}</td>
                          {row.months.flatMap((month) =>
                            ["OPT", "OBL"].map((type) => (
                              <td key={`${month.deliveryMonth}/${type}`}>
                                {mwhNumber.format(month[type])}
                              </td>
                            ))
                          )}
                        </tr>
                        {expanded.has(row.source) && (
                          <SinkHoldings
                            reportId={reportId}
                            accountHolder={accountHolder}
                            settlementPoint={settlementPoint}
                            source={row.source}
                            deliveryMonths={page.deliveryMonths}
                            mwhNumber={mwhNumber}
                            selection={selection}
                            onCellSelect={onCellSelect}
                          />
                        )}
                      </Fragment>
                    ))}
                </tbody>
              </table>
            </div>
          )}
          {query.isFetchNextPageError && (
            <p role="alert">Unable to load more sources. Try again.</p>
          )}
          {query.hasNextPage && (
            <button
              type="button"
              disabled={query.isFetchingNextPage}
              onClick={() => query.fetchNextPage()}
            >
              {query.isFetchingNextPage
                ? "Loading sources..."
                : "Show more sources"}
            </button>
          )}
        </>
      )}
    </div>
  );
}
