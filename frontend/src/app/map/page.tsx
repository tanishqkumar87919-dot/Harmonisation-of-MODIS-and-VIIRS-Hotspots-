'use client';

import React, { Suspense, useEffect, useMemo, useState } from 'react';
import dynamic from 'next/dynamic';
import { useSearchParams } from 'next/navigation';
import { useFixtureMode } from '@/lib/fixtures/FixtureContext';
import {
  FIXTURE_HARMONISED_RECORDS,
  FIXTURE_RUN_SUMMARY,
} from '@/lib/fixtures/labelledTestFixtures';
import { apiClient, ApiError } from '@/lib/api/client';
import {
  HarmonisedRecord,
  MatchStatus,
  ProcessingRunSummary,
} from '@/types/harmonisation';
import { MapFilters, MapLayerAndFilterPanel } from '@/components/map/MapLayerAndFilterPanel';
import { PersistentMapLegend } from '@/components/map/PersistentMapLegend';
import { RecordProvenanceDrawer } from '@/components/map/RecordProvenanceDrawer';
import { EmptyState, ErrorAlert, LoadingState } from '@/components/common/StateViews';
import { Layers, Map as MapIcon, Sliders } from 'lucide-react';

// Dynamic import of HotspotMapCanvas with SSR disabled to prevent window/canvas hydration mismatch
const HotspotMapCanvas = dynamic(
  () => import('@/components/map/HotspotMapCanvas').then((mod) => mod.HotspotMapCanvas),
  {
    ssr: false,
    loading: () => (
      <div className="w-full h-full flex items-center justify-center bg-slate-950 rounded-lg border border-slate-800 text-xs font-mono text-slate-400">
        Initializing Geospatial Projection Engine (EPSG:4326)...
      </div>
    ),
  }
);

