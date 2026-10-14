# Test Sample Fixtures (`data/samples/`)

## Purpose
This directory contains small, deterministic, synthetic and curated test fixtures used strictly for automated unit and integration testing of the harmonisation pipeline.

## Scientific Integrity & Non-Fabrication Rules
In accordance with **Rule 3** (Never Fabricate Data or Metrics), **Rule 4** (No Unlabelled Mock Data in Production Views), and **`04_DATA_SOURCES_AND_DICTIONARY.md` Section 7**:

1. **Test Fixtures Only**: Data files located in this directory are synthetic or truncated fixtures designed to test edge cases (such as exact spatial colocation, borderline temporal deltas, ambiguous multi-partner pairings, coordinate bounds violations, and malformed timestamps).
2. **Never Present as Real Observations**: These fixtures must **never** be presented in user-facing production interfaces or scientific publications as actual empirical satellite observations.
3. **Opt-In Preview Isolation**: Any UI preview utilizing fixture data prior to live backend connection must display the mandatory persistent banner:
   > `"TEST FIXTURE MODE — NOT REAL SATELLITE OBSERVATIONS"`
4. **Git Inclusion**: Only minimal, version-controlled fixtures for testing are committed here. Large raw satellite granules (HDF, NetCDF, GeoTIFF, large CSVs) are excluded via `.gitignore`.
