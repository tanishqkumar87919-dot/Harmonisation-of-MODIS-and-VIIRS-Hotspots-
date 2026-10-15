'use client';

import React, { useEffect, useState } from 'react';
import { useFixtureMode } from '@/lib/fixtures/FixtureContext';
import {
  FIXTURE_RUN_SUMMARY,
  FIXTURE_MODIS_DATASET,
  FIXTURE_VIIRS_DATASET,
} from '@/lib/fixtures/labelledTestFixtures';
import { apiClient, ApiError } from '@/lib/api/client';
import { DatasetRecord, ProcessingRunSummary } from '@/types/harmonisation';
import { StudyContextBanner } from '@/components/dashboard/StudyContextBanner';
import { QualityAndMatchKpiGrid } from '@/components/dashboard/QualityAndMatchKpiGrid';
import { LatestRunStatusCard } from '@/components/dashboard/LatestRunStatusCard';
import { EmptyState, ErrorAlert, LoadingState } from '@/components/common/StateViews';
import { Flame, Sliders, RefreshCw, Database } from 'lucide-react';

export default function OverviewDashboardPage() {
  const { isFixtureMode } = useFixtureMode();

  const [loading, setLoading] = useState<boolean>(!isFixtureMode);
  const [error, setError] = useState<ApiError | null>(null);
  const [runs, setRuns] = useState<ProcessingRunSummary[]>([]);
  const [datasets, setDatasets] = useState<DatasetRecord[]>([]);

  const fetchDashboardData = async () => {
    if (isFixtureMode) {
      setLoading(false);
      setError(null);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const [fetchedRuns, fetchedDatasets] = await Promise.all([
        apiClient.listProcessingRuns(),
        apiClient.listDatasets(),
      ]);
      setRuns(fetchedRuns);
      setDatasets(fetchedDatasets);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err);
      } else {
        setError(
          new ApiError(
            0,
            '/runs',
            'Failed to fetch processing dashboard telemetry',
            'Ensure the FastAPI backend is running at http://localhost:8000 or enable "Fixture Preview" to inspect UI layout.',
            err
          )
        );
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, [isFixtureMode]);

  // Select active run summary: either latest live run or fixture summary
  const activeSummary = isFixtureMode ? FIXTURE_RUN_SUMMARY : runs.length > 0 ? runs[0] : null;

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Page Header */}
      <div className="border-b border-slate-800 pb-4 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-slate-100 flex items-center gap-2">
            <Flame className="w-5 h-5 text-amber-500" />
            Active-Fire Observation Overview
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Systematic cross-sensor comparison of Terra/Aqua MODIS and Suomi-NPP/NOAA-20 VIIRS hotspots.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {!isFixtureMode && (
            <button
              onClick={fetchDashboardData}
              disabled={loading}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-mono text-slate-300 bg-slate-900 hover:bg-slate-800 border border-slate-700 rounded transition-colors disabled:opacity-50"
              title="Refresh telemetry from backend"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
          )}

          <a
            href="/workspace"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-slate-950 bg-cyan-400 hover:bg-cyan-300 rounded shadow-sm transition-colors"
          >
            <Sliders className="w-3.5 h-3.5" />
            New Processing Run
          </a>
        </div>
      </div>

      {/* Error state if backend fails and not in fixture mode (Rule 5: No silent fallback) */}
      {!isFixtureMode && error && (
        <ErrorAlert
          title="Backend Connection Failed"
          error={error}
          onRetry={fetchDashboardData}
        />
      )}

      {/* Loading State */}
      {loading && !isFixtureMode && (
        <LoadingState
          message="Retrieving processing runs and observation telemetry..."
          subtext="Connecting to PostgreSQL/PostGIS through FastAPI backend."
        />
      )}

      {/* Content Display */}
      {!loading && (
        <>
          {activeSummary ? (
            <div className="space-y-6">
              {/* Study Area & Extent Context */}
              <StudyContextBanner
                runSummary={activeSummary}
                regionName="Northern India & Indo-Gangetic Basin"
                bbox={isFixtureMode ? FIXTURE_MODIS_DATASET.bbox : undefined}
                timeRange={{
                  min: isFixtureMode ? FIXTURE_MODIS_DATASET.min_time_utc : null,
                  max: isFixtureMode ? FIXTURE_VIIRS_DATASET.max_time_utc : null,
                }}
                modisProduct={isFixtureMode ? FIXTURE_MODIS_DATASET.product_name : undefined}
                viirsProduct={isFixtureMode ? FIXTURE_VIIRS_DATASET.product_name : undefined}
              />

              {/* Data Quality & Outcome KPIs (FR-17) */}
              <QualityAndMatchKpiGrid summary={activeSummary} />

              {/* Processing Run Details & Quick Actions (FR-20) */}
              <LatestRunStatusCard summary={activeSummary} />
            </div>
          ) : (
            !error && (
              <EmptyState
                title="No Harmonisation Processing Runs Recorded"
                description="To view observation telemetry and cross-sensor match statistics, either upload datasets and execute a run in the Harmonisation Workspace, or toggle 'Fixture Preview' in the top header."
                actionText="Go to Harmonisation Workspace"
                onAction={() => {
                  window.location.href = '/workspace';
                }}
                icon={<Database className="w-6 h-6 text-cyan-400" />}
              />
            )
          )}
        </>
      )}
    </div>
  );
}
