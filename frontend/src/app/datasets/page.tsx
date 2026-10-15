'use client';

import React, { useEffect, useState } from 'react';
import { useFixtureMode } from '@/lib/fixtures/FixtureContext';
import { FIXTURE_DATASETS } from '@/lib/fixtures/labelledTestFixtures';
import { apiClient, ApiError } from '@/lib/api/client';
import { DatasetRecord, ValidationReport } from '@/types/harmonisation';
import { ProductSelectionTable } from '@/components/datasets/ProductSelectionTable';
import { DatasetUploadValidator } from '@/components/datasets/DatasetUploadValidator';
import { DatasetSchemaAndQualityDrawer } from '@/components/datasets/DatasetSchemaAndQualityDrawer';
import { ErrorAlert, LoadingState } from '@/components/common/StateViews';
import { Database, RefreshCw } from 'lucide-react';

export default function DatasetExplorerPage() {
  const { isFixtureMode } = useFixtureMode();

  const [loading, setLoading] = useState<boolean>(!isFixtureMode);
  const [error, setError] = useState<ApiError | null>(null);
  const [datasets, setDatasets] = useState<DatasetRecord[]>([]);

  const fetchDatasets = async () => {
    if (isFixtureMode) {
      setDatasets(FIXTURE_DATASETS);
      setLoading(false);
      setError(null);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const fetched = await apiClient.listDatasets();
      setDatasets(fetched);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err);
      } else {
        setError(
          new ApiError(
            0,
            '/datasets',
            'Failed to fetch registered datasets from backend service',
            'Verify the FastAPI server is running at http://localhost:8000 or toggle "Fixture Preview" to inspect UI layout.',
            err
          )
        );
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDatasets();
  }, [isFixtureMode]);

  const handleUploadSuccess = (report: ValidationReport) => {
    if (isFixtureMode) {
      return;
    }
    // Refresh datasets list after upload
    fetchDatasets();
  };

  const handleDeleteDataset = async (datasetId: string) => {
    if (isFixtureMode) {
      setDatasets((prev) => prev.filter((d) => d.id !== datasetId));
      return;
    }

    try {
      await apiClient.deleteDataset(datasetId);
      setDatasets((prev) => prev.filter((d) => d.id !== datasetId));
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err);
      }
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="border-b border-slate-800 pb-4 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold tracking-tight text-slate-100 flex items-center gap-2">
            <Database className="w-5 h-5 text-cyan-400" />
            Dataset Explorer &amp; Quality Control Pipeline
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Authoritative product specifications, CSV ingestion, coordinate validation, and schema mapping (FR-01 to FR-08).
          </p>
        </div>

        <div className="flex items-center gap-2">
          {!isFixtureMode && (
            <button
              onClick={fetchDatasets}
              disabled={loading}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-mono text-slate-300 bg-slate-900 hover:bg-slate-800 border border-slate-700 rounded transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
              Refresh Registry
            </button>
          )}
        </div>
      </div>

      {/* Error state if backend fails and not in fixture mode (Rule 5: No silent fallback) */}
      {!isFixtureMode && error && (
        <ErrorAlert
          title="Dataset Registry Connection Failed"
          error={error}
          onRetry={fetchDatasets}
        />
      )}

      {/* Loading state */}
      {loading && !isFixtureMode && (
        <LoadingState
          message="Querying registered satellite datasets..."
          subtext="Inspecting database schema and checksum tables."
        />
      )}

      {/* Section 1: Product Selection Specification Matrix */}
      <ProductSelectionTable />

      {/* Section 2: CSV Upload & Validation Engine (Stages A & B) */}
      <DatasetUploadValidator onUploadSuccess={handleUploadSuccess} />

      {/* Section 3: Registered Datasets & 17-Field Mapping Preview Drawer */}
      <DatasetSchemaAndQualityDrawer
        datasets={datasets}
        onDeleteDataset={handleDeleteDataset}
      />
    </div>
  );
}
