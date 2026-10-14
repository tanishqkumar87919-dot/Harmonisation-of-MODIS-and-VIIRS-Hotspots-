# Persistent Antigravity Agent Rules — Harmonisation of MODIS and VIIRS Hotspots

You are building a scientific geospatial web application and reproducible processing workflow titled **"Harmonisation of MODIS and VIIRS Hotspots"**. Follow these 15 non-negotiable rules on every task:

1. **Read Specifications First**: Always read all 10 documents in `docs/` (`01_PROJECT_OVERVIEW.md` through `10_TESTING_VALIDATION_DEPLOYMENT.md`) before implementing or modifying any feature.
2. **Treat Methodology & Data Dictionary as Authoritative**: Adhere strictly to the schemas in `docs/04_DATA_SOURCES_AND_DICTIONARY.md`, the 7-stage algorithm in `docs/05_HARMONISATION_ALGORITHM.md`, and the database design in `docs/07_DATABASE_SCHEMA.md`.
3. **Never Fabricate Data or Metrics**: Do not invent satellite observations, API responses, evaluation results, precision/recall scores, model accuracy, or academic citations.
4. **No Unlabelled Mock Data in Production Views**: Never embed fake data as real results. During initial frontend development (before the backend is connected), any layout preview fixture must be isolated in an opt-in test fixture module and display a persistent warning banner: `"TEST FIXTURE MODE — NOT REAL SATELLITE OBSERVATIONS"`.
5. **No Silent Fallback on Failure**: When a file upload, validation check, API call, or database query fails, surface a clear, plain-language error state. Never silently switch to synthetic or cached fallback data (`NFR-01`).
6. **Preserve Source Provenance & Raw Values**: Never overwrite original MODIS or VIIRS records. Retain original coordinates, raw timestamps, `confidence_raw`, `frp_raw`, `frp_unit`, `scan_raw`, `track_raw`, and `quality_flags_raw`. Every harmonised record must trace back to its source `modis_observation_id`, `viirs_observation_id`, `ingestion_run_id`, `matching_method_version`, and `matching_parameters`.
7. **Retain Unmatched & Ambiguous Detections**: Never discard unmatched MODIS (`unmatched_modis`) or unmatched VIIRS (`unmatched_viirs`) records. Never arbitrarily merge multi-candidate (`ambiguous`) detections without executing the selected ambiguity policy (`retain_ambiguous`, `one_to_one_deterministic`, or `many_to_many`).
8. **Respect Sensor Physics (No Default FRP Averaging or Probability Claims)**:
   - Do not average MODIS and VIIRS Fire Radiative Power (`frp_raw`) by default.
   - Do not combine MODIS and VIIRS `confidence_raw` values as if they share an identical scale.
   - Do not call `match_score` a "probability" unless calibrated against independent reference labels.
   - Do not label a matched pair as `"confirmed same fire"`; use `"Matched (Algorithm Pair)"`.
9. **Strict Separation of Concerns**: Keep scientific processing logic (`backend/app/services/`) completely independent of FastAPI route handlers (`backend/app/api/`) and React UI components (`frontend/src/`).
10. **Mandatory Automated Testing**: Add or update unit/integration tests for every meaningful code or algorithm change.
11. **Honest Test Reporting**: Run the test commands (`pytest`, `npm run build`, `npx tsc --noEmit`) in the terminal and report the actual output. Never claim tests passed without running them.
12. **Synchronize Documentation**: Update the relevant markdown file in `docs/` or `README.md` if any schema or configuration changes.
13. **Protect Existing Files & Data**: Never delete or overwrite existing user datasets, migrations, or configuration files without inspecting and explaining the impact first.
14. **Secret & Environment Security**: Store all secrets and connection strings in environment variables loaded from `.env`, maintain `.env.example` with safe placeholder values, and keep `.env` out of Git.
15. **Incremental Phased Execution**: Implement one phase at a time, verify all acceptance criteria for that phase, and stop to report completion before moving to the next phase.
