import React, { useEffect, useState } from "react";
import { Link, Navigate } from "react-router-dom";
import { deleteSavedRoute, fetchSavedRoutes } from "./api";
import { useAuth } from "./AuthContext";

function metersToKm(value) {
  return (value / 1000).toFixed(2);
}

export function SavedRoutes() {
  const { user, ready } = useAuth();
  const [rows, setRows] = useState([]);
  const [error, setError] = useState("");

  function load() {
    fetchSavedRoutes()
      .then(setRows)
      .catch((err) => setError(err.message));
  }

  useEffect(() => {
    if (user) {
      load();
    }
  }, [user]);

  if (ready && !user) {
    return <Navigate to="/login?next=/rutas" replace />;
  }

  async function remove(id) {
    try {
      await deleteSavedRoute(id);
      setRows((current) => current.filter((row) => row.id !== id));
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <section className="panel routes-panel">
      <p className="eyebrow">Cuenta</p>
      <h1>Mis rutas</h1>
      <p className="muted">Ábrelas en el mapa o comparte el link público.</p>
      {error ? <p className="error">{error}</p> : null}
      {rows.length === 0 ? (
        <p className="muted">Todavía no guardas rutas. Calcula una en el mapa y pulsa Guardar.</p>
      ) : (
        <ul className="route-list">
          {rows.map((row) => (
            <li key={row.id}>
              <div>
                <strong>{row.name}</strong>
                <p>
                  {row.ciudad_nombre || `Ciudad ${row.ciudad_id}`} · {metersToKm(row.distancia_total)} km
                </p>
                <p className="muted small">
                  {row.origin_label} → {row.dest_label}
                </p>
              </div>
              <div className="route-actions">
                <Link to={`/app?ruta=${row.id}`}>Abrir</Link>
                <Link to={`/r/${row.share_id}`}>Compartir</Link>
                <button type="button" onClick={() => remove(row.id)}>
                  Borrar
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
