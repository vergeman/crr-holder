export default function MapPointDetails({
  points = [],
  detail,
  position,
  hasLocatedPoints,
  mwhNumber,
}) {
  return (
    <>
      {!detail && points.length === 0 && (
        <p>No holdings match these filters.</p>
      )}
      {points.length > 0 && !hasLocatedPoints && (
        <p>No settlement points have both coordinates for this portfolio.</p>
      )}
      {detail && (
        <p className="map-point-details" style={position} aria-live="polite">
          {detail.settlementPoint}
          {" · "}Source {mwhNumber.format(detail.sourceMwh)} MWh
          {" · "}Sink {mwhNumber.format(detail.sinkMwh)} MWh
        </p>
      )}
    </>
  );
}
