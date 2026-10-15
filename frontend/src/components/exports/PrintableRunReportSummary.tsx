'use client';

import React from 'react';
import { Printer, ShieldAlert, FileText, CheckCircle2, Info } from 'lucide-react';
import { ProcessingRunSummary } from '@/types/harmonisation';

interface PrintableRunReportSummaryProps {
  runSummary: ProcessingRunSummary;
}

export function PrintableRunReportSummary({
  runSummary,
}: PrintableRunReportSummaryProps) {
  const handlePrint = () => {
    window.print();
  };

  const { counts, rates, parameters } = runSummary;

  return (
    <div className="space-y-4">
      {/* Header and Print Trigger */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 rounded-lg bg-slate-900 border border-slate-800">
        <div className="flex items-center gap-2.5">
          <FileText className="w-5 h-5 text-cyan-400" />
          <div>
            <h3 className="text-sm font-semibold text-slate-100">
              Printable Scientific Processing Summary Report
            </h3>
            <p className="text-xs text-slate-400 font-mono">
              Formatted for academic inclusion, project reports, or PDF archival (CSS @media print optimized).
            </p>
          </div>
        </div>

        <button
          onClick={handlePrint}
          className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-100 border border-slate-700 rounded text-xs font-mono font-semibold transition-colors flex items-center justify-center gap-2 shadow-sm"
        >
          <Printer className="w-4 h-4 text-cyan-400" />
          Print / Save PDF
        </button>
      </div>

      {/* Printable Report Document Sheet */}
      <div
        id="printable-scientific-report"
        className="p-8 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 font-sans space-y-6 print:bg-white print:text-black print:p-0 print:border-none print:shadow-none"
      >
        {/* Document Header */}
        <div className="border-b border-slate-800 print:border-neutral-300 pb-4">
          <div className="flex items-start justify-between">
            <div>
              <span className="text-[11px] font-mono uppercase tracking-wider text-cyan-400 print:text-cyan-800 font-bold">
                Technical Processing Run Report
              </span>
              <h2 className="text-xl font-bold tracking-tight text-slate-100 print:text-black mt-1">
                Harmonisation of MODIS and VIIRS Active Fire Hotspots
              </h2>
            </div>
            <div className="text-right font-mono text-[11px] text-slate-400 print:text-neutral-600">
              <div>Run ID: <strong className="text-slate-200 print:text-black">{runSummary.run_id}</strong></div>
              <div>Generated: {new Date().toISOString().replace('T', ' ').substring(0, 19)} UTC</div>
              <div>Method Version: {runSummary.method_version}</div>
            </div>
          </div>
        </div>

        {/* Section 1: Study Context & Sensor Input Metadata */}
        <div className="space-y-2">
          <h4 className="text-xs font-bold font-mono uppercase tracking-wider text-slate-300 print:text-neutral-800 border-b border-slate-800 print:border-neutral-200 pb-1">
            1. Observation Context &amp; Sensor Configuration
          </h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs font-mono">
            <div className="p-2.5 rounded bg-slate-900 print:bg-neutral-100 border border-slate-800 print:border-neutral-300">
              <div className="text-slate-500 print:text-neutral-600 text-[10px]">Study Region</div>
              <div className="font-bold text-slate-200 print:text-black mt-0.5">Northern India (Agri Fires)</div>
              <div className="text-[10px] text-slate-400 print:text-neutral-600">29.0&deg;N &ndash; 30.5&deg;N, 76.0&deg;E &ndash; 77.8&deg;E</div>
            </div>

            <div className="p-2.5 rounded bg-slate-900 print:bg-neutral-100 border border-slate-800 print:border-neutral-300">
              <div className="text-slate-500 print:text-neutral-600 text-[10px]">Temporal Coverage</div>
              <div className="font-bold text-slate-200 print:text-black mt-0.5">May 2023 Campaign</div>
              <div className="text-[10px] text-slate-400 print:text-neutral-600">2023-05-01 to 2023-05-05 UTC</div>
            </div>

            <div className="p-2.5 rounded bg-slate-900 print:bg-neutral-100 border border-slate-800 print:border-neutral-300">
              <div className="text-slate-500 print:text-neutral-600 text-[10px]">MODIS Product</div>
              <div className="font-bold text-amber-400 print:text-amber-800 mt-0.5">MOD14 / MYD14 (C6.1)</div>
              <div className="text-[10px] text-slate-400 print:text-neutral-600">Terra &amp; Aqua (1 km at nadir)</div>
            </div>

            <div className="p-2.5 rounded bg-slate-900 print:bg-neutral-100 border border-slate-800 print:border-neutral-300">
              <div className="text-slate-500 print:text-neutral-600 text-[10px]">VIIRS Product</div>
              <div className="font-bold text-cyan-400 print:text-cyan-800 mt-0.5">VNP14IMGTDL (v1.0)</div>
              <div className="text-[10px] text-slate-400 print:text-neutral-600">Suomi-NPP (375 m at nadir)</div>
            </div>
          </div>
        </div>

        {/* Section 2: Algorithm Execution Parameters */}
        <div className="space-y-2">
          <h4 className="text-xs font-bold font-mono uppercase tracking-wider text-slate-300 print:text-neutral-800 border-b border-slate-800 print:border-neutral-200 pb-1">
            2. Configured Algorithm Parameters
          </h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs font-mono">
            <div className="p-2.5 rounded bg-slate-900 print:bg-neutral-100 border border-slate-800 print:border-neutral-300">
              <span className="text-slate-500 print:text-neutral-600 text-[10px]">Max Spatial Distance (&Delta;d)</span>
              <div className="font-bold text-slate-200 print:text-black text-sm mt-0.5">{parameters.max_distance_meters} m</div>
            </div>

            <div className="p-2.5 rounded bg-slate-900 print:bg-neutral-100 border border-slate-800 print:border-neutral-300">
              <span className="text-slate-500 print:text-neutral-600 text-[10px]">Max Time Window (&Delta;t)</span>
              <div className="font-bold text-slate-200 print:text-black text-sm mt-0.5">
                {parameters.max_time_difference_seconds / 60} min ({parameters.max_time_difference_seconds}s)
              </div>
            </div>

            <div className="p-2.5 rounded bg-slate-900 print:bg-neutral-100 border border-slate-800 print:border-neutral-300">
              <span className="text-slate-500 print:text-neutral-600 text-[10px]">Ambiguity Policy</span>
              <div className="font-bold text-slate-200 print:text-black text-sm mt-0.5">{parameters.ambiguity_policy}</div>
            </div>

            <div className="p-2.5 rounded bg-slate-900 print:bg-neutral-100 border border-slate-800 print:border-neutral-300">
              <span className="text-slate-500 print:text-neutral-600 text-[10px]">Coordinate System</span>
              <div className="font-bold text-slate-200 print:text-black text-sm mt-0.5">EPSG:4326 (WGS 84)</div>
            </div>
          </div>
        </div>

        {/* Section 3: Data Quality & Harmonisation Results Table */}
        <div className="space-y-2">
          <h4 className="text-xs font-bold font-mono uppercase tracking-wider text-slate-300 print:text-neutral-800 border-b border-slate-800 print:border-neutral-200 pb-1">
            3. Data Quality &amp; Harmonisation Summary
          </h4>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono border border-slate-800 print:border-neutral-300">
              <thead className="bg-slate-900 print:bg-neutral-200 text-slate-400 print:text-neutral-800">
                <tr>
                  <th className="p-2">Metric Category</th>
                  <th className="p-2">MODIS (1 km)</th>
                  <th className="p-2">VIIRS (375 m)</th>
                  <th className="p-2">Harmonised Total / Rate</th>
                  <th className="p-2">Notes &amp; Rule Alignment</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800 print:divide-neutral-300">
                <tr>
                  <td className="p-2 font-semibold">Total Input Records</td>
                  <td className="p-2">{counts.modis_input_rows}</td>
                  <td className="p-2">{counts.viirs_input_rows}</td>
                  <td className="p-2 font-bold">{counts.modis_input_rows + counts.viirs_input_rows}</td>
                  <td className="p-2 text-slate-400 print:text-neutral-600">Raw observations ingested</td>
                </tr>
                <tr>
                  <td className="p-2 font-semibold">Valid Records (Stage A/B)</td>
                  <td className="p-2 text-emerald-400 print:text-emerald-800">{counts.modis_valid_rows}</td>
                  <td className="p-2 text-emerald-400 print:text-emerald-800">{counts.viirs_valid_rows}</td>
                  <td className="p-2 font-bold text-emerald-400 print:text-emerald-800">
                    {counts.modis_valid_rows + counts.viirs_valid_rows}
                  </td>
                  <td className="p-2 text-slate-400 print:text-neutral-600">Passed coordinate and timestamp QC</td>
                </tr>
                <tr>
                  <td className="p-2 font-semibold">Warning / Rejected Rows</td>
                  <td className="p-2">{counts.modis_warning_rows} warn / {counts.modis_rejected_rows} rej</td>
                  <td className="p-2">{counts.viirs_warning_rows} warn / {counts.viirs_rejected_rows} rej</td>
                  <td className="p-2 text-amber-400 print:text-amber-800">
                    {counts.modis_rejected_rows + counts.viirs_rejected_rows} rejected
                  </td>
                  <td className="p-2 text-slate-400 print:text-neutral-600">Missing coordinates or timestamp format</td>
                </tr>
                <tr className="bg-slate-900/40 print:bg-neutral-50 font-bold">
                  <td className="p-2 text-emerald-300 print:text-emerald-900">Matched Pairs (Stage F)</td>
                  <td className="p-2 text-emerald-300 print:text-emerald-900">{counts.matched_count}</td>
                  <td className="p-2 text-emerald-300 print:text-emerald-900">{counts.matched_count}</td>
                  <td className="p-2 text-emerald-300 print:text-emerald-900">
                    MODIS: {(rates.modis_match_rate * 100).toFixed(1)}% | VIIRS: {(rates.viirs_match_rate * 100).toFixed(1)}%
                  </td>
                  <td className="p-2 text-slate-400 print:text-neutral-600 font-normal">
                    Denominators: {rates.modis_match_rate_denominator}
                  </td>
                </tr>
                <tr>
                  <td className="p-2 font-semibold">Unmatched Observations</td>
                  <td className="p-2 text-amber-400 print:text-amber-800">{counts.unmatched_modis_count}</td>
                  <td className="p-2 text-cyan-400 print:text-cyan-800">{counts.unmatched_viirs_count}</td>
                  <td className="p-2 font-bold">{counts.unmatched_modis_count + counts.unmatched_viirs_count}</td>
                  <td className="p-2 text-slate-400 print:text-neutral-600">Preserved without deletion (Rule 7)</td>
                </tr>
                <tr>
                  <td className="p-2 font-semibold">Ambiguous Records</td>
                  <td className="p-2 text-purple-400 print:text-purple-800" colSpan={2}>
                    {counts.ambiguous_count} unresolved candidates
                  </td>
                  <td className="p-2 font-bold text-purple-400 print:text-purple-800">
                    {(rates.ambiguity_rate * 100).toFixed(1)}% ambiguity
                  </td>
                  <td className="p-2 text-slate-400 print:text-neutral-600">Multiple candidates within tolerance</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* Section 4: Mandatory Scientific Caveats (docs/03_RESEARCH_METHODOLOGY.md Section 7) */}
        <div className="p-3.5 rounded bg-slate-900 print:bg-neutral-100 border border-slate-800 print:border-neutral-300 text-xs space-y-1.5">
          <div className="font-bold text-slate-300 print:text-black flex items-center gap-1.5">
            <ShieldAlert className="w-4 h-4 text-amber-400 print:text-amber-800" />
            Mandatory Scientific Caveats &amp; Methodological Limitations
          </div>
          <ul className="list-disc list-inside text-slate-400 print:text-neutral-700 text-[11px] space-y-0.5 leading-relaxed font-mono">
            <li>A hotspot detection represents an active fire pixel; it does not directly equal an entire discrete wildfire event.</li>
            <li>MODIS (1 km) and VIIRS (375 m) FRP values are maintained strictly in original units (MW) and are never averaged.</li>
            <li>Match scores are heuristic spatial-temporal ranking metrics; they are not calibrated probabilities.</li>
            <li>Absence of detection during an overpass does not confirm absence of fire due to cloud occlusion or inter-overpass timing.</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
