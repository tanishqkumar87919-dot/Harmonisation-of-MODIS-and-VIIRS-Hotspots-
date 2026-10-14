# Software Requirements Specification (SRS)
## 1. Purpose
Define verifiable functional and non-functional requirements for the MODIS–VIIRS hotspot harmonisation application.

## 2. System Overview
The system receives active-fire observations from selected MODIS and VIIRS products, validates them, standardizes common fields, performs configurable spatial-temporal matching, and exposes the results through APIs and a user interface.

## 3. Functional Requirements
### Data ingestion
- **FR-01:** The system shall accept supported CSV files and any additional formats explicitly implemented and documented.
- **FR-02:** The system shall record source name, product/version, acquisition or download date, and processing run ID when available.
- **FR-03:** The system shall reject unsupported files with a clear error message.
- **FR-04:** The system shall preserve the original input file or a verifiable reference to it, subject to storage and licensing constraints.

### Data validation and standardization
- **FR-05:** The system shall validate required fields and numeric coordinate ranges.
- **FR-06:** The system shall identify missing values, malformed timestamps, duplicate rows, and invalid coordinates.
- **FR-07:** The system shall normalize field names and timestamp representation without overwriting original sensor-specific values.
- **FR-08:** The system shall document unit conversions and missing-value handling.

### Harmonisation and matching
- **FR-09:** The system shall support configurable spatial and temporal matching thresholds.
- **FR-10:** The system shall record the distance, time difference, source records, method version, and parameters used for each proposed match.
- **FR-11:** The system shall classify observations as matched, unmatched, or ambiguous according to documented rules.
- **FR-12:** The system shall preserve original MODIS and VIIRS observations.
- **FR-13:** The system shall avoid merging ambiguous cases without an explicit, documented rule.
- **FR-14:** The system shall make it possible to rerun a processing job with the same inputs and parameters.

### Analysis and visualisation
- **FR-15:** The user shall be able to filter results by date/time, sensor, region, and match status where those fields are available.
- **FR-16:** The interface shall distinguish MODIS, VIIRS, matched, unmatched, and ambiguous records with a legend.
- **FR-17:** The system shall show summary counts and explain the counting method used.
- **FR-18:** The system shall provide a record-level detail view with source provenance.
- **FR-19:** The system shall support export of processed observations to CSV and, where implemented, GeoJSON.
- **FR-20:** The system shall provide a processing summary including warnings and rejected-row counts.

## 4. Non-Functional Requirements
- **NFR-01 Reliability:** Invalid input must not silently produce a successful-looking output.
- **NFR-02 Reproducibility:** Processing parameters and software/method version must be stored for each run.
- **NFR-03 Performance:** The team shall define a target dataset size and acceptable processing time before performance testing.
- **NFR-04 Usability:** Errors and data limitations must be explained in plain language.
- **NFR-05 Security:** Secrets must be stored outside source control; uploaded files must be validated.
- **NFR-06 Maintainability:** Processing logic must be separated from UI code.
- **NFR-07 Accessibility:** Controls should be keyboard-accessible and use readable contrast.
- **NFR-08 Data integrity:** Source records must remain traceable after processing.

## 5. User Roles
Initial version may use a single analyst role. If authentication is required, define roles and permissions before implementing them. Do not add account management solely for appearance.

## 6. Acceptance Criteria
- A documented sample dataset can be imported.
- Invalid rows are reported and handled according to written rules.
- A matching run produces reproducible output for the same inputs and parameters.
- Each matched record references its source records.
- Unmatched and ambiguous observations remain accessible.
- Map filters and summary counts agree with the underlying query results.
- Exported data contains documented fields and units.

## 7. Assumptions and Dependencies
- Product-specific data dictionaries are available for the chosen product versions.
- The team has permission to access and process the selected data.
- Matching thresholds will be justified and validated rather than chosen only for visual appeal.
