export default function MapStatus({
  mapError,
  dataFailed,
  dataReady,
  onRetryMap,
  onRetryData,
}) {
  // Basemap and holdings requests can fail independently or at the same time.
  return (
    <>
      {mapError && (
        <div className="map-status" role="alert">
          Unable to load the basemap.
          <button type="button" onClick={onRetryMap}>
            Retry map
          </button>
        </div>
      )}
      {dataFailed && (
        <div className="map-status" role="alert">
          <p>Unable to load geographic footprint.</p>
          <button type="button" onClick={onRetryData}>
            Retry
          </button>
        </div>
      )}
      {!dataFailed && !dataReady && (
        <p className="map-status" role="status">
          Loading geographic footprint...
        </p>
      )}
    </>
  );
}
