'use client';

import React from 'react';
import { MatchStatus, SensorType } from '@/types/harmonisation';
import { MATCH_STATUS_CONFIGS, SENSOR_CONFIGS } from '@/lib/constants/design';
import { MatchStatusBadge, SensorBadge } from '@/components/common/Badges';
import {
  Calendar,
  Eye,
  Filter,
  Layers,
  MapPin,
  RefreshCw,
  Sliders,
} from 'lucide-react';
import clsx from 'clsx';

export interface MapFilters {
  startDate: string;
  endDate: string;
  sensor: 'ALL' | 'MODIS' | 'VIIRS';
  statuses: MatchStatus[];
  regionPreset: string;
  customBbox?: [number, number, number, number] | null;
}

interface MapLayerAndFilterPanelProps {
  filters: MapFilters;
  onChangeFilters: (filters: MapFilters) => void;
  activeLayers: Record<string, boolean>;
  onToggleLayer: (layerKey: string) => void;
  filteredCounts: {
    total: number;
    matched: number;
    unmatched_modis: number;
    unmatched_viirs: number;
    ambiguous: number;
  };
  onResetFilters: () => void;
}

export function MapLayerAndFilterPanel({
  filters,
  onChangeFilters,
  activeLayers,
  onToggleLayer,
  filteredCounts,
  onResetFilters,
}: MapLayerAndFilterPanelProps) {
  const handleToggleStatus = (status: MatchStatus) => {
    const exists = filters.statuses.includes(status);
    const next = exists
      ? filters.statuses.filter((s) => s !== status)
      : [...filters.statuses, status];
    onChangeFilters({ ...filters, statuses: next });
  };

  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900 p-4 shadow-sm space-y-4 text-xs font-mono">
      {/* Top Section: Live Count Agreement Check Banner (08_UI_UX_DESIGN.md Section 6) */}
      <div
        role="status"
        aria-label="Synchronized Live Count Telemetry"
        className="rounded bg-slate-950 p-2.5 border border-slate-800 flex flex-wrap items-center justify-between gap-3 text-slate-300"
      >
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-slate-400 font-bold uppercase text-[10px]">
            Live Map Telemetry Agreement Check:
          </span>
          <span className="font-extrabold text-slate-100 text-sm">
            {filteredCounts.total} Features
          </span>
        </div>

        <div className="flex flex-wrap items-center gap-3 text-[11px]">
          <span className="flex items-center gap-1">
            <span
              className="w-2 h-2 rounded-full inline-block"
              style={{ backgroundColor: MATCH_STATUS_CONFIGS.matched.color }}
            />
            Matched: <strong className="text-emerald-400">{filteredCounts.matched}</strong>
          </span>

          <span className="flex items-center gap-1">
            <span
              className="w-2 h-2 rounded-sm inline-block"
              style={{ backgroundColor: MATCH_STATUS_CONFIGS.unmatched_modis.color }}
            />
            Unmatched MODIS: <strong className="text-amber-400">{filteredCounts.unmatched_modis}</strong>
          </span>

          <span className="flex items-center gap-1">
            <span
              className="w-0 h-0 inline-block"
              style={{
                borderLeft: '4px solid transparent',
                borderRight: '4px solid transparent',
                borderBottom: `7px solid ${MATCH_STATUS_CONFIGS.unmatched_viirs.color}`,
              }}
            />
            Unmatched VIIRS: <strong className="text-cyan-400">{filteredCounts.unmatched_viirs}</strong>
          </span>

          <span className="flex items-center gap-1">
            <span
              className="w-2 h-2 rotate-45 inline-block"
              style={{ backgroundColor: MATCH_STATUS_CONFIGS.ambiguous.color }}
            />
            Ambiguous: <strong className="text-purple-400">{filteredCounts.ambiguous}</strong>
          </span>
        </div>
      </div>

      {/* Filter Controls Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-3 pt-1">
        {/* Date Window */}
        <div className="space-y-1">
          <label className="text-[10px] text-slate-400 uppercase font-semibold block flex items-center gap-1">
            <Calendar className="w-3 h-3 text-cyan-400" /> Observation Date (UTC)
          </label>
          <div className="grid grid-cols-2 gap-1.5">
            <input
              type="date"
              value={filters.startDate}
              onChange={(e) => onChangeFilters({ ...filters, startDate: e.target.value })}
              className="bg-slate-950 border border-slate-700 rounded p-1 text-[11px] text-slate-100 focus:outline-none focus:border-cyan-500"
            />
            <input
              type="date"
              value={filters.endDate}
              onChange={(e) => onChangeFilters({ ...filters, endDate: e.target.value })}
              className="bg-slate-950 border border-slate-700 rounded p-1 text-[11px] text-slate-100 focus:outline-none focus:border-cyan-500"
            />
          </div>
        </div>

        {/* Sensor Selection */}
        <div className="space-y-1">
          <label className="text-[10px] text-slate-400 uppercase font-semibold block flex items-center gap-1">
            <Filter className="w-3 h-3 text-cyan-400" /> Sensor Filter
          </label>
          <div className="flex items-center gap-1 bg-slate-950 p-1 rounded border border-slate-800">
            {(['ALL', 'MODIS', 'VIIRS'] as const).map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => onChangeFilters({ ...filters, sensor: s })}
                className={clsx(
                  'flex-1 py-1 rounded text-[10px] font-bold transition-colors',
                  filters.sensor === s
                    ? 'bg-cyan-600 text-slate-950 shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                )}
              >
                {s}
              </button>
            ))}
          </div>
        </div>

        {/* Match Status Filter */}
        <div className="space-y-1">
          <label className="text-[10px] text-slate-400 uppercase font-semibold block flex items-center gap-1">
            <Layers className="w-3 h-3 text-cyan-400" /> Match Statuses
          </label>
          <div className="flex flex-wrap items-center gap-1">
            {(['matched', 'unmatched_modis', 'unmatched_viirs', 'ambiguous'] as MatchStatus[]).map((st) => {
              const active = filters.statuses.includes(st);
              return (
                <button
                  key={st}
                  type="button"
                  onClick={() => handleToggleStatus(st)}
                  className={clsx(
                    'px-1.5 py-0.5 rounded text-[10px] border transition-colors',
                    active
                      ? 'bg-slate-800 text-slate-100 border-cyan-500 font-bold'
                      : 'bg-slate-950 text-slate-500 border-slate-800'
                  )}
                >
                  {MATCH_STATUS_CONFIGS[st].label}
                </button>
              );
            })}
          </div>
        </div>

        {/* Region & Reset */}
        <div className="space-y-1 flex flex-col justify-between">
          <label className="text-[10px] text-slate-400 uppercase font-semibold block flex items-center gap-1">
            <MapPin className="w-3 h-3 text-cyan-400" /> Spatial Study Extent
          </label>
          <div className="flex items-center gap-2">
            <select
              value={filters.regionPreset}
              onChange={(e) => onChangeFilters({ ...filters, regionPreset: e.target.value })}
              className="flex-1 bg-slate-950 border border-slate-700 rounded p-1 text-[11px] text-slate-100 focus:outline-none focus:border-cyan-500"
            >
              <option value="all">Indo-Gangetic Basin (Default)</option>
              <option value="punjab">Punjab &amp; Haryana Agriculture</option>
              <option value="central">Central Forest Fire Corridors</option>
              <option value="viewport">Current Map Viewport</option>
            </select>

            <button
              type="button"
              onClick={onResetFilters}
              className="p-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-slate-100 border border-slate-700 transition-colors"
              title="Reset all filters to defaults"
            >
              <RefreshCw className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>

      {/* Six Toggleable Map Layers Bar */}
      <div className="pt-2 border-t border-slate-800/80 flex flex-wrap items-center justify-between gap-2 text-[11px]">
        <span className="text-[10px] uppercase text-slate-400 font-semibold flex items-center gap-1">
          <Eye className="w-3 h-3 text-cyan-400" /> 6 Toggleable Geospatial Layers:
        </span>

        <div className="flex flex-wrap items-center gap-1.5">
          <button
            type="button"
            onClick={() => onToggleLayer('matched')}
            className={clsx(
              'px-2 py-0.5 rounded border transition-colors flex items-center gap-1',
              activeLayers.matched
                ? 'bg-emerald-950/80 border-emerald-700 text-emerald-300 font-bold'
                : 'bg-slate-950 border-slate-800 text-slate-500'
            )}
          >
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
            1. Matched Pairs
          </button>

          <button
            type="button"
            onClick={() => onToggleLayer('unmatched_modis')}
            className={clsx(
              'px-2 py-0.5 rounded border transition-colors flex items-center gap-1',
              activeLayers.unmatched_modis
                ? 'bg-amber-950/80 border-amber-700 text-amber-300 font-bold'
                : 'bg-slate-950 border-slate-800 text-slate-500'
            )}
          >
            <span className="w-1.5 h-1.5 bg-amber-400" />
            2. Unmatched MODIS
          </button>

          <button
            type="button"
            onClick={() => onToggleLayer('unmatched_viirs')}
            className={clsx(
              'px-2 py-0.5 rounded border transition-colors flex items-center gap-1',
              activeLayers.unmatched_viirs
                ? 'bg-blue-950/80 border-blue-700 text-cyan-300 font-bold'
                : 'bg-slate-950 border-slate-800 text-slate-500'
            )}
          >
            <span className="w-0 h-0 border-l-[3px] border-l-transparent border-r-[3px] border-r-transparent border-b-[5px] border-b-cyan-400" />
            3. Unmatched VIIRS
          </button>

          <button
            type="button"
            onClick={() => onToggleLayer('ambiguous')}
            className={clsx(
              'px-2 py-0.5 rounded border transition-colors flex items-center gap-1',
              activeLayers.ambiguous
                ? 'bg-purple-950/80 border-purple-700 text-purple-300 font-bold'
                : 'bg-slate-950 border-slate-800 text-slate-500'
            )}
          >
            <span className="w-1.5 h-1.5 rotate-45 bg-purple-400" />
            4. Ambiguous
          </button>

          <button
            type="button"
            onClick={() => onToggleLayer('raw_modis')}
            className={clsx(
              'px-2 py-0.5 rounded border transition-colors flex items-center gap-1',
              activeLayers.raw_modis
                ? 'bg-slate-800 border-amber-600 text-amber-200'
                : 'bg-slate-950 border-slate-800 text-slate-500'
            )}
          >
            5. Raw MODIS
          </button>

          <button
            type="button"
            onClick={() => onToggleLayer('raw_viirs')}
            className={clsx(
              'px-2 py-0.5 rounded border transition-colors flex items-center gap-1',
              activeLayers.raw_viirs
                ? 'bg-slate-800 border-cyan-600 text-cyan-200'
                : 'bg-slate-950 border-slate-800 text-slate-500'
            )}
          >
            6. Raw VIIRS
          </button>
        </div>
      </div>
    </div>
  );
}
