/**
 * MeetingSelector Component
 * =========================
 * Premium dropdown to select a meeting from the available list.
 */

interface MeetingSelectorProps {
  meetings: string[];
  selectedMeeting: string;
  onSelect: (meetingId: string) => void;
  loading: boolean;
}

export default function MeetingSelector({
  meetings,
  selectedMeeting,
  onSelect,
  loading,
}: MeetingSelectorProps) {
  return (
    <div className="w-full">
      <label
        htmlFor="meeting-select"
        className="block text-sm font-semibold text-slate-300 mb-2 tracking-wide uppercase"
      >
        Select Meeting
      </label>
      <div className="relative">
        <select
          id="meeting-select"
          value={selectedMeeting}
          onChange={(e) => onSelect(e.target.value)}
          disabled={loading}
          className="w-full appearance-none bg-slate-800/60 backdrop-blur-sm border border-slate-600/50 text-slate-100 rounded-xl px-4 py-3.5 pr-10 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500/60 focus:border-violet-500/60 transition-all duration-300 hover:border-slate-500 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer shadow-lg"
        >
          <option value="">
            {loading ? '⏳ Loading meetings…' : '— Choose a meeting —'}
          </option>
          {meetings.map((id) => (
            <option key={id} value={id}>
              {id}
            </option>
          ))}
        </select>
        {/* Custom chevron */}
        <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-3">
          <svg
            className="h-4 w-4 text-slate-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 9l-7 7-7-7"
            />
          </svg>
        </div>
      </div>
      {selectedMeeting && (
        <p className="mt-2 text-xs text-violet-400 animate-pulse">
          Meeting <span className="font-mono font-bold">{selectedMeeting}</span> selected
        </p>
      )}
    </div>
  );
}
