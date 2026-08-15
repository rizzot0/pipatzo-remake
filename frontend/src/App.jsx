import React, { useEffect, useMemo, useState } from "react";
import { CircleMarker, MapContainer, Polyline, TileLayer, useMap, useMapEvents } from "react-leaflet";
import {
  calcularRuta,
  fetchCiudades,
  fetchEstadisticas,
  fetchGrafoCiudad,
  fetchNodoCercano,
} from "./api";

const CITY_CENTERS = {
  Coquimbo: [-29.95, -71.34],
  "La Serena": [-29.90, -71.25],
  "Punta Arenas": [-53.16, -70.91],
  Antofagasta: [-23.65, -70.40],
  Santiago: [-33.45, -70.66]
};

function MapClickPicker({ enabled, onPick }) {
  useMapEvents({
    click: async (event) => {
      if (!enabled) {
        return;
      }
      await onPick(event.latlng.lat, event.latlng.lng);
    }
  });
  return null;
}

function metersToKm(value) {
  return (value / 1000).toFixed(2);
}

function FitBoundsEffect({ bounds }) {
  const map = useMap();

  useEffect(() => {
    if (!bounds) {
      return;
    }

    map.fitBounds(
      [
        [bounds.min_lat, bounds.min_lon],
        [bounds.max_lat, bounds.max_lon]
      ],
      { padding: [18, 18] }
    );
  }, [bounds, map]);

  return null;
}

