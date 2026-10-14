# Harmonisation of MODIS and VIIRS Hotspots

A reproducible geospatial workflow and scientific web application designed to systematically compare, validate, and harmonise active-fire hotspot observations from NASA's Moderate Resolution Imaging Spectroradiometer (**MODIS**) and the Visible Infrared Imaging Radiometer Suite (**VIIRS**).

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

## 6. Local Development Setup

### Prerequisites
- Node.js >= 18.18.0 & npm >= 9.0.0
- Python >= 3.10
- PostgreSQL >= 15 with PostGIS >= 3.3 (optional for SQLite prototype mode)

### 1. Environment Configuration
```bash
cp .env.example .env
```

### 2. Backend Setup
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:3000` to access the application.

---

## 7. License & Citation
Licensed under the Apache License, Version 2.0. When citing active fire data, acknowledge NASA FIRMS, the MODIS Science Team, and the VIIRS Land Science Team per NASA Earth Science Data policies.
