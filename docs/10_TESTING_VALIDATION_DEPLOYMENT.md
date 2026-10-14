# Testing, Scientific Validation, and Deployment Plan
## 1. Purpose
Define how the application will be tested technically and how the scientific method will be evaluated.

## 2. Software Testing
### Unit tests
Test:
- Coordinate validation.
- Timestamp parsing and UTC normalization.
- Product-specific field mappings.
- Missing-value handling.
- Spatial distance calculation.
- Time-difference calculation.
- Candidate filtering.
- Match resolution and ambiguity policy.
- Export schema and units.

### Integration tests
Test:
- Dataset upload to validation report.
- Validated records to processing run.
- Processing run to stored results.
- API response to frontend display.
- Filters to summary counts.
- Export to re-importable output where appropriate.

### Negative tests
Test:
- Empty files.
- Missing required columns.
- Invalid coordinates.
- Malformed timestamps.
- Unsupported file formats.
- No candidate matches.
- Many candidate matches.
- Database/API failure.
- Oversized uploads.
- Interrupted processing runs.

## 3. Scientific Validation
### Baseline comparison
Compare the proposed method with:
- Raw MODIS counts.
- Raw VIIRS counts.
- Simple concatenation.
- The selected harmonisation method.

### Threshold sensitivity
Run multiple documented spatial and temporal thresholds and report how match counts and ambiguity rates change. Do not select thresholds solely because they produce the most matches.

### Reference labels
If feasible, create a manually reviewed sample or use a suitable independent reference dataset. Document the labelling protocol, sampling strategy, reviewer disagreements, and limitations. Without reliable labels, do not report precision or recall as if ground truth were available.

### Suggested metrics
- Total input rows and valid rows.
- Rejected rows and reasons.
- Matched records and match rate.
- Unmatched MODIS and unmatched VIIRS counts.
- Ambiguous candidate count.
- Distribution of spatial and temporal differences.
- Runtime and memory use.
- Precision/recall only where defensible reference labels exist.
- FRP comparisons only when product semantics and units support the analysis.

Define every metric, its denominator, filters, and the dataset version used.

## 4. Acceptance Tests
- A known valid fixture loads successfully.
- An invalid fixture produces a useful validation report.
- The same input and parameters produce reproducible results.
- Every output record has provenance.
- Unmatched observations are not silently discarded.
- Ambiguous cases are represented according to the approved policy.
- API errors do not produce false success messages.
- Map counts and export counts agree with backend results.
- No fabricated results appear in reports.

## 5. Deployment Checklist
- Pin or constrain dependencies.
- Provide documented setup commands.
- Configure environment variables in the deployment platform.
- Keep secrets out of source control and logs.
- Configure database migrations and backups if using a database.
- Set upload size and request limits.
- Configure CORS for the actual frontend origin.
- Add health and readiness checks.
- Capture processing errors and run IDs in logs.
- Verify the application using a small real dataset and a known test fixture.
- Confirm that the app clearly distinguishes real data from any test fixtures.
- Document the exact deployment version and configuration.

## 6. Operations and Maintenance
- Monitor data-source availability and schema changes.
- Revalidate field mappings when product versions change.
- Keep processing parameters and method versions with results.
- Back up data and metadata according to project needs.
- Document known issues and recovery procedures.
- Rerun validation after changes to matching logic or data sources.

## 7. Limitations to Disclose
- Satellite observations have sensor- and product-specific limitations.
- A matched pair is not automatically proof of one physical fire event.
- Results depend on selected products, filters, study area, period, and thresholds.
- Detection differences may reflect acquisition conditions or algorithm characteristics.
- Risk prediction, if added, requires a separate dataset, model, and validation plan.
