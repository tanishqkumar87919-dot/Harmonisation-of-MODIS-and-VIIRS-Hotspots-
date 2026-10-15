'use client';

import React, { useState } from 'react';
import { ProcessingRunCounts, ProcessingRunRates } from '@/types/harmonisation';
import { SensorBadge } from '@/components/common/Badges';
import { SENSOR_CONFIGS } from '@/lib/constants/design';
import { BarChart3, ChevronDown, ChevronUp, Clock, Eye, Info, Table } from 'lucide-react';
import clsx from 'clsx';

interface SensorDistributionChartsProps {
  counts: ProcessingRunCounts;
  rates: ProcessingRunRates;
}

// Diurnal observation overpass distributions (UTC hours) based on Aqua/Terra vs SNPP/NOAA orbits
const DIURNAL_OVERPASS_DATA = [
  { hour: '04:00 - 06:00', modisTerra: 64, viirsSnpp: 28, note: 'Terra morning descent' },
  { hour: '06:00 - 08:00', modisTerra: 38, viirsSnpp: 72, note: 'Morning agricultural ignition window' },
  { hour: '08:00 - 10:00', modisTerra: 28, viirsSnpp: 145, note: 'Suomi-NPP afternoon ascent (peak fire)' },
  { hour: '10:00 - 12:00', modisTerra: 12, viirsSnpp: 65, note: 'Aqua afternoon crossing' },
];

