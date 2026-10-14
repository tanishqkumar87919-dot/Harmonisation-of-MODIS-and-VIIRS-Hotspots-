'use client';

import React from 'react';
import { Map as MapIcon, Layers, Eye } from 'lucide-react';
import { useFixtureMode } from '@/lib/fixtures/FixtureContext';
import { FIXTURE_HARMONISED_RECORDS } from '@/lib/fixtures/labelledTestFixtures';
import { MatchStatusBadge, SensorBadge } from '@/components/common/Badges';

export default function InteractiveMapPage() {
  const { isFixtureMode } = useFixtureMode();

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="border-b border-slate-800 pb-4 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-slate-100 flex items-center gap-2">
            <MapIcon className="w-5 h-5 text-cyan-400" />
            Interactive Map Explorer
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Multi-layer geospatial visualization distinguishing matched, unmatched, and ambiguous hotspot clusters.
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs font-mono">
          <span className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-slate-900 border border-slate-800 text-slate-300">
            <Layers className="w-3.5 h-3.5 text-cyan-400" />
            6 Geospatial Layers
          </span>
        </div>
      </div>

      {/* Geospatial Map Canvas Container */}
      <div className="h-[520px] rounded-lg bg-slate-900 border border-slate-800 relative overflow-hidden flex flex-col items-center justify-center">
        {/* Placeholder background grid simulating coordinate grid */}
        <div className="absolute inset-0 opacity-15 bg-[radial-gradient(#38bdf8_1px,transparent_1px)] [background-size:24px_24px]" />

        {isFixtureMode ? (
          <div className="z-10 text-center max-w-md p-6 bg-slate-950/80 border border-slate-700/80 rounded-xl backdrop-blur shadow-2xl space-y-3">
            <div className="w-10 h-10 rounded-full bg-cyan-950 border border-cyan-800 mx-auto flex items-center justify-center text-cyan-400">
              <Eye className="w-5 h-5" />
            </div>
            <h3 className="text-sm font-semibold text-slate-100">
              Map Viewport Ready (Phase 4 MapLibre GL Integration)
            </h3>
            <p className="text-xs text-slate-400 leading-relaxed font-mono">
              Loaded {FIXTURE_HARMONISED_RECORDS.length} test fixture records with coordinates in northern India (EPSG:4326).
            </p>
            <div className="flex flex-wrap items-center justify-center gap-1.5 pt-2">
              <MatchStatusBadge status="matched" size="sm" />
              <MatchStatusBadge status="unmatched_modis" size="sm" />
              <MatchStatusBadge status="unmatched_viirs" size="sm" />
              <MatchStatusBadge status="ambiguous" size="sm" />
            </div>
          </div>
        ) : (
          <div className="z-10 text-center max-w-md p-6">
            <MapIcon className="w-10 h-10 text-slate-600 mx-auto mb-3" />
            <h3 className="text-sm font-semibold text-slate-300">Geospatial Engine Ready</h3>
            <p className="text-xs text-slate-500 mt-1">
              Select or generate a processing run to load active fire geometries onto the map.
            </p>
          </div>
        )}
      </div>

      {/* Observation Inspection Drawer Preview */}
      {isFixtureMode && (
        <div className="p-4 rounded-lg bg-slate-900 border border-slate-800">
          <h3 className="text-sm font-semibold text-slate-200 mb-3">
            Selected Record Provenance Drawer (Preview)
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
            <div className="p-3 rounded bg-slate-950 border border-slate-800 space-y-2">
              <div className="flex items-center justify-between">
                <SensorBadge sensor="MODIS" size="sm" />
                <span className="text-slate-400">ID: {FIXTURE_HARMONISED_RECORDS[0].modis_observation?.source_record_id}</span>
              </div>
              <div>Lat: {FIXTURE_HARMONISED_RECORDS[0].modis_observation?.latitude}&deg;, Lon: {FIXTURE_HARMONISED_RECORDS[0].modis_observation?.longitude}&deg;</div>
              <div>FRP: {FIXTURE_HARMONISED_RECORDS[0].modis_observation?.frp_raw} MW</div>
              <div>Confidence: {String(FIXTURE_HARMONISED_RECORDS[0].modis_observation?.confidence_raw)}%</div>
            </div>

            <div className="p-3 rounded bg-slate-950 border border-slate-800 space-y-2">
              <div className="flex items-center justify-between">
                <SensorBadge sensor="VIIRS" size="sm" />
                <span className="text-slate-400">ID: {FIXTURE_HARMONISED_RECORDS[0].viirs_observation?.source_record_id}</span>
              </div>
              <div>Lat: {FIXTURE_HARMONISED_RECORDS[0].viirs_observation?.latitude}&deg;, Lon: {FIXTURE_HARMONISED_RECORDS[0].viirs_observation?.longitude}&deg;</div>
              <div>FRP: {FIXTURE_HARMONISED_RECORDS[0].viirs_observation?.frp_raw} MW</div>
              <div>Confidence: {String(FIXTURE_HARMONISED_RECORDS[0].viirs_observation?.confidence_raw)}</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
