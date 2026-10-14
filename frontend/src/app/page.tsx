'use client';

import React from 'react';
import { useFixtureMode } from '@/lib/fixtures/FixtureContext';
import { FIXTURE_RUN_SUMMARY } from '@/lib/fixtures/labelledTestFixtures';
import { SensorBadge, MatchStatusBadge } from '@/components/common/Badges';
import { EmptyState } from '@/components/common/StateViews';
import { Flame, Sliders, Database, ArrowRight } from 'lucide-react';

export default function OverviewDashboardPage() {
  const { isFixtureMode } = useFixtureMode();

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Page Header */}
      <div className="border-b border-slate-800 pb-4 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-slate-100 flex items-center gap-2">
            <Flame className="w-5 h-5 text-amber-500" />
            Active-Fire Observation Overview
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Systematic cross-sensor comparison of Terra/Aqua MODIS and Suomi-NPP/NOAA-20 VIIRS hotspots.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <a
            href="/workspace"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-slate-950 bg-cyan-400 hover:bg-cyan-300 rounded shadow-sm transition-colors"
          >
            <Sliders className="w-3.5 h-3.5" />
            New Processing Run
          </a>
        </div>
      </div>

      {isFixtureMode ? (
        /* Fixture Mode Preview Cards */
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="p-4 rounded-lg bg-slate-900 border border-slate-800">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-mono text-slate-400">Total Valid MODIS</span>
                <SensorBadge sensor="MODIS" size="sm" />
              </div>
              <div className="text-2xl font-bold font-mono text-slate-100">
                {FIXTURE_RUN_SUMMARY.counts.modis_valid_rows}
              </div>
              <p className="text-[11px] text-slate-500 mt-1">~1km nominal nadir resolution</p>
            </div>

            <div className="p-4 rounded-lg bg-slate-900 border border-slate-800">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-mono text-slate-400">Total Valid VIIRS</span>
                <SensorBadge sensor="VIIRS" size="sm" />
              </div>
              <div className="text-2xl font-bold font-mono text-slate-100">
                {FIXTURE_RUN_SUMMARY.counts.viirs_valid_rows}
              </div>
              <p className="text-[11px] text-slate-500 mt-1">375m I-band nadir resolution</p>
            </div>

            <div className="p-4 rounded-lg bg-slate-900 border border-slate-800">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-mono text-slate-400">Matched Pairs</span>
                <MatchStatusBadge status="matched" size="sm" />
              </div>
              <div className="text-2xl font-bold font-mono text-emerald-400">
                {FIXTURE_RUN_SUMMARY.counts.matched_count}
              </div>
              <p className="text-[11px] text-slate-500 mt-1">Spatial &le; 1500m &amp; &Delta;t &le; 3600s</p>
            </div>

            <div className="p-4 rounded-lg bg-slate-900 border border-slate-800">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-mono text-slate-400">Ambiguous Cases</span>
                <MatchStatusBadge status="ambiguous" size="sm" />
              </div>
              <div className="text-2xl font-bold font-mono text-purple-400">
                {FIXTURE_RUN_SUMMARY.counts.ambiguous_count}
              </div>
              <p className="text-[11px] text-slate-500 mt-1">Multiple candidates retained</p>
            </div>
          </div>

          <div className="p-4 rounded-lg bg-slate-900 border border-slate-800 flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold text-slate-200">Latest Run: {FIXTURE_RUN_SUMMARY.run_id}</h3>
              <p className="text-xs text-slate-400 mt-0.5 font-mono">
                Method v{FIXTURE_RUN_SUMMARY.method_version} &bull; Policy: {FIXTURE_RUN_SUMMARY.parameters.ambiguity_policy}
              </p>
            </div>
            <a
              href="/map"
              className="inline-flex items-center gap-1 text-xs text-cyan-400 hover:text-cyan-300 font-medium"
            >
              Explore on Map <ArrowRight className="w-3.5 h-3.5" />
            </a>
          </div>
        </div>
      ) : (
        /* Default Empty State when connected to live backend before any runs are submitted */
        <EmptyState
          title="No Harmonisation Processing Runs Found"
          description="Connect and ingest MODIS and VIIRS CSV datasets or execute a spatial-temporal harmonisation run to view cross-sensor statistics. You can also toggle 'Fixture Preview' in the top header to inspect the UI layout."
          actionText="Open Harmonisation Workspace"
          onAction={() => {
            window.location.href = '/workspace';
          }}
          icon={<Database className="w-6 h-6 text-cyan-400" />}
        />
      )}
    </div>
  );
}
