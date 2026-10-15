'use client';

import React from 'react';
import { ProcessingRunSummary } from '@/types/harmonisation';
import { MatchStatusBadge } from '@/components/common/Badges';
import {
  CheckCircle2,
  Clock,
  History,
  Map as MapIcon,
  RotateCcw,
  Sliders,
  XCircle,
} from 'lucide-react';
import clsx from 'clsx';

interface RunHistoryAndRerunTableProps {
  runs: ProcessingRunSummary[];
  onLoadRunParameters: (run: ProcessingRunSummary) => void;
  onRerun: (run: ProcessingRunSummary) => void;
  isRerunning?: boolean;
}

export function RunHistoryAndRerunTable({
  runs,
  onLoadRunParameters,
  onRerun,
  isRerunning = false,
}: RunHistoryAndRerunTableProps) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900 p-5 shadow-sm space-y-4">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <History className="w-5 h-5 text-cyan-400" />
          <h3 className="text-sm font-semibold text-slate-100">
            Reproducible Processing Run History &amp; Re-run (FR-14)
          </h3>
        </div>
        <span className="text-xs font-mono text-slate-400">
          Traceable Parameter Reproducibility
        </span>
      </div>

      {runs.length === 0 ? (
        <p className="text-xs font-mono text-slate-400 py-6 text-center">
          No previous runs recorded in database. Configure parameters above to initiate a run.
        </p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-slate-950 text-slate-400 border-b border-slate-800">
              <tr>
                <th className="p-3">Run Identifier</th>
                <th className="p-3">Status &amp; Timestamp</th>
                <th className="p-3">Thresholds (&Delta;d / &Delta;t)</th>
                <th className="p-3">Policy &amp; Version</th>
                <th className="p-3">Outcome Counts</th>
                <th className="p-3 text-right">Reproducibility Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {runs.map((run) => {
                const isSucceeded = run.status === 'succeeded';
                return (
                  <tr key={run.run_id} className="hover:bg-slate-800/30">
                    <td className="p-3 font-semibold text-slate-200">
                      <div className="flex items-center gap-1.5">
                        <span className="text-cyan-400">{run.run_id}</span>
                        {run.is_test_fixture && (
                          <span className="text-[9px] uppercase px-1 py-0.2 rounded bg-amber-950 text-amber-300 border border-amber-800">
                            Fixture
                          </span>
                        )}
                      </div>
                      <span className="text-[10px] text-slate-500 font-normal block">
                        MODIS: {run.input_dataset_ids.modis_dataset_id?.slice(0, 14)}...
                      </span>
                    </td>

                    <td className="p-3">
                      <div className="flex items-center gap-1.5 mb-1">
                        {isSucceeded ? (
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                        ) : (
                          <XCircle className="w-3.5 h-3.5 text-red-400" />
                        )}
                        <span
                          className={clsx(
                            'font-semibold uppercase text-[10px]',
                            isSucceeded ? 'text-emerald-400' : 'text-red-400'
                          )}
                        >
                          {run.status}
                        </span>
                      </div>
                      <span className="text-slate-400 text-[10px]">
                        {new Date(run.started_at).toLocaleString()}
                      </span>
                    </td>

                    <td className="p-3">
                      <div className="text-slate-200 font-semibold">
                        {run.parameters.max_distance_meters} m
                      </div>
                      <span className="text-slate-400 text-[10px]">
                        &Delta;t: {run.parameters.max_time_difference_seconds / 60} mins ({run.parameters.time_window_rule})
                      </span>
                    </td>

                    <td className="p-3">
                      <div className="text-purple-300 font-medium capitalize text-[11px]">
                        {run.parameters.ambiguity_policy}
                      </div>
                      <span className="text-slate-500 text-[10px]">v{run.method_version}</span>
                    </td>

                    <td className="p-3">
                      <div className="flex flex-wrap items-center gap-1.5 text-[10px]">
                        <span className="text-emerald-400 font-bold">
                          {run.counts.matched_count} matched
                        </span>
                        <span className="text-slate-600">&bull;</span>
                        <span className="text-amber-400">
                          {run.counts.unmatched_modis_count} un-M
                        </span>
                        <span className="text-slate-600">&bull;</span>
                        <span className="text-cyan-400">
                          {run.counts.unmatched_viirs_count} un-V
                        </span>
                        <span className="text-slate-600">&bull;</span>
                        <span className="text-purple-400">
                          {run.counts.ambiguous_count} amb
                        </span>
                      </div>
                    </td>

                    <td className="p-3 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        <button
                          type="button"
                          onClick={() => onLoadRunParameters(run)}
                          className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 text-[11px] transition-colors"
                          title="Load thresholds and policy into current form"
                        >
                          <Sliders className="w-3 h-3 text-cyan-400" />
                          Load
                        </button>

                        <a
                          href={`/map?run_id=${run.run_id}`}
                          className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 text-[11px] transition-colors"
                          title="Inspect run on geospatial map"
                        >
                          <MapIcon className="w-3 h-3 text-emerald-400" />
                          Map
                        </a>

                        <button
                          type="button"
                          disabled={isRerunning}
                          onClick={() => onRerun(run)}
                          className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-cyan-600/30 hover:bg-cyan-600/50 text-cyan-200 border border-cyan-700 text-[11px] transition-colors disabled:opacity-50 font-semibold"
                          title="Execute deterministic rerun with identical parameters (FR-14)"
                        >
                          <RotateCcw className="w-3 h-3 text-cyan-400" />
                          Rerun
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
