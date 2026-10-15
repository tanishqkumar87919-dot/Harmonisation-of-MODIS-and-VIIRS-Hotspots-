'use client';

import React from 'react';
import { ProcessingRunSummary } from '@/types/harmonisation';
import { MatchStatusBadge, QualityStatusBadge, SensorBadge } from '@/components/common/Badges';
import { MATCH_STATUS_CONFIGS, SENSOR_CONFIGS } from '@/lib/constants/design';
import { HelpCircle, Info, ShieldCheck } from 'lucide-react';

interface QualityAndMatchKpiGridProps {
  summary: ProcessingRunSummary;
}

export function QualityAndMatchKpiGrid({ summary }: QualityAndMatchKpiGridProps) {
  const { counts, rates } = summary;

  // Proportional breakdown calculations
  const totalHarmonisedRecords =
    counts.matched_count +
    counts.unmatched_modis_count +
    counts.unmatched_viirs_count +
    counts.ambiguous_count;

  const matchedPercent = totalHarmonisedRecords > 0 ? (counts.matched_count / totalHarmonisedRecords) * 100 : 0;
  const unmatchedModisPercent =
    totalHarmonisedRecords > 0 ? (counts.unmatched_modis_count / totalHarmonisedRecords) * 100 : 0;
  const unmatchedViirsPercent =
    totalHarmonisedRecords > 0 ? (counts.unmatched_viirs_count / totalHarmonisedRecords) * 100 : 0;
  const ambiguousPercent = totalHarmonisedRecords > 0 ? (counts.ambiguous_count / totalHarmonisedRecords) * 100 : 0;

  return (
    <div className="space-y-4">
      {/* Three Primary Cards Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Card 1: MODIS Ingestion & Quality Breakdown */}
        <div className="rounded-lg border border-slate-800 bg-slate-900 p-4 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <SensorBadge sensor="MODIS" size="md" />
                <span className="text-xs font-mono text-slate-400">Terra &amp; Aqua</span>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-950/60 text-amber-300 border border-amber-800">
                1 km Nadir
              </span>
            </div>

            <div className="flex items-baseline justify-between mb-2">
              <div>
                <span className="text-3xl font-extrabold font-mono text-slate-100">
                  {counts.modis_input_rows.toLocaleString()}
                </span>
                <span className="text-xs text-slate-400 ml-2">Total Ingested Rows</span>
              </div>
            </div>

            <p className="text-xs text-slate-400 font-mono mb-4">
              Match Rate: <strong className="text-emerald-400 font-bold">{(rates.modis_match_rate * 100).toFixed(1)}%</strong>
            </p>
          </div>

          <div className="grid grid-cols-3 gap-2 pt-3 border-t border-slate-800/80 font-mono text-xs text-center">
            <div className="bg-slate-950/80 p-2 rounded border border-slate-800/60">
              <div className="text-[10px] text-slate-400 flex items-center justify-center gap-1">
                <QualityStatusBadge status="valid" size="sm" />
              </div>
              <div className="font-bold text-emerald-400 mt-1">{counts.modis_valid_rows}</div>
            </div>

            <div className="bg-slate-950/80 p-2 rounded border border-slate-800/60">
              <div className="text-[10px] text-slate-400 flex items-center justify-center gap-1">
                <QualityStatusBadge status="warning" size="sm" />
              </div>
              <div className="font-bold text-amber-400 mt-1">{counts.modis_warning_rows}</div>
            </div>

            <div className="bg-slate-950/80 p-2 rounded border border-slate-800/60">
              <div className="text-[10px] text-slate-400 flex items-center justify-center gap-1">
                <QualityStatusBadge status="rejected" size="sm" />
              </div>
              <div className="font-bold text-slate-400 mt-1">{counts.modis_rejected_rows}</div>
            </div>
          </div>
        </div>

        {/* Card 2: VIIRS Ingestion & Quality Breakdown */}
        <div className="rounded-lg border border-slate-800 bg-slate-900 p-4 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <SensorBadge sensor="VIIRS" size="md" />
                <span className="text-xs font-mono text-slate-400">Suomi-NPP &amp; NOAA</span>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-950/60 text-cyan-300 border border-cyan-800">
                375m I-Band
              </span>
            </div>

            <div className="flex items-baseline justify-between mb-2">
              <div>
                <span className="text-3xl font-extrabold font-mono text-slate-100">
                  {counts.viirs_input_rows.toLocaleString()}
                </span>
                <span className="text-xs text-slate-400 ml-2">Total Ingested Rows</span>
              </div>
            </div>

            <p className="text-xs text-slate-400 font-mono mb-4">
              Match Rate: <strong className="text-cyan-400 font-bold">{(rates.viirs_match_rate * 100).toFixed(1)}%</strong>
            </p>
          </div>

          <div className="grid grid-cols-3 gap-2 pt-3 border-t border-slate-800/80 font-mono text-xs text-center">
            <div className="bg-slate-950/80 p-2 rounded border border-slate-800/60">
              <div className="text-[10px] text-slate-400 flex items-center justify-center gap-1">
                <QualityStatusBadge status="valid" size="sm" />
              </div>
              <div className="font-bold text-emerald-400 mt-1">{counts.viirs_valid_rows}</div>
            </div>

            <div className="bg-slate-950/80 p-2 rounded border border-slate-800/60">
              <div className="text-[10px] text-slate-400 flex items-center justify-center gap-1">
                <QualityStatusBadge status="warning" size="sm" />
              </div>
              <div className="font-bold text-amber-400 mt-1">{counts.viirs_warning_rows}</div>
            </div>

            <div className="bg-slate-950/80 p-2 rounded border border-slate-800/60">
              <div className="text-[10px] text-slate-400 flex items-center justify-center gap-1">
                <QualityStatusBadge status="rejected" size="sm" />
              </div>
              <div className="font-bold text-slate-400 mt-1">{counts.viirs_rejected_rows}</div>
            </div>
          </div>
        </div>

        {/* Card 3: Harmonisation Outcome Breakdown */}
        <div className="rounded-lg border border-slate-800 bg-slate-900 p-4 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-mono uppercase tracking-wider text-slate-400 font-semibold">
                Harmonised Outcome Records
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                {totalHarmonisedRecords.toLocaleString()} Total Output Rows
              </span>
            </div>

            {/* Proportional Stacked Segment Bar */}
            <div className="w-full h-3 rounded-full bg-slate-950 overflow-hidden flex mb-4 border border-slate-800 shadow-inner">
              <div
                style={{ width: `${matchedPercent}%`, backgroundColor: MATCH_STATUS_CONFIGS.matched.color }}
                title={`Matched: ${counts.matched_count} (${matchedPercent.toFixed(1)}%)`}
              />
              <div
                style={{
                  width: `${unmatchedModisPercent}%`,
                  backgroundColor: MATCH_STATUS_CONFIGS.unmatched_modis.color,
                }}
                title={`Unmatched MODIS: ${counts.unmatched_modis_count} (${unmatchedModisPercent.toFixed(1)}%)`}
              />
              <div
                style={{
                  width: `${unmatchedViirsPercent}%`,
                  backgroundColor: MATCH_STATUS_CONFIGS.unmatched_viirs.color,
                }}
                title={`Unmatched VIIRS: ${counts.unmatched_viirs_count} (${unmatchedViirsPercent.toFixed(1)}%)`}
              />
              <div
                style={{ width: `${ambiguousPercent}%`, backgroundColor: MATCH_STATUS_CONFIGS.ambiguous.color }}
                title={`Ambiguous: ${counts.ambiguous_count} (${ambiguousPercent.toFixed(1)}%)`}
              />
            </div>
          </div>

          {/* Breakdown Items with exact counts & accessible symbols */}
          <div className="grid grid-cols-2 gap-2 text-xs font-mono">
            <div className="p-2 rounded bg-slate-950/80 border border-slate-800/60 flex items-center justify-between">
              <MatchStatusBadge status="matched" size="sm" />
              <span className="font-bold text-slate-100">{counts.matched_count}</span>
            </div>
            <div className="p-2 rounded bg-slate-950/80 border border-slate-800/60 flex items-center justify-between">
              <MatchStatusBadge status="ambiguous" size="sm" />
              <span className="font-bold text-slate-100">{counts.ambiguous_count}</span>
            </div>
            <div className="p-2 rounded bg-slate-950/80 border border-slate-800/60 flex items-center justify-between">
              <MatchStatusBadge status="unmatched_modis" size="sm" />
              <span className="font-bold text-slate-100">{counts.unmatched_modis_count}</span>
            </div>
            <div className="p-2 rounded bg-slate-950/80 border border-slate-800/60 flex items-center justify-between">
              <MatchStatusBadge status="unmatched_viirs" size="sm" />
              <span className="font-bold text-slate-100">{counts.unmatched_viirs_count}</span>
            </div>
          </div>
        </div>
      </div>

      {/* FR-17 Explicit Counting Method and Mathematical Denominator Callout */}
      <section
        aria-label="Scientific Counting Method and Mathematical Formulations"
        className="rounded-lg border border-cyan-900/60 bg-cyan-950/30 p-4 text-xs text-slate-300 space-y-2.5 font-mono shadow-sm"
      >
        <div className="flex items-center gap-2 text-cyan-300 font-bold">
          <Info className="w-4 h-4 flex-shrink-0" />
          <span>Scientific Counting Methodology &amp; Mathematical Rate Definitions (FR-17)</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1 text-[11px] text-slate-300 leading-relaxed">
          <div className="p-2.5 rounded bg-slate-950/60 border border-slate-800/80 space-y-1">
            <span className="text-cyan-400 font-bold block">1. Record Identity &amp; Linkage Principle:</span>
            <p>
              Each <strong className="text-emerald-300">Matched</strong> record links exactly 1 valid MODIS observation and 1 valid VIIRS observation that fall within the configured thresholds (&Delta;d &le; {summary.parameters.max_distance_meters} m, &Delta;t &le; {summary.parameters.max_time_difference_seconds} s).
              Unmatched records are never discarded (<strong className="text-amber-300">FR-12</strong>).
            </p>
          </div>

          <div className="p-2.5 rounded bg-slate-950/60 border border-slate-800/80 space-y-1">
            <span className="text-cyan-400 font-bold block">2. Match Rate Denominator Formulations:</span>
            <div className="space-y-1 text-slate-300">
              <div>
                <span className="text-slate-400">&bull; MODIS Match Rate:</span>{' '}
                <span className="text-slate-100 font-semibold">{rates.modis_match_rate_denominator}</span>{' '}
                &rarr; <span className="text-emerald-400 font-bold">{(rates.modis_match_rate * 100).toFixed(2)}%</span>
              </div>
              <div>
                <span className="text-slate-400">&bull; VIIRS Match Rate:</span>{' '}
                <span className="text-slate-100 font-semibold">{rates.viirs_match_rate_denominator}</span>{' '}
                &rarr; <span className="text-cyan-400 font-bold">{(rates.viirs_match_rate * 100).toFixed(2)}%</span>
              </div>
              <div>
                <span className="text-slate-400">&bull; Ambiguity Rate:</span>{' '}
                <span className="text-slate-100 font-semibold">{rates.ambiguity_rate_denominator}</span>{' '}
                &rarr; <span className="text-purple-400 font-bold">{(rates.ambiguity_rate * 100).toFixed(2)}%</span>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
