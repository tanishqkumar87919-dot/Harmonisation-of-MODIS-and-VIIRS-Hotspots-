/**
 * Harmonisation of MODIS and VIIRS Hotspots
 * Authoritative TypeScript Type Definitions
 * Directly mapped to:
 * - docs/04_DATA_SOURCES_AND_DICTIONARY.md (Sections 3, 4, 5)
 * - docs/05_HARMONISATION_ALGORITHM.md (Stages A–G)
 * - docs/07_DATABASE_SCHEMA.md
 */

export type SensorType = 'MODIS' | 'VIIRS';

export type RowQualityStatus = 'valid' | 'warning' | 'rejected';

export type MatchStatus = 'matched' | 'unmatched_modis' | 'unmatched_viirs' | 'ambiguous';

export type CandidateDecision = 'accepted' | 'rejected' | 'ambiguous' | 'pending';

export type AmbiguityPolicy = 'retain_ambiguous' | 'one_to_one_deterministic' | 'many_to_many';

export type TimeWindowRule = 'absolute' | 'directional';

export type RunStatus = 'queued' | 'running' | 'succeeded' | 'failed';

export type ReviewStatus = 'unreviewed' | 'confirmed_candidate' | 'flagged_discrepancy';

/**
 * Product Selection Record (04_DATA_SOURCES_AND_DICTIONARY.md Section 3)
 */
export interface ProductSelectionRecord {
  sensor: SensorType;
  product_short_name: string;
  satellite_platform: string;
  product_collection_version: string;
  temporal_coverage: string;
  data_format: string;
  source_download_endpoint: string;
  required_credentials_note: string;
  quality_fields_interpretation: string;
  licence_usage_conditions: string;
}

/**
 * Dataset Record (07_DATABASE_SCHEMA.md - datasets table)
 */
export interface DatasetRecord {
  id: string;
  sensor: SensorType;
  product_name: string;
  product_version: string;
  source_uri: string;
  retrieved_at: string;
  checksum: string;
  total_rows: number;
  valid_rows: number;
  warning_rows: number;
  rejected_rows: number;
  min_time_utc: string | null;
  max_time_utc: string | null;
  bbox: [number, number, number, number] | null; // [min_lon, min_lat, max_lon, max_lat]
  metadata_json: Record<string, unknown>;
  is_test_fixture?: boolean;
}

/**
 * Validation Report produced during Stage A & Ingestion (04_DATA_SOURCES_AND_DICTIONARY.md Section 6)
 */
export interface SchemaMappingPreviewItem {
  source_column: string;
  internal_field: string;
  sample_raw_value: string;
  sample_normalized_value: string;
  unit_or_note: string;
}

export interface ValidationReport {
  dataset_id: string;
  sensor: SensorType;
  product_name: string;
  product_version: string;
  total_input_rows: number;
  valid_count: number;
  warning_count: number;
  rejected_count: number;
  duplicate_row_count: number;
  missing_coordinate_count: number;
  out_of_range_coordinate_count: number;
  malformed_timestamp_count: number;
  missing_required_field_count: number;
  rejection_reasons: Record<string, number>;
  warnings: string[];
  schema_mapping_preview: SchemaMappingPreviewItem[];
}

/**
 * Standardized Observation (04_DATA_SOURCES_AND_DICTIONARY.md Section 4)
 * Contains all 17 internal fields while strictly preserving raw values and sensor physics.
 */
export interface StandardizedObservation {
  // 17 Internal Fields
  observation_id: string;
  dataset_id: string;
  source_record_id: string;
  source_sensor: SensorType;
  platform: string;
  product_name: string;
  product_version: string;
  observation_time_utc: string; // ISO 8601 UTC
  latitude: number;             // [-90.0, 90.0]
  longitude: number;            // [-180.0, 180.0]
  confidence_raw: string | number | null; // Retain sensor-specific scale
  frp_raw: number | null;       // Original value without averaging
  frp_unit: string | null;      // Product specific (e.g. MW)
  scan_raw: number | null;      // Scan pixel size
  track_raw: number | null;     // Track pixel size
  quality_flags_raw: Record<string, unknown> | string | null;
  ingestion_run_id: string;

  // Extended Quality Audit & Metadata
  row_quality_status: RowQualityStatus;
  quality_notes: string[];
  raw_fields: Record<string, unknown>;
}

/**
 * Matching Parameters configured for a processing run (05_HARMONISATION_ALGORITHM.md Stage D)
 */
export interface MatchingQualityFilters {
  include_warnings: boolean;
  min_modis_confidence?: number | null;
  allowed_viirs_confidence_levels?: string[];
}

export interface ScoreWeights {
  spatial_weight: number;
  temporal_weight: number;
}

export interface MatchingParameters {
  max_distance_meters: number;
  max_time_difference_seconds: number;
  time_window_rule: TimeWindowRule;
  ambiguity_policy: AmbiguityPolicy;
  matching_method_version: string;
  quality_filters: MatchingQualityFilters;
  score_weights?: ScoreWeights;
}

/**
 * Match Candidate Record (07_DATABASE_SCHEMA.md - match_candidates table)
 */
export interface MatchCandidateRecord {
  id: string;
  run_id: string;
  modis_observation_id: string;
  viirs_observation_id: string;
  spatial_distance_m: number;
  time_difference_s: number;
  score: number | null;
  decision: CandidateDecision;
  decision_reason: string;
}

/**
 * Harmonised Record (04_DATA_SOURCES_AND_DICTIONARY.md Section 5)
 */
