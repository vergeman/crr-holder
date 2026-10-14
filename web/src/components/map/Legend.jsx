export default function Legend({ dataReady, missing, mwhNumber }) {
  const missingMwh = (role) =>
    mwhNumber.format(missing.reduce((sum, point) => sum + point[role], 0));

  return (
    <details className="map-legend">
      <summary>Map legend and coverage</summary>
      <div className="map-legend-scale" aria-hidden="true" />
      <div className="map-legend-labels">
        <span>Source-dominant</span>
        <span>Balanced</span>
        <span>Sink-dominant</span>
      </div>
      <p>
        Circle area represents source + sink MWh, with a minimum visible
        size for zero totals. Endpoint MWh counts both ends of each holding
        and is not the portfolio total.
      </p>
      {dataReady && (
        <p className="map-legend-coverage">
          Missing coordinates: {missing.length} points
          {" · "}Source {missingMwh("sourceMwh")} MWh · Sink{" "}
          {missingMwh("sinkMwh")} MWh. These holdings remain in portfolio
          and table totals.
        </p>
      )}
    </details>
  );
}
