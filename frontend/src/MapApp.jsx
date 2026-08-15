import React, { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { CircleMarker, MapContainer, Polyline, TileLayer, useMap, useMapEvents } from "react-leaflet";
import {
  calcularRuta,
  fetchCiudades,
  fetchEstadisticas,
  fetchGrafoCiudad,
  fetchNodoCercano,
  fetchSavedRoute,
  geocodificar,
  saveRoute
} from "./api";
import { useAuth } from "./AuthContext";

const PENDING_KEY = "planvial_pending_route";

const CITY_CENTERS = {
  Coquimbo: [-29.95, -71.34],
  "La Serena": [-29.9, -71.25],
  "Punta Arenas": [-53.16, -70.91],
  Antofagasta: [-23.65, -70.4],
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

function nodeFromSaved(route, which) {
  if (which === "origin") {
    return {
      id: route.origin_nodo_id,
      latitud: route.origin_lat,
      longitud: route.origin_lon,
      label: route.origin_label
    };
  }
  return {
    id: route.dest_nodo_id,
    latitud: route.dest_lat,
    longitud: route.dest_lon,
    label: route.dest_label
  };
}

export function MapApp() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const rutaId = searchParams.get("ruta");

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
  const [notice, setNotice] = useState("");

  const [query, setQuery] = useState("");
  const [hits, setHits] = useState([]);
  const [routeName, setRouteName] = useState("");
  const [savedShare, setSavedShare] = useState("");

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

  async function cargarMapa(ciudadId = ciudadIdSeleccionada) {
    if (!ciudadId) {
      return;
    }

    setLoadingMapa(true);
    setError("");
    setRuta([]);
    setRutaMeta(null);
    setOrigenNodo(null);
    setDestinoNodo(null);
    setSavedShare("");
    setHits([]);

    try {
      const [stats, grafo] = await Promise.all([
        fetchEstadisticas(ciudadId),
        fetchGrafoCiudad(ciudadId, 25000)
      ]);

      setCiudadIdSeleccionada(String(ciudadId));
      setCiudadIdCargada(String(ciudadId));
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

  useEffect(() => {
    if (!rutaId || !user) {
      return;
    }
    let cancelled = false;
    fetchSavedRoute(rutaId)
      .then(async (saved) => {
        if (cancelled) {
          return;
        }
        await cargarMapa(String(saved.ciudad_id));
        setOrigenNodo(nodeFromSaved(saved, "origin"));
        setDestinoNodo(nodeFromSaved(saved, "destino"));
        setRuta(saved.geometry || []);
        setRutaMeta({
          distancia: saved.distancia_total,
          pasos: saved.num_pasos,
          tiempo: 0
        });
        setRouteName(saved.name);
        setSavedShare(saved.share_id);
      })
      .catch((err) => setError(err.message));
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [rutaId, user]);

  async function aplicarPunto(nodo, label) {
    const tagged = { ...nodo, label: label || nodo.label || `Nodo #${nodo.id}` };
    if (!origenNodo) {
      setOrigenNodo(tagged);
    } else if (!destinoNodo) {
      setDestinoNodo(tagged);
    } else {
      setOrigenNodo(tagged);
      setDestinoNodo(null);
      setRuta([]);
      setRutaMeta(null);
      setSavedShare("");
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
      await aplicarPunto(nodo);
    } catch (err) {
      setError(`No se pudo seleccionar nodo: ${err.message}`);
    } finally {
      setLoading(false);
    }
  }

  async function buscarDireccion(event) {
    event.preventDefault();
    if (!query.trim()) {
      return;
    }
    setLoading(true);
    setError("");
    try {
      const results = await geocodificar(query.trim(), grafoBounds);
      setHits(results);
      if (!results.length) {
        setError("No encontré esa dirección. Prueba con otra o haz click en el mapa.");
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function elegirHit(hit) {
    if (!ciudadIdCargada) {
      setError("Carga un mapa antes de buscar direcciones.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const nodo = await fetchNodoCercano(ciudadIdCargada, hit.latitud, hit.longitud, 800);
      if (!nodo) {
        setError("Esa dirección no cae cerca del grafo de esta ciudad.");
        return;
      }
      await aplicarPunto(nodo, hit.label);
      setHits([]);
      setQuery("");
    } catch (err) {
      setError(err.message);
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
    setSavedShare("");

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

  function buildSavePayload(name) {
    const city = ciudades.find((c) => String(c.id) === String(ciudadIdCargada));
    return {
      name,
      ciudad_id: Number(ciudadIdCargada),
      ciudad_nombre: city?.nombre || estadisticas?.ciudad || "",
      origen: {
        id: origenNodo.id,
        latitud: origenNodo.latitud,
        longitud: origenNodo.longitud,
        label: origenNodo.label || `Nodo #${origenNodo.id}`
      },
      destino: {
        id: destinoNodo.id,
        latitud: destinoNodo.latitud,
        longitud: destinoNodo.longitud,
        label: destinoNodo.label || `Nodo #${destinoNodo.id}`
      },
      distancia_total: rutaMeta.distancia,
      num_pasos: rutaMeta.pasos,
      geometry: ruta.map((n) => ({
        id: n.id,
        latitud: n.latitud,
        longitud: n.longitud
      }))
    };
  }

  async function persistRoute(payload) {
    const saved = await saveRoute(payload);
    setSavedShare(saved.share_id);
    setNotice("Ruta guardada.");
    setSearchParams({ ruta: String(saved.id) });
    return saved;
  }

  async function guardar() {
    if (!rutaMeta || ruta.length < 2) {
      setError("Calcula una ruta antes de guardarla.");
      return;
    }
    const name = routeName.trim() || `Ruta ${new Date().toLocaleString("es-CL")}`;
    const payload = buildSavePayload(name);

    if (!user) {
      sessionStorage.setItem(PENDING_KEY, JSON.stringify(payload));
      navigate(`/login?next=${encodeURIComponent("/app")}`);
      return;
    }

    setLoading(true);
    setError("");
    try {
      await persistRoute(payload);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!user) {
      return;
    }
    const raw = sessionStorage.getItem(PENDING_KEY);
    if (!raw) {
      return;
    }
    let payload;
    try {
      payload = JSON.parse(raw);
    } catch {
      sessionStorage.removeItem(PENDING_KEY);
      return;
    }
    sessionStorage.removeItem(PENDING_KEY);
    persistRoute(payload).catch((err) => setError(err.message));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  function limpiarSeleccion() {
    setOrigenNodo(null);
    setDestinoNodo(null);
    setRuta([]);
    setRutaMeta(null);
    setError("");
    setSavedShare("");
    setHits([]);
  }

  function copyShare() {
    const url = `${window.location.origin}/r/${savedShare}`;
    navigator.clipboard.writeText(url).then(
      () => setNotice("Link copiado."),
      () => setNotice(url)
    );
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
    <>
      <header className="hero compact">
        <p className="eyebrow">Mapa</p>
        <h1>Calcula una ruta</h1>
        <p>Click en el mapa o busca una dirección. Origen verde, destino naranja.</p>
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
            <button className="cta" onClick={() => cargarMapa()} disabled={loadingMapa}>
              {loadingMapa ? "Cargando mapa..." : "Cargar mapa"}
            </button>
            <button onClick={limpiarSeleccion} disabled={!ciudadIdCargada}>
              Limpiar selección
            </button>
            <button className="cta" onClick={calcular} disabled={loading || !ciudadIdCargada}>
              {loading ? "Calculando..." : "Calcular ruta"}
            </button>
          </div>

          <form className="search-form" onSubmit={buscarDireccion}>
            <label>
              Buscar dirección
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Ej. Plaza de Armas, Coquimbo"
                disabled={!ciudadIdCargada}
              />
            </label>
            <button type="submit" disabled={loading || !ciudadIdCargada}>
              Buscar
            </button>
          </form>

          {hits.length > 0 && (
            <ul className="hit-list">
              {hits.map((hit) => (
                <li key={`${hit.latitud}-${hit.longitud}`}>
                  <button type="button" onClick={() => elegirHit(hit)}>
                    {hit.label}
                  </button>
                </li>
              ))}
            </ul>
          )}

          <div className="pick-status">
            <p>Origen: {origenNodo ? origenNodo.label || `#${origenNodo.id}` : "pendiente"}</p>
            <p>Destino: {destinoNodo ? destinoNodo.label || `#${destinoNodo.id}` : "pendiente"}</p>
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
              {rutaMeta.tiempo ? <p>Tiempo API: {rutaMeta.tiempo} ms</p> : null}
              <label>
                Nombre
                <input
                  value={routeName}
                  onChange={(e) => setRouteName(e.target.value)}
                  placeholder="Ej. Casa al trabajo"
                />
              </label>
              <button className="cta" type="button" onClick={guardar} disabled={loading}>
                {user ? "Guardar ruta" : "Entrar y guardar"}
              </button>
              {savedShare ? (
                <p className="share-line">
                  Pública: <Link to={`/r/${savedShare}`}>/r/{savedShare}</Link>{" "}
                  <button type="button" className="inline-btn" onClick={copyShare}>
                    Copiar
                  </button>
                </p>
              ) : null}
            </div>
          )}

          {notice && <p className="notice">{notice}</p>}
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
    </>
  );
}