export function App() {
  const [ciudades, setCiudades] = useState([]);
  const [ciudadIdSeleccionada, setCiudadIdSeleccionada] = useState("");
  const [ciudadIdCargada, setCiudadIdCargada] = useState("");
  const [estadisticas, setEstadisticas] = useState(null);
  const [grafoSegmentos, setGrafoSegmentos] = useState([]);
  const [grafoBounds, setGrafoBounds] = useState(null);
  const [grafoTruncado, setGrafoTruncado] = useState(false);

  const [origenNodo, setOrigenNodo] = useState(null);
  const [destinoNodo, setDestinoNodo] = useState(null);

  const [ruta, setRuta] = useState([]);
  const [rutaMeta, setRutaMeta] = useState(null);
  const [loadingMapa, setLoadingMapa] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchCiudades()
      .then((rows) => {
        setCiudades(rows);
        if (rows.length > 0) {
          setCiudadIdSeleccionada(String(rows[0].id));
        }
      })
      .catch((err) => setError(`No se pudo cargar ciudades: ${err.message}`));
  }, []);

  async function cargarMapa() {
    if (!ciudadIdSeleccionada) {
      return;
    }

    setLoadingMapa(true);
    setError("");
    setRuta([]);
    setRutaMeta(null);
    setOrigenNodo(null);
    setDestinoNodo(null);

    try {
      const [stats, grafo] = await Promise.all([
        fetchEstadisticas(ciudadIdSeleccionada),
        fetchGrafoCiudad(ciudadIdSeleccionada, 25000)
      ]);

      setCiudadIdCargada(ciudadIdSeleccionada);
      setEstadisticas(stats);
      setGrafoSegmentos(grafo.segmentos || []);
      setGrafoBounds(grafo.bounds || null);
      setGrafoTruncado(Boolean(grafo.truncated));
    } catch (err) {
      setError(`No se pudo cargar el mapa: ${err.message}`);
    } finally {
      setLoadingMapa(false);
    }
  }

  async function seleccionarNodoPorMapa(lat, lon) {
    if (!ciudadIdCargada) {
      return;
    }

    setLoading(true);
    setError("");

    try {
      const nodo = await fetchNodoCercano(ciudadIdCargada, lat, lon, 300);
      if (!nodo) {
        setError("No encontré nodos cercanos en ese punto del mapa.");
        return;
      }

      if (!origenNodo) {
        setOrigenNodo(nodo);
      } else if (!destinoNodo) {
        setDestinoNodo(nodo);
      } else {
        setOrigenNodo(nodo);
        setDestinoNodo(null);
        setRuta([]);
        setRutaMeta(null);
      }
    } catch (err) {
      setError(`No se pudo seleccionar nodo: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }

  async function calcular() {
    if (!ciudadIdCargada || !origenNodo?.id || !destinoNodo?.id) {
      setError("Selecciona ciudad, nodo origen y nodo destino.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const result = await calcularRuta(ciudadIdCargada, origenNodo.id, destinoNodo.id);
      setRuta(result.ruta || []);
      setRutaMeta({
        distancia: result.distancia_total,
        pasos: result.num_pasos,
        tiempo: result.tiempo_ejecucion_ms
      });
    } catch (err) {
      setError(`Error al calcular ruta: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }

  function limpiarSeleccion() {
    setOrigenNodo(null);
    setDestinoNodo(null);
    setRuta([]);
    setRutaMeta(null);
    setError("");
  }

  const selectedCity = useMemo(
    () => ciudades.find((city) => String(city.id) === String(ciudadIdSeleccionada)),
    [ciudades, ciudadIdSeleccionada]
  );

  const mapCenter = useMemo(() => {
    if (ruta.length > 0) {
      return [ruta[0].latitud, ruta[0].longitud];
    }

    if (origenNodo) {
      return [origenNodo.latitud, origenNodo.longitud];
    }

    if (grafoBounds) {
      return [
        (grafoBounds.min_lat + grafoBounds.max_lat) / 2,
        (grafoBounds.min_lon + grafoBounds.max_lon) / 2
      ];
    }

    if (selectedCity && CITY_CENTERS[selectedCity.nombre]) {
      return CITY_CENTERS[selectedCity.nombre];
    }

    return [-33.45, -70.66];
  }, [selectedCity, origenNodo, ruta, grafoBounds]);

  return (
    <div className="app-shell">
      <div className="background-glow" />
      <header className="hero">
        <p className="eyebrow">Ruteo vial</p>
        <h1>Ruta Urbana</h1>
        <p>
          Carga un mapa, marca origen y destino con un click y calcula la mejor ruta sobre el grafo vial.
        </p>
      </header>

      <main className="layout">
        <section className="panel controls">
          <label>
            Mapa de ciudad
            <select
              value={ciudadIdSeleccionada}
              onChange={(e) => setCiudadIdSeleccionada(e.target.value)}
            >
              {ciudades.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.nombre}
                </option>
              ))}
            </select>
          </label>

          <div className="button-row">
            <button className="cta" onClick={cargarMapa} disabled={loadingMapa}>
              {loadingMapa ? "Cargando mapa..." : "Cargar mapa"}
            </button>
            <button onClick={limpiarSeleccion} disabled={!ciudadIdCargada}>
              Limpiar selección
            </button>
            <button className="cta" onClick={calcular} disabled={loading || !ciudadIdCargada}>
              {loading ? "Calculando..." : "Calcular ruta"}
            </button>
          </div>

          <div className="pick-status">
            <p>
              Origen: {origenNodo ? `#${origenNodo.id}` : "pendiente"}
            </p>
            <p>
              Destino: {destinoNodo ? `#${destinoNodo.id}` : "pendiente"}
            </p>
          </div>

          {selectedCity?.nombre === "Santiago" && (
            <p className="warning">
              Santiago es un grafo grande: el mapa se recorta y el cálculo puede tardar más. Coquimbo es más liviano para probar.
            </p>
          )}

          {grafoTruncado && selectedCity?.nombre !== "Santiago" && (
            <p className="warning">
              Mapa grande: se está mostrando una muestra de edges para mantener rendimiento.
            </p>
          )}

          {estadisticas && (
            <div className="stats">
              <article>
                <strong>{estadisticas.ciudad}</strong>
                <span>{Number(estadisticas.num_nodos).toLocaleString()} nodos</span>
              </article>
              <article>
                <strong>Conectividad</strong>
                <span>{Number(estadisticas.num_edges).toLocaleString()} edges</span>
              </article>
              <article>
                <strong>Promedio</strong>
                <span>{metersToKm(estadisticas.distancia_promedio_m)} km</span>
              </article>
            </div>
          )}

          {rutaMeta && (
            <div className="result-card">
              <h3>Ruta calculada</h3>
              <p>Distancia: {metersToKm(rutaMeta.distancia)} km</p>
              <p>Pasos: {rutaMeta.pasos}</p>
              <p>Tiempo API: {rutaMeta.tiempo} ms</p>
            </div>
          )}

          {error && <p className="error">{error}</p>}
        </section>

        <section className="panel map-panel">
          {ciudadIdCargada ? (
            <MapContainer key={ciudadIdCargada} center={mapCenter} zoom={13} scrollWheelZoom className="map">
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
              <FitBoundsEffect bounds={grafoBounds} />
              <MapClickPicker enabled={true} onPick={seleccionarNodoPorMapa} />

              {grafoSegmentos.length > 0 && (
                <Polyline
                  positions={grafoSegmentos}
                  pathOptions={{ color: "#7f8c99", weight: 1, opacity: 0.55 }}
                />
              )}

              {ruta.length > 1 && (
                <Polyline
                  positions={ruta.map((n) => [n.latitud, n.longitud])}
                  pathOptions={{ color: "#ef4444", weight: 5, opacity: 0.95 }}
                />
              )}

              {origenNodo && (
                <CircleMarker
                  center={[origenNodo.latitud, origenNodo.longitud]}
                  radius={8}
                  pathOptions={{ color: "#22c55e", fillOpacity: 0.85 }}
                />
              )}

              {destinoNodo && (
                <CircleMarker
                  center={[destinoNodo.latitud, destinoNodo.longitud]}
                  radius={8}
                  pathOptions={{ color: "#f97316", fillOpacity: 0.85 }}
                />
              )}
            </MapContainer>
          ) : (
            <div className="map-empty-state">
              <h3>Mapa no cargado</h3>
              <p>Selecciona una ciudad y presiona Cargar mapa para visualizar sus edges y nodos.</p>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
