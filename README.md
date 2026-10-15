# Harmonisation of MODIS and VIIRS Hotspots

A reproducible geospatial workflow and scientific web application designed to systematically compare, validate, and harmonise active-fire hotspot observations from NASA's Moderate Resolution Imaging Spectroradiometer (**MODIS**) and the Visible Infrared Imaging Radiometer Suite (**VIIRS**).

---

## ⚡ Quick Start on Localhost (One Command)

### Single-Command Automated Startup

#### macOS / Linux / WSL:
```bash
chmod +x scripts/start_localhost.sh
./scripts/start_localhost.sh
```

#### Windows (PowerShell):
```powershell
.\scripts\start_localhost.ps1
```

Both startup scripts automatically:
1. Verify and create `.env` and `frontend/.env.local` with development defaults.
2. Detect Docker/PostGIS; automatically fallback to local SQLite (`modis_viirs_local.db`) if Docker is unavailable.
3. Configure `backend/.venv` and install Python dependencies.
4. Run `python scripts/seed_demo_fixtures.py` to initialize tables and seed verification fixtures.
5. Launch FastAPI backend on `http://127.0.0.1:8000` with `/api/health` readiness monitoring.
6. Launch Next.js frontend on `http://localhost:3000` with graceful shutdown handling.

---

### Manual 2-Terminal Startup

