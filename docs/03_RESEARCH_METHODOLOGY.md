# Research Methodology
## 1. Research Aim
Develop and evaluate a transparent method for comparing and harmonising active-fire hotspot observations from selected MODIS and VIIRS products.

## 2. Research Questions
1. How do observation counts and spatial distributions differ between the selected MODIS and VIIRS products?
2. How sensitive are proposed cross-sensor matches to spatial and temporal thresholds?
3. What proportion of records can be matched, remain unmatched, or require manual/independent review?
4. How do sensor-specific attributes, including confidence and fire radiative power (where available), differ among matched observations?
5. Does the proposed harmonisation method improve consistency for the stated use case without hiding meaningful sensor differences?

## 3. Study Design
Before analysis, specify:
- Study area and boundary source.
- Start and end dates.
- Satellite instruments and exact product/version for each sensor.
- Data access route and download date.
- Inclusion/exclusion rules.
- Spatial and temporal coordinate reference assumptions.
- Primary outcome and evaluation metrics.

## 4. Workflow
### Step 1: Data acquisition
Download records from documented, authoritative sources. Keep product/version metadata and download notes.

### Step 2: Exploratory data analysis
Inspect schema, row counts, date coverage, coordinate ranges, missingness, duplicates, sensor-specific fields, and basic distributions.

### Step 3: Quality control
Apply documented rules for invalid coordinates, malformed timestamps, missing required fields, and product-specific quality flags. Report all exclusions.

### Step 4: Standardization
Create common internal fields such as source_sensor, observation_time_utc, latitude, longitude, source_record_id, product_version, confidence_raw, and frp_raw where available. Preserve original values and units.

### Step 5: Candidate generation
Generate candidate MODIS–VIIRS pairs only within a configured spatial radius and temporal window. Document whether the time rule uses absolute time difference or a directional rule.

### Step 6: Matching
Apply a documented matching method. A baseline can use distance and time thresholds. If multiple candidates are possible, use a deterministic assignment or retain ambiguity rather than arbitrarily selecting a pair. Record every rule and parameter.

### Step 7: Harmonisation
The harmonised output may contain a cross-sensor match record and/or a unified observation view. Do not average or overwrite sensor-specific measurements unless a scientifically justified method has been specified and validated.

### Step 8: Evaluation
Compare output against a baseline and, if available, independent reference data or manually reviewed samples. Report limitations and uncertainty.

### Step 9: Reporting
Produce tables, maps, figures, processing metadata, and reproducible exports.

## 5. Baselines
At minimum, compare:
- MODIS-only observations.
- VIIRS-only observations.
- Naive concatenation with no matching.
- Proposed spatial-temporal matching/harmonisation method.

## 6. Evaluation Metrics
Use metrics that fit the project goal:
- Input and valid-row counts.
- Matched, unmatched, and ambiguous counts.
- Match rate, with its denominator explicitly stated.
- Distribution of spatial distances and time differences.
- Sensitivity analysis over multiple threshold settings.
- Precision/recall or false-match/missed-match rates only when a defensible reference label set exists.
- FRP distribution comparison only when units, product semantics, and quality filters are understood.
- Processing runtime and reproducibility.

## 7. Scientific Cautions
- A hotspot detection is not automatically a unique fire event.
- Nearby detections may be separate fires; one fire may generate multiple detections.
- MODIS or VIIRS must not be assumed to be ground truth for the other.
- Detection absence does not prove a fire was absent.
- Satellite overpass time, viewing geometry, cloud/smoke conditions, and product algorithms can affect observations.
- A matching score is not a probability unless calibrated and validated as such.
- Do not describe a system as real-time unless data ingestion and refresh behaviour support that claim.

## 8. Reproducibility
For every processing run, save:
- Input dataset identifiers and versions.
- Download timestamps and checksums if practical.
- Code/method version.
- Parameters and filters.
- Run timestamp.
- Output counts and warnings.
- Software environment/dependency versions.
