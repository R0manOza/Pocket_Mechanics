export function TypingIndicator() {
  return (
    <div className="flex w-full justify-start">
      <div className="max-w-[80%] rounded-2xl border border-brand-border bg-brand-card px-4 py-3 shadow-sm">
        <div className="flex items-center gap-1.5" aria-label="Assistant is typing">
          <span className="h-2 w-2 animate-bounce rounded-full bg-brand-accent [animation-delay:0ms]" />
          <span className="h-2 w-2 animate-bounce rounded-full bg-brand-accent [animation-delay:150ms]" />
          <span className="h-2 w-2 animate-bounce rounded-full bg-brand-accent [animation-delay:300ms]" />
        </div>
      </div>
    </div>
  )
}
