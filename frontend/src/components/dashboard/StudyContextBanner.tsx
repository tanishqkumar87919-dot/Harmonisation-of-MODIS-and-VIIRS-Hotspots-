'use client';

import React from 'react';
import { Calendar, Globe2, Layers, Cpu, Hash } from 'lucide-react';
import { ProcessingRunSummary } from '@/types/harmonisation';
import { SensorBadge } from '@/components/common/Badges';

interface StudyContextBannerProps {
  runSummary?: ProcessingRunSummary | null;
  regionName?: string;
  bbox?: [number, number, number, number] | null;
  timeRange?: { min: string | null; max: string | null };
  modisProduct?: string;
  viirsProduct?: string;
}

export function StudyContextBanner({
  runSummary,
  regionName = 'Indo-Gangetic Plain & Northern India',
  bbox = [74.5, 27.0, 80.5, 31.5],
  timeRange = { min: '2023-05-01 04:30:00 UTC', max: '2023-05-01 09:10:00 UTC' },
  modisProduct = 'MOD14 Collection 6.1 (Terra/Aqua 1km)',
  viirsProduct = 'VNP14IMGTDL Collection 1 (Suomi-NPP 375m)',
}: StudyContextBannerProps) {
  const formattedBbox = bbox
    ? `[${bbox[0].toFixed(2)}°E, ${bbox[1].toFixed(2)}°N to ${bbox[2].toFixed(2)}°E, ${bbox[3].toFixed(2)}°N]`
    : 'Bounding box unconstrained';

  return (
    <section
      aria-label="Study Area & Processing Run Context"
      className="rounded-lg border border-slate-800 bg-slate-900/80 p-4 shadow-sm backdrop-blur"
    >
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-3 mb-3">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded bg-cyan-950 border border-cyan-800 flex items-center justify-center text-cyan-400">
            <Globe2 className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-xs font-mono uppercase tracking-wider text-slate-400 font-semibold">
              Active Study Context &amp; Geospatial Extent
            </h3>
            <p className="text-sm font-bold text-slate-100 flex items-center gap-2">
              <span>{regionName}</span>
              <span className="text-xs font-mono font-normal text-cyan-400">
                {formattedBbox}
              </span>
            </p>
          </div>
        </div>

        {runSummary && (
          <div className="flex items-center gap-2 text-xs font-mono bg-slate-950 px-3 py-1.5 rounded border border-slate-800">
            <Hash className="w-3.5 h-3.5 text-slate-400" />
            <span className="text-slate-400">Active Run:</span>
            <span className="text-slate-200 font-semibold">{runSummary.run_id}</span>
            <span className="text-slate-500">|</span>
            <span className="text-cyan-400">v{runSummary.method_version}</span>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs font-mono">
        <div className="flex items-start gap-2 bg-slate-950/60 p-2.5 rounded border border-slate-800/60">
          <Calendar className="w-3.5 h-3.5 text-slate-400 flex-shrink-0 mt-0.5" />
          <div>
            <span className="text-[10px] text-slate-400 uppercase block">Observation Period</span>
            <span className="text-slate-200 font-medium">
              {timeRange.min || 'N/A'} &rarr; {timeRange.max || 'N/A'}
            </span>
          </div>
        </div>

        <div className="flex items-start gap-2 bg-slate-950/60 p-2.5 rounded border border-slate-800/60">
          <Cpu className="w-3.5 h-3.5 text-amber-500 flex-shrink-0 mt-0.5" />
          <div>
            <div className="flex items-center gap-1.5 mb-0.5">
              <span className="text-[10px] text-slate-400 uppercase">MODIS Target</span>
              <SensorBadge sensor="MODIS" size="sm" />
            </div>
            <span className="text-slate-200 truncate block text-[11px]" title={modisProduct}>
              {modisProduct}
            </span>
          </div>
        </div>

        <div className="flex items-start gap-2 bg-slate-950/60 p-2.5 rounded border border-slate-800/60">
          <Layers className="w-3.5 h-3.5 text-cyan-400 flex-shrink-0 mt-0.5" />
          <div>
            <div className="flex items-center gap-1.5 mb-0.5">
              <span className="text-[10px] text-slate-400 uppercase">VIIRS Target</span>
              <SensorBadge sensor="VIIRS" size="sm" />
            </div>
            <span className="text-slate-200 truncate block text-[11px]" title={viirsProduct}>
              {viirsProduct}
            </span>
          </div>
        </div>
      </div>
    </section>
  );
}
