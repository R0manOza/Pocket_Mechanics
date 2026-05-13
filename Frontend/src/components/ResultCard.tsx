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
    <article className="grid grid-cols-1 gap-4 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm md:grid-cols-[180px_1fr]">
      {thumbnailUrl && (
        <img
          src={thumbnailUrl}
          alt="Uploaded engine bay"
          className="h-44 w-full rounded-xl object-cover md:h-full"
        />
      )}
      <div className="flex flex-col gap-3 text-sm text-slate-700">
        {identifiedPart && (
          <header>
            <p className="text-xs uppercase tracking-wide text-slate-500">
              Likely part
            </p>
            <h3 className="text-lg font-semibold text-slate-900">
              {identifiedPart}
            </h3>
          </header>
        )}
        {explanation && (
          <section>
            <p className="text-xs uppercase tracking-wide text-slate-500">
              What it does
            </p>
            <p>{explanation}</p>
          </section>
        )}
        {nextStep && (
          <section>
            <p className="text-xs uppercase tracking-wide text-slate-500">
              Next step
            </p>
            <p>{nextStep}</p>
          </section>
        )}
        {safetyNote && (
          <section>
            <p className="text-xs uppercase tracking-wide text-slate-500">
              Safety note
            </p>
            <p className="text-amber-800">{safetyNote}</p>
          </section>
        )}
      </div>
    </article>
  )
}
