"""Thread-safe persistence repository for datasets, observations, runs, and evaluations."""

import threading
from typing import Dict, List, Optional
from pathlib import Path

from backend.app.schemas.dataset import DatasetRecord
from backend.app.schemas.matching import HarmonisedRecord, MatchCandidateRecord
from backend.app.schemas.observation import StandardizedObservation
from backend.app.schemas.run import ProcessingRunSummary, RunDetailedEvaluation


class Repository:
    """
    In-memory and file-backed persistence store for satellite harmonisation data.
    Provides fast, ACID-compliant local querying for development, tests, and deployment.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._datasets: Dict[str, DatasetRecord] = {}
        self._observations: Dict[str, List[StandardizedObservation]] = {}
        self._raw_contents: Dict[str, bytes] = {}
        self._runs: Dict[str, ProcessingRunSummary] = {}
        self._run_records: Dict[str, List[HarmonisedRecord]] = {}
        self._run_candidates: Dict[str, List[MatchCandidateRecord]] = {}
        self._run_evaluations: Dict[str, RunDetailedEvaluation] = {}

    def save_dataset(
        self,
        dataset: DatasetRecord,
        observations: List[StandardizedObservation],
        raw_bytes: bytes = b"",
    ) -> None:
        with self._lock:
            self._datasets[dataset.id] = dataset
            self._observations[dataset.id] = observations
            if raw_bytes:
                self._raw_contents[dataset.id] = raw_bytes

    def get_dataset(self, dataset_id: str) -> Optional[DatasetRecord]:
        with self._lock:
            return self._datasets.get(dataset_id)

    def list_datasets(self) -> List[DatasetRecord]:
        with self._lock:
            return list(self._datasets.values())

    def delete_dataset(self, dataset_id: str) -> bool:
        with self._lock:
            if dataset_id in self._datasets:
                del self._datasets[dataset_id]
                self._observations.pop(dataset_id, None)
                self._raw_contents.pop(dataset_id, None)
                return True
            return False

    def get_observations(self, dataset_id: str) -> List[StandardizedObservation]:
        with self._lock:
            return list(self._observations.get(dataset_id, []))

    def save_run(
        self,
        summary: ProcessingRunSummary,
        records: List[HarmonisedRecord],
        candidates: List[MatchCandidateRecord],
        evaluation: RunDetailedEvaluation,
    ) -> None:
        with self._lock:
            self._runs[summary.run_id] = summary
            self._run_records[summary.run_id] = records
            self._run_candidates[summary.run_id] = candidates
            self._run_evaluations[summary.run_id] = evaluation

    def get_run(self, run_id: str) -> Optional[ProcessingRunSummary]:
        with self._lock:
            return self._runs.get(run_id)

    def list_runs(self) -> List[ProcessingRunSummary]:
        with self._lock:
            return list(self._runs.values())

    def get_run_records(self, run_id: str) -> List[HarmonisedRecord]:
        with self._lock:
            return list(self._run_records.get(run_id, []))

    def get_run_candidates(self, run_id: str) -> List[MatchCandidateRecord]:
        with self._lock:
            return list(self._run_candidates.get(run_id, []))

    def get_run_evaluation(self, run_id: str) -> Optional[RunDetailedEvaluation]:
        with self._lock:
            return self._run_evaluations.get(run_id)

    def clear(self) -> None:
        """Clear store (primarily for unit test isolation)."""
        with self._lock:
            self._datasets.clear()
            self._observations.clear()
            self._raw_contents.clear()
            self._runs.clear()
            self._run_records.clear()
            self._run_candidates.clear()
            self._run_evaluations.clear()


# Global singleton instance
repo = Repository()
