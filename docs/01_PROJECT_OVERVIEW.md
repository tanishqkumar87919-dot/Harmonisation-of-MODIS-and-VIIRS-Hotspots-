# Project Overview
## Project Title
**Harmonisation of MODIS and VIIRS Hotspots**

## 1. Project Summary
This project aims to build a reproducible geospatial workflow and web application that makes active-fire hotspot observations from MODIS and VIIRS easier to compare. The system will ingest observations, validate and standardize fields, identify potentially corresponding detections using documented spatial and temporal rules, preserve unmatched observations, and present results through maps, summaries, and downloadable reports.

The project must distinguish **harmonisation** from simply merging files. MODIS and VIIRS have different instrument characteristics, spatial resolutions, observation timing, product versions, and detection behaviour. A harmonised output should retain source provenance and make uncertainty visible.

## 2. Problem Being Addressed
Datasets from different satellite instruments are not automatically interchangeable. Combining them without consistent preprocessing and matching rules can create duplicate counts, hide sensor-specific detections, or imply a level of certainty that the data does not support.

## 3. Proposed Solution
Create a modular application with:
1. Data ingestion for supported MODIS and VIIRS active-fire products.
2. Validation and standardized internal fields.
3. Spatial-temporal candidate matching.
4. A harmonisation output that retains original records and records matching decisions.
5. Sensor comparison and data-quality analysis.
6. Interactive map, filters, summary charts, and exports.
7. Reproducible processing logs and validation reports.

## 4. Primary Users
- Researchers and students studying active-fire observations.
- Environmental analysts.
- Fire-monitoring and disaster-management teams.
- Project evaluators who need to inspect the method and results.

## 5. Expected Outputs
- Cleaned, standardized observation tables.
- Matched, unmatched, and ambiguous detection records.
- Summary statistics by sensor, region, and time period.
- Interactive geospatial visualisation.
- Exportable CSV/GeoJSON and a report summarising data, method, parameters, and limitations.

## 6. Suggested Technology Stack
- Python for processing.
- Pandas and NumPy for tabular data.
- GeoPandas, Shapely, and PyProj for vector/geospatial operations.
- FastAPI for backend APIs.
- PostgreSQL with PostGIS for persistent geospatial storage, if a database is needed.
- React or Next.js with TypeScript for the web interface.
- Leaflet or MapLibre GL JS for maps.
- Pytest for automated tests.

The stack is provisional. Confirm it against team skills, dataset size, hosting constraints, and the final assignment requirements before implementation.

## 7. Scope
### In scope
- Active-fire/hotspot data ingestion from documented sources.
- Standardization of relevant fields.
- Spatial and temporal matching with configurable parameters.
- Sensor comparison, quality checks, and uncertainty/provenance tracking.
- Visualisation and export.

### Out of scope unless separately approved
- Guaranteed real-time fire detection.
- Guaranteed prediction of fire spread.
- Treating one satellite product as ground truth for another.
- Claiming that all nearby detections represent the same physical fire.
- Training an ML model before suitable labels, data, and an evaluation design exist.

## 8. Success Criteria
The initial release is successful when:
- Sample data can be ingested and validated.
- Every output record can be traced to its source observation(s).
- Matching parameters are configurable and recorded.
- Matched, unmatched, and ambiguous cases are represented.
- The results can be inspected on a map and exported.
- Tests cover important data-quality and matching edge cases.
- No synthetic data or invented performance metrics are presented as real results.

## 9. Decisions to Confirm
- Study area: India, a selected region, or global.
- Study period and temporal resolution.
- Exact MODIS and VIIRS products and collection versions.
- Whether the primary goal is detection matching, measurement harmonisation, or a combined product.
- Whether the application needs user accounts or can remain a research tool.
- Expected dataset volume and deployment environment.
