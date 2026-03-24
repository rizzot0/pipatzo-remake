# Backend PIPATZO

## Estructura

- `api/`: servicio FastAPI
- `scripts/`: migraciones y utilidades
- `data/`: base de datos SQLite y XML de mapas
- `docs/`: documentacion del proyecto
- `legacy-java/`: codigo/proyecto Java original

## Ejecutar API

Desde la raiz del repositorio:

python backend/api/main_sqlite.py

Documentacion Swagger:

http://127.0.0.1:8000/docs

## Scripts utiles

Ver estado de importaciones:

python backend/scripts/check_imports.py

Migrar una ciudad a SQLite:

python backend/scripts/migrate_to_sqlite.py --ciudad coquimbo

Migrar todas las ciudades:

python backend/scripts/migrate_to_sqlite.py --all
