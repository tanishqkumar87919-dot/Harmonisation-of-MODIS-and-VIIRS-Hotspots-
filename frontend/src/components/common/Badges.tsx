'use client';

import React from 'react';
import { MatchStatus, RowQualityStatus, SensorType } from '@/types/harmonisation';
import { MATCH_STATUS_CONFIGS, QUALITY_STATUS_CONFIGS, SENSOR_CONFIGS } from '@/lib/constants/design';
import clsx from 'clsx';

interface SensorBadgeProps {
  sensor: SensorType;
  showPlatform?: string;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function SensorBadge({ sensor, showPlatform, size = 'md', className }: SensorBadgeProps) {
  const config = SENSOR_CONFIGS[sensor];
  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5 gap-1',
    md: 'text-xs px-2.5 py-1 gap-1.5 font-medium',
    lg: 'text-sm px-3 py-1.5 gap-2 font-semibold',
  };

  return (
    <span
      className={clsx(
        'inline-flex items-center rounded-md border shadow-sm font-mono tracking-wide',
        sizeClasses[size],
        className
      )}
      style={{
        backgroundColor: config.bgLight,
        color: config.textColor,
        borderColor: config.borderLight,
      }}
      title={`${config.label}: ${config.nominalResolution} — ${config.description}`}
    >
      {/* Non-color geometric shape indicator */}
      {config.shape === 'square' ? (
        <svg className="w-2.5 h-2.5 flex-shrink-0" viewBox="0 0 10 10" fill="currentColor">
          <rect width="10" height="10" rx="1.5" />
        </svg>
      ) : (
        <svg className="w-2.5 h-2.5 flex-shrink-0" viewBox="0 0 10 10" fill="currentColor">
          <polygon points="5,0 10,10 0,10" />
        </svg>
      )}
      <span>{config.label}</span>
      {showPlatform && (
        <span className="opacity-75 text-[10px] uppercase">({showPlatform})</span>
      )}
    </span>
  );
}

interface MatchStatusBadgeProps {
  status: MatchStatus;
  size?: 'sm' | 'md' | 'lg';
  showDescriptionTooltip?: boolean;
  className?: string;
}

export function MatchStatusBadge({
  status,
  size = 'md',
  showDescriptionTooltip = true,
  className,
}: MatchStatusBadgeProps) {
  const config = MATCH_STATUS_CONFIGS[status];
  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5 gap-1',
    md: 'text-xs px-2.5 py-1 gap-1.5 font-medium',
    lg: 'text-sm px-3 py-1.5 gap-2 font-semibold',
  };

  return (
    <span
      className={clsx(
        'inline-flex items-center rounded-md border shadow-sm font-mono tracking-wide',
        sizeClasses[size],
        className
      )}
      style={{
        backgroundColor: config.bgLight,
        color: config.textColor,
        borderColor: config.borderLight,
      }}
      title={showDescriptionTooltip ? `${config.scientificLabel}: ${config.description}` : undefined}
    >
      {/* Distinct geometric symbol for each match status */}
      {config.shape === 'linked-circle' && (
        <svg className="w-3 h-3 flex-shrink-0" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="6" cy="8" r="4" />
          <circle cx="10" cy="8" r="4" />
        </svg>
      )}
      {config.shape === 'hollow-square' && (
        <svg className="w-2.5 h-2.5 flex-shrink-0" viewBox="0 0 10 10" fill="none" stroke="currentColor" strokeWidth="2">
          <rect x="1" y="1" width="8" height="8" rx="1" />
        </svg>
      )}
      {config.shape === 'hollow-triangle' && (
        <svg className="w-2.5 h-2.5 flex-shrink-0" viewBox="0 0 10 10" fill="none" stroke="currentColor" strokeWidth="1.8">
          <polygon points="5,1 9,9 1,9" />
        </svg>
      )}
      {config.shape === 'diamond' && (
        <svg className="w-2.5 h-2.5 flex-shrink-0" viewBox="0 0 10 10" fill="currentColor">
          <polygon points="5,0 10,5 5,10 0,5" />
        </svg>
      )}
      <span>{config.label}</span>
    </span>
  );
}

interface QualityStatusBadgeProps {
  status: RowQualityStatus;
  size?: 'sm' | 'md';
  className?: string;
}

export function QualityStatusBadge({ status, size = 'sm', className }: QualityStatusBadgeProps) {
  const config = QUALITY_STATUS_CONFIGS[status];
  const sizeClasses = {
    sm: 'text-[11px] px-2 py-0.5 gap-1 font-mono',
    md: 'text-xs px-2.5 py-1 gap-1.5 font-mono font-medium',
  };

  return (
    <span
      className={clsx(
        'inline-flex items-center rounded border shadow-sm',
        sizeClasses[size],
        className
      )}
      style={{
        backgroundColor: config.bgLight,
        color: config.textColor,
        borderColor: config.borderLight,
      }}
      title={config.description}
    >
      {config.shape === 'circle-check' && (
        <svg className="w-2.5 h-2.5 flex-shrink-0" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M2 6l3 3 5-6" />
        </svg>
      )}
      {config.shape === 'triangle-alert' && (
        <svg className="w-2.5 h-2.5 flex-shrink-0" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="2">
          <polygon points="6,1 11,11 1,11" />
          <line x1="6" y1="5" x2="6" y2="7" />
          <circle cx="6" cy="9" r="0.5" fill="currentColor" />
        </svg>
      )}
      {config.shape === 'octagon-x' && (
        <svg className="w-2.5 h-2.5 flex-shrink-0" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="2">
          <line x1="3" y1="3" x2="9" y2="9" />
          <line x1="9" y1="3" x2="3" y2="9" />
        </svg>
      )}
      <span>{config.label}</span>
    </span>
  );
}
