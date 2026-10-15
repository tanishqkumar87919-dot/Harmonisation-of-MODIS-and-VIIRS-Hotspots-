'use client';

import React, { useState } from 'react';
import { MatchStatus, SensorType } from '@/types/harmonisation';
import { MATCH_STATUS_CONFIGS, SENSOR_CONFIGS } from '@/lib/constants/design';
import { ChevronDown, ChevronUp, Layers, MapPin } from 'lucide-react';
import clsx from 'clsx';

interface StatusCountMap {
  matched: number;
  unmatched_modis: number;
  unmatched_viirs: number;
  ambiguous: number;
  total: number;
}

interface PersistentMapLegendProps {
  counts: StatusCountMap;
  activeLayers: Record<string, boolean>;
  onToggleLayer: (layerKey: string) => void;
}

export function PersistentMapLegend({
  counts,
  activeLayers,
  onToggleLayer,
}: PersistentMapLegendProps) {
  const [collapsed, setCollapsed] = useState<boolean>(false);

  return (
    <div
      aria-label="Persistent Map Layer Legend"
      className="absolute bottom-6 left-4 z-20 w-64 bg-slate-900/95 border border-slate-800 rounded-lg shadow-xl backdrop-blur-md overflow-hidden text-xs font-mono select-none"
    >
      {/* Legend Header */}
      <div
        onClick={() => setCollapsed(!collapsed)}
        className="p-2.5 bg-slate-950/80 border-b border-slate-800 flex items-center justify-between cursor-pointer hover:bg-slate-950 transition-colors"
      >
        <div className="flex items-center gap-1.5 text-slate-200 font-semibold">
          <Layers className="w-3.5 h-3.5 text-cyan-400" />
          <span>Active Map Legend</span>
        </div>
        <div className="flex items-center gap-2 text-slate-400 text-[10px]">
          <span>{counts.total} Visible</span>
          {collapsed ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        </div>
      </div>

      {!collapsed && (
        <div className="p-3 space-y-2.5">
          {/* Status Items with Interactive Toggle & Feature Counts */}
          <div className="space-y-1.5">
            {/* Matched */}
            <div
              onClick={() => onToggleLayer('matched')}
              className={clsx(
                'flex items-center justify-between p-1.5 rounded cursor-pointer transition-colors',
                activeLayers.matched ? 'bg-slate-950 hover:bg-slate-800' : 'opacity-40 hover:opacity-75'
              )}
            >
              <div className="flex items-center gap-2 text-slate-200">
                <span
                  className="w-3.5 h-3.5 rounded-full flex items-center justify-center flex-shrink-0"
                  style={{ backgroundColor: MATCH_STATUS_CONFIGS.matched.color }}
                >
                  <span className="w-1.5 h-1.5 bg-white rounded-full" />
                </span>
                <span className="text-[11px] font-medium">{MATCH_STATUS_CONFIGS.matched.label}</span>
              </div>
              <span className="font-bold text-emerald-400 text-[11px]">{counts.matched}</span>
            </div>

            {/* Unmatched MODIS */}
            <div
              onClick={() => onToggleLayer('unmatched_modis')}
              className={clsx(
                'flex items-center justify-between p-1.5 rounded cursor-pointer transition-colors',
                activeLayers.unmatched_modis ? 'bg-slate-950 hover:bg-slate-800' : 'opacity-40 hover:opacity-75'
              )}
            >
              <div className="flex items-center gap-2 text-slate-200">
                <span
                  className="w-3 h-3 rounded-sm flex-shrink-0"
                  style={{ backgroundColor: MATCH_STATUS_CONFIGS.unmatched_modis.color }}
                />
                <span className="text-[11px] font-medium">{MATCH_STATUS_CONFIGS.unmatched_modis.label}</span>
              </div>
              <span className="font-bold text-amber-400 text-[11px]">{counts.unmatched_modis}</span>
            </div>

            {/* Unmatched VIIRS */}
            <div
              onClick={() => onToggleLayer('unmatched_viirs')}
              className={clsx(
                'flex items-center justify-between p-1.5 rounded cursor-pointer transition-colors',
                activeLayers.unmatched_viirs ? 'bg-slate-950 hover:bg-slate-800' : 'opacity-40 hover:opacity-75'
              )}
            >
              <div className="flex items-center gap-2 text-slate-200">
                <span
                  className="w-0 h-0 flex-shrink-0"
                  style={{
                    borderLeft: '5px solid transparent',
                    borderRight: '5px solid transparent',
                    borderBottom: `9px solid ${MATCH_STATUS_CONFIGS.unmatched_viirs.color}`,
                  }}
                />
                <span className="text-[11px] font-medium">{MATCH_STATUS_CONFIGS.unmatched_viirs.label}</span>
              </div>
              <span className="font-bold text-cyan-400 text-[11px]">{counts.unmatched_viirs}</span>
            </div>

            {/* Ambiguous */}
            <div
              onClick={() => onToggleLayer('ambiguous')}
              className={clsx(
                'flex items-center justify-between p-1.5 rounded cursor-pointer transition-colors',
                activeLayers.ambiguous ? 'bg-slate-950 hover:bg-slate-800' : 'opacity-40 hover:opacity-75'
              )}
            >
              <div className="flex items-center gap-2 text-slate-200">
                <span
                  className="w-2.5 h-2.5 rotate-45 flex-shrink-0"
                  style={{ backgroundColor: MATCH_STATUS_CONFIGS.ambiguous.color }}
                />
                <span className="text-[11px] font-medium">{MATCH_STATUS_CONFIGS.ambiguous.label}</span>
              </div>
              <span className="font-bold text-purple-400 text-[11px]">{counts.ambiguous}</span>
            </div>
          </div>

          {/* Sensor Geometric Footprints Reference */}
          <div className="pt-2 border-t border-slate-800 text-[10px] text-slate-400 space-y-1">
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-1.5">
                <span
                  className="w-2 h-2 rounded-xs"
                  style={{ backgroundColor: SENSOR_CONFIGS.MODIS.color }}
                />
                MODIS Nadir (1 km)
              </span>
              <span className="text-slate-500">Square</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-1.5">
                <span
                  className="w-0 h-0"
                  style={{
                    borderLeft: '4px solid transparent',
                    borderRight: '4px solid transparent',
                    borderBottom: `7px solid ${SENSOR_CONFIGS.VIIRS.color}`,
                  }}
                />
                VIIRS Nadir (375 m)
              </span>
              <span className="text-slate-500">Triangle</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
