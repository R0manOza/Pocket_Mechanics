import type { ChatRole } from "../lib/types"

interface Props {
  role: ChatRole
  content: string
  streaming?: boolean
}

export function MessageBubble({ role, content, streaming = false }: Props) {
  const isUser = role === "user"
  return (
    <div className={`flex w-full ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[80%] whitespace-pre-wrap rounded-2xl px-4 py-3 text-[15px] leading-relaxed shadow-sm ${
          isUser
            ? "bg-slate-900 text-white"
            : "border border-slate-200 bg-white text-slate-800"
        }`}
      >
        {content}
        {streaming && (
          <span className="ml-1 inline-block h-2 w-2 animate-pulse rounded-full bg-slate-400 align-middle" />
        )}
      </div>
    </div>
  )
}
