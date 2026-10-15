#!/usr/bin/env bash
# ==============================================================================
# One-Command Localhost Startup Script for macOS / Linux / WSL
# Reference: docs/09_DEVELOPMENT_ROADMAP_AND_AGENT_RULES.md & docs/10_TESTING_VALIDATION_DEPLOYMENT.md
# ==============================================================================

set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

echo "======================================================================"
echo " Starting MODIS-VIIRS Hotspot Harmonisation on localhost"
echo "======================================================================"

# 1. Environment Files Configuration
if [ ! -f ".env" ]; then
    echo "[Config] Creating root .env with localhost defaults..."
    cat << 'EOF' > .env
APP_ENV=development
APP_NAME="MODIS-VIIRS Hotspot Harmonisation"
DEFAULT_METHOD_VERSION=1.0.0
BACKEND_HOST=127.0.0.1
BACKEND_PORT=8000
FRONTEND_ORIGIN=http://localhost:3000
MAX_UPLOAD_SIZE_MB=50
# Uses PostgreSQL/PostGIS if running on port 5432, or local SQLite file if Docker is unavailable:
DATABASE_URL=sqlite:///./modis_viirs_local.db
FALLBACK_SQLITE_URL=sqlite:///./modis_viirs_local.db
EOF
fi

if [ ! -f "frontend/.env.local" ]; then
    echo "[Config] Creating frontend/.env.local..."
    mkdir -p frontend
    cat << 'EOF' > frontend/.env.local
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api
NEXT_PUBLIC_DEFAULT_CRS=EPSG:4326
EOF
fi

# 2. Local Database Detection (Docker PostGIS vs SQLite Fallback)
if command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then
    echo "[Database] Docker daemon detected. Starting PostgreSQL/PostGIS container..."
    docker compose up -d db || true
    echo "[Database] Waiting for database readiness..."
    until docker compose exec -T db pg_isready -U postgres -d modis_viirs_harmonisation >/dev/null 2>&1; do
        sleep 1
    done
    if grep -q "DATABASE_URL=sqlite" .env; then
        sed -i.bak 's|^DATABASE_URL=.*|DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/modis_viirs_harmonisation|' .env && rm -f .env.bak
    fi
    echo "[Database] PostgreSQL + PostGIS is ready."
else
    echo "[Database] Docker daemon is not active. Using automatic local SQLite fallback."
    if grep -q "DATABASE_URL=postgresql" .env; then
        sed -i.bak 's|^DATABASE_URL=.*|DATABASE_URL=sqlite:///./modis_viirs_local.db|' .env && rm -f .env.bak
    fi
fi

# 3. Python Virtual Environment & Dependencies
if [ ! -d "backend/.venv" ]; then
    echo "[Python] Initializing Python virtual environment backend/.venv..."
    python3 -m venv backend/.venv
    backend/.venv/bin/pip install --upgrade pip
    backend/.venv/bin/pip install -r backend/requirements.txt
fi

# 4. Database Initialization & Seed Fixtures
echo "[Seed] Initializing tables and seeding labelled test fixtures..."
PYTHONPATH=. backend/.venv/bin/python scripts/seed_demo_fixtures.py

# 5. Process Management & Clean Shutdown Trap
BACKEND_PID=""
cleanup() {
    echo ""
    echo "[Shutdown] Caught signal. Stopping local servers cleanly..."
    if [ -n "${BACKEND_PID}" ]; then
        kill "${BACKEND_PID}" 2>/dev/null || true
    fi
    exit 0
}
trap cleanup SIGINT SIGTERM EXIT

# 6. Start FastAPI Backend Server
echo "[Backend] Launching FastAPI Uvicorn on http://127.0.0.1:8000..."
PYTHONPATH=. backend/.venv/bin/uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!

echo "[Backend] Waiting for FastAPI health endpoint (http://127.0.0.1:8000/api/health)..."
for i in {1..30}; do
    if curl -s http://127.0.0.1:8000/api/health | grep -q '"status"' 2>/dev/null; then
        echo "[Backend] FastAPI is online and healthy."
        break
    fi
    sleep 1
done

# 7. Start Next.js Frontend Server
echo "======================================================================"
echo " Application URLs:"
echo "   - Web Frontend:              http://localhost:3000"
echo "   - FastAPI Backend API:       http://localhost:8000/api"
echo "   - Interactive Swagger Docs:  http://localhost:8000/docs"
echo "   - API Health Check:          http://localhost:8000/api/health"
echo "======================================================================"
echo "[Frontend] Launching Next.js development server on http://localhost:3000..."

cd frontend
if [ ! -d "node_modules" ]; then
    npm install
fi
npm run dev -- -p 3000
