import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import * as maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import workerUrl from "maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url";
import MarkerButton from "./MarkerButton";
import MapControls from "./MapControls";
import MapPointDetails from "./MapPointDetails";

// Let Vite bundle the worker and resolve its production asset URL.
maplibregl.setWorkerUrl(workerUrl);

// Coordinates and inventory retain the API's unrounded values.
const located = (point) => point.longitude !== null && point.latitude !== null;
const totalSourceSinkMwh = (point) => point.sourceMwh + point.sinkMwh;
const basemap = "https://tiles.openfreemap.org/styles/positron";
const texasLatLng = { lat: 31, lng: -99 };

// Adjust the map's center and zoom so all report points with coordinates fit
// in the window, leaving padding for the floating panels.
function fitReport(map, points) {
  const mapped = points.filter(located);
  if (!mapped.length) return;
  const bounds = new maplibregl.LngLatBounds();
  mapped.forEach((point) => bounds.extend([point.longitude, point.latitude]));
  // Leave room for floating panels without moving filters into map state.
  const narrow = map.getContainer().clientWidth <= 760;
  map.fitBounds(bounds, {
    padding: narrow
      ? { top: 100, right: 35, bottom: 100, left: 35 }
      : { top: 90, right: 100, bottom: 150, left: 420 },
    maxZoom: 9,
    duration: 0,
  });
}

export default function Map({
  summary,
  isoSummary,
  selectedPoint,
  onPointSelect,
  mwhNumber,
}) {
  const container = useRef(null);
  const mapFitted = useRef(false); // Fit report bounds once to preserve later pan/zoom.
  const [map, setMap] = useState(null);
  // Hover/focus shows point details; selectedPoint filters the portfolio on click.
  const [activePoint, setActivePoint] = useState(null);
  const [detailPosition, setDetailPosition] = useState(null);
  const dataFailed = summary.isError || isoSummary.isError;
  const dataReady = summary.data && isoSummary.data && !dataFailed;
  const points = dataReady ? summary.data.geographicFootprint : null;
  const isoPoints = isoSummary.data?.geographicFootprint;

  useEffect(() => {
    // Keep the map and camera when portfolio filters change;
    // recreate the map when the selected report (report_id) changes.
    const instance = new maplibregl.Map({
      container: container.current,
      style: basemap,
      center: texasLatLng,
      zoom: 5,
      renderWorldCopies: false,
      attributionControl: false,
    });
    instance.addControl(
      new maplibregl.NavigationControl({ showCompass: false }),
      "top-right"
    );
    setMap(instance);
    mapFitted.current = false;

    // Remove WebGL resources and listeners when changing reports.
    return () => {
      instance.remove();
    };
  }, []);

  useEffect(() => {
    if (map && isoPoints && !mapFitted.current) {
      fitReport(map, isoPoints);
      mapFitted.current = true;
    }
  }, [map, isoPoints]);

  const maximum = Math.max(
    ...(points ?? []).filter(located).map(totalSourceSinkMwh),
    1
  );
  const mapped = (points ?? [])
    .filter(located)
    .sort((a, b) => totalSourceSinkMwh(b) - totalSourceSinkMwh(a));

  // Coordinate coverage stays part of inventory, not marker placement.
  const detail = points?.find((point) => point.settlementPoint === activePoint);

  // Only plain canvas clicks clear selection; markers and controls are separate.
  useEffect(() => {
    if (!map) return;
    let dragged = false;
    const start = () => {
      dragged = false;
    };
    const drag = () => {
      dragged = true;
    };
    const clear = (event) => {
      if (!dragged && event.originalEvent.target === map.getCanvas())
        onPointSelect("");
    };
    map.on("mousedown", start);
    map.on("dragstart", drag);
    map.on("click", clear);
    return () => {
      map.off("mousedown", start);
      map.off("dragstart", drag);
      map.off("click", clear);
    };
  }, [map, onPointSelect]);

  // Track the MapPointDetails hover box position as its marker moves on screen.
  useEffect(() => {
    if (!map || !detail) {
      setDetailPosition(null);
      return;
    }
    const position = () => {
      const pixel = map.project([detail.longitude, detail.latitude]);
      const width = map.getContainer().clientWidth;
      const height = map.getContainer().clientHeight;
      setDetailPosition({
        left: Math.max(
          8,
          Math.min(width - Math.min(260, width - 16) - 8, pixel.x + 32)
        ),
        top: Math.max(
          8,
          Math.min(height - 88, pixel.y < 100 ? pixel.y + 32 : pixel.y - 88)
        ),
      });
    };
    position();
    map.on("move", position);
    map.on("resize", position);
    return () => {
      map.off("move", position);
      map.off("resize", position);
    };
  }, [map, detail]);

  // Markers, hover details, and controls float over the basemap.
  return (
    <section
      className="geographic-footprint"
      aria-label="Geographic footprint map"
    >
      <div className="map-canvas" ref={container} />
      {map &&
        mapped.map((point) => (
          <MarkerButton
            key={point.settlementPoint}
            map={map}
            point={point}
            maximum={maximum}
            selected={point.settlementPoint === selectedPoint}
            onSelect={onPointSelect}
            onActive={setActivePoint}
            mwhNumber={mwhNumber}
          />
        ))}
      {map &&
        createPortal(
          <MapControls
            canReset={Boolean(isoPoints)}
            onReset={() => fitReport(map, isoPoints)}
          />,
          map.getContainer().querySelector(".maplibregl-ctrl-top-right")
        )}
      {detail && detailPosition && (
        <MapPointDetails
          detail={detail}
          position={detailPosition}
          mwhNumber={mwhNumber}
        />
      )}
    </section>
  );
}
