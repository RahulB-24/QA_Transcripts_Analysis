/**
 * App Component
 * =============
 * Root application component. Manages state and orchestrates the
 * meeting selection → question → answer flow.
 */

import { useEffect, useState } from 'react';
import type { AskResponse } from './types/apiTypes';
import { fetchMeetings, askQuestion } from './services/api';
import MeetingSelector from './components/MeetingSelector';
import QuestionBox from './components/QuestionBox';
import AnswerPanel from './components/AnswerPanel';

export default function App() {
  // ── State ─────────────────────────────────────────────────────────
  const [meetings, setMeetings] = useState<string[]>([]);
  const [selectedMeeting, setSelectedMeeting] = useState('');
  const [loadingMeetings, setLoadingMeetings] = useState(true);
  const [loadingAnswer, setLoadingAnswer] = useState(false);
  const [response, setResponse] = useState<AskResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  // ── Fetch meeting list on mount ───────────────────────────────────
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const ids = await fetchMeetings();
        if (!cancelled) {
          setMeetings(ids);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to load meetings');
        }
      } finally {
        if (!cancelled) setLoadingMeetings(false);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  // ── Handle question submission ────────────────────────────────────
  const handleAsk = async (question: string) => {
    if (!selectedMeeting) return;
    setLoadingAnswer(true);
    setError(null);
    setResponse(null);
    try {
      const res = await askQuestion(selectedMeeting, question);
      setResponse(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong');
    } finally {
      setLoadingAnswer(false);
    }
  };

  // ── Render ────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950 text-white">
      {/* Subtle grid pattern overlay */}
      <div className="fixed inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI2MCIgaGVpZ2h0PSI2MCI+PGRlZnM+PHBhdHRlcm4gaWQ9ImdyaWQiIHdpZHRoPSI2MCIgaGVpZ2h0PSI2MCIgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSI+PHBhdGggZD0iTSA2MCAwIEwgMCAwIDAgNjAiIGZpbGw9Im5vbmUiIHN0cm9rZT0icmdiYSgyNTUsMjU1LDI1NSwwLjAyKSIgc3Ryb2tlLXdpZHRoPSIxIi8+PC9wYXR0ZXJuPjwvZGVmcz48cmVjdCBmaWxsPSJ1cmwoI2dyaWQpIiB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIi8+PC9zdmc+')] opacity-100 pointer-events-none" />

      <div className="relative z-10 max-w-3xl mx-auto px-4 py-12 sm:px-6 lg:px-8">
        {/* Header */}
        <header className="text-center mb-12">
          <div className="inline-flex items-center gap-2 bg-violet-500/10 text-violet-400 px-4 py-1.5 rounded-full text-xs font-semibold tracking-wider uppercase mb-6 border border-violet-500/20">
            <span className="h-1.5 w-1.5 bg-violet-400 rounded-full animate-pulse" />
            AI-Powered Meeting Intelligence
          </div>
          <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight bg-gradient-to-r from-white via-slate-200 to-violet-300 bg-clip-text text-transparent">
            Trust-Weighted QA
          </h1>
          <p className="mt-4 text-slate-400 text-base sm:text-lg max-w-xl mx-auto leading-relaxed">
            Ask questions about AMI meeting transcripts and get answers grounded
            in evidence, weighted by speaker reliability.
          </p>
        </header>

        {/* Controls */}
        <div className="space-y-5 mb-10">
          <MeetingSelector
            meetings={meetings}
            selectedMeeting={selectedMeeting}
            onSelect={(id) => {
              setSelectedMeeting(id);
              setResponse(null);
              setError(null);
            }}
            loading={loadingMeetings}
          />
          <QuestionBox
            onSubmit={handleAsk}
            disabled={!selectedMeeting}
            loading={loadingAnswer}
          />
        </div>

        {/* Error display */}
        {error && (
          <div className="mb-8 bg-rose-500/10 border border-rose-500/30 text-rose-300 rounded-xl px-5 py-4 text-sm animate-in">
            <span className="font-semibold">Error:</span> {error}
          </div>
        )}

        {/* Loading skeleton */}
        {loadingAnswer && (
          <div className="space-y-4 mb-8 animate-pulse">
            <div className="bg-slate-800/40 rounded-2xl p-6 space-y-3">
              <div className="h-4 bg-slate-700/50 rounded w-1/3" />
              <div className="h-4 bg-slate-700/50 rounded w-full" />
              <div className="h-4 bg-slate-700/50 rounded w-5/6" />
            </div>
            {[1, 2, 3].map((i) => (
              <div key={i} className="bg-slate-800/40 rounded-xl p-5 space-y-3">
                <div className="h-3 bg-slate-700/50 rounded w-1/4" />
                <div className="h-3 bg-slate-700/50 rounded w-full" />
                <div className="h-2 bg-slate-700/50 rounded w-2/3" />
              </div>
            ))}
          </div>
        )}

        {/* Answer + evidence */}
        <AnswerPanel response={response} />

        {/* Footer */}
        <footer className="mt-16 text-center text-xs text-slate-600">
          Powered by Flan-T5 · Sentence-Transformers · FAISS · AMI Corpus
        </footer>
      </div>
    </div>
  );
}
