export type VerdictType = "TRUE" | "FALSE" | "UNCERTAIN";
export type ClaimClassification = "factual_claim" | "non_claim";

export interface TranscriptEvent {
  type: "transcript";
  speaker: number;
  text: string;
  raw_text?: string;
  is_final: boolean;
  timestamp_ms: number;
  is_factual_claim?: boolean;
  utterance_key?: string;
}

export interface ClaimEvent {
  type: "claim";
  classification: ClaimClassification;
  claim_text: string | null;
  segment: string;
}

export interface VerdictEvent {
  type: "verdict";
  claim: string;
  verdict: VerdictType;
  confidence: number;
  rationale: string;
  source_quote?: string;
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
  | ClaimEvent
  | VerdictEvent
  | QuestionsEvent
  | StatusEvent
  | ErrorEvent;

export interface TranscriptLine {
  id: string;
  speaker: number;
  text: string;
  rawText?: string;
  isFinal: boolean;
  isFactualClaim: boolean;
}

export type LlmProvider = "openai" | "anthropic" | "gemini";
export type EmbeddingProvider = "openai" | "google";

export interface SessionConfig {
  deepgram_api_key?: string;
  llm_provider: LlmProvider;
  llm_api_key?: string;
  embedding_provider?: EmbeddingProvider;
  openai_api_key?: string;
  anthropic_api_key?: string;
  google_api_key?: string;
  tavily_api_key?: string;
}
