"""Backwards compatibility adapter for matching engine."""

from backend.app.services.matching_engine import (
    HarmonisationEngineResult,
    MatchingEngine,
    MatchingEngineService,
)

__all__ = ["MatchingEngine", "MatchingEngineService", "HarmonisationEngineResult"]
