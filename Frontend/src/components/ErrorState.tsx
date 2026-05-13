interface Props {
  message: string
  onRetry?: () => void
  retryLabel?: string
}

export function ErrorState({ message, onRetry, retryLabel = "Try Again" }: Props) {
  return (
    <div className="flex items-center justify-between gap-3 rounded-xl border border-brand-primary/40 bg-brand-primary/10 px-4 py-3 text-sm text-brand-text">
      <span className="leading-snug">{message}</span>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="shrink-0 rounded-lg border border-brand-primary/60 bg-brand-primary px-3 py-1.5 text-xs font-semibold text-white transition-colors hover:cursor-pointer hover:bg-brand-primary-hover"
        >
          {retryLabel}
        </button>
      )}
    </div>
  )
}
