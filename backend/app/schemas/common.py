"""Common enums and core primitives for MODIS/VIIRS harmonisation."""

from enum import Enum


class SensorType(str, Enum):
    MODIS = "MODIS"
    VIIRS = "VIIRS"


class RowQualityStatus(str, Enum):
    VALID = "valid"
    WARNING = "warning"
    REJECTED = "rejected"


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
