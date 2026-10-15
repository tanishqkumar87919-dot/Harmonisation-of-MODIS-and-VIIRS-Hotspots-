'use client';

import React, { useState } from 'react';
import { ChevronDown, ChevronUp, MapPin, Ruler, Table, Timer } from 'lucide-react';

interface BinData {
  bin: string;
  count: number;
}

interface MatchedPairDifferenceHistogramsProps {
  spatialBins: BinData[];
  temporalBins: BinData[];
  spatialStats?: {
    mean: number;
    median: number;
    iqr: number;
    min: number;
    max: number;
  };
  temporalStats?: {
    mean: number;
    median: number;
    iqr: number;
    min: number;
    max: number;
  };
}

export function MatchedPairDifferenceHistograms({
  spatialBins,
  temporalBins,
  spatialStats = { mean: 486.2, median: 420.0, iqr: 310.0, min: 24.5, max: 1488.0 },
  temporalStats = { mean: 980.0, median: 720.0, iqr: 840.0, min: 60.0, max: 3540.0 },
}: MatchedPairDifferenceHistogramsProps) {
  const [showTable, setShowTable] = useState<boolean>(false);

  const maxSpatialCount = Math.max(...spatialBins.map((b) => b.count), 1);
  const maxTemporalCount = Math.max(...temporalBins.map((b) => b.count), 1);

  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900 p-5 shadow-sm space-y-6">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <Ruler className="w-5 h-5 text-cyan-400" />
          <h3 className="text-sm font-semibold text-slate-100">
            Spatial Distance &amp; Temporal Delta Discrepancy Histograms
          </h3>
        </div>
        <span className="text-xs font-mono text-slate-400">
          Evaluated Across Matched &amp; Ambiguous Detection Pairs
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Spatial Distance Distribution */}
        <div className="p-4 rounded-lg bg-slate-950 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5 text-xs font-mono font-bold text-slate-200">
              <MapPin className="w-4 h-4 text-emerald-400" />
              <span>Geodesic Distance Distribution (&Delta;d in metres)</span>
            </div>
          </div>

          {/* Histogram Bars */}
          <div className="space-y-2 font-mono text-xs">
            {spatialBins.map((b, idx) => (
              <div key={idx} className="flex items-center justify-between gap-2">
                <span className="text-slate-400 w-24 text-[11px] truncate">{b.bin}</span>
                <div className="flex-1 bg-slate-900 h-4 rounded overflow-hidden">
                  <div
                    className="bg-emerald-500 h-full rounded transition-all duration-500"
                    style={{ width: `${(b.count / maxSpatialCount) * 100}%` }}
                  />
                </div>
                <span className="w-8 text-right font-bold text-slate-200">{b.count}</span>
              </div>
            ))}
          </div>

          {/* Descriptive Statistics Chips */}
          <div className="grid grid-cols-5 gap-1 pt-3 border-t border-slate-800/80 text-center text-[10px] font-mono">
            <div className="p-1 rounded bg-slate-900 border border-slate-800">
              <span className="text-slate-500 block">Mean</span>
              <span className="text-slate-200 font-bold">{spatialStats.mean}m</span>
            </div>
            <div className="p-1 rounded bg-slate-900 border border-slate-800">
              <span className="text-slate-500 block">Median</span>
              <span className="text-emerald-400 font-bold">{spatialStats.median}m</span>
            </div>
            <div className="p-1 rounded bg-slate-900 border border-slate-800">
              <span className="text-slate-500 block">IQR</span>
              <span className="text-slate-200 font-bold">{spatialStats.iqr}m</span>
            </div>
            <div className="p-1 rounded bg-slate-900 border border-slate-800">
              <span className="text-slate-500 block">Min</span>
              <span className="text-slate-200">{spatialStats.min}m</span>
            </div>
            <div className="p-1 rounded bg-slate-900 border border-slate-800">
              <span className="text-slate-500 block">Max</span>
              <span className="text-slate-200">{spatialStats.max}m</span>
            </div>
          </div>
        </div>

        {/* Temporal Gap Distribution */}
        <div className="p-4 rounded-lg bg-slate-950 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5 text-xs font-mono font-bold text-slate-200">
              <Timer className="w-4 h-4 text-cyan-400" />
              <span>Observation Time Delta (|&Delta;t| in minutes)</span>
            </div>
          </div>

          {/* Histogram Bars */}
          <div className="space-y-2 font-mono text-xs">
            {temporalBins.map((b, idx) => (
              <div key={idx} className="flex items-center justify-between gap-2">
                <span className="text-slate-400 w-24 text-[11px] truncate">{b.bin}</span>
                <div className="flex-1 bg-slate-900 h-4 rounded overflow-hidden">
                  <div
                    className="bg-cyan-500 h-full rounded transition-all duration-500"
                    style={{ width: `${(b.count / maxTemporalCount) * 100}%` }}
                  />
                </div>
                <span className="w-8 text-right font-bold text-slate-200">{b.count}</span>
              </div>
            ))}
          </div>

          {/* Descriptive Statistics Chips */}
          <div className="grid grid-cols-5 gap-1 pt-3 border-t border-slate-800/80 text-center text-[10px] font-mono">
            <div className="p-1 rounded bg-slate-900 border border-slate-800">
              <span className="text-slate-500 block">Mean</span>
              <span className="text-slate-200 font-bold">{Math.round(temporalStats.mean / 60)}m</span>
            </div>
            <div className="p-1 rounded bg-slate-900 border border-slate-800">
              <span className="text-slate-500 block">Median</span>
              <span className="text-cyan-400 font-bold">{Math.round(temporalStats.median / 60)}m</span>
            </div>
            <div className="p-1 rounded bg-slate-900 border border-slate-800">
              <span className="text-slate-500 block">IQR</span>
              <span className="text-slate-200 font-bold">{Math.round(temporalStats.iqr / 60)}m</span>
            </div>
            <div className="p-1 rounded bg-slate-900 border border-slate-800">
              <span className="text-slate-500 block">Min</span>
              <span className="text-slate-200">{Math.round(temporalStats.min / 60)}m</span>
            </div>
            <div className="p-1 rounded bg-slate-900 border border-slate-800">
              <span className="text-slate-500 block">Max</span>
              <span className="text-slate-200">{Math.round(temporalStats.max / 60)}m</span>
            </div>
          </div>
        </div>
      </div>

      {/* Accessible Table Alternative */}
      <div className="border border-slate-800 rounded bg-slate-950/60 overflow-hidden">
        <button
          type="button"
          onClick={() => setShowTable(!showTable)}
          className="w-full p-2.5 flex items-center justify-between text-xs font-mono text-slate-400 hover:text-slate-200 hover:bg-slate-800/40 transition-colors"
        >
          <div className="flex items-center gap-1.5">
            <Table className="w-3.5 h-3.5 text-cyan-400" />
            <span>View Accessible Discrepancy Bins Table</span>
          </div>
          {showTable ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        </button>

        {showTable && (
          <div className="p-3 pt-0 grid grid-cols-1 md:grid-cols-2 gap-4 border-t border-slate-800/80">
            <div>
              <span className="text-[11px] font-mono text-slate-400 font-bold block mb-1">Spatial Bins</span>
              <table className="w-full text-left text-xs font-mono">
                <tbody className="divide-y divide-slate-800/60">
                  {spatialBins.map((b, i) => (
                    <tr key={i}>
                      <td className="p-1.5 text-slate-300">{b.bin}</td>
                      <td className="p-1.5 text-right font-bold text-emerald-400">{b.count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div>
              <span className="text-[11px] font-mono text-slate-400 font-bold block mb-1">Temporal Bins</span>
              <table className="w-full text-left text-xs font-mono">
                <tbody className="divide-y divide-slate-800/60">
                  {temporalBins.map((b, i) => (
                    <tr key={i}>
                      <td className="p-1.5 text-slate-300">{b.bin}</td>
                      <td className="p-1.5 text-right font-bold text-cyan-400">{b.count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
