import { useState } from "react"
import { ChatWindow } from "../components/ChatWindow"
import { ErrorState } from "../components/ErrorState"
import { useSession } from "../hooks/useSession"
import { useStream } from "../hooks/useStream"

export function ChatPage() {
  const { sessionId, resetSession } = useSession()
  const {
    history,
    pendingAssistant,
    isStreaming,
    error,
    send,
    retry,
    clearHistory,
  } = useStream(sessionId)
  const [input, setInput] = useState("")

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    const message = input.trim()
    if (!message || isStreaming) return
    setInput("")
    await send(message)
  }

  function onReset() {
    clearHistory()
    resetSession()
  }

  return (
    <div className="mx-auto flex h-full w-full max-w-3xl flex-col gap-3 px-4 py-4">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-slate-900">Chat</h1>
          <p className="text-xs text-slate-500">
            Ask anything about your car · Lab 6 streaming + memory
          </p>
        </div>
        <button
          type="button"
          onClick={onReset}
          className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50"
        >
          New chat
        </button>
      </header>

      <div className="min-h-0 flex-1 rounded-2xl border border-slate-200 bg-slate-50">
        <ChatWindow
          history={history}
          pendingAssistant={pendingAssistant}
          isStreaming={isStreaming}
        />
      </div>

      {error && (
        <ErrorState message={error.message} onRetry={retry} retryLabel="Try Again" />
      )}

      <form onSubmit={onSubmit} className="flex items-center gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="What does the check engine light mean?"
          className="flex-1 rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none focus:border-slate-500"
          disabled={isStreaming}
        />
        <button
          type="submit"
          disabled={!input.trim() || isStreaming}
          className="rounded-xl bg-slate-900 px-4 py-3 text-sm font-medium text-white disabled:cursor-not-allowed disabled:bg-slate-400"
        >
          {isStreaming ? "Thinking…" : "Send"}
        </button>
      </form>

      {sessionId && (
        <p className="text-[10px] text-slate-400">
          session_id: <code>{sessionId.slice(0, 8)}…</code>
        </p>
      )}
    </div>
  )
}
