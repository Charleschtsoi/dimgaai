# Single-unit production image: frontend static + FastAPI backend
FROM node:22-alpine AS frontend-build
WORKDIR /build/frontend
COPY frontend/package.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    build-essential \
    libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf-2.0-0 libffi-dev \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app ./app
COPY --from=frontend-build /build/frontend/dist ./static

ENV STATIC_DIR=/app/static
ENV CHROMA_PERSIST_DIR=/app/data/chroma
ENV UPLOAD_DIR=/app/data/uploads
ENV CORS_ORIGINS=*

EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
