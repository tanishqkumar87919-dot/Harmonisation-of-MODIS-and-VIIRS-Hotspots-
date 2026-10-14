# Database and Geospatial Schema
## 1. Purpose
Define a traceable data model for original observations, processing runs, candidate matches, harmonised records, and validation results.

## 2. Design Principles
- Never overwrite original source observations with harmonised values.
- Keep product-specific raw fields available.
- Track source and processing provenance.
- Store matching parameters and method version.
- Separate candidate relationships from final match decisions.

## 3. Proposed Tables
### `datasets`
| Column | Suggested type | Notes |
|---|---|---|
| id | UUID / BIGSERIAL | Primary key |
| sensor | TEXT | MODIS or VIIRS |
| product_name | TEXT | Exact product |
| product_version | TEXT | Product/collection version |
| source_uri | TEXT | Source reference, not a secret URL |
| retrieved_at | TIMESTAMPTZ | Retrieval time |
| checksum | TEXT | Optional integrity check |
| metadata_json | JSONB | Additional source metadata |

### `observations`
| Column | Suggested type | Notes |
|---|---|---|
| id | UUID / BIGSERIAL | Internal key |
| dataset_id | FK | References `datasets` |
| source_record_id | TEXT | Original ID or stable row reference |
| sensor | TEXT | MODIS or VIIRS |
| observed_at | TIMESTAMPTZ | UTC-normalized time |
| latitude | DOUBLE PRECISION | Validate range |
| longitude | DOUBLE PRECISION | Validate range |
| geom | geography(Point, 4326) | Optional PostGIS geometry |
| confidence_raw | TEXT/NUMERIC | Preserve product semantics |
| frp_raw | DOUBLE PRECISION | Original value |
| frp_unit | TEXT | Product-specific unit |
| raw_fields | JSONB | Preserve other source fields |
| quality_status | TEXT | valid, warning, rejected |
| quality_notes | JSONB | Validation findings |

### `processing_runs`
| Column | Suggested type | Notes |
|---|---|---|
| id | UUID | Primary key |
| started_at | TIMESTAMPTZ | Run start |
| completed_at | TIMESTAMPTZ | Nullable until complete |
| status | TEXT | queued, running, succeeded, failed |
| method_version | TEXT | Versioned method |
| parameters | JSONB | Thresholds and filters |
| input_dataset_ids | JSONB or join table | Input references |
| summary | JSONB | Counts, warnings, timings |
| error_summary | TEXT | Safe, non-secret error summary |

### `match_candidates`
| Column | Suggested type | Notes |
|---|---|---|
| id | UUID / BIGSERIAL | Primary key |
| run_id | FK | Processing run |
| modis_observation_id | FK | Candidate MODIS record |
| viirs_observation_id | FK | Candidate VIIRS record |
| spatial_distance_m | DOUBLE PRECISION | Distance metric |
| time_difference_s | DOUBLE PRECISION | Absolute time difference |
| score | DOUBLE PRECISION | Optional, documented score |
| decision | TEXT | accepted, rejected, ambiguous, pending |
| decision_reason | TEXT | Rule or reason |

### `harmonised_records`
| Column | Suggested type | Notes |
|---|---|---|
| id | UUID / BIGSERIAL | Primary key |
| run_id | FK | Processing run |
| match_status | TEXT | matched, unmatched_modis, unmatched_viirs, ambiguous |
| modis_observation_id | FK nullable | Source MODIS record |
| viirs_observation_id | FK nullable | Source VIIRS record |
| attributes | JSONB | Derived fields only, documented |
| provenance | JSONB | Source references and method details |

## 4. Relationships
- One dataset has many observations.
- One processing run uses one or more datasets.
- One processing run has many candidate matches and harmonised records.
- Each harmonised record references its source observation(s).
- Candidate relationships should not imply a final match unless the decision field says so.

## 5. Indexes and Constraints
Consider:
- Index on `observations(dataset_id)`.
- Index on `observations(sensor, observed_at)`.
- Spatial index on `geom` if PostGIS is used.
- Index on `processing_runs(status, started_at)`.
- Unique constraint on source identifiers only if their uniqueness is guaranteed within the relevant product/dataset.
- Check constraints for latitude and longitude.
- Foreign keys to prevent orphaned references.

## 6. Data Retention and Scale
The final schema depends on study area, duration, and data volume. Avoid loading an entire global archive into a small application database without estimating storage and query needs. Large source files may be retained in object storage with metadata in PostgreSQL.

## 7. Important Implementation Note
The schema is a design proposal, not an already-existing database. Validate field types and constraints against the selected source products and actual data before creating migrations.
