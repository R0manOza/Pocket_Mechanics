import { useEffect, useRef } from "react"

interface Props {
  value: string
  onChange: (value: string) => void
  onSubmit: () => void
  disabled?: boolean
  placeholder?: string
}

const MAX_HEIGHT_PX = 200

export function ChatInput({
  value,
  onChange,
  onSubmit,
  disabled = false,
  placeholder = "What does the check engine light mean?",
}: Props) {
  const ref = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    const el = ref.current
    if (!el) return
    el.style.height = "auto"
    el.style.height = `${Math.min(el.scrollHeight, MAX_HEIGHT_PX)}px`
  }, [value])

  function onKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      if (!disabled && value.trim()) onSubmit()
    }
  }

  return (
    <textarea
      ref={ref}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      onKeyDown={onKeyDown}
      placeholder={placeholder}
      rows={1}
      disabled={disabled}
      className="min-h-[44px] max-h-[200px] flex-1 resize-none overflow-y-auto rounded-xl border border-brand-border bg-brand-card px-3.5 py-2.5 2xl:px-4 2xl:py-3 text-sm text-brand-text placeholder:text-brand-text-muted/60 outline-none transition-colors focus:border-brand-accent disabled:opacity-60"
      aria-label="Message"
    />
  )
}
