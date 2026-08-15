import React, { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { CircleMarker, MapContainer, Polyline, TileLayer, useMap } from "react-leaflet";
import { fetchSharedRoute } from "./api";

function FitRoute({ points }) {
  const map = useMap();
  useEffect(() => {
    if (!points?.length) {
      return;
    }
    map.fitBounds(points, { padding: [28, 28] });
  }, [map, points]);
  return null;
}

function metersToKm(value) {
  return (value / 1000).toFixed(2);
}

export function SharedRoute() {
  const { shareId } = useParams();
  const [route, setRoute] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchSharedRoute(shareId)
      .then(setRoute)
      .catch((err) => setError(err.message));
  }, [shareId]);

  const points = useMemo(
    () => (route?.geometry || []).map((n) => [n.latitud, n.longitud]),
    [route]
  );

  if (error) {
    return (
      <section className="panel auth-card">
        <h1>Ruta no encontrada</h1>
        <p className="error">{error}</p>
      </section>
    );
  }

  if (!route) {
    return (
      <section className="panel auth-card">
        <p>Cargando ruta…</p>
      </section>
    );
  }

  return (
    <>
      <header className="hero compact">
        <p className="eyebrow">Ruta compartida</p>
        <h1>{route.name}</h1>
        <p>
          {route.ciudad_nombre} · {metersToKm(route.distancia_total)} km · {route.origin_label} → {route.dest_label}
        </p>
      </header>
      <section className="panel map-panel">
        <MapContainer
          center={points[0] || [route.origin_lat, route.origin_lon]}
          zoom={14}
          scrollWheelZoom
          className="map"
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <FitRoute points={points} />
          {points.length > 1 ? (
            <Polyline positions={points} pathOptions={{ color: "#ef4444", weight: 5, opacity: 0.95 }} />
          ) : null}
          <CircleMarker
            center={[route.origin_lat, route.origin_lon]}
            radius={8}
            pathOptions={{ color: "#22c55e", fillOpacity: 0.85 }}
          />
          <CircleMarker
            center={[route.dest_lat, route.dest_lon]}
            radius={8}
            pathOptions={{ color: "#f97316", fillOpacity: 0.85 }}
          />
        </MapContainer>
      </section>
    </>
  );
}
