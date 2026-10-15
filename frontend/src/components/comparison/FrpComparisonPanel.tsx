'use client';

import React, { useState } from 'react';
import { SensorBadge } from '@/components/common/Badges';
import { AlertCircle, Flame, Info, Table, TrendingUp } from 'lucide-react';

interface FrpBin {
  bin: string;
  count: number;
}

interface FrpComparisonPanelProps {
  modisFrpBins: FrpBin[];
  viirsFrpBins: FrpBin[];
  disclaimer: string;
}

// Sample paired FRP data points for matched pairs (MW)
const MATCHED_FRP_PAIRS = [
  { pairId: 'pair-01', modisFrp: 34.2, viirsFrp: 18.4, distM: 326 },
  { pairId: 'pair-02', modisFrp: 21.0, viirsFrp: 12.1, distM: 412 },
  { pairId: 'pair-03', modisFrp: 58.4, viirsFrp: 36.8, distM: 680 },
  { pairId: 'pair-04', modisFrp: 14.5, viirsFrp: 7.2, distM: 180 },
  { pairId: 'pair-05', modisFrp: 82.0, viirsFrp: 49.5, distM: 520 },
  { pairId: 'pair-06', modisFrp: 42.1, viirsFrp: 28.0, distM: 290 },
  { pairId: 'pair-07', modisFrp: 19.8, viirsFrp: 9.6, distM: 410 },
  { pairId: 'pair-08', modisFrp: 67.2, viirsFrp: 41.0, distM: 710 },
];

export function FrpComparisonPanel({
  modisFrpBins,
  viirsFrpBins,
  disclaimer,
}: FrpComparisonPanelProps) {
  const [showTable, setShowTable] = useState<boolean>(false);

  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900 p-5 shadow-sm space-y-6">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <Flame className="w-5 h-5 text-amber-500" />
          <h3 className="text-sm font-semibold text-slate-100">
            Fire Radiative Power (FRP) Comparative Analysis &amp; Sensor Physics (Stage G)
          </h3>
        </div>
        <span className="text-xs font-mono text-slate-400">
          Independent Measurement Retained in Megawatts (MW)
        </span>
      </div>

      {/* Rule 8 Mandatory Scientific Warning Banner */}
      <div
        role="alert"
        className="rounded-lg border border-amber-600/60 bg-amber-950/30 p-4 text-amber-200 text-xs font-mono space-y-1.5 leading-relaxed"
      >
        <div className="flex items-center gap-2 font-bold text-amber-300">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>Non-Averaging Scientific Constraint (Rule 8 &amp; docs/05_HARMONISATION_ALGORITHM.md Section 5)</span>
        </div>
        <p>
          Detection matching and measurement harmonisation are separate tasks. MODIS (1 km) and VIIRS (375 m) have different point spread functions, pixel footprints, and radiative saturation thresholds. FRP values are displayed in their original sensor units (MW) for comparative analysis and are <strong>never averaged by default</strong>.
        </p>
      </div>

      {/* Side-by-side FRP Intensity Distributions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* MODIS FRP Distribution */}
        <div className="p-4 rounded-lg bg-slate-950 border border-slate-800 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <SensorBadge sensor="MODIS" size="sm" />
              <span className="text-xs font-mono font-bold text-slate-200">
                MODIS FRP Intensity Distribution
              </span>
            </div>
            <span className="text-[10px] font-mono text-slate-400">Unit: MW</span>
          </div>

          <div className="space-y-2 font-mono text-xs">
            {modisFrpBins.map((b, idx) => (
              <div key={idx} className="flex items-center justify-between gap-2">
                <span className="text-slate-400 w-24 text-[11px]">{b.bin}</span>
                <div className="flex-1 bg-slate-900 h-4 rounded overflow-hidden">
                  <div
                    className="bg-[#D9480F] h-full rounded transition-all duration-500"
                    style={{ width: `${(b.count / 70) * 100}%` }}
                  />
                </div>
                <span className="w-8 text-right font-bold text-amber-300">{b.count}</span>
              </div>
            ))}
          </div>

          <p className="text-[10px] font-mono text-slate-500 pt-1">
            Aggregated over 1 km nominal pixels. Less sensitive to small agricultural burns (&lt; 10 MW).
          </p>
        </div>

        {/* VIIRS FRP Distribution */}
        <div className="p-4 rounded-lg bg-slate-950 border border-slate-800 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <SensorBadge sensor="VIIRS" size="sm" />
              <span className="text-xs font-mono font-bold text-slate-200">
                VIIRS FRP Intensity Distribution
              </span>
            </div>
            <span className="text-[10px] font-mono text-slate-400">Unit: MW</span>
          </div>

          <div className="space-y-2 font-mono text-xs">
            {viirsFrpBins.map((b, idx) => (
              <div key={idx} className="flex items-center justify-between gap-2">
                <span className="text-slate-400 w-24 text-[11px]">{b.bin}</span>
                <div className="flex-1 bg-slate-900 h-4 rounded overflow-hidden">
                  <div
                    className="bg-[#0B7285] h-full rounded transition-all duration-500"
                    style={{ width: `${(b.count / 150) * 100}%` }}
                  />
                </div>
                <span className="w-8 text-right font-bold text-cyan-300">{b.count}</span>
              </div>
            ))}
          </div>

          <p className="text-[10px] font-mono text-slate-500 pt-1">
            Retrieved at 375 m I-band resolution. Captures many lower-intensity active fires in the 0–5 MW range.
          </p>
        </div>
      </div>

      {/* Paired Scatter Plot Matrix / Table */}
      <div className="p-4 rounded-lg bg-slate-950 border border-slate-800 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs font-mono font-bold text-slate-200">
            <TrendingUp className="w-4 h-4 text-emerald-400" />
            <span>Matched Pair FRP Correlation Inspection Sample</span>
          </div>
          <span className="text-[10px] font-mono text-slate-400">
            MODIS (MW) vs. VIIRS (MW)
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-slate-900 text-slate-400 border-b border-slate-800">
              <tr>
                <th className="p-2">Pair ID</th>
                <th className="p-2">MODIS FRP (MW)</th>
                <th className="p-2">VIIRS FRP (MW)</th>
                <th className="p-2">Spatial Delta</th>
                <th className="p-2">Ratio (MODIS / VIIRS)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {MATCHED_FRP_PAIRS.map((p) => {
                const ratio = (p.modisFrp / p.viirsFrp).toFixed(2);
                return (
                  <tr key={p.pairId} className="hover:bg-slate-900/40">
                    <td className="p-2 text-slate-300 font-bold">{p.pairId}</td>
                    <td className="p-2 text-amber-300 font-semibold">{p.modisFrp} MW</td>
                    <td className="p-2 text-cyan-300 font-semibold">{p.viirsFrp} MW</td>
                    <td className="p-2 text-slate-400">{p.distM} m</td>
                    <td className="p-2 text-emerald-400 font-bold">{ratio} &times;</td>
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
