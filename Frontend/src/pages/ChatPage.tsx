import { useRef, useState } from "react"
import { ChatWindow } from "../components/ChatWindow"
import { ErrorState } from "../components/ErrorState"
import { useSession } from "../hooks/useSession"
import { useStream } from "../hooks/useStream"

const MAX_BYTES = 5 * 1024 * 1024 // 5 MB

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
  const [attachedFile, setAttachedFile] = useState<File | null>(null)
  const [attachedPreviewUrl, setAttachedPreviewUrl] = useState<string | null>(null)
  const [attachError, setAttachError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement | null>(null)

  function onPickFile(file: File) {
    if (!file.type.startsWith("image/")) {
      setAttachError("Please choose an image file.")
      return
    }
    if (file.size > MAX_BYTES) {
      setAttachError("That image is over 5 MB — try a smaller photo.")
      return
    }
    if (attachedPreviewUrl) URL.revokeObjectURL(attachedPreviewUrl)
    setAttachError(null)
    setAttachedFile(file)
    setAttachedPreviewUrl(URL.createObjectURL(file))
  }

  function clearAttachment() {
    if (attachedPreviewUrl) URL.revokeObjectURL(attachedPreviewUrl)
    setAttachedFile(null)
    setAttachedPreviewUrl(null)
    setAttachError(null)
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    const message = input.trim()
    if ((!message && !attachedFile) || isStreaming) return
    setInput("")
    // Ownership of the preview URL transfers to the history entry — do NOT revoke here.
    // The URL stays alive until the page unmounts or history is cleared (small accepted leak).
    const attachment =
      attachedFile && attachedPreviewUrl
        ? { file: attachedFile, previewUrl: attachedPreviewUrl }
        : undefined
    setAttachedFile(null)
    setAttachedPreviewUrl(null)
    setAttachError(null)
    await send(message, attachment)
  }

  function onReset() {
    clearHistory()
    resetSession()
  }

  const canSubmit = (input.trim().length > 0 || !!attachedFile) && !isStreaming

  return (
    <div className="flex w-full justify-center max-w-6xl 2xl:max-w-7xl mx-auto gap-4 2xl:gap-6 h-full">
      <aside className="hidden md:flex w-60 2xl:w-72 shrink-0 flex-col py-3 2xl:py-4">
        <div className="flex h-full flex-col overflow-hidden rounded-2xl border border-brand-border bg-brand-card/40 backdrop-blur">
          <header className="flex items-center justify-between gap-2 border-b border-brand-border px-3 py-2.5 2xl:px-4 2xl:py-3">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-brand-text-muted">
              Sessions
            </h2>
            <button
              type="button"
              onClick={onReset}
              aria-label="Start a new chat"
              title="New chat"
              className="inline-flex h-7 w-7 items-center justify-center rounded-lg border border-brand-border bg-brand-card text-brand-text-muted transition-colors hover:cursor-pointer hover:border-brand-accent hover:bg-brand-card-soft hover:text-brand-text"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                aria-hidden="true"
              >
                <line x1="12" y1="5" x2="12" y2="19" />
                <line x1="5" y1="12" x2="19" y2="12" />
              </svg>
            </button>
          </header>

          <div className="flex-1 overflow-y-auto p-2">
            <div className="rounded-lg bg-gradient-to-br from-brand-card-soft via-brand-card-soft to-brand-glow/30 px-2.5 py-2 2xl:px-3 2xl:py-2.5 shadow-inner">
              <div className="flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-brand-accent shadow-[0_0_8px_rgba(167,139,250,0.7)]" />
                <p className="text-sm font-medium text-brand-text">Active chat</p>
              </div>
              {sessionId && (
                <p className="mt-1 truncate pl-4 text-xs text-brand-text-muted">
                  <code>{sessionId.slice(0, 8)}…</code>
                </p>
              )}
            </div>
            <p className="mt-6 px-2 text-center text-xs text-brand-text-muted/60">
              Past sessions will appear here.
            </p>
          </div>
        </div>
      </aside>
   <div className="flex h-full w-full max-w-4xl 2xl:max-w-5xl flex-col gap-2.5 py-3 2xl:gap-3 2xl:py-4">
      <div className="rounded-2xl border border-brand-border bg-brand-card/40 backdrop-blur h-full">
        <ChatWindow
          history={history}
          pendingAssistant={pendingAssistant}
          isStreaming={isStreaming}
        />
      </div>

      {error && (
        <ErrorState message={error.message} onRetry={retry} retryLabel="Try Again" />
      )}

      {attachError && (
        <p className="text-xs text-brand-primary">{attachError}</p>
      )}

      {attachedPreviewUrl && attachedFile && (
        <div className="flex items-center gap-3 rounded-xl border border-brand-border bg-brand-card/60 backdrop-blur p-2">
          <img
            src={attachedPreviewUrl}
            alt="Selected attachment"
            className="h-12 w-16 rounded-lg object-cover"
          />
          <div className="flex-1 min-w-0 text-xs text-brand-text-muted">
            <p className="truncate font-medium text-brand-text">{attachedFile.name}</p>
            <p>{(attachedFile.size / 1024).toFixed(0)} KB · {attachedFile.type}</p>
          </div>
          <button
            type="button"
            onClick={clearAttachment}
            aria-label="Remove attachment"
            className="inline-flex items-center gap-1.5 rounded-lg border border-brand-border bg-brand-card px-3 py-2 text-xs font-medium text-brand-text-muted transition-colors hover:cursor-pointer hover:border-brand-accent hover:bg-brand-card-soft hover:text-brand-text"
          >
            Remove
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>
      )}

      <form onSubmit={onSubmit} className="flex items-center gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="What does the check engine light mean?"
          className="flex-1 rounded-xl border border-brand-border bg-brand-card px-3.5 py-2.5 2xl:px-4 2xl:py-3 text-sm text-brand-text placeholder:text-brand-text-muted/60 outline-none transition-colors focus:border-brand-accent disabled:opacity-60"
          disabled={isStreaming}
        />
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0]
            if (file) onPickFile(file)
            e.target.value = ""
          }}
        />
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          disabled={isStreaming}
          aria-label="Attach an image"
          className="inline-flex items-center justify-center rounded-xl border border-brand-border bg-brand-card px-3 2xl:px-4 h-full text-brand-text-muted shadow-sm transition-colors hover:cursor-pointer hover:border-brand-accent hover:bg-brand-card-soft hover:text-brand-text disabled:cursor-not-allowed disabled:opacity-60"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="22"
            height="22"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
          >
            <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48" />
          </svg>
        </button>
        <button
          type="submit"
          disabled={!canSubmit}
          aria-label={isStreaming ? "Sending message" : "Send message"}
          className="inline-flex items-center justify-center rounded-xl bg-brand-accent px-5 2xl:px-6 h-full text-white shadow-sm transition-colors hover:cursor-pointer hover:bg-brand-glow-soft disabled:cursor-not-allowed disabled:bg-brand-card-soft disabled:text-brand-text-muted disabled:shadow-none disabled:hover:bg-brand-card-soft disabled:hover:text-brand-text-muted"
        >
          {isStreaming ? (
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="animate-spin"
              aria-hidden="true"
            >
              <path d="M21 12a9 9 0 1 1-6.219-8.56" />
            </svg>
          ) : (
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="24"
              height="24"
              viewBox="5 5 14 14"
              fill="none"
              aria-hidden="true"
            >
              <path
                d="M6.99811 10.2467L7.43298 11.0077C7.70983 11.4922 7.84825 11.7344 7.84825 12C7.84825 12.2656 7.70983 12.5078 7.43299 12.9923L7.43298 12.9923L6.99811 13.7533C5.75981 15.9203 5.14066 17.0039 5.62348 17.5412C6.1063 18.0785 7.24961 17.5783 9.53623 16.5779L15.8119 13.8323C17.6074 13.0468 18.5051 12.654 18.5051 12C18.5051 11.346 17.6074 10.9532 15.8119 10.1677L9.53624 7.4221C7.24962 6.42171 6.1063 5.92151 5.62348 6.45883C5.14066 6.99615 5.75981 8.07966 6.99811 10.2467Z"
                fill="currentColor"
              />
            </svg>
          )}
        </button>
      </form>
    </div>
    </div>
  )
}
