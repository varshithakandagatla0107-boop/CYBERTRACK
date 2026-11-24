# ---- Build the React frontend ----
FROM node:20-alpine AS frontend
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ---- Runtime: FastAPI serves both API and built frontend ----
FROM python:3.13-slim
WORKDIR /app

COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend
COPY --from=frontend /app/frontend/dist ./frontend/dist

RUN mkdir -p /app/data
ENV CYBERTRACK_DB=/app/data/cybertrack.db
ENV CYBERTRACK_JWT_SECRET=CHANGE-THIS-IN-DEPLOYMENT
ENV CYBERTRACK_MODE=production
ENV PYTHONUNBUFFERED=1

EXPOSE 8000
CMD ["python", "-m", "uvicorn", "app.main:app", \
     "--app-dir", "backend", "--host", "0.0.0.0", "--port", "8000"]
