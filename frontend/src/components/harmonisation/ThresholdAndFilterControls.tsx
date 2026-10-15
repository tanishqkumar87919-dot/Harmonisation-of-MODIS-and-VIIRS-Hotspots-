'use client';

import React from 'react';
import { MatchingQualityFilters, TimeWindowRule } from '@/types/harmonisation';
import { SensorBadge } from '@/components/common/Badges';
import { AlertCircle, Clock, Filter, Info, MapPin, Sliders } from 'lucide-react';
import clsx from 'clsx';

interface ThresholdAndFilterControlsProps {
  maxDistanceMeters: number;
  maxTimeDifferenceSeconds: number;
  timeWindowRule: TimeWindowRule;
  qualityFilters: MatchingQualityFilters;
  onChangeMaxDistance: (val: number) => void;
  onChangeMaxTime: (val: number) => void;
  onChangeTimeWindowRule: (rule: TimeWindowRule) => void;
  onChangeQualityFilters: (filters: MatchingQualityFilters) => void;
}

const SPATIAL_CHIPS = [
  { value: 375, label: '375m', desc: 'VIIRS I-band nadir' },
  { value: 750, label: '750m', desc: 'VIIRS M-band nadir' },
  { value: 1000, label: '1000m', desc: 'MODIS nominal nadir' },
  { value: 1500, label: '1500m', desc: 'Recommended baseline' },
  { value: 2000, label: '2000m', desc: 'Mid-swath allowance' },
  { value: 3000, label: '3000m', desc: 'Scan edge coverage' },
];

const TEMPORAL_CHIPS = [
  { value: 900, label: '15 min (900s)' },
  { value: 1800, label: '30 min (1800s)' },
  { value: 3600, label: '60 min (3600s)' },
  { value: 7200, label: '120 min (7200s)' },
];

