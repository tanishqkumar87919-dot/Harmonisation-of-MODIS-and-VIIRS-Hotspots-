'use client';

import React, { useState } from 'react';
import { Sliders, AlertTriangle, ShieldCheck, HelpCircle, ArrowUpRight, BarChart3 } from 'lucide-react';
import { SensitivityGridPoint } from '@/types/harmonisation';

interface ThresholdSensitivityMatrixProps {
  sensitivityGrid: SensitivityGridPoint[];
}

export function ThresholdSensitivityMatrix({
  sensitivityGrid,
}: ThresholdSensitivityMatrixProps) {
  const [selectedIdx, setSelectedIdx] = useState<number>(2); // Default to 1500m / 3600s
  const [showGroundTruthDisclaimer, setShowGroundTruthDisclaimer] = useState<boolean>(false);

  const selectedPoint = sensitivityGrid[selectedIdx] || sensitivityGrid[0];

  return (
    <div className="space-y-4">
      {/* Header and Ground Truth Warning Guardrail */}
      <div className="p-4 rounded-lg bg-slate-900 border border-slate-800 space-y-3">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-2">
            <Sliders className="w-5 h-5 text-cyan-400 flex-shrink-0" />
            <div>
              <h3 className="text-sm font-semibold text-slate-100">
                Spatial &amp; Temporal Threshold Sensitivity Matrix
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Evaluates how candidate matching rates and ambiguity shift under varying spatiotemporal tolerances (&Delta;d, &Delta;t).
              </p>
            </div>
          </div>

          <button
            onClick={() => setShowGroundTruthDisclaimer(!showGroundTruthDisclaimer)}
            className="flex items-center gap-1.5 text-xs font-mono text-cyan-400 hover:text-cyan-300 px-2.5 py-1 rounded bg-slate-800 border border-slate-700 transition-colors"
          >
            <HelpCircle className="w-3.5 h-3.5" />
            <span>Why No F1 / Precision Scores?</span>
          </button>
        </div>

        {/* Scientific Integrity Guardrail Banner */}
        <div className="p-3 rounded bg-amber-950/20 border border-amber-800/60 text-xs text-amber-200 flex items-start gap-2.5">
          <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
          <div className="space-y-1">
            <div className="font-semibold text-amber-300">
              Scientific Guardrail: No Fabricated Ground Truth (docs/10_TESTING_VALIDATION_DEPLOYMENT.md &sect;3)
            </div>
            <p className="text-[11px] text-amber-200/90 leading-relaxed font-sans">
              Without independent, high-resolution airborne or ground-validated reference labels, calculating precision, recall, or F1-scores
              is scientifically ungrounded. Neither MODIS nor VIIRS constitutes absolute ground truth. Thresholds must be chosen based on
              instrument viewing geometry and orbital dynamics, <em>not solely because they maximize match counts</em>.
            </p>
          </div>
        </div>

        {showGroundTruthDisclaimer && (
          <div className="p-3 rounded bg-slate-950 border border-slate-800 text-xs text-slate-300 font-mono space-y-1.5">
            <div className="text-cyan-400 font-bold">Scientific Validation Protocol Note:</div>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              In satellite remote sensing, coincident observations occur with varying viewing zenith angles and footprint distortions (1 km MODIS vs 375 m VIIRS).
              Relaxing spatial threshold from 1,000 m to 2,500 m inflates apparent match count (+40%), but drastically increases candidate ambiguity (from 4 to 18 cases)
              and risks false spatial association across distinct spot fires.
            </p>
          </div>
        )}
      </div>

      {/* Interactive Sensitivity Grid Table */}
      <div className="rounded-lg bg-slate-900 border border-slate-800 overflow-hidden">
        <div className="p-3 bg-slate-950 border-b border-slate-800 flex items-center justify-between">
          <span className="text-xs font-semibold text-slate-200 font-mono">
            Sensitivity Experiments (Click row to inspect trade-offs)
          </span>
          <span className="text-[11px] text-slate-500 font-mono">
            Spatial: 500m &ndash; 2500m | Temporal: 30m &ndash; 120m
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800">
              <tr>
                <th className="p-3 font-semibold">Config Index</th>
                <th className="p-3 font-semibold">Spatial &Delta;d</th>
                <th className="p-3 font-semibold">Temporal &Delta;t</th>
                <th className="p-3 font-semibold">Matched Pairs</th>
                <th className="p-3 font-semibold">Ambiguous Cases</th>
                <th className="p-3 font-semibold">Unmatched MODIS</th>
                <th className="p-3 font-semibold">Unmatched VIIRS</th>
                <th className="p-3 font-semibold">MODIS Match Rate</th>
                <th className="p-3 font-semibold">Ambiguity Trade-off</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {sensitivityGrid.map((pt, idx) => {
                const isSelected = idx === selectedIdx;
                const ambiguityPercent = (pt.ambiguous_count / (pt.matched_count + pt.ambiguous_count) * 100).toFixed(1);

                return (
                  <tr
                    key={idx}
                    onClick={() => setSelectedIdx(idx)}
                    className={`cursor-pointer transition-colors ${
                      isSelected
                        ? 'bg-cyan-950/30 border-l-4 border-l-cyan-400'
                        : 'hover:bg-slate-800/40'
                    }`}
                  >
                    <td className="p-3 font-bold text-slate-400">
                      #{idx + 1}
                    </td>
                    <td className="p-3 font-bold text-cyan-300">
                      {pt.spatial_threshold_m} m
                    </td>
                    <td className="p-3 text-slate-300">
                      {pt.temporal_threshold_s / 60} min ({pt.temporal_threshold_s}s)
                    </td>
                    <td className="p-3 text-emerald-400 font-bold">
                      {pt.matched_count}
                    </td>
                    <td className="p-3 text-purple-400 font-semibold">
                      {pt.ambiguous_count}
                    </td>
                    <td className="p-3 text-amber-400">
                      {pt.unmatched_modis_count}
                    </td>
                    <td className="p-3 text-blue-400">
                      {pt.unmatched_viirs_count}
                    </td>
                    <td className="p-3">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-slate-200">
                          {(pt.match_rate * 100).toFixed(1)}%
                        </span>
                        <div className="w-16 h-1.5 rounded-full bg-slate-800 overflow-hidden">
                          <div
                            className="h-full bg-cyan-400 rounded-full"
                            style={{ width: `${Math.min(pt.match_rate * 100, 100)}%` }}
                          />
                        </div>
                      </div>
                    </td>
                    <td className="p-3">
                      <span
                        className={`text-[11px] px-2 py-0.5 rounded font-mono ${
                          pt.ambiguous_count > 10
                            ? 'bg-purple-950 text-purple-300 border border-purple-800'
                            : 'bg-slate-800 text-slate-400'
                        }`}
                      >
                        {ambiguityPercent}% ambiguity
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Selected Configuration Trade-off Inspector */}
      {selectedPoint && (
        <div className="p-4 rounded-lg bg-slate-900 border border-slate-800 space-y-3 font-mono text-xs">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <span className="font-bold text-slate-200 flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-cyan-400" />
              Detailed Trade-off Analysis for Config #{selectedIdx + 1} (&Delta;d={selectedPoint.spatial_threshold_m}m, &Delta;t={selectedPoint.temporal_threshold_s / 60}min)
            </span>
            <span className="text-[11px] text-cyan-400">
              Match Rate: {(selectedPoint.match_rate * 100).toFixed(1)}%
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-[11px]">
            <div className="p-2.5 rounded bg-slate-950 border border-slate-800 space-y-1">
              <div className="text-slate-400">Detection Yield</div>
              <div className="text-emerald-400 font-bold text-sm">{selectedPoint.matched_count} pairs</div>
              <div className="text-slate-500 text-[10px]">Pairs within {selectedPoint.spatial_threshold_m}m and {selectedPoint.temporal_threshold_s/60}min</div>
            </div>

            <div className="p-2.5 rounded bg-slate-950 border border-slate-800 space-y-1">
              <div className="text-slate-400">Ambiguity Burden</div>
              <div className="text-purple-400 font-bold text-sm">{selectedPoint.ambiguous_count} unresolved</div>
              <div className="text-slate-500 text-[10px]">
                {selectedPoint.ambiguous_count > 10 ? 'High collision risk across spot fires' : 'Acceptable single-partner uniqueness'}
              </div>
            </div>

            <div className="p-2.5 rounded bg-slate-950 border border-slate-800 space-y-1">
              <div className="text-slate-400">Unmatched Single-Sensor</div>
              <div className="text-slate-300 font-bold text-sm">
                {selectedPoint.unmatched_modis_count} MODIS / {selectedPoint.unmatched_viirs_count} VIIRS
              </div>
              <div className="text-slate-500 text-[10px]">Retained per scientific preservation policy</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
