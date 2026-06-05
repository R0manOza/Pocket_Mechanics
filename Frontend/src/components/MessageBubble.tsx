import type { ChatRole } from "../lib/types"

interface Props {
  role: ChatRole
  content: string
  streaming?: boolean
  imageUrl?: string
}

export function MessageBubble({ role, content, streaming = false, imageUrl }: Props) {
  const isUser = role === "user"
  return (
    <div className={`flex w-full ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[80%] overflow-hidden rounded-2xl text-sm leading-relaxed shadow-sm ${
          isUser
            // User: violet-accent pill — clearly "from you"
            ? "bg-brand-accent text-white font-medium"
            // Assistant: dark card with a soft glow border — fits the page glow theme
            : "border border-brand-border bg-brand-card text-brand-text"
        }`}
      >
        {imageUrl && (
          <img
            src={imageUrl}
            alt="Attached"
            className="block max-h-72 w-full object-cover"
          />
        )}
        {(content || streaming) && (
          <div className="whitespace-pre-wrap px-4 py-3">
            {content}
            {streaming && (
              <span
                className="ml-0.5 inline-block w-0.5 animate-pulse bg-brand-accent align-middle"
                style={{ height: "1.1em" }}
                aria-hidden
              />
            )}
          </div>
        )}
      </div>
    </div>
  )
}