function MapPageContent() {
  const searchParams = useSearchParams();
  const urlRunId = searchParams.get('run_id');

  const { isFixtureMode } = useFixtureMode();

  // State
  const [loading, setLoading] = useState<boolean>(!isFixtureMode);
  const [error, setError] = useState<ApiError | null>(null);
  const [records, setRecords] = useState<HarmonisedRecord[]>([]);
  const [selectedRecord, setSelectedRecord] = useState<HarmonisedRecord | null>(null);

  // Active Map Layers
  const [activeLayers, setActiveLayers] = useState<Record<string, boolean>>({
    matched: true,
    unmatched_modis: true,
    unmatched_viirs: true,
    ambiguous: true,
    raw_modis: true,
    raw_viirs: true,
  });

  // Filters State
  const [filters, setFilters] = useState<MapFilters>({
    startDate: '',
    endDate: '',
    sensor: 'ALL',
    statuses: ['matched', 'unmatched_modis', 'unmatched_viirs', 'ambiguous'],
    regionPreset: 'all',
  });

  const fetchMapData = async () => {
    if (isFixtureMode) {
      setRecords(FIXTURE_HARMONISED_RECORDS);
      setLoading(false);
      setError(null);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Determine run ID: from URL or fetch latest run
      let targetRunId = urlRunId;
      if (!targetRunId) {
        const runs = await apiClient.listProcessingRuns();
        if (runs.length > 0) {
          targetRunId = runs[0].run_id;
        }
      }

      if (!targetRunId) {
        setRecords([]);
        setLoading(false);
        return;
      }

      const [matches, unmatched] = await Promise.all([
        apiClient.getRunMatches(targetRunId),
        apiClient.getRunUnmatched(targetRunId),
      ]);

      setRecords([...matches, ...unmatched]);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err);
      } else {
        setError(
          new ApiError(
            0,
            '/runs/matches',
            'Failed to load spatial observation features',
            'Ensure backend is reachable or enable "Fixture Preview" to inspect the map viewer.',
            err
          )
        );
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMapData();
  }, [urlRunId, isFixtureMode]);

  // Synchronized Filter Logic (08_UI_UX_DESIGN.md Section 6: Live Count Agreement)
  const filteredRecords = useMemo(() => {
    return records.filter((rec) => {
      // Status filter
      if (!filters.statuses.includes(rec.match_status)) {
        return false;
      }

      // Sensor filter
      if (filters.sensor === 'MODIS' && rec.match_status === 'unmatched_viirs') {
        return false;
      }
      if (filters.sensor === 'VIIRS' && rec.match_status === 'unmatched_modis') {
        return false;
      }

      // Date range filter
      if (filters.startDate) {
        const startTime = new Date(filters.startDate).getTime();
        const obsTime =
          rec.modis_observation?.observation_time_utc ||
          rec.viirs_observation?.observation_time_utc;
        if (obsTime && new Date(obsTime).getTime() < startTime) return false;
      }

      if (filters.endDate) {
        const endTime = new Date(filters.endDate).getTime() + 86400000;
        const obsTime =
          rec.modis_observation?.observation_time_utc ||
          rec.viirs_observation?.observation_time_utc;
        if (obsTime && new Date(obsTime).getTime() > endTime) return false;
      }

      return true;
    });
  }, [records, filters]);

  // Exact counts computed directly from filteredRecords
  const filteredCounts = useMemo(() => {
    let matched = 0;
    let unmatched_modis = 0;
    let unmatched_viirs = 0;
    let ambiguous = 0;

    filteredRecords.forEach((r) => {
      if (r.match_status === 'matched') matched++;
      else if (r.match_status === 'unmatched_modis') unmatched_modis++;
      else if (r.match_status === 'unmatched_viirs') unmatched_viirs++;
      else if (r.match_status === 'ambiguous') ambiguous++;
    });

    return {
      total: filteredRecords.length,
      matched,
      unmatched_modis,
      unmatched_viirs,
      ambiguous,
    };
  }, [filteredRecords]);

  const handleToggleLayer = (layerKey: string) => {
    setActiveLayers((prev) => ({
      ...prev,
      [layerKey]: !prev[layerKey],
    }));
  };

  const handleResetFilters = () => {
    setFilters({
      startDate: '',
      endDate: '',
      sensor: 'ALL',
      statuses: ['matched', 'unmatched_modis', 'unmatched_viirs', 'ambiguous'],
      regionPreset: 'all',
    });
  };

  return (
    <div className="space-y-4 max-w-7xl mx-auto h-[calc(100vh-6rem)] flex flex-col justify-between">
      {/* Map Filter & Layer Telemetry Panel */}
      <MapLayerAndFilterPanel
        filters={filters}
        onChangeFilters={setFilters}
        activeLayers={activeLayers}
        onToggleLayer={handleToggleLayer}
        filteredCounts={filteredCounts}
        onResetFilters={handleResetFilters}
      />

      {/* Error state if backend fails and not in fixture mode (Rule 5: No silent fallback) */}
      {!isFixtureMode && error && (
        <ErrorAlert
          title="Geospatial Telemetry Retrieval Failed"
          error={error}
          onRetry={fetchMapData}
        />
      )}

      {/* Loading state */}
      {loading && !isFixtureMode && (
        <LoadingState
          message="Querying geospatial features and candidate linkages..."
          subtext="Rendering vector geometries in EPSG:4326."
        />
      )}

      {/* Map Viewport Area */}
      {!loading && !error && (
        <div className="flex-1 relative min-h-[480px] w-full">
          {records.length === 0 ? (
            <div className="h-full flex items-center justify-center bg-slate-900 border border-slate-800 rounded-lg">
              <EmptyState
                title="No Geospatial Hotspot Records Found"
                description="To view active fire detections on the map, execute a processing run in the Harmonisation Workspace or toggle 'Fixture Preview' in the header."
                actionText="Open Harmonisation Workspace"
                onAction={() => {
                  window.location.href = '/workspace';
                }}
                icon={<MapIcon className="w-6 h-6 text-cyan-400" />}
              />
            </div>
          ) : (
            <>
              {/* Interactive Vector Map Canvas */}
              <HotspotMapCanvas
                records={filteredRecords}
                activeLayers={activeLayers}
                onSelectRecord={setSelectedRecord}
                selectedRecordId={selectedRecord?.harmonisation_id}
                className="h-full w-full"
              />

              {/* Persistent Docked Legend (FR-16) */}
              <PersistentMapLegend
                counts={filteredCounts}
                activeLayers={activeLayers}
                onToggleLayer={handleToggleLayer}
              />
            </>
          )}

          {/* Record-Level Provenance Inspection Drawer (FR-18) */}
          <RecordProvenanceDrawer
            record={selectedRecord}
            onClose={() => setSelectedRecord(null)}
          />
        </div>
      )}
    </div>
  );
}

export default function InteractiveMapPage() {
  return (
    <Suspense
      fallback={
        <div className="p-12 text-center font-mono text-xs text-slate-400">
          Loading Map Explorer View...
        </div>
      }
    >
      <MapPageContent />
    </Suspense>
  );
}
