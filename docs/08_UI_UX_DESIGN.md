# UI/UX Design Specification
## 1. Design Goal
Create a clear scientific analysis interface where users can compare original MODIS and VIIRS observations, inspect harmonisation decisions, understand uncertainty, and export reproducible results. Prioritize clarity over decorative effects.

## 2. Suggested Pages
### 1. Overview Dashboard
- Selected study area and time period.
- Input record counts by sensor.
- Valid, warning, and rejected row counts.
- Matched, unmatched, and ambiguous counts.
- Latest processing run status.
- Link to data and methodology notes.

### 2. Dataset Explorer
- Dataset list with sensor, product, version, dates, row count, and retrieval date.
- Schema preview.
- Data-quality summary.
- Download or remove dataset controls, if appropriate.

### 3. Harmonisation Workspace
- Choose input datasets.
- Set spatial and temporal thresholds.
- Select quality filters.
- Select candidate-resolution policy.
- Display a clear warning that thresholds affect results.
- Show a configuration summary before processing.

### 4. Interactive Map
- Separate layers for MODIS, VIIRS, matched, unmatched, and ambiguous observations.
- Legend that remains visible.
- Date, sensor, status, and region filters.
- Click a point to inspect timestamp, source sensor, source ID, product version, quality fields, and match links.
- Cluster dense points when needed.
- Use a documented coordinate reference and avoid misleading map scales.

### 5. Sensor Comparison
- Side-by-side counts and distributions.
- Spatial and temporal difference charts.
- Optional FRP comparisons when valid for selected products.
- Clear denominators and definitions for every percentage.

### 6. Validation
- Matching-threshold sensitivity analysis.
- Counts across threshold configurations.
- Reviewed examples, if a labelled review set exists.
- Method limitations and caveats.

### 7. Reports and Exports
- Export CSV and GeoJSON where supported.
- Include processing parameters, source product versions, run ID, warnings, and timestamp.
- Provide a summary suitable for a project report.

### 8. Methodology and Data Information
- Plain-language explanation of harmonisation.
- Data source and product version notes.
- Definition of match statuses.
- Explanation of score semantics and uncertainty.
- Known limitations.

## 3. Visual Design
- Use a restrained scientific palette with accessible contrast.
- Use consistent sensor colors across every page and legend.
- Do not rely on color alone; include labels or symbols.
- Make map layers and filters easy to find.
- Provide loading, empty, error, and partial-result states.
- Ensure the interface works on laptop and tablet sizes.
- Use concise labels and tooltips for technical terms.

## 4. Suggested Status Labels
- **Matched:** Pair accepted by the configured algorithm.
- **Unmatched MODIS:** No accepted VIIRS partner under the current parameters.
- **Unmatched VIIRS:** No accepted MODIS partner under the current parameters.
- **Ambiguous:** Multiple plausible candidates or insufficient evidence for a unique match.
- **Rejected input row:** Row failed a documented data-quality rule.

Avoid labels such as “confirmed same fire” unless independent evidence supports that conclusion.

## 5. Accessibility and Usability
- Keyboard-accessible controls.
- Visible focus states.
- Readable font sizes.
- Text alternatives for charts.
- Clear validation errors.
- Confirmation before deleting datasets or processing results.

## 6. UI Acceptance Checks
- Map legend agrees with layer styling.
- Filtered counts agree with displayed data.
- Empty datasets do not cause crashes.
- Large result sets do not freeze the page.
- Exports reflect selected filters or clearly state that they contain the full run.
- All results show their processing run and source provenance.
