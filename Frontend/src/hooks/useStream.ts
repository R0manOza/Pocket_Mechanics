import { useCallback, useReducer, useRef } from "react"
import { fileToVisionDataUrl, streamChat } from "../lib/api"
import type { ChatError, ChatMessage } from "../lib/types"

type State = {
  history: ChatMessage[]
  pendingAssistant: string
  isStreaming: boolean
  error: ChatError | null
  // Cached so "Try Again" can replay without retyping.
  lastUserMessage: string | null
}
//hello tornike , and helloo agian , hi again pls deploy
type Action =
  | { type: "begin"; user: string; imageUrl?: string }
  | { type: "token"; token: string }
  | { type: "commit_assistant" }
  | { type: "stream_error"; error: ChatError }
  | { type: "reset_error" }
  | { type: "clear_history" }

const initial: State = {
  history: [],
  pendingAssistant: "",
  isStreaming: false,
  error: null,
  lastUserMessage: null,
}

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case "begin":
      return {
        ...state,
        isStreaming: true,
        pendingAssistant: "",
        error: null,
        lastUserMessage: action.user,
        history: [
          ...state.history,
          { role: "user", content: action.user, imageUrl: action.imageUrl },
        ],
      }
    case "token":
      return { ...state, pendingAssistant: state.pendingAssistant + action.token }
    case "commit_assistant": {
      const finished = state.pendingAssistant.trim()
      if (!finished) {
        return { ...state, isStreaming: false, pendingAssistant: "" }
      }
      return {
        ...state,
        isStreaming: false,
        pendingAssistant: "",
        history: [...state.history, { role: "assistant", content: finished }],
      }
    }
    case "stream_error":
      return { ...state, isStreaming: false, error: action.error }
    case "reset_error":
      return { ...state, error: null }
    case "clear_history":
      return { ...initial }
    default:
      return state
  }
}

export function useStream(sessionId: string) {
  const [state, dispatch] = useReducer(reducer, initial)
  const controllerRef = useRef<AbortController | null>(null)
  const lastStreamArgsRef = useRef<{
    message: string
    images?: string[]
    previewUrl?: string
  } | null>(null)

  const send = useCallback(
    async (
      message: string,
      attachment?: { file?: File; previewUrl?: string; images?: string[] },
    ) => {
      const hasFile = Boolean(attachment?.file)
      const hasPresetImages = Boolean(attachment?.images?.length)
      if ((!message.trim() && !hasFile && !hasPresetImages) || !sessionId || state.isStreaming)
        return

      controllerRef.current?.abort()
      const controller = new AbortController()
      controllerRef.current = controller

      let images = attachment?.images
      if (!images?.length && attachment?.file) {
        images = [await fileToVisionDataUrl(attachment.file)]
      }

      lastStreamArgsRef.current = {
        message,
        images: images?.length ? images : undefined,
        previewUrl: attachment?.previewUrl,
      }

      dispatch({
        type: "begin",
        user: message,
        imageUrl: attachment?.previewUrl,
      })

      try {
        for await (const event of streamChat({
          message,
          sessionId,
          images,
          signal: controller.signal,
        })) {
          if (event.kind === "token") {
            dispatch({ type: "token", token: event.token })
          } else if (event.kind === "error") {
            dispatch({
              type: "stream_error",
              error: { reason: "unknown", message: event.message },
            })
            return
          } else if (event.kind === "done") {
            dispatch({ type: "commit_assistant" })
            return
          }
        }
        dispatch({ type: "commit_assistant" })
      } catch (err) {
        if ((err as Error)?.name === "AbortError") return
        dispatch({
          type: "stream_error",
          error: {
            reason: "network",
            message:
              err instanceof Error && err.message
                ? err.message
                : "Sorry, we couldn't get a response right now. Your conversation is saved — tap Try Again to resend your question.",
          },
        })
      }
    },
    [sessionId, state.isStreaming],
  )

  const retry = useCallback(() => {
    const args = lastStreamArgsRef.current
    if (!args || state.isStreaming) return
    dispatch({ type: "reset_error" })
    void send(args.message, {
      images: args.images,
      previewUrl: args.previewUrl,
    })
  }, [send, state.isStreaming])

  const clearError = useCallback(() => dispatch({ type: "reset_error" }), [])
  const clearHistory = useCallback(() => dispatch({ type: "clear_history" }), [])

  return {
    history: state.history,
    pendingAssistant: state.pendingAssistant,
    isStreaming: state.isStreaming,
    error: state.error,
    send,
    retry,
    clearError,
    clearHistory,
  }
}
