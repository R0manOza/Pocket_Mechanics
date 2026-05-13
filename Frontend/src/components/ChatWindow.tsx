import { useEffect, useRef } from "react"
import type { ChatMessage } from "../lib/types"
import { MessageBubble } from "./MessageBubble"

interface Props {
  history: ChatMessage[]
  pendingAssistant: string
  isStreaming: boolean
}

export function ChatWindow({ history, pendingAssistant, isStreaming }: Props) {
  const endRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [history.length, pendingAssistant, isStreaming])

  const empty = history.length === 0 && !pendingAssistant

  return (
    <div className="flex h-full flex-col gap-3 overflow-y-auto px-1 py-4">
      {empty ? (
        <div className="m-auto max-w-md text-center text-slate-500">
          <p className="text-lg font-medium text-slate-700">
            Ask Pocket Mechanics anything about your car.
          </p>
          <p className="mt-2 text-sm">
            Examples: <em>What is a serpentine belt?</em> ·{" "}
            <em>How often should I change my oil?</em>
          </p>
        </div>
      ) : (
        <>
          {history.map((m, i) => (
            <MessageBubble key={i} role={m.role} content={m.content} />
          ))}
          {pendingAssistant && (
            <MessageBubble
              role="assistant"
              content={pendingAssistant}
              streaming={isStreaming}
            />
          )}
        </>
      )}
      <div ref={endRef} />
    </div>
  )
}
