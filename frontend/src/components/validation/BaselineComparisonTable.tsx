'use client';

import React from 'react';
import { GitCompare, AlertTriangle, CheckCircle2, Layers, Info } from 'lucide-react';
import { BaselineComparisonMetrics } from '@/types/harmonisation';

interface BaselineComparisonTableProps {
  baselines: BaselineComparisonMetrics[];
  totalInputObservations?: number;
}

export function BaselineComparisonTable({
  baselines,
  totalInputObservations = 452,
}: BaselineComparisonTableProps) {
  // Find naive concatenation and harmonised to compute delta
  const naive = baselines.find((b) => b.name.toLowerCase().includes('concatenation'));
  const harmonised = baselines.find((b) => b.name.toLowerCase().includes('harmonised'));
  const duplicatesPrevented = naive ? naive.duplicate_estimate : 0;

  return (
    <div className="space-y-4">
      {/* Key Insight Alert */}
      <div className="p-4 rounded-lg bg-slate-900 border border-slate-800 flex items-start gap-3">
        <div className="p-2 rounded bg-cyan-950 border border-cyan-800 text-cyan-400 mt-0.5">
          <Layers className="w-5 h-5" />
        </div>
        <div className="flex-1 space-y-1">
          <div className="flex items-center gap-2">
            <h4 className="text-sm font-semibold text-slate-100">
              Four-Baseline Scientific Comparison
            </h4>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
              docs/03_RESEARCH_METHODOLOGY.md &sect;5
            </span>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            Comparing single-sensor observations, naive concatenation, and the proposed harmonised method.
            Naive concatenation treats every detected pixel as an independent fire event, creating substantial
            false duplication during overlapping satellite overpasses.
          </p>
        </div>
      </div>

      {/* Comparison Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
        <div className="p-3.5 rounded-lg bg-slate-900 border border-slate-800">
          <div className="text-[11px] font-mono text-slate-400">Total Raw Ingested</div>
          <div className="text-xl font-bold font-mono text-slate-200 mt-1">{totalInputObservations}</div>
          <div className="text-[10px] text-slate-500 mt-1">Combined MODIS + VIIRS rows</div>
        </div>

        <div className="p-3.5 rounded-lg bg-slate-900 border border-amber-900/40 bg-amber-950/10">
          <div className="text-[11px] font-mono text-amber-400">Naive Merged Count</div>
          <div className="text-xl font-bold font-mono text-amber-300 mt-1">
            {naive?.total_records ?? 452}
          </div>
          <div className="text-[10px] text-amber-400/80 mt-1">
            Inflated by {duplicatesPrevented} double-counted fires
          </div>
        </div>

        <div className="p-3.5 rounded-lg bg-slate-900 border border-emerald-900/40 bg-emerald-950/10">
          <div className="text-[11px] font-mono text-emerald-400">Harmonised Unique Sites</div>
          <div className="text-xl font-bold font-mono text-emerald-300 mt-1">
            {harmonised?.unique_time_locations ?? 358}
          </div>
          <div className="text-[10px] text-emerald-400/80 mt-1">
            Cross-sensor deduplicated active hotspots
          </div>
        </div>

        <div className="p-3.5 rounded-lg bg-slate-900 border border-cyan-900/40 bg-cyan-950/10">
          <div className="text-[11px] font-mono text-cyan-400">Duplicates Reconciled</div>
          <div className="text-xl font-bold font-mono text-cyan-300 mt-1">
            {duplicatesPrevented}
          </div>
          <div className="text-[10px] text-cyan-400/80 mt-1">
            Pairs linked across sensors
          </div>
        </div>
      </div>

      {/* Detailed Baselines Table */}
      <div className="rounded-lg bg-slate-900 border border-slate-800 overflow-hidden">
        <div className="p-3 bg-slate-950 border-b border-slate-800 flex items-center justify-between">
          <span className="text-xs font-semibold text-slate-200 font-mono">
            Baseline Evaluation Matrix
          </span>
          <span className="text-[11px] text-slate-500 font-mono">
            Reference: docs/10_TESTING_VALIDATION_DEPLOYMENT.md &sect;3
          </span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800">
              <tr>
                <th className="p-3 font-semibold">Baseline Strategy</th>
                <th className="p-3 font-semibold">Total Records</th>
                <th className="p-3 font-semibold">Estimated Unique Sites</th>
                <th className="p-3 font-semibold">Duplication Rate</th>
                <th className="p-3 font-semibold">Scientific Assessment</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {baselines.map((baseline, idx) => {
                const isHarmonised = baseline.name.toLowerCase().includes('harmonised');
                const isNaive = baseline.name.toLowerCase().includes('concatenation');
                const dupPercent = ((baseline.duplicate_estimate / baseline.total_records) * 100).toFixed(1);

                return (
                  <tr
                    key={idx}
                    className={`hover:bg-slate-800/40 transition-colors ${
                      isHarmonised
                        ? 'bg-emerald-950/10'
                        : isNaive
                        ? 'bg-amber-950/10'
                        : ''
                    }`}
                  >
                    <td className="p-3">
                      <div className="flex items-center gap-2">
                        {isHarmonised ? (
                          <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                        ) : isNaive ? (
                          <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0" />
                        ) : (
                          <GitCompare className="w-4 h-4 text-slate-500 flex-shrink-0" />
                        )}
                        <span className={`font-bold ${isHarmonised ? 'text-emerald-300' : isNaive ? 'text-amber-300' : 'text-slate-200'}`}>
                          {baseline.name}
                        </span>
                      </div>
                    </td>
                    <td className="p-3 font-bold text-slate-200">
                      {baseline.total_records.toLocaleString()}
                    </td>
                    <td className="p-3 font-bold text-cyan-300">
                      {baseline.unique_time_locations.toLocaleString()}
                    </td>
                    <td className="p-3">
                      <span
                        className={`inline-block px-2 py-0.5 rounded text-[11px] font-semibold ${
                          isHarmonised
                            ? 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                            : isNaive
                            ? 'bg-amber-950 text-amber-300 border border-amber-800'
                            : 'bg-slate-800 text-slate-400'
                        }`}
                      >
                        {baseline.duplicate_estimate} ({dupPercent}%)
                      </span>
                    </td>
                    <td className="p-3 text-slate-400 font-sans text-xs leading-relaxed max-w-md">
                      {baseline.description}
                      {isNaive && (
                        <span className="block mt-1 text-[11px] text-amber-400/90 font-mono">
                          Warning: Severe overestimation of fire count when both sensors view same fire.
                        </span>
                      )}
                      {isHarmonised && (
                        <span className="block mt-1 text-[11px] text-emerald-400/90 font-mono">
                          Eliminates overpass duplicates while retaining unmatched single-sensor fires.
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
