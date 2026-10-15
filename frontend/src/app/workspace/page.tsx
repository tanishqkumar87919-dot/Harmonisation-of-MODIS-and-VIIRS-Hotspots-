'use client';

import React, { useEffect, useState } from 'react';
import { useFixtureMode } from '@/lib/fixtures/FixtureContext';
import {
  FIXTURE_DATASETS,
  FIXTURE_RUN_SUMMARY,
} from '@/lib/fixtures/labelledTestFixtures';
import { apiClient, ApiError } from '@/lib/api/client';
import {
  AmbiguityPolicy,
  DatasetRecord,
  MatchingParameters,
  MatchingQualityFilters,
  ProcessingRunSummary,
  ScoreWeights,
  TimeWindowRule,
} from '@/types/harmonisation';
import { DatasetPairSelector } from '@/components/harmonisation/DatasetPairSelector';
import { ThresholdAndFilterControls } from '@/components/harmonisation/ThresholdAndFilterControls';
import { AmbiguityPolicySelector } from '@/components/harmonisation/AmbiguityPolicySelector';
import { PreRunConfigurationSummary } from '@/components/harmonisation/PreRunConfigurationSummary';
import { RunHistoryAndRerunTable } from '@/components/harmonisation/RunHistoryAndRerunTable';
import { ErrorAlert, LoadingState } from '@/components/common/StateViews';
import { CheckCircle2, RefreshCw, Sliders } from 'lucide-react';

