import { useCallback, useState } from "react"

const STORAGE_KEY = "pocket-mechanics:session_id"

function readOrCreate(): string {
  if (typeof window === "undefined") return ""
  const existing = window.localStorage.getItem(STORAGE_KEY)
  if (existing) return existing
  const fresh = crypto.randomUUID()
  window.localStorage.setItem(STORAGE_KEY, fresh)
  return fresh
}

export function useSession() {
  // Lazy initializer — runs once at mount, synchronously during the first render.
  // Avoids the `react-hooks/set-state-in-effect` rule by not needing useEffect at all.
  const [sessionId, setSessionId] = useState<string>(readOrCreate)

  const resetSession = useCallback(() => {
    const fresh = crypto.randomUUID()
    window.localStorage.setItem(STORAGE_KEY, fresh)
    setSessionId(fresh)
  }, [])

  return { sessionId, resetSession }
}
