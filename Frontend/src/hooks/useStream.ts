import { useCallback, useEffect, useReducer, useRef } from "react"
import { fileToVisionDataUrl, streamChat } from "../lib/api"
import {
  loadChatHistory,
  saveChatHistory,
  titleFromMessage,
} from "../lib/sessionStorage"
import type { ChatError, ChatMessage, RepairApprovalPending } from "../lib/types"

type State = {
  history: ChatMessage[]
  pendingAssistant: string
  isStreaming: boolean
  error: ChatError | null
  lastUserMessage: string | null
  repairApproval: RepairApprovalPending | null
}

type Action =
  | { type: "begin"; user: string; imageUrl?: string; skipUserBubble?: boolean }
  | { type: "token"; token: string }
  | { type: "commit_assistant"; sessionId: string; touchSession: (title: string) => void }
  | { type: "stream_error"; error: ChatError }
  | { type: "reset_error" }
  | { type: "clear_history" }
  | { type: "load_history"; history: ChatMessage[] }
  | { type: "repair_approval_required"; pending: RepairApprovalPending }
  | { type: "dismiss_repair_approval" }

const initial: State = {
  history: [],
  pendingAssistant: "",
  isStreaming: false,
  error: null,
  lastUserMessage: null,
  repairApproval: null,
}

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case "begin":
      return {
        ...state,
        isStreaming: true,
        pendingAssistant: "",
        error: null,
        repairApproval: null,
        lastUserMessage: action.user,
        history: action.skipUserBubble
          ? state.history
          : [
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
      const history: ChatMessage[] = [
        ...state.history,
        { role: "assistant", content: finished },
      ]
      saveChatHistory(action.sessionId, history)
      const firstUser = history.find((m) => m.role === "user")
      if (firstUser) {
        action.touchSession(titleFromMessage(firstUser.content))
      }
      return {
        ...state,
        isStreaming: false,
        pendingAssistant: "",
        history,
      }
    }
    case "stream_error":
      return { ...state, isStreaming: false, error: action.error }
    case "reset_error":
      return { ...state, error: null }
    case "clear_history":
      return { ...initial }
    case "load_history":
      return { ...initial, history: action.history }
    case "repair_approval_required":
      return {
        ...state,
        isStreaming: false,
        pendingAssistant: "",
        repairApproval: action.pending,
      }
    case "dismiss_repair_approval":
      return { ...state, repairApproval: null }
    default:
      return state
  }
}

export function useStream(
  sessionId: string,
  touchSession: (title: string) => void,
  model: string | undefined,
) {
  const [state, dispatch] = useReducer(reducer, initial)
  const controllerRef = useRef<AbortController | null>(null)
  const lastStreamArgsRef = useRef<RepairApprovalPending | null>(null)

  useEffect(() => {
    dispatch({ type: "load_history", history: loadChatHistory(sessionId) })
  }, [sessionId])

  const executeStream = useCallback(
    async (opts: {
      message: string
      images?: string[]
      previewUrl?: string
      repairStepsApproved?: boolean
      skipUserBubble?: boolean
    }) => {
      controllerRef.current?.abort()
      const controller = new AbortController()
      controllerRef.current = controller

      try {
        for await (const event of streamChat({
          message: opts.message,
          sessionId,
          images: opts.images,
          model,
          repairStepsApproved: opts.repairStepsApproved,
          signal: controller.signal,
        })) {
          if (event.kind === "gate") {
            dispatch({
              type: "repair_approval_required",
              pending: {
                message: opts.message,
                images: opts.images,
                previewUrl: opts.previewUrl,
              },
            })
            return
          }
          if (event.kind === "token") {
            dispatch({ type: "token", token: event.token })
          } else if (event.kind === "error") {
            dispatch({
              type: "stream_error",
              error: { reason: "unknown", message: event.message },
            })
            return
          } else if (event.kind === "done") {
            dispatch({ type: "commit_assistant", sessionId, touchSession })
            return
          }
        }
        dispatch({ type: "commit_assistant", sessionId, touchSession })
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
    [sessionId, touchSession, model],
  )

  const send = useCallback(
    async (
      message: string,
      attachment?: { file?: File; previewUrl?: string; images?: string[] },
    ) => {
      const hasFile = Boolean(attachment?.file)
      const hasPresetImages = Boolean(attachment?.images?.length)
      if ((!message.trim() && !hasFile && !hasPresetImages) || !sessionId || state.isStreaming)
        return

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

      await executeStream({
        message,
        images,
        previewUrl: attachment?.previewUrl,
      })
    },
    [sessionId, state.isStreaming, executeStream],
  )

  const confirmRepairSteps = useCallback(async () => {
    const pending = state.repairApproval
    if (!pending || state.isStreaming) return

    lastStreamArgsRef.current = pending
    dispatch({ type: "dismiss_repair_approval" })
    dispatch({
      type: "begin",
      user: pending.message,
      skipUserBubble: true,
    })

    await executeStream({
      message: pending.message,
      images: pending.images,
      previewUrl: pending.previewUrl,
      repairStepsApproved: true,
      skipUserBubble: true,
    })
  }, [state.repairApproval, state.isStreaming, executeStream])

  const dismissRepairApproval = useCallback(() => {
    dispatch({ type: "dismiss_repair_approval" })
  }, [])

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

  const clearHistory = useCallback(() => {
    saveChatHistory(sessionId, [])
    dispatch({ type: "clear_history" })
  }, [sessionId])

  return {
    history: state.history,
    pendingAssistant: state.pendingAssistant,
    isStreaming: state.isStreaming,
    error: state.error,
    repairApproval: state.repairApproval,
    send,
    confirmRepairSteps,
    dismissRepairApproval,
    retry,
    clearError,
    clearHistory,
  }
}
