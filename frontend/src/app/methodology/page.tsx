'use client';

import React from 'react';
import { BookOpen, ShieldAlert, Cpu, FileText } from 'lucide-react';
import { SENSOR_CONFIGS, MATCH_STATUS_CONFIGS } from '@/lib/constants/design';
import { SensorBadge, MatchStatusBadge } from '@/components/common/Badges';

export default function MethodologyReferencePage() {
  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="border-b border-slate-800 pb-4">
        <h2 className="text-xl font-bold tracking-tight text-slate-100 flex items-center gap-2">
          <BookOpen className="w-5 h-5 text-cyan-400" />
          Methodology &amp; Scientific Data Reference
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Authoritative documentation of sensor physics, algorithm stages, match status semantics, and scientific caveats.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Sensor Specifications */}
        <div className="p-5 rounded-lg bg-slate-900 border border-slate-800 space-y-4">
          <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
            <Cpu className="w-4 h-4 text-cyan-400" />
            Sensor Characteristics &amp; Footprint Physics
          </h3>
          <div className="space-y-3 text-xs">
            <div className="p-3 rounded bg-slate-950 border border-slate-800 space-y-1.5">
              <div className="flex items-center justify-between">
                <SensorBadge sensor="MODIS" size="sm" />
                <span className="font-mono text-slate-400">Terra &amp; Aqua</span>
              </div>
              <p className="text-slate-300 leading-relaxed">
                Nominal 1 km spatial resolution at nadir, growing to ~2 km &times; ~4.8 km at scan edges due to optical panoramic distortion ("bow-tie effect"). Uses brightness temperatures in 4&mu;m and 11&mu;m channels.
              </p>
            </div>

            <div className="p-3 rounded bg-slate-950 border border-slate-800 space-y-1.5">
              <div className="flex items-center justify-between">
                <SensorBadge sensor="VIIRS" size="sm" />
                <span className="font-mono text-slate-400">Suomi-NPP &amp; NOAA-20/21</span>
              </div>
              <p className="text-slate-300 leading-relaxed">
                Nominal 375 m resolution in Imagery (I) bands at nadir. Features onboard pixel aggregation constraining footprint growth at scan edges to less than 2&times; nadir, detecting much smaller, lower-intensity fires.
              </p>
            </div>
          </div>
        </div>

        {/* Status Definitions */}
        <div className="p-5 rounded-lg bg-slate-900 border border-slate-800 space-y-4">
          <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
            <FileText className="w-4 h-4 text-cyan-400" />
            Match Status Definitions (docs/08_UI_UX_DESIGN.md)
          </h3>
          <div className="space-y-2.5 text-xs">
            {Object.entries(MATCH_STATUS_CONFIGS).map(([statusKey, config]) => (
              <div key={statusKey} className="p-2.5 rounded bg-slate-950 border border-slate-800 flex items-start gap-2.5">
                <MatchStatusBadge status={config.status} size="sm" showDescriptionTooltip={false} />
                <div className="flex-1">
                  <div className="font-bold text-slate-200 text-[11px]">{config.scientificLabel}</div>
                  <div className="text-slate-400 text-[11px] mt-0.5">{config.description}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Scientific Caution Alert */}
      <div className="p-4 rounded-lg bg-slate-900 border border-amber-800/60 bg-amber-950/20 text-xs text-amber-200 space-y-2">
        <div className="flex items-center gap-2 font-bold text-amber-300">
          <ShieldAlert className="w-4 h-4 flex-shrink-0" />
          Mandatory Scientific Caveats (docs/03_RESEARCH_METHODOLOGY.md Section 7)
        </div>
        <ul className="list-disc list-inside space-y-1 text-amber-200/90 font-mono text-[11px]">
          <li>A hotspot detection is not automatically a unique fire event (point detection &ne; physical event).</li>
          <li>Nearby detections may represent multiple discrete spot fires; single large fires produce multiple contiguous detections.</li>
          <li>Neither MODIS nor VIIRS is treated as "ground truth" for the other.</li>
          <li>Match score is a relative ranking index; it is not a calibrated probability.</li>
          <li>Detection absence does not prove absence of fire (e.g. thick clouds, smoke occlusion, or inter-overpass ignition).</li>
        </ul>
      </div>
    </div>
  );
}
