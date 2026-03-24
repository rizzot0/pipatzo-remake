# PIPATZO

Estructura principal del repositorio:

- backend: API, datos, scripts de migracion y documentacion tecnica
- frontend: app React + Leaflet

## Arranque rapido (backend + frontend)

Desde la raiz del repo:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/dev-up.ps1
```

Esto levanta:

- backend en http://127.0.0.1:8000
- frontend en http://127.0.0.1:5173

Para detener ambos procesos:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/dev-down.ps1
```

Los logs quedan en la carpeta `.dev-logs/`.

## Levantar backend

python backend/api/main_sqlite.py

## Levantar frontend

cd frontend
npm install
npm run dev
