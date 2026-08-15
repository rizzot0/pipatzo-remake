const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, options);
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `HTTP ${response.status}`);
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

export async function searchNodos(ciudadId, query) {
  if (!query?.trim()) {
    return [];
  }
  return request(`/api/ciudades/${ciudadId}/nodos/buscar?q=${encodeURIComponent(query.trim())}&limite=10`);
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

export { API_BASE };
