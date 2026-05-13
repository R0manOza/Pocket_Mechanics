export type ChatRole = "user" | "assistant"

export interface ChatMessage {
  role: ChatRole
  content: string
}

// Mirrors Backend/models/request_models.py::GenerateResponse
export interface GenerateResponse {
  content: string
  model: string
  input_tokens: number
  output_tokens: number
  latency_ms: number
  cost_usd: number
}

// Stream events emitted by Backend/routers/stream_router.py
export type StreamEvent =
  | { kind: "token"; token: string }
  | {
      kind: "usage"
      usage: {
        input_tokens: number
        output_tokens: number
        stream_start_ms: number
        stream_end_ms: number
        latency_ms: number
      }
    }
  | { kind: "error"; message: string }
  | { kind: "done" }

export type ChatErrorReason = "network" | "policy" | "low_confidence" | "unknown"

export interface ChatError {
  reason: ChatErrorReason
  message: string
}
