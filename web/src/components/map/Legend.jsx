export default function Legend() {
  return (
    <div className="map-legend" aria-label="Marker source and sink balance">
      <div className="map-legend-scale" aria-hidden="true" />
      <div className="map-legend-labels">
        <span>Source</span>
        <span>Balanced</span>
        <span>Sink</span>
      </div>
    </div>
  );
}
