'use client';

import React, { useEffect, useState } from 'react';
import { CheckSquare, GitCompare, Sliders, RefreshCw, AlertCircle } from 'lucide-react';
import { useFixtureMode } from '@/lib/fixtures/FixtureContext';
import { FIXTURE_EVALUATION } from '@/lib/fixtures/labelledTestFixtures';
import { apiClient } from '@/lib/api/client';
import { BaselineComparisonTable } from '@/components/validation/BaselineComparisonTable';
import { ThresholdSensitivityMatrix } from '@/components/validation/ThresholdSensitivityMatrix';
import { RunDetailedEvaluation } from '@/types/harmonisation';

export default function ValidationSensitivityPage() {
  const { isFixtureMode } = useFixtureMode();
  const [evaluationData, setEvaluationData] = useState<RunDetailedEvaluation | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function loadData() {
      if (isFixtureMode) {
        setEvaluationData(FIXTURE_EVALUATION);
        setError(null);
        return;
      }

      setLoading(true);
      setError(null);
      try {
        const runs = await apiClient.listProcessingRuns();
        if (runs && runs.length > 0 && isMounted) {
          const latestRun = runs[0];
          const evaluation = await apiClient.getRunSummaryAndEvaluation(latestRun.run_id);
          if (isMounted) setEvaluationData(evaluation);
        } else if (isMounted) {
          setEvaluationData(null);
        }
      } catch (err: any) {
        if (isMounted) {
          setError(err.message || 'Failed to connect to backend evaluation endpoint');
          setEvaluationData(null);
        }
      } finally {
        if (isMounted) setLoading(false);
      }
    }

    loadData();
    return () => {
      isMounted = false;
    };
  }, [isFixtureMode]);

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Page Header */}
      <div className="border-b border-slate-800 pb-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-slate-100 flex items-center gap-2">
            <CheckSquare className="w-5 h-5 text-cyan-400" />
            Scientific Validation &amp; Sensitivity Analysis
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Empirical benchmarking across four baseline strategies and multi-threshold spatiotemporal sensitivity matrices.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {evaluationData && (
            <span className="text-[11px] font-mono px-2.5 py-1 rounded bg-slate-900 text-slate-300 border border-slate-800">
              Run: {evaluationData.run_id}
            </span>
          )}
        </div>
      </div>

      {loading && (
        <div className="p-12 text-center text-slate-400 font-mono text-xs flex items-center justify-center gap-2">
          <RefreshCw className="w-4 h-4 animate-spin text-cyan-400" />
          <span>Fetching scientific validation models from backend...</span>
        </div>
      )}

      {error && !isFixtureMode && (
        <div className="p-4 rounded-lg bg-red-950/20 border border-red-800/60 text-xs text-red-300 flex items-start gap-3">
          <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
          <div>
            <div className="font-semibold text-red-200">Scientific Validation Error</div>
            <div className="text-[11px] text-red-300/90 mt-0.5 font-mono">{error}</div>
            <div className="text-[11px] text-slate-400 mt-2">
              Note: Connect the FastAPI backend or toggle &ldquo;Fixture Mode&rdquo; in the top navigation banner to view reference validation structures.
            </div>
          </div>
        </div>
      )}

      {!loading && !error && !evaluationData && !isFixtureMode && (
        <div className="p-12 rounded-lg bg-slate-900 border border-slate-800 text-center space-y-3">
          <Sliders className="w-8 h-8 text-slate-600 mx-auto" />
          <h3 className="text-sm font-semibold text-slate-300 font-mono">No Active Validation Data</h3>
          <p className="text-xs text-slate-500 max-w-md mx-auto">
            Run a harmonisation job in the Workspace (/workspace) to generate baseline comparisons and sensitivity matrices.
          </p>
        </div>
      )}

      {/* Main Validation View */}
      {evaluationData && (
        <div className="space-y-8">
          {/* Section 1: 4-Baseline Comparison */}
          <section className="space-y-3">
            <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider font-mono flex items-center gap-2">
              <GitCompare className="w-4 h-4 text-cyan-400" />
              1. Four-Baseline Methodological Comparison
            </h3>
            <BaselineComparisonTable
              baselines={evaluationData.baselines}
              totalInputObservations={452}
            />
          </section>

          {/* Section 2: Threshold Sensitivity Matrix */}
          <section className="space-y-3">
            <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider font-mono flex items-center gap-2">
              <Sliders className="w-4 h-4 text-cyan-400" />
              2. Spatiotemporal Threshold Sensitivity Matrix
            </h3>
            <ThresholdSensitivityMatrix
              sensitivityGrid={evaluationData.sensitivity_grid}
            />
          </section>
        </div>
      )}
    </div>
  );
}
