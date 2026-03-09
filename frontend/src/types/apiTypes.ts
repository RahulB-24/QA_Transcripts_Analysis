/**
 * API Type Definitions
 * ====================
 * TypeScript interfaces for communication with the backend API.
 */

/** Single piece of evidence returned with an answer. */
export interface Evidence {
  speaker: string;
  text: string;
  timestamp: number;
  trust_score: number;
}

/** Response body from the POST /ask endpoint. */
export interface AskResponse {
  answer: string;
  evidence: Evidence[];
}

/** Request body for the POST /ask endpoint. */
export interface AskRequest {
  meeting_id: string;
  question: string;
}
