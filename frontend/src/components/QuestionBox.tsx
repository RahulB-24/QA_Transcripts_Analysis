/**
 * QuestionBox Component
 * =====================
 * Text input with submit button for asking questions about a meeting.
 */

import { useState } from 'react';

interface QuestionBoxProps {
  onSubmit: (question: string) => void;
  disabled: boolean;
  loading: boolean;
}

export default function QuestionBox({
  onSubmit,
  disabled,
  loading,
}: QuestionBoxProps) {
  const [question, setQuestion] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = question.trim();
    if (trimmed) {
      onSubmit(trimmed);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="w-full">
      <label
        htmlFor="question-input"
        className="block text-sm font-semibold text-slate-300 mb-2 tracking-wide uppercase"
      >
        Ask a Question
      </label>
      <div className="flex gap-3">
        <div className="relative flex-1">
          <input
            id="question-input"
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="e.g. What decisions were made about the remote control design?"
            disabled={disabled || loading}
            className="w-full bg-slate-800/60 backdrop-blur-sm border border-slate-600/50 text-slate-100 placeholder-slate-500 rounded-xl px-4 py-3.5 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500/60 focus:border-violet-500/60 transition-all duration-300 hover:border-slate-500 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg"
          />
          {loading && (
            <div className="absolute inset-y-0 right-3 flex items-center">
              <div className="h-4 w-4 border-2 border-violet-400 border-t-transparent rounded-full animate-spin" />
            </div>
          )}
        </div>
        <button
          type="submit"
          disabled={disabled || loading || !question.trim()}
          className="px-6 py-3.5 bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white font-semibold rounded-xl text-sm transition-all duration-300 shadow-lg shadow-violet-900/30 disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:from-violet-600 disabled:hover:to-indigo-600 active:scale-[0.97] cursor-pointer"
        >
          {loading ? (
            <span className="flex items-center gap-2">
              <div className="h-4 w-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              Processing
            </span>
          ) : (
            'Ask'
          )}
        </button>
      </div>
    </form>
  );
}
