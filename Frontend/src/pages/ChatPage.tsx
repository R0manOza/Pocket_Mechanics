import { useEffect, useRef, useState } from "react"
import { ChatInput } from "../components/ChatInput"
import { ChatWindow } from "../components/ChatWindow"
import { ErrorState } from "../components/ErrorState"
import { ModelSelect } from "../components/ModelSelect"
import { RepairApprovalBanner } from "../components/RepairApprovalBanner"
import { fetchModels } from "../lib/api"
import { saveChatHistory, titleFromMessage } from "../lib/sessionStorage"
import type { AiModelOption } from "../lib/types"
import { useSession } from "../hooks/useSession"
import { useStream } from "../hooks/useStream"

const MAX_BYTES = 5 * 1024 * 1024 // 5 MB
const MODEL_PREF_KEY = "pocket-mechanics:preferred_model"

const FALLBACK_MODELS: AiModelOption[] = [
  {
    id: "google/gemini-2.5-flash",
    label: "Gemini 2.5 Flash",
    input_usd_per_million: 0.15,
    output_usd_per_million: 0.6,
  },
  {
    id: "openai/gpt-5-nano",
    label: "GPT-5 Nano",
    input_usd_per_million: 0.05,
    output_usd_per_million: 0.4,
  },
]

export function ChatPage() {
  const { sessionId, sessions, selectSession, startNewSession, touchSession } =
    useSession()
  const [model, setModel] = useState(
    () => localStorage.getItem(MODEL_PREF_KEY) ?? "google/gemini-2.5-flash",
  )
  const [models, setModels] = useState<AiModelOption[]>(FALLBACK_MODELS)

  const {
    history,
    pendingAssistant,
    isStreaming,
    error,
    repairApproval,
    send,
    confirmRepairSteps,
    dismissRepairApproval,
    retry,
  } = useStream(sessionId, touchSession, model)

  const [input, setInput] = useState("")
  const [attachedFile, setAttachedFile] = useState<File | null>(null)
  const [attachedPreviewUrl, setAttachedPreviewUrl] = useState<string | null>(null)
  const [attachError, setAttachError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement | null>(null)

  useEffect(() => {
    fetchModels()
      .then((res) => {
        if (res.models.length) setModels(res.models)
        const preferred = localStorage.getItem(MODEL_PREF_KEY)
        if (!preferred && res.default) {
          setModel(res.default)
        }
      })
      .catch(() => {
        /* keep FALLBACK_MODELS */
      })
  }, [])

  function onModelChange(id: string) {
    setModel(id)
    localStorage.setItem(MODEL_PREF_KEY, id)
  }

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

  async function onSubmit() {
    const message = input.trim()
    if ((!message && !attachedFile) || isStreaming) return
    setInput("")
    const attachment =
      attachedFile && attachedPreviewUrl
        ? { file: attachedFile, previewUrl: attachedPreviewUrl }
        : undefined
    setAttachedFile(null)
    setAttachedPreviewUrl(null)
    setAttachError(null)
    await send(message, attachment)
  }

  function persistCurrentSession() {
    if (history.length === 0) return
    saveChatHistory(sessionId, history)
    const firstUser = history.find((m) => m.role === "user")
    if (firstUser) {
      touchSession(titleFromMessage(firstUser.content))
    }
  }

  function onNewChat() {
    persistCurrentSession()
    const firstUser = history.find((m) => m.role === "user")
    const title = firstUser ? titleFromMessage(firstUser.content) : undefined
    startNewSession(title)
    // New sessionId triggers useStream to load empty history — do not clear old session storage.
  }

  function onSelectSession(id: string) {
    if (id === sessionId || isStreaming) return
    persistCurrentSession()
    selectSession(id)
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
              onClick={onNewChat}
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

          <div className="flex-1 overflow-y-auto p-2 space-y-1">
            {sessions.length === 0 ? (
              <p className="px-2 py-4 text-center text-xs text-brand-text-muted/60">
                Chats are saved in this browser. Use + to start a new chat and
                keep the current one in this list.
              </p>
            ) : (
              sessions.map((s) => {
                const active = s.id === sessionId
                return (
                  <button
                    key={s.id}
                    type="button"
                    onClick={() => onSelectSession(s.id)}
                    disabled={isStreaming && !active}
                    className={`w-full rounded-lg px-2.5 py-2 text-left text-sm transition-colors disabled:opacity-50 ${
                      active
                        ? "bg-gradient-to-br from-brand-card-soft via-brand-card-soft to-brand-glow/30 text-brand-text"
                        : "text-brand-text-muted hover:bg-brand-card-soft hover:text-brand-text"
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      {active && (
                        <span className="h-2 w-2 shrink-0 rounded-full bg-brand-accent shadow-[0_0_8px_rgba(34,197,94,0.7)]" />
                      )}
                      <p className="truncate font-medium">{s.title}</p>
                    </div>
                    <p className="mt-0.5 pl-4 text-xs opacity-70">
                      {new Date(s.updatedAt).toLocaleDateString()}
                    </p>
                  </button>
                )
              })
            )}
          </div>
        </div>
      </aside>

      <div className="flex h-full w-full max-w-4xl 2xl:max-w-5xl flex-col gap-2.5 py-3 2xl:gap-3 2xl:py-4">
        <div className="flex items-center justify-end px-1">
          <ModelSelect
            models={models}
            value={model}
            onChange={onModelChange}
            disabled={isStreaming}
          />
        </div>

        <div className="rounded-2xl border border-brand-border bg-brand-card/40 backdrop-blur h-full min-h-0 flex-1">
          <ChatWindow
            history={history}
            pendingAssistant={pendingAssistant}
            isStreaming={isStreaming}
          />
        </div>

        {repairApproval && (
          <RepairApprovalBanner
            onConfirm={() => void confirmRepairSteps()}
            onCancel={dismissRepairApproval}
            busy={isStreaming}
          />
        )}

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
              <p>
                {(attachedFile.size / 1024).toFixed(0)} KB · {attachedFile.type}
              </p>
            </div>
            <button
              type="button"
              onClick={clearAttachment}
              aria-label="Remove attachment"
              className="inline-flex items-center gap-1.5 rounded-lg border border-brand-border bg-brand-card px-3 py-2 text-xs font-medium text-brand-text-muted transition-colors hover:cursor-pointer hover:border-brand-accent hover:bg-brand-card-soft hover:text-brand-text"
            >
              Remove
            </button>
          </div>
        )}

        <form
          onSubmit={(e) => {
            e.preventDefault()
            void onSubmit()
          }}
          className="flex items-end gap-2"
        >
          <ChatInput
            value={input}
            onChange={setInput}
            onSubmit={() => void onSubmit()}
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
            className="inline-flex h-11 shrink-0 items-center justify-center rounded-xl border border-brand-border bg-brand-card px-3 text-brand-text-muted shadow-sm transition-colors hover:cursor-pointer hover:border-brand-accent hover:bg-brand-card-soft hover:text-brand-text disabled:cursor-not-allowed disabled:opacity-60"
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
            className="inline-flex h-11 shrink-0 items-center justify-center rounded-xl bg-brand-accent px-5 text-white shadow-sm transition-colors hover:cursor-pointer hover:bg-brand-glow-soft disabled:cursor-not-allowed disabled:bg-brand-card-soft disabled:text-brand-text-muted"
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
                viewBox="0 0 24 24"
                fill="none"
                aria-hidden="true"
              >
                <path
                  d="M6.99811 10.2467L7.43298 11.0077C7.70983 11.4922 7.84825 11.7344 7.84825 12C7.84825 12.2656 7.70983 12.5078 7.43299 12.9923L6.99811 13.7533C5.75981 15.9203 5.14066 17.0039 5.62348 17.5412C6.1063 18.0785 7.24961 17.5783 9.53623 16.5779L15.8119 13.8323C17.6074 13.0468 18.5051 12.654 18.5051 12C18.5051 11.346 17.6074 10.9532 15.8119 10.1677L9.53624 7.4221C7.24962 6.42171 6.1063 5.92151 5.62348 6.45883C5.14066 6.99615 5.75981 8.07966 6.99811 10.2467Z"
                  fill="currentColor"
                />
              </svg>
            )}
          </button>
        </form>
        <p className="text-center text-[10px] text-brand-text-muted/50">
          Enter to send · Shift+Enter for a new line
        </p>
      </div>
    </div>
  )
}
