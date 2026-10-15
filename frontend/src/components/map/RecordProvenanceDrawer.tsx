'use client';

import React from 'react';
import { HarmonisedRecord, StandardizedObservation } from '@/types/harmonisation';
import { MatchStatusBadge, QualityStatusBadge, SensorBadge } from '@/components/common/Badges';
import {
  Activity,
  AlertCircle,
  Calendar,
  Clock,
  Cpu,
  Fingerprint,
  Flame,
  GitCompare,
  Info,
  MapPin,
  Ruler,
  ShieldCheck,
  X,
} from 'lucide-react';

interface RecordProvenanceDrawerProps {
  record: HarmonisedRecord | null;
  onClose: () => void;
}

export function RecordProvenanceDrawer({ record, onClose }: RecordProvenanceDrawerProps) {
  if (!record) return null;

  const {
    harmonisation_id,
    run_id,
    match_status,
    spatial_distance_m,
    time_difference_s,
    matching_method_version,
    matching_parameters,
    match_score,
    provenance,
    modis_observation,
    viirs_observation,
    candidate_links,
  } = record;

  const formatSecondsToMmSs = (totalSeconds: number) => {
    const mins = Math.floor(totalSeconds / 60);
    const secs = Math.round(totalSeconds % 60);
    return `${totalSeconds}s (${mins}m ${secs < 10 ? '0' : ''}${secs}s)`;
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Observation Record Provenance & Cross-Sensor Inspection"
      className="fixed inset-y-0 right-0 z-50 w-full max-w-xl bg-slate-900 border-l border-slate-800 shadow-2xl flex flex-col justify-between overflow-hidden animate-in slide-in-from-right duration-200"
    >
      {/* Drawer Header */}
      <div className="p-4 bg-slate-950 border-b border-slate-800 flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <MatchStatusBadge status={match_status} size="md" />
            <span className="text-xs font-mono font-bold text-slate-100">
              {harmonisation_id}
            </span>
          </div>
          <span className="text-[10px] font-mono text-slate-400">
            Run: {run_id} &bull; Algorithm v{matching_method_version}
          </span>
        </div>

        <button
          onClick={onClose}
          type="button"
          className="p-1.5 rounded hover:bg-slate-800 text-slate-400 hover:text-slate-100 transition-colors"
          aria-label="Close Drawer"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Main Drawer Scrollable Body */}
      <div className="flex-1 overflow-y-auto p-4 space-y-5 text-xs font-mono">
        {/* Cross-Sensor Linkage Metrics (When matched or ambiguous) */}
        {(spatial_distance_m !== null || time_difference_s !== null || match_score !== null) && (
          <div className="p-4 rounded-lg bg-slate-950 border border-slate-800 space-y-3">
            <div className="flex items-center gap-2 text-cyan-400 font-bold border-b border-slate-800/80 pb-2">
              <GitCompare className="w-4 h-4" />
              <span>Cross-Sensor Proximity &amp; Linkage Metrics</span>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="p-2 rounded bg-slate-900 border border-slate-800">
                <span className="text-[10px] text-slate-400 block mb-0.5">Geodesic Distance</span>
                <span className="text-sm font-bold text-slate-100">
                  {spatial_distance_m !== null ? `${spatial_distance_m.toFixed(1)} m` : 'N/A'}
                </span>
                <span className="text-[10px] text-slate-500 block mt-0.5">
                  Limit: &le; {matching_parameters.max_distance_meters} m
                </span>
              </div>

              <div className="p-2 rounded bg-slate-900 border border-slate-800">
                <span className="text-[10px] text-slate-400 block mb-0.5">Time Difference</span>
                <span className="text-sm font-bold text-slate-100">
                  {time_difference_s !== null ? formatSecondsToMmSs(time_difference_s) : 'N/A'}
                </span>
                <span className="text-[10px] text-slate-500 block mt-0.5">
                  Limit: &le; {matching_parameters.max_time_difference_seconds} s
                </span>
              </div>
            </div>

            {match_score !== null && (
              <div className="p-2.5 rounded bg-slate-900 border border-slate-800 space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-slate-400 text-[11px]">Composite Match Score (Index):</span>
                  <span className="text-emerald-400 font-bold text-sm">
                    {match_score.toFixed(3)}
                  </span>
                </div>
                <p className="text-[10px] text-slate-500 leading-relaxed">
                  <Info className="w-3 h-3 inline mr-1 text-cyan-400" />
                  Ranking index combining normalized spatial distance &amp; temporal gap. Per Rule 8, this is an uncalibrated ranking index and <strong>not</strong> an empirical probability.
                </p>
              </div>
            )}

            {provenance.decision_reason && (
              <div className="text-[11px] text-slate-300 pt-1">
                <span className="text-slate-400">Decision Rationale: </span>
                <span className="text-cyan-300">{provenance.decision_reason}</span>
              </div>
            )}
          </div>
        )}

        {/* MODIS Source Observation Card */}
        {modis_observation ? (
          <div className="p-4 rounded-lg bg-slate-950 border border-amber-900/40 space-y-3">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <div className="flex items-center gap-2">
                <SensorBadge sensor="MODIS" size="sm" />
                <span className="font-bold text-slate-100">MODIS Source Observation</span>
              </div>
              <QualityStatusBadge status={modis_observation.row_quality_status} size="sm" />
            </div>

            <div className="grid grid-cols-2 gap-2 text-[11px]">
              <div>
                <span className="text-slate-500 block">Record ID:</span>
                <span className="text-slate-200">{modis_observation.source_record_id}</span>
              </div>
              <div>
                <span className="text-slate-500 block">Platform:</span>
                <span className="text-slate-200">{modis_observation.platform}</span>
              </div>
              <div>
                <span className="text-slate-500 block">Product &amp; Version:</span>
                <span className="text-slate-200">{modis_observation.product_name} ({modis_observation.product_version})</span>
              </div>
              <div>
                <span className="text-slate-500 block">Observation UTC:</span>
                <span className="text-cyan-300">{new Date(modis_observation.observation_time_utc).toISOString().replace('T', ' ').slice(0, 19)}</span>
              </div>
              <div>
                <span className="text-slate-500 block">Coordinates (WGS84):</span>
                <span className="text-slate-200">{modis_observation.latitude.toFixed(5)}°N, {modis_observation.longitude.toFixed(5)}°E</span>
              </div>
              <div>
                <span className="text-slate-500 block">Confidence (0-100%):</span>
                <span className="text-amber-400 font-bold">{String(modis_observation.confidence_raw)}%</span>
              </div>
              <div>
                <span className="text-slate-500 block">FRP (Original MW):</span>
                <span className="text-emerald-400 font-bold">{modis_observation.frp_raw !== null ? `${modis_observation.frp_raw} MW` : 'N/A'}</span>
              </div>
              <div>
                <span className="text-slate-500 block">Footprint (Scan &times; Track):</span>
                <span className="text-slate-200">{modis_observation.scan_raw ?? '1.0'} km &times; {modis_observation.track_raw ?? '1.0'} km</span>
              </div>
            </div>

            <div className="text-[10px] text-slate-500 pt-1 border-t border-slate-800/80">
              Ingestion Run: {modis_observation.ingestion_run_id} &bull; Internal ID: {modis_observation.observation_id}
            </div>
          </div>
        ) : (
          <div className="p-3 rounded bg-slate-950 border border-slate-800 text-slate-500 text-center">
            No linked MODIS observation (Unmatched VIIRS record)
          </div>
        )}

        {/* VIIRS Source Observation Card */}
        {viirs_observation ? (
          <div className="p-4 rounded-lg bg-slate-950 border border-cyan-900/40 space-y-3">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <div className="flex items-center gap-2">
                <SensorBadge sensor="VIIRS" size="sm" />
                <span className="font-bold text-slate-100">VIIRS Source Observation</span>
              </div>
              <QualityStatusBadge status={viirs_observation.row_quality_status} size="sm" />
            </div>

            <div className="grid grid-cols-2 gap-2 text-[11px]">
              <div>
                <span className="text-slate-500 block">Record ID:</span>
                <span className="text-slate-200">{viirs_observation.source_record_id}</span>
              </div>
              <div>
                <span className="text-slate-500 block">Platform:</span>
                <span className="text-slate-200">{viirs_observation.platform}</span>
              </div>
              <div>
                <span className="text-slate-500 block">Product &amp; Version:</span>
                <span className="text-slate-200">{viirs_observation.product_name} ({viirs_observation.product_version})</span>
              </div>
              <div>
                <span className="text-slate-500 block">Observation UTC:</span>
                <span className="text-cyan-300">{new Date(viirs_observation.observation_time_utc).toISOString().replace('T', ' ').slice(0, 19)}</span>
              </div>
              <div>
                <span className="text-slate-500 block">Coordinates (WGS84):</span>
                <span className="text-slate-200">{viirs_observation.latitude.toFixed(5)}°N, {viirs_observation.longitude.toFixed(5)}°E</span>
              </div>
              <div>
                <span className="text-slate-500 block">Confidence (Categorical):</span>
                <span className="text-cyan-400 font-bold uppercase">{String(viirs_observation.confidence_raw)}</span>
              </div>
              <div>
                <span className="text-slate-500 block">FRP (Original MW):</span>
                <span className="text-emerald-400 font-bold">{viirs_observation.frp_raw !== null ? `${viirs_observation.frp_raw} MW` : 'N/A'}</span>
              </div>
              <div>
                <span className="text-slate-500 block">Footprint (Scan &times; Track):</span>
                <span className="text-slate-200">{viirs_observation.scan_raw ?? '0.375'} km &times; {viirs_observation.track_raw ?? '0.375'} km</span>
              </div>
            </div>

            <div className="text-[10px] text-slate-500 pt-1 border-t border-slate-800/80">
              Ingestion Run: {viirs_observation.ingestion_run_id} &bull; Internal ID: {viirs_observation.observation_id}
            </div>
          </div>
        ) : (
          <div className="p-3 rounded bg-slate-950 border border-slate-800 text-slate-500 text-center">
            No linked VIIRS observation (Unmatched MODIS record)
          </div>
        )}

        {/* Candidate Partners Table (When Ambiguous) */}
        {candidate_links && candidate_links.length > 0 && (
          <div className="p-4 rounded-lg bg-slate-950 border border-purple-900/60 space-y-3">
            <h4 className="text-xs font-bold text-purple-300 flex items-center gap-1.5">
              <span>Candidate Linkages Involved ({candidate_links.length})</span>
            </h4>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-[10px]">
                <thead className="bg-slate-900 text-slate-400 border-b border-slate-800">
                  <tr>
                    <th className="p-2">VIIRS Target</th>
                    <th className="p-2">Distance</th>
                    <th className="p-2">Time Delta</th>
                    <th className="p-2">Score</th>
                    <th className="p-2">Decision</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {candidate_links.map((link) => (
                    <tr key={link.id} className="hover:bg-slate-900/40">
                      <td className="p-2 text-slate-200 font-semibold">{link.viirs_observation_id}</td>
                      <td className="p-2 text-cyan-400">{link.spatial_distance_m.toFixed(0)}m</td>
                      <td className="p-2 text-slate-300">{Math.round(link.time_difference_s / 60)}m</td>
                      <td className="p-2 text-emerald-400 font-bold">{link.score?.toFixed(3) ?? 'N/A'}</td>
                      <td className="p-2 text-purple-300 capitalize">{link.decision}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* Drawer Footer */}
      <div className="p-4 bg-slate-950 border-t border-slate-800 flex items-center justify-between">
        <span className="text-[10px] text-slate-500 font-mono">
          Scientific Provenance Audit Trail &bull; EPSG:4326
        </span>
        <button
          onClick={onClose}
          className="px-4 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-mono rounded transition-colors"
        >
          Dismiss
        </button>
      </div>
    </div>
  );
}
