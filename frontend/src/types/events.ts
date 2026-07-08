export type VerdictType = "TRUE" | "FALSE" | "UNCERTAIN";

export interface TranscriptEvent {
  type: "transcript";
  speaker: number;
  text: string;
  is_final: boolean;
  timestamp_ms: number;
}

export interface VerdictEvent {
  type: "verdict";
  claim: string;
  verdict: VerdictType;
  confidence: number;
  rationale: string;
  sources: Array<{
    text: string;
    filename: string;
    page?: number;
    score: number;
  }>;
  latency_ms: number;
  used_web_search: boolean;
}

export interface QuestionsEvent {
  type: "questions";
  segment: string;
  questions: string[];
}

export interface StatusEvent {
  type: "status";
  message: string;
}

export interface ErrorEvent {
  type: "error";
  message: string;
}

export type ServerEvent =
  | TranscriptEvent
  | VerdictEvent
  | QuestionsEvent
  | StatusEvent
  | ErrorEvent;

export interface TranscriptLine {
  id: string;
  speaker: number;
  text: string;
  isFinal: boolean;
}

export interface SessionConfig {
  deepgram_api_key?: string;
  llm_provider: "openai" | "anthropic";
  llm_api_key?: string;
  openai_api_key?: string;
  anthropic_api_key?: string;
  tavily_api_key?: string;
}
