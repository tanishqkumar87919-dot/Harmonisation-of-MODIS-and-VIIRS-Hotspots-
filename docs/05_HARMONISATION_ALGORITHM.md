# Harmonisation Algorithm Specification
## 1. Purpose
Specify a transparent, configurable procedure for standardizing and comparing MODIS and VIIRS hotspot records.

## 2. Design Principles
- Preserve original sensor records and raw measurements.
- Make thresholds configurable and record them for every run.
- Distinguish candidate matches from confirmed event identity.
- Preserve unmatched and ambiguous observations.
- Avoid false precision in match scores.
- Make output reproducible and auditable.

## 3. Processing Stages
### Stage A: Input validation
Validate schema, data types, coordinates, timestamps, and product metadata. Return a validation report.

### Stage B: Standardization
Map source fields to common internal fields. Normalize time to UTC. Preserve raw values, units, confidence fields, and quality flags.

### Stage C: Quality filtering
Apply only documented product-specific quality rules. Record exclusions and reasons. Provide configuration for filters when appropriate.

### Stage D: Candidate pair generation
For each MODIS record, find VIIRS records within a configured time window and spatial distance. Use a spatial index or geospatial database for performance on larger datasets.

Configuration parameters should include:
- `max_time_difference_seconds`
- `max_distance_meters`
- product-specific quality filters
- ambiguity policy
- matching method version

Initial threshold values must be selected after inspecting product characteristics and relevant literature; do not hard-code arbitrary values as scientifically established defaults.

### Stage E: Candidate scoring (optional)
If using a score, document the formula and inputs. A possible ranking score may combine normalized spatial and temporal differences, but it is only a ranking score until calibrated against reliable labelled data.

Do not label a score as a probability unless a calibration procedure and independent evaluation support that interpretation.

### Stage F: Resolve candidates
If one record has several plausible partners:
- use a deterministic one-to-one assignment method when scientifically justified; or
- retain multiple candidates and mark the case ambiguous; or
- apply a documented many-to-many policy.

The selected policy must be stated in the project report and tested.

### Stage G: Output construction
Produce:
1. A match table linking source records.
2. A harmonised view for comparison and visualisation.
3. An unmatched MODIS table/view.
4. An unmatched VIIRS table/view.
5. An ambiguity/candidate table.
6. A run summary and data-quality report.

Do not discard an unmatched detection simply because the other sensor has no nearby record.

## 4. Suggested Pseudocode
```text
load MODIS records and VIIRS records
validate both datasets
standardize common fields while preserving raw fields
apply documented product-specific quality filters
create spatial index for candidate search

for each eligible MODIS record:
    find VIIRS records within configured time window
    filter candidates by configured spatial threshold
    record candidate distance and time difference

resolve candidate relationships using the selected policy
classify records as matched, unmatched, or ambiguous
write results with source IDs, parameters, and method version
generate summary and quality reports
```

## 5. Handling FRP and Other Measurements
Detection matching and measurement harmonisation are separate tasks. Do not average MODIS and VIIRS FRP by default. If measurement adjustment is a project objective, define a separate analysis using product documentation, suitable reference data, and a validation strategy.

## 6. Validation Experiments
- Test multiple spatial thresholds.
- Test multiple temporal thresholds.
- Compare candidate counts and match rates.
- Inspect edge cases with multiple candidate partners.
- Evaluate a manually reviewed sample, if possible.
- Compare with an unharmonised baseline.
- Document the effects of filters and missing data.

## 7. Edge Cases to Test
- Identical coordinates and times.
- Same location but time difference above threshold.
- Close times but distance above threshold.
- One MODIS record with several VIIRS candidates.
- Missing timestamp or coordinates.
- Duplicate source rows.
- Dateline-crossing coordinates if global coverage is in scope.
- Records at study-area boundaries.
- Empty input and one-sensor-only input.

## 8. Outputs Must Include
- source observation identifiers
- source sensor and product version
- match status
- spatial distance and time difference
- thresholds and method version
- any score and its definition
- data-quality warnings
- run identifier and timestamp
