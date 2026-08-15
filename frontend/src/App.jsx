import React from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { AuthPage } from "./AuthPage";
import { Landing } from "./Landing";
import { Layout } from "./Layout";
import { MapApp } from "./MapApp";
import { SavedRoutes } from "./SavedRoutes";
import { SharedRoute } from "./SharedRoute";

export function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Landing />} />
        <Route path="/app" element={<MapApp />} />
        <Route path="/rutas" element={<SavedRoutes />} />
        <Route path="/r/:shareId" element={<SharedRoute />} />
        <Route path="/login" element={<AuthPage mode="login" />} />
        <Route path="/registro" element={<AuthPage mode="register" />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
