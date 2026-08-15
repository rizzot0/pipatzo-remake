import React from "react";
import { Link } from "react-router-dom";

export function Landing() {
  return (
    <div className="landing">
      <p className="eyebrow">Ruteo urbano</p>
      <h1>Plan Vial</h1>
      <p className="lede">
        Carga el mapa de una ciudad chilena, marca origen y destino, y Dijkstra calcula la mejor ruta
        sobre el grafo vial. Puedes probarlo sin cuenta.
      </p>
      <div className="landing-actions">
        <Link className="cta-link" to="/app">
          Probar mapa
        </Link>
        <Link className="ghost-link" to="/registro">
          Crear cuenta
        </Link>
      </div>
      <ul className="landing-points">
        <li>Cinco ciudades: Coquimbo, La Serena, Antofagasta, Punta Arenas y Santiago.</li>
        <li>Busca una dirección o haz click en el mapa para elegir nodos.</li>
        <li>Con cuenta: guarda rutas y comparte un link de solo lectura.</li>
      </ul>
    </div>
  );
}