export function ThresholdAndFilterControls({
  maxDistanceMeters,
  maxTimeDifferenceSeconds,
  timeWindowRule,
  qualityFilters,
  onChangeMaxDistance,
  onChangeMaxTime,
  onChangeTimeWindowRule,
  onChangeQualityFilters,
}: ThresholdAndFilterControlsProps) {
  const formatTimeSeconds = (s: number) => {
    const mins = Math.round(s / 60);
    const hrs = (s / 3600).toFixed(1);
    if (s < 3600) return `${mins} mins`;
    return `${hrs} hrs (${mins} mins)`;
  };

  const handleToggleViirsConfidence = (level: string) => {
    const current = qualityFilters.allowed_viirs_confidence_levels || ['nominal', 'high'];
    const exists = current.includes(level);
    const next = exists ? current.filter((l) => l !== level) : [...current, level];
    onChangeQualityFilters({
      ...qualityFilters,
      allowed_viirs_confidence_levels: next,
    });
  };

  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900 p-5 shadow-sm space-y-6">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <Sliders className="w-5 h-5 text-cyan-400" />
          <h3 className="text-sm font-semibold text-slate-100">
            2. Spatial &amp; Temporal Thresholds (Stage D, FR-09)
          </h3>
        </div>
        <span className="text-xs font-mono text-slate-400">
          Geodesic STRtree Search Window
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Spatial Distance Threshold */}
        <div className="space-y-3 p-4 rounded bg-slate-950 border border-slate-800">
          <div className="flex items-center justify-between">
            <label className="text-xs font-mono font-bold text-slate-200 flex items-center gap-1.5">
              <MapPin className="w-4 h-4 text-cyan-400" />
              Spatial Distance Radius (&Delta;d in metres)
            </label>
            <span className="text-xs font-mono text-cyan-400 font-bold">
              {maxDistanceMeters} m ({maxDistanceMeters / 1000} km)
            </span>
          </div>

          <input
            type="number"
            min={10}
            max={50000}
            step={50}
            value={maxDistanceMeters}
            onChange={(e) => onChangeMaxDistance(Math.max(1, Number(e.target.value)))}
            className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-xs font-mono text-slate-100 focus:outline-none focus:border-cyan-500"
          />

          {/* Quick-select chips */}
          <div className="flex flex-wrap gap-1.5 pt-1">
            {SPATIAL_CHIPS.map((chip) => (
              <button
                key={chip.value}
                type="button"
                onClick={() => onChangeMaxDistance(chip.value)}
                className={clsx(
                  'px-2 py-1 rounded text-[11px] font-mono border transition-colors',
                  maxDistanceMeters === chip.value
                    ? 'bg-cyan-600 text-slate-950 border-cyan-400 font-bold shadow-sm'
                    : 'bg-slate-900 text-slate-300 border-slate-700 hover:bg-slate-800'
                )}
                title={chip.desc}
              >
                {chip.label}
              </button>
            ))}
          </div>

          <div className="text-[11px] font-mono text-slate-400 pt-1 leading-relaxed border-t border-slate-800/80">
            <Info className="w-3.5 h-3.5 text-cyan-400 inline mr-1" />
            MODIS pixel footprints expand away from nadir due to the panoramic bow-tie effect (up to ~2km &times; ~4.8km at scan edge). Thresholds should account for sensor geometry.
          </div>
        </div>

        {/* Temporal Matching Window */}
        <div className="space-y-3 p-4 rounded bg-slate-950 border border-slate-800">
          <div className="flex items-center justify-between">
            <label className="text-xs font-mono font-bold text-slate-200 flex items-center gap-1.5">
              <Clock className="w-4 h-4 text-cyan-400" />
              Temporal Window (&Delta;t in seconds)
            </label>
            <span className="text-xs font-mono text-cyan-400 font-bold">
              {maxTimeDifferenceSeconds} s ({formatTimeSeconds(maxTimeDifferenceSeconds)})
            </span>
          </div>

          <input
            type="number"
            min={0}
            max={86400}
            step={60}
            value={maxTimeDifferenceSeconds}
            onChange={(e) => onChangeMaxTime(Math.max(0, Number(e.target.value)))}
            className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-xs font-mono text-slate-100 focus:outline-none focus:border-cyan-500"
          />

          {/* Quick-select chips */}
          <div className="flex flex-wrap gap-1.5 pt-1">
            {TEMPORAL_CHIPS.map((chip) => (
              <button
                key={chip.value}
                type="button"
                onClick={() => onChangeMaxTime(chip.value)}
                className={clsx(
                  'px-2 py-1 rounded text-[11px] font-mono border transition-colors',
                  maxTimeDifferenceSeconds === chip.value
                    ? 'bg-cyan-600 text-slate-950 border-cyan-400 font-bold shadow-sm'
                    : 'bg-slate-900 text-slate-300 border-slate-700 hover:bg-slate-800'
                )}
              >
                {chip.label}
              </button>
            ))}
          </div>

          {/* Time Window Directionality */}
          <div className="pt-2 border-t border-slate-800/80">
            <label className="text-[11px] font-mono text-slate-300 block mb-1 font-semibold">
              Temporal Window Directionality Rule:
            </label>
            <div className="flex items-center gap-4 text-xs font-mono">
              <label className="flex items-center gap-1.5 cursor-pointer text-slate-300">
                <input
                  type="radio"
                  name="timeWindowRule"
                  value="absolute"
                  checked={timeWindowRule === 'absolute'}
                  onChange={() => onChangeTimeWindowRule('absolute')}
                  className="text-cyan-500 focus:ring-cyan-500"
                />
                <span>Absolute (|&Delta;t| &le; {maxTimeDifferenceSeconds}s)</span>
              </label>

              <label className="flex items-center gap-1.5 cursor-pointer text-slate-300">
                <input
                  type="radio"
                  name="timeWindowRule"
                  value="directional"
                  checked={timeWindowRule === 'directional'}
                  onChange={() => onChangeTimeWindowRule('directional')}
                  className="text-cyan-500 focus:ring-cyan-500"
                />
                <span>Directional (Sequential overpass)</span>
              </label>
            </div>
          </div>
        </div>
      </div>

      {/* Stage C: Sensor-Specific Quality Filters */}
      <div className="p-4 rounded bg-slate-950 border border-slate-800 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-2">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-amber-500" />
            <h4 className="text-xs font-mono font-bold uppercase text-slate-200">
              Stage C: Sensor-Specific Quality Filters
            </h4>
          </div>
          <span className="text-[10px] text-slate-400 font-mono">
            Note: Rejected rows are permanently excluded from candidate pairing
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs font-mono">
          {/* Include Warnings Toggle */}
          <div className="space-y-1.5">
            <label className="flex items-center gap-2 cursor-pointer text-slate-300">
              <input
                type="checkbox"
                checked={qualityFilters.include_warnings}
                onChange={(e) =>
                  onChangeQualityFilters({
                    ...qualityFilters,
                    include_warnings: e.target.checked,
                  })
                }
                className="rounded border-slate-700 text-cyan-500 focus:ring-cyan-500"
              />
              <span className="font-semibold">Include Warning Rows</span>
            </label>
            <p className="text-[10px] text-slate-500 leading-relaxed">
              When checked, observations with non-fatal flags (e.g. high scan angle) participate in candidate generation.
            </p>
          </div>

          {/* MODIS Numeric Confidence Filter */}
          <div className="space-y-1.5">
            <div className="flex items-center gap-1.5">
              <SensorBadge sensor="MODIS" size="sm" />
              <span className="text-slate-300 font-semibold">Min Confidence %:</span>
            </div>
            <input
              type="number"
              min={0}
              max={100}
              placeholder="e.g. 30 (0-100)"
              value={qualityFilters.min_modis_confidence ?? ''}
              onChange={(e) =>
                onChangeQualityFilters({
                  ...qualityFilters,
                  min_modis_confidence: e.target.value === '' ? null : Number(e.target.value),
                })
              }
              className="w-full bg-slate-900 border border-slate-700 rounded p-1.5 text-xs text-slate-100 focus:outline-none focus:border-cyan-500 font-mono"
            />
            <p className="text-[10px] text-slate-500">Continuous detection probability heuristic</p>
          </div>

          {/* VIIRS Categorical Confidence Filter */}
          <div className="space-y-1.5">
            <div className="flex items-center gap-1.5">
              <SensorBadge sensor="VIIRS" size="sm" />
              <span className="text-slate-300 font-semibold">Allowed Levels:</span>
            </div>
            <div className="flex items-center gap-2 pt-0.5">
              {['low', 'nominal', 'high'].map((lvl) => {
                const active = (qualityFilters.allowed_viirs_confidence_levels || ['nominal', 'high']).includes(lvl);
                return (
                  <button
                    key={lvl}
                    type="button"
                    onClick={() => handleToggleViirsConfidence(lvl)}
                    className={clsx(
                      'px-2 py-0.5 rounded text-[10px] uppercase font-mono border transition-colors',
                      active
                        ? 'bg-cyan-950 text-cyan-300 border-cyan-700 font-bold'
                        : 'bg-slate-900 text-slate-500 border-slate-800'
                    )}
                  >
                    {lvl}
                  </button>
                );
              })}
            </div>
            <p className="text-[10px] text-slate-500">Discrete 375m I-band contextual classes</p>
          </div>
        </div>

        {/* Rule 8 Physics Note */}
        <div className="p-2.5 rounded bg-amber-950/30 border border-amber-900/60 text-amber-200 text-[11px] font-mono flex items-start gap-2">
          <AlertCircle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
          <span>
            <strong>Sensor Physics Rule 8:</strong> MODIS and VIIRS confidence fields have different product definitions and are filtered independently per sensor — never merged onto a single scale.
          </span>
        </div>
      </div>
    </div>
  );
}
