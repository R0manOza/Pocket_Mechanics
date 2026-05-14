import type { GenerateResponse, StreamEvent } from "./types"

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000"
const BEARER_TOKEN = (import.meta.env.VITE_BEARER_TOKEN ?? "").trim()

/** FastAPI often returns `{ "detail": "..." }` or a validation array. */
async function readHttpErrorDetail(r: Response): Promise<string> {
  try {
    const data: unknown = await r.json()
    if (data && typeof data === "object" && "detail" in data) {
      const detail = (data as { detail: unknown }).detail
      if (typeof detail === "string") return detail
      if (Array.isArray(detail)) {
        const first = detail[0] as { msg?: string; type?: string } | undefined
        if (first && typeof first.msg === "string") return first.msg
        return JSON.stringify(detail)
      }
    }
  } catch {
    try {
      const t = await r.text()
      if (t && t.length < 800) return t
    } catch {
      /* ignore */
    }
  }
  return r.statusText || `HTTP ${r.status}`
}

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
  opts?: { images?: string[]; signal?: AbortSignal },
): Promise<GenerateResponse> {
  const body: Record<string, unknown> = { prompt }
  if (opts?.images?.length) body.images = opts.images
  const r = await fetch(`${API_BASE_URL}/api/ai/generate`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify(body),
    signal: opts?.signal,
  })
  if (!r.ok) {
    const detail = await readHttpErrorDetail(r)
    throw new Error(`Analysis failed (${r.status}): ${detail}`)
  }
  return (await r.json()) as GenerateResponse
}

/** Read a local image file as a `data:image/...;base64,...` URL for the vision API. */
export function fileToDataUrl(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(String(reader.result))
    reader.onerror = () => reject(reader.error ?? new Error("read failed"))
    reader.readAsDataURL(file)
  })
}

function looksLikeHeic(file: File): boolean {
  const n = file.name.toLowerCase()
  return (
    file.type === "image/heic" ||
    file.type === "image/heif" ||
    n.endsWith(".heic") ||
    n.endsWith(".heif")
  )
}

/**
 * Same as {@link fileToDataUrl} for JPEG/PNG/WebP/GIF.
 * iPhone "High Efficiency" photos (HEIC/HEIF) are converted to JPEG in-browser so
 * OpenRouter / vision APIs always receive a widely supported format.
 */
export async function fileToVisionDataUrl(file: File): Promise<string> {
  if (!looksLikeHeic(file)) {
    return fileToDataUrl(file)
  }
  const heic2any = (await import("heic2any")).default
  const converted = await heic2any({
    blob: file,
    toType: "image/jpeg",
    quality: 0.92,
  })
  const blob = Array.isArray(converted) ? converted[0] : converted
  return fileToDataUrl(new File([blob], "photo.jpg", { type: "image/jpeg" }))
}

// SSE streaming via fetch + ReadableStream — EventSource cannot POST bodies.
export async function* streamChat(args: {
  message: string
  sessionId: string
  images?: string[]
  signal?: AbortSignal
}): AsyncGenerator<StreamEvent, void, void> {
  const body: Record<string, unknown> = {
    message: args.message,
    session_id: args.sessionId,
  }
  if (args.images?.length) body.images = args.images

  const r = await fetch(`${API_BASE_URL}/api/ai/stream`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify(body),
    signal: args.signal,
  })

  if (!r.ok) {
    const detail = await readHttpErrorDetail(r)
    throw new Error(`Chat request failed (${r.status}): ${detail}`)
  }
  if (!r.body) {
    throw new Error(`Chat request failed (${r.status}): empty response body`)
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
