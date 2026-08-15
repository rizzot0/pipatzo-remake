const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";

const TOKEN_KEY = "planvial_token";

export function getToken() {
  return localStorage.getItem(TOKEN_KEY) || "";
}

export function setToken(token) {
  if (token) {
    localStorage.setItem(TOKEN_KEY, token);
  } else {
    localStorage.removeItem(TOKEN_KEY);
  }
}

async function request(path, options = {}) {
  const headers = { ...(options.headers || {}) };
  const token = getToken();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  if (options.body && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (!response.ok) {
    const text = await response.text();
    let detail = text || `HTTP ${response.status}`;
    try {
      const parsed = JSON.parse(text);
      detail = parsed.detail || detail;
    } catch {
      /* keep text */
    }
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  if (response.status === 204) {
    return null;
  }
  return response.json();
}

export async function fetchCiudades() {
  return request("/api/ciudades");
}

export async function fetchEstadisticas(ciudadId) {
  return request(`/api/ciudades/${ciudadId}/estadisticas`);
}

export async function fetchGrafoCiudad(ciudadId, maxEdges = 50000) {
  return request(`/api/ciudades/${ciudadId}/grafo?max_edges=${maxEdges}`);
}

export async function fetchNodoCercano(ciudadId, lat, lon, radio = 250) {
  const path = `/api/ciudades/${ciudadId}/nodos/cercanos?latitud=${lat}&longitud=${lon}&radio_m=${radio}&limite=1`;
  const nodos = await request(path);
  return nodos[0] || null;
}

export async function calcularRuta(ciudadId, origenId, destinoId) {
  const params = new URLSearchParams({
    ciudad_id: String(ciudadId),
    nodo_origen_id: String(origenId),
    nodo_destino_id: String(destinoId)
  });

  return request(`/api/rutas/calcular?${params.toString()}`, {
    method: "POST"
  });
}

export async function geocodificar(query, bounds) {
  const params = new URLSearchParams({ q: query });
  if (bounds) {
    params.set("min_lat", String(bounds.min_lat));
    params.set("max_lat", String(bounds.max_lat));
    params.set("min_lon", String(bounds.min_lon));
    params.set("max_lon", String(bounds.max_lon));
  }
  return request(`/api/geocodificar?${params.toString()}`);
}

export async function registerAccount(email, password) {
  return request("/api/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password })
  });
}

export async function loginAccount(email, password) {
  return request("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password })
  });
}

export async function fetchMe() {
  return request("/api/me");
}

export async function fetchSavedRoutes() {
  return request("/api/rutas");
}

export async function fetchSavedRoute(id) {
  return request(`/api/rutas/${id}`);
}

export async function saveRoute(payload) {
  return request("/api/rutas", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export async function deleteSavedRoute(id) {
  return request(`/api/rutas/${id}`, { method: "DELETE" });
}

export async function fetchSharedRoute(shareId) {
  return request(`/api/rutas/compartidas/${shareId}`);
}

export { API_BASE };
