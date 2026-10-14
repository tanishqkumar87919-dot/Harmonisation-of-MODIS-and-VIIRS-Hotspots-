'use client';

import React from 'react';
import { useFixtureMode } from '@/lib/fixtures/FixtureContext';
import { FIXTURE_DATASETS, FIXTURE_VALIDATION_REPORT } from '@/lib/fixtures/labelledTestFixtures';
import { SensorBadge } from '@/components/common/Badges';
import { EmptyState } from '@/components/common/StateViews';
import { Database, UploadCloud } from 'lucide-react';

export default function DatasetExplorerPage() {
  const { isFixtureMode } = useFixtureMode();

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="border-b border-slate-800 pb-4 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-slate-100 flex items-center gap-2">
            <Database className="w-5 h-5 text-cyan-400" />
            Dataset Explorer &amp; Quality Control
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Ingest, audit, and validate MODIS and VIIRS active-fire hotspot CSV files against the Data Dictionary.
          </p>
        </div>
      </div>

      {isFixtureMode ? (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {FIXTURE_DATASETS.map((ds) => (
              <div key={ds.id} className="p-4 rounded-lg bg-slate-900 border border-slate-800 space-y-3">
                <div className="flex items-center justify-between">
                  <SensorBadge sensor={ds.sensor} size="md" />
                  <span className="text-xs font-mono text-slate-400">ID: {ds.id}</span>
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-slate-200">{ds.product_name}</h3>
                  <p className="text-xs text-slate-400 font-mono">Version: {ds.product_version}</p>
                </div>
                <div className="grid grid-cols-3 gap-2 text-center text-xs font-mono pt-2 border-t border-slate-800">
                  <div className="bg-slate-950 p-2 rounded">
                    <div className="text-slate-400 text-[10px]">TOTAL</div>
                    <div className="font-bold text-slate-200">{ds.total_rows}</div>
                  </div>
                  <div className="bg-slate-950 p-2 rounded">
                    <div className="text-emerald-400 text-[10px]">VALID</div>
                    <div className="font-bold text-emerald-400">{ds.valid_rows}</div>
                  </div>
                  <div className="bg-slate-950 p-2 rounded">
                    <div className="text-red-400 text-[10px]">REJECTED</div>
                    <div className="font-bold text-red-400">{ds.rejected_rows}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="p-4 rounded-lg bg-slate-900 border border-slate-800">
            <h3 className="text-sm font-semibold text-slate-200 mb-3">
              Schema Mapping Preview (QC Stage B)
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead className="bg-slate-950 text-slate-400 border-b border-slate-800">
                  <tr>
                    <th className="p-2">Source Header</th>
                    <th className="p-2">Internal Field</th>
                    <th className="p-2">Sample Raw</th>
                    <th className="p-2">Normalized UTC/Range</th>
                    <th className="p-2">Units &amp; Notes</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {FIXTURE_VALIDATION_REPORT.schema_mapping_preview.map((row, idx) => (
                    <tr key={idx} className="hover:bg-slate-800/40">
                      <td className="p-2 text-slate-300">{row.source_column}</td>
                      <td className="p-2 text-cyan-400 font-semibold">{row.internal_field}</td>
                      <td className="p-2 text-amber-300">{row.sample_raw_value}</td>
                      <td className="p-2 text-emerald-300">{row.sample_normalized_value}</td>
                      <td className="p-2 text-slate-400">{row.unit_or_note}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      ) : (
        <EmptyState
          title="No Datasets Ingested Yet"
          description="Upload MODIS or VIIRS active fire observations (e.g. from NASA FIRMS) to validate coordinates, normalize timestamps to UTC, and prepare for candidate matching."
          actionText="Upload Hotspot CSV"
          onAction={() => {}}
          icon={<UploadCloud className="w-6 h-6 text-cyan-400" />}
        />
      )}
    </div>
  );
}
