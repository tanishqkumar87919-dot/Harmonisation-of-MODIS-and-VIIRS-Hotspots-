'use client';

import React, { useState } from 'react';
import { DatasetRecord, SchemaMappingPreviewItem } from '@/types/harmonisation';
import { SensorBadge } from '@/components/common/Badges';
import {
  AlertTriangle,
  Database,
  Eye,
  FileCode2,
  Fingerprint,
  Info,
  Trash2,
  X,
} from 'lucide-react';
import clsx from 'clsx';

// Authoritative 17-field mapping sample for MODIS and VIIRS products
const MODIS_SCHEMA_MAPPINGS: SchemaMappingPreviewItem[] = [
  { source_column: 'latitude', internal_field: 'latitude', sample_raw_value: '29.3541', sample_normalized_value: '29.3541', unit_or_note: 'Validated range [-90, 90]' },
  { source_column: 'longitude', internal_field: 'longitude', sample_raw_value: '77.1205', sample_normalized_value: '77.1205', unit_or_note: 'Validated range [-180, 180]' },
  { source_column: 'acq_date + acq_time', internal_field: 'observation_time_utc', sample_raw_value: '2023-05-01, 0530', sample_normalized_value: '2023-05-01T05:30:00Z', unit_or_note: 'Normalized UTC ISO 8601' },
  { source_column: 'confidence', internal_field: 'confidence_raw', sample_raw_value: '84', sample_normalized_value: '84', unit_or_note: 'Integer % (0-100 continuous probability heuristic)' },
  { source_column: 'frp', internal_field: 'frp_raw', sample_raw_value: '34.2', sample_normalized_value: '34.2', unit_or_note: 'Original Megawatts (MW) — never averaged by default' },
  { source_column: 'scan', internal_field: 'scan_raw', sample_raw_value: '1.1', sample_normalized_value: '1.1', unit_or_note: 'Scan pixel dimension in km' },
  { source_column: 'track', internal_field: 'track_raw', sample_raw_value: '1.0', sample_normalized_value: '1.0', unit_or_note: 'Track pixel dimension in km' },
  { source_column: 'satellite', internal_field: 'platform', sample_raw_value: 'Terra', sample_normalized_value: 'Terra', unit_or_note: 'Spacecraft platform' },
  { source_column: 'instrument', internal_field: 'source_sensor', sample_raw_value: 'MODIS', sample_normalized_value: 'MODIS', unit_or_note: 'Controlled sensor vocabulary' },
  { source_column: 'version', internal_field: 'product_version', sample_raw_value: '6.1NRT', sample_normalized_value: 'C6.1', unit_or_note: 'Collection identifier' },
  { source_column: 'brightness + bright_t31', internal_field: 'raw_fields (JSON)', sample_raw_value: '324.5, 296.2', sample_normalized_value: '{"brightness": 324.5, "bright_t31": 296.2}', unit_or_note: 'Original 4µm/11µm brightness temperatures preserved' },
];

const VIIRS_SCHEMA_MAPPINGS: SchemaMappingPreviewItem[] = [
  { source_column: 'latitude', internal_field: 'latitude', sample_raw_value: '29.3562', sample_normalized_value: '29.3562', unit_or_note: 'Validated range [-90, 90]' },
  { source_column: 'longitude', internal_field: 'longitude', sample_raw_value: '77.1228', sample_normalized_value: '77.1228', unit_or_note: 'Validated range [-180, 180]' },
  { source_column: 'acq_date + acq_time', internal_field: 'observation_time_utc', sample_raw_value: '2023-05-01, 0542', sample_normalized_value: '2023-05-01T05:42:00Z', unit_or_note: 'Normalized UTC ISO 8601' },
  { source_column: 'confidence', internal_field: 'confidence_raw', sample_raw_value: '"nominal"', sample_normalized_value: '"nominal"', unit_or_note: 'Categorical string (low / nominal / high) — distinct from MODIS %' },
  { source_column: 'frp', internal_field: 'frp_raw', sample_raw_value: '12.8', sample_normalized_value: '12.8', unit_or_note: 'Original Megawatts (MW) — 375m I-band retrieval' },
  { source_column: 'scan', internal_field: 'scan_raw', sample_raw_value: '0.4', sample_normalized_value: '0.4', unit_or_note: 'Scan pixel dimension in km' },
  { source_column: 'track', internal_field: 'track_raw', sample_raw_value: '0.38', sample_normalized_value: '0.38', unit_or_note: 'Track pixel dimension in km' },
  { source_column: 'satellite', internal_field: 'platform', sample_raw_value: 'N', sample_normalized_value: 'Suomi-NPP', unit_or_note: 'Spacecraft platform' },
  { source_column: 'instrument', internal_field: 'source_sensor', sample_raw_value: 'VIIRS', sample_normalized_value: 'VIIRS', unit_or_note: 'Controlled sensor vocabulary' },
  { source_column: 'version', internal_field: 'product_version', sample_raw_value: '1.0NRT', sample_normalized_value: 'v1.0', unit_or_note: 'Collection identifier' },
  { source_column: 'bright_ti4 + bright_ti5', internal_field: 'raw_fields (JSON)', sample_raw_value: '335.2, 298.1', sample_normalized_value: '{"bright_ti4": 335.2, "bright_ti5": 298.1}', unit_or_note: 'Original I4/I5 band brightness temperatures preserved' },
];

