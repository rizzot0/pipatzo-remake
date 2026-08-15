import React, { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "./AuthContext";

export function AuthPage({ mode }) {
  const isRegister = mode === "register";
  const { login, register } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const next = new URLSearchParams(location.search).get("next") || "/app";
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function onSubmit(event) {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      if (isRegister) {
        await register(email, password);
      } else {
        await login(email, password);
      }
      navigate(next);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="panel auth-card">
      <p className="eyebrow">{isRegister ? "Nueva cuenta" : "Bienvenido"}</p>
      <h1>{isRegister ? "Crear cuenta" : "Entrar"}</h1>
      <p className="muted">
        El mapa se puede usar sin registrarse. La cuenta sirve para guardar y compartir rutas.
      </p>
      <form className="auth-form" onSubmit={onSubmit}>
        <label>
          Email
          <input
            type="email"
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </label>
        <label>
          Contraseña
          <input
            type="password"
            autoComplete={isRegister ? "new-password" : "current-password"}
            minLength={8}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </label>
        {error ? <p className="error">{error}</p> : null}
        <button className="cta" type="submit" disabled={loading}>
          {loading ? "Un momento..." : isRegister ? "Crear cuenta" : "Entrar"}
        </button>
      </form>
      <p className="auth-switch">
        {isRegister ? (
          <>
            ¿Ya tienes cuenta? <Link to={`/login?next=${encodeURIComponent(next)}`}>Entrar</Link>
          </>
        ) : (
          <>
            ¿No tienes cuenta? <Link to={`/registro?next=${encodeURIComponent(next)}`}>Crear una</Link>
          </>
        )}
      </p>
    </section>
  );
}
