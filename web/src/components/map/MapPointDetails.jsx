export default function MapPointDetails({ detail, position, mwhNumber }) {
  return (
    <p className="map-point-details" style={position} aria-live="polite">
      {detail.settlementPoint}
      {" · "}Source {mwhNumber.format(detail.sourceMwh)} MWh
      {" · "}Sink {mwhNumber.format(detail.sinkMwh)} MWh
    </p>
  );
}
