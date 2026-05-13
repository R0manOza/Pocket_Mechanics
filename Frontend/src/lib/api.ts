import type { GenerateResponse, StreamEvent } from "./types"

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000"
const BEARER_TOKEN = (import.meta.env.VITE_BEARER_TOKEN ?? "").trim()

function authHeaders(): Record<string, string> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  }
  if (BEARER_TOKEN) {
    headers["Authorization"] = `Bearer ${BEARER_TOKEN}`
  }
  return headers
}

export async function checkHealth(signal?: AbortSignal): Promise<boolean> {
  try {
    const r = await fetch(`${API_BASE_URL}/health`, { signal })
    return r.ok
  } catch {
    return false
  }
}

export async function generate(
  prompt: string,
  signal?: AbortSignal,
): Promise<GenerateResponse> {
  const r = await fetch(`${API_BASE_URL}/api/ai/generate`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({ prompt }),
    signal,
  })
  if (!r.ok) {
    throw new Error(`generate failed: ${r.status}`)
  }
  return (await r.json()) as GenerateResponse
}

// SSE streaming via fetch + ReadableStream — EventSource cannot POST bodies.
export async function* streamChat(args: {
  message: string
  sessionId: string
  signal?: AbortSignal
}): AsyncGenerator<StreamEvent, void, void> {
  const r = await fetch(`${API_BASE_URL}/api/ai/stream`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({ message: args.message, session_id: args.sessionId }),
    signal: args.signal,
  })

  if (!r.ok || !r.body) {
    throw new Error(`stream failed: ${r.status}`)
  }

  const reader = r.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ""

  while (true) {
    const { value, done } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })

    // SSE messages are separated by a blank line. Lines start with "data: ".
    let nlIdx
    while ((nlIdx = buffer.indexOf("\n\n")) !== -1) {
      const rawEvent = buffer.slice(0, nlIdx)
      buffer = buffer.slice(nlIdx + 2)
      const dataLine = rawEvent
        .split("\n")
        .find((l) => l.startsWith("data: "))
      if (!dataLine) continue
      const payload = dataLine.slice("data: ".length).trim()
      if (payload === "[DONE]") {
        yield { kind: "done" }
        return
      }
      try {
        const parsed = JSON.parse(payload) as Record<string, unknown>
        if (typeof parsed.token === "string") {
          yield { kind: "token", token: parsed.token }
        } else if (parsed.usage && typeof parsed.usage === "object") {
          yield { kind: "usage", usage: parsed.usage as StreamEvent extends { kind: "usage"; usage: infer U } ? U : never }
        } else if (typeof parsed.error === "string") {
          yield { kind: "error", message: parsed.error }
        }
      } catch {
        // Ignore malformed payloads; backend may emit text-only "[DONE]" etc.
      }
    }
  }
}
