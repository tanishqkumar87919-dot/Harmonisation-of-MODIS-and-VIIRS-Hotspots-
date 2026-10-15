"""Pydantic models for Processing Runs, Evaluation metrics, and Health check."""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from backend.app.schemas.common import RunStatus
from backend.app.schemas.matching import MatchingParameters


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


class ProcessingRunRates(BaseModel):
    modis_match_rate: float = 0.0
    modis_match_rate_denominator: str = "valid MODIS rows"
    viirs_match_rate: float = 0.0
    viirs_match_rate_denominator: str = "valid VIIRS rows"
    ambiguity_rate: float = 0.0
    ambiguity_rate_denominator: str = "total candidate pairs"


class InputDatasetIds(BaseModel):
    modis_dataset_id: Optional[str] = None
    viirs_dataset_id: Optional[str] = None


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


class BaselineComparisonMetrics(BaseModel):
    name: str
    description: str
    total_records: int
    unique_time_locations: int
    duplicate_estimate: int


class SensitivityGridPoint(BaseModel):
    spatial_threshold_m: float
    temporal_threshold_s: float
    matched_count: int
    ambiguous_count: int
    unmatched_modis_count: int
    unmatched_viirs_count: int
    match_rate: float


class DistributionBin(BaseModel):
    bin: str
    count: int


class FrpDistribution(BaseModel):
    modis_frp: List[DistributionBin] = Field(default_factory=list)
    viirs_frp: List[DistributionBin] = Field(default_factory=list)
    scientific_disclaimer: str


class RunDetailedEvaluation(BaseModel):
    run_id: str
    baselines: List[BaselineComparisonMetrics] = Field(default_factory=list)
    sensitivity_grid: List[SensitivityGridPoint] = Field(default_factory=list)
    spatial_distance_distribution: List[DistributionBin] = Field(default_factory=list)
    time_difference_distribution: List[DistributionBin] = Field(default_factory=list)
    frp_distribution: Optional[FrpDistribution] = None


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: str
    database_connected: bool
