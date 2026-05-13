interface Props {
  variant?: "low_confidence" | "verify" | "out_of_scope"
  children?: React.ReactNode
}

const COPY: Record<NonNullable<Props["variant"]>, string> = {
  low_confidence:
    "This answer may not be fully accurate for your specific vehicle. We recommend verifying with a certified mechanic before proceeding.",
  verify:
    "Please double-check with your owner's manual or a qualified mechanic before acting on this.",
  out_of_scope:
    "That question is outside what Pocket Mechanics can help with. Try asking about a car problem, maintenance tip, or vehicle specification.",
}

export function SafetyBanner({ variant = "low_confidence", children }: Props) {
  return (
    <div className="rounded-xl border-l-4 border-amber-400 bg-amber-50 px-4 py-3 text-sm leading-snug text-amber-900">
      {children ?? COPY[variant]}
    </div>
  )
}