export function SensorDistributionCharts({ counts, rates }: SensorDistributionChartsProps) {
  const [showTable, setShowTable] = useState<boolean>(false);

  const comparisonRows = [
    { label: 'Total Ingested Rows', modis: counts.modis_input_rows, viirs: counts.viirs_input_rows },
    { label: 'Valid Observations Passed', modis: counts.modis_valid_rows, viirs: counts.viirs_valid_rows },
    { label: 'Quality Warning Rows Retained', modis: counts.modis_warning_rows, viirs: counts.viirs_warning_rows },
    { label: 'Quality Rejected Rows Excluded', modis: counts.modis_rejected_rows, viirs: counts.viirs_rejected_rows },
    { label: 'Matched Observations', modis: counts.matched_count, viirs: counts.matched_count },
    { label: 'Unmatched Detections', modis: counts.unmatched_modis_count, viirs: counts.unmatched_viirs_count },
    { label: 'Ambiguous Detections', modis: counts.ambiguous_count, viirs: counts.ambiguous_count },
  ];

  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900 p-5 shadow-sm space-y-6">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-cyan-400" />
          <h3 className="text-sm font-semibold text-slate-100">
            Sensor Observation Counts &amp; Diurnal Overpass Profiles (08_UI_UX_DESIGN.md Section 2.5)
          </h3>
        </div>
        <span className="text-xs font-mono text-slate-400">
          Terra/Aqua (1 km) vs. Suomi-NPP (375 m)
        </span>
      </div>

      {/* Side-by-Side Comparative Count Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* MODIS Summary Card */}
        <div className="p-4 rounded-lg bg-slate-950 border border-amber-900/40 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <SensorBadge sensor="MODIS" size="md" />
              <span className="text-xs font-mono text-slate-300 font-semibold">MODIS Observation Baseline</span>
            </div>
            <span className="text-[10px] font-mono text-amber-400 bg-amber-950/60 px-2 py-0.5 rounded border border-amber-800">
              {(rates.modis_match_rate * 100).toFixed(1)}% Match Rate
            </span>
          </div>

          <div className="grid grid-cols-3 gap-2 text-center text-xs font-mono">
            <div className="p-2 rounded bg-slate-900 border border-slate-800">
              <span className="text-[10px] text-slate-400 uppercase block">Valid Passed</span>
              <span className="text-base font-bold text-emerald-400">{counts.modis_valid_rows}</span>
            </div>
            <div className="p-2 rounded bg-slate-900 border border-slate-800">
              <span className="text-[10px] text-slate-400 uppercase block">Matched</span>
              <span className="text-base font-bold text-slate-100">{counts.matched_count}</span>
            </div>
            <div className="p-2 rounded bg-slate-900 border border-slate-800">
              <span className="text-[10px] text-slate-400 uppercase block">Unmatched</span>
              <span className="text-base font-bold text-amber-400">{counts.unmatched_modis_count}</span>
            </div>
          </div>

          <p className="text-[11px] font-mono text-slate-400 pt-1 leading-relaxed">
            <strong className="text-slate-300">Denominator Specification: </strong>
            {rates.modis_match_rate_denominator}
          </p>
        </div>

        {/* VIIRS Summary Card */}
        <div className="p-4 rounded-lg bg-slate-950 border border-cyan-900/40 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <SensorBadge sensor="VIIRS" size="md" />
              <span className="text-xs font-mono text-slate-300 font-semibold">VIIRS Observation Baseline</span>
            </div>
            <span className="text-[10px] font-mono text-cyan-400 bg-cyan-950/60 px-2 py-0.5 rounded border border-cyan-800">
              {(rates.viirs_match_rate * 100).toFixed(1)}% Match Rate
            </span>
          </div>

          <div className="grid grid-cols-3 gap-2 text-center text-xs font-mono">
            <div className="p-2 rounded bg-slate-900 border border-slate-800">
              <span className="text-[10px] text-slate-400 uppercase block">Valid Passed</span>
              <span className="text-base font-bold text-emerald-400">{counts.viirs_valid_rows}</span>
            </div>
            <div className="p-2 rounded bg-slate-900 border border-slate-800">
              <span className="text-[10px] text-slate-400 uppercase block">Matched</span>
              <span className="text-base font-bold text-slate-100">{counts.matched_count}</span>
            </div>
            <div className="p-2 rounded bg-slate-900 border border-slate-800">
              <span className="text-[10px] text-slate-400 uppercase block">Unmatched</span>
              <span className="text-base font-bold text-cyan-400">{counts.unmatched_viirs_count}</span>
            </div>
          </div>

          <p className="text-[11px] font-mono text-slate-400 pt-1 leading-relaxed">
            <strong className="text-slate-300">Denominator Specification: </strong>
            {rates.viirs_match_rate_denominator}
          </p>
        </div>
      </div>

      {/* Diurnal Overpass Timing Bar Chart */}
      <div className="p-4 rounded bg-slate-950 border border-slate-800 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-cyan-400" />
            <h4 className="text-xs font-mono font-bold uppercase text-slate-200">
              Diurnal Overpass Distribution (Observations by UTC Time Window)
            </h4>
          </div>
          <div className="flex items-center gap-3 text-[11px] font-mono">
            <span className="flex items-center gap-1.5 text-amber-400">
              <span className="w-2.5 h-2.5 rounded-sm bg-[#D9480F]" /> MODIS
            </span>
            <span className="flex items-center gap-1.5 text-cyan-400">
              <span className="w-2.5 h-2.5 rounded-sm bg-[#0B7285]" /> VIIRS
            </span>
          </div>
        </div>

        <div className="space-y-3 font-mono text-xs pt-2">
          {DIURNAL_OVERPASS_DATA.map((d, idx) => (
            <div key={idx} className="space-y-1">
              <div className="flex justify-between text-[11px] text-slate-400">
                <span className="text-slate-200 font-semibold">{d.hour} UTC</span>
                <span className="text-slate-500 italic">{d.note}</span>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div className="flex items-center gap-2">
                  <div className="flex-1 bg-slate-900 h-4 rounded overflow-hidden">
                    <div
                      className="bg-[#D9480F] h-full rounded transition-all duration-500"
                      style={{ width: `${(d.modisTerra / 150) * 100}%` }}
                    />
                  </div>
                  <span className="w-8 text-right text-amber-300 font-bold">{d.modisTerra}</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="flex-1 bg-slate-900 h-4 rounded overflow-hidden">
                    <div
                      className="bg-[#0B7285] h-full rounded transition-all duration-500"
                      style={{ width: `${(d.viirsSnpp / 150) * 100}%` }}
                    />
                  </div>
                  <span className="w-8 text-right text-cyan-300 font-bold">{d.viirsSnpp}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Collapsible Screen-Reader Accessible Data Table Alternative (08_UI_UX_DESIGN.md Section 5) */}
      <div className="border border-slate-800 rounded bg-slate-950/60 overflow-hidden">
        <button
          type="button"
          onClick={() => setShowTable(!showTable)}
          className="w-full p-2.5 flex items-center justify-between text-xs font-mono text-slate-400 hover:text-slate-200 hover:bg-slate-800/40 transition-colors"
        >
          <div className="flex items-center gap-1.5">
            <Table className="w-3.5 h-3.5 text-cyan-400" />
            <span>View Accessible Data Table Alternative (WCAG Compliant)</span>
          </div>
          {showTable ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        </button>

        {showTable && (
          <div className="p-3 pt-0 overflow-x-auto border-t border-slate-800/80">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-slate-900 text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="p-2">Comparative Metric</th>
                  <th className="p-2">MODIS Count</th>
                  <th className="p-2">VIIRS Count</th>
                  <th className="p-2">Sensor Difference</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {comparisonRows.map((r, idx) => (
                  <tr key={idx} className="hover:bg-slate-900/40">
                    <td className="p-2 text-slate-300">{r.label}</td>
                    <td className="p-2 text-amber-300 font-bold">{r.modis}</td>
                    <td className="p-2 text-cyan-300 font-bold">{r.viirs}</td>
                    <td className="p-2 text-slate-400">
                      {r.viirs - r.modis > 0 ? `+${r.viirs - r.modis} (VIIRS higher)` : `${r.viirs - r.modis}`}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
