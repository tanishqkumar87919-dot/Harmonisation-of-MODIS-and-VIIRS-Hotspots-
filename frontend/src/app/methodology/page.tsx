'use client';

import React, { useState } from 'react';
import {
  BookOpen,
  Cpu,
  Layers,
  ShieldAlert,
  Database,
  FileCode,
  GitBranch,
  Info,
  CheckCircle2,
  AlertTriangle,
  ChevronRight,
  ExternalLink,
} from 'lucide-react';
import { SENSOR_CONFIGS, MATCH_STATUS_CONFIGS } from '@/lib/constants/design';
import { SensorBadge, MatchStatusBadge } from '@/components/common/Badges';

export default function MethodologyReferencePage() {
  const [activeTab, setActiveTab] = useState<'overview' | 'dictionary' | 'stages' | 'physics' | 'caveats'>('overview');

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="border-b border-slate-800 pb-4">
        <h2 className="text-xl font-bold tracking-tight text-slate-100 flex items-center gap-2">
          <BookOpen className="w-5 h-5 text-cyan-400" />
          Methodology &amp; Scientific Data Dictionary
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Authoritative technical reference on satellite footprint physics, algorithm stages, 17-field internal schema, and scientific caveats.
        </p>
      </div>

      {/* Navigation Tabs */}
      <div className="flex items-center gap-1.5 border-b border-slate-800 overflow-x-auto pb-1">
        {[
          { id: 'overview', label: '1. Overview & Principles', icon: BookOpen },
          { id: 'dictionary', label: '2. 17-Field Data Dictionary', icon: Database },
          { id: 'stages', label: '3. 7-Stage Harmonisation Algorithm', icon: GitBranch },
          { id: 'physics', label: '4. Sensor Physics & Resolution', icon: Cpu },
          { id: 'caveats', label: '5. Caveats & Limitations', icon: ShieldAlert },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center gap-2 px-3 py-2 rounded-t-lg text-xs font-mono transition-colors whitespace-nowrap ${
                isActive
                  ? 'bg-slate-900 border-t-2 border-t-cyan-400 border-x border-slate-800 text-cyan-300 font-bold'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/50'
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Tab 1: Overview & Principles */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          <div className="p-5 rounded-lg bg-slate-900 border border-slate-800 space-y-3">
            <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
              <Layers className="w-4 h-4 text-cyan-400" />
              Plain-Language Explanation of Active Fire Harmonisation
            </h3>
            <p className="text-xs text-slate-300 leading-relaxed font-sans">
              NASA instruments aboard polar-orbiting satellites observe thermal anomalies across the Earth&apos;s surface.
              The Moderate Resolution Imaging Spectroradiometer (<strong>MODIS</strong>) aboard Terra and Aqua provides a 20+ year active fire record with nominal 1 km nadir resolution.
              The Visible Infrared Imaging Radiometer Suite (<strong>VIIRS</strong>) aboard Suomi-NPP and NOAA-20/21 provides modern active fire observations with 375 m resolution.
            </p>
            <p className="text-xs text-slate-300 leading-relaxed font-sans">
              Because both sensors frequently observe the same wildfire within a 30 to 60 minute window during daytime or nighttime orbital passes,
              simply combining their detections into a single table causes severe duplicate counting. Harmonisation is the systematic, rule-governed process of
              identifying when a MODIS detection and a VIIRS detection represent the <em>same active fire event</em>, linking them through explicit spatiotemporal criteria,
              and preserving single-sensor and ambiguous observations with full provenance.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 rounded-lg bg-slate-900 border border-slate-800 space-y-3">
              <h4 className="text-xs font-bold font-mono uppercase tracking-wider text-slate-300">
                Core Scientific Principles (docs/05_HARMONISATION_ALGORITHM.md)
              </h4>
              <ul className="space-y-2 text-xs text-slate-300">
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
                  <span><strong>Preserve Original Data:</strong> Raw observations, source IDs, and uncalibrated metrics are never discarded.</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
                  <span><strong>Configurable Tolerances:</strong> Spatial (&Delta;d) and temporal (&Delta;t) thresholds are explicitly recorded in run provenance.</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
                  <span><strong>Candidate Distinction:</strong> A candidate spatiotemporal pair is not automatically a proof of single physical fire event identity.</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
                  <span><strong>No Arbitrary Deletion:</strong> Unmatched and ambiguous records are retained and reported with dedicated categories.</span>
                </li>
              </ul>
            </div>

            <div className="p-4 rounded-lg bg-slate-900 border border-slate-800 space-y-3">
              <h4 className="text-xs font-bold font-mono uppercase tracking-wider text-slate-300">
                Candidate Match Score Formulation
              </h4>
              <p className="text-xs text-slate-300 leading-relaxed font-sans">
                When candidate pairs are identified, a normalized ranking index $s \in [0, 1]$ is computed:
              </p>
              <div className="p-3 rounded bg-slate-950 border border-slate-800 font-mono text-xs text-cyan-300 text-center">
                s = w_d &times; (1 &minus; &Delta;d / d_max) + w_t &times; (1 &minus; &Delta;t / t_max)
              </div>
              <div className="p-2.5 rounded bg-amber-950/20 border border-amber-800/60 text-[11px] text-amber-200">
                <strong>Rule 9 Warning:</strong> Do not label this score as a probability. It is an empirical heuristic ranking index.
                True probability requires independent calibration and validation against ground truth.
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: 17-Field Data Dictionary */}
      {activeTab === 'dictionary' && (
        <div className="space-y-6">
          <div className="p-4 rounded-lg bg-slate-900 border border-slate-800 flex items-start gap-3">
            <Database className="w-5 h-5 text-cyan-400 flex-shrink-0 mt-0.5" />
            <div className="text-xs text-slate-300 space-y-1">
              <div className="font-semibold text-slate-100">
                Common Internal Schema (docs/04_DATA_SOURCES_AND_DICTIONARY.md &sect;4)
              </div>
              <p className="text-slate-400 leading-relaxed font-sans">
                Every ingested MODIS and VIIRS record is mapped to this standardized 17-field internal representation during Stage B standardization.
                Original source columns and quality attributes are preserved verbatim in the raw fields dictionary.
              </p>
            </div>
          </div>

          <div className="rounded-lg bg-slate-900 border border-slate-800 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead className="bg-slate-950 text-slate-400 border-b border-slate-800">
                  <tr>
                    <th className="p-3 font-semibold">#</th>
                    <th className="p-3 font-semibold">Internal Field</th>
                    <th className="p-3 font-semibold">Data Type</th>
                    <th className="p-3 font-semibold">Scientific Meaning</th>
                    <th className="p-3 font-semibold">Validation &amp; Preservation Rule</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {[
                    { num: 1, field: 'observation_id', type: 'UUID / string', meaning: 'Unique internal record identifier', rule: 'Generated deterministically by application' },
                    { num: 2, field: 'source_record_id', type: 'string', meaning: 'Original record ID from data provider', rule: 'Preserved verbatim from source file' },
                    { num: 3, field: 'source_sensor', type: 'SensorType', meaning: 'MODIS or VIIRS', rule: 'Strict controlled vocabulary' },
                    { num: 4, field: 'platform', type: 'string', meaning: 'Satellite platform name', rule: 'Terra, Aqua, Suomi-NPP, NOAA-20, NOAA-21' },
                    { num: 5, field: 'product_name', type: 'string', meaning: 'Exact scientific product identifier', rule: 'MOD14, MYD14, VNP14IMGTDL, etc.' },
                    { num: 6, field: 'product_version', type: 'string', meaning: 'Product or collection version', rule: 'e.g., C6.1, v1.0, 002' },
                    { num: 7, field: 'observation_time_utc', type: 'ISO-8601 string', meaning: 'Normalized UTC observation timestamp', rule: 'Validated against YYYY-MM-DDThh:mm:ssZ' },
                    { num: 8, field: 'latitude', type: 'float', meaning: 'Latitude in decimal degrees (WGS 84)', rule: 'Strict boundary check: -90.0 &le; lat &le; 90.0' },
                    { num: 9, field: 'longitude', type: 'float', meaning: 'Longitude in decimal degrees (WGS 84)', rule: 'Strict boundary check: -180.0 &le; lon &le; 180.0' },
                    { num: 10, field: 'confidence_raw', type: 'number | string', meaning: 'Sensor confidence value', rule: 'Never blended across sensors (0-100% vs cat)' },
                    { num: 11, field: 'frp_raw', type: 'float | null', meaning: 'Fire Radiative Power measurement', rule: 'Retained in original sensor units (MW)' },
                    { num: 12, field: 'frp_unit', type: 'string', meaning: 'FRP physical unit', rule: 'MW (Megawatts) confirmed from product spec' },
                    { num: 13, field: 'scan_raw', type: 'float | null', meaning: 'Scan pixel dimension (along-scan)', rule: 'Preserved for footprint geometry estimation' },
                    { num: 14, field: 'track_raw', type: 'float | null', meaning: 'Track pixel dimension (along-track)', rule: 'Preserved for footprint geometry estimation' },
                    { num: 15, field: 'quality_flags_raw', type: 'string | null', meaning: 'Provider quality flags or bitmasks', rule: 'Preserved without destructive decoding' },
                    { num: 16, field: 'ingestion_run_id', type: 'string', meaning: 'Traceable batch/run ID of import', rule: 'Enforces complete provenance tracking' },
                    { num: 17, field: 'row_quality_status', type: 'RowQualityStatus', meaning: 'valid, warning, or rejected', rule: 'Documented rule classification' },
                  ].map((row) => (
                    <tr key={row.num} className="hover:bg-slate-800/40">
                      <td className="p-3 text-slate-500 font-bold">{row.num}</td>
                      <td className="p-3 font-bold text-cyan-300">{row.field}</td>
                      <td className="p-3 text-purple-300">{row.type}</td>
                      <td className="p-3 text-slate-200 font-sans text-xs">{row.meaning}</td>
                      <td className="p-3 text-slate-400 font-sans text-xs">{row.rule}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Tab 3: 7-Stage Algorithm */}
      {activeTab === 'stages' && (
        <div className="space-y-4">
          <div className="p-4 rounded-lg bg-slate-900 border border-slate-800">
            <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
              <GitBranch className="w-4 h-4 text-cyan-400" />
              The 7-Stage Harmonisation Algorithm (docs/05_HARMONISATION_ALGORITHM.md)
            </h3>
            <p className="text-xs text-slate-400 mt-1">
              End-to-end processing pipeline ensuring transparent data transformations, rigorous QC, and deterministic ambiguity handling.
            </p>
          </div>

          <div className="space-y-3">
            {[
              {
                stage: 'Stage A',
                title: 'Input Validation & Verification',
                desc: 'Inspect file format, schema headers, data types, coordinate ranges (-90 to 90 lat, -180 to 180 lon), and timestamp formatting. Reject malformed rows and generate a comprehensive validation audit report.',
                rules: ['Coordinate bounds', 'Timestamp parsing', 'Missing mandatory columns'],
              },
              {
                stage: 'Stage B',
                title: 'Schema Standardization & UTC Normalization',
                desc: 'Map source-specific columns into the 17 common internal fields. Normalize local solar times or Julian dates to ISO-8601 UTC. Retain raw measurements and quality flags verbatim.',
                rules: ['UTC normalization', '17-field mapping', 'Preserve raw dictionary'],
              },
              {
                stage: 'Stage C',
                title: 'Quality Filtering (Configurable)',
                desc: 'Filter observations based on documented sensor quality rules (e.g. minimum confidence threshold, daytime/nighttime flags). Excluded rows are marked rejected or warning with logged reasons.',
                rules: ['Audit-logged exclusions', 'Optional confidence cutoff', 'Quality flag masking'],
              },
              {
                stage: 'Stage D',
                title: 'Spatiotemporal Candidate Pair Search',
                desc: 'For each valid MODIS hotspot, search for VIIRS hotspots within maximum temporal difference Delta t and maximum spatial distance Delta d using geodesic distance or projected Euclidean coordinates.',
                rules: ['Spatial indexing (R-Tree / KD-Tree)', 'Delta d <= max_distance_m', 'Delta t <= max_time_s'],
              },
              {
                stage: 'Stage E',
                title: 'Candidate Scoring (Ranking Heuristic)',
                desc: 'Compute normalized proximity score s combining spatial proximity and temporal closeness. Strictly labeled as a ranking metric, never as a calibrated probability.',
                rules: ['Weighted distance/time index', 'Bounded in [0, 1]', 'Deterministic ranking'],
              },
              {
                stage: 'Stage F',
                title: 'Candidate Resolution & Ambiguity Policy',
                desc: 'When one MODIS detection associates with multiple VIIRS candidates (or vice versa), apply the user-selected ambiguity policy: (1) retain ambiguous, (2) deterministic one-to-one, or (3) many-to-many.',
                rules: ['Explicit policy recording', 'Ambiguity rate tracking', 'No silent candidate dropping'],
              },
              {
                stage: 'Stage G',
                title: 'Output Construction & Provenance Bundling',
                desc: 'Construct unified output tables: matched pairs, unmatched MODIS, unmatched VIIRS, and ambiguous candidates. Bundle processing parameters, version tags, and audit reports into the reproducibility manifest.',
                rules: ['Complete provenance manifest', 'Preserve unmatched detections', 'Export GeoJSON and CSV'],
              },
            ].map((st) => (
              <div key={st.stage} className="p-4 rounded-lg bg-slate-900 border border-slate-800 space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800 text-xs font-mono font-bold">
                      {st.stage}
                    </span>
                    <h4 className="text-sm font-semibold text-slate-100">{st.title}</h4>
                  </div>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed font-sans">{st.desc}</p>
                <div className="flex flex-wrap gap-2 pt-1">
                  {st.rules.map((rule, idx) => (
                    <span key={idx} className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-950 text-slate-400 border border-slate-800">
                      &bull; {rule}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab 4: Sensor Physics */}
      {activeTab === 'physics' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* MODIS Physics */}
            <div className="p-5 rounded-lg bg-slate-900 border border-slate-800 space-y-4">
              <div className="flex items-center justify-between">
                <SensorBadge sensor="MODIS" size="md" />
                <span className="text-xs font-mono text-slate-400">Terra &amp; Aqua</span>
              </div>
              <div className="space-y-3 text-xs leading-relaxed text-slate-300 font-sans">
                <div>
                  <strong className="text-slate-100 font-mono">Pixel Footprint Growth (&ldquo;Bow-Tie Effect&rdquo;):</strong>
                  <p className="mt-1">
                    At nadir, MODIS pixels are 1 km &times; 1 km. As scan angle reaches &plusmn;55&deg;, geometric projection distorts the footprint to approximately 2.0 km along-track &times; 4.8 km along-scan.
                    Consequently, edge-of-scan detections encompass a ~10&times; larger physical area, causing substantial spatial uncertainty.
                  </p>
                </div>
                <div>
                  <strong className="text-slate-100 font-mono">Detection Sensitivity:</strong>
                  <p className="mt-1">
                    MODIS active fire algorithms (MOD14/MYD14) rely on the 4 &mu;m (Channel 21/22) and 11 &mu;m (Channel 31) brightness temperatures.
                    Requires higher fire radiant intensity (&ge; 10&ndash;20 MW) to trigger detection under typical atmospheric conditions.
                  </p>
                </div>
              </div>
            </div>

            {/* VIIRS Physics */}
            <div className="p-5 rounded-lg bg-slate-900 border border-slate-800 space-y-4">
              <div className="flex items-center justify-between">
                <SensorBadge sensor="VIIRS" size="md" />
                <span className="text-xs font-mono text-slate-400">Suomi-NPP &amp; NOAA-20/21</span>
              </div>
              <div className="space-y-3 text-xs leading-relaxed text-slate-300 font-sans">
                <div>
                  <strong className="text-slate-100 font-mono">Onboard Pixel Aggregation:</strong>
                  <p className="mt-1">
                    VIIRS Imagery (I) bands feature nominal 375 m resolution at nadir. Unlike MODIS, VIIRS uses an onboard aggregation scheme (3&times; aggregation at nadir, 2&times; at intermediate angles, and 1&times; at swath edges)
                    that constrains footprint growth to less than 2&times; nadir dimension (~750 m at edge), dramatically reducing spatial distortion.
                  </p>
                </div>
                <div>
                  <strong className="text-slate-100 font-mono">Detection Sensitivity:</strong>
                  <p className="mt-1">
                    The 375 m I-band active fire product (VNP14IMGTDL) detects much smaller, lower-intensity flaming fronts (&ge; 1&ndash;3 MW),
                    producing significantly higher hotspot counts than MODIS for the exact same physical fire ground scene.
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Rule 8: FRP Physics Notice */}
          <div className="p-4 rounded-lg bg-slate-900 border border-cyan-800/60 bg-cyan-950/20 text-xs text-cyan-200 space-y-2">
            <div className="flex items-center gap-2 font-bold text-cyan-300">
              <Info className="w-4 h-4 flex-shrink-0" />
              Scientific Note on Fire Radiative Power (FRP) &mdash; Rule 8
            </div>
            <p className="leading-relaxed font-sans text-cyan-200/90">
              Fire Radiative Power (FRP) is an instantaneous rate of radiative thermal energy emission expressed in Megawatts (MW).
              Because MODIS integrates thermal radiation over a 1,000 m pixel while VIIRS integrates over a 375 m pixel, their background subtraction,
              sub-pixel fire fraction, and atmospheric path lengths differ fundamentally. <strong>Averaging MODIS and VIIRS FRP values is scientifically invalid</strong>.
              All harmonised records preserve both sensors&apos; FRP values independently in original units.
            </p>
          </div>
        </div>
      )}

      {/* Tab 5: Caveats & Limitations */}
      {activeTab === 'caveats' && (
        <div className="space-y-4">
          <div className="p-4 rounded-lg bg-amber-950/30 border border-amber-800 text-amber-200 text-xs space-y-2">
            <div className="flex items-center gap-2 font-bold text-amber-300 text-sm">
              <ShieldAlert className="w-5 h-5 flex-shrink-0" />
              Mandatory Scientific Caveats (docs/03_RESEARCH_METHODOLOGY.md &sect;7 &amp; docs/10_TESTING_VALIDATION_DEPLOYMENT.md &sect;7)
            </div>
            <p className="text-amber-200/90 leading-relaxed font-sans">
              These caveats must accompany every analysis, visualization, exported dataset, and publication derived from this application:
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[
              {
                title: 'Point Detection &ne; Physical Fire Event',
                desc: 'A satellite hotspot detection indicates that a pixel contained one or more sub-pixel active combustion sources at the instantaneous second of overpass. It does not measure the total fire perimeter, duration, or discrete fire count.',
              },
              {
                title: 'Match Status is Parametric, Not Definitive',
                desc: 'A status of "matched" indicates only that detections from two sensors satisfied the configured spatial and temporal thresholds. It is not conclusive proof that the sensors observed the exact same physical flame without independent ground truth.',
              },
              {
                title: 'Absence of Detection &ne; Absence of Fire',
                desc: 'Thermal anomaly algorithms cannot detect fires obscured by dense cloud cover, heavy smoke plumes, or thick canopy. Fires that ignite and extinguish between satellite overpasses will not be detected.',
              },
              {
                title: 'Neither Sensor is Ground Truth',
                desc: 'VIIRS has finer resolution and higher sensitivity, but also produces more false detections over reflective solar panels or hot soil. MODIS has a 20+ year legacy, but coarser pixels. Neither is an absolute reference standard for the other.',
              },
              {
                title: 'Threshold Sensitivity Dictates Outcomes',
                desc: 'Relaxing spatial tolerance increases match rates while simultaneously increasing the rate of ambiguous and false associations. Thresholds should be chosen based on instrument geometry, not to artificially optimize match counts.',
              },
              {
                title: 'Risk Prediction Boundary',
                desc: 'This application harmonises active fire observations. It does not provide predictive fire danger forecasting, which requires meteorological inputs, fuel moisture data, and a separate validated machine learning pipeline.',
              },
            ].map((caveat, idx) => (
              <div key={idx} className="p-4 rounded-lg bg-slate-900 border border-slate-800 space-y-1.5">
                <div className="font-bold text-slate-200 font-mono text-xs flex items-center gap-2">
                  <span className="text-cyan-400">#{idx + 1}</span>
                  {caveat.title}
                </div>
                <p className="text-xs text-slate-400 leading-relaxed font-sans">{caveat.desc}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
