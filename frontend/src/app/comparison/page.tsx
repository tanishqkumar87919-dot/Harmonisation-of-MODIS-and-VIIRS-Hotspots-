'use client';

import React from 'react';
import { BarChart3, AlertCircle } from 'lucide-react';
import { useFixtureMode } from '@/lib/fixtures/FixtureContext';
import { FIXTURE_EVALUATION } from '@/lib/fixtures/labelledTestFixtures';

export default function SensorComparisonPage() {
  const { isFixtureMode } = useFixtureMode();

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="border-b border-slate-800 pb-4">
        <h2 className="text-xl font-bold tracking-tight text-slate-100 flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-cyan-400" />
          Sensor Comparison &amp; Physical Discrepancy Analysis
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Bivariate analysis of spatial distances, temporal overpass deltas, and sensor detection sensitivities.
        </p>
      </div>

      {isFixtureMode ? (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 rounded-lg bg-slate-900 border border-slate-800">
              <h3 className="text-sm font-semibold text-slate-200 mb-2">
                Spatial Distance Distribution (&Delta;d in metres)
              </h3>
              <div className="space-y-2 font-mono text-xs">
                {FIXTURE_EVALUATION.spatial_distance_distribution.map((bin, idx) => (
                  <div key={idx} className="flex items-center justify-between">
                    <span className="text-slate-400 w-24">{bin.bin}</span>
                    <div className="flex-1 mx-3 bg-slate-950 h-3 rounded overflow-hidden">
                      <div
                        className="bg-emerald-500 h-full rounded"
                        style={{ width: `${(bin.count / 35) * 100}%` }}
                      />
                    </div>
                    <span className="text-slate-200 font-bold">{bin.count}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="p-4 rounded-lg bg-slate-900 border border-slate-800">
              <h3 className="text-sm font-semibold text-slate-200 mb-2">
                Temporal Delta Distribution (&Delta;t in minutes)
              </h3>
              <div className="space-y-2 font-mono text-xs">
                {FIXTURE_EVALUATION.time_difference_distribution.map((bin, idx) => (
                  <div key={idx} className="flex items-center justify-between">
                    <span className="text-slate-400 w-24">{bin.bin}</span>
                    <div className="flex-1 mx-3 bg-slate-950 h-3 rounded overflow-hidden">
                      <div
                        className="bg-cyan-500 h-full rounded"
                        style={{ width: `${(bin.count / 60) * 100}%` }}
                      />
                    </div>
                    <span className="text-slate-200 font-bold">{bin.count}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* FRP Scientific Disclaimer */}
          <div className="p-4 rounded-lg bg-slate-900 border border-slate-800 space-y-2">
            <div className="flex items-start gap-2 text-amber-300 text-xs font-semibold">
              <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
              <span>Sensor Physics Rule 8 — Fire Radiative Power (FRP) Semantics</span>
            </div>
            <p className="text-xs text-slate-400 font-mono leading-relaxed">
              {FIXTURE_EVALUATION.frp_distribution?.scientific_disclaimer}
            </p>
          </div>
        </div>
      ) : (
        <div className="p-12 text-center text-slate-500 font-mono text-xs">
          Execute a processing run or enable Fixture Mode to inspect comparative distributions.
        </div>
      )}
    </div>
  );
}
