'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/navigation';
import { usePathname } from 'next/navigation';
import {
  BarChart3,
  BookOpen,
  CheckSquare,
  Database,
  Download,
  Flame,
  LayoutDashboard,
  Map as MapIcon,
  Server,
  Sliders,
  TestTube,
} from 'lucide-react';
import clsx from 'clsx';
import { TestFixtureBanner } from '@/components/common/StateViews';
import { useFixtureMode } from '@/lib/fixtures/FixtureContext';
import { apiClient } from '@/lib/api/client';
import { SENSOR_CONFIGS } from '@/lib/constants/design';

interface NavItem {
  href: string;
  label: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
}

const NAV_ITEMS: NavItem[] = [
  {
    href: '/',
    label: 'Overview Dashboard',
    description: 'Key metrics, run statuses, and observational counts',
    icon: LayoutDashboard,
  },
  {
    href: '/datasets',
    label: 'Dataset Explorer',
    description: 'Inspect schemas, coordinate bounds, and QC audits',
    icon: Database,
  },
  {
    href: '/workspace',
    label: 'Harmonisation Workspace',
    description: 'Configure spatial/temporal thresholds & launch runs',
    icon: Sliders,
  },
  {
    href: '/map',
    label: 'Interactive Map',
    description: '6-layer geospatial viewer with provenance drawer',
    icon: MapIcon,
  },
  {
    href: '/comparison',
    label: 'Sensor Comparison',
    description: 'MODIS vs VIIRS distributions and delta histograms',
    icon: BarChart3,
  },
  {
    href: '/validation',
    label: 'Validation & Sensitivity',
    description: 'Multi-threshold sensitivity and baseline comparisons',
    icon: CheckSquare,
  },
  {
    href: '/exports',
    label: 'Reports & Exports',
    description: 'Export reproducible CSV & GeoJSON with provenance',
    icon: Download,
  },
  {
    href: '/methodology',
    label: 'Methodology & Data Info',
    description: 'Scientific principles, data dictionary, and caveats',
    icon: BookOpen,
  },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { isFixtureMode, toggleFixtureMode } = useFixtureMode();
  const [backendStatus, setBackendStatus] = useState<'checking' | 'online' | 'offline'>('checking');

  useEffect(() => {
    let isMounted = true;
    apiClient
      .checkHealth()
      .then(() => {
        if (isMounted) setBackendStatus('online');
      })
      .catch(() => {
        if (isMounted) setBackendStatus('offline');
      });

    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans antialiased selection:bg-cyan-500 selection:text-slate-950">
      {/* Test Fixture Banner - Persistent and Non-dismissible if active */}
      <TestFixtureBanner active={isFixtureMode} onDisable={toggleFixtureMode} />

      {/* Top Application Context Bar */}
      <header className="h-14 border-b border-slate-800 bg-slate-900/90 backdrop-blur px-4 flex items-center justify-between sticky top-0 z-40">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded bg-gradient-to-br from-amber-500 to-cyan-600 flex items-center justify-center shadow-sm">
            <Flame className="w-5 h-5 text-slate-950 fill-current" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-sm font-semibold tracking-tight text-slate-100">
                Harmonisation of MODIS &amp; VIIRS Hotspots
              </h1>
              <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300">
                v1.0.0-scientific
              </span>
            </div>
            <p className="text-[11px] text-slate-400 hidden sm:block">
              Reproducible Earth Observation Processing &amp; Cross-Sensor Matching Engine
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Backend Connection Indicator */}
          <div
            className={clsx(
              'flex items-center gap-1.5 text-xs font-mono px-2 py-1 rounded border',
              backendStatus === 'online'
                ? 'bg-emerald-950/40 border-emerald-800 text-emerald-300'
                : backendStatus === 'offline'
                ? 'bg-red-950/40 border-red-800 text-red-300'
                : 'bg-slate-800 border-slate-700 text-slate-400'
            )}
            title={
              backendStatus === 'online'
                ? 'FastAPI Backend online at http://localhost:8000'
                : 'Backend unreachable. Toggle Fixture Mode below for UI preview.'
            }
          >
            <Server className="w-3.5 h-3.5" />
            <span className="hidden md:inline">API:</span>
            <span className="font-semibold uppercase text-[10px]">
              {backendStatus}
            </span>
          </div>

          {/* Test Fixture Mode Switch */}
          <button
            onClick={toggleFixtureMode}
            type="button"
            className={clsx(
              'flex items-center gap-1.5 text-xs font-mono px-2.5 py-1 rounded border transition-colors focus:outline-none focus:ring-2 focus:ring-amber-500',
              isFixtureMode
                ? 'bg-amber-500 text-slate-950 border-amber-400 font-bold shadow-sm'
                : 'bg-slate-800 hover:bg-slate-700 text-slate-300 border-slate-700'
            )}
            title="Toggle deterministic test fixtures for UI inspection without backend connection"
          >
            <TestTube className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Fixture Preview</span>
            <span
              className={clsx(
                'w-1.5 h-1.5 rounded-full',
                isFixtureMode ? 'bg-slate-950 animate-ping' : 'bg-slate-500'
              )}
            />
          </button>
        </div>
      </header>

      {/* Main App Layout */}
      <div className="flex-1 flex overflow-hidden">
        {/* Accessible Navigation Sidebar */}
        <aside
          aria-label="Application Navigation"
          className="w-64 border-r border-slate-800 bg-slate-900/60 flex flex-col justify-between hidden md:flex"
        >
          <nav className="p-3 space-y-1 overflow-y-auto">
            <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400 px-3 py-1.5 font-semibold">
              Scientific Modules
            </div>
            {NAV_ITEMS.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;
              return (
                <a
                  key={item.href}
                  href={item.href}
                  className={clsx(
                    'flex items-center gap-2.5 px-3 py-2 rounded-md text-xs font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-cyan-500',
                    isActive
                      ? 'bg-cyan-950/60 text-cyan-200 border border-cyan-800/60 font-semibold'
                      : 'text-slate-300 hover:bg-slate-800/80 hover:text-slate-100'
                  )}
                  title={item.description}
                >
                  <Icon
                    className={clsx(
                      'w-4 h-4 flex-shrink-0',
                      isActive ? 'text-cyan-400' : 'text-slate-400'
                    )}
                  />
                  <span>{item.label}</span>
                </a>
              );
            })}
          </nav>

          {/* Persistent Color & Symbol Legend in Sidebar */}
          <div className="p-3 border-t border-slate-800/80 bg-slate-950/40 text-[11px] font-mono">
            <div className="text-[10px] uppercase tracking-wider text-slate-400 font-semibold mb-2">
              Sensor Color Standard
            </div>
            <div className="space-y-1.5">
              <div className="flex items-center justify-between text-slate-300">
                <span className="flex items-center gap-1.5">
                  <span
                    className="w-2.5 h-2.5 rounded-sm inline-block"
                    style={{ backgroundColor: SENSOR_CONFIGS.MODIS.color }}
                  />
                  MODIS (~1km)
                </span>
                <span className="text-slate-500">Terra/Aqua</span>
              </div>
              <div className="flex items-center justify-between text-slate-300">
                <span className="flex items-center gap-1.5">
                  <span
                    className="w-2.5 h-2.5 inline-block"
                    style={{
                      borderLeft: '5px solid transparent',
                      borderRight: '5px solid transparent',
                      borderBottom: `8px solid ${SENSOR_CONFIGS.VIIRS.color}`,
                    }}
                  />
                  VIIRS (375m)
                </span>
                <span className="text-slate-500">SNPP/NOAA</span>
              </div>
            </div>
          </div>
        </aside>

        {/* Primary Viewport */}
        <main className="flex-1 overflow-y-auto p-4 md:p-6 bg-slate-950 focus:outline-none" tabIndex={-1}>
          {children}
        </main>
      </div>
    </div>
  );
}
