interface Props {
  onConfirm: () => void
  onCancel: () => void
  busy?: boolean
}

export function RepairApprovalBanner({ onConfirm, onCancel, busy }: Props) {
  return (
    <div
      role="alertdialog"
      aria-labelledby="repair-approval-title"
      aria-describedby="repair-approval-desc"
      className="rounded-xl border border-amber-500/40 bg-amber-950/40 px-4 py-4 text-sm text-brand-text shadow-lg backdrop-blur"
    >
      <p id="repair-approval-title" className="font-semibold text-amber-200">
        Hands-on repair guidance
      </p>
      <p id="repair-approval-desc" className="mt-2 leading-relaxed text-brand-text-muted">
        Your question may involve physical work on the vehicle (tools, jacks, electrical
        parts, fluids). Pocket Mechanics can share general steps, but{" "}
        <strong className="font-medium text-brand-text">
          you are responsible for safety
        </strong>
        —verify every step with your owner&apos;s manual and a qualified mechanic before
        acting.
      </p>
      <div className="mt-4 flex flex-wrap gap-2">
        <button
          type="button"
          onClick={onConfirm}
          disabled={busy}
          className="rounded-lg bg-brand-accent px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-brand-glow-soft disabled:opacity-60"
        >
          {busy ? "Loading…" : "Yes — show me the steps"}
        </button>
        <button
          type="button"
          onClick={onCancel}
          disabled={busy}
          className="rounded-lg border border-brand-border bg-brand-card px-4 py-2 text-sm font-medium text-brand-text-muted transition-colors hover:border-brand-accent hover:text-brand-text disabled:opacity-60"
        >
          Cancel
        </button>
      </div>
    </div>
  )
}