export interface HarmonisedRecordProvenance {
  modis_source_record_id?: string | null;
  viirs_source_record_id?: string | null;
  modis_product_version?: string | null;
  viirs_product_version?: string | null;
  score_formula_note?: string;
  candidate_count?: number;
  decision_reason?: string;
}

export interface HarmonisedRecord {
  harmonisation_id: string;
  run_id: string;
  modis_observation_id: string | null;
  viirs_observation_id: string | null;
  match_status: MatchStatus;
  spatial_distance_m: number | null;
  time_difference_s: number | null;
  matching_method_version: string;
  matching_parameters: MatchingParameters;
  match_score: number | null;
  review_status: ReviewStatus | null;
  provenance: HarmonisedRecordProvenance;

  // Embedded relations for rich UI rendering
  modis_observation?: StandardizedObservation | null;
  viirs_observation?: StandardizedObservation | null;
  candidate_links?: MatchCandidateRecord[];
}

/**
 * Processing Run Summary (07_DATABASE_SCHEMA.md & 08_UI_UX_DESIGN.md)
 */
export interface ProcessingRunCounts {
  modis_input_rows: number;
  viirs_input_rows: number;
  modis_valid_rows: number;
  viirs_valid_rows: number;
  modis_warning_rows: number;
  viirs_warning_rows: number;
  modis_rejected_rows: number;
  viirs_rejected_rows: number;
  matched_count: number;
  unmatched_modis_count: number;
  unmatched_viirs_count: number;
  ambiguous_count: number;
  total_candidate_pairs: number;
}

export interface ProcessingRunRates {
  modis_match_rate: number;
  modis_match_rate_denominator: string;
  viirs_match_rate: number;
  viirs_match_rate_denominator: string;
  ambiguity_rate: number;
  ambiguity_rate_denominator: string;
}

export interface ProcessingRunSummary {
  run_id: string;
  started_at: string;
  completed_at: string | null;
  status: RunStatus;
  method_version: string;
  parameters: MatchingParameters;
  input_dataset_ids: {
    modis_dataset_id: string | null;
    viirs_dataset_id: string | null;
  };
  counts: ProcessingRunCounts;
  rates: ProcessingRunRates;
  warnings: string[];
  error_summary: string | null;
  is_test_fixture?: boolean;
}

/**
 * Request payload to create a new processing run
 */
export interface RunCreateRequest {
  modis_dataset_id: string;
  viirs_dataset_id: string;
  parameters: MatchingParameters;
}

/**
 * Map and View Filter State
 */
export interface MapFilterState {
  sensors?: SensorType[];
  match_statuses?: MatchStatus[];
  min_date_utc?: string;
  max_date_utc?: string;
  min_confidence_modis?: number;
  allowed_viirs_confidence?: string[];
  max_spatial_distance_m?: number;
  max_time_difference_s?: number;
  bbox?: [number, number, number, number];
  limit?: number;
  offset?: number;
}

/**
 * Detailed Evaluation Metrics for Validation View (docs/03_RESEARCH_METHODOLOGY.md)
 */
export interface BaselineComparisonMetrics {
  name: string;
  description: string;
  total_records: number;
  unique_time_locations: number;
  duplicate_estimate: number;
}

export interface SensitivityGridPoint {
  spatial_threshold_m: number;
  temporal_threshold_s: number;
  matched_count: number;
  ambiguous_count: number;
  unmatched_modis_count: number;
  unmatched_viirs_count: number;
  match_rate: number;
  viirs_match_rate?: number;
  ambiguity_rate?: number;
}

export interface FourBaselinesComparison {
  modis_only: {
    valid_modis_count: number;
    date_range: [string, string];
    bbox: [number, number, number, number];
    frp_mean?: number;
    frp_median?: number;
  };
  viirs_only: {
    valid_viirs_count: number;
    date_range: [string, string];
    bbox: [number, number, number, number];
    frp_mean?: number;
    frp_median?: number;
  };
  naive_concatenation: {
    total_naive_count: number;
    estimated_duplicate_overlap_count: number;
  };
  proposed_harmonisation: {
    matched_count: number;
    unmatched_modis_count: number;
    unmatched_viirs_count: number;
    ambiguous_count: number;
    distinct_harmonised_records_count: number;
    modis_match_rate: number;
    modis_match_rate_denominator: string;
    viirs_match_rate: number;
    viirs_match_rate_denominator: string;
  };
}

export interface RunDetailedEvaluation {
  run_id: string;
  baselines: BaselineComparisonMetrics[];
  sensitivity_grid: SensitivityGridPoint[];
  spatial_distance_distribution: Array<{ bin: string; count: number }>;
  time_difference_distribution: Array<{ bin: string; count: number }>;
  frp_distribution?: {
    modis_frp: Array<{ bin: string; count: number }>;
    viirs_frp: Array<{ bin: string; count: number }>;
    scientific_disclaimer: string;
  };
  four_baselines?: FourBaselinesComparison;
  frp_percentiles?: Record<string, { p10: number; p25: number; p50: number; p75: number; p90: number; mean: number }>;
  temporal_hourly_distribution?: Array<{ bin: string; count: number }>;
}

/**
 * Health Check Response (docs/06_SYSTEM_ARCHITECTURE.md)
 */
export interface HealthResponse {
  status: 'ok' | 'degraded' | 'error';
  service: string;
  version: string;
  timestamp: string;
  database_connected: boolean;
}
