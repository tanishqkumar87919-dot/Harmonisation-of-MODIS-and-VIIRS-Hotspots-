'use client';

import React from 'react';
import { AlertCircle, AlertTriangle, CheckCircle, Info, Loader2, RefreshCw } from 'lucide-react';
import { ApiError } from '@/lib/api/client';
import { FIXTURE_BANNER_TEXT } from '@/lib/fixtures/labelledTestFixtures';

interface LoadingStateProps {
  message?: string;
  subtext?: string;
}

export function LoadingState({
  message = 'Processing scientific geospatial query...',
  subtext = 'Calculating candidate pairs and applying spatial indexes.',
}: LoadingStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4 text-center rounded-lg border border-slate-700/60 bg-slate-900/40">
      <Loader2 className="w-8 h-8 text-cyan-500 animate-spin mb-3" />
      <p className="text-sm font-medium text-slate-200">{message}</p>
      {subtext && <p className="text-xs text-slate-400 mt-1 max-w-sm">{subtext}</p>}
    </div>
  );
}

interface EmptyStateProps {
  title: string;
  description: string;
  actionText?: string;
  onAction?: () => void;
  icon?: React.ReactNode;
}

export function EmptyState({
  title,
  description,
  actionText,
  onAction,
  icon,
}: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-6 text-center rounded-lg border border-dashed border-slate-700 bg-slate-900/30">
      <div className="w-12 h-12 rounded-full bg-slate-800 flex items-center justify-center text-slate-400 mb-3">
        {icon || <Info className="w-6 h-6" />}
      </div>
      <h3 className="text-sm font-semibold text-slate-200 mb-1">{title}</h3>
      <p className="text-xs text-slate-400 max-w-md mb-4">{description}</p>
      {actionText && onAction && (
        <button
          onClick={onAction}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-white bg-cyan-600 hover:bg-cyan-500 rounded-md transition-colors shadow-sm focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:ring-offset-2 focus:ring-offset-slate-900"
        >
          {actionText}
        </button>
      )}
    </div>
  );
}

interface ErrorAlertProps {
  error: Error | ApiError | string | null;
  onRetry?: () => void;
  title?: string;
}

export function ErrorAlert({ error, onRetry, title = 'Application Error' }: ErrorAlertProps) {
  if (!error) return null;

  const isApiError = error instanceof ApiError;
  const message = typeof error === 'string' ? error : error.message;
  const remediation = isApiError ? error.remediation : null;
  const status = isApiError ? error.status : null;

  return (
    <div
      role="alert"
      className="rounded-lg border border-red-700/60 bg-red-950/40 p-4 text-red-200 shadow-sm"
    >
      <div className="flex items-start gap-3">
        <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <h4 className="text-sm font-semibold text-red-200">{title}</h4>
            {status !== null && (
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-red-900/80 text-red-300 border border-red-800">
                HTTP {status === 0 ? 'CONNECTION FAILED' : status}
              </span>
            )}
          </div>
          <p className="text-xs text-red-300 mt-1 leading-relaxed font-mono">{message}</p>
          {remediation && (
            <div className="mt-2.5 pt-2 border-t border-red-800/40 text-xs text-red-200/90">
              <span className="font-semibold text-red-200">Suggested Action: </span>
              {remediation}
            </div>
          )}
        </div>
        {onRetry && (
          <button
            onClick={onRetry}
            className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium text-red-100 bg-red-800/60 hover:bg-red-700/60 rounded border border-red-700 transition-colors"
          >
            <RefreshCw className="w-3 h-3" />
            Retry
          </button>
        )}
      </div>
    </div>
  );
}

interface PartialResultBannerProps {
  warnings: string[];
}

export function PartialResultBanner({ warnings }: PartialResultBannerProps) {
  if (!warnings || warnings.length === 0) return null;

  return (
    <div className="rounded-lg border border-amber-600/50 bg-amber-950/30 p-3 text-amber-200 text-xs mb-4">
      <div className="flex items-start gap-2.5">
        <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-amber-300">Processing Warnings / Caveats:</span>
          <ul className="list-disc list-inside mt-1 space-y-0.5 text-amber-200/90 font-mono text-[11px]">
            {warnings.map((w, idx) => (
              <li key={idx}>{w}</li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}

interface TestFixtureBannerProps {
  active: boolean;
  onDisable?: () => void;
}

export function TestFixtureBanner({ active, onDisable }: TestFixtureBannerProps) {
  if (!active) return null;

  return (
    <div
      role="banner"
      className="sticky top-0 z-50 w-full bg-amber-500 text-slate-950 px-4 py-1.5 font-mono text-xs font-bold text-center tracking-wide shadow-md flex items-center justify-between"
    >
      <div className="flex items-center justify-center gap-2 flex-1">
        <AlertTriangle className="w-4 h-4 text-slate-950 flex-shrink-0" />
        <span>{FIXTURE_BANNER_TEXT}</span>
      </div>
      {onDisable && (
        <button
          onClick={onDisable}
          className="text-[11px] underline hover:text-slate-800 font-semibold ml-4"
        >
          Disable Fixture Mode
        </button>
      )}
    </div>
  );
}
