import React from "react";
import { Link, NavLink, Outlet } from "react-router-dom";
import { useAuth } from "./AuthContext";

export function Layout() {
  const { user, logout, ready } = useAuth();

  return (
    <div className="app-shell">
      <div className="background-glow" />
      <header className="site-header">
        <Link to="/" className="brand">
          Plan Vial
        </Link>
        <nav className="site-nav">
          <NavLink to="/app">Mapa</NavLink>
          {user ? <NavLink to="/rutas">Mis rutas</NavLink> : null}
          {!ready ? null : user ? (
            <>
              <span className="nav-user">{user.email}</span>
              <button type="button" className="nav-button" onClick={logout}>
                Salir
              </button>
            </>
          ) : (
            <>
              <NavLink to="/login">Entrar</NavLink>
              <NavLink to="/registro" className="nav-cta">
                Crear cuenta
              </NavLink>
            </>
          )}
        </nav>
      </header>
      <Outlet />
    </div>
  );
}
