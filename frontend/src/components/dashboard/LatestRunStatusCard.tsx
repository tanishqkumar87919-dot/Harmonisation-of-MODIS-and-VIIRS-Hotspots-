'use client';

import React from 'react';
import { ProcessingRunSummary } from '@/types/harmonisation';
import { PartialResultBanner } from '@/components/common/StateViews';
import {
  Activity,
  ArrowRight,
  BookOpen,
  CheckCircle2,
  Clock,
  Map as MapIcon,
  Sliders,
  SlidersHorizontal,
  XCircle,
} from 'lucide-react';
import clsx from 'clsx';

interface LatestRunStatusCardProps {
  summary: ProcessingRunSummary;
}

export function LatestRunStatusCard({ summary }: LatestRunStatusCardProps) {
  const isSucceeded = summary.status === 'succeeded';
  const isFailed = summary.status === 'failed';

  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900 p-5 shadow-sm space-y-4">
      {/* Run Header with Status Badge */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
              <Activity className="w-4 h-4 text-cyan-400" />
              Processing Run Status
            </h3>
            <span
              className={clsx(
                'inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-mono font-medium border uppercase tracking-wider',
                isSucceeded
                  ? 'bg-emerald-950/60 text-emerald-300 border-emerald-700'
                  : isFailed
                  ? 'bg-red-950/60 text-red-300 border-red-700'
                  : 'bg-amber-950/60 text-amber-300 border-amber-700'
              )}
            >
              {isSucceeded && <CheckCircle2 className="w-3 h-3 text-emerald-400" />}
              {isFailed && <XCircle className="w-3 h-3 text-red-400" />}
              {summary.status}
            </span>
          </div>
          <span className="text-xs font-mono text-slate-400 mt-1 block">
            Run ID: <span className="text-slate-200">{summary.run_id}</span> &bull; Algorithm v{summary.method_version}
          </span>
        </div>

        <div className="flex items-center gap-4 text-xs font-mono text-slate-400">
          <div className="flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5 text-slate-500" />
            <span>Started: {new Date(summary.started_at).toLocaleTimeString()}</span>
          </div>
          {summary.completed_at && (
            <div>
              <span>Completed: {new Date(summary.completed_at).toLocaleTimeString()}</span>
            </div>
          )}
        </div>
      </div>

      {/* Matching Parameters Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
        <div className="bg-slate-950 p-2.5 rounded border border-slate-800/80">
          <span className="text-[10px] text-slate-400 uppercase block mb-0.5">Spatial Threshold</span>
          <span className="font-semibold text-cyan-400">{summary.parameters.max_distance_meters} m</span>
          <span className="text-[10px] text-slate-500 block mt-0.5">&le; {summary.parameters.max_distance_meters / 1000} km radius</span>
        </div>

        <div className="bg-slate-950 p-2.5 rounded border border-slate-800/80">
          <span className="text-[10px] text-slate-400 uppercase block mb-0.5">Temporal Window</span>
          <span className="font-semibold text-cyan-400">{summary.parameters.max_time_difference_seconds} s</span>
          <span className="text-[10px] text-slate-500 block mt-0.5">&le; {summary.parameters.max_time_difference_seconds / 60} mins</span>
        </div>

        <div className="bg-slate-950 p-2.5 rounded border border-slate-800/80">
          <span className="text-[10px] text-slate-400 uppercase block mb-0.5">Time Rule</span>
          <span className="font-semibold text-slate-200 capitalize">{summary.parameters.time_window_rule}</span>
          <span className="text-[10px] text-slate-500 block mt-0.5">|&Delta;t| absolute window</span>
        </div>

        <div className="bg-slate-950 p-2.5 rounded border border-slate-800/80">
          <span className="text-[10px] text-slate-400 uppercase block mb-0.5">Ambiguity Policy</span>
          <span className="font-semibold text-purple-300 text-[11px] truncate block" title={summary.parameters.ambiguity_policy}>
            {summary.parameters.ambiguity_policy}
          </span>
          <span className="text-[10px] text-slate-500 block mt-0.5">Deterministic rank</span>
        </div>
      </div>

      {/* Warnings & Exclusions (FR-20) */}
      {summary.warnings && summary.warnings.length > 0 && (
        <PartialResultBanner warnings={summary.warnings} />
      )}

      {/* Quick Actions Navigation */}
      <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-slate-800">
        <div className="flex flex-wrap items-center gap-2">
          <a
            href="/map"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded bg-cyan-600 hover:bg-cyan-500 text-slate-950 font-semibold text-xs transition-colors shadow-sm"
          >
            <MapIcon className="w-3.5 h-3.5" />
            Inspect on Map
          </a>
          <a
            href="/workspace"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-mono transition-colors"
          >
            <Sliders className="w-3.5 h-3.5 text-cyan-400" />
            Configure New Run
          </a>
        </div>

        <a
          href="/methodology"
          className="inline-flex items-center gap-1 text-xs text-slate-400 hover:text-slate-200 font-mono"
        >
          <BookOpen className="w-3.5 h-3.5 text-slate-400" />
          Read Methodology &amp; Limitations <ArrowRight className="w-3 h-3" />
        </a>
      </div>
    </div>
  );
}
