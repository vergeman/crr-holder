import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { Marker } from "maplibre-gl";

export default function MarkerButton({
  map,
  point,
  maximum,
  selected,
  onSelect,
  onActive,
  mwhNumber,
}) {
  // MapLibre positions the host; React owns the button and its event handlers.
  const [host] = useState(() => document.createElement("div"));

  useEffect(() => {
    const marker = new Marker({ element: host })
      .setLngLat([point.longitude, point.latitude])
      .addTo(map);
    return () => marker.remove();
  }, [map, host, point.longitude, point.latitude]);

  const total = point.sourceMwh + point.sinkMwh;
  const share = total === 0 ? 0.5 : point.sinkMwh / total;
  const diameter = total === 0 ? 6 : 48 * Math.sqrt(total / maximum);

  return createPortal(
    <button
      type="button"
      className="marker-button"
      data-point={point.settlementPoint}
      style={{
        width: diameter,
        height: diameter,
        backgroundColor: `hsl(${210 - share * 180} 60% 45%)`,
      }}
      aria-label={`${point.settlementPoint}: source ${mwhNumber.format(
        point.sourceMwh
      )} MWh, sink ${mwhNumber.format(point.sinkMwh)} MWh`}
      aria-pressed={selected}
      onClick={() => onSelect(point.settlementPoint)}
      onMouseEnter={() => onActive(point.settlementPoint)}
      onMouseLeave={(event) => {
        if (document.activeElement !== event.currentTarget) onActive(null);
      }}
      onFocus={() => onActive(point.settlementPoint)}
      onBlur={() => onActive(null)}
    />,
    host
  );
}

