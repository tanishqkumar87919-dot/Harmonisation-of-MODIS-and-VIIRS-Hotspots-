# System Architecture
## 1. Architectural Goal
Keep data ingestion, scientific processing, persistence, API logic, and user interface separate so the method can be tested independently from the web application.

## 2. Logical Architecture
```text
MODIS files / API              VIIRS files / API
       |                              |
       +--------------+---------------+
                      v
              Ingestion Layer
                      v
             Validation & QC
                      v
          Standardization Pipeline
                      v
       Spatial-Temporal Matching Engine
                      v
       Harmonised Outputs + Run Metadata
                      v
       PostgreSQL/PostGIS or File Storage
                      v
                 FastAPI
                      v
          React/Next.js Frontend
                      v
      Map, Filters, Charts, Detail, Export
```

## 3. Suggested Components
### Ingestion module
Responsibilities:
- Read supported source formats.
- Validate file type and required columns.
- Create an ingestion run.
- Record source metadata and warnings.

### Processing module
Responsibilities:
- Standardize fields.
- Apply quality rules.
- Generate spatial-temporal candidates.
- Resolve candidate matches according to the selected method.
- Create outputs and summary statistics.

### Storage layer
For a small proof of concept, versioned files may be sufficient. For multi-user access or larger data, PostgreSQL/PostGIS is a reasonable option. Keep raw data and derived outputs logically separate.

### API layer
Potential endpoints:
- `GET /api/health` - service health.
- `POST /api/datasets/validate` - validate an uploaded dataset.
- `POST /api/runs` - start a processing run.
- `GET /api/runs/{run_id}` - inspect run status and summary.
- `GET /api/runs/{run_id}/matches` - retrieve match records.
- `GET /api/runs/{run_id}/unmatched` - retrieve unmatched records.
- `GET /api/runs/{run_id}/summary` - retrieve statistics.
- `GET /api/runs/{run_id}/export` - export supported output.

These are proposed endpoints. Confirm request/response schemas before implementation.

### Frontend
Pages can include overview dashboard, dataset explorer, harmonisation setup, map explorer, comparison/validation, and reports.

## 4. Data Flow
1. User selects or uploads data.
2. Backend validates the data and returns a validation summary.
3. User selects documented processing parameters.
4. Backend executes a processing run.
5. Run metadata, warnings, and output references are stored.
6. Frontend requests results and displays counts, map layers, and charts.
7. User exports a selected output.

## 5. Error Handling
- Return understandable validation errors.
- Do not silently switch to fake or synthetic observations.
- Give each run a unique ID.
- Log technical details server-side without exposing secrets.
- Mark failed runs as failed and preserve a useful error summary.
- Prevent partial outputs from being presented as completed results.

## 6. Security and Reliability
- Keep secrets in environment variables or a secret manager.
- Validate uploads and enforce size limits.
- Apply rate limits if publicly exposed.
- Restrict write operations if authentication is added.
- Back up important derived results and metadata.
- Avoid logging sensitive credentials or access tokens.

## 7. Architecture Decisions to Confirm
- File-based prototype or database-backed application.
- Local processing or cloud processing.
- Synchronous or background processing for large datasets.
- Study area and expected data volume.
- Need for authentication.
- Deployment provider and budget.
