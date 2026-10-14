'use client';

import React from 'react';
import { Sliders, Play, AlertTriangle } from 'lucide-react';
import { useFixtureMode } from '@/lib/fixtures/FixtureContext';
import { SensorBadge } from '@/components/common/Badges';

export default function HarmonisationWorkspacePage() {
  const { isFixtureMode } = useFixtureMode();

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="border-b border-slate-800 pb-4">
        <h2 className="text-xl font-bold tracking-tight text-slate-100 flex items-center gap-2">
          <Sliders className="w-5 h-5 text-cyan-400" />
          Harmonisation Workspace
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Configure spatial distance threshold, temporal matching window, and candidate ambiguity resolution policy.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Configuration Controls */}
        <div className="lg:col-span-2 space-y-6">
          <div className="p-5 rounded-lg bg-slate-900 border border-slate-800 space-y-4">
            <h3 className="text-sm font-semibold text-slate-200">Matching Thresholds (Stage D)</h3>
            
            {/* Warning banner per SRS & UI guidelines */}
            <div className="p-3 rounded bg-amber-950/40 border border-amber-800 text-amber-200 text-xs flex items-start gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
              <span>
                <strong>Threshold Sensitivity Notice:</strong> Spatial and temporal thresholds directly influence match rates. Higher spatial thresholds increase false linkages; smaller thresholds miss corresponding detections.
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-mono text-slate-300 mb-1">
                  Max Spatial Distance (meters)
                </label>
                <input
                  type="number"
                  defaultValue={1500}
                  className="w-full bg-slate-950 border border-slate-700 rounded p-2 text-xs font-mono text-slate-100 focus:outline-none focus:border-cyan-500"
                />
                <span className="text-[10px] text-slate-500 mt-1 block">
                  Recommended: 1000m – 2000m (accounts for MODIS 1km footprint)
                </span>
              </div>

              <div>
                <label className="block text-xs font-mono text-slate-300 mb-1">
                  Max Time Difference (seconds)
                </label>
                <input
                  type="number"
                  defaultValue={3600}
                  className="w-full bg-slate-950 border border-slate-700 rounded p-2 text-xs font-mono text-slate-100 focus:outline-none focus:border-cyan-500"
                />
                <span className="text-[10px] text-slate-500 mt-1 block">
                  3600s = 60 minutes window
                </span>
              </div>
            </div>

            <div className="pt-3 border-t border-slate-800">
              <label className="block text-xs font-mono text-slate-300 mb-1">
                Candidate Ambiguity Resolution Policy (Stage F)
              </label>
              <select className="w-full bg-slate-950 border border-slate-700 rounded p-2 text-xs font-mono text-slate-100 focus:outline-none focus:border-cyan-500">
                <option value="one_to_one_deterministic">
                  one_to_one_deterministic (Deterministic nearest rank assignment)
                </option>
                <option value="retain_ambiguous">
                  retain_ambiguous (Preserve multi-candidate clusters as ambiguous)
                </option>
                <option value="many_to_many">
                  many_to_many (Record all candidate linkages)
                </option>
              </select>
            </div>
          </div>
        </div>

        {/* Right Column: Execution Summary */}
        <div className="space-y-4">
          <div className="p-5 rounded-lg bg-slate-900 border border-slate-800 space-y-4">
            <h3 className="text-sm font-semibold text-slate-200">Run Configuration Summary</h3>
            <div className="space-y-2 text-xs font-mono text-slate-300">
              <div className="flex justify-between py-1 border-b border-slate-800">
                <span className="text-slate-400">MODIS Target:</span>
                <SensorBadge sensor="MODIS" size="sm" />
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800">
                <span className="text-slate-400">VIIRS Target:</span>
                <SensorBadge sensor="VIIRS" size="sm" />
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800">
                <span className="text-slate-400">Algorithm:</span>
                <span>STRtree Geodesic</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800">
                <span className="text-slate-400">Version:</span>
                <span>1.0.0</span>
              </div>
            </div>

            <button
              disabled={!isFixtureMode}
              className="w-full py-2.5 px-4 bg-cyan-500 hover:bg-cyan-400 disabled:opacity-50 text-slate-950 font-semibold text-xs rounded transition-colors flex items-center justify-center gap-2"
            >
              <Play className="w-4 h-4 fill-current" />
              Launch Harmonisation Run
            </button>
            {!isFixtureMode && (
              <p className="text-[10px] text-slate-500 text-center">
                FastAPI backend must be online to execute real runs.
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
