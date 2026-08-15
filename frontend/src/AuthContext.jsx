import React, { createContext, useContext, useEffect, useMemo, useState } from "react";
import { fetchMe, getToken, loginAccount, registerAccount, setToken } from "./api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!getToken()) {
      setReady(true);
      return;
    }
    fetchMe()
      .then((me) => setUser(me))
      .catch(() => setUser(null))
      .finally(() => setReady(true));
  }, []);

  const value = useMemo(
    () => ({
      user,
      ready,
      async login(email, password) {
        const result = await loginAccount(email, password);
        setToken(result.token);
        setUser(result.user);
        return result.user;
      },
      async register(email, password) {
        const result = await registerAccount(email, password);
        setToken(result.token);
        setUser(result.user);
        return result.user;
      },
      logout() {
        setToken("");
        setUser(null);
      }
    }),
    [user, ready]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth requiere AuthProvider");
  }
  return ctx;
}
