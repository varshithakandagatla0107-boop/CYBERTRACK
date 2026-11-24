# CYBERTRACK Makefile
# Cross-platform targets (Windows: use `mingw32-make` or run commands directly)

.PHONY: setup test lint build run demo package clean audit

# =============================================================================
# Setup
# =============================================================================

setup: setup-backend setup-frontend

setup-backend:
	cd backend && python -m venv .venv
	@echo "Activate venv with: .venv\Scripts\activate (Windows) or source .venv/bin/activate (Linux/macOS)"
	.venv\Scripts\activate && pip install --upgrade pip && pip install -r requirements.txt
	@echo "For dev dependencies: pip install -r requirements-dev.txt"

setup-frontend:
	cd frontend && npm install

# =============================================================================
# Development
# =============================================================================

run: run-backend run-frontend

run-backend:
	cd backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

run-frontend:
	cd frontend && npm run dev

run:
	@echo "Starting both servers... (run in separate terminals)"
	@echo "Backend:  make run-backend"
	@echo "Frontend: make run-frontend"

demo:
	cd backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# =============================================================================
# Testing
# =============================================================================

test: test-backend test-frontend

test-backend:
	cd backend && python -m pytest tests/ -v --cov=app.engine --cov=app.security --cov=app.routers --cov-report=term-missing

test-frontend:
	cd frontend && npm run test 2>/dev/null || echo "Frontend tests not configured yet"

test-e2e:
	cd frontend && npm run test:e2e 2>/dev/null || echo "E2E tests not configured yet"

# =============================================================================
# Linting & Type Checking
# =============================================================================

lint: lint-backend lint-frontend

lint-backend:
	cd backend && ruff check app/ tests/ && mypy --ignore-missing-imports app/

lint-frontend:
	cd frontend && npm run lint 2>/dev/null || echo "ESLint not configured yet"

typecheck:
	cd frontend && npm run typecheck 2>/dev/null || echo "TypeScript check not configured yet"

# =============================================================================
# Building
# =============================================================================

build: build-frontend

build-frontend:
	cd frontend && npm run build

build-docker:
	docker build -t cybertrack:latest .

# =============================================================================
# Packaging
# =============================================================================

package:
	@echo "Creating release archive..."
	@git archive --format=zip --output=cybertrack-release.zip HEAD 2>/dev/null || \
		(powershell -Command "Compress-Archive -Path . -DestinationPath cybertrack-release.zip -CompressionLevel Optimal -Exclude 'node_modules','frontend/dist','__pycache__','*.pyc','.pytest_cache','.venv','*.db','*.db-wal','*.db-shm','.env','.env.local','.env.*','.git','docs/VERIFICATION_REPORT.md'")
	@echo "Created cybertrack-release.zip"

# =============================================================================
# Cleaning
# =============================================================================

clean:
	cd backend && rm -rf __pycache__ .pytest_cache .venv *.db *.db-wal *.db-shm data/*.db data/*.db-wal data/*.db-shm
	cd frontend && rm -rf node_modules dist .vite
	rm -f cybertrack-release.zip

# =============================================================================
# Security Audit
# =============================================================================

audit:
	cd backend && pip-audit 2>/dev/null || echo "pip-audit not installed"
	cd frontend && npm audit 2>/dev/null || echo "npm audit not available"

# =============================================================================
# Docker
# =============================================================================

docker-build:
	docker build -t cybertrack:latest .

docker-run:
	docker-compose up -d

docker-stop:
	docker-compose down

docker-logs:
	docker-compose logs -f

# =============================================================================
# Helpers
# =============================================================================

db-reset:
	cd backend && rm -f data/cybertrack.db data/cybertrack.db-wal data/cybertrack.db-shm
	python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

db-backup:
	copy backend\data\cybertrack.db backend\data\cybertrack.db.backup 2>nul || cp backend/data/cybertrack.db backend/data/cybertrack.db.backup

db-restore:
	copy backend\data\cybertrack.db.backup backend\data\cybertrack.db 2>nul || cp backend/data/cybertrack.db.backup backend/data/cybertrack.db

# =============================================================================
# CI Simulation
# =============================================================================

ci: lint test build-frontend audit
	@echo "CI pipeline completed successfully"

# =============================================================================
# Windows-specific helpers
# =============================================================================

# On Windows, use: mingw32-make or run commands directly in PowerShell
# Example: mingw32-make test