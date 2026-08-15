FROM node:22-alpine AS frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install --registry https://registry.npmjs.org
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/backend
ENV FRONTEND_DIST=/app/frontend/dist

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/api ./backend/api
COPY backend/scripts ./backend/scripts
COPY backend/data/pipatzo.db ./backend/data/pipatzo.db
COPY --from=frontend /app/frontend/dist ./frontend/dist

EXPOSE 8000
CMD ["sh", "-c", "uvicorn api.main_sqlite:app --host 0.0.0.0 --port ${PORT:-8000}"]
