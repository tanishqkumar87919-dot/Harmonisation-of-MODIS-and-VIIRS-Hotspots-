'use client';

import React, { useEffect, useState } from 'react';
import { useFixtureMode } from '@/lib/fixtures/FixtureContext';
import {
  FIXTURE_EVALUATION,
  FIXTURE_RUN_SUMMARY,
} from '@/lib/fixtures/labelledTestFixtures';
import { apiClient, ApiError } from '@/lib/api/client';
import { ProcessingRunSummary, RunDetailedEvaluation } from '@/types/harmonisation';
import { SensorDistributionCharts } from '@/components/comparison/SensorDistributionCharts';
import { MatchedPairDifferenceHistograms } from '@/components/comparison/MatchedPairDifferenceHistograms';
import { FrpComparisonPanel } from '@/components/comparison/FrpComparisonPanel';
import { EmptyState, ErrorAlert, LoadingState } from '@/components/common/StateViews';
import { BarChart3, RefreshCw } from 'lucide-react';

export default function SensorComparisonPage() {
  const { isFixtureMode } = useFixtureMode();

  const [loading, setLoading] = useState<boolean>(!isFixtureMode);
  const [error, setError] = useState<ApiError | null>(null);
  const [runSummary, setRunSummary] = useState<ProcessingRunSummary | null>(
    isFixtureMode ? FIXTURE_RUN_SUMMARY : null
  );
  const [evaluation, setEvaluation] = useState<RunDetailedEvaluation | null>(
    isFixtureMode ? FIXTURE_EVALUATION : null
  );

  const fetchComparisonData = async () => {
    if (isFixtureMode) {
      setRunSummary(FIXTURE_RUN_SUMMARY);
      setEvaluation(FIXTURE_EVALUATION);
      setLoading(false);
      setError(null);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const runs = await apiClient.listProcessingRuns();
      if (runs.length === 0) {
        setRunSummary(null);
        setEvaluation(null);
        setLoading(false);
        return;
      }

      const latestRun = runs[0];
      setRunSummary(latestRun);

      const evalData = await apiClient.getRunSummaryAndEvaluation(latestRun.run_id);
      setEvaluation(evalData);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err);
      } else {
        setError(
          new ApiError(
            0,
            '/runs/summary',
            'Failed to load comparative sensor evaluations',
            'Ensure the backend is online or enable "Fixture Preview" to inspect telemetry.',
            err
          )
        );
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchComparisonData();
  }, [isFixtureMode]);

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="border-b border-slate-800 pb-4 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-slate-100 flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-cyan-400" />
            Sensor Comparison &amp; Physical Discrepancy Analysis
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Comparative evaluation of observation counts, diurnal overpass windows, spatial/temporal offsets, and FRP measurements.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {!isFixtureMode && (
            <button
              onClick={fetchComparisonData}
              disabled={loading}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-mono text-slate-300 bg-slate-900 hover:bg-slate-800 border border-slate-700 rounded transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
              Refresh Analytics
            </button>
          )}
        </div>
      </div>

      {/* Error State */}
      {!isFixtureMode && error && (
        <ErrorAlert
          title="Comparative Telemetry Retrieval Error"
          error={error}
          onRetry={fetchComparisonData}
        />
      )}

      {/* Loading State */}
      {loading && !isFixtureMode && (
        <LoadingState
          message="Calculating sensor discrepancy distributions..."
          subtext="Aggregating spatial deltas, temporal offsets, and FRP histograms."
        />
      )}

      {/* Main Content */}
      {!loading && (
        <>
          {runSummary && evaluation ? (
            <div className="space-y-6">
              {/* Module 1: Sensor Observation Counts & Diurnal Distributions */}
              <SensorDistributionCharts
                counts={runSummary.counts}
                rates={runSummary.rates}
              />

              {/* Module 2: Spatial & Temporal Difference Histograms */}
              <MatchedPairDifferenceHistograms
                spatialBins={evaluation.spatial_distance_distribution}
                temporalBins={evaluation.time_difference_distribution}
              />

              {/* Module 3: FRP Comparative Analysis Panel (Rule 8) */}
              <FrpComparisonPanel
                modisFrpBins={evaluation.frp_distribution?.modis_frp || []}
                viirsFrpBins={evaluation.frp_distribution?.viirs_frp || []}
                disclaimer={evaluation.frp_distribution?.scientific_disclaimer || ''}
              />
            </div>
          ) : (
            !error && (
              <EmptyState
                title="No Processing Telemetry Available for Comparison"
                description="To view comparative sensor distributions, execute a processing run in the Workspace or enable 'Fixture Preview' in the top header."
                actionText="Open Harmonisation Workspace"
                onAction={() => {
                  window.location.href = '/workspace';
                }}
                icon={<BarChart3 className="w-6 h-6 text-cyan-400" />}
              />
            )
          )}
        </>
      )}
    </div>
  );
}
