'use client';

import React, { useState } from 'react';
import { SensorType, ValidationReport } from '@/types/harmonisation';
import { apiClient, ApiError } from '@/lib/api/client';
import { useFixtureMode } from '@/lib/fixtures/FixtureContext';
import { FIXTURE_VALIDATION_REPORT } from '@/lib/fixtures/labelledTestFixtures';
import { SensorBadge } from '@/components/common/Badges';
import { ErrorAlert, PartialResultBanner } from '@/components/common/StateViews';
import {
  AlertCircle,
  AlertTriangle,
  CheckCircle2,
  FileSpreadsheet,
  FileWarning,
  Loader2,
  UploadCloud,
  XCircle,
} from 'lucide-react';
import clsx from 'clsx';

interface DatasetUploadValidatorProps {
  onUploadSuccess?: (report: ValidationReport) => void;
}

export function DatasetUploadValidator({ onUploadSuccess }: DatasetUploadValidatorProps) {
  const { isFixtureMode } = useFixtureMode();

  // Form State
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [sensor, setSensor] = useState<SensorType>('MODIS');
  const [productName, setProductName] = useState<string>('MOD14');
  const [productVersion, setProductVersion] = useState<string>('C6.1');
  const [sourceUri, setSourceUri] = useState<string>('https://firms.modaps.eosdis.nasa.gov');
  const [retrievedAt, setRetrievedAt] = useState<string>(new Date().toISOString().slice(0, 16));

  // UI States
  const [clientFileError, setClientFileError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [apiError, setApiError] = useState<ApiError | null>(null);
  const [validationReport, setValidationReport] = useState<ValidationReport | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setClientFileError(null);
    setApiError(null);
    const files = e.target.files;
    if (!files || files.length === 0) {
      setSelectedFile(null);
      return;
    }

    const file = files[0];
    // FR-01 & FR-03 Client-side extension validation
    const isCsv = file.name.toLowerCase().endsWith('.csv');
    if (!isCsv) {
      setClientFileError(
        `Rejected unsupported file "${file.name}". The system currently accepts only valid CSV formatted hotspot tables (FR-01, FR-03).`
      );
      setSelectedFile(null);
      e.target.value = '';
      return;
    }

    setSelectedFile(file);
  };

  const handleSensorChange = (newSensor: SensorType) => {
    setSensor(newSensor);
    if (newSensor === 'MODIS') {
      setProductName('MOD14');
      setProductVersion('C6.1');
    } else {
      setProductName('VNP14IMGTDL');
      setProductVersion('v1.0');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setClientFileError(null);
    setApiError(null);

    if (!selectedFile && !isFixtureMode) {
      setClientFileError('Please select a valid CSV file to upload and validate.');
      return;
    }

    setIsSubmitting(true);

    if (isFixtureMode) {
      // Simulate validation in fixture preview mode
      setTimeout(() => {
        setValidationReport(FIXTURE_VALIDATION_REPORT);
        setIsSubmitting(false);
        if (onUploadSuccess) onUploadSuccess(FIXTURE_VALIDATION_REPORT);
      }, 600);
      return;
    }

    const formData = new FormData();
    if (selectedFile) {
      formData.append('file', selectedFile);
    }
    formData.append('sensor', sensor);
    formData.append('product_name', productName);
    formData.append('product_version', productVersion);
    formData.append('source_uri', sourceUri);
    formData.append('retrieved_at', new Date(retrievedAt).toISOString());

    try {
      const report = await apiClient.validateAndUploadDataset(formData);
      setValidationReport(report);
      if (onUploadSuccess) onUploadSuccess(report);
    } catch (err) {
      if (err instanceof ApiError) {
        setApiError(err);
      } else {
        setApiError(
          new ApiError(
            0,
            '/datasets/validate',
            'File validation request failed',
            'Ensure the FastAPI backend is running and the file is accessible.',
            err
          )
        );
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900 p-5 shadow-sm space-y-6">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <UploadCloud className="w-5 h-5 text-cyan-400" />
          <h3 className="text-sm font-semibold text-slate-100">
            Dataset Ingestion &amp; Quality Control Validator (Stages A &amp; B)
          </h3>
        </div>
        <span className="text-xs font-mono text-slate-400">
          Enforces FR-01, FR-02, FR-03, FR-05, FR-06
        </span>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Sensor Selection Radios */}
        <div>
          <label className="block text-xs font-mono text-slate-300 mb-2">
            1. Select Target Sensor (FR-02)
          </label>
          <div className="flex items-center gap-4">
            <label className="flex items-center gap-2 cursor-pointer p-2 rounded bg-slate-950 border border-slate-800 hover:border-slate-700">
              <input
                type="radio"
                name="sensor"
                value="MODIS"
                checked={sensor === 'MODIS'}
                onChange={() => handleSensorChange('MODIS')}
                className="text-amber-500 focus:ring-amber-500"
              />
              <SensorBadge sensor="MODIS" size="sm" />
              <span className="text-xs text-slate-300 font-mono">MODIS (1 km nominal)</span>
            </label>

            <label className="flex items-center gap-2 cursor-pointer p-2 rounded bg-slate-950 border border-slate-800 hover:border-slate-700">
              <input
                type="radio"
                name="sensor"
                value="VIIRS"
                checked={sensor === 'VIIRS'}
                onChange={() => handleSensorChange('VIIRS')}
                className="text-cyan-500 focus:ring-cyan-500"
              />
              <SensorBadge sensor="VIIRS" size="sm" />
              <span className="text-xs text-slate-300 font-mono">VIIRS (375 m I-band)</span>
            </label>
          </div>
        </div>

        {/* Product Metadata Inputs (FR-02) */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3 text-xs font-mono">
          <div>
            <label className="block text-slate-400 mb-1">Product Short Name</label>
            <input
              type="text"
              value={productName}
              onChange={(e) => setProductName(e.target.value)}
              required
              placeholder="e.g. MOD14 or VNP14IMGTDL"
              className="w-full bg-slate-950 border border-slate-700 rounded p-2 text-slate-100 focus:border-cyan-500 focus:outline-none"
            />
          </div>

          <div>
            <label className="block text-slate-400 mb-1">Product Version</label>
            <input
              type="text"
              value={productVersion}
              onChange={(e) => setProductVersion(e.target.value)}
              required
              placeholder="e.g. C6.1 or v1.0"
              className="w-full bg-slate-950 border border-slate-700 rounded p-2 text-slate-100 focus:border-cyan-500 focus:outline-none"
            />
          </div>

          <div>
            <label className="block text-slate-400 mb-1">Source Download Endpoint</label>
            <input
              type="text"
              value={sourceUri}
              onChange={(e) => setSourceUri(e.target.value)}
              required
              placeholder="e.g. NASA FIRMS URL"
              className="w-full bg-slate-950 border border-slate-700 rounded p-2 text-slate-100 focus:border-cyan-500 focus:outline-none"
            />
          </div>

          <div>
            <label className="block text-slate-400 mb-1">Retrieval Timestamp (UTC)</label>
            <input
              type="datetime-local"
              value={retrievedAt}
              onChange={(e) => setRetrievedAt(e.target.value)}
              required
              className="w-full bg-slate-950 border border-slate-700 rounded p-2 text-slate-100 focus:border-cyan-500 focus:outline-none"
            />
          </div>
        </div>

        {/* File Drop / Select Area */}
        <div>
          <label className="block text-xs font-mono text-slate-300 mb-1">
            2. Choose Hotspot CSV File (FR-01)
          </label>
          <div className="flex items-center gap-3">
            <input
              type="file"
              accept=".csv"
              onChange={handleFileChange}
              className="text-xs font-mono text-slate-300 file:mr-4 file:py-2 file:px-3 file:rounded file:border-0 file:text-xs file:font-semibold file:bg-cyan-600 file:text-slate-950 hover:file:bg-cyan-500 cursor-pointer bg-slate-950 p-1.5 rounded border border-slate-800 flex-1"
            />
            <button
              type="submit"
              disabled={isSubmitting || (!selectedFile && !isFixtureMode)}
              className="px-4 py-2 bg-cyan-500 hover:bg-cyan-400 disabled:opacity-50 text-slate-950 font-semibold text-xs rounded transition-colors flex items-center gap-2 shadow-sm font-mono"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Validating Quality...
                </>
              ) : (
                <>
                  <UploadCloud className="w-4 h-4" />
                  Validate &amp; Ingest Dataset
                </>
              )}
            </button>
          </div>
          {isFixtureMode && (
            <p className="text-[11px] text-amber-400 mt-1 font-mono">
              Fixture Mode Active: Submitting triggers deterministic QC validation simulation.
            </p>
          )}
        </div>
      </form>

      {/* Client-Side File Type Error (FR-03) */}
      {clientFileError && (
        <div className="p-3 rounded bg-red-950/60 border border-red-800 text-red-200 text-xs font-mono flex items-start gap-2">
          <FileWarning className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
          <span>{clientFileError}</span>
        </div>
      )}

      {/* API Failure (Rule 5) */}
      {apiError && (
        <ErrorAlert
          title="Validation Engine Failure"
          error={apiError}
          onRetry={() => setApiError(null)}
        />
      )}

      {/* Validation Quality Report (FR-05, FR-06, FR-20) */}
      {validationReport && (
        <div className="rounded-lg border border-slate-700 bg-slate-950 p-4 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <h4 className="text-xs font-mono font-bold uppercase text-slate-200">
                Quality Control Audit Report: {validationReport.dataset_id}
              </h4>
            </div>
            <span className="text-[10px] font-mono text-slate-400">
              Total Ingested: {validationReport.total_input_rows} rows
            </span>
          </div>

          {/* KPI Counters */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs font-mono text-center">
            <div className="p-2 rounded bg-slate-900 border border-slate-800">
              <span className="text-[10px] text-slate-400 uppercase block">Total Input</span>
              <span className="text-base font-bold text-slate-100">{validationReport.total_input_rows}</span>
            </div>
            <div className="p-2 rounded bg-slate-900 border border-emerald-900/60">
              <span className="text-[10px] text-emerald-400 uppercase block">Valid Passed</span>
              <span className="text-base font-bold text-emerald-400">{validationReport.valid_count}</span>
            </div>
            <div className="p-2 rounded bg-slate-900 border border-amber-900/60">
              <span className="text-[10px] text-amber-400 uppercase block">Warnings Retained</span>
              <span className="text-base font-bold text-amber-400">{validationReport.warning_count}</span>
            </div>
            <div className="p-2 rounded bg-slate-900 border border-red-900/60">
              <span className="text-[10px] text-red-400 uppercase block">Rejected Excluded</span>
              <span className="text-base font-bold text-red-400">{validationReport.rejected_count}</span>
            </div>
          </div>

          {/* Specific QC Failure Breakdown (FR-06) */}
          <div className="p-3 rounded bg-slate-900 border border-slate-800 space-y-2 text-xs font-mono">
            <span className="text-slate-300 font-semibold block text-[11px]">
              Detailed QC Integrity Checks:
            </span>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-[11px]">
              <div className="flex justify-between p-1.5 rounded bg-slate-950">
                <span className="text-slate-400">Missing Coordinates:</span>
                <span className={validationReport.missing_coordinate_count > 0 ? 'text-red-400 font-bold' : 'text-slate-300'}>
                  {validationReport.missing_coordinate_count}
                </span>
              </div>
              <div className="flex justify-between p-1.5 rounded bg-slate-950">
                <span className="text-slate-400">Out of Range Bounds:</span>
                <span className={validationReport.out_of_range_coordinate_count > 0 ? 'text-red-400 font-bold' : 'text-slate-300'}>
                  {validationReport.out_of_range_coordinate_count}
                </span>
              </div>
              <div className="flex justify-between p-1.5 rounded bg-slate-950">
                <span className="text-slate-400">Malformed Timestamps:</span>
                <span className={validationReport.malformed_timestamp_count > 0 ? 'text-red-400 font-bold' : 'text-slate-300'}>
                  {validationReport.malformed_timestamp_count}
                </span>
              </div>
              <div className="flex justify-between p-1.5 rounded bg-slate-950">
                <span className="text-slate-400">Duplicate Rows:</span>
                <span className={validationReport.duplicate_row_count > 0 ? 'text-amber-400 font-bold' : 'text-slate-300'}>
                  {validationReport.duplicate_row_count}
                </span>
              </div>
              <div className="flex justify-between p-1.5 rounded bg-slate-950">
                <span className="text-slate-400">Missing Required Fields:</span>
                <span className={validationReport.missing_required_field_count > 0 ? 'text-red-400 font-bold' : 'text-slate-300'}>
                  {validationReport.missing_required_field_count}
                </span>
              </div>
            </div>
          </div>

          {/* Warnings List (FR-20) */}
          {validationReport.warnings.length > 0 && (
            <PartialResultBanner warnings={validationReport.warnings} />
          )}
        </div>
      )}
    </div>
  );
}
