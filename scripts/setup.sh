#!/usr/bin/env bash
# setup.sh – Einrichtungsskript für das Klimadaten-Projekt
# Läuft auf Zorin OS 17 / Ubuntu-basierten Systemen
set -e

echo "=== Klimadaten-Projekt Setup ==="
echo ""

# ── Schritt 1: Python prüfen ─────────────────────────────────────────────────
echo "1/6  Python prüfen..."
if ! command -v python3 &>/dev/null; then
    echo "     Python3 nicht gefunden. Installation:"
    echo "     sudo apt install python3 python3-pip python3-venv"
    exit 1
fi
python3 --version

# ── Schritt 2: Virtuelle Umgebung ────────────────────────────────────────────
echo "2/6  Virtuelle Python-Umgebung erstellen..."
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip --quiet

# ── Schritt 3: Python-Pakete ─────────────────────────────────────────────────
echo "3/6  Python-Abhängigkeiten installieren..."
pip install -r services/api/requirements.txt --quiet
for req in modules/*/requirements.txt; do
    [ -f "$req" ] && pip install -r "$req" --quiet || true
done
pip install pytest pytest-cov ruff --quiet

# ── Schritt 4: Node.js prüfen ────────────────────────────────────────────────
echo "4/6  Node.js prüfen..."
if ! command -v node &>/dev/null; then
    echo "     Node.js nicht gefunden."
    echo "     Installation: sudo apt install nodejs npm"
    echo "     Oder: https://nodejs.org"
    echo "     Frontend-Setup wird übersprungen."
else
    node --version
    echo "5/6  Frontend-Abhängigkeiten installieren..."
    if [ -f "services/frontend/package.json" ]; then
        cd services/frontend && npm install --silent && cd ../..
    else
        echo "     Kein package.json gefunden – Frontend noch nicht initialisiert."
        echo "     Führe aus: cd services/frontend && npm create vite@latest . -- --template react"
    fi
fi

# ── Schritt 5: Verzeichnisse anlegen ─────────────────────────────────────────
echo "5/6  Datenverzeichnisse anlegen..."
mkdir -p data/raw data/processed data/samples memory/team_logs

# ── Schritt 6: .env-Datei ────────────────────────────────────────────────────
echo "6/6  Umgebungsvariablen prüfen..."
if [ ! -f ".env" ]; then
    cat > .env << 'EOF'
# Anthropic API-Key für das AI Explanation System
# Erhalte deinen Key unter: https://console.anthropic.com
ANTHROPIC_API_KEY=dein-api-key-hier-eintragen
EOF
    echo "     .env-Datei erstellt. Bitte ANTHROPIC_API_KEY eintragen!"
else
    echo "     .env existiert bereits."
fi

echo ""
echo "=== Setup abgeschlossen! ==="
echo ""
echo "Nächste Schritte:"
echo "  1. ANTHROPIC_API_KEY in .env eintragen"
echo "  2. ./scripts/run_dev.sh ausführen"
echo "  3. http://localhost:8000/docs öffnen"
