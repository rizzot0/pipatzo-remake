# Plan Vial

Planificador de rutas urbanas. Backend FastAPI + SQLite (Dijkstra) y frontend React + Leaflet, servidos juntos.

Autores: Bastian Guerra, Ian Fernandez, Max Malebran

## Demo pública

**App:** https://planvial.onrender.com/

- Mapa (sin cuenta): `/app`
- Cuentas y rutas guardadas: `/registro` y `/rutas`
- Link público de una ruta: `/r/:id`

El mapa se puede usar como invitado. Las rutas guardadas viven en Postgres (`DATABASE_URL`, Neon u otro). Si no hay `DATABASE_URL`, se usa un SQLite local `backend/data/planvial_saas.db` (en Render Free ese archivo se pierde al dormir el servicio).

El deploy gratis va a [Render](https://render.com) como un servicio Python. Variables:

- `JWT_SECRET` — obligatorio en producción
- `DATABASE_URL` — Postgres para cuentas y rutas (recomendado)

El servicio se duerme a los 15 minutos sin tráfico; el primer request tarda ~1 minuto.

[Deploy to Render](https://render.com/deploy?repo=https://github.com/rizzot0/pipatzo-remake)

1. New → Web Service → repo `rizzot0/pipatzo-remake`
2. Runtime: Python
3. Instance: Free
4. Build: `bash scripts/render-build.sh`
5. Start: `bash scripts/render-start.sh`

Santiago es un grafo grande: el mapa se recorta y el cálculo puede tardar más. Coquimbo es la ciudad más liviana para probar.

## Demo local (un solo proceso)

```bash
docker compose up --build
```

Abre http://localhost:8000

- App: `/`
- API docs: `/docs`
- Health: `/health`

## Desarrollo (frontend y API separados)

Este repo **no usa el Artifactory de LATAM**. npm queda fijado a `https://registry.npmjs.org/` en `.npmrc` (raíz y `frontend/`). Si `package-lock.json` vuelve a apuntar a `appslatam`, `npm install` y el build de Render fallan a propósito.

```powershell
powershell -ExecutionPolicy Bypass -File scripts/dev-up.ps1
```

- API: http://127.0.0.1:8000
- Frontend: http://127.0.0.1:5173 (Vite hace proxy a la API)

O, con el frontend ya compilado:

```powershell
$env:PYTHONPATH = "backend"
$env:FRONTEND_DIST = "frontend/dist"
.venv\Scripts\python.exe backend\api\main_sqlite.py
```
