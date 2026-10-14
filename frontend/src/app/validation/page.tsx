'use client';

import React from 'react';
import { CheckSquare, GitCompare, Info } from 'lucide-react';
import { useFixtureMode } from '@/lib/fixtures/FixtureContext';
import { FIXTURE_EVALUATION } from '@/lib/fixtures/labelledTestFixtures';

export default function ValidationSensitivityPage() {
  const { isFixtureMode } = useFixtureMode();

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="border-b border-slate-800 pb-4">
        <h2 className="text-xl font-bold tracking-tight text-slate-100 flex items-center gap-2">
          <CheckSquare className="w-5 h-5 text-cyan-400" />
          Validation &amp; Sensitivity Analysis
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Rigorous benchmarking against unharmonised baselines and multi-threshold sensitivity matrices.
        </p>
      </div>

      {isFixtureMode ? (
        <div className="space-y-6">
          {/* Baseline Comparison Section */}
          <div className="p-5 rounded-lg bg-slate-900 border border-slate-800">
            <h3 className="text-sm font-semibold text-slate-200 mb-3 flex items-center gap-2">
              <GitCompare className="w-4 h-4 text-cyan-400" />
              Four-Baseline Scientific Comparison (docs/03_RESEARCH_METHODOLOGY.md)
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead className="bg-slate-950 text-slate-400 border-b border-slate-800">
                  <tr>
                    <th className="p-2.5">Baseline Approach</th>
                    <th className="p-2.5">Total Observations</th>
                    <th className="p-2.5">Unique Spatiotemporal Sites</th>
                    <th className="p-2.5">Estimated Duplication</th>
                    <th className="p-2.5">Scientific Evaluation</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {FIXTURE_EVALUATION.baselines.map((b, idx) => (
                    <tr key={idx} className="hover:bg-slate-800/40">
                      <td className="p-2.5 font-bold text-slate-200">{b.name}</td>
                      <td className="p-2.5 text-slate-300">{b.total_records}</td>
                      <td className="p-2.5 text-cyan-300">{b.unique_time_locations}</td>
                      <td className="p-2.5 text-amber-400 font-semibold">{b.duplicate_estimate}</td>
                      <td className="p-2.5 text-slate-400">{b.description}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Threshold Sensitivity Grid */}
          <div className="p-5 rounded-lg bg-slate-900 border border-slate-800">
            <h3 className="text-sm font-semibold text-slate-200 mb-3">
              Spatial &amp; Temporal Sensitivity Matrix
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead className="bg-slate-950 text-slate-400 border-b border-slate-800">
                  <tr>
                    <th className="p-2.5">Spatial Threshold (&Delta;d)</th>
                    <th className="p-2.5">Temporal Threshold (&Delta;t)</th>
                    <th className="p-2.5">Matched</th>
                    <th className="p-2.5">Ambiguous</th>
                    <th className="p-2.5">Unmatched MODIS</th>
                    <th className="p-2.5">Unmatched VIIRS</th>
                    <th className="p-2.5">MODIS Match Rate</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {FIXTURE_EVALUATION.sensitivity_grid.map((pt, idx) => (
                    <tr key={idx} className="hover:bg-slate-800/40">
                      <td className="p-2.5 text-cyan-400">{pt.spatial_threshold_m} m</td>
                      <td className="p-2.5 text-slate-300">{pt.temporal_threshold_s / 60} min</td>
                      <td className="p-2.5 text-emerald-400 font-bold">{pt.matched_count}</td>
                      <td className="p-2.5 text-purple-400">{pt.ambiguous_count}</td>
                      <td className="p-2.5 text-amber-400">{pt.unmatched_modis_count}</td>
                      <td className="p-2.5 text-blue-400">{pt.unmatched_viirs_count}</td>
                      <td className="p-2.5 text-slate-200 font-bold">{(pt.match_rate * 100).toFixed(1)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      ) : (
        <div className="p-12 text-center text-slate-500 font-mono text-xs">
          Validation metrics and sensitivity curves require a completed processing run.
        </div>
      )}
    </div>
  );
}
