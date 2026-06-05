import type { AiModelOption } from "../lib/types"

interface Props {
  models: AiModelOption[]
  value: string
  onChange: (modelId: string) => void
  disabled?: boolean
}

function formatUsdPerM(n: number): string {
  if (n === 0) return "$0"
  if (n < 0.1) return `$${n.toFixed(2)}`
  if (n < 10) return `$${n.toFixed(2)}`
  return `$${n.toFixed(2)}`
}

function optionLabel(m: AiModelOption): string {
  if (m.input_usd_per_million === 0 && m.output_usd_per_million === 0) {
    return `${m.label} (free)`
  }
  const inp = formatUsdPerM(m.input_usd_per_million)
  const out = formatUsdPerM(m.output_usd_per_million)
  return `${m.label} — ${inp} in / ${out} out per 1M tokens`
}

export function ModelSelect({ models, value, onChange, disabled }: Props) {
  if (!models.length) return null

  const selected = models.find((m) => m.id === value)

  return (
    <label className="flex items-center gap-2 text-xs text-brand-text-muted">
      <span className="shrink-0 font-medium uppercase tracking-wide">Model</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        className="max-w-[min(100%,28rem)] truncate rounded-lg border border-brand-border bg-brand-card px-2 py-1.5 text-sm text-brand-text outline-none focus:border-brand-accent disabled:opacity-60"
        title={selected ? optionLabel(selected) : undefined}
      >
        {models.map((m) => (
          <option key={m.id} value={m.id}>
            {optionLabel(m)}
          </option>
        ))}
      </select>
    </label>
  )
}