#### Terminal 1 — FastAPI Backend (Port 8000)
```bash
# 1. Initialize environment files
cp .env.example .env
cp .env.example frontend/.env.local

# 2. Setup Python virtual environment
python3 -m venv backend/.venv
backend/.venv/bin/pip install --upgrade pip
backend/.venv/bin/pip install -r backend/requirements.txt

# 3. Seed fixtures & initialize database
PYTHONPATH=. backend/.venv/bin/python scripts/seed_demo_fixtures.py

# 4. Start backend server
PYTHONPATH=. backend/.venv/bin/uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

#### Terminal 2 — Next.js Frontend (Port 3000)
```bash
cd frontend
npm install
npm run dev -- -p 3000
```

---

### Localhost Endpoints Summary

| Service | Localhost URL | Notes |
|---|---|---|
| **Web Frontend** | [`http://localhost:3000`](http://localhost:3000) | Next.js 14 interactive scientific UI |
| **Backend API Base** | [`http://localhost:8000/api`](http://localhost:8000/api) | FastAPI REST service |
| **Interactive API Docs** | [`http://localhost:8000/docs`](http://localhost:8000/docs) | OpenAPI Swagger UI |
| **Health Check** | [`http://localhost:8000/api/health`](http://localhost:8000/api/health) | Service readiness probe |

---

### Common Localhost Troubleshooting

1. **CORS Origin Mismatch**:
   - The backend allows origins specified in `FRONTEND_ORIGIN` in `.env` (default: `http://localhost:3000`).
   - If accessing the frontend via `http://127.0.0.1:3000` instead of `http://localhost:3000`, ensure your browser URL matches `FRONTEND_ORIGIN` or set `CORS_ORIGINS=["*"]` in `.env`.

2. **Port Conflicts (`8000` or `3000` already in use)**:
   - Identify existing processes:
     ```bash
     lsof -i :8000 -i :3000
     ```
   - Kill conflicting processes:
     ```bash
     kill -9 <PID>
     ```

3. **Switching between Docker PostGIS and Local SQLite**:
   - **SQLite (Default without Docker)**: Set `DATABASE_URL=sqlite:///./modis_viirs_local.db` in `.env`.
   - **PostgreSQL / PostGIS (Docker)**: Run `docker compose up -d db` and set:
     `DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/modis_viirs_harmonisation`
   - Run migrations or seed fixtures after switching:
     ```bash
     PYTHONPATH=. backend/.venv/bin/python scripts/seed_demo_fixtures.py
     ```

---

## 1. Scientific Overview & Problem Statement

Satellite active-fire data products are foundational to environmental monitoring, disaster management, and climate research. However, MODIS (e.g., Terra/Aqua at ~1 km nominal nadir resolution) and VIIRS (e.g., Suomi-NPP / NOAA-20 at 375 m / 750 m nominal resolution) differ significantly in:
- Sensor spatial resolution and point spread functions.
- Swath geometry and pixel footprint distortion away from nadir.
- Overpass timing and solar illumination conditions.
- Detection algorithms, radiance thresholds, and Fire Radiative Power (FRP) retrieval physics.

**Harmonisation is fundamentally distinct from naive file concatenation.** Simply merging raw detections inflates fire counts, produces duplicate records, masks sensor-specific sensitivities, and obscures observational uncertainty. This platform executes a rigorous 7-stage processing workflow that:
- Retains full source provenance and original raw observations.
- Identifies candidate cross-sensor matches using configurable spatial and temporal thresholds.
- Explicitly models unmatched observations (`unmatched_modis`, `unmatched_viirs`) and multi-candidate ambiguities (`ambiguous`).
- Avoids default averaging of physical measurements (e.g., FRP) without empirical calibration.

---

## 2. Logical System Architecture

```text
  MODIS Hotspot Ingestion            VIIRS Hotspot Ingestion
  (FIRMS / MOD14 / MYD14)           (FIRMS / VNP14IMGTDL / VNP14)
            │                                     │
            └─────────────────┬───────────────────┘
                              ▼
                Stage A: Input Validation & QC
               (Range, UTC, Checksums, Schema)
                              ▼
                Stage B: Schema Standardization
             (17-Field Data Dictionary Normalization)
                              ▼
                Stage C: Quality Flag Filtering
                  (Product-Specific QC Flags)
                              ▼
            Stage D: Spatial-Temporal Matching Engine
               (STRtree Spatial Indexing + PyProj)
                              ▼
            Stage E: Documented Candidate Scoring
               (Normalized Spatial + Temporal Deltas)
                              ▼
            Stage F: Ambiguity & Candidate Resolution
         (Retain Ambiguous | One-to-One | Many-to-Many)
                              ▼
             Stage G: Harmonised Output Construction
          (6 Output Tables + Audit Log & Provenance)
                              ▼
                   Persistence Layer
             (PostgreSQL 16 + PostGIS 3.4 / SQLite)
                              ▼
                     FastAPI Backend API
              (REST Endpoints, OpenAPI Docs, Streaming)
                              ▼
                    Next.js 14 Frontend UI
       (8 Scientific Analysis Views, Leaflet/MapLibre Maps)
```

---

## 3. Seven Algorithmic Processing Stages (Stages A–G)

1. **Stage A: Input Validation** — Verifies file formats, required columns, latitude/longitude bounds (`[-90, 90]` and `[-180, 180]`), UTC timestamps, and calculates SHA-256 dataset checksums.
2. **Stage B: Standardization** — Maps product-specific headers to a unified 17-field internal schema while preserving all raw values, units, and original detection IDs.
3. **Stage C: Quality Filtering** — Evaluates sensor-specific confidence flags (MODIS 0–100% vs. VIIRS nominal/low/high categorical flags) without cross-sensor scale conflation.
4. **Stage D: Candidate Pair Generation** — Uses an R-tree spatial index (`STRtree`) to query candidates within configurable spatial radius ($\Delta d \le d_{\max}$) and temporal window ($\Delta t \le t_{\max}$).
5. **Stage E: Candidate Scoring** — Calculates transparent, documented ranking scores combining normalized spatial and temporal distances (never labeled as "probabilities" without reference calibration).
6. **Stage F: Ambiguity Resolution** — Resolves complex 1-to-many and many-to-many relationships using the user-selected policy (`retain_ambiguous`, `one_to_one_deterministic`, or `many_to_many`).
7. **Stage G: Output Construction** — Produces 6 distinct output views:
   - Harmonised Match Table (`matched`)
   - Unmatched MODIS Table (`unmatched_modis`)
   - Unmatched VIIRS Table (`unmatched_viirs`)
   - Ambiguous Candidates Table (`ambiguous`)
   - Complete Observation View
   - Run Execution Summary & Quality Audit Report

---

## 4. Eight User Interface Views

1. **Overview Dashboard (`/`)** — High-level metrics, active study period, counts by sensor, match breakdown, and recent run statuses.
2. **Dataset Explorer (`/datasets`)** — Ingested dataset registry, schema inspection, coordinate bounds verification, and row-level quality audits.
3. **Harmonisation Workspace (`/workspace`)** — Interactive parameter tuning (spatial radius, temporal window, ambiguity policy) and processing execution launcher.
4. **Interactive Map Explorer (`/map`)** — Multi-layer geospatial map distinguishing MODIS, VIIRS, matched pairs, unmatched hotspots, and ambiguous clusters with Record Provenance Drawer.
5. **Sensor Comparison (`/comparison`)** — Bivariate spatial/temporal delta distributions, diurnal detection profiles, and comparative sensor characteristics.
6. **Validation & Sensitivity (`/validation`)** — Threshold sensitivity matrices, match-rate curves, and documented methodological caveats.
7. **Reports & Exports (`/exports`)** — Filterable exports (CSV, GeoJSON) bundling complete run metadata, checksums, and parameter definitions.
8. **Methodology & Data Reference (`/methodology`)** — Authoritative scientific references, data dictionaries, sensor physics explanations, and citation guides.

---

## 5. Development Roadmap

- **Part 1: Monorepo Foundation & Governance**
  - **Phase 0A**: Persistent Antigravity Agent Rules (`.antigravity/rules.md`).
  - **Phase 0B**: Basic Project Structure & Monorepo Initialization.
- **Part 2: Frontend Engineering (Next.js 14 + TypeScript + Tailwind CSS)**
  - **Phase 1**: Frontend Foundation, WCAG Theme, 17-Field Types, and 8-View Shell.
  - **Phase 2**: Overview Dashboard (`/`) & Dataset Explorer (`/datasets`).
  - **Phase 3**: Harmonisation Workspace (`/workspace`) & Parameter Configuration.
  - **Phase 4**: Interactive Map Explorer (`/map`) with 6 Layers & Provenance Drawer.
  - **Phase 5**: Sensor Comparison, Validation, Exports, and Methodology Views.
- **Part 3: Backend & Processing Pipeline (FastAPI + GeoPandas + Shapely)**
  - **Phase 1**: FastAPI Application Core, Security, and Pydantic v2 Schemas.
  - **Phase 2**: Ingestion Engine & Stages A, B, and C (Validation & Normalization).
  - **Phase 3**: Matching Engine & Stages D, E, F, and G (Spatial Indexing & Ambiguity Policies).
  - **Phase 4**: REST APIs, Sensitivity Grid, and GeoJSON/CSV Exporters.
  - **Phase 5**: Automated Unit, Integration, Edge, and Negative Test Suite (`pytest`).
- **Part 4: Database & Production Persistence (PostgreSQL 16 + PostGIS 3.4)**
  - **Phase 1**: Database Models (`datasets` & immutable `observations`).
  - **Phase 2**: Relational Models (`processing_runs`, `match_candidates`, `harmonised_records`).
  - **Phase 3**: PostGIS Spatial Indexing (`ST_DWithin`, `ST_Distance`) & Alembic Migrations.
  - **Phase 4**: Full-Stack End-to-End Integration, Seed Data, and Deployment Hardening.

---

## 6. Deployment, Migration, Seeding & Testing Guide

### Prerequisites
- Python >= 3.10 (3.11 recommended)
- Node.js >= 18.18.0 & npm >= 9.0.0
- Docker & Docker Compose (for PostgreSQL 16 + PostGIS 3.4) or local SQLite fallback

### 1. Environment Configuration
```bash
cp .env.example .env
cp .env.example frontend/.env.local
```

### 2. Database Service (Docker Compose PostGIS)
Start the PostgreSQL 16 + PostGIS 3.4 container:
```bash
docker compose up -d db
```
The database healthcheck will automatically confirm readiness (`pg_isready`). To view database logs:
```bash
docker compose logs -f db
```

### 3. Alembic Database Migrations
Apply all schema migrations (extensions `postgis` and `pgcrypto`, 5 tables with relational integrity, check constraints, and GiST spatial indexes):
```bash
cd backend
alembic upgrade head
cd ..
```
To check current migration status:
```bash
cd backend
alembic current
cd ..
```

### 4. Database Seeding & Verification Script
Seed the demonstration MODIS and VIIRS fixtures into the database and compute an initial reference harmonisation run:
```bash
PYTHONPATH=. python scripts/seed_demo_fixtures.py
```
This script:
- Reads `tests/fixtures/modis_sample.csv` and `tests/fixtures/viirs_sample.csv`.
- Validates and standardizes records according to Stages A, B, and C.
- Persists source datasets and observations with SHA-256 checksums and immutable raw fields.
- Executes the matching engine (Stage D, E, F) and evaluation service.
- Commits match candidates, harmonised records, and execution summaries.
- Prints comparative baseline statistics (Raw MODIS, Raw VIIRS, Naive Concat, Harmonised).

### 5. Starting Backend & Frontend Services

**Terminal 1 — FastAPI Backend (Port 8000)**:
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**Terminal 2 — Next.js Scientific UI (Port 3000)**:
```bash
cd frontend
npm install
npm run dev -- -p 3000
```
Visit `http://localhost:3000` to interact with all 8 analysis views.

### 6. Automated Verification Test Suite
Run the full test suite (78 tests covering unit, integration, edge cases, negative tests, database ORM, PostGIS repositories, and transactional rollback):
```bash
pytest backend/tests/ -v
```

To run targeted test subsets:
- **Database & ORM Models**:
  ```bash
  pytest backend/tests/test_db_source_models.py backend/tests/test_db_harmonisation_models.py -v
  ```
- **PostGIS Repositories & Migrations**:
  ```bash
  pytest backend/tests/test_db_repositories_and_migrations.py -v
  ```
- **End-to-End System & Rollback Safety**:
  ```bash
  pytest backend/tests/test_end_to_end_system.py -v
  ```
- **Matching Engine & Spatial Indexing**:
  ```bash
  pytest backend/tests/test_matching.py backend/tests/test_matching_engine.py -v
  ```

---

## 7. Scientific Limitations & Disclosure

In compliance with NASA Earth Science Data guidelines and rigorous scientific integrity principles (`docs/10_TESTING_VALIDATION_DEPLOYMENT.md` Section 7 and `docs/03_RESEARCH_METHODOLOGY.md`), users of this software and resulting harmonised datasets must understand the physical and methodological caveats:

### 1. Spatial Resolution Divergence & Sub-Pixel Footprints
- **Nominal Resolution Mismatch**: MODIS thermal channels (Bands 21, 22, 31) have a nominal nadir spatial resolution of **1,000 m (1 km)**. VIIRS Active Fire products provide significantly finer resolution: **375 m** nominal nadir resolution for the I-band product (`VNP14IMGTDL`) and **750 m** for the M-band product (`VNP14`).
- **One-to-Many Physical Geometry**: A single 1 km MODIS pixel footprint geometrically circumscribes approximately $7.1$ VIIRS 375 m pixels at nadir. Consequently, a single large active wildfire detected as one MODIS hotspot often resolves into multiple distinct flaming front pixels in VIIRS. Naive 1-to-1 matching would artificially classify genuine secondary fire fronts as "unmatched". The platform's `retain_ambiguous` and `many_to_many` policies are designed specifically to expose this structural resolution asymmetry.
- **Off-Nadir Footprint Growth (The "Bowtie" Effect)**: Towards swath edges (view zenith angles $>50^\circ$), MODIS pixels expand up to ~4.8 km in the along-scan dimension and ~2.0 km in the along-track dimension. While VIIRS employs 3:1 along-scan sample aggregation to constrain pixel growth, pixels still expand by a factor of 2 to 4. Detections near swath boundaries exhibit greater positional uncertainty.

### 2. Temporal Offset & Wildfire Dynamism
- **Orbit and Overpass Timing**: MODIS onboard Terra flies in a morning descending orbit (~10:30 AM / 10:30 PM local solar time), while Aqua flies in an afternoon ascending orbit (~01:30 PM / 01:30 AM local solar time). VIIRS onboard Suomi-NPP and NOAA-20 flies in afternoon ascending orbits (~01:30 PM / 01:30 AM local solar time; NOAA-20 trails S-NPP by ~50 minutes).
- **Physical Fire Evolution**: Active wildfires are dynamic, non-stationary phenomena that advance, flare, smolder, or extinguish over time intervals of minutes. An observation gap of 15 to 60 minutes between sensor overpasses reflects genuine physical fire behavior changes, fuel consumption, or diurnal wind shifts. Matched pairs separated in time represent related temporal states, not simultaneous snapshots.

### 3. Viewing Geometry, Solar Illumination & Atmospheric Path
- **Solar Zenith & Glint**: Day passes are subject to solar reflection and sunglint artifacts (mitigated by contextual rejection algorithms). Night passes have zero solar reflection, resulting in higher signal-to-noise ratios and lower background thermal noise floors.
- **Atmospheric Attenuation**: Atmospheric moisture, aerosol optical depth, and viewing slant path lengthen attenuation of 4 µm and 11 µm radiances, impacting detection sensitivity and brightness temperature retrievals.

### 4. Cloud, Smoke Plume & Canopy Obscuration
- **Cloud and Heavy Smoke Attenuation**: Heavy cumulus/pyrocumulonimbus clouds or dense, water-saturated smoke plumes completely attenuate thermal infrared radiances, preventing hotspot detection.
- **Canopy Interception**: Understory surface fires under dense forest canopies may produce insufficient upward mid-infrared radiance to trigger detection thresholds, especially for coarse-resolution MODIS pixels.
- **Interpretation of "Unmatched" Detections**: An unmatched MODIS or VIIRS observation must **never** be presumed to be an algorithm failure or false positive. It frequently represents cloud obscuration during one overpass, sensor sensitivity differences, or fire ignition/suppression between orbital passes.

### 5. Fire Radiative Power (FRP) Retrieval Incommensurability
- **Differing Retrieval Physics**:
  - MODIS FRP (MW) is derived using the 4.0 µm channel via the empirical radiance method (Wooster et al., 2003; Kaufman et al., 1998).
  - VIIRS 375 m FRP is derived from the high-resolution 3.74 µm I4 channel with dual-gain radiance thresholds, differing sub-pixel saturation dynamics, and smaller background contextual windows.
- **No Direct Numerical Averaging**: **FRP values from MODIS and VIIRS cannot be naively averaged or directly substituted without empirical cross-sensor regression.** This system preserves sensor-specific FRP values (`frp_modis` and `frp_viirs`) in parallel columns and explicitly refuses naive arithmetic averaging of energy fluxes.

### 6. Algorithmic Nature & Disclaimer of Ground Truth
- **Candidate Proximity vs Physical Certainty**: A spatial-temporal match indicates mathematical proximity under user-defined thresholds ($\Delta d \le d_{\max}$, $\Delta t \le t_{\max}$). It does **not** constitute definitive proof that both sensors viewed identical flame packets.
- **Absence of Machine-Learning Hallucination**: The platform intentionally avoids synthetic generative filling or "black-box" risk predictions. Every output record retains direct cryptographic and relational provenance back to the original source row.
- **Reference Label Prerequisite**: Unless validated against high-resolution airborne thermal infrared imagery or spatially surveyed fire perimeters, precision and recall metrics cannot be reported without explicitly documented ground-truth reference datasets.

---

## 8. License & Citation
Licensed under the Apache License, Version 2.0. When citing active fire data, acknowledge NASA FIRMS, the MODIS Science Team, and the VIIRS Land Science Team per NASA Earth Science Data policies.

