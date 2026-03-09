/**
 * AnswerPanel Component
 * =====================
 * Displays the generated answer and a list of evidence cards.
 */

import type { AskResponse } from '../types/apiTypes';
import EvidenceCard from './EvidenceCard';

interface AnswerPanelProps {
  response: AskResponse | null;
}

export default function AnswerPanel({ response }: AnswerPanelProps) {
  if (!response) return null;

  return (
    <div className="w-full space-y-6 animate-in">
      {/* Answer section */}
      <div className="bg-gradient-to-br from-slate-800/70 to-slate-900/70 backdrop-blur-sm border border-slate-700/50 rounded-2xl p-6 shadow-xl">
        <div className="flex items-center gap-2 mb-4">
          <div className="h-6 w-6 rounded-lg bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center">
            <svg
              className="h-3.5 w-3.5 text-white"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
              />
            </svg>
          </div>
          <h2 className="text-lg font-bold text-slate-100 tracking-tight">
            Answer
          </h2>
        </div>
        <p className="text-slate-200 leading-relaxed text-[15px]">
          {response.answer}
        </p>
      </div>

      {/* Evidence section */}
      {response.evidence.length > 0 && (
        <div>
          <div className="flex items-center gap-2 mb-4">
            <div className="h-6 w-6 rounded-lg bg-gradient-to-br from-amber-500 to-orange-500 flex items-center justify-center">
              <svg
                className="h-3.5 w-3.5 text-white"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
            </div>
            <h2 className="text-lg font-bold text-slate-100 tracking-tight">
              Supporting Evidence
            </h2>
            <span className="ml-auto text-xs text-slate-500 bg-slate-800/60 px-2.5 py-1 rounded-full">
              {response.evidence.length} segment{response.evidence.length !== 1 ? 's' : ''}
            </span>
          </div>
          <div className="space-y-3">
            {response.evidence.map((ev, i) => (
              <EvidenceCard key={`${ev.speaker}-${ev.timestamp}-${i}`} evidence={ev} index={i} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
