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
  const diameter =
    total === 0
      ? 8
      : Math.max(8, Math.min(56, 56 * Math.sqrt(total / maximum)));

  // Blend through neutral so balanced points do not imply a third direction.
  const from = share <= 0.5 ? [37, 110, 158] : [45, 65, 85];
  const to = share <= 0.5 ? [45, 65, 85] : [184, 61, 65];
  const blend = share <= 0.5 ? share * 2 : (share - 0.5) * 2;
  const color = from.map((channel, i) =>
    Math.round(channel + (to[i] - channel) * blend)
  );

  return createPortal(
    <button
      type="button"
      className="marker-button"
      data-point={point.settlementPoint}
      style={{
        width: diameter,
        height: diameter,
        backgroundColor: `rgb(${color.join(",")})`,
      }}
      aria-label={`${point.settlementPoint}: source ${mwhNumber.format(
        point.sourceMwh
      )} MWh, sink ${mwhNumber.format(point.sinkMwh)} MWh`}
      aria-pressed={selected}
      onClick={(event) => {
        event.stopPropagation();
        onSelect(point.settlementPoint);
      }}
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
