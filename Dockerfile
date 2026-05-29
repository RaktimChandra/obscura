# ---- stage 1: build the React frontend (same-origin API) ----
FROM node:20-slim AS frontend
WORKDIR /fe
COPY frontend/package*.json ./
RUN npm ci || npm install
COPY frontend/ ./
ENV VITE_API_BASE=""
RUN npm run build

# ---- stage 2: python backend serving the built frontend ----
FROM python:3.12-slim AS app
WORKDIR /srv
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 && rm -rf /var/lib/apt/lists/*
COPY backend/requirements-core.txt .
RUN pip install --no-cache-dir -r requirements-core.txt
COPY backend/ ./
COPY --from=frontend /fe/dist ./app/static
ENV OBSCURA_SERVE_FRONTEND=1
EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
