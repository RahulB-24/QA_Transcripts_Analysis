/**
 * API Service
 * ===========
 * Functions for communicating with the Trust-Weighted QA backend.
 */

import type { AskResponse } from '../types/apiTypes';

const BASE_URL = '';   // proxied via vite.config.ts in dev

/**
 * Fetch the list of available meeting IDs.
 */
export async function fetchMeetings(): Promise<string[]> {
  const res = await fetch(`${BASE_URL}/meetings`);
  if (!res.ok) {
    throw new Error(`Failed to fetch meetings: ${res.statusText}`);
  }
  return res.json() as Promise<string[]>;
}

/**
 * Ask a question about a specific meeting.
 */
export async function askQuestion(
  meetingId: string,
  question: string,
): Promise<AskResponse> {
  const res = await fetch(`${BASE_URL}/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ meeting_id: meetingId, question }),
  });
  if (!res.ok) {
    const errBody = await res.text();
    throw new Error(`Failed to ask question: ${res.statusText} — ${errBody}`);
  }
  return res.json() as Promise<AskResponse>;
}
