interface LogoProps {
  /** When true, hides the wordmark and renders the icon only. */
  iconOnly?: boolean
}

export function Logo({ iconOnly = false }: LogoProps) {
  return (
    <span className="inline-flex items-center gap-2">
      {!iconOnly && (
        <span className="font-bold tracking-normal text-brand-text text-2xl 2xl:text-3xl">
          Pocket <span className="text-brand-accent">Mechanics</span>
        </span>
      )}
    </span>
  )
}
