export type ChatRole = "user" | "assistant"

export interface ChatMessage {
  role: ChatRole
  content: string
  // Object URL for an image attached to a user message. Created in ChatPage
  // and held until the page unmounts or history is cleared (small accepted leak).
  imageUrl?: string
}

// Mirrors Backend/models/request_models.py::GenerateResponse
export interface GenerateResponse {
  content: string
  model: string
  input_tokens: number
  output_tokens: number
  cache_read_tokens: number
  cache_write_tokens: number
  latency_ms: number
  fallback_triggered: boolean
  cost_usd: number
}

// Stream events emitted by Backend/routers/stream_router.py
export type StreamEvent =
  | { kind: "token"; token: string }
  | {
      kind: "gate"
      gate: {
        type: "repair_steps"
        approval_required: boolean
        message: string
      }
    }
  | {
      kind: "usage"
      usage: {
        input_tokens: number
        output_tokens: number
        stream_start_ms: number
        stream_end_ms: number
        latency_ms: number
        cache_read_tokens?: number
        cache_write_tokens?: number
        fallback_triggered?: boolean
        approval_required?: boolean
        approved?: boolean
      }
    }
  | { kind: "error"; message: string }
  | { kind: "done" }

export interface RepairApprovalPending {
  message: string
  images?: string[]
  previewUrl?: string
}

export type ChatErrorReason = "network" | "policy" | "low_confidence" | "unknown"

export interface ChatError {
  reason: ChatErrorReason
  message: string
}

export interface AiModelOption {
  id: string
  label: string
  input_usd_per_million: number
  output_usd_per_million: number
}

export interface ModelsResponse {
  default: string
  models: AiModelOption[]
}