export default function HarmonisationWorkspacePage() {
  const { isFixtureMode } = useFixtureMode();

  // Loading & Datasets / Runs State
  const [loading, setLoading] = useState<boolean>(!isFixtureMode);
  const [error, setError] = useState<ApiError | null>(null);
  const [datasets, setDatasets] = useState<DatasetRecord[]>([]);
  const [runs, setRuns] = useState<ProcessingRunSummary[]>([]);
  const [lastCompletedRun, setLastCompletedRun] = useState<ProcessingRunSummary | null>(null);

  // Form State
  const [selectedModisId, setSelectedModisId] = useState<string>('');
  const [selectedViirsId, setSelectedViirsId] = useState<string>('');
  const [maxDistanceMeters, setMaxDistanceMeters] = useState<number>(1500);
  const [maxTimeDifferenceSeconds, setMaxTimeDifferenceSeconds] = useState<number>(3600);
  const [timeWindowRule, setTimeWindowRule] = useState<TimeWindowRule>('absolute');
  const [ambiguityPolicy, setAmbiguityPolicy] = useState<AmbiguityPolicy>('retain_ambiguous');
  const [qualityFilters, setQualityFilters] = useState<MatchingQualityFilters>({
    include_warnings: true,
    min_modis_confidence: 30,
    allowed_viirs_confidence_levels: ['nominal', 'high'],
  });
  const [scoreWeights, setScoreWeights] = useState<ScoreWeights>({
    spatial_weight: 0.6,
    temporal_weight: 0.4,
  });

  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  const fetchWorkspaceData = async () => {
    if (isFixtureMode) {
      setDatasets(FIXTURE_DATASETS);
      setRuns([FIXTURE_RUN_SUMMARY]);
      setSelectedModisId(FIXTURE_DATASETS[0].id);
      setSelectedViirsId(FIXTURE_DATASETS[1].id);
      setLoading(false);
      setError(null);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const [fetchedDatasets, fetchedRuns] = await Promise.all([
        apiClient.listDatasets(),
        apiClient.listProcessingRuns(),
      ]);
      setDatasets(fetchedDatasets);
      setRuns(fetchedRuns);

      const modis = fetchedDatasets.find((d) => d.sensor === 'MODIS');
      const viirs = fetchedDatasets.find((d) => d.sensor === 'VIIRS');
      if (modis) setSelectedModisId(modis.id);
      if (viirs) setSelectedViirsId(viirs.id);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err);
      } else {
        setError(
          new ApiError(
            0,
            '/runs',
            'Failed to connect to harmonisation workspace backend',
            'Verify the FastAPI server is running at http://localhost:8000 or toggle "Fixture Preview" to inspect UI layout.',
            err
          )
        );
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWorkspaceData();
  }, [isFixtureMode]);

  // Validation
  let validationError: string | null = null;
  if (!selectedModisId || !selectedViirsId) {
    validationError = 'Select both a MODIS and a VIIRS target dataset before launching run.';
  } else if (maxDistanceMeters <= 0) {
    validationError = 'Spatial distance threshold must be greater than 0 metres.';
  } else if (maxTimeDifferenceSeconds < 0) {
    validationError = 'Temporal window must be 0 or greater seconds.';
  }

  const isValid = validationError === null;

  const currentParameters: MatchingParameters = {
    max_distance_meters: maxDistanceMeters,
    max_time_difference_seconds: maxTimeDifferenceSeconds,
    time_window_rule: timeWindowRule,
    ambiguity_policy: ambiguityPolicy,
    matching_method_version: '1.0.0',
    quality_filters: qualityFilters,
    score_weights: scoreWeights,
  };

  const handleLaunchRun = async () => {
    if (!isValid || isSubmitting) return;

    setIsSubmitting(true);
    setError(null);

    if (isFixtureMode) {
      setTimeout(() => {
        const syntheticRun: ProcessingRunSummary = {
          ...FIXTURE_RUN_SUMMARY,
          run_id: `run-sim-${Date.now().toString().slice(-6)}`,
          started_at: new Date().toISOString(),
          completed_at: new Date(Date.now() + 3200).toISOString(),
          parameters: currentParameters,
        };
        setRuns((prev) => [syntheticRun, ...prev]);
        setLastCompletedRun(syntheticRun);
        setIsSubmitting(false);
      }, 800);
      return;
    }

    try {
      const summary = await apiClient.createProcessingRun({
        modis_dataset_id: selectedModisId,
        viirs_dataset_id: selectedViirsId,
        parameters: currentParameters,
      });
      setRuns((prev) => [summary, ...prev]);
      setLastCompletedRun(summary);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err);
      } else {
        setError(
          new ApiError(
            0,
            '/runs',
            'Processing run execution failed',
            'Inspect backend logs and confirm input datasets are valid.',
            err
          )
        );
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleLoadRunParameters = (run: ProcessingRunSummary) => {
    setMaxDistanceMeters(run.parameters.max_distance_meters);
    setMaxTimeDifferenceSeconds(run.parameters.max_time_difference_seconds);
    setTimeWindowRule(run.parameters.time_window_rule);
    setAmbiguityPolicy(run.parameters.ambiguity_policy);
    setQualityFilters(run.parameters.quality_filters);
    if (run.parameters.score_weights) {
      setScoreWeights(run.parameters.score_weights);
    }
    if (run.input_dataset_ids.modis_dataset_id) {
      setSelectedModisId(run.input_dataset_ids.modis_dataset_id);
    }
    if (run.input_dataset_ids.viirs_dataset_id) {
      setSelectedViirsId(run.input_dataset_ids.viirs_dataset_id);
    }
  };

  const handleRerun = async (run: ProcessingRunSummary) => {
    handleLoadRunParameters(run);
    setIsSubmitting(true);
    setError(null);

    if (isFixtureMode) {
      setTimeout(() => {
        const newRun: ProcessingRunSummary = {
          ...run,
          run_id: `run-rerun-${Date.now().toString().slice(-6)}`,
          started_at: new Date().toISOString(),
          completed_at: new Date(Date.now() + 2900).toISOString(),
        };
        setRuns((prev) => [newRun, ...prev]);
        setLastCompletedRun(newRun);
        setIsSubmitting(false);
      }, 700);
      return;
    }

    try {
      const summary = await apiClient.createProcessingRun({
        modis_dataset_id: run.input_dataset_ids.modis_dataset_id || selectedModisId,
        viirs_dataset_id: run.input_dataset_ids.viirs_dataset_id || selectedViirsId,
        parameters: run.parameters,
      });
      setRuns((prev) => [summary, ...prev]);
      setLastCompletedRun(summary);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err);
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const selectedModis = datasets.find((d) => d.id === selectedModisId);
  const selectedViirs = datasets.find((d) => d.id === selectedViirsId);

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Workspace Header */}
      <div className="border-b border-slate-800 pb-4 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-slate-100 flex items-center gap-2">
            <Sliders className="w-5 h-5 text-cyan-400" />
            Harmonisation Processing Workspace
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Configure spatial-temporal matching thresholds, sensor quality filters, and candidate ambiguity policies (FR-09 to FR-14).
          </p>
        </div>

        <div className="flex items-center gap-2">
          {!isFixtureMode && (
            <button
              onClick={fetchWorkspaceData}
              disabled={loading}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-mono text-slate-300 bg-slate-900 hover:bg-slate-800 border border-slate-700 rounded transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
              Refresh Runs
            </button>
          )}
        </div>
      </div>

      {/* Error Alert (Rule 5: No silent fallback) */}
      {!isFixtureMode && error && (
        <ErrorAlert
          title="Harmonisation Pipeline Failure"
          error={error}
          onRetry={fetchWorkspaceData}
        />
      )}

      {/* Loading state */}
      {loading && !isFixtureMode && (
        <LoadingState
          message="Querying registered datasets and execution history..."
          subtext="Checking available MODIS and VIIRS granules."
        />
      )}

      {/* Success Notification after run completion */}
      {lastCompletedRun && (
        <div className="rounded-lg border border-emerald-700 bg-emerald-950/40 p-4 text-emerald-200 text-xs font-mono flex items-center justify-between shadow-sm">
          <div className="flex items-center gap-2.5">
            <CheckCircle2 className="w-5 h-5 text-emerald-400 flex-shrink-0" />
            <div>
              <span className="font-bold text-slate-100 text-[13px]">
                Harmonisation Run Succeeded: {lastCompletedRun.run_id}
              </span>
              <p className="text-emerald-300/90 text-[11px] mt-0.5">
                Produced {lastCompletedRun.counts.matched_count} matched pairs, {lastCompletedRun.counts.unmatched_modis_count} unmatched MODIS, {lastCompletedRun.counts.unmatched_viirs_count} unmatched VIIRS, and {lastCompletedRun.counts.ambiguous_count} ambiguous clusters.
              </p>
            </div>
          </div>

          <a
            href={`/map?run_id=${lastCompletedRun.run_id}`}
            className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-slate-950 font-bold rounded text-xs transition-colors shadow-sm ml-4 flex-shrink-0"
          >
            Inspect on Map &rarr;
          </a>
        </div>
      )}

      {/* Step 1: Dataset Pair Selector */}
      <DatasetPairSelector
        datasets={datasets}
        selectedModisId={selectedModisId}
        selectedViirsId={selectedViirsId}
        onSelectModis={setSelectedModisId}
        onSelectViirs={setSelectedViirsId}
      />

      {/* Step 2: Threshold and Quality Filter Controls */}
      <ThresholdAndFilterControls
        maxDistanceMeters={maxDistanceMeters}
        maxTimeDifferenceSeconds={maxTimeDifferenceSeconds}
        timeWindowRule={timeWindowRule}
        qualityFilters={qualityFilters}
        onChangeMaxDistance={setMaxDistanceMeters}
        onChangeMaxTime={setMaxTimeDifferenceSeconds}
        onChangeTimeWindowRule={setTimeWindowRule}
        onChangeQualityFilters={setQualityFilters}
      />

      {/* Step 3: Ambiguity Policy Selector */}
      <AmbiguityPolicySelector
        policy={ambiguityPolicy}
        scoreWeights={scoreWeights}
        onSelectPolicy={setAmbiguityPolicy}
        onChangeWeights={setScoreWeights}
      />

      {/* Step 4: Pre-Run Configuration Summary & Launch */}
      <PreRunConfigurationSummary
        modisDatasetId={selectedModisId}
        viirsDatasetId={selectedViirsId}
        modisProductVersion={selectedModis?.product_version}
        viirsProductVersion={selectedViirs?.product_version}
        parameters={currentParameters}
        isSubmitting={isSubmitting}
        onLaunchRun={handleLaunchRun}
        isValid={isValid}
        validationError={validationError}
      />

      {/* Step 5: Reproducible Run History & Re-run Table (FR-14) */}
      <RunHistoryAndRerunTable
        runs={runs}
        onLoadRunParameters={handleLoadRunParameters}
        onRerun={handleRerun}
        isRerunning={isSubmitting}
      />
    </div>
  );
}
