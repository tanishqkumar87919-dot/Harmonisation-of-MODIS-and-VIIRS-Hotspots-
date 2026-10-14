'use client';

import React from 'react';
import { Download, FileSpreadsheet, FileCode, ShieldCheck } from 'lucide-react';
import { useFixtureMode } from '@/lib/fixtures/FixtureContext';
import { FIXTURE_RUN_SUMMARY } from '@/lib/fixtures/labelledTestFixtures';

export default function ReportsExportsPage() {
  const { isFixtureMode } = useFixtureMode();

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="border-b border-slate-800 pb-4">
        <h2 className="text-xl font-bold tracking-tight text-slate-100 flex items-center gap-2">
          <Download className="w-5 h-5 text-cyan-400" />
          Reproducible Reports &amp; Data Exports
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Export harmonised active fire datasets with complete processing metadata, algorithm parameters, and source provenance.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="p-5 rounded-lg bg-slate-900 border border-slate-800 space-y-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded bg-emerald-950 border border-emerald-800 text-emerald-400">
              <FileSpreadsheet className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-slate-200">CSV Observation Export</h3>
              <p className="text-xs text-slate-400 font-mono">Normalized tabular format with all 17 dictionary fields</p>
            </div>
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">
            Includes linked MODIS and VIIRS identifiers, spatial distances, time differences, and match statuses.
          </p>
          <button
            disabled={!isFixtureMode}
            className="w-full py-2 px-3 bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-slate-200 border border-slate-700 rounded text-xs font-mono transition-colors flex items-center justify-center gap-2"
          >
            <Download className="w-3.5 h-3.5" />
            Export Harmonised CSV
          </button>
        </div>

        <div className="p-5 rounded-lg bg-slate-900 border border-slate-800 space-y-4">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded bg-cyan-950 border border-cyan-800 text-cyan-400">
              <FileCode className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-slate-200">GeoJSON Feature Collection</h3>
              <p className="text-xs text-slate-400 font-mono">EPSG:4326 standard geospatial format for GIS</p>
            </div>
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">
            Directly compatible with QGIS, ArcGIS, and MapLibre. Features contain full provenance properties.
          </p>
          <button
            disabled={!isFixtureMode}
            className="w-full py-2 px-3 bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-slate-200 border border-slate-700 rounded text-xs font-mono transition-colors flex items-center justify-center gap-2"
          >
            <Download className="w-3.5 h-3.5" />
            Export GeoJSON (EPSG:4326)
          </button>
        </div>
      </div>

      {isFixtureMode && (
        <div className="p-4 rounded-lg bg-slate-900 border border-slate-800 font-mono text-xs space-y-2">
          <div className="flex items-center gap-2 text-emerald-400 font-semibold">
            <ShieldCheck className="w-4 h-4" />
            Reproducibility Manifest for Run: {FIXTURE_RUN_SUMMARY.run_id}
          </div>
          <pre className="p-3 rounded bg-slate-950 text-slate-300 text-[11px] overflow-x-auto">
{JSON.stringify(
  {
    run_id: FIXTURE_RUN_SUMMARY.run_id,
    method_version: FIXTURE_RUN_SUMMARY.method_version,
    parameters: FIXTURE_RUN_SUMMARY.parameters,
    counts: FIXTURE_RUN_SUMMARY.counts,
    rates: FIXTURE_RUN_SUMMARY.rates,
  },
  null,
  2
)}
          </pre>
        </div>
      )}
    </div>
  );
}
