'use client';

import React from 'react';
import { MatchingParameters } from '@/types/harmonisation';
import { SensorBadge } from '@/components/common/Badges';
import { AlertTriangle, Play, ShieldAlert, Sparkles, CheckCircle2, Loader2 } from 'lucide-react';

interface PreRunConfigurationSummaryProps {
  modisDatasetId: string;
  viirsDatasetId: string;
  modisProductVersion?: string;
  viirsProductVersion?: string;
  parameters: MatchingParameters;
  isSubmitting: boolean;
  onLaunchRun: () => void;
  isValid: boolean;
  validationError?: string | null;
}

export function PreRunConfigurationSummary({
  modisDatasetId,
  viirsDatasetId,
  modisProductVersion = 'C6.1',
  viirsProductVersion = 'v1.0',
  parameters,
  isSubmitting,
  onLaunchRun,
  isValid,
  validationError,
}: PreRunConfigurationSummaryProps) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900 p-5 shadow-sm space-y-5">
      {/* 08_UI_UX_DESIGN.md Section 2.3 Mandatory Scientific Caution Banner */}
      <div
        role="alert"
        className="rounded-lg border border-amber-600/70 bg-amber-950/30 p-4 text-amber-200 text-xs font-mono space-y-1.5 leading-relaxed shadow-sm"
      >
        <div className="flex items-center gap-2 font-bold text-amber-300 text-[13px]">
          <ShieldAlert className="w-4 h-4 flex-shrink-0" />
          <span>Scientific Caution &amp; Epistemic Integrity Notice</span>
        </div>
        <p>
          Changing spatial (<code>max_distance_meters</code>) and temporal (<code>max_time_difference_seconds</code>) thresholds directly alters match, unmatched, and ambiguity counts. A matched record represents co-located and co-timed satellite detections under these rules—<strong>not confirmed identity of a single physical fire event</strong>. Original MODIS and VIIRS observations and FRP values are preserved without averaging.
        </p>
      </div>

      {/* Pre-Run Configuration Summary Table */}
      <div className="space-y-3">
        <h4 className="text-xs font-mono font-bold uppercase text-slate-300 tracking-wider">
          4. Pre-Run Execution Parameters Manifest
        </h4>

        <div className="overflow-x-auto rounded border border-slate-800 bg-slate-950">
          <table className="w-full text-left text-xs font-mono">
            <tbody className="divide-y divide-slate-800/60">
              <tr>
                <td className="p-2.5 text-slate-400 w-1/3 bg-slate-900/40">Target MODIS Dataset:</td>
                <td className="p-2.5 text-slate-200 flex items-center justify-between">
                  <span>{modisDatasetId || '<Unselected>'}</span>
                  <SensorBadge sensor="MODIS" showPlatform={modisProductVersion} size="sm" />
                </td>
              </tr>
              <tr>
                <td className="p-2.5 text-slate-400 bg-slate-900/40">Target VIIRS Dataset:</td>
                <td className="p-2.5 text-slate-200 flex items-center justify-between">
                  <span>{viirsDatasetId || '<Unselected>'}</span>
                  <SensorBadge sensor="VIIRS" showPlatform={viirsProductVersion} size="sm" />
                </td>
              </tr>
              <tr>
                <td className="p-2.5 text-slate-400 bg-slate-900/40">Spatial Radius Threshold (&Delta;d):</td>
                <td className="p-2.5 text-cyan-400 font-bold">
                  {parameters.max_distance_meters} metres ({parameters.max_distance_meters / 1000} km)
                </td>
              </tr>
              <tr>
                <td className="p-2.5 text-slate-400 bg-slate-900/40">Temporal Window (&Delta;t):</td>
                <td className="p-2.5 text-cyan-400 font-bold">
                  {parameters.max_time_difference_seconds} seconds ({Math.round(parameters.max_time_difference_seconds / 60)} mins) &bull; Rule: {parameters.time_window_rule}
                </td>
              </tr>
              <tr>
                <td className="p-2.5 text-slate-400 bg-slate-900/40">Ambiguity Policy:</td>
                <td className="p-2.5 text-purple-300 font-bold capitalize">
                  {parameters.ambiguity_policy}
                </td>
              </tr>
              <tr>
                <td className="p-2.5 text-slate-400 bg-slate-900/40">Method &amp; Engine Version:</td>
                <td className="p-2.5 text-slate-300">
                  v{parameters.matching_method_version} (STRtree Geodesic Engine)
                </td>
              </tr>
              <tr>
                <td className="p-2.5 text-slate-400 bg-slate-900/40">Quality Filters:</td>
                <td className="p-2.5 text-slate-300">
                  Warnings: {parameters.quality_filters.include_warnings ? 'Included' : 'Excluded'} &bull; Min MODIS Conf:{' '}
                  {parameters.quality_filters.min_modis_confidence ?? 'Any'} &bull; Allowed VIIRS Conf:{' '}
                  {parameters.quality_filters.allowed_viirs_confidence_levels?.join(', ') || 'nominal, high'}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {validationError && (
        <div className="p-3 rounded bg-red-950/60 border border-red-800 text-red-200 text-xs font-mono flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-red-400 flex-shrink-0" />
          <span>{validationError}</span>
        </div>
      )}

      {/* Launch Execution Trigger */}
      <div className="pt-2 flex items-center justify-between">
        <span className="text-[11px] font-mono text-slate-400">
          Executes Stages D through G in transactional isolation with provenance tracking
        </span>

        <button
          type="button"
          onClick={onLaunchRun}
          disabled={!isValid || isSubmitting}
          className="px-6 py-2.5 bg-cyan-500 hover:bg-cyan-400 disabled:opacity-50 text-slate-950 font-mono font-bold text-xs rounded transition-all shadow-md flex items-center gap-2 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:ring-offset-2 focus:ring-offset-slate-900 cursor-pointer"
        >
          {isSubmitting ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Executing Spatial Matching Engine...
            </>
          ) : (
            <>
              <Play className="w-4 h-4 fill-current" />
              Start Harmonisation Run
            </>
          )}
        </button>
      </div>
    </div>
  );
}
