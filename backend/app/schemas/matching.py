"""Re-export matching schemas from authoritative runs module to prevent Pydantic duplicate class mismatch."""

from backend.app.schemas.runs import (
    AmbiguityPolicy,
    CandidateDecision,
    HarmonisedRecord,
    HarmonisedRecordProvenance,
    MatchCandidateRecord,
    MatchingParameters,
    MatchingQualityFilters,
    MatchStatus,
    ReviewStatus,
    RunCreateRequest,
    ScoreWeights,
    TimeWindowRule,
)

__all__ = [
    "AmbiguityPolicy",
    "CandidateDecision",
    "HarmonisedRecord",
    "HarmonisedRecordProvenance",
    "MatchCandidateRecord",
    "MatchingParameters",
    "MatchingQualityFilters",
    "MatchStatus",
    "ReviewStatus",
    "RunCreateRequest",
    "ScoreWeights",
    "TimeWindowRule",
]
