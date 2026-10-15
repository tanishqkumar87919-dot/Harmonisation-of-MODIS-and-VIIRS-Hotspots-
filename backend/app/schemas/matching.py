"""Pydantic models for Candidate generation, Matching parameters, and Harmonised records."""

from typing import List, Optional
from pydantic import BaseModel, Field
from backend.app.schemas.common import (
    AmbiguityPolicy,
    CandidateDecision,
    MatchStatus,
    ReviewStatus,
    TimeWindowRule,
)
from backend.app.schemas.observation import StandardizedObservation


class MatchingQualityFilters(BaseModel):
    include_warnings: bool = True
    min_modis_confidence: Optional[float] = None
    allowed_viirs_confidence_levels: Optional[List[str]] = None


class ScoreWeights(BaseModel):
    spatial_weight: float = 0.5
    temporal_weight: float = 0.5


class MatchingParameters(BaseModel):
    max_distance_meters: float = 1500.0
    max_time_difference_seconds: float = 3600.0
    time_window_rule: TimeWindowRule = TimeWindowRule.ABSOLUTE
    ambiguity_policy: AmbiguityPolicy = AmbiguityPolicy.RETAIN_AMBIGUOUS
    matching_method_version: str = "v1.0.0-spatial-temporal-heuristic"
    quality_filters: MatchingQualityFilters = Field(default_factory=MatchingQualityFilters)
    score_weights: Optional[ScoreWeights] = None


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


class HarmonisedRecordProvenance(BaseModel):
    modis_source_record_id: Optional[str] = None
    viirs_source_record_id: Optional[str] = None
    modis_product_version: Optional[str] = None
    viirs_product_version: Optional[str] = None
    score_formula_note: Optional[str] = None
    candidate_count: Optional[int] = None
    decision_reason: Optional[str] = None


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
    modis_observation: Optional[StandardizedObservation] = None
    viirs_observation: Optional[StandardizedObservation] = None
    candidate_links: Optional[List[MatchCandidateRecord]] = None


class RunCreateRequest(BaseModel):
    modis_dataset_id: str
    viirs_dataset_id: str
    parameters: MatchingParameters
