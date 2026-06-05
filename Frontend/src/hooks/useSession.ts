import { useCallback, useState } from "react"
import {
  listSessions,
  readSessionId,
  type SessionMeta,
  upsertSession,
  writeSessionId,
} from "../lib/sessionStorage"

export function useSession() {
  const [sessionId, setSessionId] = useState<string>(readSessionId)
  const [sessions, setSessions] = useState<SessionMeta[]>(listSessions)

  const refreshSessions = useCallback(() => {
    setSessions(listSessions())
  }, [])

  const selectSession = useCallback((id: string) => {
    writeSessionId(id)
    setSessionId(id)
  }, [])

  const startNewSession = useCallback(
    (currentTitle?: string) => {
      if (currentTitle) {
        upsertSession({
          id: sessionId,
          title: currentTitle,
          updatedAt: Date.now(),
        })
      }
      const fresh = crypto.randomUUID()
      writeSessionId(fresh)
      setSessionId(fresh)
      refreshSessions()
      return fresh
    },
    [sessionId, refreshSessions],
  )

  const touchSession = useCallback(
    (title: string) => {
      upsertSession({
        id: sessionId,
        title,
        updatedAt: Date.now(),
      })
      refreshSessions()
    },
    [sessionId, refreshSessions],
  )

  return {
    sessionId,
    sessions,
    selectSession,
    startNewSession,
    touchSession,
    refreshSessions,
  }
}
