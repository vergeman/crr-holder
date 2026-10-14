export default function MapControls({ canReset, canClear, onReset, onClear }) {
  return (
    <div className="map-controls">
      <button type="button" disabled={!canReset} onClick={onReset}>
        Reset view
      </button>
      <button type="button" disabled={!canClear} onClick={onClear}>
        Clear point
      </button>
    </div>
  );
}
