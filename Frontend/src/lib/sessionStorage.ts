import type { ChatMessage } from "./types"

const SESSION_ID_KEY = "pocket-mechanics:session_id"
const SESSIONS_KEY = "pocket-mechanics:sessions"
const CHAT_PREFIX = "pocket-mechanics:chat:"

export interface SessionMeta {
  id: string
  title: string
  updatedAt: number
}

function readJson<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key)
    if (!raw) return fallback
    return JSON.parse(raw) as T
  } catch {
    return fallback
  }
}

export function readSessionId(): string {
  const existing = localStorage.getItem(SESSION_ID_KEY)
  if (existing) return existing
  const fresh = crypto.randomUUID()
  localStorage.setItem(SESSION_ID_KEY, fresh)
  return fresh
}

export function writeSessionId(id: string): void {
  localStorage.setItem(SESSION_ID_KEY, id)
}

export function listSessions(): SessionMeta[] {
  const sessions = readJson<SessionMeta[]>(SESSIONS_KEY, [])
  return [...sessions].sort((a, b) => b.updatedAt - a.updatedAt)
}

export function upsertSession(meta: SessionMeta): void {
  const sessions = listSessions().filter((s) => s.id !== meta.id)
  sessions.unshift(meta)
  localStorage.setItem(SESSIONS_KEY, JSON.stringify(sessions.slice(0, 30)))
}

export function titleFromMessage(text: string): string {
  const t = text.trim().replace(/\s+/g, " ")
  if (!t) return "New chat"
  return t.length > 48 ? `${t.slice(0, 48)}…` : t
}

export function loadChatHistory(sessionId: string): ChatMessage[] {
  return readJson<ChatMessage[]>(`${CHAT_PREFIX}${sessionId}`, [])
}

export function saveChatHistory(sessionId: string, history: ChatMessage[]): void {
  // imageUrl is a blob: URL — strip before persist (cannot survive reload)
  const serializable = history.map(({ role, content }) => ({ role, content }))
  localStorage.setItem(`${CHAT_PREFIX}${sessionId}`, JSON.stringify(serializable))
}
