'use client';

import React from 'react';
import { AmbiguityPolicy, ScoreWeights } from '@/types/harmonisation';
import { MatchStatusBadge } from '@/components/common/Badges';
import { AlertCircle, Check, GitFork, Info, ShieldCheck } from 'lucide-react';
import clsx from 'clsx';

interface AmbiguityPolicySelectorProps {
  policy: AmbiguityPolicy;
  scoreWeights: ScoreWeights;
  onSelectPolicy: (policy: AmbiguityPolicy) => void;
  onChangeWeights: (weights: ScoreWeights) => void;
}

export function AmbiguityPolicySelector({
  policy,
  scoreWeights,
  onSelectPolicy,
  onChangeWeights,
}: AmbiguityPolicySelectorProps) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900 p-5 shadow-sm space-y-5">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center gap-2">
          <GitFork className="w-5 h-5 text-cyan-400" />
          <h3 className="text-sm font-semibold text-slate-100">
            3. Candidate Ambiguity Resolution Policy (Stages E &amp; F, FR-11, FR-13)
          </h3>
        </div>
        <span className="text-xs font-mono text-slate-400">
          Enforces Non-Arbitrary Multi-Partner Resolution
        </span>
      </div>

      {/* Policy Selection Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Option 1: retain_ambiguous (Recommended Default) */}
        <div
          onClick={() => onSelectPolicy('retain_ambiguous')}
          className={clsx(
            'p-4 rounded-lg border cursor-pointer transition-all flex flex-col justify-between space-y-3',
            policy === 'retain_ambiguous'
              ? 'bg-slate-950 border-cyan-500 shadow-md ring-1 ring-cyan-500/50'
              : 'bg-slate-950/60 border-slate-800 hover:border-slate-700'
          )}
        >
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800 font-bold">
                Recommended Scientific Default
              </span>
              <div
                className={clsx(
                  'w-4 h-4 rounded-full border flex items-center justify-center',
                  policy === 'retain_ambiguous'
                    ? 'border-cyan-400 bg-cyan-400 text-slate-950'
                    : 'border-slate-700'
                )}
              >
                {policy === 'retain_ambiguous' && <Check className="w-3 h-3 stroke-[3]" />}
              </div>
            </div>

            <h4 className="text-xs font-mono font-bold text-slate-200">
              retain_ambiguous
            </h4>
            <p className="text-xs text-slate-400 mt-1 leading-relaxed">
              Unique 1-to-1 candidate pairs within thresholds are marked as <span className="text-emerald-400 font-semibold">Matched</span>. Multi-candidate clusters (1-to-many, many-to-many) are preserved in the <span className="text-purple-400 font-semibold">Ambiguous</span> table with all candidate links intact (FR-13).
            </p>
          </div>

          <div className="pt-2 border-t border-slate-800/80 text-[10px] font-mono text-slate-500 flex items-center gap-1">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            <span>Preserves uncertainty without forced merging</span>
          </div>
        </div>

        {/* Option 2: one_to_one_deterministic */}
        <div
          onClick={() => onSelectPolicy('one_to_one_deterministic')}
          className={clsx(
            'p-4 rounded-lg border cursor-pointer transition-all flex flex-col justify-between space-y-3',
            policy === 'one_to_one_deterministic'
              ? 'bg-slate-950 border-cyan-500 shadow-md ring-1 ring-cyan-500/50'
              : 'bg-slate-950/60 border-slate-800 hover:border-slate-700'
          )}
        >
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                Single Best Assignment
              </span>
              <div
                className={clsx(
                  'w-4 h-4 rounded-full border flex items-center justify-center',
                  policy === 'one_to_one_deterministic'
                    ? 'border-cyan-400 bg-cyan-400 text-slate-950'
                    : 'border-slate-700'
                )}
              >
                {policy === 'one_to_one_deterministic' && <Check className="w-3 h-3 stroke-[3]" />}
              </div>
            </div>

            <h4 className="text-xs font-mono font-bold text-slate-200">
              one_to_one_deterministic
            </h4>
            <p className="text-xs text-slate-400 mt-1 leading-relaxed">
              Calculates ranking index s = 1 - [w_d(d/d_max) + w_t(&Delta;t/&Delta;t_max)]. Performs deterministic greedy assignment with tie-breaking (distance &rarr; time &rarr; record ID) to yield strictly 1-to-1 links.
            </p>
          </div>

          <div className="pt-2 border-t border-slate-800/80 text-[10px] font-mono text-slate-500 flex items-center gap-1">
            <GitFork className="w-3.5 h-3.5 text-cyan-400" />
            <span>Deterministic repeatable tie-breaking</span>
          </div>
        </div>

        {/* Option 3: many_to_many */}
        <div
          onClick={() => onSelectPolicy('many_to_many')}
          className={clsx(
            'p-4 rounded-lg border cursor-pointer transition-all flex flex-col justify-between space-y-3',
            policy === 'many_to_many'
              ? 'bg-slate-950 border-cyan-500 shadow-md ring-1 ring-cyan-500/50'
              : 'bg-slate-950/60 border-slate-800 hover:border-slate-700'
          )}
        >
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                Full Bipartite Graph
              </span>
              <div
                className={clsx(
                  'w-4 h-4 rounded-full border flex items-center justify-center',
                  policy === 'many_to_many'
                    ? 'border-cyan-400 bg-cyan-400 text-slate-950'
                    : 'border-slate-700'
                )}
              >
                {policy === 'many_to_many' && <Check className="w-3 h-3 stroke-[3]" />}
              </div>
            </div>

            <h4 className="text-xs font-mono font-bold text-slate-200">
              many_to_many
            </h4>
            <p className="text-xs text-slate-400 mt-1 leading-relaxed">
              Preserves all candidate pairs satisfying &Delta;d &le; d_max and &Delta;t &le; t_max. Useful for fire cluster analysis where multiple 375m VIIRS detections reside inside a single 1km MODIS pixel footprint.
            </p>
          </div>

          <div className="pt-2 border-t border-slate-800/80 text-[10px] font-mono text-slate-500 flex items-center gap-1">
            <Info className="w-3.5 h-3.5 text-purple-400" />
            <span>Captures fine-scale sub-pixel clustering</span>
          </div>
        </div>
      </div>

      {/* Weights adjustment for one_to_one_deterministic */}
      {policy === 'one_to_one_deterministic' && (
        <div className="p-4 rounded bg-slate-950 border border-slate-800 space-y-3 text-xs font-mono">
          <div className="flex items-center justify-between">
            <span className="font-bold text-slate-200">
              Stage E Ranking Score Weights ($w_d + w_t = 1.0$):
            </span>
            <span className="text-cyan-400">
              Spatial: {(scoreWeights.spatial_weight * 100).toFixed(0)}% | Temporal: {(scoreWeights.temporal_weight * 100).toFixed(0)}%
            </span>
          </div>

          <div className="space-y-1">
            <input
              type="range"
              min={0}
              max={100}
              value={scoreWeights.spatial_weight * 100}
              onChange={(e) => {
                const s = Number(e.target.value) / 100;
                onChangeWeights({
                  spatial_weight: Number(s.toFixed(2)),
                  temporal_weight: Number((1 - s).toFixed(2)),
                });
              }}
              className="w-full accent-cyan-500 cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-slate-500">
              <span>0% Spatial (Temporal-only ranking)</span>
              <span>50% Balanced</span>
              <span>100% Spatial (Distance-only ranking)</span>
            </div>
          </div>
        </div>
      )}

      {/* Scientific Disclaimer on Score Physics */}
      <div className="p-3 rounded bg-slate-950 border border-slate-800 text-[11px] font-mono text-slate-400 leading-relaxed flex items-start gap-2">
        <AlertCircle className="w-4 h-4 text-cyan-400 flex-shrink-0 mt-0.5" />
        <span>
          <strong>Scientific Score Semantics (05_HARMONISATION_ALGORITHM.md Stage E):</strong> The match score is an uncalibrated ranking metric between 0 and 1 combining normalized distance and temporal offset. It must <em>never</em> be described as an empirical "probability" without independent ground-truth validation labels.
        </span>
      </div>
    </div>
  );
}
