interface Props {
  message: string
  onRetry?: () => void
  retryLabel?: string
}

export function ErrorState({ message, onRetry, retryLabel = "Try Again" }: Props) {
  return (
    <div className="flex items-center justify-between gap-3 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
      <span className="leading-snug">{message}</span>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="shrink-0 rounded-lg border border-amber-300 bg-white px-3 py-1.5 text-xs font-medium text-amber-900 hover:bg-amber-100"
        >
          {retryLabel}
        </button>
      )}
    </div>
  )
}
