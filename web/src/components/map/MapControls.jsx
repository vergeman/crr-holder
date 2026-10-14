export default function MapControls({ canReset, onReset }) {
  return (
    <div className="map-controls maplibregl-ctrl maplibregl-ctrl-group">
      <button
        type="button"
        disabled={!canReset}
        onClick={onReset}
        aria-label="Reset map view"
        title="Reset map view"
      >
        <span aria-hidden="true">↺</span>
      </button>
    </div>
  );
}
