#!/usr/bin/env bash
# run_dev.sh – Startet alle lokalen Entwicklungsserver
set -e

echo "=== Entwicklungsserver starten ==="

# Python-Umgebung aktivieren
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

# .env laden
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Backend starten (Hintergrund)
echo "Backend starten (FastAPI)..."
uvicorn services.api.main:app --reload --port 8000 &
BACKEND_PID=$!
echo "  Backend läuft (PID $BACKEND_PID)"

# Frontend starten (falls vorhanden)
if [ -f "services/frontend/package.json" ]; then
    echo "Frontend starten (React/Vite)..."
    cd services/frontend && npm run dev &
    FRONTEND_PID=$!
    echo "  Frontend läuft (PID $FRONTEND_PID)"
    cd ../..
fi

echo ""
echo "Erreichbar unter:"
echo "  Frontend:    http://localhost:5173"
echo "  Backend:     http://localhost:8000"
echo "  API-Docs:    http://localhost:8000/docs"
echo ""
echo "Beenden mit: Ctrl+C"

# Warten bis Ctrl+C
wait
