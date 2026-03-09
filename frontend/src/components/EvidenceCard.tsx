/**
 * EvidenceCard Component
 * ======================
 * Displays a single piece of evidence with speaker name, trust score bar,
 * timestamp, and transcript snippet.
 */

import type { Evidence } from '../types/apiTypes';

function getTrustColor(score: number): string {
  if (score >= 0.75) return 'from-emerald-500 to-green-400';
  if (score >= 0.5) return 'from-amber-500 to-yellow-400';
  return 'from-rose-500 to-red-400';
}

function getTrustLabel(score: number): string {
  if (score >= 0.75) return 'High';
  if (score >= 0.5) return 'Medium';
  return 'Low';
}

function formatTimestamp(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, '0')}`;
}

interface EvidenceCardProps {
  evidence: Evidence;
  index: number;
}

export default function EvidenceCard({ evidence, index }: EvidenceCardProps) {
  const trustPct = Math.round(evidence.trust_score * 100);
  const trustColor = getTrustColor(evidence.trust_score);
  const trustLabel = getTrustLabel(evidence.trust_score);

  return (
    <div
      className="group bg-slate-800/40 backdrop-blur-sm border border-slate-700/50 rounded-xl p-5 hover:border-violet-500/40 transition-all duration-300 hover:shadow-lg hover:shadow-violet-900/10 animate-in"
      style={{ animationDelay: `${index * 80}ms` }}
    >
      {/* Header: Speaker + Timestamp */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2.5">
          {/* Avatar circle */}
          <div className="h-8 w-8 rounded-full bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center text-xs font-bold text-white shadow-md">
            {evidence.speaker.slice(0, 2).toUpperCase()}
          </div>
          <span className="font-semibold text-slate-200 text-sm">
            {evidence.speaker}
          </span>
        </div>
        <span className="text-xs text-slate-500 font-mono bg-slate-700/40 px-2 py-1 rounded-md">
          ⏱ {formatTimestamp(evidence.timestamp)}
        </span>
      </div>

      {/* Transcript snippet */}
      <p className="text-sm text-slate-300 leading-relaxed mb-4 pl-[42px]">
        "{evidence.text}"
      </p>

      {/* Trust score bar */}
      <div className="pl-[42px]">
        <div className="flex items-center justify-between text-xs mb-1.5">
          <span className="text-slate-400 font-medium">Trust Score</span>
          <span className="font-mono font-bold text-slate-300">
            {trustPct}%{' '}
            <span className="text-slate-500 font-normal">({trustLabel})</span>
          </span>
        </div>
        <div className="h-2 w-full bg-slate-700/60 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full bg-gradient-to-r ${trustColor} transition-all duration-700 ease-out`}
            style={{ width: `${trustPct}%` }}
          />
        </div>
      </div>
    </div>
  );
}
