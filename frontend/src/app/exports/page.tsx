'use client';

import React, { useEffect, useState } from 'react';
import { Download, AlertCircle, RefreshCw } from 'lucide-react';
import { useFixtureMode } from '@/lib/fixtures/FixtureContext';
import {
  FIXTURE_RUN_SUMMARY,
  FIXTURE_HARMONISED_RECORDS,
} from '@/lib/fixtures/labelledTestFixtures';
import { apiClient } from '@/lib/api/client';
import { ExportDownloadCards } from '@/components/exports/ExportDownloadCards';
import { PrintableRunReportSummary } from '@/components/exports/PrintableRunReportSummary';
import { ProcessingRunSummary, HarmonisedRecord } from '@/types/harmonisation';

export default function ReportsExportsPage() {
  const { isFixtureMode } = useFixtureMode();
  const [runSummary, setRunSummary] = useState<ProcessingRunSummary | null>(null);
  const [records, setRecords] = useState<HarmonisedRecord[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    async function loadData() {
      if (isFixtureMode) {
        setRunSummary(FIXTURE_RUN_SUMMARY);
        setRecords(FIXTURE_HARMONISED_RECORDS);
        setError(null);
        return;
      }

      setLoading(true);
      setError(null);
      try {
        const runs = await apiClient.listProcessingRuns();
        if (runs && runs.length > 0 && isMounted) {
          const latestRun = runs[0];
          setRunSummary(latestRun);
          const matches = await apiClient.getRunMatches(latestRun.run_id);
          const unmatched = await apiClient.getRunUnmatched(latestRun.run_id);
          if (isMounted) setRecords([...matches, ...unmatched]);
        } else if (isMounted) {
          setRunSummary(null);
          setRecords([]);
        }
      } catch (err: any) {
        if (isMounted) {
          setError(err.message || 'Failed to connect to export endpoint');
          setRunSummary(null);
          setRecords([]);
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
      {/* Header */}
      <div className="border-b border-slate-800 pb-4">
        <h2 className="text-xl font-bold tracking-tight text-slate-100 flex items-center gap-2">
          <Download className="w-5 h-5 text-cyan-400" />
          Reproducible Reports &amp; Data Exports
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Export harmonised active fire records in GIS-ready GeoJSON, normalized CSV, or print-ready scientific summaries.
        </p>
      </div>

      {loading && (
        <div className="p-12 text-center text-slate-400 font-mono text-xs flex items-center justify-center gap-2">
          <RefreshCw className="w-4 h-4 animate-spin text-cyan-400" />
          <span>Fetching export datasets and run metadata...</span>
        </div>
      )}

      {error && !isFixtureMode && (
        <div className="p-4 rounded-lg bg-red-950/20 border border-red-800/60 text-xs text-red-300 flex items-start gap-3">
          <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
          <div>
            <div className="font-semibold text-red-200">Export Generation Error</div>
            <div className="text-[11px] text-red-300/90 mt-0.5 font-mono">{error}</div>
            <div className="text-[11px] text-slate-400 mt-2">
              Note: Connect the FastAPI backend or toggle &ldquo;Fixture Mode&rdquo; in the top banner to inspect export generators.
            </div>
          </div>
        </div>
      )}

      {!loading && !error && !runSummary && !isFixtureMode && (
        <div className="p-12 rounded-lg bg-slate-900 border border-slate-800 text-center space-y-3">
          <Download className="w-8 h-8 text-slate-600 mx-auto" />
          <h3 className="text-sm font-semibold text-slate-300 font-mono">No Active Run to Export</h3>
          <p className="text-xs text-slate-500 max-w-md mx-auto">
            Execute a harmonisation run in the Workspace (/workspace) to produce reproducible CSV, GeoJSON, and scientific report exports.
          </p>
        </div>
      )}

      {/* Main Export Modules */}
      {runSummary && (
        <div className="space-y-8">
          {/* Section 1: Data Downloads */}
          <section className="space-y-3">
            <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider font-mono">
              1. Scientific Data Downloads (CSV, GeoJSON, Reproducibility JSON)
            </h3>
            <ExportDownloadCards
              runSummary={runSummary}
              records={records}
              isFiltered={false}
            />
          </section>

          {/* Section 2: Printable Technical Report */}
          <section className="space-y-3">
            <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider font-mono">
              2. Printable Processing Report Summary
            </h3>
            <PrintableRunReportSummary runSummary={runSummary} />
          </section>
        </div>
      )}
    </div>
  );
}
