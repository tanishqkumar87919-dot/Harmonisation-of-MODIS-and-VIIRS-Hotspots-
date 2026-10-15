'use client';

import React, { useState } from 'react';
import { AUTHORITATIVE_PRODUCT_RECORDS } from '@/lib/constants/products';
import { SensorBadge } from '@/components/common/Badges';
import { Check, ChevronDown, ChevronUp, FileSpreadsheet, Info } from 'lucide-react';

export function ProductSelectionTable() {
  const [expanded, setExpanded] = useState<boolean>(true);

  const modis = AUTHORITATIVE_PRODUCT_RECORDS.find((p) => p.sensor === 'MODIS')!;
  const viirs = AUTHORITATIVE_PRODUCT_RECORDS.find((p) => p.sensor === 'VIIRS')!;

  const rows = [
    { label: 'Product short name', modis: modis.product_short_name, viirs: viirs.product_short_name },
    { label: 'Satellite/platform', modis: modis.satellite_platform, viirs: viirs.satellite_platform },
    { label: 'Product/collection version', modis: modis.product_collection_version, viirs: viirs.product_collection_version },
    { label: 'Temporal coverage', modis: modis.temporal_coverage, viirs: viirs.temporal_coverage },
    { label: 'Data format', modis: modis.data_format, viirs: viirs.data_format },
    { label: 'Source/download endpoint', modis: modis.source_download_endpoint, viirs: viirs.source_download_endpoint },
    { label: 'Required access credentials', modis: modis.required_credentials_note, viirs: viirs.required_credentials_note },
    { label: 'Quality fields and interpretation', modis: modis.quality_fields_interpretation, viirs: viirs.quality_fields_interpretation },
    { label: 'Licence/usage conditions', modis: modis.licence_usage_conditions, viirs: viirs.licence_usage_conditions },
  ];

  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900 shadow-sm overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        type="button"
        className="w-full p-4 flex items-center justify-between text-left hover:bg-slate-800/40 transition-colors focus:outline-none focus:ring-1 focus:ring-cyan-500"
      >
        <div className="flex items-center gap-2">
          <FileSpreadsheet className="w-4 h-4 text-cyan-400" />
          <h3 className="text-sm font-semibold text-slate-100">
            Authoritative Product Selection Record (docs/04_DATA_SOURCES_AND_DICTIONARY.md Section 3)
          </h3>
        </div>
        <div className="flex items-center gap-2 text-xs font-mono text-slate-400">
          <span>{expanded ? 'Collapse Matrix' : 'Expand Matrix'}</span>
          {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </div>
      </button>

      {expanded && (
        <div className="p-4 pt-0 border-t border-slate-800/80">
          <p className="text-xs text-slate-400 font-mono mb-3 leading-relaxed">
            <Info className="w-3.5 h-3.5 text-cyan-400 inline mr-1" />
            Sensor specifications must be verified against current NASA FIRMS / LP DAAC distribution metadata prior to ingestion. Never assume different sensor products use identical fields or error models.
          </p>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-slate-950 text-slate-300 border-b border-slate-800">
                <tr>
                  <th className="p-3 w-1/4">Metadata Property</th>
                  <th className="p-3 w-3/8">
                    <div className="flex items-center gap-2">
                      <SensorBadge sensor="MODIS" size="sm" />
                      <span className="font-semibold text-slate-200">MODIS Target Spec</span>
                    </div>
                  </th>
                  <th className="p-3 w-3/8">
                    <div className="flex items-center gap-2">
                      <SensorBadge sensor="VIIRS" size="sm" />
                      <span className="font-semibold text-slate-200">VIIRS Target Spec</span>
                    </div>
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {rows.map((row, idx) => (
                  <tr key={idx} className="hover:bg-slate-800/30">
                    <td className="p-3 font-semibold text-slate-300 bg-slate-950/40">
                      {row.label}
                    </td>
                    <td className="p-3 text-slate-300 leading-relaxed">
                      {row.modis}
                    </td>
                    <td className="p-3 text-cyan-200/90 leading-relaxed">
                      {row.viirs}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
