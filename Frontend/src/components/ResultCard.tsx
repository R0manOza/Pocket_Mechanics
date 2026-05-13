interface ResultCardProps {
  thumbnailUrl?: string
  identifiedPart?: string
  explanation?: string
  nextStep?: string
  safetyNote?: string
}

export function ResultCard({
  thumbnailUrl,
  identifiedPart,
  explanation,
  nextStep,
  safetyNote,
}: ResultCardProps) {
  return (
    <article className="grid grid-cols-1 gap-4 rounded-2xl border border-brand-border bg-brand-card/40 backdrop-blur p-4 shadow-sm md:grid-cols-[180px_1fr]">
      {thumbnailUrl && (
        <img
          src={thumbnailUrl}
          alt="Uploaded engine bay"
          className="h-44 w-full rounded-xl object-cover md:h-full"
        />
      )}
      <div className="flex flex-col gap-3 text-sm text-brand-text-muted">
        {identifiedPart && (
          <header>
            <p className="text-xs uppercase tracking-wide text-brand-text-muted/60">
              Likely part
            </p>
            <h3 className="text-lg font-semibold text-brand-text">
              {identifiedPart}
            </h3>
          </header>
        )}
        {explanation && (
          <section>
            <p className="text-xs uppercase tracking-wide text-brand-text-muted/60">
              What it does
            </p>
            <p>{explanation}</p>
          </section>
        )}
        {nextStep && (
          <section>
            <p className="text-xs uppercase tracking-wide text-brand-text-muted/60">
              Next step
            </p>
            <p>{nextStep}</p>
          </section>
        )}
        {safetyNote && (
          <section>
            <p className="text-xs uppercase tracking-wide text-brand-text-muted/60">
              Safety note
            </p>
            <p className="text-brand-accent">{safetyNote}</p>
          </section>
        )}
      </div>
    </article>
  )
}
