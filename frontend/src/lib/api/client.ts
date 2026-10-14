/**
 * Scientific Typed API Client
 * Authoritative interface between Next.js UI and FastAPI Backend
 * Enforces Rule 5 (NFR-01): Never silently switch to synthetic data on failure.
 */

import {
  DatasetRecord,
  HarmonisedRecord,
  HealthResponse,
  MapFilterState,
  ProcessingRunSummary,
  RunCreateRequest,
  RunDetailedEvaluation,
  ValidationReport,
} from '@/types/harmonisation';

export class ApiError extends Error {
  public readonly status: number;
  public readonly endpoint: string;
  public readonly remediation: string;
  public readonly detail?: unknown;

  constructor(status: number, endpoint: string, message: string, remediation: string, detail?: unknown) {
    super(`[API ${status} @ ${endpoint}]: ${message}`);
    this.name = 'ApiError';
    this.status = status;
    this.endpoint = endpoint;
    this.remediation = remediation;
    this.detail = detail;
  }
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api';

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  let response: Response;

  try {
    response = await fetch(url, {
      ...options,
      headers: {
        Accept: 'application/json',
        ...(options.headers || {}),
      },
    });
  } catch (error) {
    // Network or server unreachable failure
    throw new ApiError(
      0,
      endpoint,
      `Network connection to backend service failed (${url})`,
      'Ensure the FastAPI backend is running at http://localhost:8000. Verify network connectivity or toggle "Labelled Test Fixture Mode" in the header to inspect layout preview.',
      error
    );
  }

  if (!response.ok) {
    let errorDetail: unknown = null;
    let message = `Backend returned HTTP status ${response.status} (${response.statusText})`;
    try {
      const errorJson = await response.json();
      errorDetail = errorJson;
      if (typeof errorJson.detail === 'string') {
        message = errorJson.detail;
      } else if (errorJson.message) {
        message = errorJson.message;
      }
    } catch {
      // response was not JSON
    }

    const remediation =
      response.status === 404
        ? 'The requested dataset, run, or resource was not found. Verify the resource ID.'
        : response.status === 422
        ? 'Input validation failed. Inspect parameters or uploaded CSV schema against the Data Dictionary.'
        : response.status >= 500
        ? 'Backend processing error occurred. Inspect server logs for traceback and parameter constraints.'
        : 'Review the request parameters and retry.';

    throw new ApiError(response.status, endpoint, message, remediation, errorDetail);
  }

  return response.json() as Promise<T>;
}

export const apiClient = {
  /**
   * Health check endpoint (GET /api/health)
   */
  async checkHealth(): Promise<HealthResponse> {
    return request<HealthResponse>('/health');
  },

  /**
   * Validate and ingest an uploaded satellite dataset (POST /api/datasets/validate)
   */
  async validateAndUploadDataset(formData: FormData): Promise<ValidationReport> {
    const url = `${API_BASE_URL}/datasets/validate`;
    let response: Response;
    try {
      response = await fetch(url, {
        method: 'POST',
        body: formData,
      });
    } catch (err) {
      throw new ApiError(
        0,
        '/datasets/validate',
        'Dataset upload failed due to network error.',
        'Ensure the backend is online and the file is under the configured size limit (50 MB).',
        err
      );
    }

    if (!response.ok) {
      let detail: unknown = null;
      let msg = 'Dataset validation failed.';
      try {
        const j = await response.json();
        detail = j;
        msg = j.detail || j.message || msg;
      } catch {
        // non-json
      }
      throw new ApiError(
        response.status,
        '/datasets/validate',
        msg,
        'Confirm the CSV includes required coordinate, date, and confidence columns per 04_DATA_SOURCES_AND_DICTIONARY.md.',
        detail
      );
    }

    return response.json();
  },

  /**
   * List all ingested datasets (GET /api/datasets)
   */
  async listDatasets(): Promise<DatasetRecord[]> {
    return request<DatasetRecord[]>('/datasets');
  },

  /**
   * Delete a dataset by ID (DELETE /api/datasets/{id})
   */
  async deleteDataset(datasetId: string): Promise<void> {
    await request<void>(`/datasets/${datasetId}`, {
      method: 'DELETE',
    });
  },

  /**
   * Launch a reproducible harmonisation processing run (POST /api/runs)
   */
  async createProcessingRun(payload: RunCreateRequest): Promise<ProcessingRunSummary> {
    return request<ProcessingRunSummary>('/runs', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });
  },

  /**
   * List all processing runs (GET /api/runs)
   */
  async listProcessingRuns(): Promise<ProcessingRunSummary[]> {
    return request<ProcessingRunSummary[]>('/runs');
  },

  /**
   * Retrieve single processing run summary (GET /api/runs/{run_id})
   */
  async getProcessingRun(runId: string): Promise<ProcessingRunSummary> {
    return request<ProcessingRunSummary>(`/runs/${runId}`);
  },

  /**
   * Retrieve matched records for a run (GET /api/runs/{run_id}/matches)
   */
  async getRunMatches(runId: string, filters?: MapFilterState): Promise<HarmonisedRecord[]> {
    const params = new URLSearchParams();
    if (filters?.limit) params.set('limit', String(filters.limit));
    if (filters?.offset) params.set('offset', String(filters.offset));
    if (filters?.max_spatial_distance_m) {
      params.set('max_spatial_distance_m', String(filters.max_spatial_distance_m));
    }
    const query = params.toString() ? `?${params.toString()}` : '';
    return request<HarmonisedRecord[]>(`/runs/${runId}/matches${query}`);
  },

  /**
   * Retrieve unmatched records for a run (GET /api/runs/{run_id}/unmatched)
   */
  async getRunUnmatched(runId: string, filters?: MapFilterState): Promise<HarmonisedRecord[]> {
    const params = new URLSearchParams();
    if (filters?.sensors?.length) params.set('sensor', filters.sensors.join(','));
    if (filters?.limit) params.set('limit', String(filters.limit));
    const query = params.toString() ? `?${params.toString()}` : '';
    return request<HarmonisedRecord[]>(`/runs/${runId}/unmatched${query}`);
  },

  /**
   * Retrieve run summary and scientific evaluation metrics (GET /api/runs/{run_id}/summary)
   */
  async getRunSummaryAndEvaluation(runId: string): Promise<RunDetailedEvaluation> {
    return request<RunDetailedEvaluation>(`/runs/${runId}/summary`);
  },

  /**
   * Formulate export download URL (GET /api/runs/{run_id}/export)
   */
  getRunExportUrl(runId: string, format: 'csv' | 'geojson', filters?: MapFilterState): string {
    const params = new URLSearchParams({ format });
    if (filters?.match_statuses?.length) {
      params.set('status', filters.match_statuses.join(','));
    }
    return `${API_BASE_URL}/runs/${runId}/export?${params.toString()}`;
  },
};