interface DatasetSchemaAndQualityDrawerProps {
  datasets: DatasetRecord[];
  onDeleteDataset?: (datasetId: string) => void;
}

export function DatasetSchemaAndQualityDrawer({
  datasets,
  onDeleteDataset,
}: DatasetSchemaAndQualityDrawerProps) {
  const [selectedDatasetForInspection, setSelectedDatasetForInspection] = useState<DatasetRecord | null>(null);
  const [datasetToDelete, setDatasetToDelete] = useState<DatasetRecord | null>(null);

  const mappings =
    selectedDatasetForInspection?.sensor === 'VIIRS' ? VIIRS_SCHEMA_MAPPINGS : MODIS_SCHEMA_MAPPINGS;

  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900 p-5 shadow-sm space-y-4">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <Database className="w-5 h-5 text-cyan-400" />
          <h3 className="text-sm font-semibold text-slate-100">
            Registered Datasets ({datasets.length})
          </h3>
        </div>
        <span className="text-xs font-mono text-slate-400">
          Source Provenance &amp; Checksum Registry
        </span>
      </div>

      {datasets.length === 0 ? (
        <p className="text-xs font-mono text-slate-400 py-6 text-center">
          No datasets currently registered. Upload a MODIS or VIIRS CSV dataset above.
        </p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-slate-950 text-slate-400 border-b border-slate-800">
              <tr>
                <th className="p-3">Sensor</th>
                <th className="p-3">Product &amp; Version</th>
                <th className="p-3">Rows (Valid / Rej)</th>
                <th className="p-3">Observation Coverage (UTC)</th>
                <th className="p-3">SHA-256 Checksum</th>
                <th className="p-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {datasets.map((ds) => (
                <tr key={ds.id} className="hover:bg-slate-800/30">
                  <td className="p-3">
                    <SensorBadge sensor={ds.sensor} size="sm" />
                  </td>
                  <td className="p-3 font-semibold text-slate-200">
                    <div>{ds.product_name}</div>
                    <span className="text-[10px] text-slate-400 font-normal">v{ds.product_version}</span>
                  </td>
                  <td className="p-3">
                    <span className="text-emerald-400 font-bold">{ds.valid_rows}</span>
                    <span className="text-slate-500"> / </span>
                    <span className="text-red-400">{ds.rejected_rows}</span>
                    <span className="text-slate-500 text-[10px] block">Total: {ds.total_rows}</span>
                  </td>
                  <td className="p-3 text-slate-300 text-[11px]">
                    <div>{ds.min_time_utc ? new Date(ds.min_time_utc).toISOString().slice(0, 16) : 'N/A'}</div>
                    <div className="text-slate-500">&rarr; {ds.max_time_utc ? new Date(ds.max_time_utc).toISOString().slice(0, 16) : 'N/A'}</div>
                  </td>
                  <td className="p-3 text-[10px] text-slate-400 font-mono">
                    <div className="flex items-center gap-1" title={ds.checksum}>
                      <Fingerprint className="w-3 h-3 text-cyan-400 flex-shrink-0" />
                      <span className="truncate max-w-[120px]">{ds.checksum.slice(0, 12)}...</span>
                    </div>
                  </td>
                  <td className="p-3 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={() => setSelectedDatasetForInspection(ds)}
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-[11px] font-medium transition-colors"
                        title="Inspect 17-field mapping and quality breakdown"
                      >
                        <Eye className="w-3 h-3 text-cyan-400" />
                        Inspect
                      </button>

                      {onDeleteDataset && (
                        <button
                          onClick={() => setDatasetToDelete(ds)}
                          className="inline-flex items-center gap-1 p-1 rounded hover:bg-red-950/60 text-slate-500 hover:text-red-400 border border-transparent hover:border-red-800 transition-colors"
                          title="Remove dataset"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Slide-out Schema & QC Drawer Modal */}
      {selectedDatasetForInspection && (
        <div
          role="dialog"
          aria-modal="true"
          className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex justify-end"
        >
          <div className="w-full max-w-2xl bg-slate-900 border-l border-slate-800 h-full overflow-y-auto p-6 space-y-6 shadow-2xl flex flex-col justify-between">
            <div className="space-y-6">
              {/* Drawer Header */}
              <div className="flex items-center justify-between border-b border-slate-800 pb-4">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <SensorBadge sensor={selectedDatasetForInspection.sensor} size="md" />
                    <h3 className="text-base font-bold text-slate-100">
                      {selectedDatasetForInspection.product_name}
                    </h3>
                  </div>
                  <p className="text-xs font-mono text-slate-400">
                    Dataset ID: {selectedDatasetForInspection.id} &bull; Checksum: {selectedDatasetForInspection.checksum.slice(0, 16)}...
                  </p>
                </div>

                <button
                  onClick={() => setSelectedDatasetForInspection(null)}
                  className="p-1.5 rounded hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition-colors"
                  aria-label="Close Drawer"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Data Quality Metrics Summary */}
              <div className="grid grid-cols-3 gap-3 font-mono text-xs text-center">
                <div className="p-3 rounded bg-slate-950 border border-slate-800">
                  <span className="text-[10px] text-slate-400 uppercase block">Total Rows</span>
                  <span className="text-lg font-bold text-slate-100">{selectedDatasetForInspection.total_rows}</span>
                </div>
                <div className="p-3 rounded bg-slate-950 border border-emerald-900/60">
                  <span className="text-[10px] text-emerald-400 uppercase block">Valid Passed</span>
                  <span className="text-lg font-bold text-emerald-400">{selectedDatasetForInspection.valid_rows}</span>
                </div>
                <div className="p-3 rounded bg-slate-950 border border-red-900/60">
                  <span className="text-[10px] text-red-400 uppercase block">Rejected Excluded</span>
                  <span className="text-lg font-bold text-red-400">{selectedDatasetForInspection.rejected_rows}</span>
                </div>
              </div>

              {/* Common Internal Data Dictionary Mapping Preview (FR-07, FR-08) */}
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <FileCode2 className="w-4 h-4 text-cyan-400" />
                  <h4 className="text-xs font-mono font-bold uppercase text-slate-200">
                    Common Internal Data Dictionary Mapping Preview (FR-07, FR-08)
                  </h4>
                </div>
                <p className="text-xs text-slate-400 leading-relaxed font-mono">
                  All 17 fields normalized from raw source headers while strictly retaining original timestamps, confidence scales, and un-averaged FRP values.
                </p>

                <div className="overflow-x-auto rounded border border-slate-800 bg-slate-950">
                  <table className="w-full text-left text-xs font-mono">
                    <thead className="bg-slate-900/90 text-slate-400 border-b border-slate-800">
                      <tr>
                        <th className="p-2.5">Source Header</th>
                        <th className="p-2.5">Internal Field</th>
                        <th className="p-2.5">Sample Raw</th>
                        <th className="p-2.5">Normalized UTC / Bounds</th>
                        <th className="p-2.5">Scientific Note</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60">
                      {mappings.map((item, idx) => (
                        <tr key={idx} className="hover:bg-slate-800/40">
                          <td className="p-2.5 text-slate-300">{item.source_column}</td>
                          <td className="p-2.5 text-cyan-400 font-semibold">{item.internal_field}</td>
                          <td className="p-2.5 text-amber-300">{item.sample_raw_value}</td>
                          <td className="p-2.5 text-emerald-300">{item.sample_normalized_value}</td>
                          <td className="p-2.5 text-slate-400 text-[11px]">{item.unit_or_note}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>

            <div className="pt-4 border-t border-slate-800">
              <button
                onClick={() => setSelectedDatasetForInspection(null)}
                className="w-full py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 font-mono text-xs rounded transition-colors"
              >
                Close Inspection Drawer
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Accessible Remove Dataset Confirmation Dialog (08_UI_UX_DESIGN.md Section 5) */}
      {datasetToDelete && (
        <div
          role="dialog"
          aria-modal="true"
          className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4"
        >
          <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-lg p-5 space-y-4 shadow-2xl">
            <div className="flex items-start gap-3">
              <div className="p-2 rounded bg-red-950/80 border border-red-800 text-red-400">
                <AlertTriangle className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-slate-100">
                  Confirm Dataset Removal
                </h3>
                <p className="text-xs text-slate-400 mt-1 leading-relaxed">
                  Are you sure you want to remove <strong className="text-slate-200">{datasetToDelete.product_name}</strong> (ID: <span className="font-mono">{datasetToDelete.id}</span>)?
                  This operation protects existing files but removes ingested records from the current active session.
                </p>
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
              <button
                onClick={() => setDatasetToDelete(null)}
                className="px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-mono transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  if (onDeleteDataset) onDeleteDataset(datasetToDelete.id);
                  setDatasetToDelete(null);
                }}
                className="px-3 py-1.5 rounded bg-red-700 hover:bg-red-600 text-white text-xs font-mono font-semibold transition-colors shadow-sm"
              >
                Confirm Removal
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
