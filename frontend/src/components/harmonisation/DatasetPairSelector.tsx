'use client';

import React from 'react';
import { DatasetRecord } from '@/types/harmonisation';
import { SensorBadge } from '@/components/common/Badges';
import { AlertTriangle, CheckCircle2, Database, Layers, MapPin } from 'lucide-react';

interface DatasetPairSelectorProps {
  datasets: DatasetRecord[];
  selectedModisId: string;
  selectedViirsId: string;
  onSelectModis: (id: string) => void;
  onSelectViirs: (id: string) => void;
}

export function DatasetPairSelector({
  datasets,
  selectedModisId,
  selectedViirsId,
  onSelectModis,
  onSelectViirs,
}: DatasetPairSelectorProps) {
  const modisDatasets = datasets.filter((d) => d.sensor === 'MODIS');
  const viirsDatasets = datasets.filter((d) => d.sensor === 'VIIRS');

  const selectedModis = datasets.find((d) => d.id === selectedModisId);
  const selectedViirs = datasets.find((d) => d.id === selectedViirsId);

  // Spatio-temporal overlap calculations
  let temporalOverlap = false;
  let spatialOverlap = false;

  if (selectedModis && selectedViirs) {
    // Check temporal overlap
    if (selectedModis.min_time_utc && selectedModis.max_time_utc && selectedViirs.min_time_utc && selectedViirs.max_time_utc) {
      const modisStart = new Date(selectedModis.min_time_utc).getTime();
      const modisEnd = new Date(selectedModis.max_time_utc).getTime();
      const viirsStart = new Date(selectedViirs.min_time_utc).getTime();
      const viirsEnd = new Date(selectedViirs.max_time_utc).getTime();

      temporalOverlap = modisStart <= viirsEnd && modisEnd >= viirsStart;
    } else {
      temporalOverlap = true; // unspecified assume plausible
    }

    // Check bounding box intersection: [min_lon, min_lat, max_lon, max_lat]
    if (selectedModis.bbox && selectedViirs.bbox) {
      const [mMinLon, mMinLat, mMaxLon, mMaxLat] = selectedModis.bbox;
      const [vMinLon, vMinLat, vMaxLon, vMaxLat] = selectedViirs.bbox;

      const lonOverlap = mMinLon <= vMaxLon && mMaxLon >= vMinLon;
      const latOverlap = mMinLat <= vMaxLat && mMaxLat >= vMinLat;
      spatialOverlap = lonOverlap && latOverlap;
    } else {
      spatialOverlap = true;
    }
  }

  const hasOverlapIssue = selectedModis && selectedViirs && (!temporalOverlap || !spatialOverlap);

  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900 p-5 shadow-sm space-y-4">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <Database className="w-5 h-5 text-cyan-400" />
          <h3 className="text-sm font-semibold text-slate-100">
            1. Select Input Dataset Pair (Stage A)
          </h3>
        </div>
        <span className="text-xs font-mono text-slate-400">
          Cross-Sensor Pairing: 1 MODIS + 1 VIIRS Target
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* MODIS Dataset Select */}
        <div className="space-y-2 p-3.5 rounded bg-slate-950 border border-slate-800">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <SensorBadge sensor="MODIS" size="sm" />
              <label className="text-xs font-mono text-slate-200 font-semibold">
                MODIS Input Dataset
              </label>
            </div>
            <span className="text-[10px] text-slate-400 font-mono">
              {modisDatasets.length} available
            </span>
          </div>

          <select
            value={selectedModisId}
            onChange={(e) => onSelectModis(e.target.value)}
            className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-xs font-mono text-slate-100 focus:outline-none focus:border-cyan-500"
          >
            <option value="">-- Choose MODIS Dataset --</option>
            {modisDatasets.map((ds) => (
              <option key={ds.id} value={ds.id}>
                {ds.product_name} ({ds.product_version}) — {ds.valid_rows} valid rows
              </option>
            ))}
          </select>

          {selectedModis && (
            <div className="text-[11px] font-mono text-slate-400 space-y-1 pt-1">
              <div className="flex justify-between">
                <span>Total / Valid:</span>
                <span className="text-slate-200">{selectedModis.total_rows} / {selectedModis.valid_rows}</span>
              </div>
              <div className="flex justify-between">
                <span>Coverage UTC:</span>
                <span className="text-slate-300 truncate max-w-[190px]">
                  {selectedModis.min_time_utc ? new Date(selectedModis.min_time_utc).toISOString().slice(5, 16) : 'N/A'} &rarr;{' '}
                  {selectedModis.max_time_utc ? new Date(selectedModis.max_time_utc).toISOString().slice(5, 16) : 'N/A'}
                </span>
              </div>
            </div>
          )}
        </div>

        {/* VIIRS Dataset Select */}
        <div className="space-y-2 p-3.5 rounded bg-slate-950 border border-slate-800">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <SensorBadge sensor="VIIRS" size="sm" />
              <label className="text-xs font-mono text-slate-200 font-semibold">
                VIIRS Input Dataset
              </label>
            </div>
            <span className="text-[10px] text-slate-400 font-mono">
              {viirsDatasets.length} available
            </span>
          </div>

          <select
            value={selectedViirsId}
            onChange={(e) => onSelectViirs(e.target.value)}
            className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-xs font-mono text-slate-100 focus:outline-none focus:border-cyan-500"
          >
            <option value="">-- Choose VIIRS Dataset --</option>
            {viirsDatasets.map((ds) => (
              <option key={ds.id} value={ds.id}>
                {ds.product_name} ({ds.product_version}) — {ds.valid_rows} valid rows
              </option>
            ))}
          </select>

          {selectedViirs && (
            <div className="text-[11px] font-mono text-slate-400 space-y-1 pt-1">
              <div className="flex justify-between">
                <span>Total / Valid:</span>
                <span className="text-slate-200">{selectedViirs.total_rows} / {selectedViirs.valid_rows}</span>
              </div>
              <div className="flex justify-between">
                <span>Coverage UTC:</span>
                <span className="text-slate-300 truncate max-w-[190px]">
                  {selectedViirs.min_time_utc ? new Date(selectedViirs.min_time_utc).toISOString().slice(5, 16) : 'N/A'} &rarr;{' '}
                  {selectedViirs.max_time_utc ? new Date(selectedViirs.max_time_utc).toISOString().slice(5, 16) : 'N/A'}
                </span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Spatio-Temporal Overlap Verification Banner */}
      {selectedModis && selectedViirs && (
        <div
          className={`p-3 rounded border text-xs font-mono flex items-start gap-2.5 ${
            hasOverlapIssue
              ? 'bg-amber-950/40 border-amber-800 text-amber-200'
              : 'bg-emerald-950/30 border-emerald-800/80 text-emerald-200'
          }`}
        >
          {hasOverlapIssue ? (
            <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
          ) : (
            <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
          )}

          <div>
            <span className="font-bold">
              {hasOverlapIssue
                ? 'Spatio-Temporal Overlap Warning (docs/05_HARMONISATION_ALGORITHM.md Section 7):'
                : 'Spatio-Temporal Coincidence Verified:'}
            </span>
            <div className="mt-1 text-[11px] space-y-0.5">
              <div>
                &bull; Geographic Bounding Box Overlap:{' '}
                <strong className={spatialOverlap ? 'text-emerald-300' : 'text-amber-300'}>
                  {spatialOverlap ? 'Intersects' : 'Disjoint (No geographic overlap)'}
                </strong>
              </div>
              <div>
                &bull; Observation Time Window Overlap:{' '}
                <strong className={temporalOverlap ? 'text-emerald-300' : 'text-amber-300'}>
                  {temporalOverlap ? 'Overlaps in UTC window' : 'Disjoint (Different acquisition timeframes)'}
                </strong>
              </div>
              {hasOverlapIssue && (
                <p className="text-amber-300/90 pt-1">
                  Note: Disjoint datasets will yield 0 candidate matches. All observations will be retained as <code>unmatched_modis</code> and <code>unmatched_viirs</code> according to Rule 7.
                </p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
