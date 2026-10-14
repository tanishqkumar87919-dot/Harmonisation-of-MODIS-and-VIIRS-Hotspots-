import { MatchStatus, RowQualityStatus, SensorType } from '@/types/harmonisation';

export interface SensorVisualConfig {
  sensor: SensorType;
  color: string;
  textColor: string;
  bgLight: string;
  borderLight: string;
  shape: 'square' | 'triangle';
  label: string;
  nominalResolution: string;
  description: string;
}

export const SENSOR_CONFIGS: Record<SensorType, SensorVisualConfig> = {
  MODIS: {
    sensor: 'MODIS',
    color: '#D9480F',
    textColor: '#9C360C',
    bgLight: '#FFE8CC',
    borderLight: '#FFA94D',
    shape: 'square',
    label: 'MODIS',
    nominalResolution: '~1 km nadir (MOD14/MYD14)',
    description: 'Moderate Resolution Imaging Spectroradiometer aboard Terra and Aqua satellites.',
  },
  VIIRS: {
    sensor: 'VIIRS',
    color: '#0B7285',
    textColor: '#084C61',
    bgLight: '#E3FAFC',
    borderLight: '#66D9E8',
    shape: 'triangle',
    label: 'VIIRS',
    nominalResolution: '375 m / 750 m nadir (VNP14IMGTDL/VNP14)',
    description: 'Visible Infrared Imaging Radiometer Suite aboard Suomi-NPP and NOAA-20/21 satellites.',
  },
};

export interface MatchStatusVisualConfig {
  status: MatchStatus;
  color: string;
  textColor: string;
  bgLight: string;
  borderLight: string;
  shape: 'linked-circle' | 'hollow-square' | 'hollow-triangle' | 'diamond';
  label: string;
  scientificLabel: string;
  description: string;
}

export const MATCH_STATUS_CONFIGS: Record<MatchStatus, MatchStatusVisualConfig> = {
  matched: {
    status: 'matched',
    color: '#087F5B',
    textColor: '#065F46',
    bgLight: '#E6FCF5',
    borderLight: '#63E6BE',
    shape: 'linked-circle',
    label: 'Matched',
    scientificLabel: 'Matched (Algorithm Pair)',
    description: 'Pair accepted by the configured algorithm (not automatic proof of one physical fire event).',
  },
  unmatched_modis: {
    status: 'unmatched_modis',
    color: '#E67700',
    textColor: '#B05600',
    bgLight: '#FFF3BF',
    borderLight: '#FFD43B',
    shape: 'hollow-square',
    label: 'Unmatched MODIS',
    scientificLabel: 'Unmatched MODIS',
    description: 'No accepted VIIRS partner under the current parameters.',
  },
  unmatched_viirs: {
    status: 'unmatched_viirs',
    color: '#1971C2',
    textColor: '#1864AB',
    bgLight: '#D0EBFF',
    borderLight: '#74C0FC',
    shape: 'hollow-triangle',
    label: 'Unmatched VIIRS',
    scientificLabel: 'Unmatched VIIRS',
    description: 'No accepted MODIS partner under the current parameters.',
  },
  ambiguous: {
    status: 'ambiguous',
    color: '#862E9C',
    textColor: '#702283',
    bgLight: '#F3D9FA',
    borderLight: '#DA77F2',
    shape: 'diamond',
    label: 'Ambiguous',
    scientificLabel: 'Ambiguous Candidates',
    description: 'Multiple plausible candidates or insufficient evidence for a unique match.',
  },
};

export interface QualityStatusVisualConfig {
  status: RowQualityStatus;
  color: string;
  textColor: string;
  bgLight: string;
  borderLight: string;
  shape: 'circle-check' | 'triangle-alert' | 'octagon-x';
  label: string;
  description: string;
}

export const QUALITY_STATUS_CONFIGS: Record<RowQualityStatus, QualityStatusVisualConfig> = {
  valid: {
    status: 'valid',
    color: '#2B8A3E',
    textColor: '#217031',
    bgLight: '#EBFBEE',
    borderLight: '#8CE99A',
    shape: 'circle-check',
    label: 'Valid',
    description: 'Observation passed all schema, coordinate bounds, and timestamp checks.',
  },
  warning: {
    status: 'warning',
    color: '#D97706',
    textColor: '#92400E',
    bgLight: '#FEF3C7',
    borderLight: '#FCD34D',
    shape: 'triangle-alert',
    label: 'Warning',
    description: 'Observation retained with non-fatal data quality warning flag.',
  },
  rejected: {
    status: 'rejected',
    color: '#495057',
    textColor: '#343A40',
    bgLight: '#F1F3F5',
    borderLight: '#CED4DA',
    shape: 'octagon-x',
    label: 'Rejected input row',
    description: 'Row failed a documented data-quality rule and was excluded from candidate generation.',
  },
};

/**
 * WCAG-compliant high-contrast dark theme background and surface constants
 */
export const SCIENTIFIC_THEME = {
  bgApp: '#0F172A',         // Slate 900
  bgSurface: '#1E293B',     // Slate 800
  bgSurfaceHover: '#334155',// Slate 700
  borderSubtle: '#334155',  // Slate 700
  borderStrong: '#475569',  // Slate 600
  textPrimary: '#F8FAFC',   // Slate 50
  textSecondary: '#94A3B8', // Slate 400
  textMuted: '#64748B',     // Slate 500
};
