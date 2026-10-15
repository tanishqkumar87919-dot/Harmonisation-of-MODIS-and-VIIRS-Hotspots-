"""Pydantic v2 schemas for Processing Runs, Matching Candidates, and Harmonised Records."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from backend.app.schemas.observations import StandardizedObservationSchema


class MatchStatus(str, Enum):
    MATCHED = "matched"
    UNMATCHED_MODIS = "unmatched_modis"
    UNMATCHED_VIIRS = "unmatched_viirs"
    AMBIGUOUS = "ambiguous"


class CandidateDecision(str, Enum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    AMBIGUOUS = "ambiguous"
    PENDING = "pending"


class AmbiguityPolicy(str, Enum):
    RETAIN_AMBIGUOUS = "retain_ambiguous"
    ONE_TO_ONE_DETERMINISTIC = "one_to_one_deterministic"
    MANY_TO_MANY = "many_to_many"


class TimeWindowRule(str, Enum):
    ABSOLUTE = "absolute"
    DIRECTIONAL = "directional"


class RunStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class ReviewStatus(str, Enum):
    UNREVIEWED = "unreviewed"
    CONFIRMED_CANDIDATE = "confirmed_candidate"
    FLAGGED_DISCREPANCY = "flagged_discrepancy"


class MatchingQualityFilters(BaseModel):
    include_warnings: bool = True
    min_modis_confidence: Optional[float] = None
    allowed_viirs_confidence_levels: Optional[List[str]] = None

    model_config = ConfigDict(from_attributes=True)


class ScoreWeights(BaseModel):
    spatial_weight: float = Field(default=0.5, ge=0.0, le=1.0)
    temporal_weight: float = Field(default=0.5, ge=0.0, le=1.0)

    model_config = ConfigDict(from_attributes=True)


class MatchingParameters(BaseModel):
    max_distance_meters: float = Field(default=1500.0, gt=0.0)
    max_time_difference_seconds: float = Field(default=3600.0, gt=0.0)
    time_window_rule: TimeWindowRule = TimeWindowRule.ABSOLUTE
    ambiguity_policy: AmbiguityPolicy = AmbiguityPolicy.RETAIN_AMBIGUOUS
    matching_method_version: str = "v1.0.0-spatial-temporal-heuristic"
    quality_filters: MatchingQualityFilters = Field(default_factory=MatchingQualityFilters)
    score_weights: Optional[ScoreWeights] = None

    model_config = ConfigDict(from_attributes=True)


class MatchCandidateRecord(BaseModel):
    id: str
    run_id: str
    modis_observation_id: str
    viirs_observation_id: str
    spatial_distance_m: float
    time_difference_s: float
    score: Optional[float] = None
    decision: CandidateDecision = CandidateDecision.PENDING
    decision_reason: str = ""

    model_config = ConfigDict(from_attributes=True)


class HarmonisedRecordProvenance(BaseModel):
    modis_source_record_id: Optional[str] = None
    viirs_source_record_id: Optional[str] = None
    modis_product_version: Optional[str] = None
    viirs_product_version: Optional[str] = None
    score_formula_note: Optional[str] = None
    candidate_count: Optional[int] = None
    decision_reason: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class HarmonisedRecord(BaseModel):
    harmonisation_id: str
    run_id: str
    modis_observation_id: Optional[str] = None
    viirs_observation_id: Optional[str] = None
    match_status: MatchStatus
    spatial_distance_m: Optional[float] = None
    time_difference_s: Optional[float] = None
    matching_method_version: str
    matching_parameters: MatchingParameters
    match_score: Optional[float] = None
    review_status: Optional[ReviewStatus] = ReviewStatus.UNREVIEWED
    provenance: HarmonisedRecordProvenance = Field(default_factory=HarmonisedRecordProvenance)

    # Embedded relational observations for UI rendering
    modis_observation: Optional[StandardizedObservationSchema] = None
    viirs_observation: Optional[StandardizedObservationSchema] = None
    candidate_links: Optional[List[MatchCandidateRecord]] = None

    model_config = ConfigDict(from_attributes=True)


class RunCreateRequest(BaseModel):
    modis_dataset_id: str
    viirs_dataset_id: str
    parameters: MatchingParameters

    model_config = ConfigDict(from_attributes=True)


class ProcessingRunCounts(BaseModel):
    modis_input_rows: int = 0
    viirs_input_rows: int = 0
    modis_valid_rows: int = 0
    viirs_valid_rows: int = 0
    modis_warning_rows: int = 0
    viirs_warning_rows: int = 0
    modis_rejected_rows: int = 0
    viirs_rejected_rows: int = 0
    matched_count: int = 0
    unmatched_modis_count: int = 0
    unmatched_viirs_count: int = 0
    ambiguous_count: int = 0
    total_candidate_pairs: int = 0

    model_config = ConfigDict(from_attributes=True)


class ProcessingRunRates(BaseModel):
    modis_match_rate: float = 0.0
    modis_match_rate_denominator: str = "valid MODIS rows"
    viirs_match_rate: float = 0.0
    viirs_match_rate_denominator: str = "valid VIIRS rows"
    ambiguity_rate: float = 0.0
    ambiguity_rate_denominator: str = "total candidate pairs"

    model_config = ConfigDict(from_attributes=True)


class InputDatasetIds(BaseModel):
    modis_dataset_id: Optional[str] = None
    viirs_dataset_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ProcessingRunSummary(BaseModel):
    run_id: str
    started_at: str
    completed_at: Optional[str] = None
    status: RunStatus = RunStatus.QUEUED
    method_version: str
    parameters: MatchingParameters
    input_dataset_ids: InputDatasetIds
    counts: ProcessingRunCounts = Field(default_factory=ProcessingRunCounts)
    rates: ProcessingRunRates = Field(default_factory=ProcessingRunRates)
    warnings: List[str] = Field(default_factory=list)
    error_summary: Optional[str] = None
    is_test_fixture: bool = False

    model_config = ConfigDict(from_attributes=True)


class BaselineComparisonMetrics(BaseModel):
    name: str
    description: str
    total_records: int
    unique_time_locations: int
    duplicate_estimate: int

    model_config = ConfigDict(from_attributes=True)


class SensitivityGridPoint(BaseModel):
    spatial_threshold_m: float
    temporal_threshold_s: float
    matched_count: int
    ambiguous_count: int
    unmatched_modis_count: int
    unmatched_viirs_count: int
    match_rate: float

    model_config = ConfigDict(from_attributes=True)


class DistributionBin(BaseModel):
    bin: str
    count: int

    model_config = ConfigDict(from_attributes=True)


class FrpDistribution(BaseModel):
    modis_frp: List[DistributionBin] = Field(default_factory=list)
    viirs_frp: List[DistributionBin] = Field(default_factory=list)
    scientific_disclaimer: str

    model_config = ConfigDict(from_attributes=True)


class RunDetailedEvaluation(BaseModel):
    run_id: str
    baselines: List[BaselineComparisonMetrics] = Field(default_factory=list)
    sensitivity_grid: List[SensitivityGridPoint] = Field(default_factory=list)
    spatial_distance_distribution: List[DistributionBin] = Field(default_factory=list)
    time_difference_distribution: List[DistributionBin] = Field(default_factory=list)
    frp_distribution: Optional[FrpDistribution] = None

    model_config = ConfigDict(from_attributes=True)


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: str
    database_connected: bool

    model_config = ConfigDict(from_attributes=True)
