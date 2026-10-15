'use client';

import React, { useState } from 'react';
import { Download, FileSpreadsheet, FileCode, FileJson, CheckCircle2, Filter, Layers, Database } from 'lucide-react';
import { HarmonisedRecord, ProcessingRunSummary } from '@/types/harmonisation';

interface ExportDownloadCardsProps {
  runSummary: ProcessingRunSummary | null;
  records: HarmonisedRecord[];
  isFiltered?: boolean;
  filterDescription?: string;
}

type ExportSubset = 'all' | 'matched' | 'unmatched_modis' | 'unmatched_viirs' | 'ambiguous';
type ExportScope = 'full' | 'filtered';

export function ExportDownloadCards({
  runSummary,
  records,
  isFiltered = false,
  filterDescription = 'Active filters applied',
}: ExportDownloadCardsProps) {
  const [selectedSubset, setSelectedSubset] = useState<ExportSubset>('all');
  const [exportScope, setExportScope] = useState<ExportScope>('full');
  const [downloadSuccess, setDownloadSuccess] = useState<string | null>(null);

  const runId = runSummary?.run_id || 'run-unassigned';

  // Filter records based on selected subset
  const getFilteredSubsetRecords = () => {
    if (selectedSubset === 'all') return records;
    return records.filter((r) => r.match_status === selectedSubset);
  };

  const subsetRecords = getFilteredSubsetRecords();

  // Helper to trigger browser file download
  const triggerDownload = (filename: string, content: string, mimeType: string) => {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);

    setDownloadSuccess(filename);
    setTimeout(() => setDownloadSuccess(null), 4000);
  };

  // 1. Generate CSV
  const handleExportCsv = () => {
    const headers = [
      'harmonisation_id',
      'match_status',
      'modis_observation_id',
      'viirs_observation_id',
      'spatial_distance_m',
      'time_difference_s',
      'matching_score',
      'matching_method_version',
      'modis_lat',
      'modis_lon',
      'viirs_lat',
      'viirs_lon',
      'modis_time_utc',
      'viirs_time_utc',
      'modis_frp_mw',
      'viirs_frp_mw',
      'run_id',
    ];

    const rows = subsetRecords.map((r) => [
      r.harmonisation_id,
      r.match_status,
      r.modis_observation_id || '',
      r.viirs_observation_id || '',
      r.spatial_distance_m !== null ? r.spatial_distance_m.toFixed(1) : '',
      r.time_difference_s !== null ? r.time_difference_s : '',
      r.match_score !== null ? r.match_score.toFixed(3) : '',
      r.matching_method_version,
      r.modis_observation?.latitude ?? '',
      r.modis_observation?.longitude ?? '',
      r.viirs_observation?.latitude ?? '',
      r.viirs_observation?.longitude ?? '',
      r.modis_observation?.observation_time_utc ?? '',
      r.viirs_observation?.observation_time_utc ?? '',
      r.modis_observation?.frp_raw ?? '',
      r.viirs_observation?.frp_raw ?? '',
      r.run_id,
    ]);

    const csvContent = [
      `# Harmonisation Run ID: ${runId}`,
      `# Method Version: ${runSummary?.method_version || 'v1.0.0-spatial-temporal-euclidean'}`,
      `# Scope: ${exportScope === 'full' ? 'Full Processing Run' : `Filtered (${filterDescription})`}`,
      `# Subset: ${selectedSubset}`,
      `# Generated: ${new Date().toISOString()}`,
      headers.join(','),
      ...rows.map((row) => row.map((val) => `"${String(val).replace(/"/g, '""')}"`).join(',')),
    ].join('\n');

    triggerDownload(`harmonised_${selectedSubset}_${runId}.csv`, csvContent, 'text/csv;charset=utf-8;');
  };

  // 2. Generate GeoJSON FeatureCollection
  const handleExportGeoJson = () => {
    const features = subsetRecords.map((r) => {
      // Determine point coordinate: prefer MODIS if present, else VIIRS
      const primaryRecord = r.modis_observation || r.viirs_observation;
      const lon = primaryRecord ? primaryRecord.longitude : 0;
      const lat = primaryRecord ? primaryRecord.latitude : 0;

      return {
        type: 'Feature',
        geometry: {
          type: 'Point',
          coordinates: [lon, lat],
        },
        properties: {
          harmonisation_id: r.harmonisation_id,
          match_status: r.match_status,
          modis_observation_id: r.modis_observation_id,
          viirs_observation_id: r.viirs_observation_id,
          spatial_distance_m: r.spatial_distance_m,
          time_difference_s: r.time_difference_s,
          match_score: r.match_score,
          matching_method_version: r.matching_method_version,
          modis_frp_mw: r.modis_observation?.frp_raw,
          viirs_frp_mw: r.viirs_observation?.frp_raw,
          modis_time_utc: r.modis_observation?.observation_time_utc,
          viirs_time_utc: r.viirs_observation?.observation_time_utc,
          run_id: r.run_id,
        },
      };
    });

    const geoJson = {
      type: 'FeatureCollection',
      name: `harmonised_${selectedSubset}_${runId}`,
      crs: {
        type: 'name',
        properties: { name: 'urn:ogc:def:crs:OGC:1.3:CRS84' },
      },
      properties: {
        run_id: runId,
        method_version: runSummary?.method_version,
        parameters: runSummary?.parameters,
        record_count: subsetRecords.length,
        subset: selectedSubset,
        scope: exportScope,
        generated_at: new Date().toISOString(),
      },
      features,
    };

    triggerDownload(
      `harmonised_${selectedSubset}_${runId}.geojson`,
      JSON.stringify(geoJson, null, 2),
      'application/geo+json;charset=utf-8;'
    );
  };

  // 3. Generate Metadata Manifest JSON
  const handleExportManifest = () => {
    const manifest = {
      scientific_metadata: {
        project: 'Harmonisation of MODIS and VIIRS Hotspots',
        specification_reference: 'docs/04_DATA_SOURCES_AND_DICTIONARY.md',
        run_id: runId,
        method_version: runSummary?.method_version,
        generated_at: new Date().toISOString(),
      },
      algorithm_parameters: runSummary?.parameters,
      observation_counts: runSummary?.counts,
      computed_rates: runSummary?.rates,
      warnings_and_caveats: runSummary?.warnings,
      provenance_scope: exportScope,
    };

    triggerDownload(
      `reproducibility_manifest_${runId}.json`,
      JSON.stringify(manifest, null, 2),
      'application/json;charset=utf-8;'
    );
  };

  return (
    <div className="space-y-6">
      {/* Scope and Filter Banner (UI Acceptance Check: docs/08_UI_UX_DESIGN.md Section 6) */}
      <div className="p-4 rounded-lg bg-slate-900 border border-slate-800 space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2">
            <Database className="w-5 h-5 text-cyan-400" />
            <div>
              <h3 className="text-sm font-semibold text-slate-100">Export Scope &amp; Provenance State</h3>
              <p className="text-xs text-slate-400">
                Rule 6 &amp; UI Check: Exports must explicitly declare whether they contain the entire run or filtered view.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setExportScope('full')}
              className={`px-3 py-1.5 rounded text-xs font-mono transition-colors ${
                exportScope === 'full'
                  ? 'bg-cyan-950 text-cyan-300 border border-cyan-700 font-bold'
                  : 'bg-slate-800 text-slate-400 hover:text-slate-200 border border-slate-700'
              }`}
            >
              Full Processing Run (All Records)
            </button>
            <button
              onClick={() => setExportScope('filtered')}
              className={`px-3 py-1.5 rounded text-xs font-mono transition-colors ${
                exportScope === 'filtered'
                  ? 'bg-amber-950 text-amber-300 border border-amber-700 font-bold'
                  : 'bg-slate-800 text-slate-400 hover:text-slate-200 border border-slate-700'
              }`}
            >
              Filtered View Only
            </button>
          </div>
        </div>

        {/* Active Scope Badge */}
        <div className="flex items-center gap-2 text-xs font-mono">
          <span className="text-slate-400">Export Status:</span>
          {exportScope === 'full' ? (
            <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800 text-[11px] font-semibold flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5" />
              Complete Unfiltered Dataset ({records.length} total records)
            </span>
          ) : (
            <span className="px-2 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-800 text-[11px] font-semibold flex items-center gap-1.5">
              <Filter className="w-3.5 h-3.5" />
              Filtered Records ({subsetRecords.length} records matching {filterDescription})
            </span>
          )}
        </div>
      </div>

      {/* Subset Selection Chips */}
      <div className="space-y-2">
        <label className="text-xs font-semibold text-slate-300 font-mono flex items-center gap-2">
          <Layers className="w-4 h-4 text-cyan-400" />
          Select Data Subset for Export:
        </label>
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
          {[
            { id: 'all', label: 'All Records', count: records.length },
            { id: 'matched', label: 'Matched Pairs', count: records.filter((r) => r.match_status === 'matched').length },
            { id: 'unmatched_modis', label: 'Unmatched MODIS', count: records.filter((r) => r.match_status === 'unmatched_modis').length },
            { id: 'unmatched_viirs', label: 'Unmatched VIIRS', count: records.filter((r) => r.match_status === 'unmatched_viirs').length },
            { id: 'ambiguous', label: 'Ambiguous Cases', count: records.filter((r) => r.match_status === 'ambiguous').length },
          ].map((chip) => (
            <button
              key={chip.id}
              onClick={() => setSelectedSubset(chip.id as ExportSubset)}
              className={`p-2.5 rounded-lg border text-left font-mono transition-all ${
                selectedSubset === chip.id
                  ? 'bg-slate-800 border-cyan-500 text-slate-100 shadow-sm'
                  : 'bg-slate-900 border-slate-800 text-slate-400 hover:border-slate-700'
              }`}
            >
              <div className="text-[11px] font-medium">{chip.label}</div>
              <div className="text-xs font-bold text-cyan-400 mt-0.5">{chip.count} rows</div>
            </button>
          ))}
        </div>
      </div>

      {/* Download Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* CSV Card */}
        <div className="p-5 rounded-lg bg-slate-900 border border-slate-800 flex flex-col justify-between space-y-4">
          <div className="space-y-3">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-lg bg-emerald-950 border border-emerald-800 text-emerald-400">
                <FileSpreadsheet className="w-6 h-6" />
              </div>
              <div>
                <h4 className="text-sm font-semibold text-slate-200">Normalized CSV</h4>
                <p className="text-[11px] text-slate-400 font-mono">RFC 4180 standard table</p>
              </div>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed font-sans">
              Contains all 17 standardized internal fields, linked observation IDs, geodesic distances (&Delta;d in metres),
              time differences (&Delta;t in seconds), and match scores.
            </p>
          </div>

          <button
            onClick={handleExportCsv}
            disabled={subsetRecords.length === 0}
            className="w-full py-2.5 px-3 bg-emerald-900/60 hover:bg-emerald-800 text-emerald-200 border border-emerald-700 rounded text-xs font-mono font-semibold transition-colors flex items-center justify-center gap-2 disabled:opacity-40"
          >
            <Download className="w-4 h-4" />
            Download CSV ({subsetRecords.length} rows)
          </button>
        </div>

        {/* GeoJSON Card */}
        <div className="p-5 rounded-lg bg-slate-900 border border-slate-800 flex flex-col justify-between space-y-4">
          <div className="space-y-3">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-lg bg-cyan-950 border border-cyan-800 text-cyan-400">
                <FileCode className="w-6 h-6" />
              </div>
              <div>
                <h4 className="text-sm font-semibold text-slate-200">GeoJSON Features</h4>
                <p className="text-[11px] text-slate-400 font-mono">EPSG:4326 (WGS 84)</p>
              </div>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed font-sans">
              GIS-ready spatial layer for direct import into QGIS, ArcGIS, Google Earth Engine, or MapLibre.
              Features include full provenance attributes.
            </p>
          </div>

          <button
            onClick={handleExportGeoJson}
            disabled={subsetRecords.length === 0}
            className="w-full py-2.5 px-3 bg-cyan-900/60 hover:bg-cyan-800 text-cyan-200 border border-cyan-700 rounded text-xs font-mono font-semibold transition-colors flex items-center justify-center gap-2 disabled:opacity-40"
          >
            <Download className="w-4 h-4" />
            Download GeoJSON ({subsetRecords.length} features)
          </button>
        </div>

        {/* Reproducibility Manifest Card */}
        <div className="p-5 rounded-lg bg-slate-900 border border-slate-800 flex flex-col justify-between space-y-4">
          <div className="space-y-3">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-lg bg-purple-950 border border-purple-800 text-purple-400">
                <FileJson className="w-6 h-6" />
              </div>
              <div>
                <h4 className="text-sm font-semibold text-slate-200">Reproducibility JSON</h4>
                <p className="text-[11px] text-slate-400 font-mono">Run parameters &amp; manifest</p>
              </div>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed font-sans">
              Complete parameter state, version hashes, QA thresholds, rejection tallies, and scientific caveats for paper publication or audit.
            </p>
          </div>

          <button
            onClick={handleExportManifest}
            className="w-full py-2.5 px-3 bg-purple-900/60 hover:bg-purple-800 text-purple-200 border border-purple-700 rounded text-xs font-mono font-semibold transition-colors flex items-center justify-center gap-2"
          >
            <Download className="w-4 h-4" />
            Download Manifest JSON
          </button>
        </div>
      </div>

      {/* Success Banner */}
      {downloadSuccess && (
        <div className="p-3 rounded-lg bg-emerald-950/40 border border-emerald-800 text-xs text-emerald-300 font-mono flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
          <span>Successfully generated and downloaded: <strong>{downloadSuccess}</strong></span>
        </div>
      )}
    </div>
  );
}
